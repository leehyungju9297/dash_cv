"""Brand, portfolio roster, metric registry, and the demo dashboard color system.

Everything user-facing in the demo is named here so the dashboard reads as one
product. The roster is invented: a direct-to-consumer retail group whose brands
share one analytics layer. Aggregate rows mirror how a multi-brand dashboard
exposes portfolio-level rollups alongside individual brands.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


BRAND = 'Tidepool Commerce Analytics'
BRAND_MARK = 'TP'
BRAND_TAGLINE = 'Retail Intelligence'
BRAND_SLUG = 'tidepool'

# --------------------------------------------------------------------------
# Brand roster
# --------------------------------------------------------------------------
# ``tier`` drives which rollups a brand belongs to; ``scale`` is the synthetic
# data size multiplier; ``launch_offset`` staggers brand start dates so the
# portfolio does not look machine-generated. ``category`` is the brand's home
# category — it sells across the whole catalogue, but weighted toward this one.
BRAND_ACCOUNTS: List[Dict[str, object]] = [
    {'name': 'Aster & Vale', 'tier': 'flagship', 'scale': 1.00,
     'launch_offset': 0, 'category': 'Apparel', 'aov': 78.0},
    {'name': 'Northwind Goods', 'tier': 'flagship', 'scale': 0.66,
     'launch_offset': 45, 'category': 'Home & Kitchen', 'aov': 112.0},
    {'name': 'Lumen Skincare', 'tier': 'emerging', 'scale': 0.44,
     'launch_offset': 120, 'category': 'Beauty', 'aov': 54.0},
    {'name': 'Ridgeline Outfitters', 'tier': 'emerging', 'scale': 0.35,
     'launch_offset': 190, 'category': 'Outdoor', 'aov': 146.0},
    {'name': 'Copper Pine Coffee', 'tier': 'emerging', 'scale': 0.22,
     'launch_offset': 260, 'category': 'Food & Beverage', 'aov': 41.0},
]

BRAND_NAMES: List[str] = [account['name'] for account in BRAND_ACCOUNTS]

AGGREGATE_ALL = 'All Brands'
AGGREGATE_FLAGSHIP = 'Flagship Brands'
AGGREGATE_EMERGING = 'Emerging Brands'

AGGREGATES: List[Tuple[str, Tuple[str, ...]]] = [
    (AGGREGATE_ALL, tuple(BRAND_NAMES)),
    (AGGREGATE_FLAGSHIP, tuple(a['name'] for a in BRAND_ACCOUNTS if a['tier'] == 'flagship')),
    (AGGREGATE_EMERGING, tuple(a['name'] for a in BRAND_ACCOUNTS if a['tier'] == 'emerging')),
]

AGGREGATE_NAMES: List[str] = [name for name, _ in AGGREGATES]

# Selector order: rollups first (how a retail lead reads the portfolio), then
# individual brands.
BRANDS: List[str] = AGGREGATE_NAMES + BRAND_NAMES
DEFAULT_BRAND = AGGREGATE_ALL

# --------------------------------------------------------------------------
# Metric registry
# --------------------------------------------------------------------------
# key -> (display label, semantic accent, value format)
# ``format``: 'int' | 'money' | 'money2' | 'percent'
METRICS: Dict[str, Dict[str, str]] = {
    'orders': {'label': 'Orders', 'accent': 'teal', 'format': 'int'},
    'revenue': {'label': 'Revenue', 'accent': 'gold', 'format': 'money'},
    'aov': {'label': 'Average Order Value', 'accent': 'amber', 'format': 'money2'},
    'units': {'label': 'Units Sold', 'accent': 'cyan', 'format': 'int'},
    'customers': {'label': 'Daily Ordering Customers', 'accent': 'blue', 'format': 'int'},
    'monthly_customers': {'label': 'Monthly Active Customers', 'accent': 'lavender',
                          'format': 'int'},
    'new_customers': {'label': 'New Customers', 'accent': 'mint', 'format': 'int'},
    'repeat_customers': {'label': 'Repeat Customers', 'accent': 'green', 'format': 'int'},
    'returns': {'label': 'Returns', 'accent': 'coral', 'format': 'int'},
    # Marketing actions, not per-customer counters: a brand runs a campaign on
    # roughly a quarter of days and a flash sale a few times a quarter.
    'campaigns': {'label': 'Campaigns', 'accent': 'violet', 'format': 'int'},
    'email_sends': {'label': 'Email Sends', 'accent': 'amber', 'format': 'int'},
    'promotions': {'label': 'Flash Sales', 'accent': 'coral', 'format': 'int'},
    # Funnel terms. Revenue factors exactly as visits x conversion x AOV, which
    # is what the driver decomposition walks.
    'visits': {'label': 'Site Visits', 'accent': 'neutral', 'format': 'int'},
    'conversion': {'label': 'Conversion Rate', 'accent': 'mint', 'format': 'percent2'},
    'return_rate': {'label': 'Return Rate', 'accent': 'coral', 'format': 'percent'},
    'discount_rate': {'label': 'Discount Rate', 'accent': 'violet', 'format': 'percent'},
}

# Axis selectors on the revenue & orders trend. Cumulative variants are derived.
AXIS_METRICS: List[str] = [
    'revenue', 'orders', 'aov', 'units', 'visits', 'conversion', 'customers',
    'monthly_customers', 'new_customers', 'repeat_customers', 'returns',
    'campaigns', 'email_sends',
]

# The scatter-plot matrix panels. Five is the most that stays readable at card
# width; these are the metrics a trading review actually cross-reads.
SPLOM_METRICS: List[str] = ['revenue', 'orders', 'aov', 'visits', 'conversion']

# Metrics the anomaly scan runs over, and what counts as an outlier. The
# threshold is in robust z units (median / MAD), so a single promotion spike
# does not raise the bar for the rest of the window.
ANOMALY_METRICS: List[str] = ['revenue', 'orders', 'aov', 'conversion', 'returns']
ANOMALY_Z = 3.5

# Revenue factors as visits x conversion x AOV; the walk attributes the
# period-over-period change to each factor in turn.
DRIVER_TERMS: List[Tuple[str, str]] = [
    ('visits', 'Site Visits'),
    ('conversion', 'Conversion Rate'),
    ('aov', 'Average Order Value'),
]

# --------------------------------------------------------------------------
# Color system
# --------------------------------------------------------------------------
# A warm, light, print-safe system. Two rules drive every choice here:
#
#   1. Categorical colors are separated by *lightness*, not just hue — the
#      members of PALETTE sit 9-11 CIE L* apart, so a chart that is legible in
#      color is still legible photocopied or dropped into a greyscale deck.
#   2. Ordered dimensions (acquisition source, value tier, return reason) use a
#      single-hue sequential ramp rather than a categorical set, because their
#      categories have an order and a rainbow would hide it.
#
# Text colors clear WCAG AA against the page background; chart fills that fall
# below 3:1 always carry a darker outline (see figures.MARKER_LINE).
ACCENT = '#C4633F'          # terracotta — the one accent the product uses
ACCENT_DEEP = '#8B462D'
ACCENT_SOFT = '#F5E5DE'

POSITIVE = '#4E6B4D'        # muted sage
NEGATIVE = '#9E4B34'        # muted rust
NEUTRAL = '#8A837A'         # warm grey

# Categorical: nominal dimensions with no natural order.
PALETTE: List[str] = [
    '#6D3C29',   # clay        L* 31
    '#4E6B4D',   # sage        L* 42
    '#C4633F',   # terracotta  L* 53
    '#CA9038',   # amber       L* 64
    '#C7ADB6',   # plum        L* 73
    '#D9CAB2',   # sand        L* 82
]

# Sequential: one hue, dark to light. Ordered dimensions and heat scales.
SEQUENTIAL: List[str] = [
    '#8B462D', '#B55B3A', '#CD7B5D', '#DBA18B', '#E9C5B7', '#F5E5DE',
]

# Diverging: rust for below, sage for above, warm paper in the middle.
DIVERGING: List[str] = [
    '#9E4B34', '#C78574', '#F1EEE9', '#879B87', '#4E6B4D',
]

# Named accents, kept as a lookup so a metric keeps one hue everywhere it
# appears (chart line, axis title, stat number).
ACCENTS: Dict[str, str] = {
    'accent': ACCENT,
    'accent_deep': ACCENT_DEEP,
    'clay': '#6D3C29',
    'sage': '#4E6B4D',
    'amber': '#CA9038',
    'plum': '#8A5468',
    'sand': '#B79A6B',
    'neutral': NEUTRAL,
}

SURFACE = {
    'bg': 'rgba(0,0,0,0)',
    'page': '#FAF9F7',
    'card': '#FFFFFF',
    'grid': 'rgba(26, 26, 24, 0.08)',
    'zeroline': 'rgba(26, 26, 24, 0.20)',
    'text': '#1A1A18',
    # Axis labels and tick text are text, and are held to the same contrast bar
    # as the DOM: 7.2:1 and 5.1:1 on the card.
    'text_secondary': '#57544E',
    'text_muted': '#6F6A62',
    'border': '#E4E0D9',
}


def _ramp(colors: List[str]) -> List[Tuple[float, str]]:
    """Even color stops for a Plotly colorscale."""
    last = max(len(colors) - 1, 1)
    return [(index / last, color) for index, color in enumerate(colors)]


# Retention percentages: light paper at zero, deep accent at the top.
RETENTION_SCALE: List[Tuple[float, str]] = _ramp(list(reversed(SEQUENTIAL)))

# Average order value on the fulfillment map: below the portfolio mean reads
# sage, above it reads terracotta. Diverging, because the midpoint is meaning.
AOV_SCALE: List[Tuple[float, str]] = _ramp(DIVERGING)

# --------------------------------------------------------------------------
# Retail dimensions
# --------------------------------------------------------------------------
# Product catalogue. ``margin`` is contribution margin, used by the category
# waterfall; ``basket`` is the mean units per order in that category. Nominal,
# so the categorical palette applies.
CATEGORIES: List[Dict[str, object]] = [
    {'name': 'Apparel', 'color': PALETTE[0], 'margin': 0.54, 'basket': 1.9},
    {'name': 'Home & Kitchen', 'color': PALETTE[1], 'margin': 0.47, 'basket': 1.5},
    {'name': 'Beauty', 'color': PALETTE[2], 'margin': 0.66, 'basket': 2.4},
    {'name': 'Outdoor', 'color': PALETTE[3], 'margin': 0.42, 'basket': 1.3},
    {'name': 'Accessories', 'color': PALETTE[4], 'margin': 0.61, 'basket': 2.1},
    {'name': 'Food & Beverage', 'color': PALETTE[5], 'margin': 0.38, 'basket': 2.8},
]

CATEGORY_NAMES: List[str] = [c['name'] for c in CATEGORIES]
CATEGORY_COLORS: Dict[str, str] = {c['name']: c['color'] for c in CATEGORIES}

# Order channel — where the order was placed. Three nominal values, taken from
# the ends and middle of the categorical ramp so they separate in greyscale.
CHANNELS: List[Tuple[str, str]] = [
    ('Web', PALETTE[0]),
    ('Mobile App', PALETTE[2]),
    ('Marketplace', PALETTE[5]),
]

CHANNEL_NAMES: List[str] = [name for name, _ in CHANNELS]
CHANNEL_COLORS: Dict[str, str] = dict(CHANNELS)

# Customer acquisition source — how the customer first arrived. Distinct from
# channel: a customer acquired on Paid Social may order for years on Web.
# Ordered by typical contribution, so a sequential ramp encodes the ranking.
ACQUISITION_SOURCES: List[Tuple[str, str]] = [
    ('Paid Search', SEQUENTIAL[0]),
    ('Paid Social', SEQUENTIAL[1]),
    ('Organic Search', SEQUENTIAL[2]),
    ('Email', SEQUENTIAL[3]),
    ('Affiliate', SEQUENTIAL[4]),
    ('Referral', SEQUENTIAL[5]),
    ('Direct', NEUTRAL),
]

SOURCE_NAMES: List[str] = [name for name, _ in ACQUISITION_SOURCES]
SOURCE_COLORS: Dict[str, str] = dict(ACQUISITION_SOURCES)

# Discount codes. 'No code' is a first-class value — most orders carry no code,
# and a promotion view that hides that reads the lift backwards.
DISCOUNT_CODES: List[str] = [
    'No code', 'WELCOME10', 'SPRING20', 'FLASH30', 'BUNDLE15', 'LOYAL25',
]

# Return reasons, ordered by how often a DTC retailer sees them.
RETURN_REASONS: List[Tuple[str, str]] = [
    ('Fit / size', SEQUENTIAL[0]),
    ('Not as described', SEQUENTIAL[1]),
    ('Damaged in transit', SEQUENTIAL[2]),
    ('Changed mind', SEQUENTIAL[3]),
    ('Late delivery', SEQUENTIAL[4]),
]

RETURN_REASON_NAMES: List[str] = [name for name, _ in RETURN_REASONS]
RETURN_REASON_COLORS: Dict[str, str] = dict(RETURN_REASONS)

# --------------------------------------------------------------------------
# Customer value segmentation
# --------------------------------------------------------------------------
# RFM quadrants, ordered from most to least valuable — an ordered dimension, so
# the sequential ramp carries the ranking into greyscale.
VALUE_TIERS: List[Tuple[str, str]] = [
    ('Champions', SEQUENTIAL[0]),
    ('Loyal', SEQUENTIAL[1]),
    ('Promising', SEQUENTIAL[2]),
    ('At Risk', SEQUENTIAL[3]),
    ('Lapsed', NEUTRAL),
]

VALUE_TIER_NAMES: List[str] = [name for name, _ in VALUE_TIERS]
VALUE_TIER_COLORS: Dict[str, str] = dict(VALUE_TIERS)

# --------------------------------------------------------------------------
# Information architecture
# --------------------------------------------------------------------------
# Two levels: a retail function, then a view within it. The shell renders the
# functions as the primary tab row and the views as a segmented row beneath.
SECTIONS: List[Dict[str, object]] = [
    {
        'key': 'sales',
        'label': 'Sales Performance',
        'views': [
            {'key': 'revenue', 'label': 'Revenue & Orders',
             'blurb': 'Trade against the promotion calendar'},
            {'key': 'drivers', 'label': 'Revenue Drivers',
             'blurb': 'What moved the number, and what moves together'},
            {'key': 'category', 'label': 'Category Mix',
             'blurb': 'What the catalogue contributes'},
        ],
    },
    {
        'key': 'customers',
        'label': 'Customers',
        'views': [
            {'key': 'cohorts', 'label': 'Cohort Retention',
             'blurb': 'Repeat rate by acquisition month'},
            {'key': 'value', 'label': 'Customer Value',
             'blurb': 'Recency, frequency, and spend'},
        ],
    },
    {
        'key': 'marketing',
        'label': 'Marketing',
        'views': [
            {'key': 'channels', 'label': 'Channel Attribution',
             'blurb': 'Where customers come from and what they are worth'},
            {'key': 'promotions', 'label': 'Promotion Lift',
             'blurb': 'Promoted days against the baseline'},
        ],
    },
    {
        'key': 'operations',
        'label': 'Operations',
        'views': [
            {'key': 'fulfillment', 'label': 'Fulfillment & Regions',
             'blurb': 'Order volume and basket size by destination'},
            {'key': 'returns', 'label': 'Returns',
             'blurb': 'Return rate by category and reason'},
        ],
    },
]

VIEW_KEYS: List[str] = [view['key'] for section in SECTIONS for view in section['views']]
DEFAULT_VIEW = 'revenue'

SECTION_OF_VIEW: Dict[str, str] = {
    view['key']: section['key'] for section in SECTIONS for view in section['views']
}

VIEW_LABELS: Dict[str, str] = {
    view['key']: view['label'] for section in SECTIONS for view in section['views']
}

VIEWS_OF_SECTION: Dict[str, List[str]] = {
    section['key']: [view['key'] for view in section['views']] for section in SECTIONS
}

SECTION_LABELS: Dict[str, str] = {s['key']: s['label'] for s in SECTIONS}

DATE_PRESETS: List[Tuple[str, int]] = [
    ('30D', 30),
    ('90D', 90),
    ('6M', 182),
    ('1Y', 365),
    ('All', 0),
]

DEFAULT_PRESET = '1Y'


def metric_color(metric_key: str) -> str:
    """The chart/tile color for a metric key, falling back to neutral blue."""
    accent = METRICS.get(metric_key, {}).get('accent', 'blue')
    return ACCENTS.get(accent, ACCENTS['blue'])


def metric_label(metric_key: str) -> str:
    return METRICS.get(metric_key, {}).get('label', metric_key)


def metric_format(metric_key: str) -> str:
    return METRICS.get(metric_key, {}).get('format', 'int')
