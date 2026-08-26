"""Export the demo dataset (and shared stylesheet) for the static dashboard twin.

The portfolio's live site is a static GitHub Pages build under ``docs/``, where a
Dash server cannot run. The static twin at ``docs/dashboard/`` renders the same
dashboard client-side with plotly.js, driven by the JSON this module writes — so
the demo is interactive for a visitor while the Dash page in ``pages/dashboard.py``
stays the runnable Python implementation.

One dataset feeds both. Re-run after any change to ``demo_dashboard/data.py``::

    python3 -m demo_dashboard.export
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from demo_dashboard.config import (
    ACCENTS,
    AGGREGATE_NAMES,
    AXIS_METRICS,
    BRAND,
    BRAND_MARK,
    BRAND_TAGLINE,
    CLIENTS,
    CLIENT_NAMES,
    CORRELATION_METRICS,
    DATE_PRESETS,
    DEFAULT_CLIENT,
    DEFAULT_PRESET,
    METRICS,
    SEGMENTS,
    SURFACE,
)
from demo_dashboard.data import EVENT_KINDS, get_dataset
from demo_dashboard.figures import (
    CHART_HEIGHTS,
    HEATMAP_METRICS,
    MAP_STYLE,
    MARKER_LIMITS,
    MAX_BUBBLES,
    MEMBER_SHARE_SCALE,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DEMO = REPO_ROOT / 'docs' / 'assets' / 'demo'
DATA_FILE = DOCS_DEMO / 'frontrow_data.json'
# Assets the Dash app and the static build share verbatim. Copying them on
# export is what keeps the two from drifting: before this, a change to
# custom.css had to be remembered twice and silently wasn't.
SHARED_ASSETS = ('dashboard.css', 'custom.css', 'enhancements.js', 'tracking.js',
                 'favicon.svg')
ASSETS_DIR = REPO_ROOT / 'assets'
DOCS_ASSETS = REPO_ROOT / 'docs' / 'assets'


def build_payload() -> dict:
    """The dataset plus the config the client-side dashboard needs to render.

    Config travels with the data so the static page has no second source of
    truth for metric labels, colors, or the client roster — change
    ``demo_dashboard/config.py`` and both dashboards move together.
    """
    dataset = get_dataset()
    return {
        'brand': {
            'name': BRAND,
            'mark': BRAND_MARK,
            'tagline': BRAND_TAGLINE,
        },
        'config': {
            'clients': CLIENTS,
            'accounts': CLIENT_NAMES,
            'aggregates': AGGREGATE_NAMES,
            'defaultClient': DEFAULT_CLIENT,
            'defaultPreset': DEFAULT_PRESET,
            'presets': [{'label': label, 'days': days} for label, days in DATE_PRESETS],
            'metrics': METRICS,
            'axisMetrics': AXIS_METRICS,
            'correlationMetrics': CORRELATION_METRICS,
            'accents': ACCENTS,
            'surface': SURFACE,
            'segments': [{'name': name, 'color': color} for name, color in SEGMENTS],
            'eventKinds': {
                kind: {'color': spec['color'], 'metrics': sorted(spec['amp'])}
                for kind, spec in EVENT_KINDS.items()
            },
            # Heatmap constants travel with the data so the static twin's map
            # cannot drift from the Dash page's.
            'chartHeights': CHART_HEIGHTS,
            'heatmap': {
                'mapStyle': MAP_STYLE,
                'maxBubbles': MAX_BUBBLES,
                'markerLimits': MARKER_LIMITS,
                'memberShareScale': MEMBER_SHARE_SCALE,
                'metrics': {key: {'label': label, 'column': column}
                            for key, (label, column) in HEATMAP_METRICS.items()},
            },
        },
        'dates': dataset['dates'],
        'startDate': dataset['start_date'],
        'endDate': dataset['end_date'],
        'clients': dataset['clients'],
    }


def main() -> None:
    DOCS_DEMO.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    # separators without spaces: the file ships over the wire, not to a reader.
    DATA_FILE.write_text(json.dumps(payload, separators=(',', ':')))

    size_kb = DATA_FILE.stat().st_size / 1024
    print(f'wrote {DATA_FILE.relative_to(REPO_ROOT)}  ({size_kb:,.0f} KB)')

    for name in SHARED_ASSETS:
        source = ASSETS_DIR / name
        if not source.exists():
            print(f'skipped {name} (not in assets/)')
            continue
        shutil.copyfile(source, DOCS_ASSETS / name)
        print(f'synced docs/assets/{name}')


if __name__ == '__main__':
    main()
