"""Geography helpers shared by the Dash dashboard and its static twin.

The Audience Heatmap needs far more map markers than it would be sensible to ship
in the exported JSON (individual view alone plots thousands of points), so the
markers are *generated* from the compact per-city rows instead of transported.

That only works if both implementations generate the same points. Everything in
this module is therefore built on a 32-bit linear congruential generator using
integer arithmetic that JavaScript reproduces exactly (``Math.imul`` + ``>>> 0``),
and jitter is a sum of uniforms rather than a Box-Muller normal — no ``log``,
``sqrt`` or ``cos``, whose last-bit behavior is not guaranteed to match across
language runtimes. See the mirror of this file in ``docs/assets/demo/frontrow.js``.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

from demo_dashboard.config import SEGMENT_NAMES


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
    """FNV-1a 32-bit. Used to derive a stable per-city/per-client seed."""
    h = 2166136261
    for ch in text:
        h ^= ord(ch) & 0xFF
        h = (h * 16777619) & _MASK
    return h


# --------------------------------------------------------------------------
# Location aggregation
# --------------------------------------------------------------------------
LEVEL_KEYS = {'city': 'city', 'region': 'region', 'country': 'country'}


def aggregate_by_level(locations: Sequence[Dict], level: str) -> List[Dict]:
    """Roll city rows up to the requested location level.

    Coordinates become the user-weighted centroid of the member cities, so a
    region bubble sits where its audience actually is rather than at the
    geometric middle of the region.
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
                'users': 0,
                'engagement': 0,
                'lat_weight': 0.0,
                'lon_weight': 0.0,
                'segments': {seg: 0 for seg in SEGMENT_NAMES},
                'seed': row['seed'],
                'ramp_lag': row['ramp_lag'],
            }
            merged[name] = entry
        entry['users'] += row['users']
        entry['engagement'] += row['engagement']
        entry['lat_weight'] += row['lat'] * row['users']
        entry['lon_weight'] += row['lon'] * row['users']
        for seg in SEGMENT_NAMES:
            entry['segments'][seg] += row['segments'][seg]
        # A rolled-up market inherits the lag of its largest contributor.
        if row['users'] > entry.get('_top_users', 0):
            entry['_top_users'] = row['users']
            entry['ramp_lag'] = row['ramp_lag']
            entry['seed'] = row['seed']

    out = []
    for entry in merged.values():
        users = entry['users'] or 1
        members = entry['segments']['Member'] + entry['segments']['Super User']
        out.append({
            'name': entry['name'],
            'label': _place_label(level, entry),
            'lat': round(entry['lat_weight'] / users, 4),
            'lon': round(entry['lon_weight'] / users, 4),
            'users': entry['users'],
            'engagement': entry['engagement'],
            'members': members,
            'signed_up': entry['segments']['Signed-Up'],
            'super_users': entry['segments']['Super User'],
            'member_share': members / users,
            'segments': entry['segments'],
            'seed': entry['seed'],
            'ramp_lag': entry['ramp_lag'],
        })
    out.sort(key=lambda r: -r['users'])
    return out


def _place_label(level: str, entry: Dict) -> str:
    if level == 'city':
        return f"{entry['city']}, {entry['region']}, {entry['country']}"
    if level == 'region':
        return f"{entry['region']}, {entry['country']}"
    return entry['country']


# --------------------------------------------------------------------------
# Individual markers
# --------------------------------------------------------------------------
# How far the tail of a market reaches. Most users land far inside this — see
# the concentration term in spread_within_city — so it is the outer extent, not
# the radius of the cloud.
_SPREAD_DEGREES = 0.95
_SPREAD_INTERNATIONAL = 1.35


# Three decimals is about 100 m, two orders of magnitude finer than the jitter
# spread below — the extra digit only inflated the payload.
_COORD_DECIMALS = 3


def spread_within_city(rows: Sequence[Dict], salt: str = '') -> List[Dict]:
    """One deterministic marker per mapped user, scattered around their city.

    Every user gets a marker rather than a sampled subset: MapLibre draws the
    full ~270k cloud in about the same time it draws 5,000, and the density is
    the point of the view. The markers carry no per-point label — at this scale
    an individual fan cannot be hovered anyway, and the strings were more than
    half the payload. Drill-down lives in the market and density views.

    The scatter is deliberately not a disc. Jittering each coordinate
    independently and uniformly draws every metro as the same round blob, which
    is exactly what a city-centroid fallback looks like when geolocation has
    failed — the one thing this view must not be mistaken for. Instead each
    market gets two to four population centres, an elliptical bias, and a
    squared radial term that puts most users near a centre and a thin tail well
    beyond it.

    Every draw is integer-LCG arithmetic with no transcendental functions, so
    the JavaScript mirror produces the identical cloud.
    """
    points: List[Dict] = []

    for row in rows:
        rng = Lcg(row['seed'] ^ string_seed(salt))
        base = (_SPREAD_DEGREES if row['country'] == 'United States'
                else _SPREAD_INTERNATIONAL)

        # Market shape, drawn once: how elongated it is, and where its
        # population centres sit relative to the nominal city point.
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
        pull_total = sum(c[2] for c in centres)

        weights = [max(row['segments'][seg], 0) + 0.5 for seg in SEGMENT_NAMES]
        pool = sum(weights)

        for _ in range(row['users']):
            draw = rng.next_float() * pool
            segment = SEGMENT_NAMES[-1]
            running = 0.0
            for name, weight in zip(SEGMENT_NAMES, weights):
                running += weight
                if draw < running:
                    segment = name
                    break

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
            # A small share live well outside the metro. Without them every
            # market ends at a hard edge and the country between cities is
            # empty, which real location data never is.
            if rng.next_float() < 0.05:
                reach *= 3.0 + rng.next_float() * 4.0

            points.append({
                'lat': round(row['lat'] + centre[0]
                             + dy * base * reach * stretch_y, _COORD_DECIMALS),
                'lon': round(row['lon'] + centre[1]
                             + dx * base * reach * stretch_x * 1.3, _COORD_DECIMALS),
                'segment': segment,
            })

    return points


# --------------------------------------------------------------------------
# Growth animation frames
# --------------------------------------------------------------------------
def growth_frames(monthly_ramp: Sequence[Dict], markets: Sequence[Dict]) -> List[Dict]:
    """Cumulative arrivals per market, one frame per month.

    A market's audience at month *m* is its final size scaled by the client's
    cumulative install curve, shifted by that market's own lag — so the map fills
    in the order markets actually opened up rather than all at once.
    """
    frames = []
    span = max(len(monthly_ramp) - 1, 1)

    for index, step in enumerate(monthly_ramp):
        rows = []
        for market in markets:
            lag = market['ramp_lag'] * span
            if index < lag:
                continue
            # Re-read the client curve at the market's own (lagged, rescaled)
            # position so late markets compress their whole ramp into the
            # remaining months instead of being cut off mid-curve.
            local = (index - lag) / max(span - lag, 1e-9)
            fraction = _interpolate([s['frac'] for s in monthly_ramp], local * span)
            users = market['users'] * fraction
            if users < 1:
                continue
            rows.append({
                'label': market['label'],
                'lat': market['lat'],
                'lon': market['lon'],
                'users': int(round(users)),
                'member_share': market['member_share'],
            })
        frames.append({'period': step['period'], 'markets': rows})
    return frames


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


__all__ = [
    'Lcg', 'aggregate_by_level', 'growth_frames', 'spread_within_city', 'string_seed',
]
