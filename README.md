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

- `/` Home — a recruiter-first summary in one scan order: what this person
  delivers, evidence at scale, selected work, capabilities, experience,
  education and affiliations
- `/projects` Selected Work — a project index, not a document. Seven cards, each
  carrying the outcome, the role and the timeframe
- `/projects/<slug>` one route per project, on one case-study template
- `/dashboard` Live Demo (interactive analytics dashboard)
- `/publications` Publications
- `/contact` Contact — carries the portrait, which is secondary to the links

### Work items and their routes

`case_studies.py` is the single source for every work item; `work_ui.py` holds
the ordering, the shared card and the previous/next ring. A project needs an
entry in `case_studies.py` and nothing else: `pages/project_detail.py` registers
`/projects/<slug>` for each one from a single loop, the index and the home page
pick it up from the same list, and `build_static.py` writes its page into the
mirror.

The case-study template is fixed — title, category and outcome; overview; role,
timeframe, domain and tools in a rail; problem; approach; what I built; results;
previous/next — so the seven read the same way and can be compared.

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

No page's markup is maintained twice.

The dashboard generates every panel client-side from the section config that
travels in the payload (`docs/assets/demo/tidepool.js`), so it cannot drift from
the Dash page by way of stale HTML.

The four portfolio pages are rendered from the real Dash layout by
`build_static.py`, which walks the component tree and writes the result into the
`<main class="page-wrap">` block of each `docs/**/index.html`. Run it after
editing any of `pages/home.py`, `projects.py`, `publications.py` or
`contact.py`::

```bash
python3 -m build_static
```

Only `<main>` is generated for the four hand-kept pages. Their document head,
site header and closing scripts stay hand-maintained in `docs/**/index.html`,
because they differ per page (meta descriptions, Open Graph tags, the active nav
item, the shell's width modifier) and change rarely.

The seven case-study pages have no hand-kept file at all: their whole document
is derived from `docs/projects/index.html` — the page they sit under and share a
nav state with — with only the title, the description and the main block
differing. Deriving rather than templating them separately is what keeps the
head and header identical across all seven.

A markup change *inside* a page needs no second edit; a change to the shared
header or head still needs one per hand-kept file.

### Chart heights

`demo_dashboard/figures.CHART_HEIGHTS` is the single source for how tall each
chart renders, and both builds apply it twice: once as the figure's own
`layout.height`, and once as the CSS height of the container.

The second one is not cosmetic. A responsive Plotly graph with no CSS height
collapses its container to zero on a width change while the figure keeps its own
height — the SVG then escapes the card and paints over whatever follows it. Never
add a chart without giving its container a height from this registry.

### One layout system, everywhere

Every route centres on the same token and takes the same gutter, so the left
edge of the page never moves between pages — and the header follows the page it
sits above, because it is a sibling of the page container rather than an
ancestor and cannot inherit the width (the shell carries a route modifier, see
`SHELL_WIDTH` in `app.py`).

| role | token | value |
| --- | --- | --- |
| standard page | `--page-max` | `1040px` |
| dashboard | `--page-max-wide` | `1120px` |
| contact | `--page-max-narrow` | `900px` |
| reading column | `--reading-max` | `720px` |
| paragraph measure | `--prose-max` | `min(58ch, --reading-max)` |
| gutter | `--page-gutter` | `clamp(20px, 4vw, 32px)` |

`--reading-max` is the column; `--prose-max` is the paragraph inside it. A
paragraph filling all 720px runs 90+ characters and prose reads at 65-80, so the
two are separate tokens. `--prose-max` is in `ch` so it tracks the font size,
and clamped so it can never exceed the column.

Sections are `64px` apart (`40px` below 900px), a heading sits `16px` from its
content, a card title `8px` from its body, and card padding and grid gaps are
both `24px`. Nothing picks its own spacing.

Below `760px` the navigation collapses behind a disclosure button
(`assets/enhancements.js` owns `aria-expanded` and the `open` class). Above it
the bar holds all five destinations and a button would be a step in the way;
below it they were wrapping under the wordmark and pushing the header past
100px. The closed header holds at `64px` either way.

### One warm light system, everywhere

The reference is a technical report, not a landing page. The site and the demo
share one set of tokens, declared once in `assets/custom.css` (`:root`) and
mirrored into the demo's scope in `assets/dashboard.css` (`.tp-page`) and into
`demo_dashboard/config.py` for the charts:

| role | token | value |
| --- | --- | --- |
| page ground | `--bg` | `#FAF9F6` |
| surface | `--surface` | `#FFFFFF` |
| ink | `--text-primary` / `--text-secondary` / `--text-muted` | `#1C1917` / `#57534E` / `#78716C` |
| hairline | `--border` / `--border-strong` | `#E7E5E4` / `#D6D3D1` |
| accent | `--accent` / `--accent-hover` / `--accent-soft` | `#C2410C` / `#9A3412` / `#FFF7ED` |
| research | `--secondary-accent` | `#0F766E` |

Inter is the only typeface, on the whole site and inside the charts. Radii are
small, and there are no gradients, glows, coloured accent bars or drop shadows
on cards — surfaces are separated by whitespace and a 1px rule. The only two
things that cast a shadow are the back-to-top button and a hovered case study.

Four rules the system is built on, all measurable:

* **Colour is semantic, never decorative.** Roughly 85% of the ink is warm
  greyscale, 10% accent, 5% teal. The accent marks product and data work; teal
  marks research. Both are reinforcement — the label always says which — so
  nothing is carried by colour alone.
* **Categorical colours are separated by lightness, not only hue.** The members
  of `PALETTE` sit 9-11 CIE L* apart, so a chart that is legible in colour is
  still legible photocopied or dropped into a greyscale deck. Ordered dimensions
  (acquisition source, value tier, return reason) use a single-hue sequential
  ramp instead, because their categories have an order a rainbow would hide.
  `PALETTE` is *not* derived from `--accent`: it is an encoding held to its own
  spacing, which is why retinting the UI accent leaves it alone.
* **Contrast is checked rather than assumed.** Every visible text node on every
  page is measured against the background actually painted behind it, and clears
  WCAG AA at its own size. The accent clears AA for small text on both the page
  and a white surface (5.4:1 and 5.6:1), so unlike a mid blue it can carry a
  label as well as a rule.
* **The reading measure is set in real characters, not in `ch`.** A `ch` is the
  width of "0", which in Inter is ~0.63em while running prose averages ~0.45em —
  so a column set to `65ch` actually runs about 90 characters. `--measure` is
  `48ch`, which measures out at 65-70.

The affiliation marks in `assets/logos/` are dark-on-transparent. They were
white when the site was dark; recolouring is a matter of replacing RGB and
leaving the alpha channel — the silhouette — alone.

### Affiliation marks

`assets/logos/` holds the employer, school, partner and funder marks in the hero.
They are single-colour ink-on-transparent PNGs, not the source brand files: ten
brand palettes, several of them on their own coloured rectangles, would fight
everything else on the page.

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

Shoot the `.tp-card` as an *element*, not as a scrolled viewport: an element
screenshot frames exactly the panel and cannot silently capture the wrong
region. A scrolled viewport shot can, and does — while a panel is still
rendering the document is too short to scroll to the requested offset, the
scroll clamps at the bottom, and every shot in the run frames the same view.

Wait for the plot SVG *inside that card* to exist before shooting. Do **not**
use Playwright's `fullPage`, and do not restyle the page after it has loaded:
both resize the graphs after they have rendered, and a graph that re-lays-out
mid-capture produces a screenshot with the charts drawn on top of each other.

Crop the result to 16:9 afterwards. The cards render these with `object-fit:
cover` and `object-position: 50% 0%`, so the crop comes off the bottom and the
panel title and chart survive it.

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
