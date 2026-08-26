from typing import List

import dash
from dash import html

from case_studies import CASE_STUDIES, RESEARCH_HIGHLIGHTS
from profile_data import EMAIL, GITHUB_URL, LINKEDIN_URL, LOCATION, PHONE_DISPLAY


dash.register_page(__name__, path='/', order=0, name='Home')


# Deliberately not the three words already in the descriptor above them: these
# say what the work actually consists of.
HERO_SIGNAL_PILLS = [
    'KPI Architecture',
    'Event Instrumentation',
    'Retention & Churn',
    'Subscription Revenue',
    'Quasi-Experimental Design',
    'LiDAR 3D Detection',
]

IMPACT_CHIPS = [
    ('138', 'Client portfolio',
     'Mobile and streaming apps reporting on one source-of-truth KPI layer'),
    ('1.6B+', 'Session-minutes analysed',
     'Six years of longitudinal engagement across a 774K-user base'),
    ('34', 'Scheduled jobs in production',
     'Executive and client reporting that refreshes without anyone touching it'),
    ('5,000+', 'Labelled benchmark objects',
     'LiDAR annotation and evaluation workflows behind two published datasets'),
    ('ICPR · ISPRS', 'Peer-reviewed venues',
     'Plus the Best Master\u2019s Thesis award, York University 2022'),
]

CAPABILITY_LANES = [
    {
        'title': 'Product Analytics / Decision Systems',
        'copy': 'KPI architecture, behavioral diagnostics, experimentation, monetization analysis, and operating reviews used to support product and growth decisions.',
        'tags': ['Metric Contracts', 'Retention', 'Monetization', 'Cohorts', 'Quasi-Experimental Analysis', 'Decision Dashboards'],
    },
    {
        'title': 'Data Systems / Automation',
        'copy': 'SQL and Python workflows for analytics engineering, multi-tenant data models, recurring reporting, automation, and decision-ready reporting surfaces.',
        'tags': ['Analytics Engineering', 'Data Modeling', 'ETL Workflows', 'Automation', 'Dash / FastAPI', 'Data Quality'],
    },
    {
        'title': 'AI / ML / Research Work',
        'copy': 'LiDAR, point cloud, and computer-vision research spanning dataset curation, benchmark design, deep learning experimentation, evaluation, and technical synthesis.',
        'tags': ['Computer Vision', '3D Vision', 'LiDAR', 'Detection', 'Segmentation', 'Benchmarking'],
    },
]

SKILL_GROUPS = [
    (
        'Languages & Data',
        ['Python', 'SQL', 'R', 'TypeScript', 'Pandas', 'Polars', 'NumPy',
         'Dash/Plotly', 'React', 'Flask / FastAPI'],
    ),
    (
        'Product Analytics & Decision Systems',
        ['KPI Architecture', 'Success Metrics', 'Behavioral Segmentation', 'Retention & Churn', 'Monetization Analytics', 'Executive Review Systems'],
    ),
    (
        'Data Systems & Automation',
        ['Analytics Engineering', 'Data Modeling', 'Automation Pipelines', 'Scheduled Workflows', 'Data Quality Monitoring', 'Multi-Tenant Reporting'],
    ),
    (
        'AI / ML / Research',
        ['Computer Vision', '3D Vision', 'LiDAR / Point Clouds', 'Deep Learning Workflows', 'Dataset / Annotation Pipelines', 'Detection & Segmentation'],
    ),
    (
        'Measurement / Evaluation',
        ['Benchmark Design', 'Comparative Model Analysis', 'Statistical Diagnostics', 'Quasi-Experimental Analysis', 'Error Analysis', 'Research Synthesis'],
    ),
]

# Employers, schools, research partners and funders, in one strip under the
# portrait. Rendered as one-colour marks: eight brand palettes, half of them on
# white rectangles, would fight everything else on the page.
# The third value is a rendered height in pixels, set per mark rather than
# shared: a bounding box is not optical weight. TELEDYNE is a bold wordmark that
# fills its box, while the Lassonde lockup is small type inside a tall one, so
# the same height makes one shout and the other vanish.
AFFILIATIONS = [
    ('myseat', 'MySeat Media', 30),
    ('york-lassonde', 'York University, Lassonde School of Engineering', 30),
    ('university-of-toronto', 'University of Toronto', 28),
    ('ontario-mnrf', 'Ontario Ministry of Natural Resources and Forestry', 30),
    ('teledyne', 'Teledyne Optech', 20),
    ('thales', 'Thales Canada', 26),
    ('nserc', 'NSERC', 26),
    ('ausm-lab', 'AUSM Lab', 24),
    ('geoict', 'GeoICT Lab', 22),
]


RESUME_TRACKS = [
    {
        'title': 'Product / Analytics',
        'copy': 'Strongest for product data scientist, growth analytics, monetization, KPI systems, and decision-support roles.',
    },
    {
        'title': 'AI / ML',
        'copy': 'Signals LiDAR, computer vision, dataset engineering, evaluation methodology, and applied ML research workflows.',
    },
    {
        'title': 'Hybrid Technical',
        'copy': 'Blends analytics engineering, technical generalist data science, data systems, and research-oriented execution.',
    },
]


def _impact_chip(value: str, label: str, detail: str):
    # A chip whose value is a name, not a figure, needs a smaller type size or it
    # sets the height of the whole row.
    value_class = 'impact-value'
    if not any(character.isdigit() for character in value):
        value_class += ' impact-value--text'
    return html.Div(
        className='impact-chip',
        children=[
            html.Div(value, className=value_class),
            html.Div(label, className='impact-label'),
            html.Div(detail, className='impact-detail'),
        ],
    )


def _tag_cloud(tags: List[str]):
    return html.Div(
        className='skill-cloud',
        children=[html.Span(tag, className='skill-pill') for tag in tags],
    )


def _skill_group(title: str, skills: List[str]):
    return html.Div(
        className='glass-card skill-level-card',
        children=[
            html.H4(title, className='skill-level-title'),
            _tag_cloud(skills),
        ],
    )


def _lane_card(title: str, copy: str, tags: List[str]):
    return html.Article(
        className='glass-card lane-card reveal-up',
        children=[
            html.H4(title, className='lane-title'),
            html.P(copy, className='lane-copy'),
            _tag_cloud(tags),
        ],
    )


def _experience_block(title: str, company: str, period: str, location: str, bullets: List[str]):
    return html.Article(
        className='glass-card experience-card reveal-up',
        children=[
            html.Div(
                className='exp-head',
                children=[
                    html.Div(
                        [
                            html.H4(title, className='exp-title'),
                            html.Div(company, className='exp-company'),
                        ]
                    ),
                    html.Div([html.Div(period), html.Div(location)], className='exp-meta'),
                ],
            ),
            html.Ul([html.Li(b) for b in bullets], className='exp-bullets'),
        ],
    )


def _case_preview_card(case, primary: bool = False):
    card_class = 'glass-card featured-case-card'
    if primary:
        card_class += ' featured-case-card-primary'

    return html.Article(
        className=card_class,
        children=[
            # The card's button below points at the same anchor, so the image
            # link is hidden from assistive tech and the tab order rather than
            # announced as a second, unlabelled copy of it.
            html.A(
                href=f"/projects#{case['slug']}",
                className='featured-case-image-link',
                tabIndex='-1',
                **{
                    'aria-hidden': 'true',
                    'data-track': 'featured_case_image_click',
                    'data-track-location': 'home_featured_case',
                    'data-track-label': case['slug'],
                },
                children=html.Img(
                    src=case['thumbnail_src'],
                    className='featured-case-image',
                    alt=case['thumbnail_alt'],
                ),
            ),
            html.Div(
                className='featured-case-body',
                children=[
                    html.Div(case['scope'], className='project-scope'),
                    html.H4(case['title'], className='featured-case-title'),
                    html.P(case['problem_line'], className='featured-case-summary'),
                    _tag_cloud(case['tags']),
                    html.Ul(
                        className='featured-case-highlights',
                        children=[html.Li(item) for item in case['highlights']],
                    ),
                    html.P(case['homepage_caption'], className='featured-case-caption'),
                    html.A(
                        'View Work Sample',
                        href=f"/projects#{case['slug']}",
                        className='cta-secondary featured-case-cta',
                        **{
                            'data-track': 'featured_case_cta_click',
                            'data-track-location': 'home_featured_case',
                            'data-track-label': case['slug'],
                        },
                    ),
                ],
            ),
        ],
    )


def _research_preview_card(item):
    return html.Article(
        className='glass-card research-highlight-card reveal-up',
        children=[
            html.Div(item['scope'], className='project-scope'),
            html.H4(item['title'], className='research-highlight-title'),
            html.P(item['problem_line'], className='research-highlight-summary'),
            _tag_cloud(item['tags']),
            html.Ul(
                className='research-highlight-list',
                children=[html.Li(point) for point in item['highlights']],
            ),
            html.P(item['homepage_caption'], className='research-highlight-caption'),
            html.A(
                'View Project Summary',
                href=f"/projects#{item['slug']}",
                className='cta-secondary featured-case-cta',
            ),
        ],
    )


def _resume_track_card(title: str, copy: str):
    return html.Div(
        className='glass-card resume-track-card reveal-up',
        children=[
            html.H4(title, className='resume-track-title'),
            html.P(copy, className='resume-track-copy'),
        ],
    )


layout = html.Div(
    className='content-stack',
    children=[
        html.Section(
            className='hero reveal-up',
            children=[
                html.Div(
                    className='hero-copy',
                    children=[
                        html.Div('HYUNGJU LEE', className='hero-name'),
                        html.H1('Product Data Scientist, Analytics Engineer',
                                className='hero-role'),
                        html.Div(
                            'Product Analytics · Analytics Engineering · Applied ML Research',
                            className='hero-role-descriptor',
                        ),
                        html.P(
                            'I own the measurement layer of a subscription product end to end.',
                            className='hero-title',
                        ),
                        html.P(
                            'Source-of-truth KPI definitions, the event instrumentation and SQL/Python '
                            'pipelines underneath them, and the reporting executives decide from \u2014 '
                            'across a 138-client mobile and streaming portfolio with six years of '
                            'longitudinal history. Statistics-trained, with peer-reviewed machine '
                            'learning research in LiDAR 3D object detection.',
                            className='hero-subtitle',
                        ),
                        html.Div(
                            className='hero-signal-row',
                            children=[html.Span(pill, className='hero-signal-pill') for pill in HERO_SIGNAL_PILLS],
                        ),
                        html.Div(
                            className='hero-cta',
                            children=[
                                # Selected Work and Live Demo sit in the nav
                                # directly above this row; the hero offers what
                                # navigation cannot reach instead of repeating it.
                                html.A(
                                    'Resume (PDF)',
                                    href='/assets/Hyungju_Lee_Resume.pdf',
                                    download='Hyungju_Lee_Resume.pdf',
                                    className='cta-primary',
                                    **{
                                        'data-track': 'hero_cta_click',
                                        'data-track-location': 'home_hero',
                                        'data-track-label': 'download_resume',
                                    },
                                ),
                                html.A(
                                    'LinkedIn',
                                    href=LINKEDIN_URL,
                                    className='cta-secondary',
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
                                    className='cta-secondary',
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
                html.Div(
                    className='hero-photo-wrap',
                    children=[
                        html.Img(
                            src='/assets/my_pic_web.jpg',
                            className='hero-photo',
                            alt='Portrait of Hyungju Lee',
                        ),
                        html.Div(
                            className='affiliations',
                            children=[
                                html.Div('Worked with and studied at',
                                         className='affiliations-label'),
                                html.Div(
                                    className='affiliations-grid',
                                    children=[
                                        html.Img(
                                            src=f'/assets/logos/{slug}.png',
                                            alt=name,
                                            title=name,
                                            className='affiliation-mark',
                                            style={'maxHeight': f'{height}px'},
                                        )
                                        for slug, name, height in AFFILIATIONS
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Section(
            className='impact-row reveal-up',
            children=[_impact_chip(*chip) for chip in IMPACT_CHIPS],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H3('Capability Lanes', className='section-title'),
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
                html.H3('Selected Work', className='section-title'),
                html.P(
                    'Representative work across product analytics, technical decision systems, and AI/ML-oriented research.',
                    className='section-note',
                ),
                html.Div('PRODUCT ANALYTICS / DECISION SYSTEMS', className='eyebrow'),
                html.P(
                    [
                        'Production-facing systems for KPI monitoring, behavioral diagnostics, '
                        'segmentation, and operating reviews. All three run as an ',
                        html.A('interactive dashboard', href='/dashboard',
                               className='inline-link',
                               **{'data-track': 'live_demo_click',
                                  'data-track-location': 'home_selected_work'}),
                        '.',
                    ],
                    className='subsection-note',
                ),
                html.Div(
                    className='featured-case-grid',
                    children=[_case_preview_card(case, primary=index == 0) for index, case in enumerate(CASE_STUDIES)],
                ),
                html.Div('AI / ML / RESEARCH WORK', className='eyebrow section-subhead'),
                html.P(
                    'Compact research and technical summaries from AUSM Lab work in LiDAR, 3D vision, benchmarking, and evaluation methodology.',
                    className='subsection-note',
                ),
                html.Div(
                    className='research-highlight-grid',
                    children=[_research_preview_card(item) for item in RESEARCH_HIGHLIGHTS],
                ),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H3('Core Skills', className='section-title'),
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
                html.H3('Experience', className='section-title'),
                _experience_block(
                    'Data Scientist / Analytics Engineer',
                    'MySeat Media',
                    '2023 - Present',
                    'Toronto, ON, Canada',
                    [
                        'Built KPI and decision systems spanning engagement, retention, churn, livestream activity, memberships, and revenue across a 138-client app ecosystem.',
                        'Productionized SQL and Python data workflows across 17M+ sessions and '
                        '1.6B+ session-minutes for release diagnostics, segmentation, and '
                        'cross-client benchmarking.',
                        'Unified longitudinal analytics across 138 clients and 369K+ represented users, turning fragmented logs into reusable analytics infrastructure.',
                        'Led measurement and monetization analysis across $733K+ in subscription and in-app purchase revenue, linking revenue movement to behavior, acquisition, and membership signals.',
                        'Built dashboards, diagnostic tooling, and quasi-experimental evaluation used by product, growth, and leadership teams for recurring operating reviews.',
                    ],
                ),
                _experience_block(
                    'Research Engineer / Computer Vision Researcher',
                    'AUSM Lab',
                    '2019 - 2024 (Concurrent Research)',
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
                    '2017 - 2018',
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
                html.H3('Resume Track', className='section-title'),
                html.P(
                    'The current downloadable PDF is positioned as a broader hybrid technical profile and can credibly support multiple read paths.',
                    className='section-note',
                ),
                html.Div(
                    className='resume-track-grid',
                    children=[_resume_track_card(track['title'], track['copy']) for track in RESUME_TRACKS],
                ),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H3('Education', className='section-title'),
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
    ],
)
