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
- `/projects` Selected Work
- `/dashboard` Live Demo (interactive analytics dashboard)
- `/publications` Publications
- `/contact` Contact

## Live demo dashboard

`/dashboard` is **Tidepool Commerce Analytics**, a multi-brand direct-to-consumer
retail analytics dashboard built for this portfolio. It is a self-contained
demonstration, not a reconstruction of anything: the domain is chosen, the data
is generated, and every number on the page comes out of the generator in this
repository.

Built with JavaScript and plotly.js. Also implemented as a Dash app (Python).
Experience: React, TypeScript, FastAPI, deck.gl.

Four retail functions, nine views:

- **Sales Performance**
  - *Revenue & Orders* — dual-axis trading chart with the promotion calendar
    overlaid and outliers called out in place, plus an anomaly log beside it.
  - *Revenue Drivers* — a driver decomposition waterfall (revenue factors as
    visits x conversion x AOV, so the walk is arithmetic rather than an
    attribution model) and a scatter-plot matrix across the core metrics.
  - *Category Mix* — a category contribution waterfall and the mix over time.
- **Customers**
  - *Cohort Retention* — the retention triangle (acquisition month x months
    since) and the same data as curves.
  - *Customer Value* — an RFM scatter with labelled quadrants and the revenue
    concentration by spend decile.
- **Marketing**
  - *Channel Attribution* — revenue by order channel, first-order against repeat
    revenue by acquisition source, and the attribution detail table.
  - *Promotion Lift* — an event study (every occurrence aligned on day 0, indexed
    to day −1, with a 95% band) plus promoted-versus-baseline days and the
    discount-code split.
- **Operations**
  - *Fulfillment & Regions* — a map dual-encoded by order volume (size) and
    average order value (colour), an individual-order marker view, a density
    surface, and a month-by-month replay of the order footprint.
  - *Returns* — return rate over time, by category, and by reason.

It runs on a **deterministic synthetic dataset**: five invented brands, three
portfolio rollups, 730 days. Every brand, customer, order and figure is
generated. No real name, record, or value appears anywhere in it.

```
demo_dashboard/
  config.py       brand roster, metric registry, information architecture, colours
  assumptions.py  the retail shape parameters the generator is built on
  data.py         seeded synthetic dataset (standard library only)
  geo.py          shared PRNG, map aggregation, point generation (mirrored in JS)
  figures.py      Plotly figure builders used by the Dash page
  export.py       dumps the dataset + shared assets for the static twin
pages/dashboard.py            the Dash page (server-side callbacks)
assets/dashboard.css          the dashboard visual system (shared)
docs/dashboard/index.html     static twin scaffolding
docs/assets/demo/tidepool.js  static twin behaviour (plotly.js)
```

### Assumptions

The generator is not tuned by eye, and it is not measured from anything either.
`demo_dashboard/assumptions.py` records the shape parameters in one place —
weekday and annual seasonality, funnel levels, the retention curve, value
concentration, return rates and lags, source and channel mixes — so the
assumptions behind the demo are legible and adjustable without reading the
generator.

They encode textbook DTC relationships rather than invented-on-the-spot numbers:
traffic peaks early in the week while conversion runs higher at the weekend (so
orders are flatter than either), Q4 dominates the year, repeat purchase decays
hard for two months and then flattens, a minority of customers carry most of the
revenue, and returns land about eleven days after the order that produced them.

### Revenue is never generated directly

Visits, conversion rate and average order value are the primitives; orders are
visits x conversion and revenue is orders x AOV. That is what makes the driver
decomposition honest — the walk it draws is arithmetic, and the three factor
bars sum to the total change with no residual.

### Map markers and customer points

The fulfillment map plots one marker per order — a third of a million of them —
and the value scatter one point per sampled customer. Shipping either as data
would dominate the exported JSON, so both are *generated* from compact per-market
and per-brand parameters on each side.

`demo_dashboard/geo.py` and its JavaScript mirror share a 32-bit LCG built on
integer arithmetic that both runtimes reproduce exactly. Every draw avoids
`log`, `sqrt`, `cos` and `sin`, whose last-bit behaviour is not guaranteed to
match across languages: jitter is a sum of uniforms, directions come from
rejection sampling, and heavy tails come from repeated multiplication rather than
an inverse CDF. The two builds therefore draw the identical cloud, verified
coordinate for coordinate.

Because GitHub Pages cannot run Dash callbacks, the demo ships twice from one
dataset: `pages/dashboard.py` is the runnable Python implementation, and
`docs/dashboard/` renders the same charts client-side for the published site.

### Keeping the two builds in sync

`docs/` is a static mirror, so a few files exist in both places.
`demo_dashboard/export.py` owns that duplication: it regenerates the demo dataset
and copies every shared asset from `assets/` into `docs/assets/`.

Run it after editing anything in `demo_dashboard/` or in `assets/`:

```bash
python3 -m demo_dashboard.export
```

Editing `docs/assets/` directly is a mistake — the next export overwrites it.

The dashboard's own markup is *not* maintained twice: `docs/assets/demo/tidepool.js`
generates every panel from the section config that travels in the payload, so the
static build cannot drift from the Dash page by way of stale HTML. The other
pages are still mirrored by hand — a change to `pages/home.py`, `projects.py`,
`publications.py` or `contact.py` needs the matching edit in `docs/**/index.html`.

### Chart heights

`demo_dashboard/figures.CHART_HEIGHTS` is the single source for how tall each
chart renders, and both builds apply it twice: once as the figure's own
`layout.height`, and once as the CSS height of the container.

The second one is not cosmetic. A responsive Plotly graph with no CSS height
collapses its container to zero on a width change while the figure keeps its own
height — the SVG then escapes the card and paints over whatever follows it. Never
add a chart without giving its container a height from this registry.

### The demo is light, the site is dark

The dashboard is a different product from the portfolio around it and is themed
as one: a warm off-white surface, a single terracotta accent, serif headings, and
a categorical palette whose members are separated by lightness so every chart
survives a greyscale print. `app.py` puts `site-shell--light` on the shell for
the `/dashboard` route, so the shared header comes with it — a dark bar over a
light page reads as a rendering fault rather than a change of register.

### Affiliation marks

`assets/logos/` holds the employer, school, partner and funder marks in the hero.
They are white-on-transparent PNGs, not the source brand files: ten brand
palettes, several of them on white rectangles, would fight everything else on a
dark page.

Each mark carries its own rendered height in `AFFILIATIONS` (pages/home.py)
because a bounding box is not optical weight — a bold wordmark that fills its box
and a lockup of small type inside a tall one need different sizes to read as
equals.

### Research figures

`assets/research/` holds the figures on the Research page. `research_content.py`
is the single source for what each one is and how it sits in the grid — the Dash
page and the static mirror both read it, so the two cannot caption the same
figure differently.

Two rules the captions follow, because getting them wrong is worse than having no
figure: say what the figure shows, and say when it shows a failure. The
nine-panel segmentation figure is Mask R-CNN *erring*, not results.

### Demo screenshots

`assets/demo_shots/*.jpg` are captured from the live demo at `/dashboard`.
Re-shoot them after a visual change to the dashboard; they are 16:9 because the
cards render them with `object-fit: cover`.

Capture them at the final size — set the viewport to the frame, scroll, shoot.
Do **not** use Playwright's `fullPage`, and do not restyle the page after it has
loaded: both resize the graphs after they have rendered, and a graph that
re-lays-out mid-capture produces a screenshot with the charts drawn on top of
each other. Scroll only once the section's charts exist, and assert the scroll
landed where it was asked to — a panel still rendering leaves the document too
short to scroll to, and the capture then silently frames the wrong view.

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
