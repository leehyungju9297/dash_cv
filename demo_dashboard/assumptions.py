"""Shape parameters for the synthetic retail dataset.

Every number here is invented. They are not measured from any real store, and
nothing in this repository is derived from one. What they encode is a set of
*textbook* direct-to-consumer relationships, chosen so the generated data
behaves the way a retail analyst would expect it to:

  - traffic peaks early in the week and troughs on Saturday, while conversion
    runs slightly higher at the weekend, so orders are flatter than visits;
  - the year has a long Q4 peak and a January trough, and a promotion in
    November is competing with a high baseline rather than creating one;
  - repeat purchase decays fast for two months, then flattens into a durable
    tail — the shape that makes a cohort triangle worth reading at all;
  - a minority of customers carry the majority of revenue, so the value
    distribution is Pareto-ish rather than normal;
  - returns are a lagged function of orders, and the lag matters: a return
    rate computed against same-day orders is wrong right after a spike.

Keeping them in one module means the assumptions behind the demo are legible
and adjustable in one place, instead of scattered through the generator.
"""

from __future__ import annotations

from typing import Dict, List


# --------------------------------------------------------------------------
# Weekly shape (Monday first)
# --------------------------------------------------------------------------
# Visits and conversion move in opposite directions across the week: the weekend
# brings fewer but more decided shoppers. Orders — their product — end up much
# flatter than either, which is why a weekday effect is easy to miss in an
# orders chart and obvious in a visits chart.
WEEKDAY_VISITS: List[float] = [1.11, 1.08, 1.04, 1.01, 0.96, 0.85, 0.95]
WEEKDAY_CONVERSION: List[float] = [0.98, 0.99, 1.00, 1.00, 1.00, 1.02, 1.06]
WEEKDAY_AOV: List[float] = [0.99, 0.99, 1.00, 1.00, 1.01, 1.03, 1.02]

# --------------------------------------------------------------------------
# Annual seasonality
# --------------------------------------------------------------------------
# Multiplier by calendar month (January = index 0) applied to visits. The Q4
# ramp is the dominant feature of any DTC year; January is the trough.
MONTH_VISITS: List[float] = [
    0.82, 0.86, 0.94, 0.97, 1.02, 0.98,
    0.95, 0.99, 1.05, 1.12, 1.42, 1.34,
]

# Basket size rises into gifting season and falls in the January clearance.
MONTH_AOV: List[float] = [
    0.93, 0.96, 0.99, 1.00, 1.02, 1.00,
    0.98, 1.00, 1.03, 1.05, 1.09, 1.12,
]

# Named trading days, as (month, day, visits multiplier, aov multiplier). These
# sit on top of the monthly curve — the peak is a few days, not a whole month.
TRADING_DAYS: List[Dict[str, object]] = [
    {'name': 'Late-November peak', 'month': 11, 'day': 27, 'span': 4,
     'visits': 2.9, 'aov': 0.88, 'conversion': 1.45},
    {'name': 'Cyber week', 'month': 12, 'day': 1, 'span': 3,
     'visits': 2.2, 'aov': 0.92, 'conversion': 1.35},
    {'name': 'Mid-December gifting', 'month': 12, 'day': 12, 'span': 6,
     'visits': 1.5, 'aov': 1.14, 'conversion': 1.12},
    {'name': 'New year clearance', 'month': 1, 'day': 2, 'span': 7,
     'visits': 1.25, 'aov': 0.78, 'conversion': 1.10},
]

# --------------------------------------------------------------------------
# Funnel levels
# --------------------------------------------------------------------------
# Revenue factors exactly as visits x conversion x AOV. Conversion is stated in
# fractions of a visit, not percent.
BASE_CONVERSION = 0.0246
CONVERSION_FLOOR = 0.004
CONVERSION_CEILING = 0.14

# Mean units per order, before the per-category basket weighting.
BASE_BASKET = 1.72

# Share of a day's ordering customers who are ordering for the first time, at
# the start and end of a brand's life. Acquisition mix shifts toward repeat as
# a brand matures — the single most important thing a cohort view should show.
NEW_CUSTOMER_SHARE_EARLY = 0.78
NEW_CUSTOMER_SHARE_MATURE = 0.34

# Orders per ordering customer per day. Just above one: a few customers place
# two orders in a day, almost nobody places three.
ORDERS_PER_CUSTOMER = 1.045

# Monthly actives run about 6.4x daily ordering customers. Unlike an app's DAU,
# a store's daily buyers barely overlap day to day, so a 30-day window
# double-counts very little.
DAILY_OVER_MONTHLY = 0.156

# --------------------------------------------------------------------------
# Retention
# --------------------------------------------------------------------------
# Share of an acquisition cohort that orders again in month k. Month 0 is the
# acquisition month itself and is 100% by construction. The curve decays hard
# through month 3 and then flattens — the flat tail is the durable base.
RETENTION_CURVE: List[float] = [
    1.000, 0.238, 0.167, 0.131, 0.113, 0.101, 0.094, 0.089,
    0.085, 0.082, 0.080, 0.078, 0.077, 0.076, 0.075, 0.074,
    0.073, 0.073, 0.072, 0.072, 0.071, 0.071, 0.070, 0.070,
]

# How much a cohort's whole curve can be lifted or cut by its acquisition
# quality — a cohort bought cheaply in a Q4 discount rush retains worse than one
# acquired organically in the spring.
COHORT_QUALITY_RANGE = (0.72, 1.26)

# --------------------------------------------------------------------------
# Customer value
# --------------------------------------------------------------------------
# Pareto exponent for lifetime spend. Lower means more concentrated; 1.16 puts
# roughly the top 20% of customers on ~60% of revenue.
VALUE_PARETO_ALPHA = 1.16
VALUE_MIN_SPEND = 24.0

# Lifetime order count follows a geometric-ish tail: most customers order once.
REPEAT_DECAY = 0.44

# --------------------------------------------------------------------------
# Returns
# --------------------------------------------------------------------------
# Baseline return rate, and how many days after the order the return lands.
# Apparel returns far more than food; the per-category multipliers are applied
# on top of this.
BASE_RETURN_RATE = 0.081
RETURN_LAG_DAYS = 11

CATEGORY_RETURN_MULTIPLIER: Dict[str, float] = {
    'Apparel': 1.95,
    'Home & Kitchen': 0.82,
    'Beauty': 0.61,
    'Outdoor': 1.05,
    'Accessories': 0.74,
    'Food & Beverage': 0.22,
}

# Return reason mix, as shares. Fit dominates because apparel dominates.
RETURN_REASON_MIX: Dict[str, float] = {
    'Fit / size': 0.412,
    'Not as described': 0.221,
    'Damaged in transit': 0.148,
    'Changed mind': 0.137,
    'Late delivery': 0.082,
}

# --------------------------------------------------------------------------
# Marketing
# --------------------------------------------------------------------------
# Share of newly acquired customers by source, and the relative lifetime value
# of a customer from that source (1.0 = portfolio average). Paid acquisition
# buys volume at below-average value; referral and email buy the opposite.
SOURCE_MIX: Dict[str, float] = {
    'Paid Search': 0.243,
    'Paid Social': 0.221,
    'Organic Search': 0.174,
    'Email': 0.121,
    'Affiliate': 0.098,
    'Referral': 0.079,
    'Direct': 0.064,
}

SOURCE_VALUE_INDEX: Dict[str, float] = {
    'Paid Search': 0.91,
    'Paid Social': 0.78,
    'Organic Search': 1.14,
    'Email': 1.36,
    'Affiliate': 0.86,
    'Referral': 1.42,
    'Direct': 1.21,
}

# Blended acquisition cost per new customer, by source.
SOURCE_CAC: Dict[str, float] = {
    'Paid Search': 41.20,
    'Paid Social': 46.80,
    'Organic Search': 6.40,
    'Email': 3.90,
    'Affiliate': 28.50,
    'Referral': 11.20,
    'Direct': 0.0,
}

# Order channel mix. Marketplace carries a lower basket and a higher return rate.
CHANNEL_MIX: Dict[str, float] = {
    'Web': 0.518,
    'Mobile App': 0.347,
    'Marketplace': 0.135,
}

CHANNEL_AOV_INDEX: Dict[str, float] = {
    'Web': 1.06,
    'Mobile App': 0.94,
    'Marketplace': 0.81,
}

# How often a brand ships marketing, as a probability per day.
MARKETING_CADENCE: Dict[str, float] = {
    'campaigns': 0.263,
    'email_sends': 0.512,
    'promotions': 0.041,
}

# Discount code mix across all orders. Most orders carry no code at all.
DISCOUNT_MIX: Dict[str, float] = {
    'No code': 0.641,
    'WELCOME10': 0.121,
    'SPRING20': 0.083,
    'FLASH30': 0.062,
    'BUNDLE15': 0.055,
    'LOYAL25': 0.038,
}

DISCOUNT_DEPTH: Dict[str, float] = {
    'No code': 0.0,
    'WELCOME10': 0.10,
    'SPRING20': 0.20,
    'FLASH30': 0.30,
    'BUNDLE15': 0.15,
    'LOYAL25': 0.25,
}

# --------------------------------------------------------------------------
# Geography
# --------------------------------------------------------------------------
# Order volume across shipping markets follows rank^-a. A flat-ish alpha gives
# the long tail a national retailer has, rather than three metros holding
# everything.
MARKET_ZIPF_ALPHA = 0.721

# Spread of average order value across markets, as a fraction of the mean. Dense
# urban markets skew to smaller, more frequent baskets.
MARKET_AOV_SPREAD = 0.22
