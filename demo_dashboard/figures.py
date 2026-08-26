"""Plotly figure builders for the Tidepool Commerce Analytics demo dashboard.

Every chart on the page is built here, so the Dash page stays a layout and
callback module and the static twin has one file to mirror. Three conventions
run through all of them:

  * **Height lives in CHART_HEIGHTS, not in the individual builders.** The same
    number feeds ``layout.height`` and the CSS height of the container that holds
    the graph. A responsive Plotly graph with no CSS height collapses to zero on
    a width change while the figure keeps its own height, and the SVG then draws
    outside its card.

  * **Numbers are formatted in one place.** ``fmt_value`` and ``fmt_compact``
    route through ``round_half_up`` because Python's ``format`` rounds ties to
    even and JavaScript's ``toLocaleString`` rounds them away from zero; without
    a shared rule the two builds disagree in the last digit.

  * **Colour never encodes a category and a quantity at once.** Ordered
    dimensions get a single-hue sequential ramp, nominal ones get the
    lightness-separated categorical palette, and continuous quantities get a
    diverging ramp with a meaningful midpoint.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

import plotly.graph_objects as go

from demo_dashboard import data as demo_data
from demo_dashboard.config import (
    ACCENT,
    ACCENT_DEEP,
    ACCENT_SOFT,
    ANOMALY_METRICS,
    ANOMALY_Z,
    AOV_SCALE,
    CATEGORY_COLORS,
    CATEGORY_NAMES,
    CHANNEL_COLORS,
    CHANNEL_NAMES,
    NEGATIVE,
    NEUTRAL,
    PALETTE,
    POSITIVE,
    RETENTION_SCALE,
    RETURN_REASON_COLORS,
    RETURN_REASON_NAMES,
    SEQUENTIAL,
    SOURCE_COLORS,
    SPLOM_METRICS,
    SURFACE,
    VALUE_TIER_COLORS,
    VALUE_TIER_NAMES,
    metric_color,
    metric_format,
    metric_label,
)
from demo_dashboard.data import EVENT_KINDS
from demo_dashboard.geo import (
    RECENCY_CUT,
    RFM_QUADRANTS,
    aggregate_by_level,
    rfm_points,
    scatter_orders,
)


# --------------------------------------------------------------------------
# Chart heights
# --------------------------------------------------------------------------
# The single source of truth. ``pages/dashboard.py`` reads the same dict to pin
# the container height in CSS; see the module docstring for why that matters.
CHART_HEIGHTS = {
    'trend': 430,
    'driver': 400,
    'splom': 520,
    'category_waterfall': 400,
    'category_share': 360,
    'cohort': 520,
    'cohort_curves': 360,
    'rfm': 470,
    'decile': 340,
    'channel_area': 380,
    'source_bars': 400,
    'event_study': 430,
    'promo_bars': 340,
    'discount': 320,
    'map': 560,
    'growth_map': 520,
    'market_bars': 400,
    'return_trend': 340,
    'return_category': 340,
    'return_reason': 340,
}

# One typeface, shared with the site around it. Both names resolve to Inter;
# they stay separate so each call still says which role it is playing — display
# type against UI type — rather than collapsing the distinction into one name.
FONT = {
    'family': 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
    'color': SURFACE['text_secondary'],
    'size': 12,
}
SERIF = 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif'

# Fills lighter than this contrast ratio against the card carry an outline, so
# the shape still reads when the colour does not.
MARKER_LINE = 'rgba(28, 25, 23, 0.28)'

# Metrics that are levels rather than flows: rolling one up to a coarser grain
# means taking the period's last value, not adding the days together.
STOCK_METRICS = {'monthly_customers'}
# Metrics that are ratios: they roll up by re-dividing summed terms.
RATIO_METRICS = set(demo_data.DERIVED)


# --------------------------------------------------------------------------
# Formatting
# --------------------------------------------------------------------------
def round_half_up(value: float, decimals: int = 0) -> float:
    """Round half away from zero, matching the JavaScript mirror.

    Python's ``format`` rounds ties to even and JavaScript's ``toLocaleString``
    rounds them away from zero, so ``932.15`` renders as ``932.1`` in one build
    and ``932.2`` in the other. Every formatter below goes through this.
    """
    if value != value or value in (float('inf'), float('-inf')):
        return value
    factor = 10 ** decimals
    scaled = value * factor
    shifted = math.floor(abs(scaled) + 0.5)
    return math.copysign(shifted, scaled) / factor


def group(value: float, decimals: int = 0) -> str:
    return f'{round_half_up(value, decimals):,.{decimals}f}'


def fmt_value(value: float, kind: str = 'int') -> str:
    if value is None:
        return '—'
    if kind == 'money':
        return '$' + group(value)
    if kind == 'money2':
        return '$' + group(value, 2)
    if kind == 'percent':
        return group(value * 100, 1) + '%'
    if kind == 'percent2':
        return group(value * 100, 2) + '%'
    if kind == 'ratio':
        return group(value, 2) + 'x'
    return group(value)


def fmt_compact(value: float, kind: str = 'int') -> str:
    """Short form for headline numbers: 1.2M, $932.1K."""
    prefix = '$' if kind in ('money', 'money2') else ''
    if kind in ('percent', 'percent2'):
        return fmt_value(value, kind)
    magnitude = abs(value)
    if magnitude >= 1_000_000_000:
        return f'{prefix}{group(value / 1_000_000_000, 1)}B'
    if magnitude >= 1_000_000:
        return f'{prefix}{group(value / 1_000_000, 1)}M'
    if magnitude >= 10_000:
        return f'{prefix}{group(value / 1_000, 1)}K'
    if kind == 'money2':
        return fmt_value(value, kind)
    return f'{prefix}{group(value)}'


def _hover_number(kind: str) -> str:
    if kind == 'money':
        return '$%{y:,.0f}'
    if kind == 'money2':
        return '$%{y:,.2f}'
    if kind == 'percent':
        return '%{y:.1%}'
    if kind == 'percent2':
        return '%{y:.2%}'
    return '%{y:,.0f}'


def _axis_tick(kind: str) -> Dict[str, object]:
    if kind in ('money', 'money2'):
        # SI units on the axis: a tick reading "$25M" carries the same
        # information as "$25,000,000" and leaves room for the chart.
        return {'tickprefix': '$', 'tickformat': '~s'}
    if kind == 'percent':
        return {'tickformat': '.1%'}
    if kind == 'percent2':
        return {'tickformat': '.2%'}
    return {'tickformat': ',.0f'}


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------
def _deep_merge(base: Dict[str, object], extra: Dict[str, object]) -> Dict[str, object]:
    out = dict(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def base_layout(height: int = 420, **overrides) -> Dict[str, object]:
    """Shared layout: transparent paper on the card, hairline grid, no chrome."""
    layout: Dict[str, object] = {
        'height': height,
        'paper_bgcolor': SURFACE['bg'],
        'plot_bgcolor': SURFACE['bg'],
        'font': dict(FONT),
        'margin': {'l': 62, 'r': 26, 't': 18, 'b': 44},
        'hoverlabel': {
            'bgcolor': '#FFFFFF',
            'bordercolor': SURFACE['border'],
            'font': {'color': SURFACE['text'], 'size': 12,
                     'family': FONT['family']},
        },
        'xaxis': {
            'gridcolor': SURFACE['grid'],
            'zerolinecolor': SURFACE['zeroline'],
            'linecolor': SURFACE['border'],
            'tickfont': {'size': 11, 'color': SURFACE['text_muted']},
            'title': {'font': {'size': 11.5, 'color': SURFACE['text_secondary']}},
            'automargin': True,
        },
        'yaxis': {
            'gridcolor': SURFACE['grid'],
            'zerolinecolor': SURFACE['zeroline'],
            'linecolor': 'rgba(0,0,0,0)',
            'tickfont': {'size': 11, 'color': SURFACE['text_muted']},
            'title': {'font': {'size': 11.5, 'color': SURFACE['text_secondary']}},
            'automargin': True,
        },
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom', 'y': 1.02,
            'xanchor': 'left', 'x': 0,
            'font': {'size': 11.5, 'color': SURFACE['text_secondary']},
            'bgcolor': 'rgba(0,0,0,0)',
        },
        'colorway': list(PALETTE),
        'dragmode': 'pan',
    }
    return _deep_merge(layout, overrides)


def empty_figure(message: str, height: int = None) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(**base_layout(
        height or 300,
        xaxis={'visible': False}, yaxis={'visible': False},
        annotations=[{
            'text': message, 'showarrow': False,
            'font': {'size': 13, 'color': SURFACE['text_muted']},
            'xref': 'paper', 'yref': 'paper', 'x': 0.5, 'y': 0.5,
        }],
    ))
    return fig


def _soft(hex_color: str, alpha: float = 0.14) -> str:
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f'rgba({r}, {g}, {b}, {alpha})'


def _series(bundle, key: str) -> List[float]:
    return demo_data.series_for(bundle, key)


def _grain_series(dataset, bundle, key: str, lo: int, hi: int, grain: str):
    """A metric at the requested grain, rolled up the way that metric should be."""
    dates = dataset['dates'][lo:hi]
    if key in RATIO_METRICS:
        top, bottom = demo_data.DERIVED[key]
        return demo_data.resample_ratio(
            dates, bundle['series'][top][lo:hi], bundle['series'][bottom][lo:hi], grain)
    how = 'last' if key in STOCK_METRICS else 'sum'
    return demo_data.resample(dates, _series(bundle, key)[lo:hi], grain, how)


# ==========================================================================
# Sales Performance — Revenue & Orders
# ==========================================================================
def trend_figure(dataset, brand: str, lo: int, hi: int,
                 left: str = 'revenue', right: str = 'orders',
                 grain: str = 'daily', overlay: bool = True,
                 mark_anomalies: bool = True) -> go.Figure:
    """Two metrics on independent axes, with the promotion calendar overlaid and
    outliers called out on the series itself.

    The callouts replace a separate diagnostics panel. A panel of summary cards
    can tell you a series was volatile; it cannot tell you *which day*, and the
    day is the only part anyone acts on. Marking the point in place — and listing
    the same points beside the chart — keeps the finding and its evidence in one
    glance.
    """
    bundle = dataset['brands'][brand]
    labels, left_values = _grain_series(dataset, bundle, left, lo, hi, grain)
    _, right_values = _grain_series(dataset, bundle, right, lo, hi, grain)

    left_kind, right_kind = metric_format(left), metric_format(right)
    left_color, right_color = ACCENT_DEEP, POSITIVE

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels, y=left_values, name=metric_label(left),
        mode='lines', line={'color': left_color, 'width': 2.1},
        fill='tozeroy', fillcolor=_soft(left_color, 0.10),
        hovertemplate=f'%{{x}}<br>{metric_label(left)}: {_hover_number(left_kind)}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=labels, y=right_values, name=metric_label(right), yaxis='y2',
        mode='lines', line={'color': right_color, 'width': 1.9, 'dash': 'solid'},
        hovertemplate=f'%{{x}}<br>{metric_label(right)}: {_hover_number(right_kind)}<extra></extra>',
    ))

    layout = base_layout(
        CHART_HEIGHTS['trend'],
        margin={'l': 66, 'r': 66, 't': 56, 'b': 46},
        xaxis={'title': None},
        yaxis=_deep_merge({'title': {'text': metric_label(left)},
                           'tickfont': {'color': left_color}}, _axis_tick(left_kind)),
        yaxis2=_deep_merge({
            'title': {'text': metric_label(right),
                      'font': {'size': 11.5, 'color': right_color}},
            'overlaying': 'y', 'side': 'right', 'showgrid': False,
            'tickfont': {'size': 11, 'color': right_color},
            'automargin': True,
        }, _axis_tick(right_kind)),
        hovermode='x unified',
    )
    fig.update_layout(**layout)

    if overlay:
        _add_promotion_overlay(fig, bundle, dataset['dates'], lo, hi, grain)
    if mark_anomalies and grain == 'daily':
        _add_anomaly_callouts(fig, labels, left_values, left, left_kind)
    return fig


def _add_promotion_overlay(fig: go.Figure, bundle, all_dates: Sequence[str],
                           lo: int, hi: int, grain: str) -> None:
    """Promotion markers on the time axis, one legend entry per kind.

    At a coarse grain the markers are snapped to the bucket they fall in;
    plotting a daily date against a monthly axis puts the marker in the gutter.
    """
    events = demo_data.events_in_window(bundle['events'], all_dates, lo, hi)
    if not events:
        return

    def bucket(iso: str) -> str:
        if grain == 'daily':
            return iso
        if grain == 'monthly':
            return iso[:7]
        if grain == 'quarterly':
            month = int(iso[5:7])
            return f'{iso[:4]}-Q{(month - 1) // 3 + 1}'
        year, month, day = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
        from datetime import date as _date, timedelta as _td
        here = _date(year, month, day)
        return (here - _td(days=here.weekday())).isoformat()

    grouped: Dict[str, List[str]] = {}
    for event in events:
        grouped.setdefault(event['kind'], []).append(bucket(event['date']))

    for kind, positions in grouped.items():
        colour = EVENT_KINDS[kind]['color']
        for position in positions:
            fig.add_vline(x=position, line={'color': _soft(colour, 0.42),
                                            'width': 1, 'dash': 'dot'})
        fig.add_trace(go.Scatter(
            x=positions, y=[None] * len(positions), name=kind,
            mode='markers', marker={'color': colour, 'size': 8, 'symbol': 'triangle-down'},
            hoverinfo='skip', showlegend=True,
        ))


def _add_anomaly_callouts(fig: go.Figure, labels: Sequence[str],
                          values: Sequence[float], key: str, kind: str) -> None:
    """Ring and label the outliers on the primary series."""
    found = demo_data.detect_anomalies(list(values), list(labels), ANOMALY_Z)
    if not found:
        return

    # Label at most the four largest, or the annotations collide into a smear.
    ranked = sorted(found, key=lambda a: -abs(a['z']))[:4]
    fig.add_trace(go.Scatter(
        x=[a['date'] for a in found], y=[a['value'] for a in found],
        mode='markers', name='Outlier',
        marker={'size': 11, 'color': 'rgba(0,0,0,0)',
                'line': {'color': NEGATIVE, 'width': 1.8}},
        hovertemplate=('%{x}<br>' + metric_label(key) + ': ' + _hover_number(kind)
                       + '<br>%{customdata:+.1f} robust z<extra>Outlier</extra>'),
        customdata=[a['z'] for a in found],
    ))
    for anomaly in ranked:
        fig.add_annotation(
            x=anomaly['date'], y=anomaly['value'],
            text=f"{'+' if anomaly['pct'] >= 0 else ''}{group(anomaly['pct'])}%",
            showarrow=True, arrowhead=0, arrowwidth=1,
            arrowcolor=_soft(NEGATIVE, 0.55),
            ax=0, ay=-26,
            font={'size': 10.5, 'color': NEGATIVE, 'family': FONT['family']},
            bgcolor='rgba(255,255,255,0.86)', borderpad=2,
        )


def anomaly_log(dataset, brand: str, lo: int, hi: int, limit: int = 8):
    """The anomalies behind the callouts, as rows for the side panel.

    Scanning several metrics rather than only the plotted one is the point: a
    revenue spike with no matching visits spike is a different event from one
    with it, and the side panel is where that comparison is cheap.
    """
    bundle = dataset['brands'][brand]
    dates = dataset['dates'][lo:hi]
    rows = []
    for key in ANOMALY_METRICS:
        values = _series(bundle, key)[lo:hi]
        for anomaly in demo_data.detect_anomalies(values, dates, ANOMALY_Z):
            rows.append({
                'date': anomaly['date'],
                'metric': metric_label(key),
                'value': fmt_value(anomaly['value'], metric_format(key)),
                'baseline': fmt_value(anomaly['baseline'], metric_format(key)),
                'pct': anomaly['pct'],
                'z': anomaly['z'],
                'direction': anomaly['direction'],
                'context': _nearest_event(bundle, dataset['dates'], anomaly['date']),
            })
    rows.sort(key=lambda r: -abs(r['z']))
    return rows[:limit], len(rows)


def _nearest_event(bundle, all_dates: Sequence[str], iso: str, span: int = 3):
    """The promotion, if any, that plausibly explains an anomaly."""
    try:
        index = all_dates.index(iso)
    except ValueError:
        return None
    best = None
    for event in bundle['events']:
        delta = index - event['day_index']
        if 0 <= delta <= span and (best is None or delta < best[0]):
            best = (delta, event['kind'])
    return best[1] if best else None


def kpi_tiles(dataset, brand: str, lo: int, hi: int):
    """Headline numbers for the top strip, with window-half change."""
    bundle = dataset['brands'][brand]
    tiles = []
    for key in ('revenue', 'orders', 'aov', 'conversion', 'new_customers'):
        values = _series(bundle, key)[lo:hi]
        kind = metric_format(key)
        if key in RATIO_METRICS:
            top, bottom = demo_data.DERIVED[key]
            headline = (sum(bundle['series'][top][lo:hi])
                        / max(sum(bundle['series'][bottom][lo:hi]), 1e-9))
        else:
            headline = sum(values)
        tiles.append({
            'key': key,
            'label': metric_label(key),
            'value': fmt_compact(headline, kind),
            'delta': demo_data.prior_period_delta(bundle, key, lo, hi),
        })
    return tiles


def comparison_label(lo: int, hi: int) -> str:
    """What every delta on the page is measured against."""
    return f'vs prior {hi - lo} days'


# ==========================================================================
# Sales Performance — Revenue Drivers
# ==========================================================================
def driver_waterfall(dataset, brand: str, lo: int, hi: int) -> go.Figure:
    """Period-over-period revenue change, split into the factors that caused it.

    Revenue is exactly visits x conversion x AOV, so the change decomposes by
    substituting one factor at a time. The bars therefore sum to the total with
    no residual and no attribution model — this is arithmetic, and it answers the
    question a correlation table only gestures at: not *what moves with revenue*
    but *what moved it, and by how much*.
    """
    bundle = dataset['brands'][brand]
    walk = demo_data.driver_decomposition(bundle, lo, hi)
    if not walk['terms']:
        return empty_figure('Not enough history for a prior period.',
                            CHART_HEIGHTS['driver'])

    labels = ['Prior period'] + [term['label'] for term in walk['terms']] + ['This period']
    measures = ['absolute'] + ['relative'] * len(walk['terms']) + ['total']
    values = ([walk['prior']]
              + [term['contribution'] for term in walk['terms']]
              + [walk['current']])

    text = [fmt_compact(walk['prior'], 'money')]
    for term in walk['terms']:
        sign = '+' if term['contribution'] >= 0 else '−'
        text.append(sign + fmt_compact(abs(term['contribution']), 'money'))
    text.append(fmt_compact(walk['current'], 'money'))

    detail = ['Revenue in the equivalent window before this one']
    for term in walk['terms']:
        kind = metric_format(term['key'])
        detail.append(f"{fmt_value(term['prior'], kind)} → {fmt_value(term['current'], kind)}")
    detail.append('Revenue in the selected window')

    fig = go.Figure(go.Waterfall(
        orientation='v',
        measure=measures,
        x=labels,
        y=values,
        text=text,
        textposition='outside',
        textfont={'size': 11.5, 'color': SURFACE['text']},
        customdata=detail,
        connector={'line': {'color': SURFACE['border'], 'width': 1}},
        increasing={'marker': {'color': POSITIVE}},
        decreasing={'marker': {'color': NEGATIVE}},
        totals={'marker': {'color': NEUTRAL}},
        hovertemplate='%{x}<br>%{customdata}<extra></extra>',
    ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['driver'],
        margin={'l': 66, 'r': 26, 't': 30, 'b': 56},
        yaxis=_deep_merge({'title': {'text': 'Revenue'}}, _axis_tick('money')),
        xaxis={'tickangle': 0},
        showlegend=False,
    ))
    return fig


def driver_summary(dataset, brand: str, lo: int, hi: int):
    """One sentence naming the factor that did the most work."""
    walk = demo_data.driver_decomposition(dataset['brands'][brand], lo, hi)
    if not walk['terms']:
        return None
    biggest = max(walk['terms'], key=lambda t: abs(t['contribution']))
    share = abs(biggest['contribution']) / max(abs(walk['change']), 1e-9)
    direction = 'rose' if walk['change'] >= 0 else 'fell'
    return {
        'change': walk['change'],
        'change_pct': (walk['change'] / walk['prior'] * 100.0) if walk['prior'] else 0.0,
        'driver': biggest['label'],
        'driver_share': share,
        'direction': direction,
        'text': (f"Revenue {direction} {fmt_compact(abs(walk['change']), 'money')} "
                 f"against the prior {walk['span']} days. "
                 f"{biggest['label']} accounts for {group(share * 100)}% of the move."),
    }


def metric_splom(dataset, brand: str, lo: int, hi: int) -> go.Figure:
    """Scatter-plot matrix across the core trading metrics.

    A matrix of correlation *coefficients* compresses each pair to one number and
    hides the thing that matters — whether the relationship is linear, saturating
    or driven by a handful of promotion days. The scatter matrix shows every pair
    at once and costs nothing to read: a widening cone means the spread grows
    with the level, a hook means saturation, and a detached cluster is usually
    the promotion calendar.
    """
    bundle = dataset['brands'][brand]
    dimensions = []
    for key in SPLOM_METRICS:
        values = _series(bundle, key)[lo:hi]
        if not any(values):
            continue
        dimensions.append({'label': metric_label(key), 'values': values})

    if len(dimensions) < 2:
        return empty_figure('Not enough data in this window.', CHART_HEIGHTS['splom'])

    # Colour by position in the window so the eye can follow time through the
    # cloud — a scatter matrix with one flat colour cannot show a trend at all.
    span = len(dimensions[0]['values'])
    fig = go.Figure(go.Splom(
        dimensions=dimensions,
        diagonal={'visible': False},
        showupperhalf=False,
        marker={
            'size': 3.4,
            'color': list(range(span)),
            'colorscale': [[position, colour] for position, colour
                           in [(index / (len(SEQUENTIAL) - 1), c)
                               for index, c in enumerate(reversed(SEQUENTIAL))]],
            'opacity': 0.62,
            'line': {'width': 0},
            'showscale': True,
            'colorbar': {
                'title': {'text': 'Day in window', 'side': 'right',
                          'font': {'size': 11, 'color': SURFACE['text_secondary']}},
                'thickness': 9, 'len': 0.55, 'y': 0.5,
                'outlinewidth': 0,
                'tickvals': [0, span - 1], 'ticktext': ['start', 'end'],
                'tickfont': {'size': 10, 'color': SURFACE['text_muted']},
            },
        },
        hoverinfo='skip',
    ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['splom'],
        margin={'l': 78, 'r': 26, 't': 22, 'b': 62},
        dragmode='select',
    ))
    fig.update_traces(showlowerhalf=True)
    for axis in list(fig.layout):
        if axis.startswith('xaxis') or axis.startswith('yaxis'):
            fig.layout[axis].update(
                gridcolor=SURFACE['grid'], zerolinecolor=SURFACE['zeroline'],
                linecolor=SURFACE['border'],
                tickfont={'size': 9.5, 'color': SURFACE['text_muted']},
                title_font={'size': 10.5, 'color': SURFACE['text_secondary']},
            )
    return fig


# ==========================================================================
# Sales Performance — Category Mix
# ==========================================================================
def category_waterfall(dataset, brand: str, lo: int, hi: int) -> go.Figure:
    """Which categories carried the revenue change, largest mover first."""
    bundle = dataset['brands'][brand]
    dates = dataset['dates']
    span = hi - lo
    prior_lo = max(lo - span, 0)
    if prior_lo >= lo:
        return empty_figure('Not enough history for a prior period.',
                            CHART_HEIGHTS['category_waterfall'])

    current_months = set(m[:7] for m in dates[lo:hi])
    prior_months = set(m[:7] for m in dates[prior_lo:lo])

    current = {name: 0.0 for name in CATEGORY_NAMES}
    prior = {name: 0.0 for name in CATEGORY_NAMES}
    for row in bundle['category_mix']:
        target = current if row['period'] in current_months else (
            prior if row['period'] in prior_months else None)
        if target is None:
            continue
        for name, value in row['revenue'].items():
            target[name] += value

    moves = sorted(((name, current[name] - prior[name]) for name in CATEGORY_NAMES),
                   key=lambda item: -abs(item[1]))
    prior_total = sum(prior.values())
    current_total = sum(current.values())

    labels = ['Prior period'] + [name for name, _ in moves] + ['This period']
    measures = ['absolute'] + ['relative'] * len(moves) + ['total']
    values = [prior_total] + [move for _, move in moves] + [current_total]
    text = [fmt_compact(prior_total, 'money')]
    for name, move in moves:
        text.append(('+' if move >= 0 else '−') + fmt_compact(abs(move), 'money'))
    text.append(fmt_compact(current_total, 'money'))

    detail = ['Revenue in the equivalent window before this one']
    for name, _ in moves:
        detail.append(f"{fmt_compact(prior[name], 'money')} → "
                      f"{fmt_compact(current[name], 'money')}")
    detail.append('Revenue in the selected window')

    fig = go.Figure(go.Waterfall(
        orientation='v', measure=measures, x=labels, y=values,
        text=text, textposition='outside',
        textfont={'size': 11, 'color': SURFACE['text']},
        customdata=detail,
        connector={'line': {'color': SURFACE['border'], 'width': 1}},
        increasing={'marker': {'color': POSITIVE}},
        decreasing={'marker': {'color': NEGATIVE}},
        totals={'marker': {'color': NEUTRAL}},
        hovertemplate='%{x}<br>%{customdata}<extra></extra>',
    ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['category_waterfall'],
        margin={'l': 66, 'r': 26, 't': 30, 'b': 74},
        yaxis=_deep_merge({'title': {'text': 'Revenue'}}, _axis_tick('money')),
        xaxis={'tickangle': -22},
        showlegend=False,
    ))
    return fig


def category_share_area(dataset, brand: str, normalise: bool = True) -> go.Figure:
    """Category revenue over time, as a share of the month or in dollars."""
    bundle = dataset['brands'][brand]
    rows = [row for row in bundle['category_mix'] if sum(row['revenue'].values()) > 0]
    if not rows:
        return empty_figure('No category revenue yet.', CHART_HEIGHTS['category_share'])

    periods = [row['period'] for row in rows]
    fig = go.Figure()
    for name in CATEGORY_NAMES:
        values = []
        for row in rows:
            total = sum(row['revenue'].values()) or 1.0
            value = row['revenue'].get(name, 0.0)
            values.append(value / total if normalise else value)
        fig.add_trace(go.Scatter(
            x=periods, y=values, name=name, mode='lines',
            stackgroup='mix', groupnorm='' if not normalise else '',
            line={'width': 0.8, 'color': MARKER_LINE},
            fillcolor=CATEGORY_COLORS[name],
            hovertemplate=('%{x}<br>' + name + ': '
                           + ('%{y:.1%}' if normalise else '$%{y:,.0f}')
                           + '<extra></extra>'),
        ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['category_share'],
        margin={'l': 60, 'r': 24, 't': 48, 'b': 40},
        yaxis=_deep_merge(
            {'title': {'text': 'Share of revenue' if normalise else 'Revenue'}},
            {'tickformat': '.0%'} if normalise else _axis_tick('money')),
        hovermode='x unified',
    ))
    return fig


# ==========================================================================
# Customers — Cohort Retention
# ==========================================================================
def cohort_triangle(dataset, brand: str, max_months: int = 18) -> go.Figure:
    """Repeat rate by acquisition month and months since acquisition.

    The canonical retention artifact, and a triangle rather than a rectangle on
    purpose: a cohort acquired last month has exactly one observed month, and
    filling the rest with zero would draw a cliff that reads as collapsing
    retention. Unobserved cells stay blank.
    """
    bundle = dataset['brands'][brand]
    cohorts = bundle['cohorts']
    periods = cohorts['periods']
    sizes = cohorts['sizes']
    live = [index for index, size in enumerate(sizes) if size > 0]
    if not live:
        return empty_figure('No acquisition cohorts yet.', CHART_HEIGHTS['cohort'])

    # A cohort acquired in the final month has no month-1 yet. Keeping it would
    # draw a completely blank row, which reads as a bug rather than as "too
    # early to say".
    observable = [index for index in live
                  if any(value is not None
                         for value in cohorts['retention'][index][1:])]
    if not observable:
        return empty_figure('Cohorts are too recent to show a repeat rate yet.',
                            CHART_HEIGHTS['cohort'])
    rows = observable[-24:]
    columns = min(max_months, len(periods))

    # Month 0 is 100% by construction and would set the colour scale on its own,
    # so the grid starts at month 1 — the first month that carries information.
    z, text, hover = [], [], []
    for index in rows:
        retention = cohorts['retention'][index]
        z_row, text_row, hover_row = [], [], []
        for k in range(1, columns):
            value = retention[k] if k < len(retention) else None
            z_row.append(value)
            text_row.append('' if value is None else group(value * 100, 1))
            if value is None:
                hover_row.append('')
            else:
                hover_row.append(
                    f'{periods[index]} cohort · {group(sizes[index])} customers<br>'
                    f'Month {k}: {group(value * 100, 1)}% ordered again '
                    f'({group(value * sizes[index])} customers)')
        z.append(z_row)
        text.append(text_row)
        hover.append(hover_row)

    fig = go.Figure(go.Heatmap(
        z=z, text=text, customdata=hover,
        x=[f'M{k}' for k in range(1, columns)],
        y=[f'{periods[index]}  ({fmt_compact(sizes[index])})' for index in rows],
        colorscale=[[position, colour] for position, colour in RETENTION_SCALE],
        texttemplate='%{text}', textfont={'size': 9.5},
        hovertemplate='%{customdata}<extra></extra>',
        xgap=2, ygap=2,
        zmin=0,
        colorbar={
            'title': {'text': 'Repeat rate', 'side': 'right',
                      'font': {'size': 11, 'color': SURFACE['text_secondary']}},
            'thickness': 9, 'len': 0.62, 'outlinewidth': 0,
            'tickformat': '.0%',
            'tickfont': {'size': 10, 'color': SURFACE['text_muted']},
        },
    ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['cohort'],
        margin={'l': 116, 'r': 30, 't': 34, 'b': 42},
        xaxis={'title': {'text': 'Months since first order'}, 'side': 'top',
               'showgrid': False},
        yaxis={'title': {'text': 'Acquisition month (cohort size)'},
               'autorange': 'reversed', 'showgrid': False},
    ))
    return fig


def cohort_curves(dataset, brand: str, highlight: int = 6) -> go.Figure:
    """The same triangle read as curves, with the portfolio average on top.

    The heatmap answers "which cohort"; the curves answer "is the shape
    changing". Recent cohorts are drawn in the accent and older ones fade, so
    improvement or decay in the acquisition base is visible without reading
    numbers out of cells.
    """
    bundle = dataset['brands'][brand]
    cohorts = bundle['cohorts']
    periods, sizes = cohorts['periods'], cohorts['sizes']
    live = [index for index, size in enumerate(sizes) if size > 0]
    if not live:
        return empty_figure('No acquisition cohorts yet.', CHART_HEIGHTS['cohort_curves'])

    recent = live[-highlight:]
    fig = go.Figure()

    for order, index in enumerate(recent):
        retention = [v for v in cohorts['retention'][index][1:] if v is not None]
        if len(retention) < 2:
            continue
        weight = order / max(len(recent) - 1, 1)
        colour = SEQUENTIAL[min(int((1 - weight) * (len(SEQUENTIAL) - 1)), len(SEQUENTIAL) - 1)]
        fig.add_trace(go.Scatter(
            x=list(range(1, len(retention) + 1)), y=retention,
            name=periods[index], mode='lines',
            line={'color': colour, 'width': 1.6 + weight * 1.2},
            hovertemplate=f'{periods[index]} cohort<br>Month %{{x}}: %{{y:.1%}}<extra></extra>',
        ))

    # Size-weighted average across every observed cohort.
    columns = max(len(cohorts['retention'][index]) for index in live)
    average = []
    for k in range(1, columns):
        top = bottom = 0.0
        for index in live:
            row = cohorts['retention'][index]
            if k < len(row) and row[k] is not None:
                top += row[k] * sizes[index]
                bottom += sizes[index]
        if bottom > 0:
            average.append(top / bottom)
    if average:
        fig.add_trace(go.Scatter(
            x=list(range(1, len(average) + 1)), y=average, name='All cohorts',
            mode='lines', line={'color': SURFACE['text'], 'width': 2.4, 'dash': 'dot'},
            hovertemplate='All cohorts<br>Month %{x}: %{y:.1%}<extra></extra>',
        ))

    fig.update_layout(**base_layout(
        CHART_HEIGHTS['cohort_curves'],
        margin={'l': 60, 'r': 24, 't': 48, 'b': 44},
        xaxis={'title': {'text': 'Months since first order'}, 'dtick': 1},
        yaxis={'title': {'text': 'Repeat rate'}, 'tickformat': '.0%', 'rangemode': 'tozero'},
        hovermode='x unified',
    ))
    return fig


def cohort_summary(dataset, brand: str):
    """Headline retention numbers for the view's stat blocks."""
    cohorts = dataset['brands'][brand]['cohorts']
    sizes, retention = cohorts['sizes'], cohorts['retention']
    live = [index for index, size in enumerate(sizes) if size > 0]
    if not live:
        return []

    def weighted(month: int):
        top = bottom = 0.0
        for index in live:
            row = retention[index]
            if month < len(row) and row[month] is not None:
                top += row[month] * sizes[index]
                bottom += sizes[index]
        return (top / bottom) if bottom else None

    out = []
    for month, label in ((1, 'Month 1 repeat rate'), (3, 'Month 3 repeat rate'),
                         (6, 'Month 6 repeat rate')):
        value = weighted(month)
        if value is not None:
            out.append({'label': label, 'value': fmt_value(value, 'percent')})
    out.append({'label': 'Cohorts tracked', 'value': group(len(live))})
    return out


# ==========================================================================
# Customers — Customer Value
# ==========================================================================
def rfm_scatter(dataset, brand: str) -> go.Figure:
    """Recency against frequency, sized by lifetime spend, split into quadrants.

    All three RFM terms are on the chart at once: recency on x (reversed, so the
    valuable side is the right), frequency on y, and monetary as marker area.
    The quadrant labels are drawn rather than left implicit, because the whole
    reason to plot RFM instead of tabulating it is that the four corners have
    names people act on.
    """
    bundle = dataset['brands'][brand]
    params = bundle['value_params']
    points = rfm_points(params, brand)
    if not points:
        return empty_figure('No customers yet.', CHART_HEIGHTS['rfm'])

    window = float(params['window_days'])
    max_spend = max(point['spend'] for point in points)
    cut_x = window * RECENCY_CUT

    fig = go.Figure()
    for tier in VALUE_TIER_NAMES:
        members = [point for point in points if point['tier'] == tier]
        if not members:
            continue
        fig.add_trace(go.Scatter(
            x=[p['recency'] for p in members],
            y=[p['frequency'] + (p['spend'] % 7) / 22.0 for p in members],
            name=tier, mode='markers',
            marker={
                'size': [6 + 26 * (p['spend'] / max_spend) ** 0.55 for p in members],
                'color': VALUE_TIER_COLORS[tier],
                'opacity': 0.66,
                'line': {'width': 0.6, 'color': MARKER_LINE},
            },
            customdata=[[p['spend'], p['frequency']] for p in members],
            hovertemplate=('%{customdata[1]} orders · last order %{x:.0f} days ago'
                           '<br>Lifetime spend $%{customdata[0]:,.0f}'
                           f'<extra>{tier}</extra>'),
        ))

    fig.add_vline(x=cut_x, line={'color': SURFACE['zeroline'], 'width': 1, 'dash': 'dash'})
    fig.add_hline(y=1.5, line={'color': SURFACE['zeroline'], 'width': 1, 'dash': 'dash'})

    # Anchor the upper labels inside the populated band rather than at the top
    # of the axis: frequency has a long thin tail, and a label parked at the
    # maximum floats over empty paper.
    frequencies = sorted(point['frequency'] for point in points)
    upper = frequencies[int(len(frequencies) * 0.992)]
    for quadrant in RFM_QUADRANTS:
        fig.add_annotation(
            x=(cut_x * 0.42) if quadrant['recent'] else (cut_x + (window - cut_x) * 0.62),
            y=(upper * 0.86) if quadrant['frequent'] else 1.16,
            text=f"<b>{quadrant['label']}</b><br>"
                 f"<span style='font-size:10px'>{quadrant['note']}</span>",
            showarrow=False, align='center',
            font={'size': 12, 'color': SURFACE['text'], 'family': SERIF},
            bgcolor='rgba(250, 249, 247, 0.82)', borderpad=5,
        )

    fig.update_layout(**base_layout(
        CHART_HEIGHTS['rfm'],
        margin={'l': 62, 'r': 26, 't': 48, 'b': 52},
        xaxis={'title': {'text': 'Days since last order  ·  recent →'},
               'autorange': 'reversed'},
        yaxis={'title': {'text': 'Lifetime orders'}, 'dtick': 1, 'rangemode': 'tozero'},
        legend={'title': {'text': 'Marker area = lifetime spend   ',
                          'font': {'size': 11, 'color': SURFACE['text_muted']}}},
    ))
    return fig


def value_decile_bars(dataset, brand: str) -> go.Figure:
    """Share of revenue by customer spend decile, with the cumulative curve.

    The single most useful thing to know about a customer base is how much of it
    the top decile carries; a mean spend number actively hides that.
    """
    bundle = dataset['brands'][brand]
    points = rfm_points(bundle['value_params'], brand)
    if not points:
        return empty_figure('No customers yet.', CHART_HEIGHTS['decile'])

    ordered = sorted((point['spend'] for point in points), reverse=True)
    total = sum(ordered) or 1.0
    size = max(len(ordered) // 10, 1)

    shares, cumulative, running = [], [], 0.0
    for index in range(10):
        chunk = ordered[index * size:(index + 1) * size]
        share = sum(chunk) / total
        running += share
        shares.append(share)
        cumulative.append(running)

    labels = ['Top 10%'] + [f'{index * 10}–{index * 10 + 10}%' for index in range(1, 10)]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=shares, name='Share of revenue',
        marker={'color': [SEQUENTIAL[min(index // 2, len(SEQUENTIAL) - 1)]
                          for index in range(10)],
                'line': {'width': 0.6, 'color': MARKER_LINE}},
        hovertemplate='%{x}<br>%{y:.1%} of revenue<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=labels, y=cumulative, name='Cumulative', yaxis='y2', mode='lines+markers',
        line={'color': SURFACE['text'], 'width': 1.8, 'dash': 'dot'},
        marker={'size': 5, 'color': SURFACE['text']},
        hovertemplate='%{x}<br>%{y:.1%} cumulative<extra></extra>',
    ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['decile'],
        margin={'l': 58, 'r': 58, 't': 48, 'b': 52},
        xaxis={'title': None, 'tickangle': -20},
        yaxis={'title': {'text': 'Share of revenue'}, 'tickformat': '.0%'},
        yaxis2={'overlaying': 'y', 'side': 'right', 'showgrid': False,
                'tickformat': '.0%', 'range': [0, 1.02],
                'tickfont': {'size': 11, 'color': SURFACE['text_muted']},
                'title': {'text': 'Cumulative',
                          'font': {'size': 11.5, 'color': SURFACE['text_secondary']}}},
        hovermode='x unified',
    ))
    return fig


def value_summary(dataset, brand: str):
    points = rfm_points(dataset['brands'][brand]['value_params'], brand)
    if not points:
        return []
    ordered = sorted((point['spend'] for point in points), reverse=True)
    total = sum(ordered) or 1.0
    top_decile = sum(ordered[:max(len(ordered) // 10, 1)]) / total
    repeat = sum(1 for point in points if point['frequency'] > 1) / len(points)
    return [
        {'label': 'Top 10% of customers', 'value': fmt_value(top_decile, 'percent'),
         'note': 'of lifetime revenue'},
        {'label': 'Repeat customers', 'value': fmt_value(repeat, 'percent'),
         'note': 'ordered more than once'},
        {'label': 'Median lifetime spend',
         'value': fmt_value(ordered[len(ordered) // 2], 'money'), 'note': 'per customer'},
        {'label': 'Mean lifetime orders',
         'value': group(sum(p['frequency'] for p in points) / len(points), 2),
         'note': 'per customer'},
    ]


# ==========================================================================
# Marketing — Channel Attribution
# ==========================================================================
def channel_area(dataset, brand: str, normalise: bool = False) -> go.Figure:
    """Revenue by order channel over time."""
    bundle = dataset['brands'][brand]
    rows = [row for row in bundle['channel_mix'] if sum(row['revenue'].values()) > 0]
    if not rows:
        return empty_figure('No channel revenue yet.', CHART_HEIGHTS['channel_area'])

    periods = [row['period'] for row in rows]
    fig = go.Figure()
    for name in CHANNEL_NAMES:
        values = []
        for row in rows:
            total = sum(row['revenue'].values()) or 1.0
            value = row['revenue'].get(name, 0.0)
            values.append(value / total if normalise else value)
        fig.add_trace(go.Scatter(
            x=periods, y=values, name=name, mode='lines', stackgroup='channel',
            line={'width': 0.8, 'color': MARKER_LINE},
            fillcolor=CHANNEL_COLORS[name],
            hovertemplate=('%{x}<br>' + name + ': '
                           + ('%{y:.1%}' if normalise else '$%{y:,.0f}')
                           + '<extra></extra>'),
        ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['channel_area'],
        margin={'l': 62, 'r': 24, 't': 48, 'b': 40},
        yaxis=_deep_merge({'title': {'text': 'Share' if normalise else 'Revenue'}},
                          {'tickformat': '.0%'} if normalise else _axis_tick('money')),
        hovermode='x unified',
    ))
    return fig


def source_bars(dataset, brand: str) -> go.Figure:
    """Revenue against acquisition spend by source, with return on ad spend.

    First-order and repeat revenue are stacked separately: a source that looks
    expensive on first orders alone can be the best one in the portfolio once
    the customers it brought keep ordering, and that is invisible in a single bar.
    """
    bundle = dataset['brands'][brand]
    rows = sorted(bundle['sources'], key=lambda r: r['revenue'])
    if not rows:
        return empty_figure('No attribution yet.', CHART_HEIGHTS['source_bars'])

    names = [row['source'] for row in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=[row['first_order_revenue'] for row in rows],
        name='First-order revenue', orientation='h',
        marker={'color': ACCENT, 'line': {'width': 0.6, 'color': MARKER_LINE}},
        hovertemplate='%{y}<br>First-order revenue $%{x:,.0f}<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        y=names, x=[row['repeat_revenue'] for row in rows],
        name='Repeat revenue', orientation='h',
        marker={'color': POSITIVE, 'line': {'width': 0.6, 'color': MARKER_LINE}},
        hovertemplate='%{y}<br>Repeat revenue $%{x:,.0f}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        y=names, x=[row['spend'] for row in rows], name='Acquisition spend',
        mode='markers', marker={'symbol': 'line-ns-open', 'size': 16,
                                'color': SURFACE['text'], 'line': {'width': 2}},
        hovertemplate='%{y}<br>Acquisition spend $%{x:,.0f}<extra></extra>',
    ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['source_bars'],
        margin={'l': 116, 'r': 26, 't': 48, 'b': 44},
        barmode='stack',
        xaxis=_deep_merge({'title': {'text': 'Revenue and spend'}}, _axis_tick('money')),
        yaxis={'title': None, 'showgrid': False},
    ))
    return fig


def source_table(dataset, brand: str):
    """Attribution rows for the table beside the chart."""
    bundle = dataset['brands'][brand]
    rows = []
    for row in bundle['sources']:
        spend = row['spend']
        rows.append({
            'Source': row['source'],
            'New customers': group(row['new_customers']),
            'Revenue': fmt_compact(row['revenue'], 'money'),
            'Repeat share': fmt_value(
                row['repeat_revenue'] / max(row['revenue'], 1e-9), 'percent'),
            'CAC': fmt_value(row['cac'], 'money2') if row['cac'] else '—',
            'ROAS': fmt_value(row['revenue'] / spend, 'ratio') if spend > 0 else '—',
        })
    return rows


# ==========================================================================
# Marketing — Promotion Lift
# ==========================================================================
def event_study_chart(dataset, brand: str, metric: str = 'revenue',
                      kinds: Sequence[str] = ()) -> go.Figure:
    """Average response around a promotion, aligned on the day it ran.

    Every occurrence of a promotion type is normalised to its own day −1 level
    and stacked on a common axis, so the answer is a *shape* rather than a single
    percentage: whether the lift is instant or builds, whether it decays back to
    baseline or leaves a step, and whether the days before show pull-forward. The
    shaded band is a 95% interval across occurrences — a promotion type that ran
    three times shows a band wide enough to say so.
    """
    bundle = dataset['brands'][brand]
    studies = demo_data.event_study(bundle, dataset['dates'], metric, kinds)
    if not studies:
        return empty_figure('Not enough repeat occurrences to average.',
                            CHART_HEIGHTS['event_study'])

    fig = go.Figure()
    for study in studies:
        colour = study['color']
        fig.add_trace(go.Scatter(
            x=study['offsets'] + study['offsets'][::-1],
            y=study['upper'] + study['lower'][::-1],
            fill='toself', fillcolor=_soft(colour, 0.13),
            line={'width': 0}, hoverinfo='skip', showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=study['offsets'], y=study['mean'],
            name=f"{study['kind']}  ({study['occurrences']})",
            mode='lines', line={'color': colour, 'width': 2},
            hovertemplate=('Day %{x:+d}<br>%{y:.2f}x the day before'
                           f"<extra>{study['kind']}</extra>"),
        ))

    fig.add_vline(x=0, line={'color': SURFACE['zeroline'], 'width': 1.2})
    fig.add_hline(y=1.0, line={'color': SURFACE['zeroline'], 'width': 1, 'dash': 'dot'})
    fig.add_annotation(x=0, y=1.0, yref='paper', yanchor='bottom',
                       text='promotion runs', showarrow=False, yshift=6,
                       font={'size': 10.5, 'color': SURFACE['text_muted']})

    fig.update_layout(**base_layout(
        CHART_HEIGHTS['event_study'],
        margin={'l': 62, 'r': 26, 't': 54, 'b': 48},
        xaxis={'title': {'text': 'Days from promotion'}, 'dtick': 2, 'zeroline': False},
        yaxis={'title': {'text': f'{metric_label(metric)}, indexed to day −1'},
               'tickformat': '.2f'},
        hovermode='x unified',
    ))
    return fig


def promotion_lift_bars(dataset, brand: str, lo: int, hi: int) -> go.Figure:
    """Promoted days against the non-promoted days of the same window.

    The comparison is inside the window on purpose. Measured against an annual
    average, a November promotion would be credited with November.
    """
    bundle = dataset['brands'][brand]
    on, off = demo_data.promotion_windows(bundle, lo, hi)
    if len(on) < 3 or len(off) < 3:
        return empty_figure('Not enough promoted days in this window.',
                            CHART_HEIGHTS['promo_bars'])

    def per_day(indices, key):
        if key in RATIO_METRICS:
            top, bottom = demo_data.DERIVED[key]
            return (sum(bundle['series'][top][index] for index in indices)
                    / max(sum(bundle['series'][bottom][index] for index in indices), 1e-9))
        return sum(_series(bundle, key)[index] for index in indices) / len(indices)

    metrics = ['revenue', 'orders', 'aov', 'conversion']
    labels = [metric_label(key) for key in metrics]
    lifts, hover = [], []
    for key in metrics:
        base = per_day(off, key)
        promo = per_day(on, key)
        lift = (promo / base - 1.0) if base else 0.0
        lifts.append(lift)
        kind = metric_format(key)
        hover.append(f'{fmt_value(base, kind)} → {fmt_value(promo, kind)} per day')

    fig = go.Figure(go.Bar(
        x=labels, y=lifts, customdata=hover,
        marker={'color': [POSITIVE if value >= 0 else NEGATIVE for value in lifts],
                'line': {'width': 0.6, 'color': MARKER_LINE}},
        text=[('+' if value >= 0 else '') + group(value * 100, 1) + '%' for value in lifts],
        textposition='outside', textfont={'size': 11.5, 'color': SURFACE['text']},
        hovertemplate='%{x}<br>%{customdata}<extra></extra>',
    ))
    fig.add_hline(y=0, line={'color': SURFACE['zeroline'], 'width': 1})
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['promo_bars'],
        margin={'l': 60, 'r': 26, 't': 34, 'b': 44},
        yaxis={'title': {'text': 'Lift vs baseline days'}, 'tickformat': '+.0%'},
        xaxis={'title': None},
        showlegend=False,
    ))
    return fig


def promotion_summary(dataset, brand: str, lo: int, hi: int):
    bundle = dataset['brands'][brand]
    on, off = demo_data.promotion_windows(bundle, lo, hi)
    if not on or not off:
        return []
    revenue = _series(bundle, 'revenue')
    promo_day = sum(revenue[index] for index in on) / len(on)
    base_day = sum(revenue[index] for index in off) / len(off)
    incremental = (promo_day - base_day) * len(on)
    return [
        {'label': 'Promoted days', 'value': group(len(on)),
         'note': f'of {group(len(on) + len(off))} in window'},
        {'label': 'Revenue per promoted day', 'value': fmt_compact(promo_day, 'money'),
         'note': f"vs {fmt_compact(base_day, 'money')} baseline"},
        {'label': 'Incremental revenue', 'value': fmt_compact(incremental, 'money'),
         'note': 'above baseline days'},
        {'label': 'Discount given back',
         'value': fmt_compact(sum(bundle['series']['discount_value'][lo:hi]), 'money'),
         'note': 'across the whole window'},
    ]


def discount_bars(dataset, brand: str) -> go.Figure:
    """Revenue kept against discount given back, by code."""
    bundle = dataset['brands'][brand]
    rows = sorted(bundle['discounts'], key=lambda r: r['revenue'])
    if not rows:
        return empty_figure('No discount codes in use.', CHART_HEIGHTS['discount'])

    names = [row['code'] for row in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=[row['revenue'] for row in rows], name='Revenue kept',
        orientation='h', marker={'color': NEUTRAL,
                                 'line': {'width': 0.6, 'color': MARKER_LINE}},
        hovertemplate='%{y}<br>Revenue kept $%{x:,.0f}<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        y=names, x=[row['discount'] for row in rows], name='Discount given',
        orientation='h', marker={'color': ACCENT,
                                 'line': {'width': 0.6, 'color': MARKER_LINE}},
        hovertemplate='%{y}<br>Discount given $%{x:,.0f}<extra></extra>',
    ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['discount'],
        margin={'l': 96, 'r': 26, 't': 48, 'b': 42},
        barmode='stack',
        xaxis=_deep_merge({'title': {'text': 'Gross order value'}}, _axis_tick('money')),
        yaxis={'title': None, 'showgrid': False},
    ))
    return fig


# ==========================================================================
# Operations — Fulfillment & Regions
# ==========================================================================
# A light basemap, to match the page rather than fight it. No access token.
MAP_STYLE = 'carto-positron'

MAP_DISPLAYS = [
    ('market', 'Market bubbles'),
    ('orders', 'Individual orders'),
    ('density', 'Order density'),
]


def _bubble_sizes(values: Sequence[float], cap: int = 46, floor: int = 6):
    """Area-proportional sizes: a market with four times the orders should look
    four times the size, which means the *radius* scales with the square root."""
    peak = max(values) if values else 1.0
    if peak <= 0:
        return [floor] * len(values)
    return [floor + (cap - floor) * (value / peak) ** 0.5 for value in values]


def _map_view(markets: Sequence[Dict]):
    """Centre and zoom on where the orders are, weighted by volume."""
    if not markets:
        return {'center': {'lat': 39.0, 'lon': -98.0}, 'zoom': 3.1}
    total = sum(market['orders'] for market in markets) or 1
    lat = sum(market['lat'] * market['orders'] for market in markets) / total
    lon = sum(market['lon'] * market['orders'] for market in markets) / total
    return {'center': {'lat': lat, 'lon': lon}, 'zoom': 3.15}


def _map_layout(markets, height=None, uirevision=None, **overrides):
    view = _map_view(markets)
    layout = base_layout(
        height or CHART_HEIGHTS['map'],
        margin={'l': 0, 'r': 0, 't': 0, 'b': 0},
        map={'style': MAP_STYLE, 'center': view['center'], 'zoom': view['zoom']},
        showlegend=False,
    )
    layout.pop('xaxis', None)
    layout.pop('yaxis', None)
    if uirevision:
        layout['uirevision'] = uirevision
    return _deep_merge(layout, overrides)


def _aov_range(markets: Sequence[Dict]):
    """Symmetric colour range around the portfolio's own average order value.

    A diverging scale is only honest if its midpoint is the thing it diverges
    about. Anchoring at the blended AOV makes "warmer than average" literal.
    """
    if not markets:
        return 0.0, 1.0, 0.5
    orders = sum(market['orders'] for market in markets) or 1
    mid = sum(market['aov'] * market['orders'] for market in markets) / orders
    values = [market['aov'] for market in markets]
    reach = max(max(values) - mid, mid - min(values), 1e-6)
    return mid - reach, mid + reach, mid


def fulfillment_map(dataset, brand: str, level: str = 'city',
                    display: str = 'market') -> go.Figure:
    """Where orders ship, sized by volume and coloured by basket size.

    Size and colour carry two independent facts — how many orders a market
    places, and how large each one is — which is exactly the pair a fulfillment
    or merchandising decision turns on. A market can be big and cheap, or small
    and rich, and a single-encoding map cannot say which.
    """
    bundle = dataset['brands'][brand]
    markets = aggregate_by_level(bundle['locations'], level)
    if not markets:
        return empty_figure('No orders in this view.', CHART_HEIGHTS['map'])

    if display == 'orders':
        return _order_marker_map(markets, brand)
    if display == 'density':
        return _density_map(markets, brand)
    return _market_bubble_map(markets, brand, level)


def _market_bubble_map(markets, brand: str, level: str) -> go.Figure:
    low, high, mid = _aov_range(markets)
    hover = [
        f"<b>{market['label']}</b><br>"
        f"{group(market['orders'])} orders<br>"
        f"{fmt_compact(market['revenue'], 'money')} revenue<br>"
        f"{fmt_value(market['aov'], 'money2')} average order"
        for market in markets
    ]
    fig = go.Figure(go.Scattermap(
        lat=[market['lat'] for market in markets],
        lon=[market['lon'] for market in markets],
        mode='markers',
        marker={
            'size': _bubble_sizes([market['orders'] for market in markets]),
            'color': [market['aov'] for market in markets],
            'colorscale': [[position, colour] for position, colour in AOV_SCALE],
            'cmin': low, 'cmax': high,
            'opacity': 0.82,
            'colorbar': {
                'title': {'text': 'Average<br>order value', 'side': 'right',
                          'font': {'size': 11, 'color': SURFACE['text_secondary']}},
                'thickness': 10, 'len': 0.6, 'x': 0.99, 'xanchor': 'right',
                'outlinewidth': 0, 'tickprefix': '$', 'tickformat': ',.0f',
                'bgcolor': 'rgba(255,255,255,0.72)',
                'tickfont': {'size': 10, 'color': SURFACE['text_muted']},
            },
        },
        text=hover,
        hovertemplate='%{text}<extra></extra>',
        customdata=[market['name'] for market in markets],
    ))
    fig.update_layout(**_map_layout(markets, uirevision=f'map-{brand}-{level}'))
    return fig


# Value bands for the per-order views. The bubble map colours a continuous
# quantity continuously; a cloud of a third of a million points cannot afford
# to — a per-point colour array is a third of the payload on its own, and at
# three pixels a point the eye reads bands anyway. Five bands, single hue,
# ordered light to dark, so the legend survives a greyscale print.
ORDER_VALUE_BANDS = 5


def _band_points(points):
    """Split points into value bands, returning (label, colour, members).

    The band edges come from the orders themselves, between the 5th and 95th
    percentile. Reusing the map's colour range would be wrong here: that range
    is built around the spread of *market averages*, which is a fraction of the
    spread of individual orders, so every band but one would be empty.
    """
    if not points:
        return []
    ordered = sorted(point['value'] for point in points)
    low = ordered[int(len(ordered) * 0.05)]
    high = ordered[min(int(len(ordered) * 0.95), len(ordered) - 1)]
    step = (high - low) / ORDER_VALUE_BANDS
    buckets = [[] for _ in range(ORDER_VALUE_BANDS)]
    for point in points:
        index = int((point['value'] - low) / step) if step > 0 else 0
        buckets[max(0, min(index, ORDER_VALUE_BANDS - 1))].append(point)

    ramp = list(reversed(SEQUENTIAL))[:ORDER_VALUE_BANDS]
    out = []
    for index, members in enumerate(buckets):
        if not members:
            continue
        lower = low + step * index
        upper = lower + step
        if index == 0:
            label = f'under {fmt_compact(upper, "money")}'
        elif index == ORDER_VALUE_BANDS - 1:
            label = f'{fmt_compact(lower, "money")} and up'
        else:
            label = f'{fmt_compact(lower, "money")} – {fmt_compact(upper, "money")}'
        out.append((label, ramp[index], members))
    return out


def _order_marker_map(markets, brand: str) -> go.Figure:
    """One marker per order, banded by order value.

    Every order is drawn rather than a sample: MapLibre renders the full cloud in
    about the time it takes to render five thousand points, and the density is
    the whole point of the view. The markers carry no per-point label — at this
    scale an individual order cannot be hovered anyway, and the strings would be
    most of the payload. Drill-down lives in the bubble and density views.
    """
    points = scatter_orders(markets, brand)
    if not points:
        return empty_figure('No orders in this view.', CHART_HEIGHTS['map'])

    fig = go.Figure()
    for label, colour, members in _band_points(points):
        fig.add_trace(go.Scattermap(
            lat=[point['lat'] for point in members],
            lon=[point['lon'] for point in members],
            mode='markers', name=label,
            marker={'size': 3.4, 'color': colour, 'opacity': 0.5},
            hoverinfo='skip',
        ))
    fig.update_layout(**_map_layout(
        markets, uirevision=f'map-{brand}-orders',
        showlegend=True,
        legend={'orientation': 'h', 'yanchor': 'top', 'y': 0.99,
                'xanchor': 'left', 'x': 0.01,
                'bgcolor': 'rgba(255,255,255,0.82)', 'borderwidth': 0,
                'title': {'text': 'Order value  ',
                          'font': {'size': 11, 'color': SURFACE['text_secondary']}},
                'font': {'size': 11, 'color': SURFACE['text_secondary']}},
    ))
    return fig


def _density_map(markets, brand: str) -> go.Figure:
    """Order density, with the market boundaries dropped."""
    points = scatter_orders(markets, brand)
    if not points:
        return empty_figure('No orders in this view.', CHART_HEIGHTS['map'])
    fig = go.Figure(go.Densitymap(
        lat=[point['lat'] for point in points],
        lon=[point['lon'] for point in points],
        radius=11,
        colorscale=[[position, colour] for position, colour
                    in zip([index / (len(SEQUENTIAL) - 1) for index in range(len(SEQUENTIAL))],
                           list(reversed(SEQUENTIAL)))],
        showscale=False,
        hoverinfo='skip',
    ))
    fig.update_layout(**_map_layout(markets, uirevision=f'map-{brand}-density'))
    return fig


def growth_timeline(dataset, brand: str) -> List[str]:
    """Month labels for the replay transport."""
    return [row['period'] for row in dataset['brands'][brand]['monthly']]


def growth_map(dataset, brand: str, level: str = 'city',
               month_index: int = -1) -> go.Figure:
    """Every order placed up to the end of a month, one marker each.

    One month, not an animation. Plotly's own play button and slider live inside
    the plotting area, where they read as map controls rather than as a timeline;
    the page owns the transport instead and asks for a frame by index.

    Individual markers rather than market bubbles: resizing a fixed set of blobs
    shows a market getting bigger, but it cannot show the footprint *spreading* —
    new suburbs, then new metros, then the gaps between them filling in. That
    spread is the thing worth replaying.
    """
    bundle = dataset['brands'][brand]
    markets = aggregate_by_level(bundle['locations'], level)
    ramp = [row['frac'] for row in bundle['monthly']]
    if not markets or not ramp:
        return empty_figure('No orders in this view.', CHART_HEIGHTS['growth_map'])

    if month_index < 0:
        month_index = len(ramp) - 1
    month_index = max(0, min(month_index, len(ramp) - 1))

    points = scatter_orders(markets, brand, ramp)
    shown = [point for point in points if point['month'] <= month_index]

    fig = go.Figure()
    for label, colour, members in _band_points(shown):
        fig.add_trace(go.Scattermap(
            lat=[point['lat'] for point in members],
            lon=[point['lon'] for point in members],
            mode='markers', name=label,
            marker={'size': 3.2, 'color': colour, 'opacity': 0.5},
            hoverinfo='skip',
        ))
    fig.update_layout(**_map_layout(
        markets, CHART_HEIGHTS['growth_map'],
        uirevision=f'growth-{brand}-{level}', showlegend=False))
    return fig


def growth_totals(dataset, brand: str, level: str = 'city', month_index: int = -1):
    """What the replay is showing, in words."""
    bundle = dataset['brands'][brand]
    markets = aggregate_by_level(bundle['locations'], level)
    ramp = [row['frac'] for row in bundle['monthly']]
    periods = [row['period'] for row in bundle['monthly']]
    if not markets or not ramp:
        return None

    if month_index < 0:
        month_index = len(ramp) - 1
    month_index = max(0, min(month_index, len(ramp) - 1))

    points = scatter_orders(markets, brand, ramp)
    shown = [point for point in points if point['month'] <= month_index]
    orders = len(shown)
    total = len(points) or 1
    value = sum(point['value'] for point in shown)
    return {
        'period': periods[month_index],
        'orders': orders,
        'share': orders / total,
        'value': value,
        'markets': sum(1 for market in markets
                       if market['ramp_lag'] * (len(ramp) - 1) <= month_index),
        'total_markets': len(markets),
    }


def market_bars(dataset, brand: str, level: str = 'city', limit: int = 12) -> go.Figure:
    """Top markets by orders, with average order value alongside."""
    bundle = dataset['brands'][brand]
    markets = aggregate_by_level(bundle['locations'], level)[:limit][::-1]
    if not markets:
        return empty_figure('No orders in this view.', CHART_HEIGHTS['market_bars'])

    low, high, _ = _aov_range(markets)
    fig = go.Figure(go.Bar(
        y=[market['name'] for market in markets],
        x=[market['orders'] for market in markets],
        orientation='h',
        marker={
            'color': [market['aov'] for market in markets],
            'colorscale': [[position, colour] for position, colour in AOV_SCALE],
            'cmin': low, 'cmax': high,
            'line': {'width': 0.6, 'color': MARKER_LINE},
        },
        customdata=[[market['aov'], market['revenue']] for market in markets],
        hovertemplate=('<b>%{y}</b><br>%{x:,.0f} orders'
                       '<br>$%{customdata[0]:,.2f} average order'
                       '<br>$%{customdata[1]:,.0f} revenue<extra></extra>'),
    ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['market_bars'],
        margin={'l': 132, 'r': 26, 't': 22, 'b': 44},
        xaxis={'title': {'text': 'Orders'}, 'tickformat': ',.0f'},
        yaxis={'title': None, 'showgrid': False},
        showlegend=False,
    ))
    return fig


def fulfillment_summary(dataset, brand: str, level: str = 'city'):
    bundle = dataset['brands'][brand]
    markets = aggregate_by_level(bundle['locations'], level)
    if not markets:
        return []
    orders = sum(market['orders'] for market in markets)
    revenue = sum(market['revenue'] for market in markets)
    top_five = sum(market['orders'] for market in markets[:5]) / max(orders, 1)
    return [
        {'label': 'Orders shipped', 'value': fmt_compact(orders),
         'note': f'across {group(len(markets))} markets'},
        {'label': 'Largest market', 'value': markets[0]['name'],
         'note': f"{fmt_compact(markets[0]['orders'])} orders"},
        {'label': 'Top 5 concentration', 'value': fmt_value(top_five, 'percent'),
         'note': 'of all orders'},
        {'label': 'Blended order value',
         'value': fmt_value(revenue / max(orders, 1), 'money2'),
         'note': 'across every market'},
    ]


# ==========================================================================
# Operations — Returns
# ==========================================================================
def return_rate_trend(dataset, brand: str, lo: int, hi: int,
                      grain: str = 'weekly') -> go.Figure:
    """Return rate over time against the orders that produced it.

    Returns are plotted against the return rate rather than the raw count, and
    the rate is summed-returns over summed-orders per bucket — averaging daily
    rates would let a quiet Tuesday outvote a sale week.
    """
    bundle = dataset['brands'][brand]
    dates = dataset['dates'][lo:hi]
    labels, rate = demo_data.resample_ratio(
        dates, bundle['series']['returns'][lo:hi], bundle['series']['orders'][lo:hi], grain)
    _, returns = demo_data.resample(dates, bundle['series']['returns'][lo:hi], grain)
    if not labels:
        return empty_figure('No returns in this window.', CHART_HEIGHTS['return_trend'])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=returns, name='Returns',
        marker={'color': _soft(NEUTRAL, 0.45), 'line': {'width': 0}},
        hovertemplate='%{x}<br>%{y:,.0f} returns<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=labels, y=rate, name='Return rate', yaxis='y2', mode='lines',
        line={'color': ACCENT, 'width': 2.1},
        hovertemplate='%{x}<br>%{y:.2%} of orders<extra></extra>',
    ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['return_trend'],
        margin={'l': 60, 'r': 62, 't': 48, 'b': 42},
        yaxis={'title': {'text': 'Returns'}, 'tickformat': ',.0f'},
        yaxis2={'overlaying': 'y', 'side': 'right', 'showgrid': False,
                'tickformat': '.1%', 'rangemode': 'tozero',
                'tickfont': {'size': 11, 'color': ACCENT},
                'title': {'text': 'Return rate',
                          'font': {'size': 11.5, 'color': ACCENT}}},
        hovermode='x unified',
    ))
    return fig


def return_category_bars(dataset, brand: str) -> go.Figure:
    """Return rate by product category, with the value at stake behind it."""
    bundle = dataset['brands'][brand]
    rows = sorted(bundle['returns']['by_category'], key=lambda r: r['rate'])
    if not rows:
        return empty_figure('No returns recorded.', CHART_HEIGHTS['return_category'])

    fig = go.Figure(go.Bar(
        y=[row['category'] for row in rows],
        x=[row['rate'] for row in rows], orientation='h',
        marker={'color': [CATEGORY_COLORS[row['category']] for row in rows],
                'line': {'width': 0.6, 'color': MARKER_LINE}},
        text=[group(row['rate'] * 100, 1) + '%' for row in rows],
        textposition='outside', textfont={'size': 11, 'color': SURFACE['text']},
        customdata=[row['returned_value'] for row in rows],
        hovertemplate=('<b>%{y}</b><br>%{x:.2%} of revenue returned'
                       '<br>$%{customdata:,.0f} at stake<extra></extra>'),
    ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['return_category'],
        margin={'l': 116, 'r': 44, 't': 22, 'b': 42},
        xaxis={'title': {'text': 'Return rate'}, 'tickformat': '.0%'},
        yaxis={'title': None, 'showgrid': False},
        showlegend=False,
    ))
    return fig


def return_reason_bars(dataset, brand: str) -> go.Figure:
    """Why the returns happened, by value."""
    bundle = dataset['brands'][brand]
    rows = sorted(bundle['returns']['by_reason'], key=lambda r: r['value'])
    if not rows:
        return empty_figure('No returns recorded.', CHART_HEIGHTS['return_reason'])

    fig = go.Figure(go.Bar(
        y=[row['reason'] for row in rows],
        x=[row['value'] for row in rows], orientation='h',
        marker={'color': [RETURN_REASON_COLORS[row['reason']] for row in rows],
                'line': {'width': 0.6, 'color': MARKER_LINE}},
        customdata=[row['share'] for row in rows],
        hovertemplate=('<b>%{y}</b><br>$%{x:,.0f} returned'
                       '<br>%{customdata:.1%} of all returns<extra></extra>'),
    ))
    fig.update_layout(**base_layout(
        CHART_HEIGHTS['return_reason'],
        margin={'l': 138, 'r': 26, 't': 22, 'b': 42},
        xaxis=_deep_merge({'title': {'text': 'Value returned'}}, _axis_tick('money')),
        yaxis={'title': None, 'showgrid': False},
        showlegend=False,
    ))
    return fig


def returns_summary(dataset, brand: str, lo: int, hi: int):
    bundle = dataset['brands'][brand]
    returns = sum(bundle['series']['returns'][lo:hi])
    orders = sum(bundle['series']['orders'][lo:hi])
    value = sum(bundle['series']['return_value'][lo:hi])
    by_category = bundle['returns']['by_category']
    worst = max(by_category, key=lambda r: r['rate']) if by_category else None
    return [
        {'label': 'Return rate', 'value': fmt_value(returns / max(orders, 1), 'percent'),
         'note': 'of orders in window'},
        {'label': 'Value returned', 'value': fmt_compact(value, 'money'),
         'note': 'in window'},
        {'label': 'Highest-return category',
         'value': worst['category'] if worst else '—',
         'note': fmt_value(worst['rate'], 'percent') + ' of its revenue' if worst else ''},
        {'label': 'Returns processed', 'value': fmt_compact(returns),
         'note': 'in window'},
    ]
