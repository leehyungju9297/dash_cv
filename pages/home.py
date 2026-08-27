"""The home page.

Seven chapters, in the order a hiring reader needs them: the proposition, the
evidence that it has held at scale, the systems themselves, what they add up
to, the record, the credentials, the way to make contact.

The page is deliberately not evenly spaced. Space is the signal that a chapter
has changed, so the transitions into Selected Systems and around the flagship
are wide, and everything that supports a claim rather than making one — the
stack line, the record, the credentials — is set tight.
"""

from typing import Optional

import dash
from dash import html

from profile_data import EMAIL, GITHUB_URL, LINKEDIN_URL, LOCATION, PHONE_DISPLAY
from research_content import RESEARCH_FIGURES
from work_ui import FEATURED_SLUG, HOME_PRODUCT, HOME_RESEARCH, by_slug, outcome, tags


dash.register_page(__name__, path='/', order=0, name='Home')


RESUME_HREF = '/assets/Hyungju_Lee_Resume.pdf'

# --------------------------------------------------------------------------
# Chapter B — proof of scale
# --------------------------------------------------------------------------
# Four figures, each one already carried elsewhere on the site: the first three
# are the MySeat engagement's own numbers, restated from the Experience section
# below, and the fourth is the research record. The third line on each is where
# the figure comes from, because a number with no provenance is a claim.
PROOF = [
    ('1.6B+', 'session-minutes analyzed',
     'Production analytics across 17M+ sessions'),
    ('138', 'client apps instrumented',
     'One metric contract across the portfolio'),
    ('21\u00d7', 'faster analytics pipeline',
     '567.6s \u2192 26.7s runtime'),
    ('ICPR / ISPRS', 'peer-reviewed publications',
     'LiDAR 3D detection benchmark research'),
]

# --------------------------------------------------------------------------
# Chapter C — the flagship
# --------------------------------------------------------------------------
# What the project is evidence of, in four lines. Each one is a fact about this
# build specifically — the demo is a standalone product built from a generated
# dataset, so none of the MySeat scale figures belong to it.
FLAGSHIP_EVIDENCE = [
    'End-to-end ownership — dataset, analysis, chart craft, front end',
    'Nine views across trading, customers, marketing and operations',
    'Cohort retention, RFM segmentation, driver decomposition, event studies',
    'Two independent front ends, one dataset, agreeing to the last digit',
]

FLAGSHIP_COPY = (
    'A multi-brand direct-to-consumer analytics surface, owned end to end — '
    'dataset, analysis, chart craft and front end. Nine views run from sales '
    'performance to fulfillment, each built around an operating decision '
    'rather than around a metric.'
)

# The two supporting frames under the flagship's lead visual. Both are real
# screens from the build in this repository; the captions are the ones the case
# study uses, shortened to a single clause.
FLAGSHIP_SHOTS = [
    ('/assets/demo_shots/cohort-retention.jpg',
     'A cohort retention triangle: acquisition month down the side, months '
     'since first order across the top.',
     'Repeat rate by acquisition month — a triangle, not a rectangle, because '
     'last month’s cohort has one observed month.'),
    ('/assets/demo_shots/fulfillment-geography.jpg',
     'A light map of North America with market bubbles sized by order volume '
     'and coloured by average order value.',
     'Order volume as size, average order value as colour — a large cheap '
     'market reads differently from a small rich one.'),
]

# The two production systems get a schematic rather than a screenshot: the
# software is a client's, not mine to publish. Three stages — what goes in,
# what it is turned into, what a person actually reads — which is the part of
# the system a reader is trying to judge anyway.
SCHEMATICS = {
    'executive-kpi-monitoring': [
        ('Sources', 'Event logs, membership snapshots and revenue records '
                    'across 138 client accounts'),
        ('Contract', 'One definition each for DAU, memberships, downloads, '
                     'new members and revenue'),
        ('Surface', 'Leadership review: monitored time series, event overlays, '
                    'per-client filters'),
    ],
    'geo-segmented-user-intelligence': [
        ('Sources', 'User location records, account metadata and segment flags'),
        ('Model', 'Standardized location and segment logic, comparable across '
                  'every client'),
        ('Surface', 'Map layers by account type, density corridors, market '
                    'concentration'),
    ],
}

# The research pair carry real figures from the work itself, reused from the
# Research page so the alt text cannot drift between the two surfaces.
_FIGURES = {figure['src']: figure for figure in RESEARCH_FIGURES}

RESEARCH_VISUALS = {
    'lidar-benchmark-engineering': (
        '/assets/research/yuto-benchmark-items.jpg',
        'YUTO Tree-5000 benchmark items — one scene as semantic classes, '
        'instance polygons and 3D boxes.',
    ),
    'volumetric-3d-vision-evaluation': (
        '/assets/research/detection-model-comparison.jpg',
        'Average precision against IoU for eight 3D detectors, in '
        'bird’s-eye view and full 3D.',
    ),
}

# --------------------------------------------------------------------------
# Chapter D — what the systems above add up to
# --------------------------------------------------------------------------
PRACTICE = [
    ('Product Analytics',
     'Decision systems, KPI architecture, experimentation, retention, '
     'monetization, behavioral segmentation.'),
    ('Data Systems',
     'Analytics engineering, ETL, automation, scheduled workflows, data '
     'quality monitoring.'),
    ('Applied ML',
     'Computer vision, benchmarking, model evaluation, detection and '
     'experimentation.'),
]

# Two lines: what I work in, and what I work on. Supporting evidence for the
# systems above, which is why it is a line of text and not a rack of badges.
STACK = [
    ('Tools', ['Python', 'SQL', 'R', 'TypeScript', 'Pandas / Polars',
               'Plotly / Dash', 'React', 'FastAPI', 'Celery', 'deck.gl']),
    ('Methods', ['ETL & Scheduled Workflows', 'KPI Architecture',
                 'Retention & Monetization', 'Behavioral Segmentation',
                 'Benchmark Design', '3D Computer Vision']),
]

# --------------------------------------------------------------------------
# Chapter E — the record
# --------------------------------------------------------------------------
# One or two sentences an entry, not a bullet list. The quantities that survive
# are the ones that change how the role reads; the rest is in the resume.
EXPERIENCE = [
    {
        'company': 'MySeat Media',
        'role': 'Data Scientist / Analytics Engineer',
        'period': '2023 – Present',
        'copy': 'Built the product analytics and decision systems spanning '
                'engagement, retention, memberships, livestream activity, '
                'revenue and executive reporting across a 138-client app '
                'ecosystem. Productionized the SQL and Python workflows behind '
                '17M+ sessions and the 34 scheduled jobs that refresh '
                'leadership and client reporting unattended.',
    },
    {
        'company': 'AUSM Lab',
        'role': 'Research Engineer / Computer Vision Researcher',
        'period': '2019 – 2024',
        'copy': 'Built the dataset, annotation and benchmark infrastructure '
                'behind airborne LiDAR 3D detection research — 5,000+ '
                'QA’d single-tree annotations, reproducible splits and '
                'comparative model evaluation. Published at ICPR 2022 and '
                'ISPRS 2023.',
    },
    {
        'company': 'Ontario Ministry of Natural Resources and Forestry',
        'role': 'Financial Analyst',
        'period': '2017 – 2018',
        'copy': 'Built Oracle-based reporting workflows that standardized '
                'recurring monthly financial reporting across offices, and '
                'wrote the guidance teams used to interpret the outputs.',
    },
]

EDUCATION = [
    ('M.E.Sc., Earth and Space Science & Engineering', 'York University',
     '2020 – 2022', 'Best Master’s Thesis Award, 2022'),
    ('H.B.Sc., Statistics (Quantitative Finance)', 'University of Toronto',
     '2015 – 2020', None),
]

# Employers, schools, research partners and funders, as one quiet strip at the
# foot of the credentials chapter. Rendered as one-colour marks: nine brand
# palettes would fight everything else on the page.
#
# The third value is a rendered height in pixels, set per mark rather than
# shared, because a bounding box is not optical weight — TELEDYNE is a bold
# wordmark that fills its box, the Lassonde lockup is small type inside a tall
# one. The fourth is the width that height produces, carried rather than
# computed because it becomes a `width` attribute: the strip is lazy-loaded at
# the bottom of a long page, and without both dimensions the footer jumps when
# the marks arrive.
AFFILIATIONS = [
    ('myseat', 'MySeat Media', 26, 56),
    ('york-lassonde', 'York University, Lassonde School of Engineering', 26, 166),
    ('university-of-toronto', 'University of Toronto', 24, 69),
    ('ontario-mnrf', 'Ontario Ministry of Natural Resources and Forestry', 26, 59),
    ('teledyne', 'Teledyne Optech', 17, 133),
    ('thales', 'Thales Canada', 22, 75),
    ('nserc', 'NSERC', 22, 55),
    ('ausm-lab', 'AUSM Lab', 20, 121),
    ('geoict', 'GeoICT Lab', 19, 135),
]


# ==========================================================================
# Pieces
# ==========================================================================

def _track(event: str, location: str, label: Optional[str] = None) -> dict:
    attrs = {'data-track': event, 'data-track-location': location}
    if label:
        attrs['data-track-label'] = label
    return attrs


def _arrow_link(text: str, href: str, class_name: str, track: dict, **kwargs):
    """A text link that ends in an arrow. The arrow is CSS, not a character in
    the string, so it can move on hover without the label moving with it."""
    return html.A(text, href=href, className=class_name, **track, **kwargs)


def _chapter_head(title: str, note: Optional[str] = None):
    """A chapter heading, and at most one line saying what is under it.

    The heading's weight comes from the class on the section — `chapter--major`
    sets it larger and gives it the space above; a plain chapter is announced
    by a rule instead.
    """
    children = [html.H2(title, className='chapter-title')]
    if note:
        children.append(html.P(note, className='chapter-note'))
    return html.Div(children, className='chapter-head')


def _hero():
    return html.Section(
        className='hero reveal-up',
        children=[
            # The headline takes the full width of the page rather than the
            # left track. At 56px a 60-character sentence needs about a
            # thousand pixels to sit on two lines, and a 650px column turns it
            # into four — which is not a dominant headline, it is a paragraph
            # set large. The supporting copy and the work sample split the row
            # underneath it.
            html.Div(
                'Product Analytics · Data Systems · Applied ML',
                className='hero-eyebrow',
            ),
            html.H1(
                className='hero-headline',
                children=[
                    'I turn product data into',
                    html.Br(),
                    'decision systems teams actually use.',
                ],
            ),
            html.Div(
                className='hero-lede',
                children=[
                    html.P(
                        'Product analytics, experimentation, and data systems '
                        'for real operating decisions.',
                        className='hero-support',
                    ),
                    html.Div(
                        className='hero-actions',
                        children=[
                            html.A('View selected work', href='#selected-systems',
                                   className='cta-primary',
                                   **_track('hero_cta_click', 'home_hero',
                                            'selected_work')),
                            html.A('Resume', href=RESUME_HREF,
                                   download='Hyungju_Lee_Resume.pdf',
                                   className='cta-secondary',
                                   **_track('hero_cta_click', 'home_hero',
                                            'download_resume')),
                            html.Span(
                                className='hero-profiles',
                                children=[
                                    html.A('LinkedIn', href=LINKEDIN_URL,
                                           target='_blank', rel='noreferrer',
                                           className='hero-link',
                                           **_track('hero_cta_click', 'home_hero',
                                                    'linkedin')),
                                    html.A('GitHub', href=GITHUB_URL,
                                           target='_blank', rel='noreferrer',
                                           className='hero-link',
                                           **_track('hero_cta_click', 'home_hero',
                                                    'github')),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            # Not decoration: a crop of a dashboard whose source is in this
            # repository, linking to the case study.
            #
            # It shows the product rather than one of its charts — the brand
            # selector, the four section tabs, the nine views behind them, the
            # KPI strip, and the head of one panel. The flagship below opens
            # with the trading surface in full and two more views under it, so
            # the page discloses the project rather than showing it twice: no
            # analytical view appears on this page more than once.
            html.A(
                href='/projects/tidepool-commerce-analytics',
                className='hero-visual',
                **_track('hero_visual_click', 'home_hero',
                         'tidepool-commerce-analytics'),
                children=[
                    html.Img(
                        src='/assets/demo_shots/hero-overview.jpg',
                        className='hero-visual-image',
                        alt='The Tidepool Commerce Analytics application: a brand '
                            'selector and date-window control above four section '
                            'tabs — sales performance, customers, marketing, '
                            'operations — a five-metric KPI strip, and the head of '
                            'the customer value panel.',
                        width=1032,
                        height=860,
                    ),
                    html.Span('Tidepool Commerce Analytics · built and shipped '
                              'end to end', className='hero-visual-caption'),
                ],
            ),
        ],
    )


def _proof():
    return html.Section(
        className='proof',
        **{'aria-label': 'Proof of scale'},
        children=[
            html.Div(
                className='proof-item',
                children=[
                    html.Div(figure, className='proof-value'
                             + ('' if figure[0].isdigit() or figure[0] == '$'
                                else ' proof-value--text')),
                    html.Div(label, className='proof-label'),
                    html.Div(source, className='proof-source'),
                ],
            )
            for figure, label, source in PROOF
        ],
    )


def _flagship():
    item = by_slug(FEATURED_SLUG)
    name, _, subtitle = item['title'].partition(' — ')

    return html.Article(
        className='flagship',
        children=[
            html.A(
                href=f"/projects/{item['slug']}",
                className='flagship-figure',
                **_track('featured_work_image_click', 'home_selected_systems',
                         item['slug']),
                children=[
                    html.Img(
                        src=item['shots'][0]['src'],
                        className='flagship-image',
                        alt=item['shots'][0]['alt'],
                        width=1600,
                        height=900,
                    ),
                    html.Span(
                        'Trading performance — revenue and orders on '
                        'independent axes, the promotion calendar overlaid, '
                        'outliers called out in place.',
                        className='flagship-image-caption',
                    ),
                ],
            ),
            html.Div(
                className='flagship-body',
                children=[
                    html.Div(
                        className='flagship-lede',
                        children=[
                            html.Div('Featured system', className='eyebrow'),
                            html.Div(item['scope'], className='project-scope'),
                            html.H3(name, className='flagship-title'),
                            html.Div(subtitle or item['domain'],
                                     className='flagship-subtitle'),
                            html.P(FLAGSHIP_COPY, className='flagship-copy'),
                            html.Div(
                                className='flagship-meta',
                                children=[
                                    html.Span(item['role']),
                                    html.Span(item['period'],
                                              className='flagship-period'),
                                ],
                            ),
                            html.Div(
                                className='flagship-actions',
                                children=[
                                    _arrow_link('Read case study',
                                                f"/projects/{item['slug']}",
                                                'arrow-link',
                                                _track('work_card_click',
                                                       'home_featured',
                                                       item['slug'])),
                                    _arrow_link('Open the live dashboard',
                                                item['href'],
                                                'arrow-link arrow-link--quiet',
                                                _track('demo_click',
                                                       'home_featured')),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className='flagship-evidence',
                        children=[
                            html.Div('Evidence', className='evidence-label'),
                            html.Ul(
                                className='evidence-list',
                                children=[html.Li(point) for point in
                                          FLAGSHIP_EVIDENCE],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className='flagship-shots',
                children=[
                    html.Figure(
                        className='flagship-shot',
                        children=[
                            html.Img(src=src, alt=alt,
                                     className='flagship-shot-image',
                                     width=1200, height=750),
                            html.Figcaption(caption,
                                            className='flagship-shot-caption'),
                        ],
                    )
                    for src, alt, caption in FLAGSHIP_SHOTS
                ],
            ),
        ],
    )


def _schematic(slug: str):
    """A system in three stages, drawn in type and hairlines.

    The two production systems belong to a client, so there is no screenshot to
    show. What a reader is judging is the shape anyway: what goes in, what it is
    turned into, and what somebody actually reads.
    """
    return html.Div(
        className='schematic',
        children=[
            html.Div(
                className='schematic-stage',
                children=[
                    html.Div(f'{index:02d}', className='schematic-index'),
                    html.Div(label, className='schematic-label'),
                    html.Div(body, className='schematic-body'),
                ],
            )
            for index, (label, body) in enumerate(SCHEMATICS[slug], start=1)
        ],
    )


def _system_card(slug: str, *, research: bool = False):
    item = by_slug(slug)
    class_name = 'system-card system-card--research' if research else 'system-card'

    if research:
        src, caption = RESEARCH_VISUALS[slug]
        visual = html.Div(
            className='system-visual',
            children=[
                html.Img(src=src, className='system-image',
                         alt=_FIGURES[src]['alt'], width=1200, height=750),
                html.Span(caption, className='system-visual-caption'),
            ],
        )
    else:
        visual = html.Div(
            className='system-visual system-visual--schematic',
            children=[
                _schematic(slug),
                html.Span('System shape — the software is a client\u2019s, so the '
                          'architecture stands in for a screenshot.',
                          className='system-visual-caption'),
            ],
        )

    return html.A(
        href=f"/projects/{slug}",
        className=class_name,
        **_track('work_card_click', 'home_selected_systems', slug),
        children=[
            visual,
            html.Div(
                className='system-body',
                children=[
                    html.Div(item['scope'], className='project-scope'),
                    html.H4(item['title'], className='system-title'),
                    html.P(outcome(item), className='system-outcome'),
                    tags(item, 3),
                    html.Span('Read case study', className='system-link'),
                ],
            ),
        ],
    )


def _tier(label: str, note: str, cards, *, research: bool = False):
    class_name = 'tier tier--research' if research else 'tier'
    return html.Div(
        className=class_name,
        children=[
            html.Div(
                className='tier-head',
                children=[
                    html.H3(label, className='tier-label'),
                    html.P(note, className='tier-note'),
                ],
            ),
            html.Div(cards, className='system-row'),
        ],
    )


def _selected_systems():
    return html.Section(
        id='selected-systems',
        className='chapter chapter--major',
        children=[
            _chapter_head(
                'Selected Systems',
                'One build I own end to end, two production analytics systems '
                'running against a live client portfolio, and the research '
                'infrastructure underneath the ML work. Each opens onto its '
                'own case study.',
            ),
            _flagship(),
            _tier(
                'Product / data systems',
                'Built at MySeat Media, in production against a 138-client app '
                'ecosystem.',
                [_system_card(slug) for slug in HOME_PRODUCT],
            ),
            _tier(
                'Applied ML / research',
                'Airborne LiDAR 3D detection at AUSM Lab — the datasets, '
                'benchmarks and evaluation behind two peer-reviewed papers.',
                [_system_card(slug, research=True) for slug in HOME_RESEARCH],
                research=True,
            ),
            _arrow_link('All seven projects', '/projects',
                        'arrow-link chapter-cta',
                        _track('work_index_click',
                               'home_selected_systems_footer')),
        ],
    )


def _practice():
    return html.Section(
        className='chapter chapter--major',
        children=[
            _chapter_head('What I Build'),
            html.Div(
                className='practice-row',
                children=[
                    html.Div(
                        className='practice-item',
                        children=[
                            html.Div(f'{index:02d}', className='practice-index'),
                            html.H3(title, className='practice-title'),
                            html.P(copy, className='practice-copy'),
                        ],
                    )
                    for index, (title, copy) in enumerate(PRACTICE, start=1)
                ],
            ),
            html.Div(
                className='stack',
                children=[
                    html.Div(
                        className='stack-row',
                        children=[
                            html.Div(label, className='stack-label'),
                            html.Div(
                                className='stack-terms',
                                children=[html.Span(term, className='stack-term')
                                          for term in terms],
                            ),
                        ],
                    )
                    for label, terms in STACK
                ],
            ),
        ],
    )


def _experience():
    return html.Section(
        className='chapter',
        children=[
            _chapter_head('Experience'),
            html.Div(
                className='record',
                children=[
                    html.Article(
                        className='record-entry',
                        children=[
                            html.Div(
                                className='record-head',
                                children=[
                                    html.H3(role['company'],
                                            className='record-company'),
                                    html.Div(role['role'],
                                             className='record-role'),
                                    html.Div(role['period'],
                                             className='record-period'),
                                ],
                            ),
                            html.P(role['copy'], className='record-copy'),
                        ],
                    )
                    for role in EXPERIENCE
                ],
            ),
            _arrow_link('View full résumé', RESUME_HREF,
                        'arrow-link arrow-link--quiet chapter-cta',
                        _track('resume_click', 'home_experience'),
                        download='Hyungju_Lee_Resume.pdf'),
        ],
    )


def _credentials():
    return html.Section(
        className='chapter',
        children=[
            _chapter_head('Education & Credentials'),
            html.Div(
                className='record record--education',
                children=[
                    html.Div(
                        className='record-entry',
                        children=[
                            html.Div(
                                className='record-head',
                                children=[
                                    html.Div(degree, className='record-company'),
                                    html.Div(school, className='record-role'),
                                    html.Div(years, className='record-period'),
                                ],
                            ),
                        ] + ([html.Div(note, className='record-note')] if note else []),
                    )
                    for degree, school, years, note in EDUCATION
                ],
            ),
            html.Div(
                className='affiliations',
                children=[
                    html.Div('Worked with and studied at',
                             className='affiliations-label'),
                    html.Div(
                        className='affiliations-grid',
                        children=[
                            html.Img(src=f'/assets/logos/{slug}.png', alt=name,
                                     title=name, className='affiliation-mark',
                                     width=width, height=height)
                            for slug, name, height, width in AFFILIATIONS
                        ],
                    ),
                ],
            ),
        ],
    )


def _footer():
    return html.Section(
        className='home-footer',
        **{'aria-label': 'Contact'},
        children=[
            html.Div(
                className='home-footer-lede',
                children=[
                    html.Div('Open to product analytics, analytics engineering '
                             'and applied data science roles.',
                             className='home-footer-line'),
                    html.Div(f'{LOCATION} · {PHONE_DISPLAY}',
                             className='home-footer-meta'),
                ],
            ),
            html.Div(
                className='home-footer-links',
                children=[
                    html.A(EMAIL, href=f'mailto:{EMAIL}', className='hero-link',
                           **_track('footer_click', 'home_footer', 'email')),
                    html.A('LinkedIn', href=LINKEDIN_URL, target='_blank',
                           rel='noreferrer', className='hero-link',
                           **_track('footer_click', 'home_footer', 'linkedin')),
                    html.A('GitHub', href=GITHUB_URL, target='_blank',
                           rel='noreferrer', className='hero-link',
                           **_track('footer_click', 'home_footer', 'github')),
                    html.A('Resume', href=RESUME_HREF,
                           download='Hyungju_Lee_Resume.pdf',
                           className='hero-link',
                           **_track('footer_click', 'home_footer', 'resume')),
                ],
            ),
        ],
    )


layout = html.Div(
    className='content-stack content-stack--home',
    children=[
        _hero(),
        _proof(),
        _selected_systems(),
        _practice(),
        _experience(),
        _credentials(),
        _footer(),
    ],
)
