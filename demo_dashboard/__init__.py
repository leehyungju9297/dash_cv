"""Frontrow Analytics — a self-contained, synthetic-data demo dashboard.

This package powers the interactive case-study demo shipped with the portfolio
site. It reproduces the structure of a production multi-tenant product analytics
dashboard (KPI overview, audience geography, behavioral diagnostics, revenue and
retention) against a deterministic synthetic dataset. No real client data, names,
or numbers appear anywhere in this package.

Modules
-------
config   Brand, client roster, metric registry, and the color system.
data     Deterministic synthetic dataset generation (standard library only).
figures  Plotly figure builders shared by the Dash page.
export   Dumps the dataset to JSON for the static (client-side) twin.
"""

from demo_dashboard.config import BRAND, CLIENTS, DEFAULT_CLIENT
from demo_dashboard.data import get_dataset

__all__ = ['BRAND', 'CLIENTS', 'DEFAULT_CLIENT', 'get_dataset']
