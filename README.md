# dash_cv

Modern portfolio site built with Dash.

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8050`.

## Public pages

- `/` Home
- `/projects` Case Studies
- `/dashboard` Live Demo (interactive analytics dashboard)
- `/publications` Publications
- `/contact` Contact

## Live demo dashboard

`/dashboard` is a working rebuild of the multi-tenant product analytics system
described in the case studies. Four sections:

- **Overview** — KPI hero, dual-axis trend chart with the release calendar
  overlaid, period summary table.
- **Audience Heatmap** — market bubbles, a density surface, and individual user
  markers over a MapLibre basemap; click-to-drill-down, a month-by-month
  cumulative arrival animation, and top-market ranking.
- **Behavior** — relationship scatter with an OLS fit, correlation structure,
  session depth against DAU/MAU stickiness.
- **Revenue & Retention** — revenue trend, source mix, monthly churn comparison,
  membership tenure, most-engaged-fan leaderboard.

It runs on a **deterministic synthetic dataset** — the fictional "Frontrow
Analytics" platform and its artist accounts. No real client data, names, or
numbers appear anywhere in it.

```
demo_dashboard/
  config.py       brand, client roster, metric registry, color system
  calibration.py  the distribution targets the generator is tuned to
  data.py         seeded synthetic dataset (standard library only)
  geo.py          shared PRNG + map aggregation (mirrored in JS)
  figures.py      Plotly figure builders used by the Dash page
  export.py       dumps the dataset + stylesheet for the static twin
pages/dashboard.py            the Dash page (server-side callbacks)
assets/dashboard.css          the dashboard visual system (shared)
docs/dashboard/index.html     static twin markup
docs/assets/demo/frontrow.js  static twin behavior (plotly.js)
```

### Calibration

The generator is not tuned by eye. `demo_dashboard/calibration.py` records
aggregate distribution targets — weekday seasonality, DAU/MAU stickiness, churn
quantiles, revenue per member, content-event cadence, market concentration,
store and tenure mixes — measured once from a production dataset of the system
this demo is modelled on, and the generator is fitted to them. Only those
aggregates were taken: no name, no record, and no individual value from that
dataset exists in this repository or in anything the site publishes.

The measured shapes are worth reading before changing anything, because several
are counter-intuitive: Sunday is the *weakest* day for active users, stickiness
is ~5% rather than the ~25% a consumer social app shows, and timeline posts and
notifications are content events (a busy account posts on a quarter of days),
not per-user counters.

### Map markers

The heatmap plots thousands of individual markers, far more than it would be
sensible to ship in the exported JSON, so they are *generated* from the compact
per-city rows on both sides. `demo_dashboard/geo.py` and its JavaScript mirror
share a 32-bit LCG built on integer arithmetic that both runtimes reproduce
exactly, and jitter is a sum of uniforms rather than a Box-Muller normal — no
`log`/`sqrt`/`cos`, whose last-bit behavior is not guaranteed to match across
languages. The two dashboards therefore draw the identical point cloud.

Because GitHub Pages cannot run Dash callbacks, the demo ships twice from one
dataset: `pages/dashboard.py` is the runnable Python implementation, and
`docs/dashboard/` renders the same charts client-side for the published site.

### Keeping the two builds in sync

`docs/` is a hand-written static mirror of the Dash app, so a few files exist in
both places. `demo_dashboard/export.py` owns that duplication: it regenerates the
demo dataset and copies every shared asset from `assets/` into `docs/assets/`
(`custom.css`, `dashboard.css`, `enhancements.js`, `tracking.js`, `favicon.svg`).

Run it after editing anything in `demo_dashboard/` or in `assets/`:

```bash
python3 -m demo_dashboard.export
```

Editing `docs/assets/` directly is a mistake — the next export overwrites it.
Page markup itself is still maintained twice: a change to `pages/*.py` needs the
matching edit in `docs/**/index.html`.

### Chart heights

`demo_dashboard/figures.CHART_HEIGHTS` is the single source for how tall each
chart renders, and both builds apply it twice: once as the figure's own
`layout.height`, and once as the CSS height of the container.

The second one is not cosmetic. A responsive Plotly graph with no CSS height
collapses its container to zero on a width change while the figure keeps its own
height — the SVG then escapes the card and paints over whatever follows it. Never
add a chart without giving its container a height from this registry.

### Case study screenshots

`assets/case_studies/*.jpg` are captured from the live demo at `/dashboard`, not
from any production system. Re-shoot them after a visual change to the dashboard;
they are 16:9 because the cards render them with `object-fit: cover`.

Capture them at the final size — set the viewport to the frame, scroll, shoot.
Do **not** use Playwright's `fullPage`, and do not restyle the page after it has
loaded: both resize the graphs after they have rendered, and a graph that
re-lays-out mid-capture produces a screenshot with the charts drawn on top of
each other.

## GitHub Pages (Free Static Option)

A static copy of the site is in `docs/` for GitHub Pages hosting without backend cold starts.

Setup:
1. Push the current branch to GitHub.
2. Repo `Settings` -> `Pages`.
3. Source: `Deploy from a branch`.
4. Branch: `master` (or `main`) and folder: `/docs`.
5. Save and wait for publish.

Project site URL pattern:
- `https://<username>.github.io/dash_cv/`

## Deployment Scope

GitHub Pages only. No Vercel/Render deployment config is kept in this repository.

## Notes

- Resume download is at `/assets/Hyungju_Lee_Resume.pdf`.
- Legacy Dash experiment files were moved to `sandbox_pages/` so they are not auto-imported in production.
