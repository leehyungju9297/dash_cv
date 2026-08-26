"""Tidepool Commerce Analytics — a self-contained, synthetic-data demo dashboard.

This package powers the interactive demo shipped with the portfolio site: a
multi-brand direct-to-consumer retail analytics surface covering sales
performance, cohort retention and customer value, marketing attribution and
promotion lift, and fulfillment and returns — all against a deterministic
synthetic dataset. Every brand, customer, order and figure is generated. No real
name, record or value appears anywhere in this package.

Modules
-------
config   Brand roster, metric registry, information architecture, color system.
data     Deterministic synthetic dataset generation (standard library only).
geo      Shared PRNG and geography helpers, mirrored bit-for-bit in JavaScript.
figures  Plotly figure builders shared by the Dash page.
export   Dumps the dataset to JSON for the static (client-side) twin.
"""

from demo_dashboard.config import BRAND, BRANDS, DEFAULT_BRAND
from demo_dashboard.data import get_dataset

__all__ = ['BRAND', 'BRANDS', 'DEFAULT_BRAND', 'get_dataset']
