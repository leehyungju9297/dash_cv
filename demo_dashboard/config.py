"""Brand, client roster, metric registry, and the demo dashboard color system.

Everything user-facing in the demo is named here so the dashboard reads as one
product. The roster is fictional: a white-label fan-app platform ("Frontrow")
whose tenants are artists. Aggregate rows mirror how a real multi-tenant
dashboard exposes portfolio-level rollups alongside individual accounts.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


BRAND = 'Frontrow Analytics'
BRAND_MARK = 'FR'
BRAND_TAGLINE = 'Fan Platform Intelligence'

# --------------------------------------------------------------------------
# Client roster
# --------------------------------------------------------------------------
# ``tier`` drives which aggregate rollups a client belongs to; ``scale`` is the
# synthetic-data size multiplier; ``launch_offset`` staggers account start dates
# so the portfolio does not look machine-generated.
CLIENT_ACCOUNTS: List[Dict[str, object]] = [
    {'name': 'Nova Reyes', 'tier': 'vip', 'scale': 1.00, 'launch_offset': 0, 'genre': 'Pop / Electronic'},
    {'name': 'Kaito Mori', 'tier': 'saas', 'scale': 0.62, 'launch_offset': 45, 'genre': 'Hip-Hop'},
    {'name': 'Lena Vossberg', 'tier': 'saas', 'scale': 0.41, 'launch_offset': 120, 'genre': 'Indie Rock'},
    {'name': 'Marcus Dune', 'tier': 'vip', 'scale': 0.33, 'launch_offset': 190, 'genre': 'R&B / Soul'},
    {'name': 'Sable Collective', 'tier': 'saas', 'scale': 0.21, 'launch_offset': 260, 'genre': 'Alt / Shoegaze'},
]

CLIENT_NAMES: List[str] = [account['name'] for account in CLIENT_ACCOUNTS]

AGGREGATE_ALL = f'All {BRAND.split()[0]}'          # "All Frontrow"
AGGREGATE_SAAS = 'All Active SAAS Clients'
AGGREGATE_VIP = 'All VIP Artists'

AGGREGATES: List[Tuple[str, Tuple[str, ...]]] = [
    (AGGREGATE_ALL, tuple(CLIENT_NAMES)),
    (AGGREGATE_VIP, tuple(a['name'] for a in CLIENT_ACCOUNTS if a['tier'] == 'vip')),
    (AGGREGATE_SAAS, tuple(a['name'] for a in CLIENT_ACCOUNTS if a['tier'] == 'saas')),
]

AGGREGATE_NAMES: List[str] = [name for name, _ in AGGREGATES]

# Selector order: rollups first (how leadership reads the portfolio), then
# individual accounts.
CLIENTS: List[str] = AGGREGATE_NAMES + CLIENT_NAMES
DEFAULT_CLIENT = AGGREGATE_ALL

# --------------------------------------------------------------------------
# Metric registry
# --------------------------------------------------------------------------
# key -> (display label, semantic accent, value format)
# ``format``: 'int' | 'money' | 'minutes' | 'percent'
METRICS: Dict[str, Dict[str, str]] = {
    'downloads': {'label': 'Downloads', 'accent': 'teal', 'format': 'int'},
    'dau': {'label': 'Daily Active Users', 'accent': 'blue', 'format': 'int'},
    'mau': {'label': 'Monthly Active Users', 'accent': 'lavender', 'format': 'int'},
    'memberships': {'label': 'Current Memberships', 'accent': 'green', 'format': 'int'},
    'new_memberships': {'label': 'New Memberships', 'accent': 'mint', 'format': 'int'},
    'revenue': {'label': 'Revenue', 'accent': 'gold', 'format': 'money'},
    # Content events, not per-user counters: a busy account posts on about a
    # quarter of days and almost never runs an auction. See calibration.py.
    'posts': {'label': 'Timeline Posts', 'accent': 'violet', 'format': 'int'},
    'notifications': {'label': 'Notifications', 'accent': 'amber', 'format': 'int'},
    'livestreams': {'label': 'Livestreams', 'accent': 'cyan', 'format': 'int'},
    'auctions': {'label': 'Auctions', 'accent': 'coral', 'format': 'int'},
    'session_minutes': {'label': 'Minutes / Active User', 'accent': 'lavender',
                        'format': 'minutes'},
}

# Axis selectors on the trend chart. Cumulative variants are derived, not stored.
AXIS_METRICS: List[str] = [
    'dau', 'mau', 'downloads', 'memberships', 'new_memberships',
    'revenue', 'posts', 'notifications', 'livestreams', 'auctions',
]

# Metrics fed into the correlation diagnostics.
CORRELATION_METRICS: List[str] = [
    'dau', 'mau', 'downloads', 'memberships', 'new_memberships',
    'revenue', 'posts', 'notifications',
]

# --------------------------------------------------------------------------
# Color system
# --------------------------------------------------------------------------
# A muted enterprise palette calibrated for the charcoal dashboard surface: a
# metric keeps the same hue everywhere it appears (chart line, axis, KPI tile),
# so two metrics are never confused across sections.
ACCENTS: Dict[str, str] = {
    'blue': '#6BAEE8',
    'cyan': '#5CC5BA',
    'teal': '#4DB6AC',
    'green': '#79D29B',
    'mint': '#6FD9C4',
    'gold': '#E6B450',
    'amber': '#F0C05A',
    'violet': '#AC9BE8',
    'lavender': '#9B8AD6',
    'coral': '#F08C7E',
    'neutral': '#8FA0B4',
}

SURFACE = {
    'bg': 'rgba(0,0,0,0)',
    'grid': 'rgba(148, 163, 184, 0.13)',
    'zeroline': 'rgba(148, 163, 184, 0.22)',
    'text': '#F1F5F9',
    'text_secondary': '#AAB4C3',
    'text_muted': '#7E8A9A',
    'card': '#10151D',
    'border': '#263244',
}

# Audience segmentation: how a fan-app account matures. Used by the map and the
# location breakdown.
SEGMENTS: List[Tuple[str, str]] = [
    ('Non-Signed-Up', '#5A6B80'),
    ('Signed-Up', '#6BAEE8'),
    ('Member', '#79D29B'),
    ('Super User', '#E6B450'),
]

SEGMENT_NAMES: List[str] = [name for name, _ in SEGMENTS]
SEGMENT_COLORS: Dict[str, str] = dict(SEGMENTS)

# Revenue source dimensions (mirrors a real store/ledger breakdown).
REVENUE_DIMENSIONS: Dict[str, List[str]] = {
    'platform': ['iOS', 'Android', 'Other'],
    'revenue_type': ['Subscription', 'Unknown', 'Auction',
                     'Meet & Greet', 'Album', 'Livestream Ticket'],
}

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
