"""Geography and point-generation helpers shared by the Dash app and its twin.

The fulfillment map plots one marker per order, and the customer-value scatter
one point per sampled customer. Shipping either as data would dominate the
exported payload, so both are *generated* from compact per-market and per-brand
parameters instead.

That only works if both implementations generate the same points. Everything in
this module is therefore built on a 32-bit linear congruential generator using
integer arithmetic that JavaScript reproduces exactly (``Math.imul`` + ``>>> 0``),
and every draw avoids ``log``, ``sqrt``, ``cos`` and ``sin``, whose last-bit
behavior is not guaranteed to match across language runtimes: jitter is a sum of
uniforms, directions come from rejection sampling, and heavy tails come from
repeated multiplication rather than an inverse-CDF. See the mirror of this file
in ``docs/assets/demo/tidepool.js``.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

from demo_dashboard.config import VALUE_TIER_NAMES


_MASK = 0xFFFFFFFF
_MULT = 1664525
_INC = 1013904223


class Lcg:
    """Numerical Recipes LCG. ``next_float`` returns a value in [0, 1).

    The state update and the float conversion are both exact in IEEE-754 doubles
    (a 32-bit integer divided by 2**32), so the JavaScript mirror produces a
    bit-identical stream.
    """

    __slots__ = ('state',)

    def __init__(self, seed: int):
        self.state = seed & _MASK

    def next_float(self) -> float:
        self.state = (_MULT * self.state + _INC) & _MASK
        return self.state / 4294967296.0

    def jitter(self, spread: float) -> float:
        """Symmetric offset in [-spread, spread], densest near zero.

        Three uniforms averaged: enough clustering that a metro reads as a
        cluster rather than a square patch, with no transcendental functions.
        """
        u = (self.next_float() + self.next_float() + self.next_float()) / 3.0
        return (u * 2.0 - 1.0) * spread


def string_seed(text: str) -> int:
    """FNV-1a 32-bit. Used to derive a stable per-market/per-brand seed."""
    h = 2166136261
    for ch in text:
        h ^= ord(ch) & 0xFF
        h = (h * 16777619) & _MASK
    return h


# --------------------------------------------------------------------------
# Market aggregation
# --------------------------------------------------------------------------
LEVEL_KEYS = {'city': 'city', 'region': 'region', 'country': 'country'}


def aggregate_by_level(locations: Sequence[Dict], level: str) -> List[Dict]:
    """Roll city rows up to the requested shipping level.

    Coordinates become the order-weighted centroid of the member cities, so a
    region bubble sits where its orders actually ship rather than at the
    geometric middle of the region. Average order value re-blends from summed
    revenue over summed orders — averaging the member averages would give a
    hundred-order town the same say as a hundred-thousand-order metro.
    """
    key = LEVEL_KEYS.get(level, 'city')
    merged: Dict[str, Dict] = {}

    for row in locations:
        name = row[key]
        entry = merged.get(name)
        if entry is None:
            entry = {
                'name': name,
                'city': row['city'],
                'region': row['region'],
                'country': row['country'],
                'orders': 0,
                'revenue': 0.0,
                'lat_weight': 0.0,
                'lon_weight': 0.0,
                'seed': row['seed'],
                'ramp_lag': row['ramp_lag'],
                '_top': 0,
            }
            merged[name] = entry
        entry['orders'] += row['orders']
        entry['revenue'] += row['revenue']
        entry['lat_weight'] += row['lat'] * row['orders']
        entry['lon_weight'] += row['lon'] * row['orders']
        # A rolled-up market inherits the identity of its largest contributor.
        if row['orders'] > entry['_top']:
            entry['_top'] = row['orders']
            entry['ramp_lag'] = row['ramp_lag']
            entry['seed'] = row['seed']

    out = []
    for entry in merged.values():
        orders = entry['orders'] or 1
        out.append({
            'name': entry['name'],
            'label': _place_label(level, entry),
            # Carried through because the marker spread is wider outside the US,
            # where a "market" covers a much larger delivery area.
            'country': entry['country'],
            'lat': round(entry['lat_weight'] / orders, 4),
            'lon': round(entry['lon_weight'] / orders, 4),
            'orders': entry['orders'],
            'revenue': round(entry['revenue'], 2),
            'aov': round(entry['revenue'] / orders, 2),
            'seed': entry['seed'],
            'ramp_lag': entry['ramp_lag'],
        })
    out.sort(key=lambda r: -r['orders'])
    return out


def _place_label(level: str, entry: Dict) -> str:
    if level == 'city':
        return f"{entry['city']}, {entry['region']}, {entry['country']}"
    if level == 'region':
        return f"{entry['region']}, {entry['country']}"
    return entry['country']


# --------------------------------------------------------------------------
# Individual order markers
# --------------------------------------------------------------------------
# How far the tail of a market reaches. Most orders land far inside this — see
# the squared radial term below — so it is the outer extent of the delivery
# footprint, not the radius of the cloud.
_SPREAD_DEGREES = 0.95
_SPREAD_INTERNATIONAL = 1.35

# Three decimals is about 100 m, two orders of magnitude finer than the spread
# below — the extra digit only inflated the payload.
_COORD_DECIMALS = 3


def _market_shape(rng: Lcg, base: float):
    """Delivery geometry for one market, drawn once.

    The scatter is deliberately not a disc. Jittering each coordinate
    independently and uniformly draws every metro as the same round blob, which
    is what a city-centroid fallback looks like when geocoding has failed — the
    one thing this view must not be mistaken for. Instead each market gets two to
    four population centres and an elliptical bias, so deliveries cluster the way
    a metro's suburbs actually do.
    """
    stretch_x = 0.75 + rng.next_float() * 0.9
    stretch_y = 0.75 + rng.next_float() * 0.9
    centre_count = 2 + int(rng.next_float() * 3)
    centres = []
    for index in range(centre_count):
        # The first centre is the city itself; the rest are satellites.
        offset = 0.0 if index == 0 else 0.34
        centres.append((
            rng.jitter(base * offset) * stretch_y,
            rng.jitter(base * offset) * stretch_x * 1.3,
            0.45 + rng.next_float(),          # relative pull
        ))
    return stretch_x, stretch_y, centres


def _cumulative_arrival(ramp: Sequence[float], lag: float) -> List[float]:
    """A market's own cumulative order curve across the month grid.

    A market that opened late compresses its whole ramp into the months it
    actually had, rather than being cut off mid-curve — otherwise every late
    market would appear to stop growing at the end of the window.
    """
    span = max(len(ramp) - 1, 1)
    offset = lag * span
    out = []
    for index in range(len(ramp)):
        if index < offset:
            out.append(0.0)
            continue
        local = (index - offset) / max(span - offset, 1e-9)
        out.append(_interpolate(ramp, local * span))
    # Force monotone and end at exactly 1 so the last month holds every order.
    peak = out[-1] or 1.0
    running = 0.0
    for index, value in enumerate(out):
        running = max(running, value / peak)
        out[index] = running
    return out


def scatter_orders(rows: Sequence[Dict], salt: str = '',
                   ramp: Sequence[float] = ()) -> List[Dict]:
    """One deterministic marker per order, scattered across its market.

    Every order gets a marker rather than a sampled subset: MapLibre draws the
    full cloud in about the same time it draws five thousand points, and the
    density is the point of the view. Each marker carries its own order value, so
    the individual view uses the same continuous value scale as the market
    bubbles instead of a separate categorical legend.

    When ``ramp`` is supplied each marker also gets the month it was placed in,
    which is what lets the replay show orders accumulating rather than a set of
    blobs resizing.
    """
    points: List[Dict] = []

    for row in rows:
        rng = Lcg(row['seed'] ^ string_seed(salt))
        base = (_SPREAD_DEGREES if row['country'] == 'United States'
                else _SPREAD_INTERNATIONAL)
        stretch_x, stretch_y, centres = _market_shape(rng, base)
        pull_total = sum(c[2] for c in centres)
        arrival = _cumulative_arrival(ramp, row['ramp_lag']) if ramp else ()
        aov = row['aov']

        for _ in range(row['orders']):
            pick = rng.next_float() * pull_total
            running = 0.0
            centre = centres[-1]
            for candidate in centres:
                running += candidate[2]
                if pick < running:
                    centre = candidate
                    break

            # A direction, by rejection so no sine or cosine is involved.
            for _ in range(12):
                dx = rng.next_float() * 2.0 - 1.0
                dy = rng.next_float() * 2.0 - 1.0
                if dx * dx + dy * dy <= 1.0:
                    break
            else:
                dx = dy = 0.0

            # Squared radius: dense core, thin tail.
            reach = rng.next_float()
            reach *= reach
            # A small share of orders ship well outside the metro. Without them
            # every market ends at a hard edge and the country between cities is
            # empty, which no real delivery footprint is.
            if rng.next_float() < 0.05:
                reach *= 3.0 + rng.next_float() * 4.0

            # Order value around the market mean, right-skewed: a few large
            # baskets, most near the middle.
            spread = (rng.next_float() + rng.next_float() + rng.next_float()) / 3.0
            value = aov * (0.45 + spread * 1.1)
            if rng.next_float() < 0.04:
                value *= 1.8 + rng.next_float() * 2.2

            point = {
                'lat': round(row['lat'] + centre[0]
                             + dy * base * reach * stretch_y, _COORD_DECIMALS),
                'lon': round(row['lon'] + centre[1]
                             + dx * base * reach * stretch_x * 1.3, _COORD_DECIMALS),
                'value': round(value, 2),
            }
            if arrival:
                u = rng.next_float()
                month = len(arrival) - 1
                for index, reached in enumerate(arrival):
                    if u <= reached:
                        month = index
                        break
                point['month'] = month
            points.append(point)

    return points


def _interpolate(values: Sequence[float], position: float) -> float:
    if not values:
        return 0.0
    if position <= 0:
        return values[0]
    if position >= len(values) - 1:
        return values[-1]
    low = int(position)
    weight = position - low
    return values[low] * (1 - weight) + values[low + 1] * weight


# --------------------------------------------------------------------------
# Customer value points
# --------------------------------------------------------------------------
# Quadrant thresholds on the RFM plane. Recency is a fraction of the window;
# frequency is a lifetime order count. These two cuts define the four quadrants
# the scatter labels, and the monetary term splits the best quadrant in two —
# which is what the M in RFM is for, and what marker size alone cannot say.
RECENCY_CUT = 0.25
FREQUENCY_CUT = 2
CHAMPION_SPEND_PERCENTILE = 0.72


def rfm_points(params: Dict[str, object], salt: str = '') -> List[Dict]:
    """One point per sampled customer: recency, frequency, lifetime spend, tier.

    Spend follows a Pareto-ish tail — a minority of customers carry the majority
    of revenue, which is the fact the whole view exists to show — drawn by
    repeated multiplication rather than an inverse power so the two languages
    agree to the last bit. Frequency is geometric: most customers order once and
    never return, and a value view that smooths that away is lying.
    """
    if not params:
        return []

    rng = Lcg(int(params['seed']) ^ string_seed(salt))
    sample = int(params['sample'])
    window = float(params['window_days'])
    mean_spend = float(params['mean_spend'])
    decay = float(params['repeat_decay'])

    points: List[Dict] = []
    for _ in range(sample):
        # Frequency: geometric tail, at least one order.
        frequency = 1
        while frequency < 24 and rng.next_float() < decay:
            frequency += 1

        # Recency: customers who order more are, on average, more recent — but
        # only on average. A third of the base has stopped regardless of how
        # much they used to buy, and those are precisely the customers the
        # At Risk quadrant exists to surface; coupling recency to frequency
        # tightly would empty that quadrant and make the chart useless.
        pull = rng.next_float()
        pull *= pull
        if rng.next_float() < 0.34:
            churned = 0.35 + rng.next_float() * 0.65
            recency = churned * window
        else:
            recency = pull * window / (0.6 + 0.4 * frequency)
        recency = min(recency, window)

        # Spend: a heavy right tail built from repeated multiplication.
        magnitude = 0.55 + rng.next_float() * 0.9
        for _ in range(3):
            if rng.next_float() < 0.28:
                magnitude *= 1.35 + rng.next_float() * 1.4
        spend = mean_spend * frequency * magnitude * 0.62

        points.append({
            'recency': round(recency, 1),
            'frequency': frequency,
            'spend': round(spend, 2),
        })

    # The champion cut is a percentile of this sample, so it adapts to the brand
    # rather than hard-coding a dollar figure that would be wrong for four of the
    # five brands. Computed on a sorted copy, which both languages agree on.
    ordered = sorted(point['spend'] for point in points)
    cut_index = min(int(len(ordered) * CHAMPION_SPEND_PERCENTILE), len(ordered) - 1)
    champion_spend = ordered[cut_index] if ordered else 0.0

    for point in points:
        recent = point['recency'] <= window * RECENCY_CUT
        frequent = point['frequency'] >= FREQUENCY_CUT
        if recent and frequent:
            # Top-right quadrant, split by spend.
            tier = VALUE_TIER_NAMES[0] if point['spend'] >= champion_spend \
                else VALUE_TIER_NAMES[1]
        elif recent:
            tier = VALUE_TIER_NAMES[2]        # Promising — bought once, recently
        elif frequent:
            tier = VALUE_TIER_NAMES[3]        # At Risk — bought often, gone quiet
        else:
            tier = VALUE_TIER_NAMES[4]        # Lapsed
        point['tier'] = tier

    return points


# The four quadrant labels the scatter draws, as (recency side, frequency side).
RFM_QUADRANTS = [
    {'recent': True, 'frequent': True, 'label': 'Champions & Loyal',
     'note': 'Recent and repeat'},
    {'recent': False, 'frequent': True, 'label': 'At Risk',
     'note': 'Bought often, gone quiet'},
    {'recent': True, 'frequent': False, 'label': 'Promising',
     'note': 'First order, still warm'},
    {'recent': False, 'frequent': False, 'label': 'Lapsed',
     'note': 'One order, long ago'},
]


__all__ = [
    'Lcg', 'aggregate_by_level', 'rfm_points', 'scatter_orders', 'string_seed',
]
