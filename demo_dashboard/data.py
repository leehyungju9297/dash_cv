"""Deterministic synthetic dataset for the Tidepool Commerce Analytics demo.

One seeded generator produces two years of daily retail activity for a portfolio
of five invented direct-to-consumer brands, plus everything the dashboard reads
off it: shipping geography, category mix, acquisition-source attribution,
monthly acquisition cohorts, customer value parameters, discount-code mix and
returns. Portfolio rows ("All Brands", "Flagship Brands", "Emerging Brands") are
rolled up from the brands rather than generated separately, so a rollup always
reconciles with its members.

Two design rules run through the whole module:

  * **Revenue is never generated directly.** Visits, conversion rate and average
    order value are the primitives; orders are visits x conversion and revenue is
    orders x AOV. That is what makes the driver decomposition honest — the walk
    it draws is arithmetic, not an attribution model.

  * **Nothing is drawn per customer.** Individual points on the map and in the
    value scatter are generated from compact per-market and per-brand parameters
    by a PRNG that Python and JavaScript reproduce bit-for-bit (see ``geo``), so
    the exported payload stays small and both builds draw the identical cloud.

Standard library only, and the window is fixed rather than relative to today, so
the dataset is byte-stable across runs and across machines.

Every brand, customer, order, market total and figure here is invented for this
portfolio. No real name, record or value appears anywhere.
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta
from typing import Dict, List, Sequence, Tuple

from demo_dashboard.assumptions import (
    BASE_BASKET,
    BASE_CONVERSION,
    BASE_RETURN_RATE,
    CATEGORY_RETURN_MULTIPLIER,
    CHANNEL_AOV_INDEX,
    CHANNEL_MIX,
    COHORT_QUALITY_RANGE,
    CONVERSION_CEILING,
    CONVERSION_FLOOR,
    DAILY_OVER_MONTHLY,
    DISCOUNT_DEPTH,
    DISCOUNT_MIX,
    MARKET_AOV_SPREAD,
    MARKET_ZIPF_ALPHA,
    MARKETING_CADENCE,
    MONTH_AOV,
    MONTH_VISITS,
    NEW_CUSTOMER_SHARE_EARLY,
    NEW_CUSTOMER_SHARE_MATURE,
    ORDERS_PER_CUSTOMER,
    REPEAT_DECAY,
    RETENTION_CURVE,
    RETURN_LAG_DAYS,
    RETURN_REASON_MIX,
    SOURCE_CAC,
    SOURCE_MIX,
    SOURCE_VALUE_INDEX,
    TRADING_DAYS,
    VALUE_MIN_SPEND,
    VALUE_PARETO_ALPHA,
    WEEKDAY_AOV,
    WEEKDAY_CONVERSION,
    WEEKDAY_VISITS,
)
from demo_dashboard.config import (
    AGGREGATES,
    BRAND_ACCOUNTS,
    BRAND_NAMES,
    CATEGORIES,
    CATEGORY_NAMES,
    CHANNEL_NAMES,
    DISCOUNT_CODES,
    RETURN_REASON_NAMES,
    SOURCE_NAMES,
)
from demo_dashboard.geo import string_seed


# The window is fixed rather than relative to "today" so the demo is byte-stable.
END_DATE = date(2026, 6, 30)
WINDOW_DAYS = 730
START_DATE = END_DATE - timedelta(days=WINDOW_DAYS - 1)

SEED = 20260630

# Primitive daily series. Everything else the dashboard shows is derived from
# these by DERIVED below, which keeps rollups correct for free: summing visits
# and orders across brands and *then* dividing gives the right blended
# conversion rate, where averaging per-brand rates would not.
SERIES_KEYS = [
    'visits', 'orders', 'revenue', 'units', 'customers', 'new_customers',
    'repeat_customers', 'monthly_customers', 'returns', 'return_value',
    'campaigns', 'email_sends', 'promotions', 'discount_value',
]

# key -> (numerator, denominator). Computed after aggregation, never summed.
DERIVED: Dict[str, Tuple[str, str]] = {
    'aov': ('revenue', 'orders'),
    'conversion': ('orders', 'visits'),
    'return_rate': ('returns', 'orders'),
    'discount_rate': ('discount_value', 'revenue'),
    'basket': ('units', 'orders'),
}

# Summing daily ordering customers across brands double-counts the shoppers who
# buy from two of them; a portfolio rollup applies an overlap discount instead.
_DEDUPED = {'customers': 0.94, 'monthly_customers': 0.88}


# --------------------------------------------------------------------------
# Promotion calendar
# --------------------------------------------------------------------------
# Each kind names the funnel terms it moves and how hard. Note that several move
# them in opposite directions — a flash sale buys traffic and conversion at the
# cost of basket size — which is the whole reason the promotion view compares
# revenue rather than orders.
#   amp    peak multiplier added at the event date (negative = suppressed)
#   decay  days for the lift to fall to ~1/e of its peak
EVENT_KINDS: Dict[str, Dict[str, object]] = {
    'Flash Sale': {
        'amp': {'visits': 1.45, 'conversion': 0.92, 'aov': -0.19, 'email_sends': 1.2},
        'decay': 2.0, 'color': '#C4633F',
    },
    'Seasonal Campaign': {
        'amp': {'visits': 0.88, 'conversion': 0.24, 'aov': 0.05, 'campaigns': 1.5},
        'decay': 12.0, 'color': '#6D3C29',
    },
    'New Collection': {
        'amp': {'visits': 0.72, 'conversion': 0.16, 'aov': 0.15, 'campaigns': 1.1},
        'decay': 16.0, 'color': '#4E6B4D',
    },
    'Email Blast': {
        'amp': {'visits': 0.54, 'conversion': 0.31, 'email_sends': 2.4},
        'decay': 3.0, 'color': '#CA9038',
    },
    'Marketplace Feature': {
        'amp': {'visits': 1.15, 'conversion': -0.11, 'aov': -0.07},
        'decay': 5.0, 'color': '#8A5468',
    },
    'Loyalty Push': {
        'amp': {'visits': 0.22, 'conversion': 0.34, 'aov': 0.13, 'email_sends': 1.0},
        'decay': 8.0, 'color': '#B79A6B',
    },
}

EVENT_ORDER = list(EVENT_KINDS)

# What each kind puts on the marketing counters the day it runs. Without this,
# the calendar overlay and the marketing metrics drift apart: a flash sale fires
# on ~4% of days, so a "Flash Sale" marker would usually sit over a flat zero.
EVENT_ACTIONS: Dict[str, Dict[str, int]] = {
    'Flash Sale': {'promotions': 1, 'email_sends': 2},
    'Seasonal Campaign': {'campaigns': 2, 'email_sends': 1},
    'New Collection': {'campaigns': 1, 'email_sends': 1},
    'Email Blast': {'email_sends': 3},
    'Marketplace Feature': {'campaigns': 1},
    'Loyalty Push': {'campaigns': 1, 'email_sends': 2},
}


# --------------------------------------------------------------------------
# Geography
# --------------------------------------------------------------------------
# Shipping markets in order volume rank. The weights are not written by hand:
# they follow the rank^-a curve in assumptions.MARKET_ZIPF_ALPHA, which gives the
# long flat tail a national retailer has instead of three metros holding
# everything.
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
    """Attach the rank^-a order weight to each shipping market."""
    return [
        (city, region, country, lat, lon, (rank + 1) ** -MARKET_ZIPF_ALPHA)
        for rank, (city, region, country, lat, lon) in enumerate(CITY_TABLE_RANKED)
    ]


CITY_TABLE = _ranked_city_table()


# ==========================================================================
# Helpers
# ==========================================================================
def _date_strings() -> List[str]:
    return [(START_DATE + timedelta(days=i)).isoformat() for i in range(WINDOW_DAYS)]


def _weekly_shape(rnd: random.Random, base: Sequence[float]) -> List[float]:
    """Weekday multipliers for one funnel term, jittered per brand."""
    return [value * rnd.uniform(0.97, 1.03) for value in base]


def _poisson(rnd: random.Random, lam: float) -> int:
    """Knuth's sampler. Marketing actions are counts of things a brand shipped
    that day, so they are drawn as counts rather than scaled from order volume."""
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


def _pareto(rnd: random.Random, alpha: float, minimum: float) -> float:
    """Inverse-transform draw from a Pareto tail."""
    return minimum / (rnd.random() ** (1.0 / alpha))


def _event_multiplier(events, day_index: int, term: str) -> float:
    """Combined lift on ``term`` at ``day_index`` from every nearby promotion.

    The kernel is asymmetric on purpose: anticipation before the date is short
    and shallow, the lift is instant, and the tail decays over days. A symmetric
    bell would imply shoppers reacted before the sale was announced.
    """
    lift = 0.0
    for event in events:
        amp = EVENT_KINDS[event['kind']]['amp'].get(term)
        if not amp:
            continue
        delta = day_index - event['day_index']
        if delta < -4 or delta > 60:
            continue
        decay = EVENT_KINDS[event['kind']]['decay']
        kernel = math.exp(-delta / decay) if delta >= 0 else math.exp(delta * 1.4)
        lift += amp * event['magnitude'] * kernel
    return max(1.0 + lift, 0.05)


def _scheduled_actions(events, day_index: int) -> Dict[str, int]:
    """Marketing actions the calendar puts on this exact day."""
    out = {'campaigns': 0, 'email_sends': 0, 'promotions': 0}
    for event in events:
        if event['day_index'] != day_index:
            continue
        for key, count in EVENT_ACTIONS.get(event['kind'], {}).items():
            out[key] += count
    return out


def _seasonal(day: date, curve: Sequence[float]) -> float:
    """Monthly seasonality, interpolated so months do not step at midnight."""
    days_in_month = (date(day.year + (day.month == 12), day.month % 12 + 1, 1)
                     - date(day.year, day.month, 1)).days
    position = (day.day - 1) / days_in_month
    here = curve[day.month - 1]
    nxt = curve[day.month % 12]
    return here + (nxt - here) * position


def _trading_day_lift(day: date, term: str) -> float:
    """Named trading peaks, which sit on top of the monthly curve."""
    lift = 1.0
    for window in TRADING_DAYS:
        try:
            start = date(day.year, int(window['month']), int(window['day']))
        except ValueError:
            continue
        delta = (day - start).days
        if 0 <= delta < int(window['span']):
            # Triangular within the window: the first day is the peak.
            weight = 1.0 - delta / float(window['span'])
            factor = float(window.get(term, 1.0))
            lift *= 1.0 + (factor - 1.0) * weight
    return lift


def _build_events(rnd: random.Random, launch: int) -> List[Dict[str, object]]:
    """A plausible promotion calendar for one brand."""
    events: List[Dict[str, object]] = []
    day = launch + rnd.randint(10, 32)
    while day < WINDOW_DAYS - 5:
        kind = rnd.choices(EVENT_ORDER, weights=[2.4, 1.4, 1.2, 2.8, 1.0, 1.3])[0]
        events.append({
            'kind': kind,
            'day_index': day,
            'date': (START_DATE + timedelta(days=day)).isoformat(),
            'magnitude': round(rnd.uniform(0.55, 1.35), 3),
        })
        day += rnd.randint(11, 34)
    return events


def _rolling_monthly_customers(daily: Sequence[float], window: int = 30) -> List[float]:
    """Approximate monthly actives from daily ordering customers.

    Real monthly actives are a distinct count. Summing 30 days of buyers would
    count a customer who orders weekly four times, so the sum is compressed to
    land the daily/monthly ratio near assumptions.DAILY_OVER_MONTHLY. Unlike an
    app's DAU, a store's daily buyers barely overlap, so the compression is mild.
    """
    out: List[float] = []
    running = 0.0
    for i, value in enumerate(daily):
        running += value
        if i >= window:
            running -= daily[i - window]
        span = min(i + 1, window)
        out.append((running / span) / DAILY_OVER_MONTHLY)
    return out


# ==========================================================================
# Per-brand generation
# ==========================================================================
def _build_brand_series(account: Dict[str, object], events) -> Dict[str, List[float]]:
    """Daily series for one brand.

    Visits, conversion and AOV are generated; orders, revenue, units, customers
    and returns fall out of them. Order of operations matters here — returns are
    a lagged function of *orders*, so they can only be filled in once the whole
    order series exists.
    """
    rnd = random.Random(SEED ^ string_seed(str(account['name'])))
    scale = float(account['scale'])
    launch = int(account['launch_offset'])

    weekday_visits = _weekly_shape(rnd, WEEKDAY_VISITS)
    weekday_conversion = _weekly_shape(rnd, WEEKDAY_CONVERSION)
    weekday_aov = _weekly_shape(rnd, WEEKDAY_AOV)

    # A brand's traffic follows a logistic ramp from launch: slow, then steep,
    # then settling. ``ceiling`` is where it lands, not where it starts.
    #
    # The absolute level is chosen, not arbitrary: it puts the portfolio at a few
    # hundred thousand orders across the window. That is a credible size for a
    # five-brand DTC group, and it keeps the individual-order map at a marker
    # count MapLibre draws instantly — a portfolio ten times larger would be no
    # more interesting and would make the map the slowest thing on the page.
    ceiling = 8_000 * scale
    steepness = 5.4 / max(WINDOW_DAYS - launch, 60)
    midpoint = launch + (WINDOW_DAYS - launch) * rnd.uniform(0.30, 0.46)

    base_conversion = BASE_CONVERSION * rnd.uniform(0.86, 1.16)
    base_aov = float(account['aov'])
    basket_bias = float(next(c['basket'] for c in CATEGORIES
                             if c['name'] == account['category'])) / BASE_BASKET

    series: Dict[str, List[float]] = {key: [] for key in SERIES_KEYS}
    orders_series: List[float] = []

    for index in range(WINDOW_DAYS):
        day = START_DATE + timedelta(days=index)
        weekday = day.weekday()

        if index < launch:
            for key in SERIES_KEYS:
                series[key].append(0.0)
            orders_series.append(0.0)
            continue

        ramp = 1.0 / (1.0 + math.exp(-steepness * (index - midpoint)))

        visits = (ceiling * ramp
                  * weekday_visits[weekday]
                  * _seasonal(day, MONTH_VISITS)
                  * _trading_day_lift(day, 'visits')
                  * _event_multiplier(events, index, 'visits')
                  * rnd.uniform(0.90, 1.10))

        conversion = (base_conversion
                      * weekday_conversion[weekday]
                      * _trading_day_lift(day, 'conversion')
                      * _event_multiplier(events, index, 'conversion')
                      * rnd.uniform(0.93, 1.07))
        conversion = min(max(conversion, CONVERSION_FLOOR), CONVERSION_CEILING)

        aov = (base_aov
               * weekday_aov[weekday]
               * _seasonal(day, MONTH_AOV)
               * _trading_day_lift(day, 'aov')
               * _event_multiplier(events, index, 'aov')
               * rnd.uniform(0.95, 1.05))

        orders = visits * conversion
        revenue = orders * aov
        units = orders * BASE_BASKET * basket_bias * rnd.uniform(0.94, 1.06)

        customers = orders / ORDERS_PER_CUSTOMER
        maturity = min((index - launch) / max(WINDOW_DAYS - launch, 1), 1.0)
        new_share = (NEW_CUSTOMER_SHARE_EARLY
                     + (NEW_CUSTOMER_SHARE_MATURE - NEW_CUSTOMER_SHARE_EARLY) * maturity)
        new_customers = customers * new_share * rnd.uniform(0.94, 1.06)

        scheduled = _scheduled_actions(events, index)
        actions = {}
        for key, cadence in MARKETING_CADENCE.items():
            lam = cadence * _event_multiplier(events, index, key)
            actions[key] = _poisson(rnd, lam) + scheduled.get(key, 0)

        # Weighted mean discount depth, then the money it took off the order.
        depth = sum(DISCOUNT_MIX[code] * DISCOUNT_DEPTH[code] for code in DISCOUNT_CODES)
        depth *= _event_multiplier(events, index, 'conversion') ** 0.35

        series['visits'].append(visits)
        series['orders'].append(orders)
        series['revenue'].append(revenue)
        series['units'].append(units)
        series['customers'].append(customers)
        series['new_customers'].append(new_customers)
        series['repeat_customers'].append(max(customers - new_customers, 0.0))
        series['monthly_customers'].append(0.0)          # filled below
        series['returns'].append(0.0)                    # filled below
        series['return_value'].append(0.0)
        series['campaigns'].append(float(actions['campaigns']))
        series['email_sends'].append(float(actions['email_sends']))
        series['promotions'].append(float(actions['promotions']))
        series['discount_value'].append(revenue * depth)
        orders_series.append(orders)

    series['monthly_customers'] = _rolling_monthly_customers(series['customers'])

    # Returns land RETURN_LAG_DAYS after the order that produced them. Computing
    # them against same-day orders would put the return spike on the sale day
    # and make the return rate look flat through it.
    category_weight = CATEGORY_RETURN_MULTIPLIER.get(str(account['category']), 1.0)
    rate = BASE_RETURN_RATE * (0.55 + 0.45 * category_weight)
    for index in range(WINDOW_DAYS):
        source = index - RETURN_LAG_DAYS
        if source < 0:
            continue
        returned = orders_series[source] * rate * rnd.uniform(0.82, 1.18)
        series['returns'][index] = returned
        series['return_value'][index] = returned * series['revenue'][source] / max(
            orders_series[source], 1e-9)

    return series


def _round_series(series: Dict[str, List[float]]) -> Dict[str, List[float]]:
    """Counts become integers; money keeps cents."""
    money = {'revenue', 'return_value', 'discount_value'}
    out: Dict[str, List[float]] = {}
    for key, values in series.items():
        if key in money:
            out[key] = [round(v, 2) for v in values]
        else:
            out[key] = [float(round(v)) for v in values]
    return out


def _build_locations(account: Dict[str, object], series: Dict[str, List[float]]):
    """Per-market order totals, revenue and average order value.

    A market's share of orders comes from the rank curve, perturbed per brand so
    two brands do not have identical geography. Average order value varies across
    markets independently of volume — that independence is the point of the dual
    encoding on the map, which would say nothing if size and color agreed.
    """
    rnd = random.Random(SEED ^ string_seed('geo:' + str(account['name'])))
    total_orders = sum(series['orders'])
    total_revenue = sum(series['revenue'])
    if total_orders <= 0:
        return []

    portfolio_aov = total_revenue / total_orders
    weights = []
    for city, region, country, lat, lon, weight in CITY_TABLE:
        weights.append(weight * rnd.uniform(0.55, 1.55))
    weight_total = sum(weights)

    rows = []
    for (city, region, country, lat, lon, _), weight in zip(CITY_TABLE, weights):
        share = weight / weight_total
        orders = int(round(total_orders * share))
        if orders < 1:
            continue
        aov = portfolio_aov * (1.0 + rnd.uniform(-MARKET_AOV_SPREAD, MARKET_AOV_SPREAD))
        rows.append({
            'city': city,
            'region': region,
            'country': country,
            'lat': lat,
            'lon': lon,
            'orders': orders,
            'revenue': round(orders * aov, 2),
            'aov': round(aov, 2),
            # Stable per-market seed: the marker cloud must not move between runs
            # or between the two builds.
            'seed': string_seed(f'{account["name"]}|{city}|{region}') & 0xFFFFFFFF,
            # Where in the brand's life this market opened up, 0-1.
            'ramp_lag': round(rnd.uniform(0.0, 0.55) ** 1.5, 4),
        })
    rows.sort(key=lambda r: -r['orders'])
    return rows


def _build_monthly(series: Dict[str, List[float]], dates: List[str]):
    """Monthly totals, plus the cumulative order curve the growth map replays."""
    buckets: Dict[str, Dict[str, float]] = {}
    order = []
    for index, iso in enumerate(dates):
        period = iso[:7]
        if period not in buckets:
            buckets[period] = {key: 0.0 for key in SERIES_KEYS}
            order.append(period)
        for key in SERIES_KEYS:
            buckets[period][key] += series[key][index]

    total = sum(series['orders']) or 1.0
    running = 0.0
    out = []
    for period in order:
        running += buckets[period]['orders']
        row = {'period': period, 'frac': round(running / total, 6)}
        for key in SERIES_KEYS:
            row[key] = round(buckets[period][key], 2)
        out.append(row)
    return out


def _build_category_mix(account: Dict[str, object], monthly: List[Dict[str, float]]):
    """Revenue by product category, per month.

    The brand's home category leads, but its lead erodes as the brand broadens —
    a range extension is exactly the kind of thing a category view should show.
    """
    rnd = random.Random(SEED ^ string_seed('cat:' + str(account['name'])))
    home = str(account['category'])
    drift = {name: rnd.uniform(-0.35, 0.55) for name in CATEGORY_NAMES}

    rows = []
    span = max(len(monthly) - 1, 1)
    for index, month in enumerate(monthly):
        position = index / span
        weights = {}
        for name in CATEGORY_NAMES:
            base = 2.6 if name == home else 0.55
            base *= 1.0 + drift[name] * position
            weights[name] = max(base * rnd.uniform(0.88, 1.12), 0.04)
        total = sum(weights.values())
        revenue = month['revenue']
        rows.append({
            'period': month['period'],
            'revenue': {name: round(revenue * weights[name] / total, 2)
                        for name in CATEGORY_NAMES},
        })
    return rows


def _build_channel_mix(account: Dict[str, object], monthly: List[Dict[str, float]]):
    """Orders and revenue by order channel, per month."""
    rnd = random.Random(SEED ^ string_seed('chan:' + str(account['name'])))
    bias = {name: rnd.uniform(0.8, 1.25) for name in CHANNEL_NAMES}

    rows = []
    span = max(len(monthly) - 1, 1)
    for index, month in enumerate(monthly):
        position = index / span
        weights = {}
        for name in CHANNEL_NAMES:
            weight = CHANNEL_MIX[name] * bias[name]
            # App share grows over a brand's life at the expense of web.
            if name == 'Mobile App':
                weight *= 1.0 + 0.65 * position
            elif name == 'Web':
                weight *= 1.0 - 0.22 * position
            weights[name] = max(weight, 0.01)
        total = sum(weights.values())
        orders = {name: month['orders'] * weights[name] / total for name in CHANNEL_NAMES}
        revenue = {name: orders[name] * CHANNEL_AOV_INDEX[name] for name in CHANNEL_NAMES}
        revenue_total = sum(revenue.values()) or 1.0
        rows.append({
            'period': month['period'],
            'orders': {name: round(orders[name]) for name in CHANNEL_NAMES},
            'revenue': {name: round(month['revenue'] * revenue[name] / revenue_total, 2)
                        for name in CHANNEL_NAMES},
        })
    return rows


def _build_sources(account: Dict[str, object], monthly: List[Dict[str, float]]):
    """Acquisition-source attribution: who was acquired where, and what they were
    worth afterwards.

    First-order revenue is attributed to the source that acquired the customer;
    repeat revenue is attributed to the same source, which is what makes the
    difference between a cheap source and a good one visible at all.
    """
    rnd = random.Random(SEED ^ string_seed('src:' + str(account['name'])))
    bias = {name: rnd.uniform(0.82, 1.22) for name in SOURCE_NAMES}
    weights = {name: SOURCE_MIX[name] * bias[name] for name in SOURCE_NAMES}
    total_weight = sum(weights.values())

    new_customers = sum(m['new_customers'] for m in monthly)
    revenue = sum(m['revenue'] for m in monthly)
    orders = sum(m['orders'] for m in monthly)

    # Split revenue by source using acquisition share weighted by lifetime value.
    value_weights = {name: weights[name] * SOURCE_VALUE_INDEX[name] for name in SOURCE_NAMES}
    value_total = sum(value_weights.values())

    rows = []
    for name in SOURCE_NAMES:
        share = weights[name] / total_weight
        value_share = value_weights[name] / value_total
        acquired = new_customers * share
        source_revenue = revenue * value_share
        # Repeat share rises with source quality: a referral customer comes back.
        repeat_share = min(0.18 + 0.30 * SOURCE_VALUE_INDEX[name], 0.74)
        rows.append({
            'source': name,
            'new_customers': int(round(acquired)),
            'orders': int(round(orders * value_share)),
            'revenue': round(source_revenue, 2),
            'first_order_revenue': round(source_revenue * (1 - repeat_share), 2),
            'repeat_revenue': round(source_revenue * repeat_share, 2),
            'cac': SOURCE_CAC[name],
            'spend': round(acquired * SOURCE_CAC[name], 2),
        })
    rows.sort(key=lambda r: -r['revenue'])
    return rows


def _build_cohorts(account: Dict[str, object], monthly: List[Dict[str, float]]):
    """Monthly acquisition cohorts and their repeat rate by months-since.

    The result is a triangle, not a rectangle: a cohort acquired last month has
    exactly one observed month. Filling the unobserved cells with zero would draw
    a cliff that looks like collapsing retention, so they stay ``None``.
    """
    rnd = random.Random(SEED ^ string_seed('coh:' + str(account['name'])))
    periods = [m['period'] for m in monthly]
    sizes = [int(round(m['new_customers'])) for m in monthly]
    span = len(periods)

    quality_low, quality_high = COHORT_QUALITY_RANGE
    retention: List[List[float]] = []
    for index in range(span):
        # Cohorts acquired into a discount rush retain worse. Months 10-11 of the
        # calendar year are the Q4 rush.
        month_number = int(periods[index][5:7])
        seasonal_penalty = 0.82 if month_number in (11, 12) else 1.0
        quality = rnd.uniform(quality_low, quality_high) * seasonal_penalty

        row: List[float] = []
        observable = span - index
        for k in range(span):
            if k >= observable or sizes[index] <= 0:
                row.append(None)
                continue
            base = RETENTION_CURVE[k] if k < len(RETENTION_CURVE) else RETENTION_CURVE[-1]
            value = 1.0 if k == 0 else base * quality * rnd.uniform(0.92, 1.08)
            row.append(round(min(value, 1.0), 4))
        retention.append(row)

    return {'periods': periods, 'sizes': sizes, 'retention': retention}


def _build_value_params(account: Dict[str, object], monthly: List[Dict[str, float]]):
    """Compact parameters the RFM scatter is generated from.

    The scatter needs thousands of customers. Shipping thousands of rows per
    brand to the static build would dominate the payload, so the points are
    *generated* in both languages from these few numbers instead — the same
    trick the map markers use.
    """
    orders = sum(m['orders'] for m in monthly)
    revenue = sum(m['revenue'] for m in monthly)
    customers = sum(m['new_customers'] for m in monthly)
    if customers <= 0:
        return None
    return {
        'sample': 1400,
        'customers': int(round(customers)),
        'mean_orders': round(orders / customers, 4),
        'mean_spend': round(revenue / customers, 2),
        'alpha': VALUE_PARETO_ALPHA,
        'min_spend': VALUE_MIN_SPEND,
        'repeat_decay': REPEAT_DECAY,
        'window_days': WINDOW_DAYS,
        'seed': string_seed('rfm:' + str(account['name'])) & 0xFFFFFFFF,
    }


def _build_discount_mix(account: Dict[str, object], monthly: List[Dict[str, float]]):
    """Order and revenue share by discount code."""
    rnd = random.Random(SEED ^ string_seed('disc:' + str(account['name'])))
    orders = sum(m['orders'] for m in monthly)
    revenue = sum(m['revenue'] for m in monthly)

    weights = {code: DISCOUNT_MIX[code] * rnd.uniform(0.85, 1.18) for code in DISCOUNT_CODES}
    total = sum(weights.values())
    rows = []
    for code in DISCOUNT_CODES:
        share = weights[code] / total
        code_orders = orders * share
        # A deeper code buys a bigger basket but gives back more than it gains.
        basket_index = 1.0 + DISCOUNT_DEPTH[code] * 0.9
        gross = revenue * share * basket_index
        rows.append({
            'code': code,
            'orders': int(round(code_orders)),
            'revenue': round(gross * (1 - DISCOUNT_DEPTH[code]), 2),
            'discount': round(gross * DISCOUNT_DEPTH[code], 2),
            'depth': DISCOUNT_DEPTH[code],
        })
    return rows


def _build_returns(account: Dict[str, object], monthly: List[Dict[str, float]],
                   category_mix: List[Dict[str, object]]):
    """Return rate by category and the reason mix behind it."""
    rnd = random.Random(SEED ^ string_seed('ret:' + str(account['name'])))
    revenue_by_category = {name: 0.0 for name in CATEGORY_NAMES}
    for month in category_mix:
        for name, value in month['revenue'].items():
            revenue_by_category[name] += value

    by_category = []
    for name in CATEGORY_NAMES:
        rate = BASE_RETURN_RATE * CATEGORY_RETURN_MULTIPLIER[name] * rnd.uniform(0.9, 1.1)
        value = revenue_by_category[name]
        by_category.append({
            'category': name,
            'rate': round(rate, 5),
            'revenue': round(value, 2),
            'returned_value': round(value * rate, 2),
        })

    total_returned = sum(row['returned_value'] for row in by_category) or 1.0
    by_reason = []
    weights = {name: RETURN_REASON_MIX[name] * rnd.uniform(0.88, 1.14)
               for name in RETURN_REASON_NAMES}
    weight_total = sum(weights.values())
    for name in RETURN_REASON_NAMES:
        share = weights[name] / weight_total
        by_reason.append({
            'reason': name,
            'share': round(share, 5),
            'value': round(total_returned * share, 2),
        })

    return {'by_category': by_category, 'by_reason': by_reason}


# ==========================================================================
# Portfolio rollups
# ==========================================================================
def _aggregate_series(members: Sequence[Dict[str, List[float]]]) -> Dict[str, List[float]]:
    """Sum member series, discounting the metrics that double-count shoppers."""
    if not members:
        return {key: [0.0] * WINDOW_DAYS for key in SERIES_KEYS}
    out: Dict[str, List[float]] = {}
    for key in SERIES_KEYS:
        totals = [0.0] * WINDOW_DAYS
        for series in members:
            values = series[key]
            for index in range(WINDOW_DAYS):
                totals[index] += values[index]
        factor = _DEDUPED.get(key, 1.0)
        out[key] = [round(value * factor, 2) for value in totals]
    return out


def _merge_locations(rows_by_brand: Sequence[Sequence[Dict]]) -> List[Dict]:
    """Combine per-brand market rows. Average order value re-blends by weight —
    averaging the averages would over-weight the smallest markets."""
    merged: Dict[str, Dict] = {}
    for rows in rows_by_brand:
        for row in rows:
            key = f'{row["city"]}|{row["region"]}'
            entry = merged.get(key)
            if entry is None:
                entry = dict(row)
                merged[key] = entry
            else:
                entry['orders'] += row['orders']
                entry['revenue'] = round(entry['revenue'] + row['revenue'], 2)
    out = []
    for entry in merged.values():
        entry['aov'] = round(entry['revenue'] / max(entry['orders'], 1), 2)
        out.append(entry)
    out.sort(key=lambda r: -r['orders'])
    return out


def _merge_keyed(rows_by_brand, key_field: str, sum_fields: Sequence[str],
                 carry: Sequence[str] = ()) -> List[Dict]:
    """Sum a list-of-dicts dimension across brands, keyed on ``key_field``."""
    merged: Dict[str, Dict] = {}
    order: List[str] = []
    for rows in rows_by_brand:
        for row in rows:
            name = row[key_field]
            entry = merged.get(name)
            if entry is None:
                entry = {key_field: name}
                entry.update({field: 0.0 for field in sum_fields})
                for field in carry:
                    entry[field] = row[field]
                merged[name] = entry
                order.append(name)
            for field in sum_fields:
                entry[field] += row[field]
    return [merged[name] for name in order]


def _merge_monthly(monthly_by_brand) -> List[Dict[str, float]]:
    buckets: Dict[str, Dict[str, float]] = {}
    order: List[str] = []
    for monthly in monthly_by_brand:
        for row in monthly:
            period = row['period']
            if period not in buckets:
                buckets[period] = {key: 0.0 for key in SERIES_KEYS}
                order.append(period)
            for key in SERIES_KEYS:
                buckets[period][key] += row[key]
    order.sort()
    total = sum(buckets[p]['orders'] for p in order) or 1.0
    running = 0.0
    out = []
    for period in order:
        running += buckets[period]['orders']
        row = {'period': period, 'frac': round(running / total, 6)}
        for key in SERIES_KEYS:
            row[key] = round(buckets[period][key], 2)
        out.append(row)
    return out


def _merge_monthly_dimension(rows_by_brand, field: str) -> List[Dict[str, object]]:
    """Combine a per-month, per-category (or per-channel) breakdown."""
    buckets: Dict[str, Dict[str, float]] = {}
    order: List[str] = []
    for rows in rows_by_brand:
        for row in rows:
            period = row['period']
            if period not in buckets:
                buckets[period] = {}
                order.append(period)
            for name, value in row[field].items():
                buckets[period][name] = buckets[period].get(name, 0.0) + value
    order.sort()
    return [{'period': period,
             field: {name: round(value, 2) for name, value in buckets[period].items()}}
            for period in order]


def _merge_cohorts(cohorts_by_brand) -> Dict[str, object]:
    """Combine cohort triangles by weighting each brand's retention by its cohort
    size — the portfolio repeat rate is a weighted mean, not a mean of means."""
    periods: List[str] = []
    for cohort in cohorts_by_brand:
        for period in cohort['periods']:
            if period not in periods:
                periods.append(period)
    periods.sort()
    index_of = {period: i for i, period in enumerate(periods)}
    span = len(periods)

    sizes = [0.0] * span
    weighted = [[0.0] * span for _ in range(span)]
    weights = [[0.0] * span for _ in range(span)]

    for cohort in cohorts_by_brand:
        for local, period in enumerate(cohort['periods']):
            row_index = index_of[period]
            size = cohort['sizes'][local]
            sizes[row_index] += size
            for k, value in enumerate(cohort['retention'][local]):
                if value is None or size <= 0:
                    continue
                weighted[row_index][k] += value * size
                weights[row_index][k] += size

    retention = [
        [round(weighted[r][k] / weights[r][k], 4) if weights[r][k] > 0 else None
         for k in range(span)]
        for r in range(span)
    ]
    return {'periods': periods, 'sizes': [int(round(s)) for s in sizes],
            'retention': retention}


def _merge_value_params(params_by_brand) -> Dict[str, object]:
    live = [p for p in params_by_brand if p]
    if not live:
        return None
    customers = sum(p['customers'] for p in live)
    return {
        'sample': 1800,
        'customers': customers,
        'mean_orders': round(sum(p['mean_orders'] * p['customers'] for p in live) / customers, 4),
        'mean_spend': round(sum(p['mean_spend'] * p['customers'] for p in live) / customers, 2),
        'alpha': VALUE_PARETO_ALPHA,
        'min_spend': VALUE_MIN_SPEND,
        'repeat_decay': REPEAT_DECAY,
        'window_days': WINDOW_DAYS,
        'seed': live[0]['seed'] ^ len(live),
    }


def _merge_returns(returns_by_brand) -> Dict[str, object]:
    by_category = _merge_keyed(
        [r['by_category'] for r in returns_by_brand], 'category',
        ('revenue', 'returned_value'))
    for row in by_category:
        row['rate'] = round(row['returned_value'] / max(row['revenue'], 1e-9), 5)
        row['revenue'] = round(row['revenue'], 2)
        row['returned_value'] = round(row['returned_value'], 2)

    by_reason = _merge_keyed([r['by_reason'] for r in returns_by_brand], 'reason', ('value',))
    total = sum(row['value'] for row in by_reason) or 1.0
    for row in by_reason:
        row['share'] = round(row['value'] / total, 5)
        row['value'] = round(row['value'], 2)
    return {'by_category': by_category, 'by_reason': by_reason}


# ==========================================================================
# Public API
# ==========================================================================
_CACHE: Dict[str, object] = {}


def get_dataset() -> Dict[str, object]:
    """Build (once) and return the whole synthetic dataset."""
    if _CACHE:
        return _CACHE

    dates = _date_strings()
    bundles: Dict[str, Dict[str, object]] = {}

    for account in BRAND_ACCOUNTS:
        name = str(account['name'])
        events = _build_events(random.Random(SEED ^ string_seed('cal:' + name)),
                               int(account['launch_offset']))
        series = _round_series(_build_brand_series(account, events))
        monthly = _build_monthly(series, dates)
        category_mix = _build_category_mix(account, monthly)
        bundles[name] = {
            'name': name,
            'tier': account['tier'],
            'category': account['category'],
            'series': series,
            'events': events,
            'monthly': monthly,
            'locations': _build_locations(account, series),
            'category_mix': category_mix,
            'channel_mix': _build_channel_mix(account, monthly),
            'sources': _build_sources(account, monthly),
            'cohorts': _build_cohorts(account, monthly),
            'value_params': _build_value_params(account, monthly),
            'discounts': _build_discount_mix(account, monthly),
            'returns': _build_returns(account, monthly, category_mix),
        }

    for label, members in AGGREGATES:
        parts = [bundles[name] for name in members if name in bundles]
        monthly = _merge_monthly([p['monthly'] for p in parts])
        bundles[label] = {
            'name': label,
            'tier': 'portfolio',
            'category': None,
            'series': _aggregate_series([p['series'] for p in parts]),
            # A portfolio calendar is every brand's calendar, tagged by brand.
            'events': sorted(
                [dict(event, brand=p['name']) for p in parts for event in p['events']],
                key=lambda e: e['day_index']),
            'monthly': monthly,
            'locations': _merge_locations([p['locations'] for p in parts]),
            'category_mix': _merge_monthly_dimension(
                [p['category_mix'] for p in parts], 'revenue'),
            'channel_mix': _merge_monthly_dimension(
                [p['channel_mix'] for p in parts], 'revenue'),
            'sources': sorted(
                _merge_keyed([p['sources'] for p in parts], 'source',
                             ('new_customers', 'orders', 'revenue',
                              'first_order_revenue', 'repeat_revenue', 'spend'),
                             carry=('cac',)),
                key=lambda r: -r['revenue']),
            'cohorts': _merge_cohorts([p['cohorts'] for p in parts]),
            'value_params': _merge_value_params([p['value_params'] for p in parts]),
            'discounts': _merge_keyed([p['discounts'] for p in parts], 'code',
                                      ('orders', 'revenue', 'discount'),
                                      carry=('depth',)),
            'returns': _merge_returns([p['returns'] for p in parts]),
        }

    _CACHE.update({
        'dates': dates,
        'brands': bundles,
        'brand_names': BRAND_NAMES,
        'start': dates[0],
        'end': dates[-1],
        'window_days': WINDOW_DAYS,
    })
    return _CACHE


# --------------------------------------------------------------------------
# Windowing and derivation
# --------------------------------------------------------------------------
def window_indices(dates: Sequence[str], days: int) -> Tuple[int, int]:
    """Inclusive-exclusive slice for a date preset. ``days <= 0`` means all."""
    if days <= 0 or days >= len(dates):
        return 0, len(dates)
    return len(dates) - days, len(dates)


def series_for(bundle: Dict[str, object], key: str) -> List[float]:
    """Any metric, primitive or derived, as a full-length daily series.

    Derived metrics are ratios and are computed here rather than stored, so a
    portfolio rollup divides summed numerators by summed denominators instead of
    averaging per-brand rates.
    """
    series = bundle['series']
    if key in series:
        return series[key]
    if key in DERIVED:
        top, bottom = DERIVED[key]
        return [(a / b) if b else 0.0 for a, b in zip(series[top], series[bottom])]
    return [0.0] * len(next(iter(series.values())))


def summarize(values: Sequence[float]) -> Dict[str, float]:
    live = [v for v in values if v is not None]
    if not live:
        return {'total': 0.0, 'mean': 0.0, 'peak': 0.0, 'last': 0.0}
    return {
        'total': sum(live),
        'mean': sum(live) / len(live),
        'peak': max(live),
        'last': live[-1],
    }


def delta_pct(values: Sequence[float]) -> float:
    """Percent change between the first and second half of a window."""
    if len(values) < 4:
        return 0.0
    half = len(values) // 2
    first = sum(values[:half])
    second = sum(values[half:])
    if first <= 0:
        return 0.0
    return (second - first) / first * 100.0


def ratio_delta_pct(numerator: Sequence[float], denominator: Sequence[float]) -> float:
    """Percent change in a *ratio* between window halves.

    Applying delta_pct to a rate series would average the daily rates, which
    weights a quiet Tuesday the same as a sale day. Rates compare as summed
    numerator over summed denominator, per half.
    """
    if len(numerator) < 4:
        return 0.0
    half = len(numerator) // 2
    first_top, first_bottom = sum(numerator[:half]), sum(denominator[:half])
    second_top, second_bottom = sum(numerator[half:]), sum(denominator[half:])
    if first_bottom <= 0 or second_bottom <= 0 or first_top <= 0:
        return 0.0
    first = first_top / first_bottom
    second = second_top / second_bottom
    return (second - first) / first * 100.0


def metric_delta_pct(bundle: Dict[str, object], key: str, lo: int, hi: int) -> float:
    """Window-half change for any metric, ratio-aware."""
    if key in DERIVED:
        top, bottom = DERIVED[key]
        return ratio_delta_pct(bundle['series'][top][lo:hi], bundle['series'][bottom][lo:hi])
    return delta_pct(series_for(bundle, key)[lo:hi])


def prior_period_delta(bundle: Dict[str, object], key: str, lo: int, hi: int) -> float:
    """Percent change against the equal-length window immediately before this one.

    The retail comparison, and the one the driver decomposition walks. Comparing
    a window against its own two halves — the other obvious choice — reports a
    seasonal business as shrinking every January, which is true of the halves and
    false of the business.
    """
    span = hi - lo
    prior_lo = max(lo - span, 0)
    if prior_lo >= lo:
        return 0.0

    if key in DERIVED:
        top, bottom = DERIVED[key]
        prior_bottom = sum(bundle['series'][bottom][prior_lo:lo])
        current_bottom = sum(bundle['series'][bottom][lo:hi])
        if prior_bottom <= 0 or current_bottom <= 0:
            return 0.0
        prior = sum(bundle['series'][top][prior_lo:lo]) / prior_bottom
        current = sum(bundle['series'][top][lo:hi]) / current_bottom
    else:
        values = series_for(bundle, key)
        prior = sum(values[prior_lo:lo])
        current = sum(values[lo:hi])
    if prior <= 0:
        return 0.0
    return (current - prior) / prior * 100.0


def resample(dates: Sequence[str], values: Sequence[float], grain: str,
             how: str = 'sum') -> Tuple[List[str], List[float]]:
    """Roll a daily series up to weekly, monthly or quarterly buckets."""
    if grain == 'daily':
        return list(dates), list(values)

    buckets: Dict[str, List[float]] = {}
    order: List[str] = []
    for iso, value in zip(dates, values):
        year, month, day = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
        if grain == 'weekly':
            monday = date(year, month, day) - timedelta(days=date(year, month, day).weekday())
            label = monday.isoformat()
        elif grain == 'monthly':
            label = iso[:7]
        else:
            label = f'{year}-Q{(month - 1) // 3 + 1}'
        if label not in buckets:
            buckets[label] = []
            order.append(label)
        buckets[label].append(value)

    if how == 'mean':
        return order, [sum(v) / len(v) for v in (buckets[k] for k in order)]
    if how == 'last':
        return order, [buckets[k][-1] for k in order]
    return order, [sum(buckets[k]) for k in order]


def resample_ratio(dates: Sequence[str], numerator: Sequence[float],
                   denominator: Sequence[float], grain: str):
    """Roll a *ratio* up correctly: sum both terms per bucket, then divide."""
    labels, tops = resample(dates, numerator, grain, 'sum')
    _, bottoms = resample(dates, denominator, grain, 'sum')
    return labels, [(a / b) if b else 0.0 for a, b in zip(tops, bottoms)]


def events_in_window(events, dates: Sequence[str], lo: int, hi: int):
    window = set(dates[lo:hi])
    return [event for event in events if event['date'] in window]


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------
def _median(values: Sequence[float]) -> float:
    live = sorted(values)
    if not live:
        return 0.0
    mid = len(live) // 2
    return live[mid] if len(live) % 2 else (live[mid - 1] + live[mid]) / 2.0


def detect_anomalies(values: Sequence[float], dates: Sequence[str],
                     threshold: float = 3.5, window: int = 28) -> List[Dict[str, object]]:
    """Points that sit far from their own local level, in robust z units.

    Median and MAD rather than mean and standard deviation, because the outliers
    are exactly what is being looked for: one Black-Friday spike inflates a
    standard deviation enough to hide every other anomaly in the window. The
    baseline is local (a trailing median) so a brand's growth trend is not itself
    flagged as a run of anomalies.
    """
    out: List[Dict[str, object]] = []
    if len(values) < window + 4:
        return out

    for index in range(window, len(values)):
        history = values[index - window:index]
        centre = _median(history)
        spread = _median([abs(v - centre) for v in history]) * 1.4826
        if spread <= 1e-9:
            continue
        z = (values[index] - centre) / spread
        if abs(z) < threshold:
            continue
        out.append({
            'index': index,
            'date': dates[index],
            'value': values[index],
            'baseline': centre,
            'z': round(z, 2),
            'direction': 'high' if z > 0 else 'low',
            'pct': ((values[index] - centre) / centre * 100.0) if centre else 0.0,
        })
    return out


def driver_decomposition(bundle: Dict[str, object], lo: int, hi: int) -> Dict[str, object]:
    """Split the period-over-period revenue change into its funnel factors.

    Revenue is exactly visits x conversion x AOV, so the change between two
    periods can be walked one factor at a time: swap visits to the current
    period holding the rest at prior levels, then conversion, then AOV. The three
    steps sum to the total change with no residual — the order of substitution is
    a choice, and this one (top of funnel first) is the one a trading review
    reads naturally.
    """
    span = hi - lo
    prior_lo = max(lo - span, 0)
    if prior_lo >= lo:
        return {'terms': [], 'prior': 0.0, 'current': 0.0, 'change': 0.0, 'span': span}

    series = bundle['series']

    def totals(start: int, stop: int):
        visits = sum(series['visits'][start:stop])
        orders = sum(series['orders'][start:stop])
        revenue = sum(series['revenue'][start:stop])
        return {
            'visits': visits,
            'conversion': (orders / visits) if visits else 0.0,
            'aov': (revenue / orders) if orders else 0.0,
            'revenue': revenue,
        }

    prior = totals(prior_lo, lo)
    current = totals(lo, hi)

    # Walk the factors in order, carrying the swapped ones forward.
    state = dict(prior)
    walked = state['visits'] * state['conversion'] * state['aov']
    terms = []
    for key, label in (('visits', 'Site Visits'),
                       ('conversion', 'Conversion Rate'),
                       ('aov', 'Average Order Value')):
        state[key] = current[key]
        after = state['visits'] * state['conversion'] * state['aov']
        terms.append({
            'key': key,
            'label': label,
            'contribution': after - walked,
            'prior': prior[key],
            'current': current[key],
        })
        walked = after

    return {
        'terms': terms,
        'prior': prior['revenue'],
        'current': current['revenue'],
        'change': current['revenue'] - prior['revenue'],
        'span': span,
        'prior_window': (prior_lo, lo),
    }


def event_study(bundle: Dict[str, object], dates: Sequence[str], metric: str,
                kinds: Sequence[str] = (), before: int = 7, after: int = 14):
    """Average response around a promotion, normalised to the day before it runs.

    Each occurrence contributes one aligned window; day 0 is the promotion. The
    series is divided by its own day -1 level before averaging, so a sale on a
    large brand and a sale on a small one contribute equally instead of the large
    brand deciding the shape. The band is a standard error of the mean across
    occurrences, which is what makes a two-occurrence "lift" visibly untrustworthy.
    """
    values = series_for(bundle, metric)
    wanted = set(kinds) if kinds else None

    aligned: Dict[str, List[List[float]]] = {}
    for event in bundle['events']:
        kind = event['kind']
        if wanted and kind not in wanted:
            continue
        origin = event['day_index']
        if origin - before < 0 or origin + after >= len(values):
            continue
        baseline = values[origin - 1]
        if baseline <= 0:
            continue
        aligned.setdefault(kind, []).append(
            [values[origin + offset] / baseline for offset in range(-before, after + 1)])

    offsets = list(range(-before, after + 1))
    out = []
    for kind, windows in aligned.items():
        if len(windows) < 2:
            continue
        mean, lower, upper = [], [], []
        for position in range(len(offsets)):
            column = [window[position] for window in windows]
            avg = sum(column) / len(column)
            variance = sum((v - avg) ** 2 for v in column) / max(len(column) - 1, 1)
            stderr = math.sqrt(variance / len(column))
            mean.append(avg)
            lower.append(avg - 1.96 * stderr)
            upper.append(avg + 1.96 * stderr)
        out.append({
            'kind': kind,
            'occurrences': len(windows),
            'offsets': offsets,
            'mean': mean,
            'lower': lower,
            'upper': upper,
            'peak': max(mean),
            'color': EVENT_KINDS[kind]['color'],
        })
    out.sort(key=lambda r: -r['peak'])
    return out


def promotion_windows(bundle: Dict[str, object], lo: int, hi: int, span: int = 3):
    """Split a window into promoted and baseline days.

    A day counts as promoted if a promotion started within ``span`` days before
    it. Comparing a promotion day against the *annual* mean would credit the
    promotion with December; comparing against the non-promoted days of the same
    window does not.
    """
    promoted = set()
    for event in bundle['events']:
        if event['kind'] not in ('Flash Sale', 'Seasonal Campaign', 'Loyalty Push'):
            continue
        for offset in range(span):
            promoted.add(event['day_index'] + offset)

    on = [index for index in range(lo, hi) if index in promoted]
    off = [index for index in range(lo, hi) if index not in promoted]
    return on, off


def linear_fit(xs: Sequence[float], ys: Sequence[float]):
    """Least-squares slope, intercept and r-squared."""
    n = len(xs)
    if n < 3:
        return 0.0, 0.0, 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    if var_x <= 0:
        return 0.0, mean_y, 0.0
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = cov / var_x
    intercept = mean_y - slope * mean_x
    var_y = sum((y - mean_y) ** 2 for y in ys)
    r2 = (cov ** 2) / (var_x * var_y) if var_y > 0 else 0.0
    return slope, intercept, r2
