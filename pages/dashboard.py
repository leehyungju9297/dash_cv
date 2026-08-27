"""Live demo: the Tidepool Commerce Analytics dashboard.

A multi-brand direct-to-consumer retail analytics surface, fully wired, running
on a deterministic synthetic dataset (see :mod:`demo_dashboard.data`). Sales
performance, revenue drivers and category mix; cohort retention and customer
value; channel attribution and promotion lift; fulfillment geography and returns.

Two structural decisions worth naming:

* **Every view stays mounted and is toggled with a class.** Tearing a view down
  when its tab is hidden would tear its callbacks down with it, so every control
  would lose its state on the way back. Nine hidden ``div``s cost nothing; nine
  re-initialised control groups cost the reader their place.

* **Figures are built in :mod:`demo_dashboard.figures`, never here.** This module
  is layout and wiring. That is what lets the static twin mirror one file instead
  of reimplementing the page.
"""

import dash
from dash import ALL, Input, Output, State, callback, ctx, dash_table, dcc, html

from demo_dashboard.config import (
    AXIS_METRICS,
    BRAND,
    BRAND_MARK,
    BRAND_TAGLINE,
    BRANDS,
    DATE_PRESETS,
    DEFAULT_BRAND,
    DEFAULT_PRESET,
    DEFAULT_VIEW,
    SECTIONS,
    SECTION_OF_VIEW,
    VIEW_KEYS,
    VIEWS_OF_SECTION,
    metric_label,
)
from demo_dashboard.data import EVENT_ORDER, get_dataset, window_indices
from demo_dashboard import figures as fig_builders
from demo_dashboard.figures import CHART_HEIGHTS, MAP_DISPLAYS, group


dash.register_page(
    __name__,
    path='/dashboard',
    order=2,
    name='Live Demo',
    title=f'Live Demo | {BRAND}',
)


DATASET = get_dataset()
PRESET_DAYS = dict(DATE_PRESETS)

GRAPH_CONFIG = {'displayModeBar': False, 'showTips': False, 'responsive': True}

METRIC_OPTIONS = [{'label': metric_label(key), 'value': key} for key in AXIS_METRICS]
GRAIN_OPTIONS = [{'label': label, 'value': value} for label, value in
                 (('Daily', 'daily'), ('Weekly', 'weekly'),
                  ('Monthly', 'monthly'), ('Quarterly', 'quarterly'))]
DISPLAY_OPTIONS = [{'label': label, 'value': value} for value, label in MAP_DISPLAYS]
LEVEL_OPTIONS = [{'label': label, 'value': value} for value, label in
                 (('city', 'City'), ('region', 'State / Region'), ('country', 'Country'))]
STUDY_METRIC_OPTIONS = [{'label': metric_label(key), 'value': key} for key in
                        ('revenue', 'orders', 'visits', 'conversion', 'aov')]

GROWTH_MONTHS = fig_builders.growth_timeline(DATASET, DEFAULT_BRAND)
GROWTH_MARKS = {
    index: {'label': month if index % 6 == 0 or index == len(GROWTH_MONTHS) - 1 else ''}
    for index, month in enumerate(GROWTH_MONTHS)
}

TABLE_HEADER = {
    'backgroundColor': 'transparent',
    'border': 'none',
    'borderBottom': '1px solid #E7E5E4',
    'color': '#78716C',
    'fontSize': '11px',
    'fontWeight': '600',
    'letterSpacing': '0.06em',
    'textTransform': 'uppercase',
    'padding': '10px 12px',
}
TABLE_CELL = {
    'backgroundColor': 'transparent',
    'border': 'none',
    'borderBottom': '1px solid rgba(28, 25, 23, 0.06)',
    'color': '#1C1917',
    'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    'fontSize': '12.5px',
    'padding': '9px 12px',
    'textAlign': 'right',
}


# --------------------------------------------------------------------------
# Layout helpers
# --------------------------------------------------------------------------
def _card(*children, title=None, subtitle=None, className=''):
    body = list(children)
    if title:
        # h2: the page title above is the h1, and there is no level between
        # them — a card title is the page's first subdivision.
        header = [html.H2(title, className='tp-card-title')]
        if subtitle:
            header.append(html.P(subtitle, className='tp-card-subtitle'))
        body = [html.Div(header, className='tp-card-header'), *body]
    return html.Div(body, className=f'tp-card {className}'.strip())


def _control(label, control, grow=False):
    return html.Div(
        [html.Label(label, className='tp-control-label'), control],
        className='tp-control' + (' tp-control--grow' if grow else ''),
    )


def _graph(graph_id, chart):
    """A graph whose container is pinned to the same height its figure uses.

    dcc.Graph runs with ``responsive: true``; without a CSS height, a width
    change collapses the container to zero while the figure keeps its own
    height, and the SVG then paints over the card below it. Reading the number
    from ``CHART_HEIGHTS`` keeps the two from drifting apart.
    """
    return dcc.Graph(id=graph_id, config=GRAPH_CONFIG,
                     style={'height': f'{CHART_HEIGHTS[chart]}px'})


def _stat_blocks(block_id):
    """A row of plain bordered stat blocks, filled by callback."""
    return html.Div(id=block_id, className='tp-stats')


def _render_stats(rows):
    return [
        html.Div(
            [
                html.Div(row['label'], className='tp-stat-label'),
                html.Div(row['value'], className='tp-stat-value'),
                html.Div(row.get('note', ''), className='tp-stat-note'),
            ],
            className='tp-stat',
        )
        for row in rows
    ]


def _delta_chip(value, comparison):
    """Direction and magnitude for a headline number."""
    if abs(value) < 0.05:
        return f'no change {comparison}', 'flat'
    arrow = '▲' if value > 0 else '▼'
    return f'{arrow} {group(abs(value), 1)}% {comparison}', 'up' if value > 0 else 'down'


def _panel(view_key, *children):
    return html.Section(
        list(children),
        id=f'tp-panel-{view_key}',
        className='tp-panel tp-panel--hidden',
    )


# --------------------------------------------------------------------------
# Shell
# --------------------------------------------------------------------------
topbar = html.Div(
    className='tp-topbar',
    children=[
        html.Div(
            [
                html.Div(BRAND_MARK, className='tp-brand-mark'),
                html.Div(
                    [
                        html.Div(BRAND, className='tp-brand-name'),
                        html.Div(BRAND_TAGLINE, className='tp-brand-tagline'),
                    ]
                ),
            ],
            className='tp-brand',
        ),
        html.Div(
            className='tp-topbar-controls',
            children=[
                _control('Brand', dcc.Dropdown(
                    id='tp-brand',
                    options=[{'label': name, 'value': name} for name in BRANDS],
                    value=DEFAULT_BRAND, clearable=False, searchable=False,
                    className='tp-dropdown')),
                _control('Date window', dcc.RadioItems(
                    id='tp-preset',
                    options=[{'label': label, 'value': label} for label, _ in DATE_PRESETS],
                    value=DEFAULT_PRESET, className='tp-segmented',
                    inputClassName='tp-segmented-input',
                    labelClassName='tp-segmented-label')),
            ],
        ),
    ],
)

tabs = html.Nav(
    className='tp-tabs',
    children=[
        html.Button(
            section['label'],
            id={'type': 'tp-section', 'section': section['key']},
            className='tp-tab', n_clicks=0,
        )
        for section in SECTIONS
    ],
)

subtabs = html.Nav(id='tp-subtabs', className='tp-subtabs')

kpi_strip = html.Div(id='tp-kpis', className='tp-kpis')


# --------------------------------------------------------------------------
# Sales Performance — Revenue & Orders
# --------------------------------------------------------------------------
panel_revenue = _panel(
    'revenue',
    _card(
        html.Div(
            className='tp-controls',
            children=[
                _control('Left axis', dcc.Dropdown(
                    id='tp-trend-left', options=METRIC_OPTIONS, value='revenue',
                    clearable=False, searchable=False, className='tp-dropdown')),
                _control('Right axis', dcc.Dropdown(
                    id='tp-trend-right', options=METRIC_OPTIONS, value='orders',
                    clearable=False, searchable=False, className='tp-dropdown')),
                _control('Interval', dcc.Dropdown(
                    id='tp-trend-grain', options=GRAIN_OPTIONS, value='daily',
                    clearable=False, searchable=False, className='tp-dropdown')),
                _control('Annotate', dcc.Checklist(
                    id='tp-trend-marks',
                    options=[
                        {'label': 'Promotion calendar', 'value': 'events'},
                        {'label': 'Outliers', 'value': 'anomalies'},
                    ],
                    value=['events', 'anomalies'], className='tp-checklist',
                    inputClassName='tp-checkbox', labelClassName='tp-checklabel')),
            ],
        ),
        _graph('tp-trend', 'trend'),
        title='Trading Performance',
        subtitle=('Two metrics on independent axes with the promotion calendar '
                  'overlaid, and outliers marked in place — so a spike can be '
                  'read against what ran that week.'),
    ),
    _card(
        html.Div(id='tp-anomaly-log', className='tp-log'),
        title='Detected Anomalies',
        subtitle=('Days that sit far from their own trailing level, in robust z '
                  'units. Median and MAD rather than mean and standard deviation, '
                  'so one large spike does not raise the bar past every other one.'),
    ),
)


# --------------------------------------------------------------------------
# Sales Performance — Revenue Drivers
# --------------------------------------------------------------------------
panel_drivers = _panel(
    'drivers',
    _card(
        html.Div(id='tp-driver-note', className='tp-callout'),
        _graph('tp-driver', 'driver'),
        title='What Moved Revenue',
        subtitle=('Revenue is exactly site visits x conversion rate x average '
                  'order value, so the change against the prior period splits by '
                  'substituting one factor at a time. The bars sum to the total '
                  'with no residual.'),
    ),
    _card(
        _graph('tp-splom', 'splom'),
        title='How the Metrics Move Together',
        subtitle=('Every pair of core metrics, coloured by position in the '
                  'window. A widening cone means the spread grows with the '
                  'level, a hook means saturation, and a detached cluster is '
                  'usually the promotion calendar.'),
    ),
)


# --------------------------------------------------------------------------
# Sales Performance — Category Mix
# --------------------------------------------------------------------------
panel_category = _panel(
    'category',
    _card(
        _graph('tp-category-waterfall', 'category_waterfall'),
        title='Category Contribution to the Change',
        subtitle=('Which parts of the catalogue carried the revenue change '
                  'against the prior period, largest mover first.'),
    ),
    _card(
        html.Div(
            className='tp-controls',
            children=[
                _control('Measure', dcc.RadioItems(
                    id='tp-category-mode',
                    options=[{'label': 'Share of revenue', 'value': 'share'},
                             {'label': 'Revenue', 'value': 'absolute'}],
                    value='share', className='tp-segmented',
                    inputClassName='tp-segmented-input',
                    labelClassName='tp-segmented-label')),
            ],
        ),
        _graph('tp-category-share', 'category_share'),
        title='Category Mix Over Time',
        subtitle='How the catalogue has rebalanced month by month.',
    ),
)


# --------------------------------------------------------------------------
# Customers — Cohort Retention
# --------------------------------------------------------------------------
panel_cohorts = _panel(
    'cohorts',
    _card(
        _stat_blocks('tp-cohort-stats'),
        _graph('tp-cohort', 'cohort'),
        title='Cohort Retention',
        subtitle=('Share of each acquisition month that ordered again, by months '
                  'since their first order. A triangle rather than a rectangle: a '
                  'cohort acquired last month has one observed month, and the '
                  'unobserved cells stay blank instead of being filled with zero.'),
    ),
    _card(
        _graph('tp-cohort-curves', 'cohort_curves'),
        title='Retention Curves',
        subtitle=('The same data read as curves. Recent cohorts are drawn '
                  'darkest, so a change in the shape of the acquisition base '
                  'shows without reading numbers out of cells.'),
    ),
)


# --------------------------------------------------------------------------
# Customers — Customer Value
# --------------------------------------------------------------------------
panel_value = _panel(
    'value',
    _card(
        _stat_blocks('tp-value-stats'),
        _graph('tp-rfm', 'rfm'),
        title='Recency, Frequency and Spend',
        subtitle=('One point per customer: how long since their last order, how '
                  'many they have placed, and — as marker area — what they have '
                  'spent. The four quadrants are labelled because that is the '
                  'part anyone acts on.'),
    ),
    _card(
        _graph('tp-decile', 'decile'),
        title='Revenue Concentration',
        subtitle=('Share of revenue by customer spend decile, with the '
                  'cumulative curve. A mean spend figure hides this entirely.'),
    ),
)


# --------------------------------------------------------------------------
# Marketing — Channel Attribution
# --------------------------------------------------------------------------
panel_channels = _panel(
    'channels',
    _card(
        html.Div(
            className='tp-controls',
            children=[
                _control('Measure', dcc.RadioItems(
                    id='tp-channel-mode',
                    options=[{'label': 'Revenue', 'value': 'absolute'},
                             {'label': 'Share', 'value': 'share'}],
                    value='absolute', className='tp-segmented',
                    inputClassName='tp-segmented-input',
                    labelClassName='tp-segmented-label')),
            ],
        ),
        _graph('tp-channel-area', 'channel_area'),
        title='Where Orders Are Placed',
        subtitle='Revenue by order channel, month by month.',
    ),
    _card(
        _graph('tp-source-bars', 'source_bars'),
        title='Acquisition Source Value',
        subtitle=('First-order and repeat revenue stacked separately, with '
                  'acquisition spend marked. A source that looks expensive on '
                  'first orders alone can be the best one in the portfolio once '
                  'its customers come back.'),
    ),
    _card(
        html.Div(id='tp-source-table', className='tp-table'),
        title='Attribution Detail',
        subtitle='Customers acquired, what they returned, and what they cost.',
    ),
)


# --------------------------------------------------------------------------
# Marketing — Promotion Lift
# --------------------------------------------------------------------------
panel_promotions = _panel(
    'promotions',
    _card(
        _stat_blocks('tp-promo-stats'),
        html.Div(
            className='tp-controls',
            children=[
                _control('Response metric', dcc.Dropdown(
                    id='tp-study-metric', options=STUDY_METRIC_OPTIONS,
                    value='revenue', clearable=False, searchable=False,
                    className='tp-dropdown')),
                _control('Promotion types', dcc.Dropdown(
                    id='tp-study-kinds',
                    options=[{'label': kind, 'value': kind} for kind in EVENT_ORDER],
                    value=[], multi=True, placeholder='All types',
                    className='tp-dropdown'), grow=True),
            ],
        ),
        _graph('tp-event-study', 'event_study'),
        title='Event Study',
        subtitle=('Every occurrence of a promotion type aligned on the day it ran '
                  'and indexed to the day before, so the answer is a shape: '
                  'whether the lift is instant or builds, whether it decays back '
                  'to baseline or leaves a step, and whether the days before show '
                  'pull-forward. The band is a 95% interval across occurrences.'),
    ),
    _card(
        _graph('tp-promo-bars', 'promo_bars'),
        title='Promoted Days Against Baseline',
        subtitle=('Promoted days compared with the non-promoted days of the same '
                  'window. Measured against an annual average, a November '
                  'promotion would be credited with November.'),
    ),
    _card(
        _graph('tp-discount', 'discount'),
        title='Discount Codes',
        subtitle='Revenue kept against the discount given back, by code.',
    ),
)


# --------------------------------------------------------------------------
# Operations — Fulfillment & Regions
# --------------------------------------------------------------------------
panel_fulfillment = _panel(
    'fulfillment',
    _card(
        _stat_blocks('tp-geo-stats'),
        html.Div(
            className='tp-controls',
            children=[
                _control('Display', dcc.Dropdown(
                    id='tp-map-display', options=DISPLAY_OPTIONS, value='market',
                    clearable=False, searchable=False, className='tp-dropdown')),
                _control('Level', dcc.Dropdown(
                    id='tp-map-level', options=LEVEL_OPTIONS, value='city',
                    clearable=False, searchable=False, className='tp-dropdown')),
                html.Div(id='tp-map-hint', className='tp-hint'),
            ],
        ),
        _graph('tp-map', 'map'),
        title='Where Orders Ship',
        subtitle=('Bubble size is order volume and colour is average order value, '
                  'so a market that is large and cheap reads differently from one '
                  'that is small and rich.'),
    ),
    _card(
        html.Div(
            className='tp-playback',
            children=[
                html.Button('▶  Play', id='tp-growth-play', n_clicks=0,
                            className='tp-play-button'),
                dcc.Slider(id='tp-growth-month', min=0, max=len(GROWTH_MONTHS) - 1,
                           step=1, value=len(GROWTH_MONTHS) - 1, marks=GROWTH_MARKS,
                           included=True, updatemode='drag', className='tp-scrub'),
            ],
        ),
        html.Div(id='tp-growth-readout', className='tp-readout'),
        _graph('tp-growth', 'growth_map'),
        dcc.Interval(id='tp-growth-timer', interval=420, disabled=True),
        title='Order Footprint by Month',
        subtitle=('Every order placed up to the end of the selected month, one '
                  'marker each. Individual orders rather than market bubbles: '
                  'resizing blobs shows a market growing, but only points can '
                  'show the footprint spreading into new ground.'),
    ),
    _card(
        _graph('tp-market-bars', 'market_bars'),
        title='Largest Markets',
        subtitle='Ordered by volume, coloured by average order value.',
    ),
)


# --------------------------------------------------------------------------
# Operations — Returns
# --------------------------------------------------------------------------
panel_returns = _panel(
    'returns',
    _card(
        _stat_blocks('tp-return-stats'),
        html.Div(
            className='tp-controls',
            children=[
                _control('Interval', dcc.Dropdown(
                    id='tp-return-grain', options=GRAIN_OPTIONS[1:], value='weekly',
                    clearable=False, searchable=False, className='tp-dropdown')),
            ],
        ),
        _graph('tp-return-trend', 'return_trend'),
        title='Returns Over Time',
        subtitle=('Counts as bars, rate as a line. The rate is summed returns '
                  'over summed orders per bucket — averaging daily rates would '
                  'let a quiet Tuesday outvote a sale week.'),
    ),
    _card(
        _graph('tp-return-category', 'return_category'),
        title='Return Rate by Category',
        subtitle='Where the returns concentrate, and what value is at stake.',
    ),
    _card(
        _graph('tp-return-reason', 'return_reason'),
        title='Why Orders Come Back',
        subtitle='Returned value by stated reason.',
    ),
)


PANELS = {
    'revenue': panel_revenue,
    'drivers': panel_drivers,
    'category': panel_category,
    'cohorts': panel_cohorts,
    'value': panel_value,
    'channels': panel_channels,
    'promotions': panel_promotions,
    'fulfillment': panel_fulfillment,
    'returns': panel_returns,
}


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
SPEC_ROWS = (
    ('Built with', 'JavaScript and plotly.js'),
    ('Also implemented as', 'Dash app (Python)'),
    ('Experience', 'React · TypeScript · FastAPI · deck.gl'),
    ('Dataset', '730 days · 5 brands · 3 rollups · seeded'),
    ('Functions', ' · '.join(section['label'] for section in SECTIONS)),
)

layout = html.Div(
    className='content-stack tp-page',
    children=[
        html.Header(
            className='section-hero tp-hero',
            children=[
                html.Div(
                    [
                        html.P('LIVE DEMO', className='section-hero-eyebrow'),
                        # Two lines by construction rather than by luck: the
                        # em dash left the title breaking wherever the column
                        # happened to end, which at this width was after
                        # "Retail". The name is one line, what it is is the
                        # next.
                        html.H1(
                            className='section-hero-title',
                            children=[
                                # The space is for the accessible name: the
                                # span is a block, so it prints nothing, but
                                # without it a screen reader says
                                # "AnalyticsRetail".
                                BRAND + ' ',
                                html.Span('Retail Dashboard',
                                          className='tp-hero-title-kind'),
                            ],
                        ),
                        html.P(
                            'A multi-brand direct-to-consumer analytics surface: '
                            'trading performance and revenue drivers, cohort '
                            'retention and customer value, channel attribution and '
                            'promotion lift, fulfillment geography and returns. '
                            'Every control is live.',
                            className='section-hero-lede',
                        ),
                    ],
                    className='tp-hero-copy',
                ),
                html.Dl(
                    className='tp-spec',
                    children=[
                        item for label, value in SPEC_ROWS
                        for item in (html.Dt(label, className='tp-spec-label'),
                                     html.Dd(value, className='tp-spec-value'))
                    ],
                ),
            ],
        ),
        # The notice reads as a label and its statement, not as a paragraph
        # that happens to start with a bold word. The label takes a fifth of
        # the measure and the text takes the rest, so a full-width block is
        # actually using its width.
        html.Aside(
            className='tp-disclaimer',
            children=[
                html.Div('Synthetic data', className='tp-disclaimer-tag'),
                html.Div(
                    className='tp-disclaimer-body',
                    children=[
                        html.P(
                            'Every brand, customer, order, and figure is '
                            'generated. No real customer or commercial data '
                            'appears anywhere.',
                            className='tp-disclaimer-line',
                        ),
                        html.P(
                            'Built as a self-contained demonstration of the '
                            'analytical workflow across retention, revenue, '
                            'customer, and channel analytics.',
                            className='tp-disclaimer-note',
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            className='tp-shell',
            children=[
                topbar,
                tabs,
                subtabs,
                kpi_strip,
                html.Main(list(PANELS.values()), className='tp-views'),
            ],
        ),
        dcc.Store(id='tp-view', data=DEFAULT_VIEW),
    ],
)


# ==========================================================================
# Navigation
# ==========================================================================
@callback(
    Output('tp-view', 'data'),
    Input({'type': 'tp-section', 'section': ALL}, 'n_clicks'),
    Input({'type': 'tp-view-tab', 'view': ALL}, 'n_clicks'),
    State('tp-view', 'data'),
    prevent_initial_call=True,
)
def switch_view(_section_clicks, _view_clicks, current):
    """Clicking a function tab lands on that function's first view."""
    trigger = ctx.triggered_id
    if not isinstance(trigger, dict):
        return current
    if trigger.get('type') == 'tp-section':
        views = VIEWS_OF_SECTION.get(trigger['section'], [])
        return views[0] if views else current
    return trigger.get('view', current)


@callback(
    Output('tp-subtabs', 'children'),
    [Output({'type': 'tp-section', 'section': section['key']}, 'className')
     for section in SECTIONS],
    Input('tp-view', 'data'),
)
def render_navigation(view):
    """The view row under the tabs, plus the active state on the tabs."""
    active_section = SECTION_OF_VIEW.get(view, SECTIONS[0]['key'])
    section = next(s for s in SECTIONS if s['key'] == active_section)

    children = [
        html.Button(
            [
                html.Span(item['label'], className='tp-subtab-label'),
                html.Span(item['blurb'], className='tp-subtab-blurb'),
            ],
            id={'type': 'tp-view-tab', 'view': item['key']},
            n_clicks=0,
            className='tp-subtab' + (' tp-subtab--active' if item['key'] == view else ''),
        )
        for item in section['views']
    ]
    classes = ['tp-tab' + (' tp-tab--active' if s['key'] == active_section else '')
               for s in SECTIONS]
    return [children, *classes]


@callback(
    [Output(f'tp-panel-{key}', 'className') for key in VIEW_KEYS],
    Input('tp-view', 'data'),
)
def toggle_panels(view):
    return ['tp-panel' if key == view else 'tp-panel tp-panel--hidden'
            for key in VIEW_KEYS]


def _window(preset):
    return window_indices(DATASET['dates'], PRESET_DAYS.get(preset, 365))


# ==========================================================================
# Headline strip
# ==========================================================================
@callback(
    Output('tp-kpis', 'children'),
    Input('tp-brand', 'value'),
    Input('tp-preset', 'value'),
)
def update_kpis(brand, preset):
    lo, hi = _window(preset)
    comparison = fig_builders.comparison_label(lo, hi)
    children = []
    for tile in fig_builders.kpi_tiles(DATASET, brand, lo, hi):
        text, tone = _delta_chip(tile['delta'], comparison)
        children.append(html.Div(
            [
                html.Div(tile['label'], className='tp-kpi-label'),
                html.Div(tile['value'], className='tp-kpi-value'),
                html.Div(text, className=f'tp-kpi-delta tp-kpi-delta--{tone}'),
            ],
            className='tp-kpi',
        ))
    return children


# ==========================================================================
# Sales Performance
# ==========================================================================
@callback(
    Output('tp-trend', 'figure'),
    Input('tp-brand', 'value'), Input('tp-preset', 'value'),
    Input('tp-trend-left', 'value'), Input('tp-trend-right', 'value'),
    Input('tp-trend-grain', 'value'), Input('tp-trend-marks', 'value'),
)
def update_trend(brand, preset, left, right, grain, marks):
    lo, hi = _window(preset)
    marks = marks or []
    return fig_builders.trend_figure(
        DATASET, brand, lo, hi, left, right, grain,
        overlay='events' in marks, mark_anomalies='anomalies' in marks)


@callback(
    Output('tp-anomaly-log', 'children'),
    Input('tp-brand', 'value'), Input('tp-preset', 'value'),
)
def update_anomaly_log(brand, preset):
    lo, hi = _window(preset)
    rows, total = fig_builders.anomaly_log(DATASET, brand, lo, hi)
    if not rows:
        return html.P('Nothing in this window sits far enough from its own '
                      'trailing level to flag.', className='tp-empty')

    items = []
    for row in rows:
        tone = 'up' if row['direction'] == 'high' else 'down'
        context = (f" · alongside {row['context']}" if row['context']
                   else ' · no promotion within three days')
        items.append(html.Li(
            [
                html.Div(
                    [
                        html.Span(row['date'], className='tp-log-date'),
                        html.Span(row['metric'], className='tp-log-metric'),
                    ],
                    className='tp-log-head',
                ),
                html.Div(
                    [
                        html.Span(row['value'], className='tp-log-value'),
                        html.Span(f" against a {row['baseline']} baseline",
                                  className='tp-log-baseline'),
                    ],
                    className='tp-log-body',
                ),
                html.Div(
                    [
                        html.Span(
                            ('+' if row['pct'] >= 0 else '') + group(row['pct'], 1) + '%',
                            className=f'tp-log-delta tp-log-delta--{tone}'),
                        html.Span(f"{row['z']:+.1f} robust z{context}",
                                  className='tp-log-note'),
                    ],
                    className='tp-log-foot',
                ),
            ],
            className='tp-log-item',
        ))

    body = [html.Ol(items, className='tp-log-list')]
    if total > len(rows):
        body.append(html.P(f'Showing the {len(rows)} largest of {total} flagged '
                           f'points across five metrics.', className='tp-log-footer'))
    return body


@callback(
    Output('tp-driver', 'figure'),
    Output('tp-driver-note', 'children'),
    Input('tp-brand', 'value'), Input('tp-preset', 'value'),
)
def update_drivers(brand, preset):
    lo, hi = _window(preset)
    summary = fig_builders.driver_summary(DATASET, brand, lo, hi)
    note = summary['text'] if summary else 'Not enough history for a prior period.'
    return fig_builders.driver_waterfall(DATASET, brand, lo, hi), note


@callback(
    Output('tp-splom', 'figure'),
    Input('tp-brand', 'value'), Input('tp-preset', 'value'),
)
def update_splom(brand, preset):
    lo, hi = _window(preset)
    return fig_builders.metric_splom(DATASET, brand, lo, hi)


@callback(
    Output('tp-category-waterfall', 'figure'),
    Input('tp-brand', 'value'), Input('tp-preset', 'value'),
)
def update_category_waterfall(brand, preset):
    lo, hi = _window(preset)
    return fig_builders.category_waterfall(DATASET, brand, lo, hi)


@callback(
    Output('tp-category-share', 'figure'),
    Input('tp-brand', 'value'), Input('tp-category-mode', 'value'),
)
def update_category_share(brand, mode):
    return fig_builders.category_share_area(DATASET, brand, normalise=(mode == 'share'))


# ==========================================================================
# Customers
# ==========================================================================
@callback(
    Output('tp-cohort', 'figure'),
    Output('tp-cohort-curves', 'figure'),
    Output('tp-cohort-stats', 'children'),
    Input('tp-brand', 'value'),
)
def update_cohorts(brand):
    return (fig_builders.cohort_triangle(DATASET, brand),
            fig_builders.cohort_curves(DATASET, brand),
            _render_stats(fig_builders.cohort_summary(DATASET, brand)))


@callback(
    Output('tp-rfm', 'figure'),
    Output('tp-decile', 'figure'),
    Output('tp-value-stats', 'children'),
    Input('tp-brand', 'value'),
)
def update_value(brand):
    return (fig_builders.rfm_scatter(DATASET, brand),
            fig_builders.value_decile_bars(DATASET, brand),
            _render_stats(fig_builders.value_summary(DATASET, brand)))


# ==========================================================================
# Marketing
# ==========================================================================
@callback(
    Output('tp-channel-area', 'figure'),
    Input('tp-brand', 'value'), Input('tp-channel-mode', 'value'),
)
def update_channel_area(brand, mode):
    return fig_builders.channel_area(DATASET, brand, normalise=(mode == 'share'))


@callback(
    Output('tp-source-bars', 'figure'),
    Output('tp-source-table', 'children'),
    Input('tp-brand', 'value'),
)
def update_sources(brand):
    rows = fig_builders.source_table(DATASET, brand)
    columns = list(rows[0].keys()) if rows else []
    table = dash_table.DataTable(
        data=rows,
        columns=[{'name': name, 'id': name} for name in columns],
        style_as_list_view=True,
        style_table={'overflowX': 'auto'},
        style_header=TABLE_HEADER,
        style_cell=TABLE_CELL,
        style_cell_conditional=[{'if': {'column_id': 'Source'}, 'textAlign': 'left'}],
    )
    return fig_builders.source_bars(DATASET, brand), table


@callback(
    Output('tp-event-study', 'figure'),
    Input('tp-brand', 'value'), Input('tp-study-metric', 'value'),
    Input('tp-study-kinds', 'value'),
)
def update_event_study(brand, metric, kinds):
    return fig_builders.event_study_chart(DATASET, brand, metric, kinds or ())


@callback(
    Output('tp-promo-bars', 'figure'),
    Output('tp-discount', 'figure'),
    Output('tp-promo-stats', 'children'),
    Input('tp-brand', 'value'), Input('tp-preset', 'value'),
)
def update_promotions(brand, preset):
    lo, hi = _window(preset)
    return (fig_builders.promotion_lift_bars(DATASET, brand, lo, hi),
            fig_builders.discount_bars(DATASET, brand),
            _render_stats(fig_builders.promotion_summary(DATASET, brand, lo, hi)))


# ==========================================================================
# Operations
# ==========================================================================
_DISPLAY_HINTS = {
    'market': 'One bubble per market, sized by orders and coloured by average '
              'order value.',
    'orders': 'One marker per order, banded by order value.',
    'density': 'Market boundaries dropped, so only where orders concentrate '
               'remains.',
}


@callback(
    Output('tp-map', 'figure'),
    Output('tp-map-hint', 'children'),
    Output('tp-geo-stats', 'children'),
    Output('tp-market-bars', 'figure'),
    Input('tp-brand', 'value'), Input('tp-map-display', 'value'),
    Input('tp-map-level', 'value'),
)
def update_map(brand, display, level):
    return (fig_builders.fulfillment_map(DATASET, brand, level, display),
            _DISPLAY_HINTS.get(display, ''),
            _render_stats(fig_builders.fulfillment_summary(DATASET, brand, level)),
            fig_builders.market_bars(DATASET, brand, level))


@callback(
    Output('tp-growth-timer', 'disabled'),
    Output('tp-growth-play', 'children'),
    Input('tp-growth-play', 'n_clicks'),
)
def toggle_growth_playback(clicks):
    playing = bool(clicks) and clicks % 2 == 1
    return (not playing), ('❚❚  Pause' if playing else '▶  Play')


@callback(
    Output('tp-growth-month', 'value'),
    Input('tp-growth-timer', 'n_intervals'),
    State('tp-growth-month', 'value'),
    prevent_initial_call=True,
)
def advance_growth_month(_ticks, month):
    return 0 if month is None or month >= len(GROWTH_MONTHS) - 1 else month + 1


@callback(
    Output('tp-growth', 'figure'),
    Output('tp-growth-readout', 'children'),
    Input('tp-brand', 'value'), Input('tp-map-level', 'value'),
    Input('tp-growth-month', 'value'),
)
def update_growth(brand, level, month):
    figure = fig_builders.growth_map(DATASET, brand, level, month)
    totals = fig_builders.growth_totals(DATASET, brand, level, month)
    if not totals:
        return figure, ''
    readout = (f"{totals['period']} · {group(totals['orders'])} orders placed across "
               f"{group(totals['markets'])} of {group(totals['total_markets'])} markets "
               f"— {group(totals['share'] * 100, 1)}% of every order in the dataset, "
               f"worth {fig_builders.fmt_compact(totals['value'], 'money')}.")
    return figure, readout


@callback(
    Output('tp-return-trend', 'figure'),
    Output('tp-return-category', 'figure'),
    Output('tp-return-reason', 'figure'),
    Output('tp-return-stats', 'children'),
    Input('tp-brand', 'value'), Input('tp-preset', 'value'),
    Input('tp-return-grain', 'value'),
)
def update_returns(brand, preset, grain):
    lo, hi = _window(preset)
    return (fig_builders.return_rate_trend(DATASET, brand, lo, hi, grain),
            fig_builders.return_category_bars(DATASET, brand),
            fig_builders.return_reason_bars(DATASET, brand),
            _render_stats(fig_builders.returns_summary(DATASET, brand, lo, hi)))
