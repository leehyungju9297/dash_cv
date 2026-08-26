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
    ACCENT,
    ACCENT_DEEP,
    ACCENT_SOFT,
    ACCENTS,
    AGGREGATE_NAMES,
    ANOMALY_METRICS,
    ANOMALY_Z,
    AOV_SCALE,
    AXIS_METRICS,
    BRAND,
    BRAND_MARK,
    BRAND_SLUG,
    BRAND_TAGLINE,
    BRANDS,
    BRAND_NAMES,
    CATEGORIES,
    CHANNELS,
    DATE_PRESETS,
    DEFAULT_BRAND,
    DEFAULT_PRESET,
    DEFAULT_VIEW,
    DIVERGING,
    METRICS,
    NEGATIVE,
    NEUTRAL,
    PALETTE,
    POSITIVE,
    RETENTION_SCALE,
    RETURN_REASONS,
    SECTIONS,
    SEQUENTIAL,
    SOURCE_COLORS,
    SPLOM_METRICS,
    SURFACE,
    VALUE_TIERS,
)
from demo_dashboard.data import DERIVED, EVENT_KINDS, SERIES_KEYS, get_dataset
from demo_dashboard.figures import CHART_HEIGHTS, MAP_DISPLAYS, MAP_STYLE
from demo_dashboard.geo import (
    CHAMPION_SPEND_PERCENTILE,
    FREQUENCY_CUT,
    RECENCY_CUT,
    RFM_QUADRANTS,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DEMO = REPO_ROOT / 'docs' / 'assets' / 'demo'
DATA_FILE = DOCS_DEMO / f'{BRAND_SLUG}_data.json'
# Assets the Dash app and the static build share verbatim. Copying them on
# export is what keeps the two from drifting: before this, a change to
# custom.css had to be remembered twice and silently wasn't.
SHARED_ASSETS = ('dashboard.css', 'custom.css', 'enhancements.js', 'tracking.js',
                 'favicon.svg', 'Hyungju_Lee_Resume.pdf')
SHARED_ASSET_DIRS = ('research', 'logos', 'demo_shots')
ASSETS_DIR = REPO_ROOT / 'assets'
DOCS_ASSETS = REPO_ROOT / 'docs' / 'assets'

# Whatever the exporter wrote under a previous brand is still being served until
# it is removed, and a stale twin is worse than no twin. Rather than list old
# names — which would keep a retired brand in the source forever — anything in
# the demo directory that is not part of the current build is pruned.
CURRENT_DEMO_FILES = (f'{BRAND_SLUG}_data.json', f'{BRAND_SLUG}.js')


def build_payload() -> dict:
    """The dataset plus the config the client-side dashboard needs to render.

    Config travels with the data so the static page has no second source of
    truth for metric labels, colours, thresholds or the brand roster — change
    ``demo_dashboard/config.py`` and both builds move together. The same goes
    for the analysis constants: the anomaly threshold and the RFM quadrant cuts
    are shipped rather than restated, because two copies of a threshold is two
    charts that eventually disagree.
    """
    dataset = get_dataset()
    return {
        'brand': {
            'name': BRAND,
            'mark': BRAND_MARK,
            'tagline': BRAND_TAGLINE,
        },
        'config': {
            'brands': BRANDS,
            'accounts': BRAND_NAMES,
            'aggregates': AGGREGATE_NAMES,
            'defaultBrand': DEFAULT_BRAND,
            'defaultPreset': DEFAULT_PRESET,
            'defaultView': DEFAULT_VIEW,
            'presets': [{'label': label, 'days': days} for label, days in DATE_PRESETS],
            'sections': SECTIONS,
            'metrics': METRICS,
            'axisMetrics': AXIS_METRICS,
            'splomMetrics': SPLOM_METRICS,
            'anomalyMetrics': ANOMALY_METRICS,
            'anomalyZ': ANOMALY_Z,
            'seriesKeys': SERIES_KEYS,
            'derived': {key: list(pair) for key, pair in DERIVED.items()},
            'accents': ACCENTS,
            'surface': SURFACE,
            'palette': PALETTE,
            'sequential': SEQUENTIAL,
            'diverging': DIVERGING,
            'accent': ACCENT,
            'accentDeep': ACCENT_DEEP,
            'accentSoft': ACCENT_SOFT,
            'positive': POSITIVE,
            'negative': NEGATIVE,
            'neutral': NEUTRAL,
            'retentionScale': [[position, colour] for position, colour in RETENTION_SCALE],
            'aovScale': [[position, colour] for position, colour in AOV_SCALE],
            'categories': [{'name': c['name'], 'color': c['color']} for c in CATEGORIES],
            'channels': [{'name': name, 'color': colour} for name, colour in CHANNELS],
            'sourceColors': SOURCE_COLORS,
            'returnReasons': [{'name': name, 'color': colour}
                              for name, colour in RETURN_REASONS],
            'valueTiers': [{'name': name, 'color': colour} for name, colour in VALUE_TIERS],
            'rfm': {
                'recencyCut': RECENCY_CUT,
                'frequencyCut': FREQUENCY_CUT,
                'championPercentile': CHAMPION_SPEND_PERCENTILE,
                'quadrants': RFM_QUADRANTS,
            },
            'eventKinds': {
                kind: {'color': spec['color'], 'terms': sorted(spec['amp'])}
                for kind, spec in EVENT_KINDS.items()
            },
            # Chart geometry travels with the data so the static twin's cards
            # cannot drift from the Dash page's.
            'chartHeights': CHART_HEIGHTS,
            'map': {
                'style': MAP_STYLE,
                'displays': [{'value': value, 'label': label}
                             for value, label in MAP_DISPLAYS],
            },
        },
        'dates': dataset['dates'],
        'startDate': dataset['start'],
        'endDate': dataset['end'],
        'brands': dataset['brands'],
    }


def main() -> None:
    DOCS_DEMO.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    # separators without spaces: the file ships over the wire, not to a reader.
    DATA_FILE.write_text(json.dumps(payload, separators=(',', ':')))

    size_kb = DATA_FILE.stat().st_size / 1024
    print(f'wrote {DATA_FILE.relative_to(REPO_ROOT)}  ({size_kb:,.0f} KB)')

    for stale in sorted(DOCS_DEMO.iterdir()):
        if stale.is_file() and stale.name not in CURRENT_DEMO_FILES:
            stale.unlink()
            print(f'removed stale docs/assets/demo/{stale.name}')

    for name in SHARED_ASSETS:
        source = ASSETS_DIR / name
        if not source.exists():
            print(f'skipped {name} (not in assets/)')
            continue
        shutil.copyfile(source, DOCS_ASSETS / name)
        print(f'synced docs/assets/{name}')

    # Whole image directories, mirrored wholesale so a new figure only has to be
    # dropped into assets/ once.
    for folder in SHARED_ASSET_DIRS:
        source = ASSETS_DIR / folder
        if not source.is_dir():
            continue
        target = DOCS_ASSETS / folder
        target.mkdir(parents=True, exist_ok=True)
        # Underscore-prefixed files are working scratch (crop previews, review
        # captures) and must not be published.
        published = [item for item in sorted(source.iterdir())
                     if item.is_file() and not item.name.startswith(('.', '_'))]
        for item in published:
            shutil.copyfile(item, target / item.name)
        for stale in target.iterdir():
            if stale.is_file() and stale.name not in {i.name for i in published}:
                stale.unlink()
        print(f'synced docs/assets/{folder}/ ({len(published)} files)')


if __name__ == '__main__':
    main()
