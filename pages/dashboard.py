"""Live demo: the Frontrow Analytics product dashboard.

An interactive, fully wired rebuild of the multi-tenant product analytics
dashboard described in the Selected Work case studies, running on a deterministic
synthetic dataset (see :mod:`demo_dashboard.data`). Same structure as the
production system it mirrors — client scoping, KPI monitoring with a release
overlay, audience geography, behavioral diagnostics, revenue and retention — with
every name and number invented for this portfolio.

All four sections stay mounted and are toggled with a class, so every control
keeps its callback wiring instead of being torn down when a section is hidden.
"""

import dash
from dash import Input, Output, callback, dash_table, dcc, html

from demo_dashboard.config import (
    AXIS_METRICS,
    BRAND,
    BRAND_MARK,
    BRAND_TAGLINE,
    CLIENTS,
    CLIENT_NAMES,
    DATE_PRESETS,
    DEFAULT_CLIENT,
    DEFAULT_PRESET,
    SEGMENT_NAMES,
    metric_format,
    metric_label,
)
from demo_dashboard.data import (
    delta_pct,
    get_dataset,
    summarize,
    window_indices,
)
from demo_dashboard import figures as fig_builders
from demo_dashboard.figures import CHART_HEIGHTS, fmt_compact, fmt_value, group


dash.register_page(
    __name__,
    path='/dashboard',
    order=2,
    name='Live Demo',
    title='Live Demo | Frontrow Analytics Dashboard',
)


DATASET = get_dataset()
PRESET_DAYS = dict(DATE_PRESETS)

SECTIONS = [
    ('overview', 'Overview', 'Portfolio KPIs and the release calendar'),
    ('audience', 'Audience Heatmap', 'Where the fanbase is and how it converts'),
    ('behavior', 'Behavior', 'Relationships between product signals'),
    ('revenue', 'Revenue & Retention', 'Monetization, churn, and tenure'),
]

GRAPH_CONFIG = {'displayModeBar': False, 'showTips': False, 'responsive': True}

METRIC_OPTIONS = [{'label': metric_label(key), 'value': key} for key in AXIS_METRICS]

TABLE_STYLE = {'overflowX': 'auto'}
TABLE_HEADER = {
    'backgroundColor': '#141a24',
    'color': '#aab4c3',
    'fontWeight': '600',
    'textTransform': 'uppercase',
    'letterSpacing': '0.06em',
    'fontSize': '11px',
    'border': 'none',
    'borderBottom': '1px solid #263244',
    'padding': '10px 12px',
}
TABLE_CELL = {
    'backgroundColor': 'transparent',
    'color': '#e8eef6',
    'border': 'none',
    'borderBottom': '1px solid rgba(148, 163, 184, 0.10)',
    'padding': '9px 12px',
    'fontSize': '12.5px',
    'fontFamily': 'Public Sans, sans-serif',
    'textAlign': 'right',
}
TABLE_CONDITIONAL = [
    {'if': {'column_id': 'Metric'}, 'textAlign': 'left', 'fontWeight': '600'},
    {'if': {'column_id': 'Fan'}, 'textAlign': 'left', 'fontWeight': '600'},
    {'if': {'column_id': 'Account'}, 'textAlign': 'left'},
    {'if': {'column_id': 'Location'}, 'textAlign': 'left'},
    {'if': {'column_id': 'Market'}, 'textAlign': 'left'},
    {'if': {'column_id': 'Tier'}, 'textAlign': 'left'},
    {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgba(148, 163, 184, 0.035)'},
]


# --------------------------------------------------------------------------
# Small presentational builders
# --------------------------------------------------------------------------
def _card(*children, title=None, subtitle=None, className=''):
    body = list(children)
    if title:
        header = [html.H3(title, className='fr-card-title')]
        if subtitle:
            header.append(html.P(subtitle, className='fr-card-subtitle'))
        body = [html.Div(header, className='fr-card-header'), *body]
    return html.Div(body, className=f'fr-card {className}'.strip())


def _control(label, control, grow=False):
    return html.Div(
        [html.Label(label, className='fr-control-label'), control],
        className='fr-control' + (' fr-control--grow' if grow else ''),
    )


def _kpi_tile(slot_id, label, accent):
    return html.Div(
        [
            html.Div(label, className='fr-tile-label'),
            html.Div('—', id=f'{slot_id}-value', className='fr-tile-value'),
            html.Div('—', id=f'{slot_id}-delta', className='fr-tile-delta'),
        ],
        className=f'fr-tile fr-tile--{accent}',
    )


def _graph(graph_id, chart):
    """A graph whose container is pinned to the same height its figure uses.

    dcc.Graph runs with ``responsive: true``; without a CSS height, a width
    change collapses the container to zero while the figure keeps its own
    height, and the SVG then paints over the card below it. Reading the number
    from ``CHART_HEIGHTS`` keeps the two from drifting apart.
    """
    return dcc.Graph(
        id=graph_id,
        config=GRAPH_CONFIG,
        style={'height': f"{CHART_HEIGHTS[chart]}px"},
    )


def _delta_chip(value):
    """Direction + magnitude for a KPI tile. Returns (text, class suffix)."""
    if abs(value) < 0.05:
        return 'flat vs. prior half', 'flat'
    arrow = '▲' if value > 0 else '▼'
    return f'{arrow} {group(abs(value), 1)}% vs. prior half', 'up' if value > 0 else 'down'


# --------------------------------------------------------------------------
# Sidebar + global controls
# --------------------------------------------------------------------------
sidebar = html.Aside(
    className='fr-sidebar',
    children=[
        html.Div(
            [
                html.Div(BRAND_MARK, className='fr-brand-mark'),
                html.Div(
                    [
                        html.Div(BRAND, className='fr-brand-name'),
                        html.Div(BRAND_TAGLINE, className='fr-brand-tagline'),
                    ]
                ),
            ],
            className='fr-brand',
        ),
        dcc.RadioItems(
            id='fr-section',
            options=[
                {
                    'label': html.Span(
                        [
                            html.Span(title, className='fr-nav-title'),
                            html.Span(blurb, className='fr-nav-blurb'),
                        ]
                    ),
                    'value': key,
                }
                for key, title, blurb in SECTIONS
            ],
            value='overview',
            className='fr-nav',
            inputClassName='fr-nav-input',
            labelClassName='fr-nav-link',
        ),
        html.Div(
            [
                html.Div('DATA WINDOW', className='fr-sidebar-tag'),
                html.Div(
                    f"{DATASET['start_date']} → {DATASET['end_date']}",
                    className='fr-sidebar-value',
                ),
                html.Div('SOURCE', className='fr-sidebar-tag'),
                html.Div('Synthetic · seeded', className='fr-sidebar-value'),
            ],
            className='fr-sidebar-footer',
        ),
    ],
)


global_controls = html.Div(
    className='fr-control-bar',
    children=[
        _control(
            'Client account',
            dcc.Dropdown(
                id='fr-client',
                options=[{'label': name, 'value': name} for name in CLIENTS],
                value=DEFAULT_CLIENT,
                clearable=False,
                className='fr-dropdown',
            ),
            grow=True,
        ),
        _control(
            'Date window',
            dcc.RadioItems(
                id='fr-preset',
                options=[{'label': label, 'value': label} for label, _ in DATE_PRESETS],
                value=DEFAULT_PRESET,
                className='fr-segmented',
                inputClassName='fr-segmented-input',
                labelClassName='fr-segmented-label',
            ),
        ),
    ],
)


# --------------------------------------------------------------------------
# Section: Overview
# --------------------------------------------------------------------------
panel_overview = html.Div(
    id='fr-panel-overview',
    className='fr-panel',
    children=[
        html.Div(
            className='fr-hero',
            children=[
                html.Div(
                    className='fr-hero-primary',
                    children=[
                        html.Div(id='fr-hero-client', className='fr-hero-client'),
                        html.Div(id='fr-hero-period', className='fr-hero-period'),
                        html.Div('—', id='fr-hero-value', className='fr-hero-value'),
                        html.Div('Downloads', className='fr-hero-label'),
                        html.Div(id='fr-hero-insight', className='fr-hero-insight'),
                    ],
                ),
                html.Div(
                    className='fr-tile-grid',
                    children=[
                        _kpi_tile('fr-kpi-dau', 'Avg Daily Active Users', 'blue'),
                        _kpi_tile('fr-kpi-members', 'Current Memberships', 'green'),
                        _kpi_tile('fr-kpi-revenue', 'Revenue', 'gold'),
                        _kpi_tile('fr-kpi-posts', 'Timeline Posts', 'violet'),
                    ],
                ),
            ],
        ),
        _card(
            html.Div(
                className='fr-inline-controls',
                children=[
                    _control(
                        'Left axis',
                        dcc.Dropdown(id='fr-left-metric', options=METRIC_OPTIONS,
                                     value='dau', clearable=False, className='fr-dropdown'),
                    ),
                    _control(
                        'Right axis',
                        dcc.Dropdown(id='fr-right-metric', options=METRIC_OPTIONS,
                                     value='memberships', clearable=False,
                                     className='fr-dropdown'),
                    ),
                    _control(
                        'Interval',
                        dcc.Dropdown(
                            id='fr-grain',
                            options=[{'label': g, 'value': g}
                                     for g in ('Daily', 'Weekly', 'Monthly', 'Quarterly')],
                            value='Daily', clearable=False, className='fr-dropdown',
                        ),
                    ),
                    _control(
                        'Overlay',
                        dcc.Checklist(
                            id='fr-show-events',
                            options=[{'label': 'Release calendar', 'value': 'on'}],
                            value=['on'],
                            className='fr-checklist',
                            inputClassName='fr-checkbox',
                            labelClassName='fr-checklist-label',
                        ),
                    ),
                ],
            ),
            _graph('fr-trend', 'trend'),
            title='Activity Trends',
            subtitle=('Two metrics on independent axes with the release calendar '
                      'overlaid, so a spike can be read against what shipped that week.'),
        ),
        _card(
            html.Div(id='fr-summary-table'),
            title='Period Summary',
            subtitle='Mean, range, and totals for the selected window.',
        ),
    ],
)


# --------------------------------------------------------------------------
# Section: Audience Heatmap
# --------------------------------------------------------------------------
DISPLAY_OPTIONS = [
    {'label': 'Market bubbles', 'value': 'market'},
    {'label': 'Density heatmap', 'value': 'density'},
    {'label': 'Individual users', 'value': 'individual'},
]

LEVEL_OPTIONS = [
    {'label': 'City', 'value': 'city'},
    {'label': 'Region', 'value': 'region'},
    {'label': 'Country', 'value': 'country'},
]

METRIC_VIEW_OPTIONS = [
    {'label': label, 'value': key}
    for key, (label, _) in fig_builders.HEATMAP_METRICS.items()
]

panel_audience = html.Div(
    id='fr-panel-audience',
    className='fr-panel',
    children=[
        html.Div(
            className='fr-tile-grid fr-tile-grid--wide',
            children=[
                _kpi_tile('fr-geo-users', 'Mapped users', 'blue'),
                _kpi_tile('fr-geo-markets', 'Markets reached', 'violet'),
                _kpi_tile('fr-geo-share', 'Member share', 'green'),
                _kpi_tile('fr-geo-top', 'Largest market', 'gold'),
            ],
        ),
        _card(
            html.Div(
                className='fr-inline-controls',
                children=[
                    _control(
                        'Display',
                        dcc.Dropdown(id='fr-map-display', options=DISPLAY_OPTIONS,
                                     value='market', clearable=False,
                                     className='fr-dropdown'),
                    ),
                    _control(
                        'Size by',
                        dcc.Dropdown(id='fr-map-metric', options=METRIC_VIEW_OPTIONS,
                                     value='users', clearable=False,
                                     className='fr-dropdown'),
                    ),
                    _control(
                        'Location level',
                        dcc.Dropdown(id='fr-loc-level', options=LEVEL_OPTIONS,
                                     value='city', clearable=False,
                                     className='fr-dropdown'),
                    ),
                    _control(
                        'Lifecycle segments',
                        dcc.Checklist(
                            id='fr-segments',
                            options=[{'label': name, 'value': name} for name in SEGMENT_NAMES],
                            value=list(SEGMENT_NAMES),
                            className='fr-checklist fr-checklist--inline',
                            inputClassName='fr-checkbox',
                            labelClassName='fr-checklist-label',
                        ),
                        grow=True,
                    ),
                ],
            ),
            html.Div(id='fr-map-hint', className='fr-note fr-note--tight'),
            _graph('fr-map', 'map'),
            html.Div(id='fr-map-detail', className='fr-detail'),
            title='Audience Heatmap',
            subtitle=('Market bubbles size each location by the selected metric and '
                      'color it by member share; the density view drops the boundaries '
                      'to show where activity actually concentrates. Click a market to '
                      'drill into it.'),
        ),
        _card(
            _graph('fr-growth', 'growth'),
            html.P(
                'Each frame adds one month of cumulative arrivals. Bubble sizes are '
                'pinned to the final month, so growth reads as growth rather than every '
                'frame rescaling to its own peak.',
                className='fr-note',
            ),
            title='How the Audience Spread',
            subtitle='Cumulative arrival by market, replayed month by month.',
        ),
        _card(
            html.Div(id='fr-top-markets'),
            title='Top Markets',
            subtitle='The largest markets at the selected location level.',
        ),
        _card(
            _graph('fr-segment-mix', 'segment_mix'),
            html.Div(id='fr-segment-note', className='fr-note'),
            title='Lifecycle Mix',
            subtitle='Share of the audience at each stage, from install to super user.',
        ),
        _card(
            html.Div(
                className='fr-inline-controls',
                children=[
                    _control(
                        'Segment',
                        dcc.Dropdown(
                            id='fr-loc-segment',
                            options=([{'label': 'All users', 'value': 'All'}]
                                     + [{'label': name, 'value': name} for name in SEGMENT_NAMES]),
                            value='All', clearable=False, className='fr-dropdown',
                        ),
                    ),
                ],
            ),
            _graph('fr-location-bar', 'location_bar'),
            title='Market Ranking by Segment',
            subtitle='The same geography filtered to one stage of the lifecycle.',
        ),
    ],
)


# --------------------------------------------------------------------------
# Section: Behavior
# --------------------------------------------------------------------------
panel_behavior = html.Div(
    id='fr-panel-behavior',
    className='fr-panel',
    children=[
        _card(
            html.Div(
                className='fr-inline-controls',
                children=[
                    _control(
                        'X metric',
                        dcc.Dropdown(id='fr-x-metric', options=METRIC_OPTIONS,
                                     value='dau', clearable=False, className='fr-dropdown'),
                    ),
                    _control(
                        'Y metric',
                        dcc.Dropdown(id='fr-y-metric', options=METRIC_OPTIONS,
                                     value='memberships', clearable=False,
                                     className='fr-dropdown'),
                    ),
                ],
            ),
            _graph('fr-scatter', 'scatter'),
            html.Div(id='fr-scatter-readout', className='fr-readout'),
            title='Relationship Diagnostics',
            subtitle=('Daily observations with a least-squares fit. Co-movement is '
                      'not causation — this is a triage tool for what to test next.'),
        ),
        _card(
            _graph('fr-correlation', 'correlation'),
            title='Correlation Structure',
            subtitle='Pearson correlation across the product event families in the window.',
        ),
        _card(
            _graph('fr-engagement', 'engagement'),
            title='Depth vs. Reach',
            subtitle=('Average session length against DAU/MAU stickiness — whether the '
                      'audience is growing wider or getting more engaged.'),
        ),
    ],
)


# --------------------------------------------------------------------------
# Section: Revenue & Retention
# --------------------------------------------------------------------------
panel_revenue = html.Div(
    id='fr-panel-revenue',
    className='fr-panel',
    children=[
        html.Div(
            className='fr-tile-grid fr-tile-grid--wide',
            children=[
                _kpi_tile('fr-rev-total', 'Revenue in window', 'gold'),
                _kpi_tile('fr-rev-arpm', 'Revenue per member / mo', 'amber'),
                _kpi_tile('fr-rev-churn', 'Latest monthly churn', 'coral'),
                _kpi_tile('fr-rev-tenure', 'Median membership tenure', 'green'),
            ],
        ),
        _card(
            html.Div(
                className='fr-inline-controls',
                children=[
                    _control(
                        'Interval',
                        dcc.Dropdown(
                            id='fr-rev-grain',
                            options=[{'label': g, 'value': g}
                                     for g in ('Daily', 'Weekly', 'Monthly', 'Quarterly')],
                            value='Monthly', clearable=False, className='fr-dropdown',
                        ),
                    ),
                ],
            ),
            _graph('fr-revenue', 'revenue'),
            title='Revenue Trend',
            subtitle='Gross in-app revenue for the selected account and window.',
        ),
        html.Div(
            className='fr-split',
            children=[
                _card(_graph('fr-mix-type', 'mix_donut'), title='Revenue by Type',
                      subtitle='Product mix across the full history.'),
                _card(_graph('fr-mix-platform', 'mix_donut'), title='Revenue by Platform',
                      subtitle='Store split across the full history.'),
            ],
        ),
        _card(
            html.Div(
                className='fr-inline-controls',
                children=[
                    _control(
                        'Compare accounts',
                        dcc.Dropdown(
                            id='fr-churn-clients',
                            options=[{'label': name, 'value': name} for name in CLIENTS],
                            value=list(CLIENT_NAMES[:3]),
                            multi=True,
                            className='fr-dropdown',
                        ),
                        grow=True,
                    ),
                ],
            ),
            _graph('fr-churn', 'churn'),
            html.P(
                'Lost members are the residual of the membership stock '
                '(start + joins − end), so churn can never disagree with the '
                'membership line on the Overview tab.',
                className='fr-note',
            ),
            title='Monthly Membership Churn',
            subtitle='Share of the starting membership base lost each month.',
        ),
        _card(
            _graph('fr-lifetime', 'lifetime'),
            title='Membership Tenure',
            subtitle='How long current members have been subscribed.',
        ),
        _card(
            html.Div(id='fr-top-users'),
            title='Most Engaged Fans',
            subtitle='Leaderboard by time in app for the selected account.',
        ),
    ],
)


# --------------------------------------------------------------------------
# Page layout
# --------------------------------------------------------------------------
layout = html.Div(
    className='content-stack fr-page',
    children=[
        html.Section(
            className='reveal-up',
            children=[
                html.Div(
                    className='fr-intro',
                    children=[
                        html.Div(
                            [
                                html.Div('LIVE DEMO', className='eyebrow'),
                                html.H2('Frontrow Analytics — Product Dashboard',
                                        className='section-hero-title'),
                                html.P(
                                    'A working rebuild of the multi-tenant product analytics '
                                    'system described in the case studies below: client-scoped '
                                    'KPI monitoring with a release overlay, audience geography, '
                                    'behavioral diagnostics, and revenue/retention analysis. '
                                    'Every control is live.',
                                    className='section-hero-subtitle',
                                ),
                            ]
                        ),
                        # Counts are read from the dataset rather than written down, so
                        # the panel cannot describe a build it is not running on.
                        html.Dl(
                            className='fr-spec',
                            children=[
                                item
                                for label, value in (
                                    ('This build', 'Python · Dash · Plotly'),
                                    # The demo genuinely ships twice from one
                                    # dataset; the static twin is what the
                                    # published site serves.
                                    ('Also ships as',
                                     'Static plotly.js build, same dataset'),
                                    # Names the real system this demo rebuilds,
                                    # not this page — see the case studies.
                                    ('Original system',
                                     'React · TypeScript · FastAPI · deck.gl'),
                                    ('Dataset',
                                     f"{len(DATASET['dates'])} days · "
                                     f'{len(CLIENTS)} accounts · seeded'),
                                    ('Surfaces',
                                     ' · '.join(title for _, title, _ in SECTIONS)),
                                )
                                for item in (
                                    html.Dt(label, className='fr-spec-label'),
                                    html.Dd(value, className='fr-spec-value'),
                                )
                            ],
                        ),
                    ],
                ),
                html.Div(
                    [
                        html.Span('Synthetic data', className='fr-banner-tag'),
                        html.Span(
                            'Frontrow and every account, fan, and figure on this page are '
                            'invented for this portfolio. The structure mirrors production '
                            'work, and the distributions behind it — stickiness, churn, store '
                            'mix, market concentration, content cadence — are calibrated '
                            'against a real client base. No real name, record, or value '
                            'appears anywhere.',
                            className='fr-banner-copy',
                        ),
                    ],
                    className='fr-banner',
                ),
            ],
        ),
        html.Div(
            className='fr-shell',
            children=[
                sidebar,
                html.Div(
                    className='fr-main',
                    children=[
                        global_controls,
                        panel_overview,
                        panel_audience,
                        panel_behavior,
                        panel_revenue,
                    ],
                ),
            ],
        ),
    ],
)


# --------------------------------------------------------------------------
# Callbacks
# --------------------------------------------------------------------------
@callback(
    [Output(f'fr-panel-{key}', 'className') for key, _, _ in SECTIONS],
    Input('fr-section', 'value'),
)
def toggle_sections(active):
    """Show one section at a time.

    Panels are hidden with a class rather than replaced, so every control in a
    hidden section stays mounted and its callbacks keep firing — the alternative
    (rendering the active panel only) breaks any callback whose input is
    currently off-screen.
    """
    return ['fr-panel' if key == active else 'fr-panel fr-panel--hidden'
            for key, _, _ in SECTIONS]


def _window(preset):
    return window_indices(DATASET['dates'], PRESET_DAYS.get(preset, 365))


def _series(client):
    return DATASET['clients'][client]['series']


# ---- Overview -------------------------------------------------------------
@callback(
    Output('fr-hero-client', 'children'),
    Output('fr-hero-period', 'children'),
    Output('fr-hero-value', 'children'),
    Output('fr-hero-insight', 'children'),
    Output('fr-kpi-dau-value', 'children'),
    Output('fr-kpi-dau-delta', 'children'),
    Output('fr-kpi-dau-delta', 'className'),
    Output('fr-kpi-members-value', 'children'),
    Output('fr-kpi-members-delta', 'children'),
    Output('fr-kpi-members-delta', 'className'),
    Output('fr-kpi-revenue-value', 'children'),
    Output('fr-kpi-revenue-delta', 'children'),
    Output('fr-kpi-revenue-delta', 'className'),
    Output('fr-kpi-posts-value', 'children'),
    Output('fr-kpi-posts-delta', 'children'),
    Output('fr-kpi-posts-delta', 'className'),
    Input('fr-client', 'value'),
    Input('fr-preset', 'value'),
)
def update_hero(client, preset):
    lo, hi = _window(preset)
    series = _series(client)
    dates = DATASET['dates']
    bundle = DATASET['clients'][client]

    downloads = summarize(series['downloads'][lo:hi])['total']
    dau = summarize(series['dau'][lo:hi])['mean']
    members = series['memberships'][hi - 1]
    revenue = summarize(series['revenue'][lo:hi])['total']
    posts = summarize(series['posts'][lo:hi])['total']

    top_market = bundle['locations'][0]['city'] if bundle['locations'] else '—'
    insight = f'Top market · {top_market}'

    tiles = []
    for value, key, window in (
        (dau, 'dau', series['dau'][lo:hi]),
        (members, 'memberships', series['memberships'][lo:hi]),
        (revenue, 'revenue', series['revenue'][lo:hi]),
        (posts, 'posts', series['posts'][lo:hi]),
    ):
        text, direction = _delta_chip(delta_pct(window))
        tiles.extend([
            fmt_compact(value, metric_format(key)),
            text,
            f'fr-tile-delta fr-tile-delta--{direction}',
        ])

    return (
        client,
        f'{dates[lo]} → {dates[hi - 1]}',
        fmt_compact(downloads),
        insight,
        *tiles,
    )


@callback(
    Output('fr-trend', 'figure'),
    Input('fr-client', 'value'),
    Input('fr-preset', 'value'),
    Input('fr-left-metric', 'value'),
    Input('fr-right-metric', 'value'),
    Input('fr-grain', 'value'),
    Input('fr-show-events', 'value'),
)
def update_trend(client, preset, left, right, grain, show_events):
    lo, hi = _window(preset)
    return fig_builders.trend_figure(
        DATASET, client, lo, hi, left, right, grain, bool(show_events)
    )


@callback(
    Output('fr-summary-table', 'children'),
    Input('fr-client', 'value'),
    Input('fr-preset', 'value'),
)
def update_summary(client, preset):
    lo, hi = _window(preset)
    series = _series(client)
    rows = []
    for key in ('downloads', 'dau', 'mau', 'memberships', 'new_memberships',
                'revenue', 'posts', 'notifications', 'livestreams', 'auctions'):
        stats = summarize(series[key][lo:hi])
        kind = metric_format(key)
        # Totals are meaningless for stock metrics (a membership count is not
        # additive across days), so those rows show the closing level instead.
        is_stock = key in fig_builders.STOCK_METRICS
        rows.append({
            'Metric': metric_label(key),
            'Mean': fmt_value(stats['mean'], kind),
            'Min': fmt_value(stats['min'], kind),
            'Max': fmt_value(stats['max'], kind),
            'Total': ('—' if is_stock else fmt_value(stats['total'], kind)),
            'Latest': fmt_value(stats['last'], kind),
        })

    return dash_table.DataTable(
        data=rows,
        columns=[{'name': column, 'id': column}
                 for column in ('Metric', 'Mean', 'Min', 'Max', 'Total', 'Latest')],
        style_table=TABLE_STYLE,
        style_header=TABLE_HEADER,
        style_cell=TABLE_CELL,
        style_data_conditional=TABLE_CONDITIONAL,
        cell_selectable=False,
    )


# ---- Audience Heatmap -----------------------------------------------------
_DISPLAY_HINTS = {
    'market': 'One bubble per market, sized by the selected metric and colored by '
              'member share. Click a bubble to drill into that market.',
    'density': 'A continuous surface weighted by the selected metric — no market '
               'boundaries implied. Click a hotspot to drill into it.',
    'individual': 'Every mapped user, colored by lifecycle segment — not a sample. '
                  'Markers are generated deterministically from the market '
                  'aggregates, so the same seed always draws the same cloud. At '
                  'this density a single fan cannot be hovered; use the market or '
                  'density view to drill in.',
}


@callback(
    Output('fr-geo-users-value', 'children'),
    Output('fr-geo-users-delta', 'children'),
    Output('fr-geo-markets-value', 'children'),
    Output('fr-geo-markets-delta', 'children'),
    Output('fr-geo-share-value', 'children'),
    Output('fr-geo-share-delta', 'children'),
    Output('fr-geo-top-value', 'children'),
    Output('fr-geo-top-delta', 'children'),
    Input('fr-client', 'value'),
    Input('fr-loc-level', 'value'),
)
def update_geo_kpis(client, level):
    summary = fig_builders.heatmap_summary(DATASET, client, level)
    return (
        fmt_compact(summary['users']), 'located from app activity',
        group(summary['markets']), f'at {level} level',
        fmt_value(summary['member_share'], 'percent'), 'of mapped users are members',
        summary['top_label'].split(',')[0],
        f"{fmt_compact(summary['top_users'])} users · top 5 hold "
        f"{fmt_value(summary['concentration'], 'percent')}",
    )


@callback(
    Output('fr-map', 'figure'),
    Output('fr-map-hint', 'children'),
    Input('fr-client', 'value'),
    Input('fr-map-display', 'value'),
    Input('fr-map-metric', 'value'),
    Input('fr-loc-level', 'value'),
    Input('fr-segments', 'value'),
)
def update_map(client, display, metric, level, segments):
    figure = fig_builders.heatmap_map(
        DATASET, client, display, metric, level, segments or SEGMENT_NAMES,
    )
    return figure, _DISPLAY_HINTS.get(display, '')


@callback(
    Output('fr-map-metric', 'disabled'),
    Output('fr-segments', 'options'),
    Input('fr-map-display', 'value'),
)
def sync_map_controls(display):
    """Grey out the controls a display mode does not use.

    The individual view has no metric to size by, and the aggregate views have no
    per-user markers to filter — leaving those live would let the viewer change
    something the map ignores.
    """
    individual = display == 'individual'
    options = [{'label': name, 'value': name, 'disabled': not individual}
               for name in SEGMENT_NAMES]
    return individual, options


@callback(
    Output('fr-map-detail', 'children'),
    Input('fr-map', 'clickData'),
    Input('fr-client', 'value'),
    Input('fr-loc-level', 'value'),
    Input('fr-map-display', 'value'),
)
def update_map_detail(click_data, client, level, display):
    if display == 'individual':
        return html.Div(
            'Switch to Market bubbles or Density to drill into a market.',
            className='fr-detail-empty',
        )
    if not click_data or not click_data.get('points'):
        return html.Div('Click a market on the map to break it down.',
                        className='fr-detail-empty')

    payload = click_data['points'][0].get('customdata')
    # Market bubbles carry the market name alone; density points carry
    # [name, users] so their hover can show a count.
    name = payload[0] if isinstance(payload, (list, tuple)) else payload
    detail = fig_builders.location_detail(DATASET, client, level, name)
    if detail is None:
        return html.Div('That market is not in the current selection.',
                        className='fr-detail-empty')

    rows = [
        ('Users', fmt_value(detail['users'])),
        ('Share of audience', fmt_value(detail['share_of_audience'], 'percent')),
        ('Members', f"{fmt_value(detail['members'])} "
                    f"({fmt_value(detail['member_share'], 'percent')})"),
        ('Engagement index', fmt_value(detail['engagement'])),
        ('Engagement per user', group(detail['engagement_per_user'], 2)),
    ]
    return html.Div(
        className='fr-detail-body',
        children=[
            html.Div(detail['label'], className='fr-detail-title'),
            html.Div(
                className='fr-detail-rows',
                children=[
                    html.Div(
                        [html.Span(label, className='fr-detail-label'),
                         html.Span(value, className='fr-detail-value')],
                        className='fr-detail-row',
                    )
                    for label, value in rows
                ],
            ),
            html.Div(
                className='fr-detail-rows',
                children=[
                    html.Div(
                        [html.Span(segment, className='fr-detail-label'),
                         html.Span(fmt_value(count), className='fr-detail-value')],
                        className='fr-detail-row',
                    )
                    for segment, count in detail['segments'].items()
                ],
            ),
        ],
    )


@callback(
    Output('fr-growth', 'figure'),
    Input('fr-client', 'value'),
    Input('fr-loc-level', 'value'),
)
def update_growth(client, level):
    return fig_builders.growth_map(DATASET, client, level)


@callback(
    Output('fr-top-markets', 'children'),
    Input('fr-client', 'value'),
    Input('fr-loc-level', 'value'),
)
def update_top_markets(client, level):
    rows = [
        {
            '#': row['rank'],
            'Market': row['label'],
            'Users': fmt_value(row['users']),
            'Signed-up': fmt_value(row['signed_up']),
            'Members': fmt_value(row['members']),
            'Member share': fmt_value(row['member_share'], 'percent'),
            'Engagement': fmt_value(row['engagement']),
        }
        for row in fig_builders.top_locations(DATASET, client, level)
    ]
    return dash_table.DataTable(
        data=rows,
        columns=[{'name': column, 'id': column} for column in
                 ('#', 'Market', 'Users', 'Signed-up', 'Members', 'Member share', 'Engagement')],
        style_table=TABLE_STYLE,
        style_header=TABLE_HEADER,
        style_cell=TABLE_CELL,
        style_data_conditional=TABLE_CONDITIONAL,
        cell_selectable=False,
    )


@callback(
    Output('fr-segment-mix', 'figure'),
    Output('fr-segment-note', 'children'),
    Input('fr-client', 'value'),
)
def update_segment_mix(client):
    rows = DATASET['clients'][client]['locations']
    totals = {name: sum(r['segments'][name] for r in rows) for name in SEGMENT_NAMES}
    grand = sum(totals.values()) or 1
    member_share = (totals['Member'] + totals['Super User']) / grand * 100
    note = (f'{fmt_value(grand)} mapped users · '
            f'{fmt_value(member_share, "percent")} have converted to a paid membership.')
    return fig_builders.segment_mix(DATASET, client), note


@callback(
    Output('fr-location-bar', 'figure'),
    Input('fr-client', 'value'),
    Input('fr-loc-level', 'value'),
    Input('fr-loc-segment', 'value'),
)
def update_location_bar(client, level, segment):
    return fig_builders.location_bar(DATASET, client, level, segment)


# ---- Behavior -------------------------------------------------------------
@callback(
    Output('fr-scatter', 'figure'),
    Output('fr-scatter-readout', 'children'),
    Input('fr-client', 'value'),
    Input('fr-preset', 'value'),
    Input('fr-x-metric', 'value'),
    Input('fr-y-metric', 'value'),
)
def update_scatter(client, preset, x_metric, y_metric):
    lo, hi = _window(preset)
    figure = fig_builders.relationship_scatter(DATASET, client, lo, hi, x_metric, y_metric)

    series = _series(client)
    xs, ys = series[x_metric][lo:hi], series[y_metric][lo:hi]
    from demo_dashboard.data import linear_fit

    slope, _, r2 = linear_fit(list(xs), list(ys))
    if r2 >= 0.5:
        strength = 'strong co-movement'
    elif r2 >= 0.2:
        strength = 'moderate co-movement'
    else:
        strength = 'weak or no linear relationship'
    readout = (
        f'R² = {group(r2, 2)} — {strength}. A one-unit rise in {metric_label(x_metric)} '
        f'is associated with {"+" if slope >= 0 else ""}{group(slope, 3)} '
        f'in {metric_label(y_metric)} across {hi - lo} days.'
    )
    return figure, readout


@callback(
    Output('fr-correlation', 'figure'),
    Input('fr-client', 'value'),
    Input('fr-preset', 'value'),
)
def update_correlation(client, preset):
    lo, hi = _window(preset)
    return fig_builders.correlation_heatmap(DATASET, client, lo, hi)


@callback(
    Output('fr-engagement', 'figure'),
    Input('fr-client', 'value'),
    Input('fr-preset', 'value'),
)
def update_engagement(client, preset):
    lo, hi = _window(preset)
    grain = 'Daily' if hi - lo <= 95 else 'Weekly'
    return fig_builders.engagement_trend(DATASET, client, lo, hi, grain)


# ---- Revenue & Retention --------------------------------------------------
@callback(
    Output('fr-rev-total-value', 'children'),
    Output('fr-rev-total-delta', 'children'),
    Output('fr-rev-total-delta', 'className'),
    Output('fr-rev-arpm-value', 'children'),
    Output('fr-rev-arpm-delta', 'children'),
    Output('fr-rev-arpm-delta', 'className'),
    Output('fr-rev-churn-value', 'children'),
    Output('fr-rev-churn-delta', 'children'),
    Output('fr-rev-churn-delta', 'className'),
    Output('fr-rev-tenure-value', 'children'),
    Output('fr-rev-tenure-delta', 'children'),
    Output('fr-rev-tenure-delta', 'className'),
    Input('fr-client', 'value'),
    Input('fr-preset', 'value'),
)
def update_revenue_kpis(client, preset):
    lo, hi = _window(preset)
    bundle = DATASET['clients'][client]
    series = bundle['series']

    revenue = summarize(series['revenue'][lo:hi])['total']
    rev_text, rev_dir = _delta_chip(delta_pct(series['revenue'][lo:hi]))

    members = summarize(series['memberships'][lo:hi])['mean'] or 1
    days = max(hi - lo, 1)
    arpm = revenue / members / days * 30.44

    churn_rows = [r for r in bundle['churn'] if r['start'] > 50]
    if churn_rows:
        latest = churn_rows[-1]
        churn_value = fmt_value(latest['churn_pct'], 'percent')
        churn_note = (f"{group(latest['lost'])} of {group(latest['start'])} members "
                      f"in {latest['period']}")
        prior = churn_rows[-2]['churn_pct'] if len(churn_rows) > 1 else latest['churn_pct']
        churn_dir = 'down' if latest['churn_pct'] < prior else (
            'up' if latest['churn_pct'] > prior else 'flat')
        # Falling churn is good news, so the chip color is inverted here.
        churn_dir = {'down': 'up', 'up': 'down', 'flat': 'flat'}[churn_dir]
    else:
        churn_value, churn_note, churn_dir = '—', 'not enough history', 'flat'

    lifetime = bundle['lifetime']
    tenure_value = f"{group(lifetime['median_days'])} days"
    tenure_note = (f"mean {group(lifetime['mean_days'])} days · "
                   f"{group(lifetime['active_members'])} members")

    return (
        fmt_compact(revenue, 'money'), rev_text, f'fr-tile-delta fr-tile-delta--{rev_dir}',
        f'${group(arpm, 2)}', 'per member per 30 days', 'fr-tile-delta fr-tile-delta--flat',
        churn_value, churn_note, f'fr-tile-delta fr-tile-delta--{churn_dir}',
        tenure_value, tenure_note, 'fr-tile-delta fr-tile-delta--flat',
    )


@callback(
    Output('fr-revenue', 'figure'),
    Input('fr-client', 'value'),
    Input('fr-preset', 'value'),
    Input('fr-rev-grain', 'value'),
)
def update_revenue(client, preset, grain):
    lo, hi = _window(preset)
    return fig_builders.revenue_trend(DATASET, client, lo, hi, grain)


@callback(
    Output('fr-mix-type', 'figure'),
    Output('fr-mix-platform', 'figure'),
    Input('fr-client', 'value'),
)
def update_revenue_mix(client):
    return (
        fig_builders.revenue_mix_donut(DATASET, client, 'revenue_type'),
        fig_builders.revenue_mix_donut(DATASET, client, 'platform'),
    )


@callback(
    Output('fr-churn', 'figure'),
    Input('fr-churn-clients', 'value'),
)
def update_churn(clients):
    return fig_builders.churn_lines(DATASET, clients or [])


@callback(
    Output('fr-lifetime', 'figure'),
    Input('fr-client', 'value'),
)
def update_lifetime(client):
    return fig_builders.lifetime_bars(DATASET, client)


@callback(
    Output('fr-top-users', 'children'),
    Input('fr-client', 'value'),
)
def update_top_users(client):
    records = DATASET['clients'][client]['top_users'][:12]
    show_account = any('client' in record for record in records)

    rows = []
    for record in records:
        row = {
            '#': record['rank'],
            'Fan': f"@{record['handle']}",
            'Tier': record['membership'],
            'Location': record['city'],
            'Sessions': f"{record['sessions']:,}",
            'Time in app': f"{record['minutes'] / 60:,.0f} h",
            'Posts': f"{record['posts']:,}",
            'Spend': f"${record['spend']:,.0f}",
        }
        if show_account:
            row['Account'] = record.get('client', client)
        rows.append(row)

    columns = ['#', 'Fan', 'Tier', 'Location', 'Sessions', 'Time in app', 'Posts', 'Spend']
    if show_account:
        columns.insert(2, 'Account')

    return dash_table.DataTable(
        data=rows,
        columns=[{'name': column, 'id': column} for column in columns],
        style_table=TABLE_STYLE,
        style_header=TABLE_HEADER,
        style_cell=TABLE_CELL,
        style_data_conditional=TABLE_CONDITIONAL,
        cell_selectable=False,
    )
