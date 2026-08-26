"""Deterministic synthetic dataset for the Frontrow Analytics demo.

Standard library only — no pandas/numpy — so the portfolio site keeps its single
`dash` dependency and the dataset can be generated identically on any machine.

Everything is seeded, so the same dashboard renders on every run and the static
JSON twin never drifts from the live Dash page.

Shape of the generated data
---------------------------
Daily per-client series (downloads, DAU, MAU, memberships, revenue, and the
engagement event families), a per-client event log used for chart overlays, a
geo/segment breakdown, a revenue source ledger, monthly churn, membership
lifetime buckets, and a top-user leaderboard. Aggregate rows ("All Frontrow",
"All VIP Artists", "All Active SAAS Clients") are summed from account rows, with
active-user metrics de-duplicated so rollups do not double-count fans who follow
more than one artist.
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta
from functools import lru_cache
from typing import Dict, List, Sequence

from demo_dashboard.config import (
    AGGREGATES,
    CLIENT_ACCOUNTS,
    CORRELATION_METRICS,
    SEGMENT_NAMES,
)
from demo_dashboard.calibration import (
    CONTENT_CADENCE,
    DAU_OVER_MAU,
    MARKET_ZIPF_ALPHA,
    PLATFORM_MIX,
    REVENUE_PER_MEMBER_DAY,
    REVENUE_TYPE_MIX,
    TENURE_MIX,
    WEEKDAY_ACTIVE,
    WEEKDAY_DOWNLOADS,
    WEEKDAY_REVENUE,
)
from demo_dashboard.geo import string_seed


# The window is fixed rather than relative to "today" so the demo is byte-stable.
END_DATE = date(2026, 6, 30)
WINDOW_DAYS = 730
START_DATE = END_DATE - timedelta(days=WINDOW_DAYS - 1)

SEED = 20260630

# Metrics carried in the daily series. Rollups sum these except for the
# de-duplicated active-user metrics listed in _DEDUPED.
SERIES_KEYS = [
    'downloads', 'dau', 'mau', 'memberships', 'new_memberships',
    'revenue', 'posts', 'notifications', 'livestreams',
    'auctions', 'session_minutes',
]

# Summing DAU/MAU across accounts double-counts multi-artist fans; a portfolio
# rollup applies an overlap discount instead. Session length is an average, so it
# is weighted by DAU rather than summed.
_DEDUPED = {'dau': 0.88, 'mau': 0.82}
_AVERAGED = {'session_minutes'}


# --------------------------------------------------------------------------
# Event log
# --------------------------------------------------------------------------
# Each event kind names the metrics it lifts and the shape of that lift:
#   amp    peak multiplier added at the event date
#   decay  days for the lift to fall to ~1/e of its peak
EVENT_KINDS: Dict[str, Dict[str, object]] = {
    'Album Drop': {
        'amp': {'downloads': 2.6, 'dau': 1.1, 'posts': 1.9, 'notifications': 1.4,
                'livestreams': 0.9, 'new_memberships': 1.3, 'session_minutes': 0.35},
        'decay': 11.0, 'color': '#6BAEE8',
    },
    'Tour Announcement': {
        'amp': {'downloads': 1.5, 'dau': 0.8, 'notifications': 2.2, 'posts': 0.9,
                'new_memberships': 0.9},
        'decay': 7.0, 'color': '#AC9BE8',
    },
    'Livestream Q&A': {
        'amp': {'livestreams': 3.4, 'dau': 0.7, 'session_minutes': 0.8, 'posts': 0.6},
        'decay': 2.5, 'color': '#5CC5BA',
    },
    'Merch Auction': {
        'amp': {'auctions': 3.8, 'revenue': 1.4, 'dau': 0.4, 'notifications': 0.7},
        'decay': 4.0, 'color': '#F08C7E',
    },
    'Membership Push': {
        'amp': {'new_memberships': 2.7, 'notifications': 1.6, 'revenue': 0.5, 'dau': 0.3},
        'decay': 6.0, 'color': '#79D29B',
    },
    'App Release': {
        'amp': {'downloads': 0.9, 'session_minutes': 0.5, 'dau': 0.45},
        'decay': 14.0, 'color': '#E6B450',
    },
}

EVENT_ORDER = list(EVENT_KINDS)


# --------------------------------------------------------------------------
# Geography
# --------------------------------------------------------------------------
# Markets in audience-rank order. Weights are not written by hand: they follow
# the rank^-a curve measured on the real client base (calibration.MARKET_ZIPF_ALPHA),
# which produces the long, flat tail a real fan app has instead of three metros
# holding everything. The roster is US-weighted to match the measured country mix.
CITY_TABLE_RANKED = [
    ('Los Angeles', 'California', 'United States', 34.05, -118.24),
    ('New York', 'New York', 'United States', 40.71, -74.01),
    ('Chicago', 'Illinois', 'United States', 41.88, -87.63),
    ('Houston', 'Texas', 'United States', 29.76, -95.37),
    ('Atlanta', 'Georgia', 'United States', 33.75, -84.39),
    ('Dallas', 'Texas', 'United States', 32.78, -96.80),
    ('Philadelphia', 'Pennsylvania', 'United States', 39.95, -75.17),
    ('Toronto', 'Ontario', 'Canada', 43.65, -79.38),
    ('Phoenix', 'Arizona', 'United States', 33.45, -112.07),
    ('Miami', 'Florida', 'United States', 25.76, -80.19),
    ('San Antonio', 'Texas', 'United States', 29.42, -98.49),
    ('Detroit', 'Michigan', 'United States', 42.33, -83.05),
    ('Charlotte', 'North Carolina', 'United States', 35.23, -80.84),
    ('Memphis', 'Tennessee', 'United States', 35.15, -90.05),
    ('Baltimore', 'Maryland', 'United States', 39.29, -76.61),
    ('Columbus', 'Ohio', 'United States', 39.96, -83.00),
    ('Las Vegas', 'Nevada', 'United States', 36.17, -115.14),
    ('Seattle', 'Washington', 'United States', 47.61, -122.33),
    ('Denver', 'Colorado', 'United States', 39.74, -104.99),
    ('Indianapolis', 'Indiana', 'United States', 39.77, -86.16),
    ('Montreal', 'Quebec', 'Canada', 45.50, -73.57),
    ('Jacksonville', 'Florida', 'United States', 30.33, -81.66),
    ('Nashville', 'Tennessee', 'United States', 36.16, -86.78),
    ('Milwaukee', 'Wisconsin', 'United States', 43.04, -87.91),
    ('Washington', 'District of Columbia', 'United States', 38.91, -77.04),
    ('Boston', 'Massachusetts', 'United States', 42.36, -71.06),
    ('San Francisco', 'California', 'United States', 37.77, -122.42),
    ('Austin', 'Texas', 'United States', 30.27, -97.74),
    ('Fort Worth', 'Texas', 'United States', 32.76, -97.33),
    ('Kansas City', 'Missouri', 'United States', 39.10, -94.58),
    ('New Orleans', 'Louisiana', 'United States', 29.95, -90.07),
    ('London', 'England', 'United Kingdom', 51.51, -0.13),
    ('Cleveland', 'Ohio', 'United States', 41.50, -81.69),
    ('Louisville', 'Kentucky', 'United States', 38.25, -85.76),
    ('St. Louis', 'Missouri', 'United States', 38.63, -90.20),
    ('Oklahoma City', 'Oklahoma', 'United States', 35.47, -97.52),
    ('Portland', 'Oregon', 'United States', 45.52, -122.68),
    ('San Diego', 'California', 'United States', 32.72, -117.16),
    ('Vancouver', 'British Columbia', 'Canada', 49.28, -123.12),
    ('Minneapolis', 'Minnesota', 'United States', 44.98, -93.27),
    ('Sacramento', 'California', 'United States', 38.58, -121.49),
    ('Tampa', 'Florida', 'United States', 27.95, -82.46),
    ('Orlando', 'Florida', 'United States', 28.54, -81.38),
    ('Birmingham', 'Alabama', 'United States', 33.52, -86.80),
    ('Richmond', 'Virginia', 'United States', 37.54, -77.44),
    ('Raleigh', 'North Carolina', 'United States', 35.78, -78.64),
    ('Calgary', 'Alberta', 'Canada', 51.05, -114.07),
    ('Cincinnati', 'Ohio', 'United States', 39.10, -84.51),
    ('Pittsburgh', 'Pennsylvania', 'United States', 40.44, -79.996),
    ('Newark', 'New Jersey', 'United States', 40.74, -74.17),
    ('Buffalo', 'New York', 'United States', 42.89, -78.88),
    ('Tucson', 'Arizona', 'United States', 32.22, -110.97),
    ('Albuquerque', 'New Mexico', 'United States', 35.08, -106.65),
    ('Fresno', 'California', 'United States', 36.74, -119.79),
    ('Omaha', 'Nebraska', 'United States', 41.26, -95.93),
    ('Tulsa', 'Oklahoma', 'United States', 36.15, -95.99),
    ('Jackson', 'Mississippi', 'United States', 32.30, -90.18),
    ('Shreveport', 'Louisiana', 'United States', 32.53, -93.75),
    ('Sydney', 'New South Wales', 'Australia', -33.87, 151.21),
    ('Little Rock', 'Arkansas', 'United States', 34.75, -92.29),
    ('Montgomery', 'Alabama', 'United States', 32.38, -86.30),
    ('Salt Lake City', 'Utah', 'United States', 40.76, -111.89),
    ('Mumbai', 'Maharashtra', 'India', 19.08, 72.88),
    ('Boise', 'Idaho', 'United States', 43.62, -116.20),
    ('Rome', 'Lazio', 'Italy', 41.90, 12.50),
    ('Lagos', 'Lagos', 'Nigeria', 6.52, 3.38),
    ('Melbourne', 'Victoria', 'Australia', -37.81, 144.96),
    ('Johannesburg', 'Gauteng', 'South Africa', -26.20, 28.05),
    ('Berlin', 'Berlin', 'Germany', 52.52, 13.40),
    ('Honolulu', 'Hawaii', 'United States', 21.31, -157.86),
    ('Manchester', 'England', 'United Kingdom', 53.48, -2.24),
    ('Delhi', 'Delhi', 'India', 28.61, 77.21),
    ('Warsaw', 'Mazovia', 'Poland', 52.23, 21.01),
    ('Cape Town', 'Western Cape', 'South Africa', -33.92, 18.42),
    ('Milan', 'Lombardy', 'Italy', 45.46, 9.19),
    ('Paris', 'Ile-de-France', 'France', 48.86, 2.35),
    ('Amsterdam', 'North Holland', 'Netherlands', 52.37, 4.90),
    ('Anchorage', 'Alaska', 'United States', 61.22, -149.90),
]


def _ranked_city_table():
    """Attach the measured rank^-a weight to each market."""
    return [
        (city, region, country, lat, lon, (rank + 1) ** -MARKET_ZIPF_ALPHA)
        for rank, (city, region, country, lat, lon) in enumerate(CITY_TABLE_RANKED)
    ]


CITY_TABLE = _ranked_city_table()


# Handles for the top-user leaderboard. Fictional, deliberately generic.
_HANDLE_STEMS = [
    'novafan', 'frontrow', 'midnight', 'echopark', 'stagelight', 'lowtide',
    'goldenhour', 'papermoon', 'velvet', 'northline', 'reverb', 'sunroom',
    'crescent', 'analog', 'saltwater', 'wildcard', 'neonrun', 'quietstorm',
    'afterglow', 'bluehour', 'tapehiss', 'slowburn', 'citylights', 'driftwood',
]


# ==========================================================================
# Helpers
# ==========================================================================
def _date_strings() -> List[str]:
    return [(START_DATE + timedelta(days=i)).isoformat() for i in range(WINDOW_DAYS)]


def _weekly_shape(rnd: random.Random, base: Sequence[float]) -> List[float]:
    """Weekday multipliers for one metric family, jittered per account.

    The shapes are measured, not guessed, and they are not the intuitive ones:
    active users *fall* on the weekend and bottom out on Sunday (0.65 of Monday),
    while downloads peak on Friday. See calibration.WEEKDAY_ACTIVE.
    """
    return [value * rnd.uniform(0.97, 1.03) for value in base]


def _poisson(rnd: random.Random, lam: float) -> int:
    """Knuth's sampler. Content events are counts of things the artist shipped
    that day, so they are drawn as counts rather than scaled from user volume."""
    if lam <= 0:
        return 0
    if lam > 24:
        return int(round(lam))
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rnd.random()
        if p <= limit:
            return k
        k += 1


def _event_multiplier(events, day_index: int, metric: str) -> float:
    """Combined lift on ``metric`` at ``day_index`` from every nearby event.

    The kernel is asymmetric on purpose: anticipation before the date is short
    and shallow, the drop is instant, and the tail decays over days. A symmetric
    bell would imply the audience reacted before the announcement existed.
    """
    lift = 0.0
    for event in events:
        amp = EVENT_KINDS[event['kind']]['amp'].get(metric)
        if not amp:
            continue
        delta = day_index - event['day_index']
        if delta < -4 or delta > 60:
            continue
        decay = EVENT_KINDS[event['kind']]['decay']
        if delta >= 0:
            kernel = math.exp(-delta / decay)
        else:
            kernel = math.exp(delta * 1.4)  # short, shallow pre-buzz
        lift += amp * event['magnitude'] * kernel
    return 1.0 + lift


# What each event kind puts on the timeline on the day it happens. Without this
# the content metrics and the release-calendar overlay would drift apart: a
# livestream fires on 1.7% of days, so a "Livestream Q&A" marker would usually
# sit above a flat zero line.
EVENT_CONTENT = {
    'Album Drop': {'posts': 2, 'notifications': 1},
    'Tour Announcement': {'posts': 1, 'notifications': 1},
    'Livestream Q&A': {'livestreams': 1, 'posts': 1},
    'Merch Auction': {'auctions': 1, 'notifications': 1},
    'Membership Push': {'notifications': 1},
    'App Release': {'notifications': 1},
}


def _scheduled_content(events, day_index: int) -> Dict[str, int]:
    """Content the release calendar puts on this exact day."""
    out = {'posts': 0, 'notifications': 0, 'livestreams': 0, 'auctions': 0}
    for event in events:
        if event['day_index'] != day_index:
            continue
        for key, count in EVENT_CONTENT.get(event['kind'], {}).items():
            out[key] += count
    return out


def _build_events(rnd: random.Random, launch: int) -> List[Dict[str, object]]:
    """A plausible release calendar for one account."""
    events: List[Dict[str, object]] = []
    day = launch + rnd.randint(14, 40)
    while day < WINDOW_DAYS - 5:
        kind = rnd.choices(
            EVENT_ORDER,
            weights=[1.0, 1.3, 2.2, 1.8, 1.5, 0.8],
        )[0]
        events.append({
            'kind': kind,
            'day_index': day,
            'date': (START_DATE + timedelta(days=day)).isoformat(),
            'magnitude': round(rnd.uniform(0.55, 1.35), 3),
        })
        day += rnd.randint(28, 74)
    return events


def _rolling_dedup_mau(dau: Sequence[float], window: int = 30) -> List[float]:
    """Approximate MAU from DAU with a 30-day rolling sum and a repeat-visit
    discount.

    Real MAU is a distinct-user count. Summing 30 days of DAU would count a fan
    who opens the app daily thirty times, so the sum is compressed to land the
    DAU/MAU stickiness ratio in the ~25-35% band a healthy fan app shows, without
    carrying user-level identities through the whole dataset."""
    out: List[float] = []
    running = 0.0
    # Measured stickiness is ~4.8%, i.e. monthly actives run about 21x daily
    # actives: the audience opens the app once or twice a month around a release,
    # so a 30-day sum of DAU barely double-counts anyone. The compression is
    # therefore mild — an intuitive "most dailies are the same people" factor
    # would understate MAU by 4x.
    for i, value in enumerate(dau):
        running += value
        if i >= window:
            running -= dau[i - window]
        span = min(i + 1, window)
        out.append((running / span) / DAU_OVER_MAU)
    return out


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x <= 0 or var_y <= 0:
        return 0.0
    return cov / math.sqrt(var_x * var_y)


# ==========================================================================
# Per-account generation
# ==========================================================================
def _build_account_series(account: Dict[str, object], events) -> Dict[str, List[float]]:
    """Daily metric series for one account.

    Growth is a logistic install ramp modulated by yearly seasonality, weekday
    shape, noise, and the event calendar. Memberships are simulated as a stock
    (new joins in, daily churn out) rather than a cumulative sum, so the churn
    page and the membership page agree by construction.
    """
    rnd = random.Random(f"{SEED}:{account['name']}")
    scale = float(account['scale'])
    launch = int(account['launch_offset'])
    weekly_active = _weekly_shape(rnd, WEEKDAY_ACTIVE)
    weekly_downloads = _weekly_shape(rnd, WEEKDAY_DOWNLOADS)
    weekly_revenue = _weekly_shape(rnd, WEEKDAY_REVENUE)
    active_days = max(WINDOW_DAYS - launch, 1)

    # Every rate below is anchored to a measured quantile — see calibration.py.
    base_downloads = 190.0 * scale
    install_conversion = rnd.uniform(0.038, 0.058)  # measured median 0.047
    reactivation = rnd.uniform(0.0004, 0.0011)      # existing active -> membership
    daily_churn = rnd.uniform(0.0028, 0.0058)       # measured p25..p75
    arpu_daily = REVENUE_PER_MEMBER_DAY * rnd.uniform(0.60, 1.02)
    reach = rnd.uniform(0.030, 0.062)               # installed base -> DAU
    minutes_per_active = rnd.uniform(1.5, 2.6)      # measured ~1.96

    series: Dict[str, List[float]] = {key: [] for key in SERIES_KEYS}
    installed_base = 0.0
    members = 0.0

    for i in range(WINDOW_DAYS):
        if i < launch:
            for key in SERIES_KEYS:
                series[key].append(0.0)
            continue

        age = (i - launch) / active_days
        ramp = 1.0 / (1.0 + math.exp(-(age - 0.30) * 5.4))
        season = 1.0 + 0.16 * math.sin(2.0 * math.pi * i / 365.25 - 1.05)
        weekday_index = (START_DATE + timedelta(days=i)).weekday()

        downloads = (
            base_downloads * ramp * season * weekly_downloads[weekday_index]
            * rnd.gauss(1.0, 0.085)
            * _event_multiplier(events, i, 'downloads')
        )
        downloads = max(downloads, 0.0)
        installed_base += downloads * 0.93  # net of uninstalls

        dau = (
            installed_base * reach * weekly_active[weekday_index] * season
            * rnd.gauss(1.0, 0.055)
            * _event_multiplier(events, i, 'dau')
        )
        dau = max(dau, 0.0)

        # Most joins come from fresh installs; a smaller trickle converts fans
        # who have been active for a while. Splitting the two keeps the
        # membership stock anchored to the installed base instead of drifting
        # above it, which a flat DAU-conversion would do over a long window.
        new_members = (
            (downloads * install_conversion + dau * reactivation)
            * rnd.gauss(1.0, 0.14)
            * _event_multiplier(events, i, 'new_memberships')
        )
        new_members = max(new_members, 0.0)
        members = max(members + new_members - members * daily_churn, 0.0)

        revenue = (
            members * arpu_daily * weekly_revenue[weekday_index]
            + dau * 0.004 * rnd.uniform(0.7, 1.3)
        ) * _event_multiplier(events, i, 'revenue')

        # Content events: counts of what the artist shipped that day, drawn at
        # the measured cadence and lifted by the release calendar. Scaling these
        # off user volume (the intuitive reading of the column names) overstates
        # them by three orders of magnitude.
        scheduled = _scheduled_content(events, i)
        posts = scheduled['posts'] + _poisson(
            rnd, CONTENT_CADENCE['posts'] * _event_multiplier(events, i, 'posts'))
        notifications = scheduled['notifications'] + _poisson(
            rnd, CONTENT_CADENCE['notifications']
            * _event_multiplier(events, i, 'notifications'))
        livestreams = scheduled['livestreams'] + _poisson(
            rnd, CONTENT_CADENCE['livestreams'] * _event_multiplier(events, i, 'livestreams'))
        auctions = scheduled['auctions'] + _poisson(
            rnd, CONTENT_CADENCE['auctions'] * _event_multiplier(events, i, 'auctions'))

        session = (
            minutes_per_active * (0.9 + 0.25 * ramp)
            * _event_multiplier(events, i, 'session_minutes')
            * rnd.gauss(1.0, 0.06)
        )

        series['downloads'].append(downloads)
        series['dau'].append(dau)
        series['memberships'].append(members)
        series['new_memberships'].append(new_members)
        series['revenue'].append(revenue)
        series['posts'].append(posts)
        series['notifications'].append(notifications)
        series['livestreams'].append(livestreams)
        series['auctions'].append(auctions)
        series['session_minutes'].append(session)
        series['mau'].append(0.0)  # filled below

    series['mau'] = _rolling_dedup_mau(series['dau'])
    return series


def _round_series(series: Dict[str, List[float]]) -> Dict[str, List[float]]:
    """Round for transport: counts and money to whole units, session length to
    one decimal. Keeps the exported JSON small and the Dash page and its static
    twin byte-identical in what they display."""
    out: Dict[str, List[float]] = {}
    for key, values in series.items():
        if key == 'session_minutes':
            out[key] = [round(v, 1) for v in values]
        else:
            # Daily revenue runs in the hundreds-to-thousands; cents are noise
            # that would only bloat the exported JSON.
            out[key] = [int(round(v)) for v in values]
    return out


def _build_locations(account: Dict[str, object], series: Dict[str, List[float]]):
    """City-level audience counts split by lifecycle segment.

    Totals are anchored to the account's installed base so the geography page and
    the KPI page tell the same story, and each account gets its own city weighting
    (an artist's audience is not uniformly distributed).
    """
    rnd = random.Random(f"{SEED}:geo:{account['name']}")
    installed = sum(series['downloads']) * 0.93
    members = series['memberships'][-1]

    weights = []
    for _, _, country, _, _, base in CITY_TABLE:
        # A modest tilt so two accounts rank their markets differently, but not
        # so much that it erases the measured rank^-a curve underneath.
        tilt = rnd.uniform(0.70, 1.45)
        if country != 'United States':
            tilt *= rnd.uniform(0.65, 1.25)
        weights.append(base * tilt)
    total_weight = sum(weights)

    rows = []
    for (city, region, country, lat, lon, _), weight in zip(CITY_TABLE, weights):
        share = weight / total_weight
        users = installed * share
        if users < 12:
            continue
        member_count = members * share * rnd.uniform(0.7, 1.35)
        member_count = min(member_count, users * 0.42)
        super_users = member_count * rnd.uniform(0.08, 0.19)
        signed_up = (users - member_count) * rnd.uniform(0.35, 0.6)
        non_signed = users - member_count - signed_up
        rows.append({
            'city': city,
            'region': region,
            'country': country,
            'lat': lat,
            'lon': lon,
            'users': int(round(users)),
            # Active usage in this market. Sized off members and signed-up fans
            # rather than raw installs, so the Engagement view ranks markets by
            # how much the audience *uses* the app, not how many downloaded it.
            'engagement': int(round(
                (member_count * rnd.uniform(2.2, 4.1) + signed_up * rnd.uniform(0.4, 1.1))
            )),
            # Stable per-market seed for the shared marker generator, and the
            # market's lag in the growth animation (0 = launched with the app).
            'seed': string_seed(f'{account["name"]}|{city}'),
            # A share of markets are there from launch day; the rest open later,
            # so the growth animation spreads outward instead of fading in evenly.
            'ramp_lag': 0.0 if rnd.random() < 0.4 else round(rnd.uniform(0.06, 0.55), 4),
            'segments': {
                'Non-Signed-Up': int(round(max(non_signed, 0))),
                'Signed-Up': int(round(max(signed_up, 0))),
                'Member': int(round(max(member_count - super_users, 0))),
                'Super User': int(round(max(super_users, 0))),
            },
        })
    rows.sort(key=lambda r: -r['users'])
    return rows


def _build_monthly_ramp(series: Dict[str, List[float]], dates: List[str]):
    """Cumulative share of the account's installed base reached by each month.

    The growth animation replays this curve per market instead of shipping
    per-user arrival timestamps.
    """
    total = sum(series['downloads']) or 1.0
    steps: List[Dict[str, object]] = []
    running = 0.0
    for iso, downloads in zip(dates, series['downloads']):
        running += downloads
        month = iso[:7]
        if steps and steps[-1]['period'] == month:
            steps[-1]['frac'] = round(running / total, 6)
        else:
            steps.append({'period': month, 'frac': round(running / total, 6)})
    return steps


def _build_revenue_mix(account: Dict[str, object], series: Dict[str, List[float]]):
    """Revenue split by store platform and product type."""
    rnd = random.Random(f"{SEED}:rev:{account['name']}")
    total = sum(series['revenue'])

    def _split(mix):
        """Measured mix, jittered per account so the roster is not identical.

        The store split is nowhere near even: iOS carries ~92% of recognised
        revenue, and subscriptions carry ~92% of it by product type.
        """
        weights = [share * rnd.uniform(0.82, 1.22) for share in mix.values()]
        pool = sum(weights)
        return [
            {'label': label, 'revenue': round(total * w / pool, 2)}
            for label, w in zip(mix, weights)
        ]

    return {'platform': _split(PLATFORM_MIX), 'revenue_type': _split(REVENUE_TYPE_MIX)}


def _build_churn(series: Dict[str, List[float]], dates: List[str]):
    """Monthly membership churn derived from the same stock the KPI page shows.

    Lost members are the residual of the stock identity
    (start + joins - end), so churn can never disagree with the membership line.
    """
    months: List[Dict[str, object]] = []
    current = None
    for i, iso in enumerate(dates):
        month = iso[:7]
        members = series['memberships'][i]
        joins = series['new_memberships'][i]
        if current is None or current['period'] != month:
            if current is not None:
                months.append(current)
            current = {'period': month, 'start': members, 'joined': 0.0, 'end': members}
        current['joined'] += joins
        current['end'] = members
    if current is not None:
        months.append(current)

    out = []
    for row in months:
        start = row['start']
        lost = max(start + row['joined'] - row['end'], 0.0)
        churn_pct = (lost / start * 100.0) if start > 30 else 0.0
        out.append({
            'period': row['period'],
            'start': int(round(start)),
            'joined': int(round(row['joined'])),
            'lost': int(round(lost)),
            'churn_pct': round(churn_pct, 2),
        })
    return [row for row in out if row['start'] > 0]


LIFETIME_BUCKETS = ['0-30d', '31-90d', '91-180d', '181-365d', '1-2y', '2y+']


def _build_lifetime(account: Dict[str, object], series: Dict[str, List[float]]):
    """Membership tenure distribution plus the headline median/mean."""
    rnd = random.Random(f"{SEED}:life:{account['name']}")
    members = series['memberships'][-1]
    # Measured tenure distribution: the mode is 31-90 days, not a flat spread.
    # Roughly a fifth of members are inside their first month at any time.
    shape = [TENURE_MIX[bucket] * rnd.uniform(0.85, 1.18) for bucket in LIFETIME_BUCKETS]
    pool = sum(shape)
    counts = [int(round(members * w / pool)) for w in shape]
    midpoints = [15, 60, 135, 273, 547, 900]
    total = sum(counts) or 1
    mean_days = sum(c * m for c, m in zip(counts, midpoints)) / total

    running = 0
    median_days = midpoints[-1]
    for count, mid in zip(counts, midpoints):
        running += count
        if running >= total / 2:
            median_days = mid
            break

    return {
        'buckets': [{'bucket': b, 'members': c} for b, c in zip(LIFETIME_BUCKETS, counts)],
        'mean_days': round(mean_days, 1),
        'median_days': median_days,
        'active_members': int(round(members)),
    }


def _build_top_users(account: Dict[str, object], series: Dict[str, List[float]]):
    """Leaderboard of the most engaged fans for the account."""
    rnd = random.Random(f"{SEED}:users:{account['name']}")
    rows = []
    for rank in range(25):
        stem = rnd.choice(_HANDLE_STEMS)
        handle = f"{stem}_{rnd.randint(100, 9999)}"
        weight = math.exp(-rank * 0.14) * rnd.uniform(0.85, 1.15)
        rows.append({
            'rank': rank + 1,
            'handle': handle,
            'city': rnd.choice(CITY_TABLE)[0],
            'membership': rnd.choices(
                ['Super User', 'Member', 'Signed-Up'], weights=[4, 5, 1]
            )[0],
            'sessions': int(round(430 * weight * rnd.uniform(0.8, 1.2))),
            'minutes': int(round(9400 * weight * rnd.uniform(0.75, 1.25))),
            'posts': int(round(180 * weight * rnd.uniform(0.5, 1.5))),
            'bids': int(round(46 * weight * rnd.uniform(0.3, 1.8))),
            'spend': round(880 * weight * rnd.uniform(0.6, 1.4), 2),
        })
    rows.sort(key=lambda r: -r['minutes'])
    for i, row in enumerate(rows):
        row['rank'] = i + 1
    return rows


# ==========================================================================
# Aggregation
# ==========================================================================
def _aggregate_series(members: Sequence[Dict[str, List[float]]],
                      dau_by_client: Sequence[List[float]]) -> Dict[str, List[float]]:
    """Roll several accounts into one portfolio row.

    Counts sum; DAU/MAU get an overlap discount (a fan following two artists is
    one person); session length is a DAU-weighted average, not a sum.
    """
    out: Dict[str, List[float]] = {}
    for key in SERIES_KEYS:
        if key in _AVERAGED:
            values = []
            for i in range(WINDOW_DAYS):
                weight = sum(d[i] for d in dau_by_client)
                if weight <= 0:
                    values.append(0.0)
                else:
                    values.append(
                        sum(m[key][i] * d[i] for m, d in zip(members, dau_by_client)) / weight
                    )
            out[key] = values
        else:
            factor = _DEDUPED.get(key, 1.0)
            out[key] = [
                sum(m[key][i] for m in members) * factor for i in range(WINDOW_DAYS)
            ]
    return out


def _merge_locations(rows_by_client):
    merged: Dict[str, Dict[str, object]] = {}
    for rows in rows_by_client:
        for row in rows:
            entry = merged.get(row['city'])
            if entry is None:
                entry = {k: row[k] for k in
                         ('city', 'region', 'country', 'lat', 'lon', 'seed', 'ramp_lag')}
                entry['users'] = 0
                entry['engagement'] = 0
                entry['segments'] = {name: 0 for name in SEGMENT_NAMES}
                merged[row['city']] = entry
            entry['users'] += row['users']
            entry['engagement'] += row['engagement']
            for name in SEGMENT_NAMES:
                entry['segments'][name] += row['segments'][name]
    out = list(merged.values())
    out.sort(key=lambda r: -r['users'])
    return out


def _merge_revenue_mix(mixes):
    out = {}
    for dimension in ('platform', 'revenue_type'):
        totals: Dict[str, float] = {}
        for mix in mixes:
            for row in mix[dimension]:
                totals[row['label']] = totals.get(row['label'], 0.0) + row['revenue']
        out[dimension] = [
            {'label': label, 'revenue': round(value, 2)} for label, value in totals.items()
        ]
    return out


def _merge_lifetime(lifetimes):
    counts = {bucket: 0 for bucket in LIFETIME_BUCKETS}
    for life in lifetimes:
        for row in life['buckets']:
            counts[row['bucket']] += row['members']
    total = sum(counts.values()) or 1
    midpoints = dict(zip(LIFETIME_BUCKETS, [15, 60, 135, 273, 547, 900]))
    mean_days = sum(counts[b] * midpoints[b] for b in LIFETIME_BUCKETS) / total
    running = 0
    median_days = 900
    for bucket in LIFETIME_BUCKETS:
        running += counts[bucket]
        if running >= total / 2:
            median_days = midpoints[bucket]
            break
    return {
        'buckets': [{'bucket': b, 'members': counts[b]} for b in LIFETIME_BUCKETS],
        'mean_days': round(mean_days, 1),
        'median_days': median_days,
        'active_members': total,
    }


# ==========================================================================
# Public API
# ==========================================================================
@lru_cache(maxsize=1)
def get_dataset() -> Dict[str, object]:
    """Build (once per process) the full demo dataset."""
    dates = _date_strings()

    accounts: Dict[str, Dict[str, object]] = {}
    for account in CLIENT_ACCOUNTS:
        rnd = random.Random(f"{SEED}:events:{account['name']}")
        events = _build_events(rnd, int(account['launch_offset']))
        raw = _build_account_series(account, events)
        locations = _build_locations(account, raw)
        accounts[account['name']] = {
            'meta': {
                'name': account['name'],
                'tier': account['tier'],
                'genre': account['genre'],
                'launch_date': (START_DATE + timedelta(days=int(account['launch_offset']))).isoformat(),
            },
            'raw': raw,
            'series': _round_series(raw),
            'events': [{k: e[k] for k in ('kind', 'date', 'magnitude')} for e in events],
            'locations': locations,
            'monthly_ramp': _build_monthly_ramp(raw, dates),
            'revenue_mix': _build_revenue_mix(account, raw),
            'churn': _build_churn(raw, dates),
            'lifetime': _build_lifetime(account, raw),
            'top_users': _build_top_users(account, raw),
        }

    clients: Dict[str, Dict[str, object]] = {}

    for name, bundle in accounts.items():
        clients[name] = {
            'meta': bundle['meta'],
            'series': bundle['series'],
            'events': bundle['events'],
            'locations': bundle['locations'],
            'monthly_ramp': bundle['monthly_ramp'],
            'revenue_mix': bundle['revenue_mix'],
            'churn': bundle['churn'],
            'lifetime': bundle['lifetime'],
            'top_users': bundle['top_users'],
        }

    for agg_name, member_names in AGGREGATES:
        members = [accounts[n]['raw'] for n in member_names]
        dau_by_client = [accounts[n]['raw']['dau'] for n in member_names]
        agg_raw = _aggregate_series(members, dau_by_client)
        agg_locations = _merge_locations([accounts[n]['locations'] for n in member_names])
        # Portfolio events keep their account label so an overlay stays readable.
        agg_events = []
        for n in member_names:
            for event in accounts[n]['events']:
                agg_events.append({**event, 'client': n})
        agg_events.sort(key=lambda e: e['date'])

        top_users = []
        for n in member_names:
            for row in accounts[n]['top_users']:
                top_users.append({**row, 'client': n})
        top_users.sort(key=lambda r: -r['minutes'])
        top_users = top_users[:25]
        for i, row in enumerate(top_users):
            row['rank'] = i + 1

        clients[agg_name] = {
            'meta': {
                'name': agg_name,
                'tier': 'aggregate',
                'genre': f"{len(member_names)} accounts",
                'launch_date': min(accounts[n]['meta']['launch_date'] for n in member_names),
            },
            'series': _round_series(agg_raw),
            'events': agg_events,
            'locations': agg_locations,
            'monthly_ramp': _build_monthly_ramp(agg_raw, dates),
            'revenue_mix': _merge_revenue_mix([accounts[n]['revenue_mix'] for n in member_names]),
            'churn': _build_churn(agg_raw, dates),
            'lifetime': _merge_lifetime([accounts[n]['lifetime'] for n in member_names]),
            'top_users': top_users,
        }

    return {
        'dates': dates,
        'start_date': START_DATE.isoformat(),
        'end_date': END_DATE.isoformat(),
        'clients': clients,
    }


# --------------------------------------------------------------------------
# Windowing / derived views used by both the Dash page and the static twin
# --------------------------------------------------------------------------
def window_indices(dates: Sequence[str], days: int):
    """Index bounds for a trailing-window preset. ``days <= 0`` means all time."""
    if days <= 0:
        return 0, len(dates)
    return max(len(dates) - days, 0), len(dates)


def correlation_matrix(series: Dict[str, List[float]], lo: int, hi: int):
    """Pearson correlation across the correlation metric family for a window."""
    columns = [key for key in CORRELATION_METRICS if key in series]
    sliced = {key: series[key][lo:hi] for key in columns}
    return columns, [
        [round(_pearson(sliced[a], sliced[b]), 3) for b in columns] for a in columns
    ]


def summarize(values: Sequence[float]) -> Dict[str, float]:
    """Mean / min / max / total for a metric window — the quick-diagnostic row a
    reviewer scans before opening the chart."""
    window = list(values)
    if not window:
        return {'mean': 0.0, 'min': 0.0, 'max': 0.0, 'total': 0.0, 'last': 0.0}
    return {
        'mean': sum(window) / len(window),
        'min': min(window),
        'max': max(window),
        'total': sum(window),
        'last': window[-1],
    }


def delta_pct(values: Sequence[float]) -> float:
    """Percent change between the first and second half of a window.

    Used for the KPI trend chips. Comparing halves rather than endpoints keeps a
    single noisy day from flipping the direction of a whole quarter.
    """
    window = [v for v in values]
    if len(window) < 4:
        return 0.0
    mid = len(window) // 2
    first = sum(window[:mid]) / mid
    second = sum(window[mid:]) / (len(window) - mid)
    if first <= 0:
        return 0.0
    return (second - first) / first * 100.0


def resample(dates: Sequence[str], values: Sequence[float], grain: str, how: str = 'sum'):
    """Roll a daily series up to weekly / monthly / quarterly buckets.

    ``how='last'`` is for stock metrics (memberships) where summing days would be
    meaningless; flow metrics (revenue, downloads) sum.
    """
    if grain == 'Daily':
        return list(dates), list(values)

    def key_for(iso: str) -> str:
        year, month, day = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
        if grain == 'Weekly':
            monday = date(year, month, day) - timedelta(days=date(year, month, day).weekday())
            return monday.isoformat()
        if grain == 'Monthly':
            return f'{iso[:7]}-01'
        if grain == 'Quarterly':
            return f'{year}-{3 * ((month - 1) // 3) + 1:02d}-01'
        return f'{year}-01-01'

    buckets: List[str] = []
    out: List[float] = []
    for iso, value in zip(dates, values):
        key = key_for(iso)
        if not buckets or buckets[-1] != key:
            buckets.append(key)
            out.append(0.0)
        if how == 'last':
            out[-1] = value
        else:
            out[-1] += value
    return buckets, out


def linear_fit(xs: Sequence[float], ys: Sequence[float]):
    """Ordinary least squares slope/intercept plus r-squared for the regression
    overlay on the relationship scatter."""
    n = len(xs)
    if n < 3:
        return 0.0, 0.0, 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    if var_x <= 0:
        return 0.0, mean_y, 0.0
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / var_x
    intercept = mean_y - slope * mean_x
    r = _pearson(xs, ys)
    return slope, intercept, r * r


def events_in_window(events, dates: Sequence[str], lo: int, hi: int):
    """Events falling inside a rendered date window, for chart overlays."""
    if lo >= hi or not dates:
        return []
    start, end = dates[lo], dates[hi - 1]
    return [event for event in events if start <= event['date'] <= end]
