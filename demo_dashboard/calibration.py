"""Distribution targets the synthetic generator is tuned to hit.

Where these came from
---------------------
A one-off, local, read-only pass over a production ETL output of the real
multi-tenant dashboard this demo is modelled on. Only *aggregate* statistics
were taken — quantiles, ratios, and mix proportions across the whole client
base. No client name, no user record, and no individual value from that dataset
exists in this repository or in anything the site publishes; the numbers below
are the entire extract, and they are here so the generator's choices are
reviewable instead of arbitrary.

"Flagship tier" means the accounts whose mean daily active users exceeded 300 over
the trailing two years — the working accounts the demo's five clients stand in
for, rather than the long tail of dormant ones that dominates an unfiltered
median.

Reading the numbers
-------------------
Several of these are counter-intuitive and are exactly why calibrating mattered:

- Sunday is the *weakest* day for active users (0.65 of Monday), not the
  strongest. Downloads peak Friday while usage peaks Tuesday/Friday.
- Stickiness is ~4.8%, not the 25-30% a healthy consumer social app shows.
  Monthly actives run ~20x daily actives: a large, mostly lapsed audience that
  returns around releases.
- Timeline posts, notifications, livestreams, and auctions are *content events*,
  not per-user counters. A busy account posts on a quarter of days and almost
  never runs an auction. Modelling them as per-user volumes (the intuitive
  reading of the column names) inflates them by three orders of magnitude.
- Revenue is overwhelmingly subscription on iOS. The store split is not close to
  even.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Weekday seasonality — index against Monday, flagship tier, Mon..Sun
# --------------------------------------------------------------------------
WEEKDAY_ACTIVE = [1.000, 1.058, 1.030, 1.011, 1.078, 0.893, 0.645]
WEEKDAY_DOWNLOADS = [1.000, 1.073, 0.981, 1.365, 1.821, 1.249, 1.139]
WEEKDAY_REVENUE = [1.000, 1.040, 0.972, 0.991, 1.177, 0.896, 0.823]

# --------------------------------------------------------------------------
# Core ratios (flagship tier medians unless noted)
# --------------------------------------------------------------------------
DAU_OVER_MAU = 0.0477                  # monthly actives run ~21x daily actives
MEMBERS_PER_DOWNLOAD = (0.0055, 0.0285)   # p25/p50 .. p75 across accounts
NEW_MEMBERS_PER_DOWNLOAD = 0.047
REVENUE_PER_MEMBER_DAY = 0.075         # ~$2.28 per member per month
DAILY_CHURN = (0.00023, 0.00157, 0.00432)  # p25 / median / p75
MONTHLY_CHURN_PCT = (0.70, 4.67, 12.34)    # p25 / median / p75

# Average minutes per active user per day, derived from the trailing-30-day
# minutes of active users (median 58.9 minutes / 30 days).
MINUTES_PER_ACTIVE_USER_DAY = 1.96

# --------------------------------------------------------------------------
# Content-event cadence — share of days with at least one, flagship tier.
# When one does happen, the count is essentially always 1.
# --------------------------------------------------------------------------
CONTENT_CADENCE = {
    'posts': 0.251,
    'notifications': 0.480,
    'livestreams': 0.017,
    'auctions': 0.002,
}

# --------------------------------------------------------------------------
# Geography
# --------------------------------------------------------------------------
# Market share follows share_i ~ rank^-a across ~11,000 markets.
MARKET_ZIPF_ALPHA = 0.721
GEO_US_SHARE = 0.786                   # of distinct users, all markets
GEO_US_SHARE_TOP_MARKETS = 0.954       # within the 90 largest markets
GEO_COUNTRY_MIX = {
    'United States': 78.6, 'Canada': 6.0, 'United Kingdom': 1.9, 'India': 0.9,
    'Australia': 0.8, 'Italy': 0.7, 'South Africa': 0.7, 'Nigeria': 0.7,
    'Germany': 0.6, 'Poland': 0.5, 'Netherlands': 0.4,
}
# Cumulative share held by the top N markets (all ~11,000 markets).
GEO_CONCENTRATION = {1: 6.4, 5: 12.7, 10: 18.0, 25: 28.3, 50: 39.5, 100: 50.0}

# --------------------------------------------------------------------------
# Revenue mix — share of recognised USD
# --------------------------------------------------------------------------
PLATFORM_MIX = {'iOS': 91.8, 'Android': 7.1, 'Other': 1.1}
REVENUE_TYPE_MIX = {
    'Subscription': 91.7, 'Unknown': 7.1, 'Auction': 0.6,
    'Meet & Greet': 0.5, 'Album': 0.2, 'Livestream Ticket': 0.1,
}

# --------------------------------------------------------------------------
# Membership tenure — share of memberships in each bucket
# --------------------------------------------------------------------------
TENURE_MIX = {
    '0-30d': 19.5, '31-90d': 36.7, '91-180d': 16.4,
    '181-365d': 16.0, '1-2y': 6.9, '2y+': 4.5,
}
LIFETIME_DAYS = {'mean_p50': 95, 'median_p50': 31}
