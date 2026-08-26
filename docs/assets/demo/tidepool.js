/* ==========================================================================
   Tidepool Commerce Analytics — static twin of the Dash demo dashboard

   The published site is a static GitHub Pages build, where a Dash server cannot
   run. This file renders the same dashboard client-side with plotly.js from the
   same seeded dataset the Dash page uses (tidepool_data.json, written by
   demo_dashboard/export.py).

   The two builds are meant to agree to the last digit, which drives three
   things here:

     * Numbers are formatted through roundHalfUp, never toFixed. JavaScript's
       toLocaleString rounds ties away from zero and Python's format rounds them
       to even, so $932.15 would render differently in the two builds.
     * The PRNG, the market spread and the customer sampler are transliterated
       from demo_dashboard/geo.py rather than reimplemented: same integer LCG,
       same draw order, no transcendental functions anywhere.
     * Every threshold, colour and label is read from the payload rather than
       restated here. Two copies of a constant is two charts that eventually
       disagree.

   The shell markup is generated from the section config below rather than
   written into index.html, for the same reason.
   ========================================================================== */
(function () {
  'use strict';

  var DATA_URL = '../assets/demo/tidepool_data.json';
  var DB = null;      // payload
  var CFG = null;     // payload.config

  var state = {
    brand: null,
    preset: null,
    view: null,
    trend: { left: 'revenue', right: 'orders', grain: 'daily',
             events: true, anomalies: true },
    categoryMode: 'share',
    channelMode: 'absolute',
    study: { metric: 'revenue', kinds: [] },
    map: { display: 'market', level: 'city' },
    returnGrain: 'weekly',
    growthMonth: null,
    growthTimer: null,
  };

  // Caches. Generating a third of a million markers is fast but not free, and
  // the same cloud is asked for by three different views.
  var cache = { orders: {}, rfm: {} };

  // ======================================================================
  // Formatting
  // ======================================================================
  function roundHalfUp(value, decimals) {
    decimals = decimals || 0;
    if (!isFinite(value)) return value;
    var factor = Math.pow(10, decimals);
    var scaled = value * factor;
    var shifted = Math.floor(Math.abs(scaled) + 0.5);
    return (scaled < 0 ? -shifted : shifted) / factor;
  }

  function group(value, decimals) {
    decimals = decimals || 0;
    return roundHalfUp(value, decimals).toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  function fmtValue(value, kind) {
    if (value === null || value === undefined) return '—';
    if (kind === 'money') return '$' + group(value);
    if (kind === 'money2') return '$' + group(value, 2);
    if (kind === 'percent') return group(value * 100, 1) + '%';
    if (kind === 'percent2') return group(value * 100, 2) + '%';
    if (kind === 'ratio') return group(value, 2) + 'x';
    return group(value);
  }

  function fmtCompact(value, kind) {
    var prefix = (kind === 'money' || kind === 'money2') ? '$' : '';
    if (kind === 'percent' || kind === 'percent2') return fmtValue(value, kind);
    var magnitude = Math.abs(value);
    if (magnitude >= 1e9) return prefix + group(value / 1e9, 1) + 'B';
    if (magnitude >= 1e6) return prefix + group(value / 1e6, 1) + 'M';
    if (magnitude >= 1e4) return prefix + group(value / 1e3, 1) + 'K';
    if (kind === 'money2') return fmtValue(value, kind);
    return prefix + group(value);
  }

  function metricLabel(key) {
    return (CFG.metrics[key] && CFG.metrics[key].label) || key;
  }

  function metricFormat(key) {
    return (CFG.metrics[key] && CFG.metrics[key].format) || 'int';
  }

  function hoverNumber(kind) {
    if (kind === 'money') return '$%{y:,.0f}';
    if (kind === 'money2') return '$%{y:,.2f}';
    if (kind === 'percent') return '%{y:.1%}';
    if (kind === 'percent2') return '%{y:.2%}';
    return '%{y:,.0f}';
  }

  function axisTick(kind) {
    if (kind === 'money' || kind === 'money2') {
      return { tickprefix: '$', tickformat: '~s' };
    }
    if (kind === 'percent') return { tickformat: '.1%' };
    if (kind === 'percent2') return { tickformat: '.2%' };
    return { tickformat: ',.0f' };
  }

  function soft(hex, alpha) {
    var clean = hex.replace('#', '');
    var r = parseInt(clean.slice(0, 2), 16);
    var g = parseInt(clean.slice(2, 4), 16);
    var b = parseInt(clean.slice(4, 6), 16);
    return 'rgba(' + r + ', ' + g + ', ' + b + ', ' + (alpha === undefined ? 0.14 : alpha) + ')';
  }

  // ======================================================================
  // Layout
  // ======================================================================
  var MARKER_LINE = 'rgba(26, 26, 24, 0.28)';
  var SERIF = 'Source Serif 4, Iowan Old Style, Georgia, serif';
  var FONT_FAMILY = 'Public Sans, Segoe UI, Helvetica Neue, sans-serif';

  function deepMerge(base, extra) {
    var out = {};
    Object.keys(base).forEach(function (key) { out[key] = base[key]; });
    Object.keys(extra || {}).forEach(function (key) {
      var value = extra[key];
      if (value && typeof value === 'object' && !Array.isArray(value) &&
          out[key] && typeof out[key] === 'object' && !Array.isArray(out[key])) {
        out[key] = deepMerge(out[key], value);
      } else {
        out[key] = value;
      }
    });
    return out;
  }

  function baseLayout(height, overrides) {
    var surface = CFG.surface;
    var layout = {
      height: height,
      paper_bgcolor: surface.bg,
      plot_bgcolor: surface.bg,
      font: { family: FONT_FAMILY, color: surface.text_secondary, size: 12 },
      margin: { l: 62, r: 26, t: 18, b: 44 },
      hoverlabel: {
        bgcolor: '#FFFFFF',
        bordercolor: surface.border,
        font: { color: surface.text, size: 12, family: FONT_FAMILY },
      },
      xaxis: {
        gridcolor: surface.grid, zerolinecolor: surface.zeroline,
        linecolor: surface.border,
        tickfont: { size: 11, color: surface.text_muted },
        title: { font: { size: 11.5, color: surface.text_secondary } },
        automargin: true,
      },
      yaxis: {
        gridcolor: surface.grid, zerolinecolor: surface.zeroline,
        linecolor: 'rgba(0,0,0,0)',
        tickfont: { size: 11, color: surface.text_muted },
        title: { font: { size: 11.5, color: surface.text_secondary } },
        automargin: true,
      },
      legend: {
        orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'left', x: 0,
        font: { size: 11.5, color: surface.text_secondary },
        bgcolor: 'rgba(0,0,0,0)',
      },
      colorway: CFG.palette.slice(),
      dragmode: 'pan',
    };
    return deepMerge(layout, overrides);
  }

  var PLOT_CONFIG = { displayModeBar: false, responsive: true, showTips: false };

  function draw(id, traces, layout) {
    var node = document.getElementById(id);
    if (!node) return;
    Plotly.react(node, traces, layout, PLOT_CONFIG);
  }

  function drawEmpty(id, message, height) {
    draw(id, [], baseLayout(height || 300, {
      xaxis: { visible: false }, yaxis: { visible: false },
      annotations: [{
        text: message, showarrow: false,
        font: { size: 13, color: CFG.surface.text_muted },
        xref: 'paper', yref: 'paper', x: 0.5, y: 0.5,
      }],
    }));
  }

  // ======================================================================
  // Series access and windowing
  // ======================================================================
  function bundle() { return DB.brands[state.brand]; }

  function seriesFor(bnd, key) {
    if (bnd.series[key]) return bnd.series[key];
    var pair = CFG.derived[key];
    if (pair) {
      var top = bnd.series[pair[0]];
      var bottom = bnd.series[pair[1]];
      return top.map(function (value, index) {
        return bottom[index] ? value / bottom[index] : 0;
      });
    }
    return DB.dates.map(function () { return 0; });
  }

  function isRatio(key) { return Object.prototype.hasOwnProperty.call(CFG.derived, key); }

  function presetDays(label) {
    var found = CFG.presets.filter(function (p) { return p.label === label; })[0];
    return found ? found.days : 365;
  }

  function windowIndices() {
    var days = presetDays(state.preset);
    var total = DB.dates.length;
    if (days <= 0 || days >= total) return [0, total];
    return [total - days, total];
  }

  function sum(values) {
    return values.reduce(function (a, b) { return a + b; }, 0);
  }

  function bucketLabel(iso, grain) {
    if (grain === 'daily') return iso;
    if (grain === 'monthly') return iso.slice(0, 7);
    if (grain === 'quarterly') {
      return iso.slice(0, 4) + '-Q' + (Math.floor((Number(iso.slice(5, 7)) - 1) / 3) + 1);
    }
    var date = new Date(iso + 'T00:00:00Z');
    var weekday = (date.getUTCDay() + 6) % 7;          // Monday = 0
    date.setUTCDate(date.getUTCDate() - weekday);
    return date.toISOString().slice(0, 10);
  }

  function resample(dates, values, grain, how) {
    if (grain === 'daily') return [dates.slice(), values.slice()];
    var order = [];
    var buckets = {};
    dates.forEach(function (iso, index) {
      var label = bucketLabel(iso, grain);
      if (!buckets[label]) { buckets[label] = []; order.push(label); }
      buckets[label].push(values[index]);
    });
    var out = order.map(function (label) {
      var chunk = buckets[label];
      if (how === 'mean') return sum(chunk) / chunk.length;
      if (how === 'last') return chunk[chunk.length - 1];
      return sum(chunk);
    });
    return [order, out];
  }

  function resampleRatio(dates, top, bottom, grain) {
    var a = resample(dates, top, grain, 'sum');
    var b = resample(dates, bottom, grain, 'sum');
    return [a[0], a[1].map(function (value, index) {
      return b[1][index] ? value / b[1][index] : 0;
    })];
  }

  function grainSeries(bnd, key, lo, hi, grain) {
    var dates = DB.dates.slice(lo, hi);
    if (isRatio(key)) {
      var pair = CFG.derived[key];
      return resampleRatio(dates, bnd.series[pair[0]].slice(lo, hi),
                           bnd.series[pair[1]].slice(lo, hi), grain);
    }
    return resample(dates, seriesFor(bnd, key).slice(lo, hi), grain, 'sum');
  }

  function priorPeriodDelta(bnd, key, lo, hi) {
    var span = hi - lo;
    var priorLo = Math.max(lo - span, 0);
    if (priorLo >= lo) return 0;
    var prior;
    var current;
    if (isRatio(key)) {
      var pair = CFG.derived[key];
      var priorBottom = sum(bnd.series[pair[1]].slice(priorLo, lo));
      var currentBottom = sum(bnd.series[pair[1]].slice(lo, hi));
      if (priorBottom <= 0 || currentBottom <= 0) return 0;
      prior = sum(bnd.series[pair[0]].slice(priorLo, lo)) / priorBottom;
      current = sum(bnd.series[pair[0]].slice(lo, hi)) / currentBottom;
    } else {
      var values = seriesFor(bnd, key);
      prior = sum(values.slice(priorLo, lo));
      current = sum(values.slice(lo, hi));
    }
    if (prior <= 0) return 0;
    return (current - prior) / prior * 100;
  }

  // ======================================================================
  // Analysis
  // ======================================================================
  function median(values) {
    var ordered = values.slice().sort(function (a, b) { return a - b; });
    if (!ordered.length) return 0;
    var mid = Math.floor(ordered.length / 2);
    return ordered.length % 2 ? ordered[mid] : (ordered[mid - 1] + ordered[mid]) / 2;
  }

  function detectAnomalies(values, dates, threshold, window) {
    threshold = threshold || CFG.anomalyZ;
    window = window || 28;
    var out = [];
    if (values.length < window + 4) return out;
    for (var index = window; index < values.length; index += 1) {
      var history = values.slice(index - window, index);
      var centre = median(history);
      var spread = median(history.map(function (v) { return Math.abs(v - centre); })) * 1.4826;
      if (spread <= 1e-9) continue;
      var z = (values[index] - centre) / spread;
      if (Math.abs(z) < threshold) continue;
      out.push({
        index: index, date: dates[index], value: values[index], baseline: centre,
        z: roundHalfUp(z, 2), direction: z > 0 ? 'high' : 'low',
        pct: centre ? (values[index] - centre) / centre * 100 : 0,
      });
    }
    return out;
  }

  function driverDecomposition(bnd, lo, hi) {
    var span = hi - lo;
    var priorLo = Math.max(lo - span, 0);
    if (priorLo >= lo) return { terms: [], prior: 0, current: 0, change: 0, span: span };

    function totals(start, stop) {
      var visits = sum(bnd.series.visits.slice(start, stop));
      var orders = sum(bnd.series.orders.slice(start, stop));
      var revenue = sum(bnd.series.revenue.slice(start, stop));
      return {
        visits: visits,
        conversion: visits ? orders / visits : 0,
        aov: orders ? revenue / orders : 0,
        revenue: revenue,
      };
    }

    var prior = totals(priorLo, lo);
    var current = totals(lo, hi);
    var state_ = { visits: prior.visits, conversion: prior.conversion, aov: prior.aov };
    var walked = state_.visits * state_.conversion * state_.aov;
    var terms = [];
    [['visits', 'Site Visits'], ['conversion', 'Conversion Rate'],
     ['aov', 'Average Order Value']].forEach(function (pair) {
      state_[pair[0]] = current[pair[0]];
      var after = state_.visits * state_.conversion * state_.aov;
      terms.push({
        key: pair[0], label: pair[1], contribution: after - walked,
        prior: prior[pair[0]], current: current[pair[0]],
      });
      walked = after;
    });

    return {
      terms: terms, prior: prior.revenue, current: current.revenue,
      change: current.revenue - prior.revenue, span: span,
    };
  }

  function eventStudy(bnd, metric, kinds, before, after) {
    before = before || 7;
    after = after || 14;
    var values = seriesFor(bnd, metric);
    var wanted = (kinds && kinds.length) ? kinds : null;
    var aligned = {};

    bnd.events.forEach(function (event) {
      if (wanted && wanted.indexOf(event.kind) === -1) return;
      var origin = event.day_index;
      if (origin - before < 0 || origin + after >= values.length) return;
      var baseline = values[origin - 1];
      if (baseline <= 0) return;
      var row = [];
      for (var offset = -before; offset <= after; offset += 1) {
        row.push(values[origin + offset] / baseline);
      }
      if (!aligned[event.kind]) aligned[event.kind] = [];
      aligned[event.kind].push(row);
    });

    var offsets = [];
    for (var o = -before; o <= after; o += 1) offsets.push(o);

    var out = [];
    Object.keys(aligned).forEach(function (kind) {
      var windows = aligned[kind];
      if (windows.length < 2) return;
      var mean = [];
      var lower = [];
      var upper = [];
      offsets.forEach(function (_, position) {
        var column = windows.map(function (row) { return row[position]; });
        var avg = sum(column) / column.length;
        var variance = sum(column.map(function (v) { return Math.pow(v - avg, 2); }))
                       / Math.max(column.length - 1, 1);
        var stderr = Math.sqrt(variance / column.length);
        mean.push(avg);
        lower.push(avg - 1.96 * stderr);
        upper.push(avg + 1.96 * stderr);
      });
      out.push({
        kind: kind, occurrences: windows.length, offsets: offsets,
        mean: mean, lower: lower, upper: upper, peak: Math.max.apply(null, mean),
        color: CFG.eventKinds[kind].color,
      });
    });
    out.sort(function (a, b) { return b.peak - a.peak; });
    return out;
  }

  function promotionWindows(bnd, lo, hi, span) {
    span = span || 3;
    var promoted = {};
    bnd.events.forEach(function (event) {
      if (['Flash Sale', 'Seasonal Campaign', 'Loyalty Push'].indexOf(event.kind) === -1) return;
      for (var offset = 0; offset < span; offset += 1) promoted[event.day_index + offset] = true;
    });
    var on = [];
    var off = [];
    for (var index = lo; index < hi; index += 1) {
      if (promoted[index]) on.push(index); else off.push(index);
    }
    return [on, off];
  }

  // ======================================================================
  // Deterministic point generation — mirrors demo_dashboard/geo.py
  // ======================================================================
  var MASK = 0xFFFFFFFF;

  function Lcg(seed) { this.state = seed >>> 0; }

  Lcg.prototype.nextFloat = function () {
    // Math.imul keeps the 32-bit multiply exact, which is what makes the stream
    // identical to Python's.
    this.state = (Math.imul(1664525, this.state) + 1013904223) >>> 0;
    return this.state / 4294967296;
  };

  Lcg.prototype.jitter = function (spread) {
    var u = (this.nextFloat() + this.nextFloat() + this.nextFloat()) / 3;
    return (u * 2 - 1) * spread;
  };

  function stringSeed(text) {
    var h = 2166136261;
    for (var index = 0; index < text.length; index += 1) {
      h ^= text.charCodeAt(index) & 0xFF;
      h = Math.imul(h, 16777619) & MASK;
    }
    return h >>> 0;
  }

  var LEVEL_KEYS = { city: 'city', region: 'region', country: 'country' };

  function placeLabel(level, entry) {
    if (level === 'city') return entry.city + ', ' + entry.region + ', ' + entry.country;
    if (level === 'region') return entry.region + ', ' + entry.country;
    return entry.country;
  }

  function aggregateByLevel(locations, level) {
    var key = LEVEL_KEYS[level] || 'city';
    var merged = {};
    locations.forEach(function (row) {
      var name = row[key];
      var entry = merged[name];
      if (!entry) {
        entry = {
          name: name, city: row.city, region: row.region, country: row.country,
          orders: 0, revenue: 0, latWeight: 0, lonWeight: 0,
          seed: row.seed, ramp_lag: row.ramp_lag, top: 0,
        };
        merged[name] = entry;
      }
      entry.orders += row.orders;
      entry.revenue += row.revenue;
      entry.latWeight += row.lat * row.orders;
      entry.lonWeight += row.lon * row.orders;
      if (row.orders > entry.top) {
        entry.top = row.orders;
        entry.ramp_lag = row.ramp_lag;
        entry.seed = row.seed;
      }
    });

    var out = Object.keys(merged).map(function (name) {
      var entry = merged[name];
      var orders = entry.orders || 1;
      return {
        name: entry.name,
        label: placeLabel(level, entry),
        country: entry.country,
        lat: roundHalfUp(entry.latWeight / orders, 4),
        lon: roundHalfUp(entry.lonWeight / orders, 4),
        orders: entry.orders,
        revenue: roundHalfUp(entry.revenue, 2),
        aov: roundHalfUp(entry.revenue / orders, 2),
        seed: entry.seed,
        ramp_lag: entry.ramp_lag,
      };
    });
    out.sort(function (a, b) { return b.orders - a.orders; });
    return out;
  }

  var SPREAD_DEGREES = 0.95;
  var SPREAD_INTERNATIONAL = 1.35;
  var COORD_DECIMALS = 3;

  function marketShape(rng, base) {
    var stretchX = 0.75 + rng.nextFloat() * 0.9;
    var stretchY = 0.75 + rng.nextFloat() * 0.9;
    var centreCount = 2 + Math.floor(rng.nextFloat() * 3);
    var centres = [];
    for (var index = 0; index < centreCount; index += 1) {
      var offset = index === 0 ? 0 : 0.34;
      centres.push([
        rng.jitter(base * offset) * stretchY,
        rng.jitter(base * offset) * stretchX * 1.3,
        0.45 + rng.nextFloat(),
      ]);
    }
    return { stretchX: stretchX, stretchY: stretchY, centres: centres };
  }

  function interpolate(values, position) {
    if (!values.length) return 0;
    if (position <= 0) return values[0];
    if (position >= values.length - 1) return values[values.length - 1];
    var low = Math.floor(position);
    var weight = position - low;
    return values[low] * (1 - weight) + values[low + 1] * weight;
  }

  function cumulativeArrival(ramp, lag) {
    var span = Math.max(ramp.length - 1, 1);
    var offset = lag * span;
    var out = [];
    for (var index = 0; index < ramp.length; index += 1) {
      if (index < offset) { out.push(0); continue; }
      var local = (index - offset) / Math.max(span - offset, 1e-9);
      out.push(interpolate(ramp, local * span));
    }
    var peak = out[out.length - 1] || 1;
    var running = 0;
    for (var i = 0; i < out.length; i += 1) {
      running = Math.max(running, out[i] / peak);
      out[i] = running;
    }
    return out;
  }

  function scatterOrders(rows, salt, ramp) {
    var points = [];
    rows.forEach(function (row) {
      var rng = new Lcg((row.seed ^ stringSeed(salt)) >>> 0);
      var base = row.country === 'United States' ? SPREAD_DEGREES : SPREAD_INTERNATIONAL;
      var shape = marketShape(rng, base);
      var centres = shape.centres;
      var pullTotal = centres.reduce(function (a, c) { return a + c[2]; }, 0);
      var arrival = ramp && ramp.length ? cumulativeArrival(ramp, row.ramp_lag) : null;
      var aov = row.aov;

      for (var n = 0; n < row.orders; n += 1) {
        var pick = rng.nextFloat() * pullTotal;
        var running = 0;
        var centre = centres[centres.length - 1];
        for (var c = 0; c < centres.length; c += 1) {
          running += centres[c][2];
          if (pick < running) { centre = centres[c]; break; }
        }

        var dx = 0;
        var dy = 0;
        for (var attempt = 0; attempt < 12; attempt += 1) {
          dx = rng.nextFloat() * 2 - 1;
          dy = rng.nextFloat() * 2 - 1;
          if (dx * dx + dy * dy <= 1) break;
          if (attempt === 11) { dx = 0; dy = 0; }
        }

        var reach = rng.nextFloat();
        reach *= reach;
        if (rng.nextFloat() < 0.05) reach *= 3 + rng.nextFloat() * 4;

        var spread = (rng.nextFloat() + rng.nextFloat() + rng.nextFloat()) / 3;
        var value = aov * (0.45 + spread * 1.1);
        if (rng.nextFloat() < 0.04) value *= 1.8 + rng.nextFloat() * 2.2;

        var point = {
          lat: roundHalfUp(row.lat + centre[0] + dy * base * reach * shape.stretchY,
                           COORD_DECIMALS),
          lon: roundHalfUp(row.lon + centre[1] + dx * base * reach * shape.stretchX * 1.3,
                           COORD_DECIMALS),
          value: roundHalfUp(value, 2),
        };
        if (arrival) {
          var u = rng.nextFloat();
          var month = arrival.length - 1;
          for (var m = 0; m < arrival.length; m += 1) {
            if (u <= arrival[m]) { month = m; break; }
          }
          point.month = month;
        }
        points.push(point);
      }
    });
    return points;
  }

  function rfmPoints(params, salt) {
    if (!params) return [];
    var rng = new Lcg((params.seed ^ stringSeed(salt)) >>> 0);
    var sample = params.sample;
    var window = params.window_days;
    var meanSpend = params.mean_spend;
    var decay = params.repeat_decay;
    var tiers = CFG.valueTiers.map(function (tier) { return tier.name; });

    var points = [];
    for (var n = 0; n < sample; n += 1) {
      var frequency = 1;
      while (frequency < 24 && rng.nextFloat() < decay) frequency += 1;

      var pull = rng.nextFloat();
      pull *= pull;
      var recency;
      if (rng.nextFloat() < 0.34) {
        recency = (0.35 + rng.nextFloat() * 0.65) * window;
      } else {
        recency = pull * window / (0.6 + 0.4 * frequency);
      }
      recency = Math.min(recency, window);

      var magnitude = 0.55 + rng.nextFloat() * 0.9;
      for (var k = 0; k < 3; k += 1) {
        if (rng.nextFloat() < 0.28) magnitude *= 1.35 + rng.nextFloat() * 1.4;
      }
      var spend = meanSpend * frequency * magnitude * 0.62;

      points.push({
        recency: roundHalfUp(recency, 1),
        frequency: frequency,
        spend: roundHalfUp(spend, 2),
      });
    }

    var ordered = points.map(function (p) { return p.spend; })
                        .sort(function (a, b) { return a - b; });
    var cutIndex = Math.min(Math.floor(ordered.length * CFG.rfm.championPercentile),
                            ordered.length - 1);
    var championSpend = ordered.length ? ordered[cutIndex] : 0;

    points.forEach(function (point) {
      var recent = point.recency <= window * CFG.rfm.recencyCut;
      var frequent = point.frequency >= CFG.rfm.frequencyCut;
      if (recent && frequent) point.tier = point.spend >= championSpend ? tiers[0] : tiers[1];
      else if (recent) point.tier = tiers[2];
      else if (frequent) point.tier = tiers[3];
      else point.tier = tiers[4];
    });
    return points;
  }

  function orderCloud(level, ramp) {
    var key = state.brand + '|' + level + '|' + (ramp ? 'ramp' : 'flat');
    if (!cache.orders[key]) {
      var markets = aggregateByLevel(bundle().locations, level);
      cache.orders[key] = { markets: markets, points: scatterOrders(markets, state.brand, ramp) };
    }
    return cache.orders[key];
  }

  function customerCloud() {
    if (!cache.rfm[state.brand]) {
      cache.rfm[state.brand] = rfmPoints(bundle().value_params, state.brand);
    }
    return cache.rfm[state.brand];
  }

  // ======================================================================
  // Shell
  // ======================================================================
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function control(label, node, grow) {
    var wrap = el('div', 'tp-control' + (grow ? ' tp-control--grow' : ''));
    wrap.appendChild(el('label', 'tp-control-label', label));
    wrap.appendChild(node);
    return wrap;
  }

  function select(id, options, value, onChange) {
    var node = el('select', 'tp-select');
    node.id = id;
    options.forEach(function (option) {
      var item = el('option', null, option.label);
      item.value = option.value;
      if (option.value === value) item.selected = true;
      node.appendChild(item);
    });
    node.addEventListener('change', function () { onChange(node.value); });
    return node;
  }

  function segmented(name, options, value, onChange) {
    var wrap = el('div', 'tp-segmented');
    options.forEach(function (option) {
      var label = el('label', 'tp-segmented-label');
      var input = el('input', 'tp-segmented-input');
      input.type = 'radio';
      input.name = name;
      input.value = option.value;
      input.checked = option.value === value;
      input.addEventListener('change', function () { onChange(option.value); });
      label.appendChild(input);
      label.appendChild(document.createTextNode(option.label));
      wrap.appendChild(label);
    });
    return wrap;
  }

  function checkbox(label, checked, onChange) {
    var wrap = el('label', 'tp-checklabel');
    var input = el('input', 'tp-checkbox');
    input.type = 'checkbox';
    input.checked = checked;
    input.addEventListener('change', function () { onChange(input.checked); });
    wrap.appendChild(input);
    wrap.appendChild(document.createTextNode(label));
    return wrap;
  }

  function card(spec) {
    var node = el('section', 'tp-card');
    var header = el('div', 'tp-card-header');
    header.appendChild(el('h3', 'tp-card-title', spec.title));
    if (spec.subtitle) header.appendChild(el('p', 'tp-card-subtitle', spec.subtitle));
    node.appendChild(header);
    (spec.build || []).forEach(function (build) {
      var child = build();
      if (child) node.appendChild(child);
    });
    return node;
  }

  function chart(id, heightKey) {
    var node = el('div', 'tp-chart');
    node.id = id;
    node.style.height = CFG.chartHeights[heightKey] + 'px';
    return node;
  }

  function controls(children) {
    var wrap = el('div', 'tp-controls');
    children.forEach(function (child) { wrap.appendChild(child); });
    return wrap;
  }

  function statsSlot(id) {
    var node = el('div', 'tp-stats');
    node.id = id;
    return node;
  }

  function renderStats(id, rows) {
    var host = document.getElementById(id);
    if (!host) return;
    host.innerHTML = '';
    rows.forEach(function (row) {
      var block = el('div', 'tp-stat');
      block.appendChild(el('div', 'tp-stat-label', row.label));
      block.appendChild(el('div', 'tp-stat-value', row.value));
      if (row.note) block.appendChild(el('div', 'tp-stat-note', row.note));
      host.appendChild(block);
    });
  }

  var METRIC_OPTIONS = null;

  function metricOptions(keys) {
    return keys.map(function (key) { return { value: key, label: metricLabel(key) }; });
  }

  var GRAIN_OPTIONS = [
    { value: 'daily', label: 'Daily' }, { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' }, { value: 'quarterly', label: 'Quarterly' },
  ];
  var LEVEL_OPTIONS = [
    { value: 'city', label: 'City' }, { value: 'region', label: 'State / Region' },
    { value: 'country', label: 'Country' },
  ];

  // Each view names the cards it holds. The Dash page and this file describe the
  // same nine views; keeping the description declarative on both sides is what
  // makes a drift visible when they are read side by side.
  function viewSpecs() {
    return {
      revenue: [
        { title: 'Trading Performance',
          subtitle: 'Two metrics on independent axes with the promotion calendar '
                  + 'overlaid, and outliers marked in place — so a spike can be '
                  + 'read against what ran that week.',
          build: [
            function () {
              return controls([
                control('Left axis', select('tp-trend-left', METRIC_OPTIONS,
                  state.trend.left, function (v) { state.trend.left = v; renderView(); })),
                control('Right axis', select('tp-trend-right', METRIC_OPTIONS,
                  state.trend.right, function (v) { state.trend.right = v; renderView(); })),
                control('Interval', select('tp-trend-grain', GRAIN_OPTIONS,
                  state.trend.grain, function (v) { state.trend.grain = v; renderView(); })),
                (function () {
                  var list = el('div', 'tp-checklist');
                  list.appendChild(checkbox('Promotion calendar', state.trend.events,
                    function (on) { state.trend.events = on; renderView(); }));
                  list.appendChild(checkbox('Outliers', state.trend.anomalies,
                    function (on) { state.trend.anomalies = on; renderView(); }));
                  return control('Annotate', list);
                }()),
              ]);
            },
            function () { return chart('tp-trend', 'trend'); },
          ] },
        { title: 'Detected Anomalies',
          subtitle: 'Days that sit far from their own trailing level, in robust z '
                  + 'units. Median and MAD rather than mean and standard deviation, '
                  + 'so one large spike does not raise the bar past every other one.',
          build: [function () {
            var node = el('div', 'tp-log');
            node.id = 'tp-anomaly-log';
            return node;
          }] },
      ],
      drivers: [
        { title: 'What Moved Revenue',
          subtitle: 'Revenue is exactly site visits x conversion rate x average '
                  + 'order value, so the change against the prior period splits by '
                  + 'substituting one factor at a time. The bars sum to the total '
                  + 'with no residual.',
          build: [
            function () {
              var node = el('div', 'tp-callout');
              node.id = 'tp-driver-note';
              return node;
            },
            function () { return chart('tp-driver', 'driver'); },
          ] },
        { title: 'How the Metrics Move Together',
          subtitle: 'Every pair of core metrics, coloured by position in the window. '
                  + 'A widening cone means the spread grows with the level, a hook '
                  + 'means saturation, and a detached cluster is usually the '
                  + 'promotion calendar.',
          build: [function () { return chart('tp-splom', 'splom'); }] },
      ],
      category: [
        { title: 'Category Contribution to the Change',
          subtitle: 'Which parts of the catalogue carried the revenue change against '
                  + 'the prior period, largest mover first.',
          build: [function () {
            return chart('tp-category-waterfall', 'category_waterfall');
          }] },
        { title: 'Category Mix Over Time',
          subtitle: 'How the catalogue has rebalanced month by month.',
          build: [
            function () {
              return controls([control('Measure', segmented('tp-category-mode', [
                { value: 'share', label: 'Share of revenue' },
                { value: 'absolute', label: 'Revenue' },
              ], state.categoryMode, function (v) {
                state.categoryMode = v; renderView();
              }))]);
            },
            function () { return chart('tp-category-share', 'category_share'); },
          ] },
      ],
      cohorts: [
        { title: 'Cohort Retention',
          subtitle: 'Share of each acquisition month that ordered again, by months '
                  + 'since their first order. A triangle rather than a rectangle: a '
                  + 'cohort acquired last month has one observed month, and the '
                  + 'unobserved cells stay blank instead of being filled with zero.',
          build: [
            function () { return statsSlot('tp-cohort-stats'); },
            function () { return chart('tp-cohort', 'cohort'); },
          ] },
        { title: 'Retention Curves',
          subtitle: 'The same data read as curves. Recent cohorts are drawn darkest, '
                  + 'so a change in the shape of the acquisition base shows without '
                  + 'reading numbers out of cells.',
          build: [function () { return chart('tp-cohort-curves', 'cohort_curves'); }] },
      ],
      value: [
        { title: 'Recency, Frequency and Spend',
          subtitle: 'One point per customer: how long since their last order, how '
                  + 'many they have placed, and — as marker area — what they have '
                  + 'spent. The four quadrants are labelled because that is the part '
                  + 'anyone acts on.',
          build: [
            function () { return statsSlot('tp-value-stats'); },
            function () { return chart('tp-rfm', 'rfm'); },
          ] },
        { title: 'Revenue Concentration',
          subtitle: 'Share of revenue by customer spend decile, with the cumulative '
                  + 'curve. A mean spend figure hides this entirely.',
          build: [function () { return chart('tp-decile', 'decile'); }] },
      ],
      channels: [
        { title: 'Where Orders Are Placed',
          subtitle: 'Revenue by order channel, month by month.',
          build: [
            function () {
              return controls([control('Measure', segmented('tp-channel-mode', [
                { value: 'absolute', label: 'Revenue' },
                { value: 'share', label: 'Share' },
              ], state.channelMode, function (v) {
                state.channelMode = v; renderView();
              }))]);
            },
            function () { return chart('tp-channel-area', 'channel_area'); },
          ] },
        { title: 'Acquisition Source Value',
          subtitle: 'First-order and repeat revenue stacked separately, with '
                  + 'acquisition spend marked. A source that looks expensive on '
                  + 'first orders alone can be the best one in the portfolio once '
                  + 'its customers come back.',
          build: [function () { return chart('tp-source-bars', 'source_bars'); }] },
        { title: 'Attribution Detail',
          subtitle: 'Customers acquired, what they returned, and what they cost.',
          build: [function () {
            var node = el('div', 'tp-table');
            node.id = 'tp-source-table';
            return node;
          }] },
      ],
      promotions: [
        { title: 'Event Study',
          subtitle: 'Every occurrence of a promotion type aligned on the day it ran '
                  + 'and indexed to the day before, so the answer is a shape: whether '
                  + 'the lift is instant or builds, whether it decays back to baseline '
                  + 'or leaves a step, and whether the days before show pull-forward. '
                  + 'The band is a 95% interval across occurrences.',
          build: [
            function () { return statsSlot('tp-promo-stats'); },
            function () {
              var kinds = Object.keys(CFG.eventKinds);
              var picker = el('div', 'tp-checklist');
              kinds.forEach(function (kind) {
                picker.appendChild(checkbox(kind, state.study.kinds.indexOf(kind) !== -1,
                  function (on) {
                    if (on) state.study.kinds.push(kind);
                    else state.study.kinds = state.study.kinds.filter(function (k) {
                      return k !== kind;
                    });
                    renderView();
                  }));
              });
              return controls([
                control('Response metric', select('tp-study-metric',
                  metricOptions(['revenue', 'orders', 'visits', 'conversion', 'aov']),
                  state.study.metric, function (v) {
                    state.study.metric = v; renderView();
                  })),
                control('Promotion types (all if none ticked)', picker, true),
              ]);
            },
            function () { return chart('tp-event-study', 'event_study'); },
          ] },
        { title: 'Promoted Days Against Baseline',
          subtitle: 'Promoted days compared with the non-promoted days of the same '
                  + 'window. Measured against an annual average, a November promotion '
                  + 'would be credited with November.',
          build: [function () { return chart('tp-promo-bars', 'promo_bars'); }] },
        { title: 'Discount Codes',
          subtitle: 'Revenue kept against the discount given back, by code.',
          build: [function () { return chart('tp-discount', 'discount'); }] },
      ],
      fulfillment: [
        { title: 'Where Orders Ship',
          subtitle: 'Bubble size is order volume and colour is average order value, '
                  + 'so a market that is large and cheap reads differently from one '
                  + 'that is small and rich.',
          build: [
            function () { return statsSlot('tp-geo-stats'); },
            function () {
              var hint = el('div', 'tp-hint');
              hint.id = 'tp-map-hint';
              return controls([
                control('Display', select('tp-map-display',
                  CFG.map.displays, state.map.display, function (v) {
                    state.map.display = v; renderView();
                  })),
                control('Level', select('tp-map-level', LEVEL_OPTIONS, state.map.level,
                  function (v) { state.map.level = v; renderView(); })),
                hint,
              ]);
            },
            function () { return chart('tp-map', 'map'); },
          ] },
        { title: 'Order Footprint by Month',
          subtitle: 'Every order placed up to the end of the selected month, one '
                  + 'marker each. Individual orders rather than market bubbles: '
                  + 'resizing blobs shows a market growing, but only points can show '
                  + 'the footprint spreading into new ground.',
          build: [
            function () { return buildTransport(); },
            function () {
              var node = el('div', 'tp-readout');
              node.id = 'tp-growth-readout';
              return node;
            },
            function () { return chart('tp-growth', 'growth_map'); },
          ] },
        { title: 'Largest Markets',
          subtitle: 'Ordered by volume, coloured by average order value.',
          build: [function () { return chart('tp-market-bars', 'market_bars'); }] },
      ],
      returns: [
        { title: 'Returns Over Time',
          subtitle: 'Counts as bars, rate as a line. The rate is summed returns over '
                  + 'summed orders per bucket — averaging daily rates would let a '
                  + 'quiet Tuesday outvote a sale week.',
          build: [
            function () { return statsSlot('tp-return-stats'); },
            function () {
              return controls([control('Interval', select('tp-return-grain',
                GRAIN_OPTIONS.slice(1), state.returnGrain, function (v) {
                  state.returnGrain = v; renderView();
                }))]);
            },
            function () { return chart('tp-return-trend', 'return_trend'); },
          ] },
        { title: 'Return Rate by Category',
          subtitle: 'Where the returns concentrate, and what value is at stake.',
          build: [function () { return chart('tp-return-category', 'return_category'); }] },
        { title: 'Why Orders Come Back',
          subtitle: 'Returned value by stated reason.',
          build: [function () { return chart('tp-return-reason', 'return_reason'); }] },
      ],
    };
  }

  function growthMonths() {
    return bundle().monthly.map(function (row) { return row.period; });
  }

  function buildTransport() {
    var months = growthMonths();
    var wrap = el('div', 'tp-playback');

    var button = el('button', 'tp-play-button', '▶  Play');
    button.id = 'tp-growth-play';
    button.type = 'button';
    button.addEventListener('click', function () {
      setGrowthPlaying(state.growthTimer === null);
    });

    var scrub = el('div', 'tp-scrub tp-scrub--native');
    var input = el('input');
    input.id = 'tp-growth-month';
    input.type = 'range';
    input.min = '0';
    input.max = String(months.length - 1);
    input.step = '1';
    input.value = String(state.growthMonth === null ? months.length - 1 : state.growthMonth);
    input.addEventListener('input', function () {
      // Scrubbing is a deliberate act; keeping playback running would fight it.
      setGrowthPlaying(false);
      state.growthMonth = Number(input.value);
      renderGrowth();
    });

    var marks = el('div', 'tp-scrub-marks');
    marks.id = 'tp-growth-marks';
    months.forEach(function (month, index) {
      if (index % 6 === 0 || index === months.length - 1) {
        marks.appendChild(el('span', null, month));
      }
    });

    scrub.appendChild(input);
    scrub.appendChild(marks);
    wrap.appendChild(button);
    wrap.appendChild(scrub);
    return wrap;
  }

  function setGrowthPlaying(playing) {
    var button = document.getElementById('tp-growth-play');
    if (state.growthTimer !== null) {
      clearInterval(state.growthTimer);
      state.growthTimer = null;
    }
    if (playing) {
      var months = growthMonths();
      state.growthTimer = setInterval(function () {
        var current = state.growthMonth === null ? months.length - 1 : state.growthMonth;
        state.growthMonth = current >= months.length - 1 ? 0 : current + 1;
        var input = document.getElementById('tp-growth-month');
        if (input) input.value = String(state.growthMonth);
        renderGrowth();
      }, 420);
    }
    if (button) button.textContent = playing ? '❚❚  Pause' : '▶  Play';
  }

  // ======================================================================
  // Rendering — figures
  // ======================================================================
  function addPromotionOverlay(traces, layout, bnd, lo, hi, grain) {
    var window_ = {};
    DB.dates.slice(lo, hi).forEach(function (iso) { window_[iso] = true; });
    var grouped = {};
    bnd.events.forEach(function (event) {
      if (!window_[event.date]) return;
      var position = bucketLabel(event.date, grain);
      if (!grouped[event.kind]) grouped[event.kind] = [];
      grouped[event.kind].push(position);
    });

    layout.shapes = layout.shapes || [];
    Object.keys(grouped).forEach(function (kind) {
      var colour = CFG.eventKinds[kind].color;
      grouped[kind].forEach(function (position) {
        layout.shapes.push({
          type: 'line', xref: 'x', yref: 'paper',
          x0: position, x1: position, y0: 0, y1: 1,
          line: { color: soft(colour, 0.42), width: 1, dash: 'dot' },
        });
      });
      traces.push({
        type: 'scatter', x: grouped[kind], y: grouped[kind].map(function () { return null; }),
        name: kind, mode: 'markers',
        marker: { color: colour, size: 8, symbol: 'triangle-down' },
        hoverinfo: 'skip', showlegend: true,
      });
    });
  }

  function addAnomalyCallouts(traces, layout, labels, values, key, kind) {
    var found = detectAnomalies(values, labels);
    if (!found.length) return;
    traces.push({
      type: 'scatter', mode: 'markers', name: 'Outlier',
      x: found.map(function (a) { return a.date; }),
      y: found.map(function (a) { return a.value; }),
      marker: { size: 11, color: 'rgba(0,0,0,0)',
                line: { color: CFG.negative, width: 1.8 } },
      customdata: found.map(function (a) { return a.z; }),
      hovertemplate: '%{x}<br>' + metricLabel(key) + ': ' + hoverNumber(kind)
                   + '<br>%{customdata:+.1f} robust z<extra>Outlier</extra>',
    });
    layout.annotations = layout.annotations || [];
    found.slice().sort(function (a, b) { return Math.abs(b.z) - Math.abs(a.z); })
      .slice(0, 4).forEach(function (anomaly) {
        layout.annotations.push({
          x: anomaly.date, y: anomaly.value,
          text: (anomaly.pct >= 0 ? '+' : '') + group(anomaly.pct) + '%',
          showarrow: true, arrowhead: 0, arrowwidth: 1,
          arrowcolor: soft(CFG.negative, 0.55), ax: 0, ay: -26,
          font: { size: 10.5, color: CFG.negative, family: FONT_FAMILY },
          bgcolor: 'rgba(255,255,255,0.86)', borderpad: 2,
        });
      });
  }

  function renderTrend(bnd, lo, hi) {
    var left = state.trend.left;
    var right = state.trend.right;
    var grain = state.trend.grain;
    var a = grainSeries(bnd, left, lo, hi, grain);
    var b = grainSeries(bnd, right, lo, hi, grain);
    var leftKind = metricFormat(left);
    var rightKind = metricFormat(right);
    var leftColor = CFG.accentDeep;
    var rightColor = CFG.positive;

    var traces = [
      { type: 'scatter', x: a[0], y: a[1], name: metricLabel(left), mode: 'lines',
        line: { color: leftColor, width: 2.1 },
        fill: 'tozeroy', fillcolor: soft(leftColor, 0.10),
        hovertemplate: '%{x}<br>' + metricLabel(left) + ': ' + hoverNumber(leftKind)
                     + '<extra></extra>' },
      { type: 'scatter', x: b[0], y: b[1], name: metricLabel(right), mode: 'lines',
        yaxis: 'y2', line: { color: rightColor, width: 1.9 },
        hovertemplate: '%{x}<br>' + metricLabel(right) + ': ' + hoverNumber(rightKind)
                     + '<extra></extra>' },
    ];

    var layout = baseLayout(CFG.chartHeights.trend, {
      margin: { l: 66, r: 66, t: 56, b: 46 },
      xaxis: { title: null },
      yaxis: deepMerge({ title: { text: metricLabel(left) },
                         tickfont: { color: leftColor } }, axisTick(leftKind)),
      yaxis2: deepMerge({
        title: { text: metricLabel(right), font: { size: 11.5, color: rightColor } },
        overlaying: 'y', side: 'right', showgrid: false,
        tickfont: { size: 11, color: rightColor }, automargin: true,
      }, axisTick(rightKind)),
      hovermode: 'x unified',
    });

    if (state.trend.events) addPromotionOverlay(traces, layout, bnd, lo, hi, grain);
    if (state.trend.anomalies && grain === 'daily') {
      addAnomalyCallouts(traces, layout, a[0], a[1], left, leftKind);
    }
    draw('tp-trend', traces, layout);
  }

  function nearestEvent(bnd, iso, span) {
    span = span === undefined ? 3 : span;
    var index = DB.dates.indexOf(iso);
    if (index < 0) return null;
    var best = null;
    bnd.events.forEach(function (event) {
      var delta = index - event.day_index;
      if (delta >= 0 && delta <= span && (best === null || delta < best[0])) {
        best = [delta, event.kind];
      }
    });
    return best ? best[1] : null;
  }

  function renderAnomalyLog(bnd, lo, hi) {
    var host = document.getElementById('tp-anomaly-log');
    if (!host) return;
    var dates = DB.dates.slice(lo, hi);
    var rows = [];
    CFG.anomalyMetrics.forEach(function (key) {
      var values = seriesFor(bnd, key).slice(lo, hi);
      detectAnomalies(values, dates).forEach(function (anomaly) {
        rows.push({
          date: anomaly.date, metric: metricLabel(key),
          value: fmtValue(anomaly.value, metricFormat(key)),
          baseline: fmtValue(anomaly.baseline, metricFormat(key)),
          pct: anomaly.pct, z: anomaly.z, direction: anomaly.direction,
          context: nearestEvent(bnd, anomaly.date),
        });
      });
    });
    rows.sort(function (a, b) { return Math.abs(b.z) - Math.abs(a.z); });
    var total = rows.length;
    rows = rows.slice(0, 8);

    host.innerHTML = '';
    if (!rows.length) {
      host.appendChild(el('p', 'tp-empty', 'Nothing in this window sits far enough '
        + 'from its own trailing level to flag.'));
      return;
    }

    var list = el('ol', 'tp-log-list');
    rows.forEach(function (row) {
      var item = el('li', 'tp-log-item');
      var head = el('div', 'tp-log-head');
      head.appendChild(el('span', 'tp-log-date', row.date));
      head.appendChild(el('span', 'tp-log-metric', row.metric));
      item.appendChild(head);

      var body = el('div', 'tp-log-body');
      body.appendChild(el('span', 'tp-log-value', row.value));
      body.appendChild(el('span', 'tp-log-baseline', ' against a ' + row.baseline + ' baseline'));
      item.appendChild(body);

      var foot = el('div', 'tp-log-foot');
      foot.appendChild(el('span', 'tp-log-delta tp-log-delta--'
        + (row.direction === 'high' ? 'up' : 'down'),
        (row.pct >= 0 ? '+' : '') + group(row.pct, 1) + '%'));
      foot.appendChild(el('span', 'tp-log-note',
        (row.z >= 0 ? '+' : '') + group(row.z, 1) + ' robust z'
        + (row.context ? ' · alongside ' + row.context
                       : ' · no promotion within three days')));
      item.appendChild(foot);
      list.appendChild(item);
    });
    host.appendChild(list);
    if (total > rows.length) {
      host.appendChild(el('p', 'tp-log-footer', 'Showing the ' + rows.length
        + ' largest of ' + total + ' flagged points across five metrics.'));
    }
  }

  function renderDrivers(bnd, lo, hi) {
    var walk = driverDecomposition(bnd, lo, hi);
    var note = document.getElementById('tp-driver-note');
    if (!walk.terms.length) {
      if (note) note.textContent = 'Not enough history for a prior period.';
      drawEmpty('tp-driver', 'Not enough history for a prior period.',
                CFG.chartHeights.driver);
      return;
    }

    if (note) {
      var biggest = walk.terms.slice().sort(function (a, b) {
        return Math.abs(b.contribution) - Math.abs(a.contribution);
      })[0];
      var share = Math.abs(biggest.contribution) / Math.max(Math.abs(walk.change), 1e-9);
      note.textContent = 'Revenue ' + (walk.change >= 0 ? 'rose' : 'fell') + ' '
        + fmtCompact(Math.abs(walk.change), 'money') + ' against the prior '
        + walk.span + ' days. ' + biggest.label + ' accounts for '
        + group(share * 100) + '% of the move.';
    }

    var labels = ['Prior period'].concat(walk.terms.map(function (t) { return t.label; }))
                                 .concat(['This period']);
    var measures = ['absolute'].concat(walk.terms.map(function () { return 'relative'; }))
                               .concat(['total']);
    var values = [walk.prior].concat(walk.terms.map(function (t) { return t.contribution; }))
                             .concat([walk.current]);
    var text = [fmtCompact(walk.prior, 'money')].concat(walk.terms.map(function (t) {
      return (t.contribution >= 0 ? '+' : '−') + fmtCompact(Math.abs(t.contribution), 'money');
    })).concat([fmtCompact(walk.current, 'money')]);
    var detail = ['Revenue in the equivalent window before this one'].concat(
      walk.terms.map(function (t) {
        var kind = metricFormat(t.key);
        return fmtValue(t.prior, kind) + ' → ' + fmtValue(t.current, kind);
      })).concat(['Revenue in the selected window']);

    draw('tp-driver', [{
      type: 'waterfall', orientation: 'v', measure: measures, x: labels, y: values,
      text: text, textposition: 'outside',
      textfont: { size: 11.5, color: CFG.surface.text },
      customdata: detail,
      connector: { line: { color: CFG.surface.border, width: 1 } },
      increasing: { marker: { color: CFG.positive } },
      decreasing: { marker: { color: CFG.negative } },
      totals: { marker: { color: CFG.neutral } },
      hovertemplate: '%{x}<br>%{customdata}<extra></extra>',
    }], baseLayout(CFG.chartHeights.driver, {
      margin: { l: 66, r: 26, t: 30, b: 56 },
      yaxis: deepMerge({ title: { text: 'Revenue' } }, axisTick('money')),
      xaxis: { tickangle: 0 },
      showlegend: false,
    }));
  }

  function renderSplom(bnd, lo, hi) {
    var dimensions = [];
    CFG.splomMetrics.forEach(function (key) {
      var values = seriesFor(bnd, key).slice(lo, hi);
      if (!values.some(function (v) { return v; })) return;
      dimensions.push({ label: metricLabel(key), values: values });
    });
    if (dimensions.length < 2) {
      drawEmpty('tp-splom', 'Not enough data in this window.', CFG.chartHeights.splom);
      return;
    }

    var span = dimensions[0].values.length;
    var reversed = CFG.sequential.slice().reverse();
    var scale = reversed.map(function (colour, index) {
      return [index / (reversed.length - 1), colour];
    });

    var layout = baseLayout(CFG.chartHeights.splom, {
      margin: { l: 78, r: 26, t: 22, b: 62 },
      dragmode: 'select',
    });
    // Splom generates one axis pair per dimension; style them all.
    for (var index = 1; index <= dimensions.length; index += 1) {
      var suffix = index === 1 ? '' : String(index);
      ['xaxis', 'yaxis'].forEach(function (prefix) {
        layout[prefix + suffix] = {
          gridcolor: CFG.surface.grid, zerolinecolor: CFG.surface.zeroline,
          linecolor: CFG.surface.border,
          tickfont: { size: 9.5, color: CFG.surface.text_muted },
          title: { font: { size: 10.5, color: CFG.surface.text_secondary } },
        };
      });
    }

    draw('tp-splom', [{
      type: 'splom', dimensions: dimensions,
      diagonal: { visible: false }, showupperhalf: false,
      marker: {
        size: 3.4,
        color: dimensions[0].values.map(function (_, index) { return index; }),
        colorscale: scale, opacity: 0.62, line: { width: 0 }, showscale: true,
        colorbar: {
          title: { text: 'Day in window', side: 'right',
                   font: { size: 11, color: CFG.surface.text_secondary } },
          thickness: 9, len: 0.55, y: 0.5, outlinewidth: 0,
          tickvals: [0, span - 1], ticktext: ['start', 'end'],
          tickfont: { size: 10, color: CFG.surface.text_muted },
        },
      },
      hoverinfo: 'skip',
    }], layout);
  }

  function categoryNames() {
    return CFG.categories.map(function (c) { return c.name; });
  }

  function categoryColor(name) {
    var found = CFG.categories.filter(function (c) { return c.name === name; })[0];
    return found ? found.color : CFG.neutral;
  }

  function renderCategoryWaterfall(bnd, lo, hi) {
    var span = hi - lo;
    var priorLo = Math.max(lo - span, 0);
    if (priorLo >= lo) {
      drawEmpty('tp-category-waterfall', 'Not enough history for a prior period.',
                CFG.chartHeights.category_waterfall);
      return;
    }
    var currentMonths = {};
    var priorMonths = {};
    DB.dates.slice(lo, hi).forEach(function (iso) { currentMonths[iso.slice(0, 7)] = true; });
    DB.dates.slice(priorLo, lo).forEach(function (iso) { priorMonths[iso.slice(0, 7)] = true; });

    var names = categoryNames();
    var current = {};
    var prior = {};
    names.forEach(function (name) { current[name] = 0; prior[name] = 0; });
    bnd.category_mix.forEach(function (row) {
      var target = currentMonths[row.period] ? current : (priorMonths[row.period] ? prior : null);
      if (!target) return;
      Object.keys(row.revenue).forEach(function (name) {
        target[name] = (target[name] || 0) + row.revenue[name];
      });
    });

    var moves = names.map(function (name) { return [name, current[name] - prior[name]]; })
      .sort(function (a, b) { return Math.abs(b[1]) - Math.abs(a[1]); });
    var priorTotal = names.reduce(function (a, n) { return a + prior[n]; }, 0);
    var currentTotal = names.reduce(function (a, n) { return a + current[n]; }, 0);

    draw('tp-category-waterfall', [{
      type: 'waterfall', orientation: 'v',
      measure: ['absolute'].concat(moves.map(function () { return 'relative'; })).concat(['total']),
      x: ['Prior period'].concat(moves.map(function (m) { return m[0]; })).concat(['This period']),
      y: [priorTotal].concat(moves.map(function (m) { return m[1]; })).concat([currentTotal]),
      text: [fmtCompact(priorTotal, 'money')].concat(moves.map(function (m) {
        return (m[1] >= 0 ? '+' : '−') + fmtCompact(Math.abs(m[1]), 'money');
      })).concat([fmtCompact(currentTotal, 'money')]),
      textposition: 'outside', textfont: { size: 11, color: CFG.surface.text },
      customdata: ['Revenue in the equivalent window before this one'].concat(
        moves.map(function (m) {
          return fmtCompact(prior[m[0]], 'money') + ' → ' + fmtCompact(current[m[0]], 'money');
        })).concat(['Revenue in the selected window']),
      connector: { line: { color: CFG.surface.border, width: 1 } },
      increasing: { marker: { color: CFG.positive } },
      decreasing: { marker: { color: CFG.negative } },
      totals: { marker: { color: CFG.neutral } },
      hovertemplate: '%{x}<br>%{customdata}<extra></extra>',
    }], baseLayout(CFG.chartHeights.category_waterfall, {
      margin: { l: 66, r: 26, t: 30, b: 74 },
      yaxis: deepMerge({ title: { text: 'Revenue' } }, axisTick('money')),
      xaxis: { tickangle: -22 },
      showlegend: false,
    }));
  }

  function stackedArea(id, rows, field, names, colorOf, normalise, heightKey, title) {
    var live = rows.filter(function (row) {
      return Object.keys(row[field]).some(function (name) { return row[field][name] > 0; });
    });
    if (!live.length) {
      drawEmpty(id, 'No revenue yet.', CFG.chartHeights[heightKey]);
      return;
    }
    var periods = live.map(function (row) { return row.period; });
    var traces = names.map(function (name) {
      return {
        type: 'scatter', mode: 'lines', name: name, x: periods,
        y: live.map(function (row) {
          var total = Object.keys(row[field]).reduce(function (a, key) {
            return a + row[field][key];
          }, 0) || 1;
          var value = row[field][name] || 0;
          return normalise ? value / total : value;
        }),
        stackgroup: 'mix',
        line: { width: 0.8, color: MARKER_LINE },
        fillcolor: colorOf(name),
        hovertemplate: '%{x}<br>' + name + ': '
                     + (normalise ? '%{y:.1%}' : '$%{y:,.0f}') + '<extra></extra>',
      };
    });
    draw(id, traces, baseLayout(CFG.chartHeights[heightKey], {
      margin: { l: 62, r: 24, t: 48, b: 40 },
      yaxis: deepMerge({ title: { text: normalise ? title.share : title.absolute } },
                       normalise ? { tickformat: '.0%' } : axisTick('money')),
      hovermode: 'x unified',
    }));
  }

  function renderCohorts(bnd) {
    var cohorts = bnd.cohorts;
    var periods = cohorts.periods;
    var sizes = cohorts.sizes;
    var live = [];
    sizes.forEach(function (size, index) { if (size > 0) live.push(index); });
    var observable = live.filter(function (index) {
      return cohorts.retention[index].slice(1).some(function (v) { return v !== null; });
    });

    if (!observable.length) {
      drawEmpty('tp-cohort', 'Cohorts are too recent to show a repeat rate yet.',
                CFG.chartHeights.cohort);
      drawEmpty('tp-cohort-curves', 'Cohorts are too recent to show a repeat rate yet.',
                CFG.chartHeights.cohort_curves);
      renderStats('tp-cohort-stats', []);
      return;
    }

    var rows = observable.slice(-24);
    var columns = Math.min(18, periods.length);
    var z = [];
    var text = [];
    var hover = [];
    rows.forEach(function (index) {
      var retention = cohorts.retention[index];
      var zRow = [];
      var textRow = [];
      var hoverRow = [];
      for (var k = 1; k < columns; k += 1) {
        var value = k < retention.length ? retention[k] : null;
        zRow.push(value);
        textRow.push(value === null ? '' : group(value * 100, 1));
        hoverRow.push(value === null ? '' :
          periods[index] + ' cohort · ' + group(sizes[index]) + ' customers<br>Month '
          + k + ': ' + group(value * 100, 1) + '% ordered again ('
          + group(value * sizes[index]) + ' customers)');
      }
      z.push(zRow);
      text.push(textRow);
      hover.push(hoverRow);
    });

    var xLabels = [];
    for (var k2 = 1; k2 < columns; k2 += 1) xLabels.push('M' + k2);

    draw('tp-cohort', [{
      type: 'heatmap', z: z, text: text, customdata: hover,
      x: xLabels,
      y: rows.map(function (index) {
        return periods[index] + '  (' + fmtCompact(sizes[index]) + ')';
      }),
      colorscale: CFG.retentionScale,
      texttemplate: '%{text}', textfont: { size: 9.5 },
      hovertemplate: '%{customdata}<extra></extra>',
      xgap: 2, ygap: 2, zmin: 0,
      colorbar: {
        title: { text: 'Repeat rate', side: 'right',
                 font: { size: 11, color: CFG.surface.text_secondary } },
        thickness: 9, len: 0.62, outlinewidth: 0, tickformat: '.0%',
        tickfont: { size: 10, color: CFG.surface.text_muted },
      },
    }], baseLayout(CFG.chartHeights.cohort, {
      margin: { l: 116, r: 30, t: 34, b: 42 },
      xaxis: { title: { text: 'Months since first order' }, side: 'top', showgrid: false },
      yaxis: { title: { text: 'Acquisition month (cohort size)' },
               autorange: 'reversed', showgrid: false },
    }));

    // Curves.
    var recent = observable.slice(-6);
    var traces = [];
    recent.forEach(function (index, order) {
      var retention = cohorts.retention[index].slice(1)
        .filter(function (v) { return v !== null; });
      if (retention.length < 2) return;
      var weight = order / Math.max(recent.length - 1, 1);
      var position = Math.min(Math.floor((1 - weight) * (CFG.sequential.length - 1)),
                              CFG.sequential.length - 1);
      traces.push({
        type: 'scatter', mode: 'lines', name: periods[index],
        x: retention.map(function (_, i) { return i + 1; }), y: retention,
        line: { color: CFG.sequential[position], width: 1.6 + weight * 1.2 },
        hovertemplate: periods[index] + ' cohort<br>Month %{x}: %{y:.1%}<extra></extra>',
      });
    });

    var maxColumns = Math.max.apply(null, observable.map(function (index) {
      return cohorts.retention[index].length;
    }));
    var average = [];
    for (var k3 = 1; k3 < maxColumns; k3 += 1) {
      var top = 0;
      var bottom = 0;
      observable.forEach(function (index) {
        var row = cohorts.retention[index];
        if (k3 < row.length && row[k3] !== null) {
          top += row[k3] * sizes[index];
          bottom += sizes[index];
        }
      });
      if (bottom > 0) average.push(top / bottom);
    }
    if (average.length) {
      traces.push({
        type: 'scatter', mode: 'lines', name: 'All cohorts',
        x: average.map(function (_, i) { return i + 1; }), y: average,
        line: { color: CFG.surface.text, width: 2.4, dash: 'dot' },
        hovertemplate: 'All cohorts<br>Month %{x}: %{y:.1%}<extra></extra>',
      });
    }

    draw('tp-cohort-curves', traces, baseLayout(CFG.chartHeights.cohort_curves, {
      margin: { l: 60, r: 24, t: 48, b: 44 },
      xaxis: { title: { text: 'Months since first order' }, dtick: 1 },
      yaxis: { title: { text: 'Repeat rate' }, tickformat: '.0%', rangemode: 'tozero' },
      hovermode: 'x unified',
    }));

    // Stats.
    function weighted(month) {
      var top = 0;
      var bottom = 0;
      observable.forEach(function (index) {
        var row = cohorts.retention[index];
        if (month < row.length && row[month] !== null) {
          top += row[month] * sizes[index];
          bottom += sizes[index];
        }
      });
      return bottom ? top / bottom : null;
    }
    var stats = [];
    [[1, 'Month 1 repeat rate'], [3, 'Month 3 repeat rate'],
     [6, 'Month 6 repeat rate']].forEach(function (pair) {
      var value = weighted(pair[0]);
      if (value !== null) stats.push({ label: pair[1], value: fmtValue(value, 'percent') });
    });
    stats.push({ label: 'Cohorts tracked', value: group(observable.length) });
    renderStats('tp-cohort-stats', stats);
  }

  function tierColor(name) {
    var found = CFG.valueTiers.filter(function (t) { return t.name === name; })[0];
    return found ? found.color : CFG.neutral;
  }

  function renderValue(bnd) {
    var points = customerCloud();
    if (!points.length) {
      drawEmpty('tp-rfm', 'No customers yet.', CFG.chartHeights.rfm);
      drawEmpty('tp-decile', 'No customers yet.', CFG.chartHeights.decile);
      renderStats('tp-value-stats', []);
      return;
    }

    var window_ = bnd.value_params.window_days;
    var maxSpend = Math.max.apply(null, points.map(function (p) { return p.spend; }));
    var cutX = window_ * CFG.rfm.recencyCut;

    var traces = CFG.valueTiers.map(function (tier) {
      var members = points.filter(function (p) { return p.tier === tier.name; });
      if (!members.length) return null;
      return {
        type: 'scatter', mode: 'markers', name: tier.name,
        x: members.map(function (p) { return p.recency; }),
        y: members.map(function (p) { return p.frequency + (p.spend % 7) / 22; }),
        marker: {
          size: members.map(function (p) {
            return 6 + 26 * Math.pow(p.spend / maxSpend, 0.55);
          }),
          color: tier.color, opacity: 0.66,
          line: { width: 0.6, color: MARKER_LINE },
        },
        customdata: members.map(function (p) { return [p.spend, p.frequency]; }),
        hovertemplate: '%{customdata[1]} orders · last order %{x:.0f} days ago'
                     + '<br>Lifetime spend $%{customdata[0]:,.0f}<extra>'
                     + tier.name + '</extra>',
      };
    }).filter(Boolean);

    var frequencies = points.map(function (p) { return p.frequency; })
                            .sort(function (a, b) { return a - b; });
    var upper = frequencies[Math.floor(frequencies.length * 0.992)];

    var layout = baseLayout(CFG.chartHeights.rfm, {
      margin: { l: 62, r: 26, t: 48, b: 52 },
      xaxis: { title: { text: 'Days since last order  ·  recent →' }, autorange: 'reversed' },
      yaxis: { title: { text: 'Lifetime orders' }, dtick: 1, rangemode: 'tozero' },
      legend: { title: { text: 'Marker area = lifetime spend   ',
                         font: { size: 11, color: CFG.surface.text_muted } } },
      shapes: [
        { type: 'line', xref: 'x', yref: 'paper', x0: cutX, x1: cutX, y0: 0, y1: 1,
          line: { color: CFG.surface.zeroline, width: 1, dash: 'dash' } },
        { type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: 1.5, y1: 1.5,
          line: { color: CFG.surface.zeroline, width: 1, dash: 'dash' } },
      ],
      annotations: CFG.rfm.quadrants.map(function (quadrant) {
        return {
          x: quadrant.recent ? cutX * 0.42 : cutX + (window_ - cutX) * 0.62,
          y: quadrant.frequent ? upper * 0.86 : 1.16,
          text: '<b>' + quadrant.label + '</b><br>'
              + "<span style='font-size:10px'>" + quadrant.note + '</span>',
          showarrow: false, align: 'center',
          font: { size: 12, color: CFG.surface.text, family: SERIF },
          bgcolor: 'rgba(250, 249, 247, 0.82)', borderpad: 5,
        };
      }),
    });
    draw('tp-rfm', traces, layout);

    // Deciles.
    var ordered = points.map(function (p) { return p.spend; })
                        .sort(function (a, b) { return b - a; });
    var total = sum(ordered) || 1;
    var size = Math.max(Math.floor(ordered.length / 10), 1);
    var shares = [];
    var cumulative = [];
    var running = 0;
    for (var index = 0; index < 10; index += 1) {
      var share = sum(ordered.slice(index * size, (index + 1) * size)) / total;
      running += share;
      shares.push(share);
      cumulative.push(running);
    }
    var labels = ['Top 10%'];
    for (var d = 1; d < 10; d += 1) labels.push(d * 10 + '–' + (d * 10 + 10) + '%');

    draw('tp-decile', [
      { type: 'bar', x: labels, y: shares, name: 'Share of revenue',
        marker: {
          color: shares.map(function (_, index) {
            return CFG.sequential[Math.min(Math.floor(index / 2), CFG.sequential.length - 1)];
          }),
          line: { width: 0.6, color: MARKER_LINE },
        },
        hovertemplate: '%{x}<br>%{y:.1%} of revenue<extra></extra>' },
      { type: 'scatter', x: labels, y: cumulative, name: 'Cumulative', yaxis: 'y2',
        mode: 'lines+markers',
        line: { color: CFG.surface.text, width: 1.8, dash: 'dot' },
        marker: { size: 5, color: CFG.surface.text },
        hovertemplate: '%{x}<br>%{y:.1%} cumulative<extra></extra>' },
    ], baseLayout(CFG.chartHeights.decile, {
      margin: { l: 58, r: 58, t: 48, b: 52 },
      xaxis: { title: null, tickangle: -20 },
      yaxis: { title: { text: 'Share of revenue' }, tickformat: '.0%' },
      yaxis2: { overlaying: 'y', side: 'right', showgrid: false, tickformat: '.0%',
                range: [0, 1.02],
                tickfont: { size: 11, color: CFG.surface.text_muted },
                title: { text: 'Cumulative',
                         font: { size: 11.5, color: CFG.surface.text_secondary } } },
      hovermode: 'x unified',
    }));

    var topDecile = sum(ordered.slice(0, size)) / total;
    var repeat = points.filter(function (p) { return p.frequency > 1; }).length / points.length;
    renderStats('tp-value-stats', [
      { label: 'Top 10% of customers', value: fmtValue(topDecile, 'percent'),
        note: 'of lifetime revenue' },
      { label: 'Repeat customers', value: fmtValue(repeat, 'percent'),
        note: 'ordered more than once' },
      { label: 'Median lifetime spend',
        value: fmtValue(ordered[Math.floor(ordered.length / 2)], 'money'),
        note: 'per customer' },
      { label: 'Mean lifetime orders',
        value: group(sum(points.map(function (p) { return p.frequency; })) / points.length, 2),
        note: 'per customer' },
    ]);
  }

  function renderChannels(bnd) {
    stackedArea('tp-channel-area', bnd.channel_mix, 'revenue',
      CFG.channels.map(function (c) { return c.name; }),
      function (name) {
        var found = CFG.channels.filter(function (c) { return c.name === name; })[0];
        return found ? found.color : CFG.neutral;
      },
      state.channelMode === 'share', 'channel_area',
      { share: 'Share', absolute: 'Revenue' });

    var rows = bnd.sources.slice().sort(function (a, b) { return a.revenue - b.revenue; });
    if (!rows.length) {
      drawEmpty('tp-source-bars', 'No attribution yet.', CFG.chartHeights.source_bars);
      return;
    }
    var names = rows.map(function (row) { return row.source; });
    draw('tp-source-bars', [
      { type: 'bar', orientation: 'h', name: 'First-order revenue', y: names,
        x: rows.map(function (row) { return row.first_order_revenue; }),
        marker: { color: CFG.accent, line: { width: 0.6, color: MARKER_LINE } },
        hovertemplate: '%{y}<br>First-order revenue $%{x:,.0f}<extra></extra>' },
      { type: 'bar', orientation: 'h', name: 'Repeat revenue', y: names,
        x: rows.map(function (row) { return row.repeat_revenue; }),
        marker: { color: CFG.positive, line: { width: 0.6, color: MARKER_LINE } },
        hovertemplate: '%{y}<br>Repeat revenue $%{x:,.0f}<extra></extra>' },
      { type: 'scatter', mode: 'markers', name: 'Acquisition spend', y: names,
        x: rows.map(function (row) { return row.spend; }),
        marker: { symbol: 'line-ns-open', size: 16, color: CFG.surface.text,
                  line: { width: 2 } },
        hovertemplate: '%{y}<br>Acquisition spend $%{x:,.0f}<extra></extra>' },
    ], baseLayout(CFG.chartHeights.source_bars, {
      margin: { l: 116, r: 26, t: 48, b: 44 },
      barmode: 'stack',
      xaxis: deepMerge({ title: { text: 'Revenue and spend' } }, axisTick('money')),
      yaxis: { title: null, showgrid: false },
    }));

    var host = document.getElementById('tp-source-table');
    if (!host) return;
    var headers = ['Source', 'New customers', 'Revenue', 'Repeat share', 'CAC', 'ROAS'];
    var table = el('table', 'tp-data-table');
    var thead = el('thead');
    var headRow = el('tr');
    headers.forEach(function (name, index) {
      var th = el('th', index === 0 ? 'tp-cell-left' : null, name);
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = el('tbody');
    bnd.sources.forEach(function (row) {
      var tr = el('tr');
      [
        row.source,
        group(row.new_customers),
        fmtCompact(row.revenue, 'money'),
        fmtValue(row.repeat_revenue / Math.max(row.revenue, 1e-9), 'percent'),
        row.cac ? fmtValue(row.cac, 'money2') : '—',
        row.spend > 0 ? fmtValue(row.revenue / row.spend, 'ratio') : '—',
      ].forEach(function (value, index) {
        tr.appendChild(el('td', index === 0 ? 'tp-cell-left' : null, value));
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    host.innerHTML = '';
    host.appendChild(table);
  }

  function renderPromotions(bnd, lo, hi) {
    var studies = eventStudy(bnd, state.study.metric, state.study.kinds);
    if (!studies.length) {
      drawEmpty('tp-event-study', 'Not enough repeat occurrences to average.',
                CFG.chartHeights.event_study);
    } else {
      var traces = [];
      studies.forEach(function (study) {
        traces.push({
          type: 'scatter', x: study.offsets.concat(study.offsets.slice().reverse()),
          y: study.upper.concat(study.lower.slice().reverse()),
          fill: 'toself', fillcolor: soft(study.color, 0.13),
          line: { width: 0 }, hoverinfo: 'skip', showlegend: false,
        });
        traces.push({
          type: 'scatter', mode: 'lines', x: study.offsets, y: study.mean,
          name: study.kind + '  (' + study.occurrences + ')',
          line: { color: study.color, width: 2 },
          hovertemplate: 'Day %{x:+d}<br>%{y:.2f}x the day before<extra>'
                       + study.kind + '</extra>',
        });
      });
      draw('tp-event-study', traces, baseLayout(CFG.chartHeights.event_study, {
        margin: { l: 62, r: 26, t: 54, b: 48 },
        xaxis: { title: { text: 'Days from promotion' }, dtick: 2, zeroline: false },
        yaxis: { title: { text: metricLabel(state.study.metric) + ', indexed to day −1' },
                 tickformat: '.2f' },
        hovermode: 'x unified',
        shapes: [
          { type: 'line', xref: 'x', yref: 'paper', x0: 0, x1: 0, y0: 0, y1: 1,
            line: { color: CFG.surface.zeroline, width: 1.2 } },
          { type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: 1, y1: 1,
            line: { color: CFG.surface.zeroline, width: 1, dash: 'dot' } },
        ],
        annotations: [{
          x: 0, y: 1, yref: 'paper', yanchor: 'bottom', text: 'promotion runs',
          showarrow: false, yshift: 6,
          font: { size: 10.5, color: CFG.surface.text_muted },
        }],
      }));
    }

    var split = promotionWindows(bnd, lo, hi);
    var on = split[0];
    var off = split[1];
    if (on.length < 3 || off.length < 3) {
      drawEmpty('tp-promo-bars', 'Not enough promoted days in this window.',
                CFG.chartHeights.promo_bars);
      renderStats('tp-promo-stats', []);
    } else {
      var perDay = function (indices, key) {
        if (isRatio(key)) {
          var pair = CFG.derived[key];
          var top = indices.reduce(function (a, i) { return a + bnd.series[pair[0]][i]; }, 0);
          var bottom = indices.reduce(function (a, i) { return a + bnd.series[pair[1]][i]; }, 0);
          return bottom ? top / bottom : 0;
        }
        var values = seriesFor(bnd, key);
        return indices.reduce(function (a, i) { return a + values[i]; }, 0) / indices.length;
      };
      var metrics = ['revenue', 'orders', 'aov', 'conversion'];
      var lifts = [];
      var hover = [];
      metrics.forEach(function (key) {
        var base = perDay(off, key);
        var promo = perDay(on, key);
        lifts.push(base ? promo / base - 1 : 0);
        var kind = metricFormat(key);
        hover.push(fmtValue(base, kind) + ' → ' + fmtValue(promo, kind) + ' per day');
      });

      draw('tp-promo-bars', [{
        type: 'bar', x: metrics.map(metricLabel), y: lifts, customdata: hover,
        marker: {
          color: lifts.map(function (v) { return v >= 0 ? CFG.positive : CFG.negative; }),
          line: { width: 0.6, color: MARKER_LINE },
        },
        text: lifts.map(function (v) {
          return (v >= 0 ? '+' : '') + group(v * 100, 1) + '%';
        }),
        textposition: 'outside', textfont: { size: 11.5, color: CFG.surface.text },
        hovertemplate: '%{x}<br>%{customdata}<extra></extra>',
      }], baseLayout(CFG.chartHeights.promo_bars, {
        margin: { l: 60, r: 26, t: 34, b: 44 },
        yaxis: { title: { text: 'Lift vs baseline days' }, tickformat: '+.0%' },
        xaxis: { title: null },
        showlegend: false,
        shapes: [{ type: 'line', xref: 'paper', yref: 'y', x0: 0, x1: 1, y0: 0, y1: 0,
                   line: { color: CFG.surface.zeroline, width: 1 } }],
      }));

      var revenue = seriesFor(bnd, 'revenue');
      var promoDay = on.reduce(function (a, i) { return a + revenue[i]; }, 0) / on.length;
      var baseDay = off.reduce(function (a, i) { return a + revenue[i]; }, 0) / off.length;
      renderStats('tp-promo-stats', [
        { label: 'Promoted days', value: group(on.length),
          note: 'of ' + group(on.length + off.length) + ' in window' },
        { label: 'Revenue per promoted day', value: fmtCompact(promoDay, 'money'),
          note: 'vs ' + fmtCompact(baseDay, 'money') + ' baseline' },
        { label: 'Incremental revenue',
          value: fmtCompact((promoDay - baseDay) * on.length, 'money'),
          note: 'above baseline days' },
        { label: 'Discount given back',
          value: fmtCompact(sum(bnd.series.discount_value.slice(lo, hi)), 'money'),
          note: 'across the whole window' },
      ]);
    }

    var codes = bnd.discounts.slice().sort(function (a, b) { return a.revenue - b.revenue; });
    if (!codes.length) {
      drawEmpty('tp-discount', 'No discount codes in use.', CFG.chartHeights.discount);
      return;
    }
    draw('tp-discount', [
      { type: 'bar', orientation: 'h', name: 'Revenue kept',
        y: codes.map(function (row) { return row.code; }),
        x: codes.map(function (row) { return row.revenue; }),
        marker: { color: CFG.neutral, line: { width: 0.6, color: MARKER_LINE } },
        hovertemplate: '%{y}<br>Revenue kept $%{x:,.0f}<extra></extra>' },
      { type: 'bar', orientation: 'h', name: 'Discount given',
        y: codes.map(function (row) { return row.code; }),
        x: codes.map(function (row) { return row.discount; }),
        marker: { color: CFG.accent, line: { width: 0.6, color: MARKER_LINE } },
        hovertemplate: '%{y}<br>Discount given $%{x:,.0f}<extra></extra>' },
    ], baseLayout(CFG.chartHeights.discount, {
      margin: { l: 96, r: 26, t: 48, b: 42 },
      barmode: 'stack',
      xaxis: deepMerge({ title: { text: 'Gross order value' } }, axisTick('money')),
      yaxis: { title: null, showgrid: false },
    }));
  }

  // --- Map ----------------------------------------------------------------
  function bubbleSizes(values, cap, floor) {
    cap = cap || 46;
    floor = floor || 6;
    var peak = Math.max.apply(null, values) || 1;
    return values.map(function (value) {
      return floor + (cap - floor) * Math.pow(value / peak, 0.5);
    });
  }

  function mapView(markets) {
    if (!markets.length) return { center: { lat: 39, lon: -98 }, zoom: 3.1 };
    var total = markets.reduce(function (a, m) { return a + m.orders; }, 0) || 1;
    return {
      center: {
        lat: markets.reduce(function (a, m) { return a + m.lat * m.orders; }, 0) / total,
        lon: markets.reduce(function (a, m) { return a + m.lon * m.orders; }, 0) / total,
      },
      zoom: 3.15,
    };
  }

  function mapLayout(markets, height, uirevision, overrides) {
    var view = mapView(markets);
    var layout = baseLayout(height || CFG.chartHeights.map, deepMerge({
      margin: { l: 0, r: 0, t: 0, b: 0 },
      map: { style: CFG.map.style, center: view.center, zoom: view.zoom },
      showlegend: false,
      uirevision: uirevision,
    }, overrides || {}));
    delete layout.xaxis;
    delete layout.yaxis;
    return layout;
  }

  function aovRange(markets) {
    if (!markets.length) return [0, 1, 0.5];
    var orders = markets.reduce(function (a, m) { return a + m.orders; }, 0) || 1;
    var mid = markets.reduce(function (a, m) { return a + m.aov * m.orders; }, 0) / orders;
    var values = markets.map(function (m) { return m.aov; });
    var reach = Math.max(Math.max.apply(null, values) - mid,
                         mid - Math.min.apply(null, values), 1e-6);
    return [mid - reach, mid + reach, mid];
  }

  var ORDER_VALUE_BANDS = 5;

  function bandPoints(points) {
    if (!points.length) return [];
    var ordered = points.map(function (p) { return p.value; })
                        .sort(function (a, b) { return a - b; });
    var low = ordered[Math.floor(ordered.length * 0.05)];
    var high = ordered[Math.min(Math.floor(ordered.length * 0.95), ordered.length - 1)];
    var step = (high - low) / ORDER_VALUE_BANDS;
    var buckets = [];
    for (var b = 0; b < ORDER_VALUE_BANDS; b += 1) buckets.push([]);
    points.forEach(function (point) {
      var index = step > 0 ? Math.floor((point.value - low) / step) : 0;
      buckets[Math.max(0, Math.min(index, ORDER_VALUE_BANDS - 1))].push(point);
    });
    var ramp = CFG.sequential.slice().reverse().slice(0, ORDER_VALUE_BANDS);
    var out = [];
    buckets.forEach(function (members, index) {
      if (!members.length) return;
      var lower = low + step * index;
      var upper = lower + step;
      var label;
      if (index === 0) label = 'under ' + fmtCompact(upper, 'money');
      else if (index === ORDER_VALUE_BANDS - 1) label = fmtCompact(lower, 'money') + ' and up';
      else label = fmtCompact(lower, 'money') + ' – ' + fmtCompact(upper, 'money');
      out.push({ label: label, color: ramp[index], members: members });
    });
    return out;
  }

  function renderMap(bnd) {
    var level = state.map.level;
    var display = state.map.display;
    var hint = document.getElementById('tp-map-hint');
    var hints = {
      market: 'One bubble per market, sized by orders and coloured by average order value.',
      orders: 'One marker per order, banded by order value.',
      density: 'Market boundaries dropped, so only where orders concentrate remains.',
    };
    if (hint) hint.textContent = hints[display] || '';

    var markets = aggregateByLevel(bnd.locations, level);
    if (!markets.length) {
      drawEmpty('tp-map', 'No orders in this view.', CFG.chartHeights.map);
      return;
    }

    if (display === 'market') {
      var range = aovRange(markets);
      draw('tp-map', [{
        type: 'scattermap', mode: 'markers',
        lat: markets.map(function (m) { return m.lat; }),
        lon: markets.map(function (m) { return m.lon; }),
        marker: {
          size: bubbleSizes(markets.map(function (m) { return m.orders; })),
          color: markets.map(function (m) { return m.aov; }),
          colorscale: CFG.aovScale, cmin: range[0], cmax: range[1], opacity: 0.82,
          colorbar: {
            title: { text: 'Average<br>order value', side: 'right',
                     font: { size: 11, color: CFG.surface.text_secondary } },
            thickness: 10, len: 0.6, x: 0.99, xanchor: 'right', outlinewidth: 0,
            tickprefix: '$', tickformat: ',.0f', bgcolor: 'rgba(255,255,255,0.72)',
            tickfont: { size: 10, color: CFG.surface.text_muted },
          },
        },
        text: markets.map(function (m) {
          return '<b>' + m.label + '</b><br>' + group(m.orders) + ' orders<br>'
               + fmtCompact(m.revenue, 'money') + ' revenue<br>'
               + fmtValue(m.aov, 'money2') + ' average order';
        }),
        hovertemplate: '%{text}<extra></extra>',
      }], mapLayout(markets, null, 'map-' + state.brand + '-' + level));
      return;
    }

    var cloud = orderCloud(level, null);
    if (display === 'density') {
      var reversed = CFG.sequential.slice().reverse();
      draw('tp-map', [{
        type: 'densitymap',
        lat: cloud.points.map(function (p) { return p.lat; }),
        lon: cloud.points.map(function (p) { return p.lon; }),
        radius: 11,
        colorscale: reversed.map(function (colour, index) {
          return [index / (reversed.length - 1), colour];
        }),
        showscale: false, hoverinfo: 'skip',
      }], mapLayout(markets, null, 'map-' + state.brand + '-density'));
      return;
    }

    draw('tp-map', bandPoints(cloud.points).map(function (band) {
      return {
        type: 'scattermap', mode: 'markers', name: band.label,
        lat: band.members.map(function (p) { return p.lat; }),
        lon: band.members.map(function (p) { return p.lon; }),
        marker: { size: 3.4, color: band.color, opacity: 0.5 },
        hoverinfo: 'skip',
      };
    }), mapLayout(markets, null, 'map-' + state.brand + '-orders', {
      showlegend: true,
      legend: {
        orientation: 'h', yanchor: 'top', y: 0.99, xanchor: 'left', x: 0.01,
        bgcolor: 'rgba(255,255,255,0.82)', borderwidth: 0,
        title: { text: 'Order value  ',
                 font: { size: 11, color: CFG.surface.text_secondary } },
        font: { size: 11, color: CFG.surface.text_secondary },
      },
    }));
  }

  function renderMarketBars(bnd) {
    var markets = aggregateByLevel(bnd.locations, state.map.level).slice(0, 12).reverse();
    if (!markets.length) {
      drawEmpty('tp-market-bars', 'No orders in this view.', CFG.chartHeights.market_bars);
      return;
    }
    var range = aovRange(markets);
    draw('tp-market-bars', [{
      type: 'bar', orientation: 'h',
      y: markets.map(function (m) { return m.name; }),
      x: markets.map(function (m) { return m.orders; }),
      marker: {
        color: markets.map(function (m) { return m.aov; }),
        colorscale: CFG.aovScale, cmin: range[0], cmax: range[1],
        line: { width: 0.6, color: MARKER_LINE },
      },
      customdata: markets.map(function (m) { return [m.aov, m.revenue]; }),
      hovertemplate: '<b>%{y}</b><br>%{x:,.0f} orders<br>'
                   + '$%{customdata[0]:,.2f} average order<br>'
                   + '$%{customdata[1]:,.0f} revenue<extra></extra>',
    }], baseLayout(CFG.chartHeights.market_bars, {
      margin: { l: 132, r: 26, t: 22, b: 44 },
      xaxis: { title: { text: 'Orders' }, tickformat: ',.0f' },
      yaxis: { title: null, showgrid: false },
      showlegend: false,
    }));
  }

  function renderGeoStats(bnd) {
    var markets = aggregateByLevel(bnd.locations, state.map.level);
    if (!markets.length) { renderStats('tp-geo-stats', []); return; }
    var orders = markets.reduce(function (a, m) { return a + m.orders; }, 0);
    var revenue = markets.reduce(function (a, m) { return a + m.revenue; }, 0);
    var topFive = markets.slice(0, 5).reduce(function (a, m) { return a + m.orders; }, 0)
                  / Math.max(orders, 1);
    renderStats('tp-geo-stats', [
      { label: 'Orders shipped', value: fmtCompact(orders),
        note: 'across ' + group(markets.length) + ' markets' },
      { label: 'Largest market', value: markets[0].name,
        note: fmtCompact(markets[0].orders) + ' orders' },
      { label: 'Top 5 concentration', value: fmtValue(topFive, 'percent'),
        note: 'of all orders' },
      { label: 'Blended order value',
        value: fmtValue(revenue / Math.max(orders, 1), 'money2'),
        note: 'across every market' },
    ]);
  }

  function renderGrowth() {
    var bnd = bundle();
    var months = growthMonths();
    if (state.growthMonth === null) state.growthMonth = months.length - 1;
    var monthIndex = Math.max(0, Math.min(state.growthMonth, months.length - 1));

    var ramp = bnd.monthly.map(function (row) { return row.frac; });
    var cloud = orderCloud(state.map.level, ramp);
    var shown = cloud.points.filter(function (point) { return point.month <= monthIndex; });

    draw('tp-growth', bandPoints(shown).map(function (band) {
      return {
        type: 'scattermap', mode: 'markers', name: band.label,
        lat: band.members.map(function (p) { return p.lat; }),
        lon: band.members.map(function (p) { return p.lon; }),
        marker: { size: 3.2, color: band.color, opacity: 0.5 },
        hoverinfo: 'skip',
      };
    }), mapLayout(cloud.markets, CFG.chartHeights.growth_map,
                  'growth-' + state.brand + '-' + state.map.level));

    var readout = document.getElementById('tp-growth-readout');
    if (readout) {
      var reached = cloud.markets.filter(function (market) {
        return market.ramp_lag * (months.length - 1) <= monthIndex;
      }).length;
      var value = shown.reduce(function (a, p) { return a + p.value; }, 0);
      readout.textContent = months[monthIndex] + ' · ' + group(shown.length)
        + ' orders placed across ' + group(reached) + ' of ' + group(cloud.markets.length)
        + ' markets — ' + group(shown.length / (cloud.points.length || 1) * 100, 1)
        + '% of every order in the dataset, worth ' + fmtCompact(value, 'money') + '.';
    }
  }

  function renderReturns(bnd, lo, hi) {
    var dates = DB.dates.slice(lo, hi);
    var grain = state.returnGrain;
    var rate = resampleRatio(dates, bnd.series.returns.slice(lo, hi),
                             bnd.series.orders.slice(lo, hi), grain);
    var counts = resample(dates, bnd.series.returns.slice(lo, hi), grain, 'sum');
    if (!rate[0].length) {
      drawEmpty('tp-return-trend', 'No returns in this window.',
                CFG.chartHeights.return_trend);
    } else {
      draw('tp-return-trend', [
        { type: 'bar', x: counts[0], y: counts[1], name: 'Returns',
          marker: { color: soft(CFG.neutral, 0.45), line: { width: 0 } },
          hovertemplate: '%{x}<br>%{y:,.0f} returns<extra></extra>' },
        { type: 'scatter', mode: 'lines', x: rate[0], y: rate[1], name: 'Return rate',
          yaxis: 'y2', line: { color: CFG.accent, width: 2.1 },
          hovertemplate: '%{x}<br>%{y:.2%} of orders<extra></extra>' },
      ], baseLayout(CFG.chartHeights.return_trend, {
        margin: { l: 60, r: 62, t: 48, b: 42 },
        yaxis: { title: { text: 'Returns' }, tickformat: ',.0f' },
        yaxis2: { overlaying: 'y', side: 'right', showgrid: false, tickformat: '.1%',
                  rangemode: 'tozero', tickfont: { size: 11, color: CFG.accent },
                  title: { text: 'Return rate', font: { size: 11.5, color: CFG.accent } } },
        hovermode: 'x unified',
      }));
    }

    var byCategory = bnd.returns.by_category.slice()
      .sort(function (a, b) { return a.rate - b.rate; });
    draw('tp-return-category', [{
      type: 'bar', orientation: 'h',
      y: byCategory.map(function (row) { return row.category; }),
      x: byCategory.map(function (row) { return row.rate; }),
      marker: {
        color: byCategory.map(function (row) { return categoryColor(row.category); }),
        line: { width: 0.6, color: MARKER_LINE },
      },
      text: byCategory.map(function (row) { return group(row.rate * 100, 1) + '%'; }),
      textposition: 'outside', textfont: { size: 11, color: CFG.surface.text },
      customdata: byCategory.map(function (row) { return row.returned_value; }),
      hovertemplate: '<b>%{y}</b><br>%{x:.2%} of revenue returned'
                   + '<br>$%{customdata:,.0f} at stake<extra></extra>',
    }], baseLayout(CFG.chartHeights.return_category, {
      margin: { l: 116, r: 44, t: 22, b: 42 },
      xaxis: { title: { text: 'Return rate' }, tickformat: '.0%' },
      yaxis: { title: null, showgrid: false },
      showlegend: false,
    }));

    var byReason = bnd.returns.by_reason.slice()
      .sort(function (a, b) { return a.value - b.value; });
    draw('tp-return-reason', [{
      type: 'bar', orientation: 'h',
      y: byReason.map(function (row) { return row.reason; }),
      x: byReason.map(function (row) { return row.value; }),
      marker: {
        color: byReason.map(function (row) {
          var found = CFG.returnReasons.filter(function (r) { return r.name === row.reason; })[0];
          return found ? found.color : CFG.neutral;
        }),
        line: { width: 0.6, color: MARKER_LINE },
      },
      customdata: byReason.map(function (row) { return row.share; }),
      hovertemplate: '<b>%{y}</b><br>$%{x:,.0f} returned'
                   + '<br>%{customdata:.1%} of all returns<extra></extra>',
    }], baseLayout(CFG.chartHeights.return_reason, {
      margin: { l: 138, r: 26, t: 22, b: 42 },
      xaxis: deepMerge({ title: { text: 'Value returned' } }, axisTick('money')),
      yaxis: { title: null, showgrid: false },
      showlegend: false,
    }));

    var returns = sum(bnd.series.returns.slice(lo, hi));
    var orders = sum(bnd.series.orders.slice(lo, hi));
    var value = sum(bnd.series.return_value.slice(lo, hi));
    var worst = byCategory[byCategory.length - 1];
    renderStats('tp-return-stats', [
      { label: 'Return rate', value: fmtValue(returns / Math.max(orders, 1), 'percent'),
        note: 'of orders in window' },
      { label: 'Value returned', value: fmtCompact(value, 'money'), note: 'in window' },
      { label: 'Highest-return category', value: worst ? worst.category : '—',
        note: worst ? fmtValue(worst.rate, 'percent') + ' of its revenue' : '' },
      { label: 'Returns processed', value: fmtCompact(returns), note: 'in window' },
    ]);
  }

  // ======================================================================
  // Page wiring
  // ======================================================================
  function sectionOfView(view) {
    var found = CFG.sections.filter(function (section) {
      return section.views.some(function (item) { return item.key === view; });
    })[0];
    return found ? found.key : CFG.sections[0].key;
  }

  function renderTopbar() {
    var host = document.getElementById('tp-topbar');
    host.innerHTML = '';

    var brand = el('div', 'tp-brand');
    brand.appendChild(el('div', 'tp-brand-mark', DB.brand.mark));
    var text = el('div');
    text.appendChild(el('div', 'tp-brand-name', DB.brand.name));
    text.appendChild(el('div', 'tp-brand-tagline', DB.brand.tagline));
    brand.appendChild(text);
    host.appendChild(brand);

    var group_ = el('div', 'tp-topbar-controls');
    group_.appendChild(control('Brand', select('tp-brand-select',
      CFG.brands.map(function (name) { return { value: name, label: name }; }),
      state.brand, function (value) {
        state.brand = value;
        state.growthMonth = null;
        renderKpis();
        renderView();
      })));
    group_.appendChild(control('Date window', segmented('tp-preset',
      CFG.presets.map(function (preset) {
        return { value: preset.label, label: preset.label };
      }), state.preset, function (value) {
        state.preset = value;
        renderKpis();
        renderView();
      })));
    host.appendChild(group_);
  }

  function renderTabs() {
    var host = document.getElementById('tp-tabs');
    host.innerHTML = '';
    var active = sectionOfView(state.view);
    CFG.sections.forEach(function (section) {
      var button = el('button', 'tp-tab' + (section.key === active ? ' tp-tab--active' : ''),
                      section.label);
      button.type = 'button';
      button.addEventListener('click', function () {
        state.view = section.views[0].key;
        renderShell();
      });
      host.appendChild(button);
    });

    var subhost = document.getElementById('tp-subtabs');
    subhost.innerHTML = '';
    var section = CFG.sections.filter(function (s) { return s.key === active; })[0];
    section.views.forEach(function (item) {
      var button = el('button', 'tp-subtab'
        + (item.key === state.view ? ' tp-subtab--active' : ''));
      button.type = 'button';
      button.appendChild(el('span', 'tp-subtab-label', item.label));
      button.appendChild(el('span', 'tp-subtab-blurb', item.blurb));
      button.addEventListener('click', function () {
        state.view = item.key;
        renderShell();
      });
      subhost.appendChild(button);
    });
  }

  function renderKpis() {
    var span = windowIndices();
    var lo = span[0];
    var hi = span[1];
    var bnd = bundle();
    var host = document.getElementById('tp-kpis');
    host.innerHTML = '';
    var comparison = 'vs prior ' + (hi - lo) + ' days';

    ['revenue', 'orders', 'aov', 'conversion', 'new_customers'].forEach(function (key) {
      var kind = metricFormat(key);
      var headline;
      if (isRatio(key)) {
        var pair = CFG.derived[key];
        headline = sum(bnd.series[pair[0]].slice(lo, hi))
                 / Math.max(sum(bnd.series[pair[1]].slice(lo, hi)), 1e-9);
      } else {
        headline = sum(seriesFor(bnd, key).slice(lo, hi));
      }
      var delta = priorPeriodDelta(bnd, key, lo, hi);
      var tone = Math.abs(delta) < 0.05 ? 'flat' : (delta > 0 ? 'up' : 'down');
      var text = tone === 'flat'
        ? 'no change ' + comparison
        : (delta > 0 ? '▲ ' : '▼ ') + group(Math.abs(delta), 1) + '% ' + comparison;

      var tile = el('div', 'tp-kpi');
      tile.appendChild(el('div', 'tp-kpi-label', metricLabel(key)));
      tile.appendChild(el('div', 'tp-kpi-value', fmtCompact(headline, kind)));
      tile.appendChild(el('div', 'tp-kpi-delta tp-kpi-delta--' + tone, text));
      host.appendChild(tile);
    });
  }

  function renderShell() {
    setGrowthPlaying(false);
    renderTabs();
    var host = document.getElementById('tp-views');
    host.innerHTML = '';
    var panel = el('section', 'tp-panel');
    panel.id = 'tp-panel-' + state.view;
    viewSpecs()[state.view].forEach(function (spec) {
      panel.appendChild(card(spec));
    });
    host.appendChild(panel);
    renderView();
  }

  function renderView() {
    var span = windowIndices();
    var lo = span[0];
    var hi = span[1];
    var bnd = bundle();

    switch (state.view) {
      case 'revenue':
        renderTrend(bnd, lo, hi);
        renderAnomalyLog(bnd, lo, hi);
        break;
      case 'drivers':
        renderDrivers(bnd, lo, hi);
        renderSplom(bnd, lo, hi);
        break;
      case 'category':
        renderCategoryWaterfall(bnd, lo, hi);
        stackedArea('tp-category-share', bnd.category_mix, 'revenue', categoryNames(),
          categoryColor, state.categoryMode === 'share', 'category_share',
          { share: 'Share of revenue', absolute: 'Revenue' });
        break;
      case 'cohorts':
        renderCohorts(bnd);
        break;
      case 'value':
        renderValue(bnd);
        break;
      case 'channels':
        renderChannels(bnd);
        break;
      case 'promotions':
        renderPromotions(bnd, lo, hi);
        break;
      case 'fulfillment':
        renderGeoStats(bnd);
        renderMap(bnd);
        renderGrowth();
        renderMarketBars(bnd);
        break;
      case 'returns':
        renderReturns(bnd, lo, hi);
        break;
      default:
        break;
    }
  }

  function boot(payload) {
    DB = payload;
    CFG = payload.config;
    state.brand = CFG.defaultBrand;
    state.preset = CFG.defaultPreset;
    state.view = CFG.defaultView;
    METRIC_OPTIONS = metricOptions(CFG.axisMetrics);

    renderTopbar();
    renderKpis();
    renderShell();

    var loading = document.getElementById('tp-loading');
    if (loading) loading.remove();
  }

  function fail(message) {
    var loading = document.getElementById('tp-loading');
    if (loading) loading.textContent = message;
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (typeof Plotly === 'undefined') {
      fail('The charting library did not load. Try a hard refresh.');
      return;
    }
    fetch(DATA_URL)
      .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      })
      .then(boot)
      .catch(function (error) {
        fail('Could not load the demo dataset (' + error.message + ').');
      });
  });
}());
