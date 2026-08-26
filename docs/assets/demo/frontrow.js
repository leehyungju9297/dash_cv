/* =============================================================================
   Frontrow Analytics — static twin of the Dash demo dashboard
   -----------------------------------------------------------------------------
   The portfolio's live site is a static GitHub Pages build, so this page renders
   the dashboard client-side with plotly.js instead of Dash callbacks. It reads
   the same seeded dataset the Dash page uses (frontrow_data.json, written by
   demo_dashboard/export.py) and mirrors demo_dashboard/figures.py chart for
   chart, so the two dashboards show identical numbers.

   Regenerate the data after changing demo_dashboard/data.py:
       python3 -m demo_dashboard.export
   ============================================================================= */
(function () {
  'use strict';

  var DATA_URL = '../assets/demo/frontrow_data.json';
  var D = null;      // full payload
  var CFG = null;    // payload.config
  var SEGMENT_NAMES = [];
  var SEGMENT_COLORS = {};

  // Metrics that describe a level at a point in time rather than a flow. They
  // are carried forward when resampled and never summed across periods.
  // Mirrors figures.STOCK_METRICS.
  var STOCK_METRICS = { memberships: 1, mau: 1, session_minutes: 1 };

  var PLOT_CONFIG = { displayModeBar: false, responsive: true, showTips: false };

  var state = {
    section: 'overview',
    client: null,
    preset: null,
    left: 'dau',
    right: 'memberships',
    grain: 'Daily',
    events: true,
    display: 'market',
    mapMetric: 'users',
    mapSelection: null,
    segments: [],
    locLevel: 'city',
    locSegment: 'All',
    x: 'dau',
    y: 'memberships',
    revGrain: 'Monthly',
    churnClients: []
  };

  // ==========================================================================
  // Config accessors (mirror demo_dashboard/config.py)
  // ==========================================================================
  function metricLabel(key) {
    return (CFG.metrics[key] && CFG.metrics[key].label) || key;
  }

  function metricFormat(key) {
    return (CFG.metrics[key] && CFG.metrics[key].format) || 'int';
  }

  function metricColor(key) {
    var accent = (CFG.metrics[key] && CFG.metrics[key].accent) || 'blue';
    return CFG.accents[accent] || CFG.accents.blue;
  }

  function bundle(client) {
    return D.clients[client];
  }

  function series(client) {
    return D.clients[client].series;
  }

  // ==========================================================================
  // Formatting (mirrors figures.fmt_value / fmt_compact)
  // ==========================================================================
  /* Round ties away from zero.

     JavaScript's toLocaleString rounds ties away from zero while Python's
     format() rounds them to even, so a revenue total of 932,150 would render as
     $932.2K here and $932.1K on the Dash page. Both sides pre-round through this
     identical rule (see figures.round_half_up) so the two dashboards can never
     disagree on a displayed number. */
  function roundHalfUp(value, decimals) {
    var factor = Math.pow(10, decimals || 0);
    var rounded = Math.floor(Math.abs(value) * factor + 0.5) / factor;
    if (rounded === 0) return 0;   // never render a negative zero
    return value < 0 ? -rounded : rounded;
  }

  function group(value, decimals) {
    var places = decimals || 0;
    return roundHalfUp(value, places).toLocaleString('en-US', {
      minimumFractionDigits: places, maximumFractionDigits: places
    });
  }

  function fmtValue(value, kind) {
    if (value === null || value === undefined || isNaN(value)) return '—';
    if (kind === 'money') return Math.abs(value) >= 100 ? '$' + group(value, 0) : '$' + group(value, 2);
    if (kind === 'minutes') return group(value, 1) + ' min';
    if (kind === 'percent') return group(value, 1) + '%';
    return group(value, 0);
  }

  function fmtCompact(value, kind) {
    if (value === null || value === undefined || isNaN(value)) return '—';
    if (kind === 'minutes') return group(value, 1) + ' min';
    var prefix = kind === 'money' ? '$' : '';
    var magnitude = Math.abs(value);
    if (magnitude >= 1e6) return prefix + group(value / 1e6, 2) + 'M';
    if (magnitude >= 1e4) return prefix + group(value / 1e3, 1) + 'K';
    return prefix + group(value, 0);
  }

  function hoverNumber(kind) {
    if (kind === 'money') return '$%{y:,.0f}';
    if (kind === 'minutes') return '%{y:,.1f} min';
    return '%{y:,.0f}';
  }

  // ==========================================================================
  // Computation (mirrors demo_dashboard/data.py)
  // ==========================================================================
  function windowIndices(days) {
    var n = D.dates.length;
    if (!days || days <= 0) return [0, n];
    return [Math.max(n - days, 0), n];
  }

  function currentWindow() {
    var preset = CFG.presets.filter(function (p) { return p.label === state.preset; })[0];
    return windowIndices(preset ? preset.days : 365);
  }

  function summarize(values) {
    if (!values.length) return { mean: 0, min: 0, max: 0, total: 0, last: 0 };
    var total = 0, min = Infinity, max = -Infinity;
    for (var i = 0; i < values.length; i++) {
      total += values[i];
      if (values[i] < min) min = values[i];
      if (values[i] > max) max = values[i];
    }
    return { mean: total / values.length, min: min, max: max, total: total, last: values[values.length - 1] };
  }

  function deltaPct(values) {
    if (values.length < 4) return 0;
    var mid = Math.floor(values.length / 2);
    var first = 0, second = 0;
    for (var i = 0; i < mid; i++) first += values[i];
    for (var j = mid; j < values.length; j++) second += values[j];
    first /= mid;
    second /= (values.length - mid);
    if (first <= 0) return 0;
    return (second - first) / first * 100;
  }

  function pearson(xs, ys) {
    var n = xs.length;
    if (n < 3) return 0;
    var mx = 0, my = 0, i;
    for (i = 0; i < n; i++) { mx += xs[i]; my += ys[i]; }
    mx /= n; my /= n;
    var cov = 0, vx = 0, vy = 0;
    for (i = 0; i < n; i++) {
      var dx = xs[i] - mx, dy = ys[i] - my;
      cov += dx * dy; vx += dx * dx; vy += dy * dy;
    }
    if (vx <= 0 || vy <= 0) return 0;
    return cov / Math.sqrt(vx * vy);
  }

  function linearFit(xs, ys) {
    var n = xs.length;
    if (n < 3) return { slope: 0, intercept: 0, r2: 0 };
    var mx = 0, my = 0, i;
    for (i = 0; i < n; i++) { mx += xs[i]; my += ys[i]; }
    mx /= n; my /= n;
    var num = 0, vx = 0;
    for (i = 0; i < n; i++) { num += (xs[i] - mx) * (ys[i] - my); vx += (xs[i] - mx) * (xs[i] - mx); }
    if (vx <= 0) return { slope: 0, intercept: my, r2: 0 };
    var slope = num / vx;
    var r = pearson(xs, ys);
    return { slope: slope, intercept: my - slope * mx, r2: r * r };
  }

  /* Roll a daily series up to weekly / monthly / quarterly buckets.
     `how === 'last'` is for stock metrics where summing days is meaningless. */
  function resample(dates, values, grain, how) {
    if (grain === 'Daily') return { x: dates.slice(), y: values.slice() };

    function keyFor(iso) {
      var year = +iso.slice(0, 4), month = +iso.slice(5, 7);
      if (grain === 'Weekly') {
        var d = new Date(iso + 'T00:00:00Z');
        var weekday = (d.getUTCDay() + 6) % 7;    // Monday = 0, matching Python
        d.setUTCDate(d.getUTCDate() - weekday);
        return d.toISOString().slice(0, 10);
      }
      if (grain === 'Monthly') return iso.slice(0, 7) + '-01';
      if (grain === 'Quarterly') {
        var q = 3 * Math.floor((month - 1) / 3) + 1;
        return year + '-' + String(q).padStart(2, '0') + '-01';
      }
      return year + '-01-01';
    }

    var xs = [], ys = [];
    for (var i = 0; i < dates.length; i++) {
      var key = keyFor(dates[i]);
      if (!xs.length || xs[xs.length - 1] !== key) { xs.push(key); ys.push(0); }
      if (how === 'last') ys[ys.length - 1] = values[i];
      else ys[ys.length - 1] += values[i];
    }
    return { x: xs, y: ys };
  }

  function correlationMatrix(client, lo, hi) {
    var s = series(client);
    var columns = CFG.correlationMetrics.filter(function (k) { return s[k]; });
    var sliced = columns.map(function (k) { return s[k].slice(lo, hi); });
    var matrix = sliced.map(function (a) {
      return sliced.map(function (b) { return Math.round(pearson(a, b) * 1000) / 1000; });
    });
    return { columns: columns, matrix: matrix };
  }

  function eventsInWindow(client, lo, hi) {
    if (lo >= hi) return [];
    var start = D.dates[lo], end = D.dates[hi - 1];
    return bundle(client).events.filter(function (e) { return e.date >= start && e.date <= end; });
  }

  // ==========================================================================
  // Geography (mirrors demo_dashboard/geo.py)
  // ==========================================================================
  /* The heatmap plots far more markers than it would be sensible to transport,
     so markers are generated from the compact per-city rows. That only works if
     both implementations generate the same points, hence a 32-bit LCG built on
     integer arithmetic Python reproduces exactly, and jitter as a sum of
     uniforms rather than a Box-Muller normal — no log/sqrt/cos, whose last-bit
     behavior is not guaranteed to match across language runtimes. */
  function Lcg(seed) {
    this.state = seed >>> 0;
  }

  Lcg.prototype.nextFloat = function () {
    this.state = (Math.imul(1664525, this.state) + 1013904223) >>> 0;
    return this.state / 4294967296;
  };

  Lcg.prototype.jitter = function (spread) {
    var u = (this.nextFloat() + this.nextFloat() + this.nextFloat()) / 3;
    return (u * 2 - 1) * spread;
  };

  function stringSeed(text) {
    var h = 2166136261;
    for (var i = 0; i < text.length; i++) {
      h ^= text.charCodeAt(i) & 0xff;
      h = Math.imul(h, 16777619) >>> 0;
    }
    return h >>> 0;
  }

  // Three decimals is about 100 m, far below the jitter spread; the extra digit
  // only inflated the payload. Must match geo._COORD_DECIMALS.
  var COORD_DECIMALS = 3;

  function round4(value) {
    return roundHalfUp(value, 4);
  }

  function roundCoord(value) {
    return roundHalfUp(value, COORD_DECIMALS);
  }

  function placeLabel(level, entry) {
    if (level === 'city') return entry.city + ', ' + entry.region + ', ' + entry.country;
    if (level === 'region') return entry.region + ', ' + entry.country;
    return entry.country;
  }

  var _levelCache = {};

  function aggregateByLevel(client, level) {
    var cacheKey = client + '|' + level;
    if (_levelCache[cacheKey]) return _levelCache[cacheKey];

    var key = level === 'region' ? 'region' : (level === 'country' ? 'country' : 'city');
    var order = [];
    var merged = {};

    bundle(client).locations.forEach(function (row) {
      var name = row[key];
      var entry = merged[name];
      if (!entry) {
        entry = {
          name: name, city: row.city, region: row.region, country: row.country,
          users: 0, engagement: 0, latWeight: 0, lonWeight: 0,
          segments: {}, seed: row.seed, rampLag: row.ramp_lag, topUsers: 0
        };
        SEGMENT_NAMES.forEach(function (s) { entry.segments[s] = 0; });
        merged[name] = entry;
        order.push(entry);
      }
      entry.users += row.users;
      entry.engagement += row.engagement;
      entry.latWeight += row.lat * row.users;
      entry.lonWeight += row.lon * row.users;
      SEGMENT_NAMES.forEach(function (s) { entry.segments[s] += row.segments[s]; });
      // A rolled-up market inherits the lag of its largest contributor.
      if (row.users > entry.topUsers) {
        entry.topUsers = row.users;
        entry.rampLag = row.ramp_lag;
        entry.seed = row.seed;
      }
    });

    var out = order.map(function (entry) {
      var users = entry.users || 1;
      var members = entry.segments.Member + entry.segments['Super User'];
      return {
        name: entry.name,
        label: placeLabel(level, entry),
        lat: round4(entry.latWeight / users),
        lon: round4(entry.lonWeight / users),
        users: entry.users,
        engagement: entry.engagement,
        members: members,
        signed_up: entry.segments['Signed-Up'],
        super_users: entry.segments['Super User'],
        member_share: members / users,
        segments: entry.segments,
        seed: entry.seed,
        ramp_lag: entry.rampLag
      };
    });
    out.sort(function (a, b) { return b.users - a.users; });
    _levelCache[cacheKey] = out;
    return out;
  }

  // Metros are tight, sparse international markets spread wider.
  var SPREAD_DEGREES = 0.42;
  var SPREAD_INTERNATIONAL = 0.62;

  /* One marker per mapped user, not a sample: MapLibre draws the full ~270k
     cloud in about the time it draws 5,000, and the density is the point of the
     view. No per-point label — at this scale a single fan cannot be hovered. */
  function spreadWithinCity(rows, salt) {
    var points = [];

    rows.forEach(function (row) {
      var allocation = row.users;
      var rng = new Lcg((row.seed ^ stringSeed(salt)) >>> 0);
      var spread = row.country === 'United States' ? SPREAD_DEGREES : SPREAD_INTERNATIONAL;
      var weights = SEGMENT_NAMES.map(function (s) { return Math.max(row.segments[s], 0) + 0.5; });
      var pool = weights.reduce(function (a, b) { return a + b; }, 0);

      for (var i = 0; i < allocation; i++) {
        var draw = rng.nextFloat() * pool;
        var segment = SEGMENT_NAMES[SEGMENT_NAMES.length - 1];
        var running = 0;
        for (var j = 0; j < SEGMENT_NAMES.length; j++) {
          running += weights[j];
          if (draw < running) { segment = SEGMENT_NAMES[j]; break; }
        }
        points.push({
          lat: roundCoord(row.lat + rng.jitter(spread)),
          lon: roundCoord(row.lon + rng.jitter(spread * 1.3)),
          segment: segment
        });
      }
    });
    return points;
  }

  function interpolate(values, position) {
    if (!values.length) return 0;
    if (position <= 0) return values[0];
    if (position >= values.length - 1) return values[values.length - 1];
    var low = Math.trunc(position);
    var weight = position - low;
    return values[low] * (1 - weight) + values[low + 1] * weight;
  }

  function growthFrames(client, level) {
    var ramp = bundle(client).monthly_ramp;
    var markets = aggregateByLevel(client, level);
    var fractions = ramp.map(function (s) { return s.frac; });
    var span = Math.max(ramp.length - 1, 1);

    return ramp.map(function (step, index) {
      var rows = [];
      markets.forEach(function (market) {
        var lag = market.ramp_lag * span;
        if (index < lag) return;
        // Re-read the client curve at the market's own lagged, rescaled position
        // so late markets compress their ramp into the remaining months.
        var local = (index - lag) / Math.max(span - lag, 1e-9);
        var users = market.users * interpolate(fractions, local * span);
        if (users < 1) return;
        rows.push({
          label: market.label, lat: market.lat, lon: market.lon,
          users: Math.round(users), member_share: market.member_share
        });
      });
      return { period: step.period, markets: rows };
    });
  }

  // ==========================================================================
  // Shared figure theme (mirrors figures.base_layout)
  // ==========================================================================
  var FONT = { family: 'Public Sans, Inter, Helvetica Neue, sans-serif', color: '#AAB4C3', size: 12 };

  function deepMerge(base, extra) {
    Object.keys(extra).forEach(function (key) {
      var value = extra[key];
      if (value && typeof value === 'object' && !Array.isArray(value) &&
          base[key] && typeof base[key] === 'object' && !Array.isArray(base[key])) {
        deepMerge(base[key], value);
      } else {
        base[key] = value;
      }
    });
    return base;
  }

  function baseLayout(height, overrides) {
    var surface = CFG.surface;
    var layout = {
      height: height || 420,
      template: 'plotly_dark',
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: FONT,
      margin: { l: 56, r: 30, t: 24, b: 44 },
      hovermode: 'x unified',
      hoverlabel: { bgcolor: '#141a24', bordercolor: surface.border, font: { color: surface.text, size: 12 } },
      legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, x: 0, bgcolor: 'rgba(0,0,0,0)', font: { size: 11 } },
      xaxis: { gridcolor: surface.grid, zerolinecolor: surface.zeroline, linecolor: surface.grid, showspikes: false },
      yaxis: { gridcolor: surface.grid, zerolinecolor: surface.zeroline, linecolor: 'rgba(0,0,0,0)' }
    };
    return deepMerge(layout, overrides || {});
  }

  function softColor(hex, alpha) {
    var h = hex.replace('#', '');
    return 'rgba(' + parseInt(h.slice(0, 2), 16) + ',' + parseInt(h.slice(2, 4), 16) + ',' +
      parseInt(h.slice(4, 6), 16) + ',' + (alpha === undefined ? 0.10 : alpha) + ')';
  }

  function draw(id, traces, layout) {
    var el = document.getElementById(id);
    if (!el) return;
    var loading = el.querySelector('.fr-loading');
    if (loading) loading.remove();
    return Plotly.react(el, traces, layout, PLOT_CONFIG);
  }

  /* Frames only attach through newPlot + addFrames; Plotly.react leaves stale
     frames behind, which is why the animation is drawn from scratch. */
  function drawAnimated(id, traces, layout, frames) {
    var el = document.getElementById(id);
    if (!el) return;
    var loading = el.querySelector('.fr-loading');
    if (loading) loading.remove();
    Plotly.purge(el);
    Plotly.newPlot(el, traces, layout, PLOT_CONFIG).then(function () {
      Plotly.addFrames(el, frames);
    });
  }

  function drawEmpty(id, message, height) {
    return draw(id, [], baseLayout(height || 300, {
      hovermode: false,
      showlegend: false,
      xaxis: { visible: false },
      yaxis: { visible: false },
      annotations: [{
        text: message, x: 0.5, y: 0.5, xref: 'paper', yref: 'paper',
        showarrow: false, font: { color: CFG.surface.text_muted, size: 14 }
      }]
    }));
  }

  // ==========================================================================
  // Figures
  // ==========================================================================
  function renderTrend() {
    var w = currentWindow(), lo = w[0], hi = w[1];
    var dates = D.dates.slice(lo, hi);
    if (!dates.length) return drawEmpty('fr-trend', 'Select a date range to plot.', CFG.chartHeights.trend);

    var s = series(state.client);
    var traces = [];
    [[state.left, 'y'], [state.right, 'y2']].forEach(function (pair) {
      var metric = pair[0], axis = pair[1];
      if (!metric) return;
      var how = STOCK_METRICS[metric] ? 'last' : 'sum';
      var r = resample(dates, s[metric].slice(lo, hi), state.grain, how);
      var color = metricColor(metric);
      traces.push({
        type: 'scatter', mode: 'lines', x: r.x, y: r.y, yaxis: axis,
        name: metricLabel(metric),
        line: { color: color, width: 2 },
        fill: axis === 'y' ? 'tozeroy' : 'none',
        fillcolor: axis === 'y' ? softColor(color) : undefined,
        hovertemplate: '<b>' + metricLabel(metric) + '</b> ' + hoverNumber(metricFormat(metric)) + '<extra></extra>'
      });
    });

    var shapes = [];
    if (state.events) {
      var events = eventsInWindow(state.client, lo, hi);
      // Capped at 14: past that the overlay stops being an annotation and starts
      // being the chart. When the cap bites, the largest events win.
      if (events.length > 14) {
        events = events.slice().sort(function (a, b) { return b.magnitude - a.magnitude; }).slice(0, 14);
        events.sort(function (a, b) { return a.date < b.date ? -1 : 1; });
      }
      var seen = {};
      events.forEach(function (event) {
        var color = CFG.eventKinds[event.kind].color;
        shapes.push({
          type: 'line', x0: event.date, x1: event.date, y0: 0, y1: 1,
          xref: 'x', yref: 'paper', layer: 'below',
          line: { color: color, width: 1, dash: 'dot' }
        });
        traces.push({
          type: 'scatter', mode: 'markers', x: [event.date], y: [1], yaxis: 'y3',
          marker: { symbol: 'triangle-down', size: 9, color: color, line: { width: 0 } },
          name: event.kind,
          legendgroup: 'event-' + event.kind,
          showlegend: !seen[event.kind],
          hovertemplate: '<b>' + event.kind + '</b>' +
            (event.client ? ' · ' + event.client : '') + '<br>%{x}<extra></extra>'
        });
        seen[event.kind] = true;
      });
    }

    draw('fr-trend', traces, baseLayout(CFG.chartHeights.trend, {
      margin: { l: 62, r: 62, t: 30, b: 44 },
      shapes: shapes,
      yaxis: {
        title: { text: metricLabel(state.left), font: { color: metricColor(state.left) } },
        tickfont: { color: metricColor(state.left) }
      },
      yaxis2: {
        title: { text: metricLabel(state.right), font: { color: metricColor(state.right) } },
        tickfont: { color: metricColor(state.right) },
        overlaying: 'y', side: 'right', showgrid: false
      },
      yaxis3: {
        overlaying: 'y', side: 'left', range: [0, 1],
        showgrid: false, showticklabels: false, zeroline: false, fixedrange: true
      }
    }));
  }

  function renderLocationBar() {
    var rows = bundle(state.client).locations;
    var totals = {};
    rows.forEach(function (row) {
      var value = state.locSegment === 'All' ? row.users : (row.segments[state.locSegment] || 0);
      totals[row[state.locLevel]] = (totals[row[state.locLevel]] || 0) + value;
    });

    var ranked = Object.keys(totals).map(function (k) { return [k, totals[k]]; })
      .sort(function (a, b) { return b[1] - a[1]; }).slice(0, 14).reverse();
    if (!ranked.length) return drawEmpty('fr-location-bar', 'No location data for this selection.');

    var color = state.locSegment === 'All' ? CFG.accents.blue : SEGMENT_COLORS[state.locSegment];
    draw('fr-location-bar', [{
      type: 'bar', orientation: 'h',
      x: ranked.map(function (r) { return r[1]; }),
      y: ranked.map(function (r) { return r[0]; }),
      marker: { color: color, line: { width: 0 } },
      hovertemplate: '<b>%{y}</b><br>%{x:,.0f} users<extra></extra>'
    }], baseLayout(CFG.chartHeights.location_bar, {
      hovermode: 'closest',
      margin: { l: 130, r: 24, t: 16, b: 40 },
      showlegend: false,
      xaxis: { title: { text: 'Users' } }
    }));
  }

  // --------------------------------------------------------------------------
  // Audience Heatmap (mirrors figures.heatmap_map / growth_map)
  // --------------------------------------------------------------------------
  var MAX_BUBBLES = 600;

  var DISPLAY_HINTS = {
    market: 'One bubble per market, sized by the selected metric and colored by ' +
            'member share. Click a bubble to drill into that market.',
    density: 'A continuous surface weighted by the selected metric — no market ' +
             'boundaries implied. Click a hotspot to drill into it.',
    individual: 'Every mapped user, colored by lifecycle segment — not a sample. ' +
                'Markers are generated deterministically from the market aggregates, ' +
                'so the same seed always draws the same cloud. At this density a ' +
                'single fan cannot be hovered; use the market or density view to ' +
                'drill in.'
  };

  /* Square-root sizing so a market ten times larger reads as ~3x the radius —
     area, not radius, tracks the value. */
  function bubbleSizes(values, refMax) {
    var peak = refMax || (values.length ? Math.max.apply(null, values) : 0);
    if (!peak) return values.map(function () { return 6; });
    return values.map(function (v) { return 6 + 44 * Math.sqrt(Math.max(v, 0) / peak); });
  }

  function mapView(markets) {
    if (!markets.length) return { center: { lat: 39.0, lon: -98.0 }, zoom: 2.2 };
    var weight = markets.reduce(function (a, m) { return a + m.users; }, 0) || 1;
    var lat = markets.reduce(function (a, m) { return a + m.lat * m.users; }, 0) / weight;
    var lon = markets.reduce(function (a, m) { return a + m.lon * m.users; }, 0) / weight;
    var lats = markets.map(function (m) { return m.lat; });
    var lons = markets.map(function (m) { return m.lon; });
    var span = Math.max(
      Math.max.apply(null, lats) - Math.min.apply(null, lats),
      (Math.max.apply(null, lons) - Math.min.apply(null, lons)) / 2
    );
    var zoom = span > 60 ? 2.6 : (span > 25 ? 3.0 : 4.0);
    return { center: { lat: roundHalfUp(lat, 3), lon: roundHalfUp(lon, 3) }, zoom: zoom };
  }

  function mapLayout(markets, height, uirevision, overrides) {
    var view = mapView(markets);
    return baseLayout(height || 560, Object.assign({
      hovermode: 'closest',
      margin: { l: 0, r: 0, t: 0, b: 0 },
      xaxis: { visible: false },
      yaxis: { visible: false },
      map: { style: CFG.heatmap.mapStyle, center: view.center, zoom: view.zoom },
      // Keeps the viewer's pan/zoom across filter changes; it resets only when
      // the account changes, because a new account is a new map.
      uirevision: uirevision || 'map'
    }, overrides || {}));
  }

  function marketHover(market) {
    return '<b>' + market.label + '</b><br>' +
      'Users: ' + group(market.users) + '<br>' +
      'Signed-up: ' + group(market.signed_up) + '<br>' +
      'Members: ' + group(market.members) + ' (' + group(market.member_share * 100, 1) + '% share)<br>' +
      'Super users: ' + group(market.super_users) + '<br>' +
      'Engagement: ' + group(market.engagement);
  }

  function metricColumn(metric) {
    var spec = CFG.heatmap.metrics[metric] || CFG.heatmap.metrics.users;
    return spec.column;
  }

  function renderMap() {
    var markets = aggregateByLevel(state.client, state.locLevel);
    document.getElementById('fr-map-hint').textContent = DISPLAY_HINTS[state.display] || '';
    if (!markets.length) return drawEmpty('fr-map', 'No location data for this selection.', CFG.chartHeights.map);

    var plotted = state.display === 'individual' ? renderIndividualMap(markets)
      : (state.display === 'density' ? renderDensityMap(markets) : renderMarketMap(markets));
    // Plotly only attaches its event emitter to the div once it has plotted.
    return Promise.resolve(plotted).then(bindMapClick);
  }

  function renderMarketMap(markets) {
    var plotted = markets.slice(0, MAX_BUBBLES);
    var column = metricColumn(state.mapMetric);
    var shares = plotted.map(function (m) { return m.member_share * 100; });
    // Headroom above the observed maximum so the top market is not pinned to the
    // end of the ramp, where every dense market would look identical.
    var cmax = Math.max(shares.length ? Math.max.apply(null, shares) : 0, 5) * 1.08;

    return draw('fr-map', [{
      type: 'scattermap', mode: 'markers',
      lat: plotted.map(function (m) { return m.lat; }),
      lon: plotted.map(function (m) { return m.lon; }),
      marker: {
        size: bubbleSizes(plotted.map(function (m) { return m[column]; })),
        color: shares,
        colorscale: CFG.heatmap.memberShareScale,
        cmin: 0, cmax: cmax, opacity: 0.82,
        colorbar: {
          title: { text: 'Member share', side: 'right',
                   font: { color: CFG.surface.text_secondary, size: 11 } },
          tickfont: { color: CFG.surface.text_secondary, size: 10 },
          ticksuffix: '%', nticks: 4, thickness: 8, len: 0.42,
          x: 0.99, y: 0.5, yanchor: 'middle', outlinewidth: 0,
          bgcolor: 'rgba(11,15,23,0.55)'
        }
      },
      customdata: plotted.map(function (m) { return m.name; }),
      text: plotted.map(marketHover),
      hovertemplate: '%{text}<extra></extra>',
      name: ''
    }], mapLayout(plotted, null, state.client, { showlegend: false }));
  }

  function renderDensityMap(markets) {
    var column = metricColumn(state.mapMetric);
    var values = markets.map(function (m) { return Math.max(m[column], 0); });
    var peak = values.length ? Math.max.apply(null, values) : 1;
    // Weight by the square root as well: raw counts let one metro saturate the
    // surface and flatten every other market to invisible.
    var weights = values.map(function (v) { return peak ? Math.sqrt(v / peak) : 0; });

    return draw('fr-map', [{
      type: 'densitymap',
      lat: markets.map(function (m) { return m.lat; }),
      lon: markets.map(function (m) { return m.lon; }),
      z: weights, radius: 34, colorscale: 'Inferno', opacity: 0.72,
      colorbar: {
        title: { text: (CFG.heatmap.metrics[state.mapMetric] || {}).label || 'Audience',
                 side: 'right', font: { color: CFG.surface.text_secondary, size: 11 } },
        tickfont: { color: CFG.surface.text_secondary, size: 10 },
        showticklabels: false, thickness: 8, len: 0.42,
        x: 0.99, y: 0.5, yanchor: 'middle', outlinewidth: 0,
        bgcolor: 'rgba(11,15,23,0.55)'
      },
      text: markets.map(function (m) { return m.label; }),
      customdata: markets.map(function (m) { return [m.name, m.users]; }),
      hovertemplate: '<b>%{text}</b><br>%{customdata[1]:,.0f} users<extra></extra>',
      name: ''
    }], mapLayout(markets, null, state.client, { showlegend: false }));
  }

  function renderIndividualMap(markets) {
    var active = SEGMENT_NAMES.filter(function (s) { return state.segments.indexOf(s) >= 0; });
    if (!active.length) active = SEGMENT_NAMES.slice();
    var points = spreadWithinCity(bundle(state.client).locations, state.client);

    var traces = [];
    active.forEach(function (segment) {
      var subset = points.filter(function (p) { return p.segment === segment; });
      if (!subset.length) return;
      traces.push({
        type: 'scattermap', mode: 'markers',
        lat: subset.map(function (p) { return p.lat; }),
        lon: subset.map(function (p) { return p.lon; }),
        name: segment + ' (' + group(subset.length) + ')',
        marker: { size: 4, color: SEGMENT_COLORS[segment], opacity: 0.55 },
        hovertemplate: segment + '<extra></extra>'
      });
    });

    if (!traces.length) return drawEmpty('fr-map', 'No users in the selected segments.', CFG.chartHeights.map);

    return draw('fr-map', traces, mapLayout(markets, null, state.client, {
      showlegend: true,
      legend: { orientation: 'h', y: 0.02, x: 0.02, yanchor: 'bottom',
                bgcolor: 'rgba(11,15,23,0.72)', font: { size: 11 },
                bordercolor: CFG.surface.border, borderwidth: 1 }
    }));
  }

  function renderGrowth() {
    var frames = growthFrames(state.client, state.locLevel);
    var markets = aggregateByLevel(state.client, state.locLevel);
    if (frames.length < 2) return drawEmpty('fr-growth', 'Not enough history to animate.', CFG.chartHeights.growth);

    // Pinned to the final frame so a market growing is visible as growth, rather
    // than every frame rescaling to its own peak and the map appearing static.
    var sizeRef = frames[frames.length - 1].markets.reduce(
      function (a, m) { return Math.max(a, m.users); }, 1);

    function traceFor(frame) {
      var rows = frame.markets;
      return {
        type: 'scattermap', mode: 'markers',
        lat: rows.map(function (r) { return r.lat; }),
        lon: rows.map(function (r) { return r.lon; }),
        marker: {
          size: bubbleSizes(rows.map(function (r) { return r.users; }), sizeRef),
          color: rows.map(function (r) { return r.member_share * 100; }),
          colorscale: CFG.heatmap.memberShareScale,
          cmin: 0, cmax: 24, opacity: 0.8
        },
        text: rows.map(function (r) { return r.label; }),
        customdata: rows.map(function (r) { return r.users; }),
        hovertemplate: '<b>%{text}</b><br>%{customdata:,.0f} users<extra></extra>',
        name: ''
      };
    }

    var playArgs = { frame: { duration: 320, redraw: true },
                     transition: { duration: 0 }, mode: 'immediate' };

    var layout = mapLayout(markets, CFG.chartHeights.growth, 'growth', {
      showlegend: false,
      updatemenus: [{
        type: 'buttons', direction: 'left',
        x: 0.01, y: 0.02, xanchor: 'left', yanchor: 'bottom',
        pad: { l: 6, r: 6, t: 6, b: 6 },
        bgcolor: 'rgba(11,15,23,0.78)',
        bordercolor: CFG.surface.border,
        font: { color: CFG.surface.text, size: 12 },
        showactive: false,
        buttons: [
          { label: '▶  Play', method: 'animate', args: [null, playArgs] },
          { label: '❚❚  Pause', method: 'animate',
            args: [[null], { frame: { duration: 0, redraw: false }, mode: 'immediate' }] }
        ]
      }],
      sliders: [{
        active: 0,
        x: 0.16, y: 0.02, len: 0.66, xanchor: 'left', yanchor: 'bottom',
        pad: { t: 6, b: 6 },
        bgcolor: 'rgba(148,163,184,0.35)',
        bordercolor: 'rgba(0,0,0,0)',
        activebgcolor: CFG.accents.blue,
        tickcolor: 'rgba(0,0,0,0)',
        font: { color: CFG.surface.text_secondary, size: 10 },
        currentvalue: { prefix: 'Month: ', xanchor: 'left',
                        font: { color: CFG.surface.text, size: 13 } },
        steps: frames.map(function (f) {
          return { label: f.period, method: 'animate',
                   args: [[f.period], { frame: { duration: 0, redraw: true },
                                        mode: 'immediate' }] };
        })
      }]
    });

    drawAnimated('fr-growth', [traceFor(frames[0])], layout,
      frames.map(function (f) { return { name: f.period, data: [traceFor(f)] }; }));
  }

  var _mapClickBound = false;

  function bindMapClick() {
    var el = document.getElementById('fr-map');
    if (!el || _mapClickBound || !el.on) return;
    el.on('plotly_click', function (event) {
      if (!event || !event.points || !event.points.length) return;
      state.mapSelection = event.points[0].customdata;
      renderMapDetail();
    });
    _mapClickBound = true;
  }

  function renderMapDetail() {
    var host = document.getElementById('fr-map-detail');
    if (state.display === 'individual') {
      host.innerHTML = '<div class="fr-detail-empty">Switch to Market bubbles or ' +
        'Density to drill into a market.</div>';
      return;
    }
    if (!state.mapSelection) {
      host.innerHTML = '<div class="fr-detail-empty">Click a market on the map to ' +
        'break it down.</div>';
      return;
    }
    // Market bubbles carry the market name alone; density points carry
    // [name, users] so their hover can show a count.
    var name = Array.isArray(state.mapSelection) ? state.mapSelection[0] : state.mapSelection;
    var markets = aggregateByLevel(state.client, state.locLevel);
    var match = markets.filter(function (m) { return m.name === name; })[0];
    if (!match) {
      host.innerHTML = '<div class="fr-detail-empty">That market is not in the ' +
        'current selection.</div>';
      return;
    }
    var total = markets.reduce(function (a, m) { return a + m.users; }, 0) || 1;
    var rows = [
      ['Users', fmtValue(match.users)],
      ['Share of audience', fmtValue(match.users / total * 100, 'percent')],
      ['Members', fmtValue(match.members) + ' (' + fmtValue(match.member_share * 100, 'percent') + ')'],
      ['Engagement index', fmtValue(match.engagement)],
      ['Engagement per user', group(match.engagement / (match.users || 1), 2)]
    ];
    var segmentRows = SEGMENT_NAMES.map(function (s) { return [s, fmtValue(match.segments[s])]; });

    function rowHtml(pair) {
      return '<div class="fr-detail-row"><span class="fr-detail-label">' + pair[0] +
        '</span><span class="fr-detail-value">' + pair[1] + '</span></div>';
    }

    host.innerHTML = '<div class="fr-detail-body">' +
      '<div class="fr-detail-title">' + match.label + '</div>' +
      '<div class="fr-detail-rows">' + rows.map(rowHtml).join('') + '</div>' +
      '<div class="fr-detail-rows">' + segmentRows.map(rowHtml).join('') + '</div>' +
      '</div>';
  }

  function renderGeoKpis() {
    var markets = aggregateByLevel(state.client, state.locLevel);
    var users = markets.reduce(function (a, m) { return a + m.users; }, 0);
    var members = markets.reduce(function (a, m) { return a + m.members; }, 0);
    // How concentrated the audience is: the share in the top five markets.
    var topFive = markets.slice(0, 5).reduce(function (a, m) { return a + m.users; }, 0);
    var top = markets[0];

    document.getElementById('fr-geo-tiles').innerHTML = [
      tile('fr-geo-users', 'Mapped users', fmtCompact(users),
           'located from app activity', 'flat', 'blue'),
      tile('fr-geo-markets', 'Markets reached', group(markets.length),
           'at ' + state.locLevel + ' level', 'flat', 'violet'),
      tile('fr-geo-share', 'Member share', fmtValue(users ? members / users * 100 : 0, 'percent'),
           'of mapped users are members', 'flat', 'green'),
      tile('fr-geo-top', 'Largest market', top ? top.label.split(',')[0] : '—',
           (top ? fmtCompact(top.users) : '0') + ' users · top 5 hold ' +
           fmtValue(users ? topFive / users * 100 : 0, 'percent'), 'flat', 'gold')
    ].join('');
  }

  function renderTopMarkets() {
    var markets = aggregateByLevel(state.client, state.locLevel).slice(0, 10);
    var columns = ['#', 'Market', 'Users', 'Signed-up', 'Members', 'Member share', 'Engagement'];
    var head = '<thead><tr>' + columns.map(function (c) {
      var textual = c === '#' || c === 'Market';
      return '<th' + (textual ? ' class="fr-cell-text"' : '') + '>' + c + '</th>';
    }).join('') + '</tr></thead>';

    var body = markets.map(function (m, i) {
      var cells = [
        ['#', String(i + 1), true],
        ['Market', m.label, true],
        ['Users', fmtValue(m.users), false],
        ['Signed-up', fmtValue(m.signed_up), false],
        ['Members', fmtValue(m.members), false],
        ['Member share', fmtValue(m.member_share * 100, 'percent'), false],
        ['Engagement', fmtValue(m.engagement), false]
      ];
      return '<tr>' + cells.map(function (c) {
        return '<td' + (c[2] ? ' class="fr-cell-text"' : '') + '>' + c[1] + '</td>';
      }).join('') + '</tr>';
    }).join('');

    document.getElementById('fr-top-markets').innerHTML = head + '<tbody>' + body + '</tbody>';
  }

  function renderSegmentMix() {
    var rows = bundle(state.client).locations;
    var totals = {}, grand = 0;
    SEGMENT_NAMES.forEach(function (name) {
      totals[name] = rows.reduce(function (acc, r) { return acc + r.segments[name]; }, 0);
      grand += totals[name];
    });
    grand = grand || 1;

    draw('fr-segment-mix', SEGMENT_NAMES.map(function (name) {
      return {
        type: 'bar', orientation: 'h', x: [totals[name] / grand * 100], y: ['mix'],
        name: name, marker: { color: SEGMENT_COLORS[name], line: { width: 0 } },
        hovertemplate: '<b>' + name + '</b><br>%{x:.1f}%<br>' + group(totals[name], 0) +
          ' users<extra></extra>'
      };
    }), baseLayout(CFG.chartHeights.segment_mix, {
      hovermode: 'closest',
      margin: { l: 8, r: 8, t: 8, b: 8 },
      barmode: 'stack',
      xaxis: { visible: false, range: [0, 100] },
      yaxis: { visible: false },
      legend: { orientation: 'h', y: -0.6, x: 0, yanchor: 'top', font: { size: 11 } }
    }));

    var memberShare = (totals.Member + totals['Super User']) / grand * 100;
    document.getElementById('fr-segment-note').textContent =
      fmtValue(grand, 'int') + ' mapped users · ' + fmtValue(memberShare, 'percent') +
      ' have converted to a paid membership.';
  }

  function renderScatter() {
    var w = currentWindow(), lo = w[0], hi = w[1];
    var s = series(state.client);
    var xs = [], ys = [], labels = [];
    for (var i = lo; i < hi; i++) {
      if (s[state.x][i] || s[state.y][i]) {
        xs.push(s[state.x][i]); ys.push(s[state.y][i]); labels.push(D.dates[i]);
      }
    }
    if (xs.length < 5) {
      drawEmpty('fr-scatter', 'Not enough observations in this window.', CFG.chartHeights.scatter);
      document.getElementById('fr-scatter-readout').textContent = '';
      return;
    }

    var fit = linearFit(xs, ys);
    var xLo = Math.min.apply(null, xs), xHi = Math.max.apply(null, xs);

    draw('fr-scatter', [
      {
        type: 'scatter', mode: 'markers', x: xs, y: ys, text: labels,
        name: 'Daily observation',
        marker: { size: 6, color: metricColor(state.y), opacity: 0.45, line: { width: 0 } },
        hovertemplate: '%{text}<br>' + metricLabel(state.x) + ': %{x:,.0f}<br>' +
          metricLabel(state.y) + ': %{y:,.0f}<extra></extra>'
      },
      {
        type: 'scatter', mode: 'lines',
        x: [xLo, xHi],
        y: [fit.slope * xLo + fit.intercept, fit.slope * xHi + fit.intercept],
        name: 'Least-squares fit (R²=' + group(fit.r2, 2) + ')',
        line: { color: CFG.accents.gold, width: 2, dash: 'dash' },
        hoverinfo: 'skip'
      }
    ], baseLayout(CFG.chartHeights.scatter, {
      hovermode: 'closest',
      xaxis: { title: { text: metricLabel(state.x) } },
      yaxis: { title: { text: metricLabel(state.y) } }
    }));

    var strength = fit.r2 >= 0.5 ? 'strong co-movement'
      : (fit.r2 >= 0.2 ? 'moderate co-movement' : 'weak or no linear relationship');
    document.getElementById('fr-scatter-readout').textContent =
      'R² = ' + group(fit.r2, 2) + ' — ' + strength + '. A one-unit rise in ' +
      metricLabel(state.x) + ' is associated with ' +
      (fit.slope >= 0 ? '+' : '') + group(fit.slope, 3) + ' in ' + metricLabel(state.y) +
      ' across ' + (hi - lo) + ' days.';
  }

  function renderCorrelation() {
    var w = currentWindow();
    var result = correlationMatrix(state.client, w[0], w[1]);
    var labels = result.columns.map(metricLabel);

    draw('fr-correlation', [{
      type: 'heatmap', z: result.matrix, x: labels, y: labels,
      zmin: -1, zmax: 1,
      colorscale: [
        [0.0, '#7f3f4f'], [0.35, '#2b3340'], [0.5, '#1a212c'],
        [0.65, '#2c4a48'], [1.0, '#3f8f7a']
      ],
      showscale: true,
      colorbar: { thickness: 10, outlinewidth: 0, tickfont: { size: 10 }, len: 0.8 },
      hovertemplate: '%{y} vs %{x}<br>r = %{z:.2f}<extra></extra>',
      text: result.matrix.map(function (row) {
        return row.map(function (v) { return (v >= 0 ? '+' : '') + group(v, 2); });
      }),
      texttemplate: '%{text}',
      textfont: { size: 10, color: CFG.surface.text }
    }], baseLayout(CFG.chartHeights.correlation, {
      hovermode: 'closest',
      margin: { l: 150, r: 20, t: 20, b: 120 },
      showlegend: false,
      xaxis: { tickangle: -35, showgrid: false },
      yaxis: { autorange: 'reversed', showgrid: false }
    }));
  }

  function renderEngagement() {
    var w = currentWindow(), lo = w[0], hi = w[1];
    var dates = D.dates.slice(lo, hi);
    if (!dates.length) return drawEmpty('fr-engagement', 'Select a date range to plot.');
    var grain = (hi - lo) <= 95 ? 'Daily' : 'Weekly';
    var s = series(state.client);

    var minutes = resample(dates, s.session_minutes.slice(lo, hi), grain, 'last');
    var dau = resample(dates, s.dau.slice(lo, hi), grain, 'last');
    var mau = resample(dates, s.mau.slice(lo, hi), grain, 'last');
    var stickiness = dau.y.map(function (d, i) { return mau.y[i] ? d / mau.y[i] * 100 : 0; });

    draw('fr-engagement', [
      {
        type: 'scatter', mode: 'lines', x: minutes.x, y: minutes.y,
        name: 'Avg Session Minutes',
        line: { color: CFG.accents.lavender, width: 2 },
        fill: 'tozeroy', fillcolor: softColor(CFG.accents.lavender),
        hovertemplate: '<b>Avg Session</b> %{y:,.1f} min<extra></extra>'
      },
      {
        type: 'scatter', mode: 'lines', x: minutes.x, y: stickiness, yaxis: 'y2',
        name: 'Stickiness (DAU/MAU)',
        line: { color: CFG.accents.cyan, width: 2 },
        hovertemplate: '<b>Stickiness</b> %{y:.1f}%<extra></extra>'
      }
    ], baseLayout(CFG.chartHeights.engagement, {
      margin: { l: 60, r: 60, t: 26, b: 44 },
      yaxis: { title: { text: 'Minutes' } },
      yaxis2: { title: { text: 'DAU / MAU' }, overlaying: 'y', side: 'right', showgrid: false, ticksuffix: '%' }
    }));
  }

  function renderRevenue() {
    var w = currentWindow(), lo = w[0], hi = w[1];
    var dates = D.dates.slice(lo, hi);
    if (!dates.length) return drawEmpty('fr-revenue', 'Select a date range to plot.');
    var r = resample(dates, series(state.client).revenue.slice(lo, hi), state.revGrain, 'sum');

    var traces = [{
      type: 'bar', x: r.x, y: r.y, name: 'Revenue',
      marker: { color: CFG.accents.gold, line: { width: 0 } },
      hovertemplate: '<b>Revenue</b> $%{y:,.0f}<extra></extra>'
    }];

    if (r.y.length > 3) {
      var smoothed = r.y.map(function (_, i) {
        var slice = r.y.slice(Math.max(0, i - 2), i + 1);
        return slice.reduce(function (a, b) { return a + b; }, 0) / slice.length;
      });
      traces.push({
        type: 'scatter', mode: 'lines', x: r.x, y: smoothed, name: '3-period average',
        line: { color: CFG.accents.amber, width: 2, dash: 'dot' },
        hovertemplate: '<b>Trend</b> $%{y:,.0f}<extra></extra>'
      });
    }

    draw('fr-revenue', traces, baseLayout(CFG.chartHeights.revenue, { yaxis: { title: { text: 'Revenue (USD)' } } }));
  }

  function renderRevenueMix() {
    var palette = [CFG.accents.gold, CFG.accents.cyan, CFG.accents.violet,
                   CFG.accents.green, CFG.accents.coral, CFG.accents.blue];

    [['revenue_type', 'fr-mix-type'], ['platform', 'fr-mix-platform']].forEach(function (pair) {
      var rows = bundle(state.client).revenue_mix[pair[0]].slice()
        .sort(function (a, b) { return b.revenue - a.revenue; });
      draw(pair[1], [{
        type: 'pie', hole: 0.62, sort: false,
        labels: rows.map(function (r) { return r.label; }),
        values: rows.map(function (r) { return r.revenue; }),
        marker: { colors: palette.slice(0, rows.length), line: { color: '#10151d', width: 2 } },
        textinfo: 'percent',
        textfont: { size: 11, color: '#0b0f17' },
        hovertemplate: '<b>%{label}</b><br>$%{value:,.0f} (%{percent})<extra></extra>'
      }], baseLayout(CFG.chartHeights.mix_donut, {
        hovermode: 'closest',
        margin: { l: 8, r: 8, t: 8, b: 8 },
        xaxis: { visible: false },
        yaxis: { visible: false },
        legend: { orientation: 'v', x: 1.0, y: 0.5, yanchor: 'middle', font: { size: 11 } }
      }));
    });
  }

  function renderChurn() {
    var selected = state.churnClients.filter(function (c) { return D.clients[c]; });
    if (!selected.length) {
      return drawEmpty('fr-churn', 'Select at least one account to compare churn.', CFG.chartHeights.churn);
    }
    var palette = [CFG.accents.coral, CFG.accents.blue, CFG.accents.green, CFG.accents.violet,
                   CFG.accents.gold, CFG.accents.cyan, CFG.accents.mint, CFG.accents.lavender];

    var traces = [];
    selected.forEach(function (name, index) {
      var rows = bundle(name).churn.filter(function (r) { return r.start > 50; });
      if (!rows.length) return;
      traces.push({
        type: 'scatter', mode: 'lines+markers', name: name,
        x: rows.map(function (r) { return r.period + '-01'; }),
        y: rows.map(function (r) { return r.churn_pct; }),
        line: { color: palette[index % palette.length], width: 2 },
        marker: { size: 5 },
        customdata: rows.map(function (r) { return [r.lost, r.start]; }),
        hovertemplate: '<b>' + name + '</b><br>%{y:.2f}% churned' +
          '<br>%{customdata[0]:,} lost of %{customdata[1]:,}<extra></extra>'
      });
    });
    if (!traces.length) {
      return drawEmpty('fr-churn', 'Not enough membership history for the selection.', CFG.chartHeights.churn);
    }
    draw('fr-churn', traces, baseLayout(CFG.chartHeights.churn, {
      yaxis: { ticksuffix: '%', title: { text: 'Monthly churn' } }
    }));
  }

  function renderLifetime() {
    var buckets = bundle(state.client).lifetime.buckets;
    draw('fr-lifetime', [{
      type: 'bar',
      x: buckets.map(function (b) { return b.bucket; }),
      y: buckets.map(function (b) { return b.members; }),
      marker: { color: CFG.accents.green, line: { width: 0 } },
      hovertemplate: '<b>%{x}</b><br>%{y:,.0f} members<extra></extra>'
    }], baseLayout(CFG.chartHeights.lifetime, {
      hovermode: 'closest', showlegend: false,
      yaxis: { title: { text: 'Members' } },
      xaxis: { title: { text: 'Time as a member' } }
    }));
  }

  // ==========================================================================
  // Non-chart panels
  // ==========================================================================
  function tile(id, label, value, delta, direction, accent) {
    return '<div class="fr-tile fr-tile--' + accent + '">' +
      '<div class="fr-tile-label">' + label + '</div>' +
      '<div class="fr-tile-value" id="' + id + '-value">' + value + '</div>' +
      '<div class="fr-tile-delta fr-tile-delta--' + direction + '" id="' + id +
      '-delta">' + delta + '</div>' +
      '</div>';
  }

  function deltaChip(value) {
    if (Math.abs(value) < 0.05) return { text: 'flat vs. prior half', direction: 'flat' };
    return {
      text: (value > 0 ? '▲ ' : '▼ ') + group(Math.abs(value), 1) + '% vs. prior half',
      direction: value > 0 ? 'up' : 'down'
    };
  }

  function renderHero() {
    var w = currentWindow(), lo = w[0], hi = w[1];
    var s = series(state.client);
    var b = bundle(state.client);

    document.getElementById('fr-hero-client').textContent = state.client;
    document.getElementById('fr-hero-period').textContent = D.dates[lo] + ' → ' + D.dates[hi - 1];
    document.getElementById('fr-hero-value').textContent =
      fmtCompact(summarize(s.downloads.slice(lo, hi)).total, 'int');
    document.getElementById('fr-hero-insight').textContent =
      'Top market · ' + (b.locations.length ? b.locations[0].city : '—');

    var specs = [
      ['fr-kpi-dau', 'Avg Daily Active Users', summarize(s.dau.slice(lo, hi)).mean, 'dau', s.dau.slice(lo, hi), 'blue'],
      ['fr-kpi-members', 'Current Memberships', s.memberships[hi - 1], 'memberships', s.memberships.slice(lo, hi), 'green'],
      ['fr-kpi-revenue', 'Revenue', summarize(s.revenue.slice(lo, hi)).total, 'revenue', s.revenue.slice(lo, hi), 'gold'],
      ['fr-kpi-posts', 'Timeline Posts', summarize(s.posts.slice(lo, hi)).total, 'posts', s.posts.slice(lo, hi), 'violet']
    ];
    document.getElementById('fr-overview-tiles').innerHTML = specs.map(function (spec) {
      var chip = deltaChip(deltaPct(spec[4]));
      return tile(spec[0], spec[1], fmtCompact(spec[2], metricFormat(spec[3])),
                  chip.text, chip.direction, spec[5]);
    }).join('');
  }

  function renderSummaryTable() {
    var w = currentWindow(), lo = w[0], hi = w[1];
    var s = series(state.client);
    var keys = ['downloads', 'dau', 'mau', 'memberships', 'new_memberships',
                'revenue', 'posts', 'notifications', 'livestreams', 'auctions'];

    var head = '<thead><tr><th>Metric</th><th>Mean</th><th>Min</th><th>Max</th>' +
      '<th>Total</th><th>Latest</th></tr></thead>';
    var body = keys.map(function (key) {
      var stats = summarize(s[key].slice(lo, hi));
      var kind = metricFormat(key);
      // Totals are meaningless for stock metrics (a membership count is not
      // additive across days), so those rows show the closing level instead.
      var total = STOCK_METRICS[key] ? '—' : fmtValue(stats.total, kind);
      return '<tr><td>' + metricLabel(key) + '</td><td>' + fmtValue(stats.mean, kind) +
        '</td><td>' + fmtValue(stats.min, kind) + '</td><td>' + fmtValue(stats.max, kind) +
        '</td><td>' + total + '</td><td>' + fmtValue(stats.last, kind) + '</td></tr>';
    }).join('');

    document.getElementById('fr-summary-table').innerHTML = head + '<tbody>' + body + '</tbody>';
  }

  function renderRevenueKpis() {
    var w = currentWindow(), lo = w[0], hi = w[1];
    var b = bundle(state.client), s = b.series;

    var revenue = summarize(s.revenue.slice(lo, hi)).total;
    var revChip = deltaChip(deltaPct(s.revenue.slice(lo, hi)));
    var members = summarize(s.memberships.slice(lo, hi)).mean || 1;
    var arpm = revenue / members / Math.max(hi - lo, 1) * 30.44;

    var churnRows = b.churn.filter(function (r) { return r.start > 50; });
    var churnValue = '—', churnNote = 'not enough history', churnDir = 'flat';
    if (churnRows.length) {
      var latest = churnRows[churnRows.length - 1];
      var prior = churnRows.length > 1 ? churnRows[churnRows.length - 2].churn_pct : latest.churn_pct;
      churnValue = fmtValue(latest.churn_pct, 'percent');
      churnNote = group(latest.lost, 0) + ' of ' + group(latest.start, 0) +
        ' members in ' + latest.period;
      // Falling churn is good news, so the chip color is inverted here.
      churnDir = latest.churn_pct < prior ? 'up' : (latest.churn_pct > prior ? 'down' : 'flat');
    }

    var life = b.lifetime;
    document.getElementById('fr-revenue-tiles').innerHTML = [
      tile('fr-rev-total', 'Revenue in window', fmtCompact(revenue, 'money'),
           revChip.text, revChip.direction, 'gold'),
      tile('fr-rev-arpm', 'Revenue per member / mo', '$' + group(arpm, 2),
           'per member per 30 days', 'flat', 'amber'),
      tile('fr-rev-churn', 'Latest monthly churn', churnValue, churnNote, churnDir, 'coral'),
      tile('fr-rev-tenure', 'Median membership tenure', group(life.median_days, 0) + ' days',
           'mean ' + group(life.mean_days, 0) + ' days · ' + group(life.active_members, 0) + ' members',
           'flat', 'green')
    ].join('');
  }

  function renderTopUsers() {
    var records = bundle(state.client).top_users.slice(0, 12);
    var showAccount = records.some(function (r) { return r.client; });

    var columns = ['#', 'Fan', 'Tier', 'Location', 'Sessions', 'Time in app', 'Posts', 'Spend'];
    if (showAccount) columns.splice(2, 0, 'Account');

    var head = '<thead><tr>' + columns.map(function (c) {
      var textual = ['#', 'Fan', 'Tier', 'Location', 'Account'].indexOf(c) >= 0;
      return '<th' + (textual ? ' class="fr-cell-text"' : '') + '>' + c + '</th>';
    }).join('') + '</tr></thead>';

    var body = records.map(function (r) {
      var cells = [
        ['#', r.rank, true],
        ['Fan', '@' + r.handle, true]
      ];
      if (showAccount) cells.push(['Account', r.client || state.client, true]);
      cells.push(
        ['Tier', r.membership, true],
        ['Location', r.city, true],
        ['Sessions', group(r.sessions, 0), false],
        ['Time in app', group(Math.round(r.minutes / 60), 0) + ' h', false],
        ['Posts', group(r.posts, 0), false],
        ['Spend', '$' + group(r.spend, 0), false]
      );
      return '<tr>' + cells.map(function (c) {
        return '<td' + (c[2] ? ' class="fr-cell-text"' : '') + '>' + c[1] + '</td>';
      }).join('') + '</tr>';
    }).join('');

    document.getElementById('fr-top-users').innerHTML = head + '<tbody>' + body + '</tbody>';
  }

  // ==========================================================================
  // Rendering orchestration
  // ==========================================================================
  // Only the visible section is drawn: plotly.js sizes a chart from its
  // container, and a container inside a display:none panel measures zero.
  // Sections are re-rendered when they become visible.
  var RENDERERS = {
    overview: function () { renderHero(); renderTrend(); renderSummaryTable(); },
    audience: function () {
      renderGeoKpis(); renderMap(); renderMapDetail(); renderGrowth();
      renderTopMarkets(); renderSegmentMix(); renderLocationBar();
    },
    behavior: function () { renderScatter(); renderCorrelation(); renderEngagement(); },
    revenue: function () {
      renderRevenueKpis(); renderRevenue(); renderRevenueMix();
      renderChurn(); renderLifetime(); renderTopUsers();
    }
  };

  var dirty = { overview: true, audience: true, behavior: true, revenue: true };

  function invalidate(sections) {
    (sections || Object.keys(dirty)).forEach(function (s) { dirty[s] = true; });
    renderActive();
  }

  function renderActive() {
    if (dirty[state.section]) {
      RENDERERS[state.section]();
      dirty[state.section] = false;
    }
  }

  function showSection(section) {
    state.section = section;
    Object.keys(RENDERERS).forEach(function (key) {
      var panel = document.getElementById('fr-panel-' + key);
      panel.className = 'fr-panel' + (key === section ? '' : ' fr-panel--hidden');
    });
    renderActive();
  }

  // ==========================================================================
  // Control wiring
  // ==========================================================================
  function fillSelect(id, options, value) {
    var el = document.getElementById(id);
    el.innerHTML = options.map(function (o) {
      return '<option value="' + o.value + '"' + (o.value === value ? ' selected' : '') + '>' +
        o.label + '</option>';
    }).join('');
    return el;
  }

  function metricOptions() {
    return CFG.axisMetrics.map(function (k) { return { value: k, label: metricLabel(k) }; });
  }

  function onSelect(id, key, sections) {
    document.getElementById(id).addEventListener('change', function (e) {
      state[key] = e.target.value;
      invalidate(sections);
    });
  }

  function buildControls() {
    fillSelect('fr-client', CFG.clients.map(function (c) { return { value: c, label: c }; }), state.client);
    document.getElementById('fr-client').addEventListener('change', function (e) {
      state.client = e.target.value;
      state.mapSelection = null;   // the drilldown belongs to the previous account
      invalidate(null);
    });

    document.getElementById('fr-preset').innerHTML = CFG.presets.map(function (p) {
      return '<label class="fr-segmented-label"><input class="fr-segmented-input" type="radio" ' +
        'name="fr-preset" value="' + p.label + '"' + (p.label === state.preset ? ' checked' : '') +
        ' />' + p.label + '</label>';
    }).join('');
    document.getElementById('fr-preset').addEventListener('change', function (e) {
      state.preset = e.target.value;
      // The audience panel is history-wide, so the date window never changes it.
      invalidate(['overview', 'behavior', 'revenue']);
    });

    fillSelect('fr-left-metric', metricOptions(), state.left);
    fillSelect('fr-right-metric', metricOptions(), state.right);
    onSelect('fr-left-metric', 'left', ['overview']);
    onSelect('fr-right-metric', 'right', ['overview']);
    onSelect('fr-grain', 'grain', ['overview']);
    document.getElementById('fr-show-events').addEventListener('change', function (e) {
      state.events = e.target.checked;
      invalidate(['overview']);
    });

    fillSelect('fr-map-metric', Object.keys(CFG.heatmap.metrics).map(function (key) {
      return { value: key, label: CFG.heatmap.metrics[key].label };
    }), state.mapMetric);
    document.getElementById('fr-map-display').addEventListener('change', function (e) {
      state.display = e.target.value;
      syncMapControls();
      invalidate(['audience']);
    });
    onSelect('fr-map-metric', 'mapMetric', ['audience']);
    syncMapControls();

    document.getElementById('fr-segments').innerHTML = SEGMENT_NAMES.map(function (name) {
      return '<label class="fr-checklist-label"><input class="fr-checkbox" type="checkbox" value="' +
        name + '" checked />' + name + '</label>';
    }).join('');
    document.getElementById('fr-segments').addEventListener('change', function () {
      state.segments = readChecked('fr-segments');
      invalidate(['audience']);
    });
    syncMapControls();   // the checklist did not exist on the first call

    document.getElementById('fr-loc-level').addEventListener('change', function (e) {
      state.locLevel = e.target.value;
      // A market name is only meaningful at the level it was picked from.
      state.mapSelection = null;
      invalidate(['audience']);
    });
    fillSelect('fr-loc-segment',
      [{ value: 'All', label: 'All users' }].concat(SEGMENT_NAMES.map(function (n) {
        return { value: n, label: n };
      })), 'All');
    onSelect('fr-loc-segment', 'locSegment', ['audience']);

    fillSelect('fr-x-metric', metricOptions(), state.x);
    fillSelect('fr-y-metric', metricOptions(), state.y);
    onSelect('fr-x-metric', 'x', ['behavior']);
    onSelect('fr-y-metric', 'y', ['behavior']);

    onSelect('fr-rev-grain', 'revGrain', ['revenue']);
    document.getElementById('fr-churn-clients').innerHTML = CFG.clients.map(function (c) {
      var checked = state.churnClients.indexOf(c) >= 0;
      return '<label class="fr-checklist-label"><input class="fr-checkbox" type="checkbox" value="' +
        c + '"' + (checked ? ' checked' : '') + ' />' + c + '</label>';
    }).join('');
    document.getElementById('fr-churn-clients').addEventListener('change', function () {
      state.churnClients = readChecked('fr-churn-clients');
      invalidate(['revenue']);
    });

    document.getElementById('fr-section').addEventListener('change', function (e) {
      showSection(e.target.value);
    });

    // plotly.js `responsive` only reflows charts that are currently laid out, so
    // hidden panels are marked dirty and redrawn when the viewer opens them.
    var resizeTimer = null;
    window.addEventListener('resize', function () {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(function () {
        Object.keys(dirty).forEach(function (key) {
          if (key !== state.section) dirty[key] = true;
        });
      }, 200);
    });
  }

  /* Grey out the controls a display mode does not use: the individual view has
     no metric to size by, and the aggregate views have no per-user markers to cap
     or filter. */
  function syncMapControls() {
    var individual = state.display === 'individual';
    document.getElementById('fr-map-metric').disabled = individual;
    document.getElementById('fr-segments')
      .querySelectorAll('input').forEach(function (input) { input.disabled = !individual; });
  }

  function readChecked(containerId) {
    return Array.prototype.slice
      .call(document.getElementById(containerId).querySelectorAll('input:checked'))
      .map(function (input) { return input.value; });
  }

  // ==========================================================================
  // Boot
  // ==========================================================================
  function failGracefully(message) {
    document.querySelectorAll('.fr-chart').forEach(function (el) {
      el.innerHTML = '<p class="fr-loading">' + message + '</p>';
    });
  }

  fetch(DATA_URL)
    .then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(function (payload) {
      D = payload;
      CFG = payload.config;
      SEGMENT_NAMES = CFG.segments.map(function (s) { return s.name; });
      CFG.segments.forEach(function (s) { SEGMENT_COLORS[s.name] = s.color; });

      state.client = CFG.defaultClient;
      state.preset = CFG.defaultPreset;
      state.segments = SEGMENT_NAMES.slice();
      state.churnClients = CFG.accounts.slice(0, 3);

      document.getElementById('fr-data-window').textContent =
        payload.startDate + ' → ' + payload.endDate;
      // Described from the payload, so the panel cannot claim a shape the data
      // does not have.
      document.getElementById('fr-spec-dataset').textContent =
        payload.dates.length + ' days · ' + CFG.clients.length + ' accounts · seeded';

      buildControls();
      showSection('overview');
    })
    .catch(function (error) {
      failGracefully('Could not load the demo dataset (' + error.message + ').');
    });
})();
