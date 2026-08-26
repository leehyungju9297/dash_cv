"""Plotly figure builders for the Frontrow Analytics demo dashboard.

Every figure is built from the synthetic dataset in :mod:`demo_dashboard.data`
and styled by one shared dark theme, so charts on different tabs read as one
product rather than a pile of Plotly defaults. A metric keeps the same color
wherever it appears (see ``config.metric_color``).
"""

from __future__ import annotations

import math
from typing import Dict, Sequence

import plotly.graph_objects as go

from demo_dashboard.config import (
    ACCENTS,
    SEGMENT_COLORS,
    SEGMENT_NAMES,
    SURFACE,
    metric_color,
    metric_format,
    metric_label,
)
from demo_dashboard.geo import (
    aggregate_by_level,
    growth_frames,
    spread_within_city,
)
from demo_dashboard.data import (
    EVENT_KINDS,
    correlation_matrix,
    events_in_window,
    linear_fit,
    resample,
)


# Rendered height of each chart, in one place.
#
# These are not only figure geometry: the Dash page also applies them as the CSS
# height of the graph container. A dcc.Graph with `responsive: true` and no CSS
# height collapses its container to zero on a width change — the figure keeps its
# own height, so the SVG then escapes the card and paints over whatever follows.
# Pinning the container to the same number the figure uses makes a window resize
# a no-op.
CHART_HEIGHTS = {
    'trend': 460,
    'map': 560,
    'growth': 560,
    'location_bar': 460,
    'segment_mix': 120,
    'scatter': 440,
    'correlation': 470,
    'engagement': 400,
    'revenue': 400,
    'mix_donut': 290,
    'churn': 400,
    'lifetime': 320,
    'empty': 300,
}


FONT = {'family': 'Public Sans, Inter, Helvetica Neue, sans-serif', 'color': SURFACE['text_secondary'], 'size': 12}

# Metrics that describe a level at a point in time rather than a flow. They are
# carried forward when resampled and never summed across periods.
STOCK_METRICS = {'memberships', 'mau', 'session_minutes'}


# --------------------------------------------------------------------------
# Formatting
# --------------------------------------------------------------------------
def round_half_up(value: float, decimals: int = 0) -> float:
    """Round ties away from zero.

    Python's ``format()`` rounds ties to even while JavaScript's
    ``toLocaleString`` rounds them away from zero, so a revenue total of
    932,150 renders as ``$932.1K`` on the Dash page and ``$932.2K`` on the
    static twin. Both sides pre-round through this identical rule instead, so
    the two dashboards can never disagree on a displayed number.
    """
    factor = 10 ** decimals
    rounded = math.floor(abs(value) * factor + 0.5) / factor
    if rounded == 0:
        return 0.0  # never render a negative zero
    return -rounded if value < 0 else rounded


def group(value: float, decimals: int = 0) -> str:
    """Thousands-separated number using the shared rounding rule."""
    return f'{round_half_up(value, decimals):,.{decimals}f}'


def fmt_value(value: float, kind: str = 'int') -> str:
    if value is None:
        return '—'
    if kind == 'money':
        return f'${group(value)}' if abs(value) >= 100 else f'${group(value, 2)}'
    if kind == 'minutes':
        return f'{group(value, 1)} min'
    if kind == 'percent':
        return f'{group(value, 1)}%'
    return group(value)


def fmt_compact(value: float, kind: str = 'int') -> str:
    """Short form for KPI tiles: 1.2M / 48.3K. Money keeps its symbol."""
    prefix = '$' if kind == 'money' else ''
    magnitude = abs(value)
    if kind == 'minutes':
        return f'{group(value, 1)} min'
    if magnitude >= 1_000_000:
        return f'{prefix}{group(value / 1_000_000, 2)}M'
    if magnitude >= 10_000:
        return f'{prefix}{group(value / 1_000, 1)}K'
    return f'{prefix}{group(value)}'


def _hover_number(kind: str) -> str:
    if kind == 'money':
        return '$%{y:,.0f}'
    if kind == 'minutes':
        return '%{y:,.1f} min'
    return '%{y:,.0f}'


# --------------------------------------------------------------------------
# Shared theme
# --------------------------------------------------------------------------
def _deep_merge(base: Dict[str, object], extra: Dict[str, object]) -> Dict[str, object]:
    """Recursive dict merge used so a figure can tweak one axis property without
    restating the whole shared axis block."""
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def base_layout(height: int = 420, **overrides) -> Dict[str, object]:
    layout = {
        'height': height,
        'template': 'plotly_dark',
        'paper_bgcolor': SURFACE['bg'],
        'plot_bgcolor': SURFACE['bg'],
        'font': FONT,
        'margin': {'l': 56, 'r': 30, 't': 24, 'b': 44},
        'hovermode': 'x unified',
        'hoverlabel': {
            'bgcolor': '#141a24',
            'bordercolor': SURFACE['border'],
            'font': {'color': SURFACE['text'], 'size': 12},
        },
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'x': 0,
            'bgcolor': 'rgba(0,0,0,0)',
            'font': {'size': 11},
        },
        'xaxis': {
            'gridcolor': SURFACE['grid'],
            'zerolinecolor': SURFACE['zeroline'],
            'linecolor': SURFACE['grid'],
            'showspikes': False,
        },
        'yaxis': {
            'gridcolor': SURFACE['grid'],
            'zerolinecolor': SURFACE['zeroline'],
            'linecolor': 'rgba(0,0,0,0)',
        },
    }
    return _deep_merge(layout, overrides)


def empty_figure(message: str, height: int = None) -> go.Figure:
    """Axis-less guide state — a centered message instead of an empty grid."""
    height = height or CHART_HEIGHTS['empty']
    fig = go.Figure()
    fig.update_layout(**base_layout(
        height=height, hovermode=False,
        xaxis={'visible': False},
        yaxis={'visible': False},
        showlegend=False,
        annotations=[{
            'text': message, 'x': 0.5, 'y': 0.5, 'xref': 'paper', 'yref': 'paper',
            'showarrow': False, 'font': {'color': SURFACE['text_muted'], 'size': 14},
        }],
    ))
    return fig


# --------------------------------------------------------------------------
# Overview — dual-axis trend with event overlays
# --------------------------------------------------------------------------
def trend_figure(dataset, client: str, lo: int, hi: int,
                 left_metric: str, right_metric: str,
                 grain: str = 'Daily', show_events: bool = True) -> go.Figure:
    """The flagship monitor: two metrics on independent axes with the release
    calendar overlaid, so a spike can be read against what shipped that week."""
    bundle = dataset['clients'][client]
    dates = dataset['dates'][lo:hi]
    if not dates:
        return empty_figure('Select a date range to plot.', CHART_HEIGHTS['trend'])

    fig = go.Figure()
    for metric, axis, dash in ((left_metric, 'y', 'solid'), (right_metric, 'y2', 'solid')):
        if not metric:
            continue
        how = 'last' if metric in STOCK_METRICS else 'sum'
        x, y = resample(dates, bundle['series'][metric][lo:hi], grain, how=how)
        color = metric_color(metric)
        fig.add_trace(go.Scatter(
            x=x, y=y, name=metric_label(metric),
            mode='lines', yaxis=axis,
            line={'color': color, 'width': 2, 'dash': dash},
            fill='tozeroy' if axis == 'y' else None,
            fillcolor=_soft(color) if axis == 'y' else None,
            hovertemplate=f'<b>{metric_label(metric)}</b> {_hover_number(metric_format(metric))}<extra></extra>',
        ))

    if show_events:
        _add_event_overlay(fig, bundle, dataset['dates'], lo, hi)

    fig.update_layout(**base_layout(
        height=CHART_HEIGHTS['trend'], margin={'l': 62, 'r': 62, 't': 30, 'b': 44},
        yaxis={
            'title': {'text': metric_label(left_metric),
                      'font': {'color': metric_color(left_metric)}},
            'tickfont': {'color': metric_color(left_metric)},
        },
        yaxis2={
            'title': {'text': metric_label(right_metric),
                      'font': {'color': metric_color(right_metric)}},
            'tickfont': {'color': metric_color(right_metric)},
            'overlaying': 'y', 'side': 'right', 'showgrid': False,
        },
    ))
    return fig


def _add_event_overlay(fig: go.Figure, bundle, all_dates: Sequence[str], lo: int, hi: int):
    """Vertical markers for release-calendar events inside the window.

    Capped at 14 markers: past that the overlay stops being an annotation and
    starts being the chart. When the cap bites, the largest-magnitude events win.
    """
    events = events_in_window(bundle['events'], all_dates, lo, hi)
    if not events:
        return
    if len(events) > 14:
        events = sorted(events, key=lambda e: -e['magnitude'])[:14]
        events.sort(key=lambda e: e['date'])

    seen_kinds = set()
    for event in events:
        color = EVENT_KINDS[event['kind']]['color']
        label = event['kind']
        client_suffix = f" · {event['client']}" if 'client' in event else ''
        fig.add_shape(
            type='line', x0=event['date'], x1=event['date'],
            y0=0, y1=1, yref='paper', xref='x',
            line={'color': color, 'width': 1, 'dash': 'dot'},
            layer='below',
        )
        fig.add_trace(go.Scatter(
            x=[event['date']], y=[1.0],
            mode='markers',
            marker={'symbol': 'triangle-down', 'size': 9, 'color': color,
                    'line': {'width': 0}},
            name=label,
            legendgroup=f'event-{label}',
            showlegend=label not in seen_kinds,
            yaxis='y3',
            hovertemplate=f'<b>{label}</b>{client_suffix}<br>%{{x}}<extra></extra>',
        ))
        seen_kinds.add(label)

    fig.update_layout(yaxis3={
        'overlaying': 'y', 'side': 'left', 'range': [0, 1],
        'showgrid': False, 'showticklabels': False, 'zeroline': False,
        'fixedrange': True,
    })


def _soft(hex_color: str, alpha: float = 0.10) -> str:
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f'rgba({r},{g},{b},{alpha})'


# --------------------------------------------------------------------------
# Audience — locations and geography
# --------------------------------------------------------------------------
def location_bar(dataset, client: str, level: str = 'city',
                 segment: str = 'All', top_n: int = 14) -> go.Figure:
    """Top audience locations for the selection, colored by the same segment
    palette the map uses."""
    rows = dataset['clients'][client]['locations']
    key = {'city': 'city', 'region': 'region', 'country': 'country'}[level]

    totals: Dict[str, int] = {}
    for row in rows:
        value = row['users'] if segment == 'All' else row['segments'].get(segment, 0)
        totals[row[key]] = totals.get(row[key], 0) + value

    ranked = sorted(totals.items(), key=lambda kv: -kv[1])[:top_n]
    if not ranked:
        return empty_figure('No location data for this selection.')
    ranked.reverse()

    color = ACCENTS['blue'] if segment == 'All' else SEGMENT_COLORS.get(segment, ACCENTS['blue'])
    fig = go.Figure(go.Bar(
        x=[value for _, value in ranked],
        y=[label for label, _ in ranked],
        orientation='h',
        marker={'color': color, 'line': {'width': 0}},
        hovertemplate='<b>%{y}</b><br>%{x:,.0f} users<extra></extra>',
    ))
    fig.update_layout(**base_layout(
        height=CHART_HEIGHTS['location_bar'], hovermode='closest',
        margin={'l': 130, 'r': 24, 't': 16, 'b': 40},
        showlegend=False,
        xaxis={'title': {'text': 'Users'}},
    ))
    return fig


def segment_mix(dataset, client: str) -> go.Figure:
    """Lifecycle funnel: how the audience splits across account maturity."""
    rows = dataset['clients'][client]['locations']
    totals = {name: sum(r['segments'][name] for r in rows) for name in SEGMENT_NAMES}
    grand = sum(totals.values()) or 1

    fig = go.Figure()
    for name in SEGMENT_NAMES:
        fig.add_trace(go.Bar(
            x=[totals[name] / grand * 100], y=['mix'], orientation='h',
            name=name, marker={'color': SEGMENT_COLORS[name], 'line': {'width': 0}},
            hovertemplate=f'<b>{name}</b><br>%{{x:.1f}}%<br>{totals[name]:,} users<extra></extra>',
        ))
    fig.update_layout(**base_layout(
        height=CHART_HEIGHTS['segment_mix'], hovermode='closest',
        margin={'l': 8, 'r': 8, 't': 8, 'b': 8},
        barmode='stack',
        xaxis={'visible': False, 'range': [0, 100]},
        yaxis={'visible': False},
        legend={'orientation': 'h', 'y': -0.6, 'x': 0, 'font': {'size': 11}},
    ))
    return fig


# --------------------------------------------------------------------------
# Behavior — relationships and correlation
# --------------------------------------------------------------------------
def relationship_scatter(dataset, client: str, lo: int, hi: int,
                         x_metric: str, y_metric: str) -> go.Figure:
    """Daily observations for two metrics with an OLS overlay and r-squared.

    The caption on the card is deliberate: this shows co-movement, not causation.
    """
    series = dataset['clients'][client]['series']
    xs = list(series[x_metric][lo:hi])
    ys = list(series[y_metric][lo:hi])
    dates = dataset['dates'][lo:hi]
    pairs = [(x, y, d) for x, y, d in zip(xs, ys, dates) if x or y]
    if len(pairs) < 5:
        return empty_figure('Not enough observations in this window.', CHART_HEIGHTS['scatter'])

    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    labels = [p[2] for p in pairs]
    slope, intercept, r2 = linear_fit(xs, ys)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode='markers', name='Daily observation',
        text=labels,
        marker={'size': 6, 'color': metric_color(y_metric), 'opacity': 0.45,
                'line': {'width': 0}},
        hovertemplate=('%{text}<br>' + metric_label(x_metric) + ': %{x:,.0f}<br>'
                       + metric_label(y_metric) + ': %{y:,.0f}<extra></extra>'),
    ))
    x_lo, x_hi = min(xs), max(xs)
    fig.add_trace(go.Scatter(
        x=[x_lo, x_hi],
        y=[slope * x_lo + intercept, slope * x_hi + intercept],
        mode='lines', name=f'Least-squares fit (R²={group(r2, 2)})',
        line={'color': ACCENTS['gold'], 'width': 2, 'dash': 'dash'},
        hoverinfo='skip',
    ))
    fig.update_layout(**base_layout(
        height=CHART_HEIGHTS['scatter'], hovermode='closest',
        xaxis={'title': {'text': metric_label(x_metric)}},
        yaxis={'title': {'text': metric_label(y_metric)}},
    ))
    return fig


def correlation_heatmap(dataset, client: str, lo: int, hi: int) -> go.Figure:
    """Correlation structure across the event families, annotated in-cell."""
    columns, matrix = correlation_matrix(dataset['clients'][client]['series'], lo, hi)
    labels = [metric_label(key) for key in columns]

    fig = go.Figure(go.Heatmap(
        z=matrix, x=labels, y=labels,
        zmin=-1, zmax=1,
        colorscale=[
            [0.0, '#7f3f4f'], [0.35, '#2b3340'], [0.5, '#1a212c'],
            [0.65, '#2c4a48'], [1.0, '#3f8f7a'],
        ],
        showscale=True,
        colorbar={'thickness': 10, 'outlinewidth': 0, 'tickfont': {'size': 10},
                  'len': 0.8},
        hovertemplate='%{y} vs %{x}<br>r = %{z:.2f}<extra></extra>',
        text=[[('+' if value >= 0 else '') + group(value, 2) for value in row]
              for row in matrix],
        texttemplate='%{text}',
        textfont={'size': 10, 'color': SURFACE['text']},
    ))
    fig.update_layout(**base_layout(
        height=CHART_HEIGHTS['correlation'], hovermode='closest',
        margin={'l': 150, 'r': 20, 't': 20, 'b': 120},
        xaxis={'tickangle': -35, 'showgrid': False},
        yaxis={'autorange': 'reversed', 'showgrid': False},
        showlegend=False,
    ))
    return fig


def engagement_trend(dataset, client: str, lo: int, hi: int,
                     grain: str = 'Weekly') -> go.Figure:
    """Session length against DAU/MAU stickiness — depth versus reach."""
    series = dataset['clients'][client]['series']
    dates = dataset['dates'][lo:hi]
    if not dates:
        return empty_figure('Select a date range to plot.', CHART_HEIGHTS['engagement'])

    x, minutes = resample(dates, series['session_minutes'][lo:hi], grain, how='last')
    _, dau = resample(dates, series['dau'][lo:hi], grain, how='last')
    _, mau = resample(dates, series['mau'][lo:hi], grain, how='last')
    stickiness = [(d / m * 100.0) if m else 0.0 for d, m in zip(dau, mau)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=minutes, name='Avg Session Minutes', mode='lines',
        line={'color': ACCENTS['lavender'], 'width': 2},
        fill='tozeroy', fillcolor=_soft(ACCENTS['lavender']),
        hovertemplate='<b>Avg Session</b> %{y:,.1f} min<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=x, y=stickiness, name='Stickiness (DAU/MAU)', mode='lines', yaxis='y2',
        line={'color': ACCENTS['cyan'], 'width': 2},
        hovertemplate='<b>Stickiness</b> %{y:.1f}%<extra></extra>',
    ))
    fig.update_layout(**base_layout(
        height=CHART_HEIGHTS['engagement'], margin={'l': 60, 'r': 60, 't': 26, 'b': 44},
        yaxis={'title': {'text': 'Minutes'}},
        yaxis2={'title': {'text': 'DAU / MAU'}, 'overlaying': 'y', 'side': 'right',
                'showgrid': False, 'ticksuffix': '%'},
    ))
    return fig


# --------------------------------------------------------------------------
# Revenue and retention
# --------------------------------------------------------------------------
def revenue_trend(dataset, client: str, lo: int, hi: int,
                  grain: str = 'Monthly') -> go.Figure:
    series = dataset['clients'][client]['series']
    dates = dataset['dates'][lo:hi]
    if not dates:
        return empty_figure('Select a date range to plot.')
    x, values = resample(dates, series['revenue'][lo:hi], grain, how='sum')

    fig = go.Figure(go.Bar(
        x=x, y=values, name='Revenue',
        marker={'color': ACCENTS['gold'], 'line': {'width': 0}},
        hovertemplate='<b>Revenue</b> $%{y:,.0f}<extra></extra>',
    ))
    if len(values) > 3:
        window = 3
        smoothed = [
            sum(values[max(0, i - window + 1):i + 1]) / len(values[max(0, i - window + 1):i + 1])
            for i in range(len(values))
        ]
        fig.add_trace(go.Scatter(
            x=x, y=smoothed, name=f'{window}-period average', mode='lines',
            line={'color': ACCENTS['amber'], 'width': 2, 'dash': 'dot'},
            hovertemplate='<b>Trend</b> $%{y:,.0f}<extra></extra>',
        ))
    fig.update_layout(**base_layout(
        height=CHART_HEIGHTS['revenue'], yaxis={'title': {'text': 'Revenue (USD)'}}))
    return fig


def revenue_mix_donut(dataset, client: str, dimension: str = 'revenue_type') -> go.Figure:
    rows = dataset['clients'][client]['revenue_mix'][dimension]
    rows = sorted(rows, key=lambda r: -r['revenue'])
    palette = [ACCENTS['gold'], ACCENTS['cyan'], ACCENTS['violet'],
               ACCENTS['green'], ACCENTS['coral'], ACCENTS['blue']]

    fig = go.Figure(go.Pie(
        labels=[r['label'] for r in rows],
        values=[r['revenue'] for r in rows],
        hole=0.62,
        sort=False,
        marker={'colors': palette[:len(rows)], 'line': {'color': '#10151d', 'width': 2}},
        textinfo='percent',
        textfont={'size': 11, 'color': '#0b0f17'},
        hovertemplate='<b>%{label}</b><br>$%{value:,.0f} (%{percent})<extra></extra>',
    ))
    fig.update_layout(**base_layout(
        height=CHART_HEIGHTS['mix_donut'], hovermode='closest',
        margin={'l': 8, 'r': 8, 't': 8, 'b': 8},
        xaxis={'visible': False},
        yaxis={'visible': False},
        legend={'orientation': 'v', 'x': 1.0, 'y': 0.5, 'yanchor': 'middle',
                'font': {'size': 11}},
    ))
    return fig


def churn_lines(dataset, clients: Sequence[str]) -> go.Figure:
    """Monthly membership churn for one or more accounts."""
    selected = [c for c in clients if c in dataset['clients']]
    if not selected:
        return empty_figure('Select at least one account to compare churn.', CHART_HEIGHTS['churn'])

    palette = [ACCENTS['coral'], ACCENTS['blue'], ACCENTS['green'],
               ACCENTS['violet'], ACCENTS['gold'], ACCENTS['cyan'],
               ACCENTS['mint'], ACCENTS['lavender']]

    fig = go.Figure()
    for index, name in enumerate(selected):
        rows = [r for r in dataset['clients'][name]['churn'] if r['start'] > 50]
        if not rows:
            continue
        fig.add_trace(go.Scatter(
            x=[f"{r['period']}-01" for r in rows],
            y=[r['churn_pct'] for r in rows],
            name=name, mode='lines+markers',
            line={'color': palette[index % len(palette)], 'width': 2},
            marker={'size': 5},
            customdata=[[r['lost'], r['start']] for r in rows],
            hovertemplate=(f'<b>{name}</b><br>%{{y:.2f}}% churned'
                           '<br>%{customdata[0]:,} lost of %{customdata[1]:,}<extra></extra>'),
        ))
    if not fig.data:
        return empty_figure('Not enough membership history for the selection.', CHART_HEIGHTS['churn'])

    fig.update_layout(**base_layout(
        height=CHART_HEIGHTS['churn'],
        yaxis={'ticksuffix': '%', 'title': {'text': 'Monthly churn'}}))
    return fig


def lifetime_bars(dataset, client: str) -> go.Figure:
    """Membership tenure distribution for the selected account."""
    buckets = dataset['clients'][client]['lifetime']['buckets']
    fig = go.Figure(go.Bar(
        x=[b['bucket'] for b in buckets],
        y=[b['members'] for b in buckets],
        marker={'color': ACCENTS['green'], 'line': {'width': 0}},
        hovertemplate='<b>%{x}</b><br>%{y:,.0f} members<extra></extra>',
    ))
    fig.update_layout(**base_layout(
        height=CHART_HEIGHTS['lifetime'], hovermode='closest', showlegend=False,
        yaxis={'title': {'text': 'Members'}},
        xaxis={'title': {'text': 'Time as a member'}},
    ))
    return fig


# --------------------------------------------------------------------------
# Audience Heatmap — the geography explorer
# --------------------------------------------------------------------------
# A basemap style that needs no access token, so the demo has no credential to
# leak and no account to expire.
MAP_STYLE = 'carto-darkmatter'

# View mode -> which aggregate sizes the bubbles. Color is always member share,
# which keeps the map audience intelligence rather than raw telemetry.
HEATMAP_METRICS = {
    'users': ('Audience', 'users'),
    'members': ('Members', 'members'),
    'engagement': ('Engagement', 'engagement'),
}

# Cap plotted bubbles so a portfolio-wide selection stays responsive. The KPI
# strip and the top-markets table still read the full aggregation.
MAX_BUBBLES = 600

MARKER_LIMITS = [500, 2000, 5000]

# Member-share color ramp: teal (few members) through to coral (member-dense).
MEMBER_SHARE_SCALE = [
    [0.0, '#1b6f7a'], [0.3, '#3fa39b'], [0.55, '#9fc9a5'],
    [0.78, '#eeb56a'], [1.0, '#f0715c'],
]


def _bubble_sizes(values: Sequence[float], ref_max: float = None, cap: int = 44):
    """Square-root sizing so a market ten times larger reads as ~3x the radius —
    area, not radius, tracks the value."""
    peak = ref_max if ref_max else (max(values) if values else 0)
    if not peak:
        return [6 for _ in values]
    return [6 + cap * math.sqrt(max(v, 0) / peak) for v in values]


def _map_view(markets: Sequence[Dict]):
    """User-weighted centroid and a zoom that fits the plotted spread."""
    if not markets:
        return {'center': {'lat': 39.0, 'lon': -98.0}, 'zoom': 2.2}
    weight = sum(m['users'] for m in markets) or 1
    lat = sum(m['lat'] * m['users'] for m in markets) / weight
    lon = sum(m['lon'] * m['users'] for m in markets) / weight
    span = max(
        max(m['lat'] for m in markets) - min(m['lat'] for m in markets),
        (max(m['lon'] for m in markets) - min(m['lon'] for m in markets)) / 2.0,
    )
    zoom = 2.6 if span > 60 else (3.0 if span > 25 else 4.0)
    return {'center': {'lat': round(lat, 3), 'lon': round(lon, 3)}, 'zoom': zoom}


def _map_layout(markets, height=None, uirevision=None, **overrides):
    layout = base_layout(
        height=height or CHART_HEIGHTS['map'],
        hovermode='closest',
        margin={'l': 0, 'r': 0, 't': 0, 'b': 0},
        xaxis={'visible': False},
        yaxis={'visible': False},
        map={'style': MAP_STYLE, **_map_view(markets)},
        # Keeps the viewer's pan/zoom across filter changes; it resets only when
        # the account changes, because a new account is a new map.
        uirevision=uirevision or 'map',
        **overrides,
    )
    return layout


def _market_hover(market: Dict) -> str:
    return (
        f"<b>{market['label']}</b><br>"
        f"Users: {group(market['users'])}<br>"
        f"Signed-up: {group(market['signed_up'])}<br>"
        f"Members: {group(market['members'])} "
        f"({group(market['member_share'] * 100, 1)}% share)<br>"
        f"Super users: {group(market['super_users'])}<br>"
        f"Engagement: {group(market['engagement'])}"
    )


def heatmap_map(dataset, client: str, display: str = 'market', metric: str = 'users',
                level: str = 'city', marker_limit: int = 2000,
                segments: Sequence[str] = SEGMENT_NAMES) -> go.Figure:
    """The audience map in one of three readings of the same geography.

    ``market``      one bubble per market, sized by the selected metric and
                    colored by member share.
    ``density``     a continuous heat surface — where activity concentrates,
                    with no market boundaries implied.
    ``individual``  one marker per user, colored by lifecycle segment.
    """
    locations = dataset['clients'][client]['locations']
    markets = aggregate_by_level(locations, level)
    if not markets:
        return empty_figure('No location data for this selection.', CHART_HEIGHTS['map'])

    if display == 'individual':
        return _individual_map(locations, markets, segments, marker_limit, client)
    if display == 'density':
        return _density_map(markets, metric, client)
    return _market_map(markets, metric, client)


def _market_map(markets, metric, client) -> go.Figure:
    plotted = markets[:MAX_BUBBLES]
    size_key = HEATMAP_METRICS.get(metric, HEATMAP_METRICS['users'])[1]
    shares = [m['member_share'] * 100 for m in plotted]
    # Headroom above the observed maximum so the top market is not pinned to the
    # end of the ramp, where every dense market would look identical.
    cmax = max(max(shares) if shares else 0, 5.0) * 1.08

    fig = go.Figure(go.Scattermap(
        lat=[m['lat'] for m in plotted],
        lon=[m['lon'] for m in plotted],
        mode='markers',
        marker={
            'size': _bubble_sizes([m[size_key] for m in plotted]),
            'color': shares,
            'colorscale': MEMBER_SHARE_SCALE,
            'cmin': 0,
            'cmax': cmax,
            'opacity': 0.82,
            'colorbar': {
                'title': {'text': 'Member share', 'side': 'right',
                          'font': {'color': SURFACE['text_secondary'], 'size': 11}},
                'tickfont': {'color': SURFACE['text_secondary'], 'size': 10},
                'ticksuffix': '%', 'nticks': 4, 'thickness': 8, 'len': 0.42,
                'x': 0.99, 'y': 0.5, 'yanchor': 'middle', 'outlinewidth': 0,
                'bgcolor': 'rgba(11,15,23,0.55)',
            },
        },
        customdata=[m['name'] for m in plotted],
        text=[_market_hover(m) for m in plotted],
        hovertemplate='%{text}<extra></extra>',
        name='',
    ))
    fig.update_layout(**_map_layout(plotted, uirevision=client, showlegend=False))
    return fig


def _density_map(markets, metric, client) -> go.Figure:
    size_key = HEATMAP_METRICS.get(metric, HEATMAP_METRICS['users'])[1]
    values = [max(m[size_key], 0) for m in markets]
    peak = max(values) if values else 1
    # Weight by the square root as well: raw counts let one metro saturate the
    # surface and flatten every other market to invisible.
    weights = [math.sqrt(v / peak) if peak else 0 for v in values]

    fig = go.Figure(go.Densitymap(
        lat=[m['lat'] for m in markets],
        lon=[m['lon'] for m in markets],
        z=weights,
        radius=34,
        colorscale='Inferno',
        opacity=0.72,
        colorbar={
            'title': {'text': HEATMAP_METRICS.get(metric, ('Audience',))[0],
                      'side': 'right',
                      'font': {'color': SURFACE['text_secondary'], 'size': 11}},
            'tickfont': {'color': SURFACE['text_secondary'], 'size': 10},
            'showticklabels': False, 'thickness': 8, 'len': 0.42,
            'x': 0.99, 'y': 0.5, 'yanchor': 'middle', 'outlinewidth': 0,
            'bgcolor': 'rgba(11,15,23,0.55)',
        },
        text=[m['label'] for m in markets],
        customdata=[[m['name'], m['users']] for m in markets],
        hovertemplate='<b>%{text}</b><br>%{customdata[1]:,.0f} users<extra></extra>',
        name='',
    ))
    fig.update_layout(**_map_layout(markets, uirevision=client, showlegend=False))
    return fig


def _individual_map(locations, markets, segments, marker_limit, client) -> go.Figure:
    active = [s for s in SEGMENT_NAMES if s in set(segments)] or list(SEGMENT_NAMES)
    points = spread_within_city(locations, marker_limit, salt=client)

    fig = go.Figure()
    for segment in active:
        subset = [p for p in points if p['segment'] == segment]
        if not subset:
            continue
        fig.add_trace(go.Scattermap(
            lat=[p['lat'] for p in subset],
            lon=[p['lon'] for p in subset],
            mode='markers',
            name=f'{segment} ({group(len(subset))})',
            marker={'size': 6, 'color': SEGMENT_COLORS[segment], 'opacity': 0.7},
            text=[p['label'] for p in subset],
            hovertemplate=f'<b>%{{text}}</b><br>{segment}<extra></extra>',
        ))

    if not fig.data:
        return empty_figure('No users in the selected segments.', CHART_HEIGHTS['map'])

    fig.update_layout(**_map_layout(
        markets, uirevision=client, showlegend=True,
        legend={'orientation': 'h', 'y': 0.02, 'x': 0.02, 'yanchor': 'bottom',
                'bgcolor': 'rgba(11,15,23,0.72)', 'font': {'size': 11},
                'bordercolor': SURFACE['border'], 'borderwidth': 1},
    ))
    return fig


def growth_map(dataset, client: str, level: str = 'city') -> go.Figure:
    """Cumulative audience arrival, one animation frame per month.

    Bubble sizes are pinned to the final frame's maximum so a market growing is
    visible as growth, rather than every frame rescaling to its own peak and the
    map appearing static.
    """
    bundle = dataset['clients'][client]
    markets = aggregate_by_level(bundle['locations'], level)
    frames_data = growth_frames(bundle['monthly_ramp'], markets)
    if len(frames_data) < 2:
        return empty_figure('Not enough history to animate.', CHART_HEIGHTS['growth'])

    size_ref = max((m['users'] for m in frames_data[-1]['markets']), default=1)

    def trace_for(frame):
        rows = frame['markets']
        return go.Scattermap(
            lat=[r['lat'] for r in rows],
            lon=[r['lon'] for r in rows],
            mode='markers',
            marker={
                'size': _bubble_sizes([r['users'] for r in rows], ref_max=size_ref),
                'color': [r['member_share'] * 100 for r in rows],
                'colorscale': MEMBER_SHARE_SCALE,
                'cmin': 0, 'cmax': 24, 'opacity': 0.8,
            },
            text=[r['label'] for r in rows],
            customdata=[r['users'] for r in rows],
            hovertemplate='<b>%{text}</b><br>%{customdata:,.0f} users<extra></extra>',
            name='',
        )

    fig = go.Figure(
        data=[trace_for(frames_data[0])],
        frames=[go.Frame(data=[trace_for(f)], name=f['period']) for f in frames_data],
    )

    play_args = {'frame': {'duration': 320, 'redraw': True},
                 'transition': {'duration': 0}, 'mode': 'immediate'}
    fig.update_layout(**_map_layout(
        markets, height=CHART_HEIGHTS['growth'],
        # Not keyed on the client: an animation must reset its camera when the
        # account changes, and there is no filter here to preserve zoom across.
        uirevision='growth',
        showlegend=False,
        updatemenus=[{
            'type': 'buttons', 'direction': 'left',
            'x': 0.01, 'y': 0.02, 'xanchor': 'left', 'yanchor': 'bottom',
            'pad': {'l': 6, 'r': 6, 't': 6, 'b': 6},
            'bgcolor': 'rgba(11,15,23,0.78)',
            'bordercolor': SURFACE['border'],
            'font': {'color': SURFACE['text'], 'size': 12},
            'showactive': False,
            'buttons': [
                {'label': '▶  Play', 'method': 'animate', 'args': [None, play_args]},
                {'label': '❚❚  Pause', 'method': 'animate',
                 'args': [[None], {'frame': {'duration': 0, 'redraw': False},
                                   'mode': 'immediate'}]},
            ],
        }],
        sliders=[{
            'active': 0,
            'x': 0.16, 'y': 0.02, 'len': 0.66,
            'xanchor': 'left', 'yanchor': 'bottom',
            'pad': {'t': 6, 'b': 6},
            'bgcolor': 'rgba(148,163,184,0.35)',
            'bordercolor': 'rgba(0,0,0,0)',
            'activebgcolor': ACCENTS['blue'],
            'tickcolor': 'rgba(0,0,0,0)',
            'font': {'color': SURFACE['text_secondary'], 'size': 10},
            'currentvalue': {'prefix': 'Month: ', 'xanchor': 'left',
                             'font': {'color': SURFACE['text'], 'size': 13}},
            'steps': [{
                'label': f['period'],
                'method': 'animate',
                'args': [[f['period']], {'frame': {'duration': 0, 'redraw': True},
                                         'mode': 'immediate'}],
            } for f in frames_data],
        }],
    ))
    return fig


def heatmap_summary(dataset, client: str, level: str = 'city') -> Dict[str, object]:
    """KPI strip values for the heatmap: reach, spread, and member density."""
    markets = aggregate_by_level(dataset['clients'][client]['locations'], level)
    users = sum(m['users'] for m in markets)
    members = sum(m['members'] for m in markets)
    top = markets[0] if markets else None
    # How concentrated the audience is: the share sitting in the top five markets.
    top_five = sum(m['users'] for m in markets[:5])
    return {
        'users': users,
        'markets': len(markets),
        'member_share': (members / users * 100) if users else 0.0,
        'top_label': top['label'] if top else '—',
        'top_users': top['users'] if top else 0,
        'concentration': (top_five / users * 100) if users else 0.0,
    }


def top_locations(dataset, client: str, level: str = 'city', limit: int = 10):
    """Ranked markets for the table under the map."""
    markets = aggregate_by_level(dataset['clients'][client]['locations'], level)
    return [
        {
            'rank': index + 1,
            'name': market['name'],
            'label': market['label'],
            'users': market['users'],
            'signed_up': market['signed_up'],
            'members': market['members'],
            'member_share': market['member_share'] * 100,
            'engagement': market['engagement'],
        }
        for index, market in enumerate(markets[:limit])
    ]


def location_detail(dataset, client: str, level: str, name: str):
    """The drilldown panel's content for one clicked market."""
    markets = aggregate_by_level(dataset['clients'][client]['locations'], level)
    match = next((m for m in markets if m['name'] == name), None)
    if match is None:
        return None
    total = sum(m['users'] for m in markets) or 1
    return {
        'label': match['label'],
        'users': match['users'],
        'share_of_audience': match['users'] / total * 100,
        'segments': match['segments'],
        'members': match['members'],
        'member_share': match['member_share'] * 100,
        'engagement': match['engagement'],
        'engagement_per_user': match['engagement'] / (match['users'] or 1),
    }


__all__ = [
    'CHART_HEIGHTS', 'base_layout', 'group', 'round_half_up',
    'growth_map', 'heatmap_map', 'heatmap_summary', 'location_detail',
    'top_locations', 'churn_lines', 'correlation_heatmap', 'empty_figure',
    'engagement_trend', 'fmt_compact', 'fmt_value', 'lifetime_bars',
    'location_bar', 'relationship_scatter', 'revenue_mix_donut', 'revenue_trend',
    'segment_mix', 'trend_figure',
]
