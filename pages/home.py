from typing import List

import dash
from dash import html

from profile_data import EMAIL, GITHUB_URL, LINKEDIN_URL, LOCATION, PHONE_DISPLAY
from work_ui import FEATURED_SLUG, HOME_SECONDARY, by_slug, outcome, tags, work_card


dash.register_page(__name__, path='/', order=0, name='Home')


# The evidence for the headline, with one figure carrying it. The primary proof
# is the scale of the production analytics work; the two secondary proofs say
# how broad it was and that the research behind it was peer-reviewed.
PRIMARY_PROOF = ('1.6B+', 'session-minutes analyzed',
                 'through production analytics and reporting systems')

SECONDARY_PROOF = [
    ('138', 'client-app portfolio'),
    ('ICPR / ISPRS', 'research publications'),
]

CAPABILITY_LANES = [
    {
        'title': 'Product Analytics / Decision Systems',
        'copy': 'KPI architecture, retention and monetization, and operating reviews.',
        'tags': ['Metric Contracts', 'Retention', 'Monetization', 'Experimentation'],
    },
    {
        'title': 'Data Systems / Automation',
        'copy': 'SQL and Python analytics engineering: data models, pipelines, automation.',
        'tags': ['Analytics Engineering', 'Data Modeling', 'Pipeline Automation', 'Data Quality'],
    },
    {
        'title': 'AI / ML / Research Work',
        'copy': 'LiDAR and 3D vision research: datasets, benchmarks, model evaluation.',
        'tags': ['LiDAR / 3D Vision', 'Detection', 'Segmentation', 'Benchmark Design'],
    },
]

# Four groups, six to eight terms each: evidence of breadth, not an inventory.
# The granular vocabulary each of these stands for is in the case studies and in
# the Tools and methods rail beside them.
SKILL_GROUPS = [
    (
        'Product Analytics',
        ['KPI Architecture', 'Retention & Churn', 'Monetization', 'Behavioral Segmentation',
         'Experimentation', 'Executive Reporting'],
    ),
    (
        'Data Systems & Automation',
        ['Analytics Engineering', 'Data Modeling', 'ETL Pipelines', 'Scheduled Workflows',
         'Data Quality Monitoring', 'Multi-Tenant Reporting'],
    ),
    (
        'AI / ML & Research',
        ['Computer Vision', '3D Vision / LiDAR', 'Deep Learning Workflows', 'Detection & Segmentation',
         'Benchmark Design', 'Model Evaluation'],
    ),
    (
        'Languages & Tools',
        ['Python', 'SQL', 'R', 'TypeScript', 'Pandas / Polars', 'Plotly / Dash',
         'React', 'FastAPI'],
    ),
]

# Employers, schools, research partners and funders, in one strip at the foot of
# the page. Rendered as one-colour marks: nine brand palettes, half of them on
# white rectangles, would fight everything else on the page.
#
# The third value is a rendered height in pixels, set per mark rather than
# shared: a bounding box is not optical weight. TELEDYNE is a bold wordmark that
# fills its box, while the Lassonde lockup is small type inside a tall one, so
# the same height makes one shout and the other vanish.
#
# The fourth is the width that height produces. Every source file is 120px tall,
# so it is `round(intrinsic_width * height / 120)`. It is carried here rather
# than computed because it becomes a `width` attribute on the image: the strip
# is lazy-loaded at the bottom of a long page, and without both dimensions the
# marks occupy nothing until they arrive and the footer jumps when they do.
AFFILIATIONS = [
    ('myseat', 'MySeat Media', 30, 65),
    ('york-lassonde', 'York University, Lassonde School of Engineering', 30, 191),
    ('university-of-toronto', 'University of Toronto', 28, 80),
    ('ontario-mnrf', 'Ontario Ministry of Natural Resources and Forestry', 30, 68),
    ('teledyne', 'Teledyne Optech', 20, 157),
    ('thales', 'Thales Canada', 26, 89),
    ('nserc', 'NSERC', 26, 65),
    ('ausm-lab', 'AUSM Lab', 24, 145),
    ('geoict', 'GeoICT Lab', 22, 156),
]


def _tag_cloud(tags: List[str]):
    return html.Div(
        className='skill-cloud',
        children=[html.Span(tag, className='skill-pill') for tag in tags],
    )


def _skill_group(title: str, skills: List[str]):
    return html.Div(
        className='glass-card skill-level-card',
        children=[
            html.H3(title, className='skill-level-title'),
            _tag_cloud(skills),
        ],
    )


def _lane_card(title: str, copy: str, tags: List[str]):
    return html.Article(
        className='glass-card lane-card reveal-up',
        children=[
            html.H3(title, className='lane-title'),
            html.P(copy, className='lane-copy'),
            _tag_cloud(tags),
        ],
    )


def _experience_block(title: str, company: str, period: str, location: str, bullets: List[str]):
    return html.Article(
        className='glass-card experience-card reveal-up',
        children=[
            # The header's two halves are placed directly on the entry's grid
            # (`.exp-head` is display:contents), so the bullet list beneath them
            # can span both columns instead of sitting in the left one.
            html.Div(
                className='exp-head',
                children=[
                    html.Div(
                        className='exp-identity',
                        children=[
                            html.H3(title, className='exp-title'),
                            html.Div(company, className='exp-company'),
                        ],
                    ),
                    html.Div(
                        className='exp-meta',
                        children=[
                            html.Div(f'Engagement: {period}', className='exp-period'),
                            html.Div(location, className='exp-location'),
                        ],
                    ),
                ],
            ),
            html.Ul([html.Li(b) for b in bullets], className='exp-bullets'),
        ],
    )


def _featured_card():
    """The featured project: a picture, the outcome, and a way in.

    It is the only home-page card with a screenshot, because it is the only item
    whose software this repository actually contains. Everything else about it
    is the same card the index uses.
    """
    item = by_slug(FEATURED_SLUG)
    return html.Article(
        className='glass-card card-hover featured-work',
        children=[
            html.A(
                href=f"/projects/{item['slug']}",
                className='featured-work-image-link',
                tabIndex='-1',
                **{
                    'aria-hidden': 'true',
                    'data-track': 'featured_work_image_click',
                    'data-track-location': 'home_selected_work',
                    'data-track-label': item['slug'],
                },
                children=html.Img(
                    src=item['shots'][0]['src'],
                    className='featured-work-image',
                    alt=item['shots'][0]['alt'],
                ),
            ),
            html.Div(
                className='featured-work-body',
                children=[
                    html.Div('FEATURED PROJECT', className='eyebrow'),
                    html.Div(item['scope'], className='project-scope'),
                    html.H3(item['title'], className='featured-work-title'),
                    html.P(outcome(item), className='featured-work-outcome'),
                    html.Div(
                        className='work-card-meta',
                        children=[
                            html.Span(item['role'], className='work-card-role'),
                            html.Span(item['period'], className='work-card-period'),
                        ],
                    ),
                    tags(item, 4),
                    html.A(
                        'Read case study',
                        href=f"/projects/{item['slug']}",
                        className='featured-work-link',
                        **{
                            'data-track': 'work_card_click',
                            'data-track-location': 'home_featured',
                            'data-track-label': item['slug'],
                        },
                    ),
                ],
            ),
        ],
    )


layout = html.Div(
    className='content-stack',
    children=[
        # One proposition, then the evidence for it, in one column. The formal
        # role is in the eyebrow, so it is not repeated above the figure, and
        # the portrait now lives on the Contact page, where a face belongs.
        html.Section(
            className='hero reveal-up',
            children=[
                html.Div(
                    'HYUNGJU LEE · PRODUCT DATA SCIENTIST / ANALYTICS ENGINEER',
                    className='hero-eyebrow',
                ),
                html.H1(
                    'I turn product data into decision systems teams actually use.',
                    className='hero-headline',
                ),
                html.P(
                    'Product analytics, data systems, and applied ML research for '
                    'measurable operating decisions.',
                    className='hero-support',
                ),
                html.Div(
                    className='hero-proof',
                    children=[
                        html.Div('PROOF OF SCALE', className='hero-proof-eyebrow'),
                        html.Div(
                            className='hero-proof-primary',
                            children=[
                                html.Div(
                                    className='hero-proof-headline',
                                    children=[
                                        html.Span(PRIMARY_PROOF[0], className='hero-proof-value'),
                                        html.Span(PRIMARY_PROOF[1], className='hero-proof-label'),
                                    ],
                                ),
                                html.Div(PRIMARY_PROOF[2], className='hero-proof-note'),
                            ],
                        ),
                        html.Div(
                            className='hero-proof-secondary',
                            children=[
                                html.Div(
                                    className='hero-proof-item',
                                    children=[
                                        html.Span(figure, className='hero-proof-figure'),
                                        html.Span(label, className='hero-proof-text'),
                                    ],
                                )
                                for figure, label in SECONDARY_PROOF
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className='hero-cta',
                    children=[
                        # Two buttons, then two text links. The work and the
                        # resume are what a reader is here for; the profiles are
                        # destinations, not calls to action, and are set as links
                        # so the two real CTAs stay legible as the only buttons.
                        html.A(
                            'View selected work',
                            href='/projects',
                            className='cta-primary',
                            **{
                                'data-track': 'hero_cta_click',
                                'data-track-location': 'home_hero',
                                'data-track-label': 'selected_work',
                            },
                        ),
                        html.A(
                            'Download resume',
                            href='/assets/Hyungju_Lee_Resume.pdf',
                            download='Hyungju_Lee_Resume.pdf',
                            className='cta-secondary',
                            **{
                                'data-track': 'hero_cta_click',
                                'data-track-location': 'home_hero',
                                'data-track-label': 'download_resume',
                            },
                        ),
                        html.A(
                            'LinkedIn',
                            href=LINKEDIN_URL,
                            className='hero-link',
                            target='_blank',
                            rel='noreferrer',
                            **{
                                'data-track': 'hero_cta_click',
                                'data-track-location': 'home_hero',
                                'data-track-label': 'linkedin',
                            },
                        ),
                        html.A(
                            'GitHub',
                            href=GITHUB_URL,
                            className='hero-link',
                            target='_blank',
                            rel='noreferrer',
                            **{
                                'data-track': 'hero_cta_click',
                                'data-track-location': 'home_hero',
                                'data-track-label': 'github',
                            },
                        ),
                    ],
                ),
                html.Div(
                    f'{LOCATION} | {PHONE_DISPLAY} | {EMAIL}',
                    className='hero-contact',
                ),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H2('Capability Lanes', className='section-title'),
                html.P(
                    'The profile is intentionally multi-lane: production analytics, data systems, and AI/ML research work.',
                    className='section-note',
                ),
                html.Div(
                    className='lane-grid',
                    children=[_lane_card(lane['title'], lane['copy'], lane['tags']) for lane in CAPABILITY_LANES],
                ),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H2('Selected Work', className='section-title'),
                # The featured item is the one whose software this repository
                # actually contains, so it is the only one that gets a picture.
                _featured_card(),
                html.Div(
                    className='work-grid work-grid--secondary',
                    children=[work_card(by_slug(slug), track_location='home_selected_work')
                              for slug in HOME_SECONDARY],
                ),
                html.A(
                    'View all projects',
                    href='/projects',
                    className='cta-secondary section-cta',
                    **{'data-track': 'work_index_click',
                       'data-track-location': 'home_selected_work_footer'},
                ),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H2('Core Skills', className='section-title'),
                html.P(
                    'Five capability clusters covering product measurement, data systems, and research-oriented technical work.',
                    className='section-note',
                ),
                html.Div(
                    className='skill-level-grid',
                    children=[_skill_group(title, skills) for title, skills in SKILL_GROUPS],
                ),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H2('Experience', className='section-title'),
                _experience_block(
                    'Data Scientist / Analytics Engineer',
                    'MySeat Media',
                    '2023 – Present',
                    'Toronto, ON, Canada',
                    [
                        'Built KPI and decision systems spanning engagement, retention, churn, livestream activity, memberships, and revenue across a 138-client app ecosystem.',
                        'Productionized SQL and Python data workflows across 17M+ sessions and '
                        '1.6B+ session-minutes for release diagnostics, segmentation, and '
                        'cross-client benchmarking.',
                        'Unified longitudinal analytics across 138 clients and 369K+ represented users, turning fragmented logs into reusable analytics infrastructure.',
                        'Led measurement and monetization analysis across $733K+ in subscription and in-app purchase revenue, linking revenue movement to behavior, acquisition, and membership signals.',
                        'Built dashboards, diagnostic tooling, and quasi-experimental evaluation used by product, growth, and leadership teams for recurring operating reviews, with 34 scheduled jobs refreshing executive and client reporting unattended.',
                    ],
                ),
                _experience_block(
                    'Research Engineer / Computer Vision Researcher',
                    'AUSM Lab',
                    '2019 – 2024 (concurrent)',
                    'Toronto, ON, Canada',
                    [
                        'Built reproducible dataset, annotation, and experiment workflows for airborne LiDAR research, covering preprocessing, label QA, benchmark splits, and evaluation assets for 3D vision studies.',
                        'Produced 5,000+ benchmark-grade single-tree annotations and supported large-scale LiDAR datasets used for detection and semantic segmentation research.',
                        'Ran deep learning experiment cycles for LiDAR-based detection workflows, comparing model behavior, input representations, and evaluation settings.',
                        'Synthesized results into thesis and publication outputs including ICPR 2022, ISPRS 2023, and a Best Master\'s Thesis award at York University.',
                        'Expanded the research footprint beyond annotation into benchmarking, comparative model analysis, scene-understanding-adjacent dataset work, and technical experimentation.',
                    ],
                ),
                _experience_block(
                    'Financial Analyst',
                    'Ontario Ministry of Natural Resources and Forestry',
                    '2017 – 2018',
                    'Peterborough, ON, Canada',
                    [
                        'Built Oracle-based reporting workflows to standardize recurring monthly financial reporting across offices.',
                        'Defined reporting guidance and trained teams to improve adoption and interpretation of performance outputs.',
                    ],
                ),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H2('Education', className='section-title'),
                html.Div(
                    className='glass-card edu-card',
                    children=[
                        html.Div('M.E.Sc., Earth and Space Science & Engineering', className='edu-title'),
                        html.Div('York University | 2020 - 2022', className='edu-meta'),
                        html.Div("Best Master's Thesis Award (2022)", className='edu-note'),
                        html.Hr(),
                        html.Div('H.B.Sc., Statistics (Quantitative Finance Stream)', className='edu-title'),
                        html.Div('University of Toronto | 2015 - 2020', className='edu-meta'),
                    ],
                ),
            ],
        ),
        # Supporting credibility, not the central proof of value: it sits after
        # the record it supports rather than interrupting the run from the
        # proposition to the work.
        html.Section(
            className='affiliations reveal-up',
            children=[
                html.Div('Worked with and studied at', className='affiliations-label'),
                html.Div(
                    className='affiliations-grid',
                    children=[
                        html.Img(
                            src=f'/assets/logos/{slug}.png',
                            alt=name,
                            title=name,
                            className='affiliation-mark',
                            width=width,
                            height=height,
                        )
                        for slug, name, height, width in AFFILIATIONS
                    ],
                ),
            ],
        ),
    ],
)
