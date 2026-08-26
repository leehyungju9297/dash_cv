import dash
from dash import html

from case_studies import CASE_STUDIES, LIVE_DEMO, RESEARCH_HIGHLIGHTS


dash.register_page(__name__, path='/projects', order=1, name='Selected Work')


def _list_section(title: str, items):
    return html.Div(
        className='case-detail-block',
        children=[
            html.H4(title, className='case-detail-label'),
            html.Ul(className='case-detail-list', children=[html.Li(item) for item in items]),
        ],
    )


def _text_section(title: str, text: str):
    return html.Div(
        className='case-detail-block',
        children=[
            html.H4(title, className='case-detail-label'),
            html.P(text, className='case-detail-copy'),
        ],
    )


def _demo_showcase():
    """The live demo, as its own work item.

    It used to be introduced as an interactive version of the case studies below.
    It is not: it is a separate build in a different domain, and the honest way
    to show it is on its own terms with its own screenshots.
    """
    return html.Article(
        id=LIVE_DEMO['slug'],
        className='glass-card case-study-card demo-showcase reveal-up',
        children=[
            html.Div(LIVE_DEMO['scope'], className='project-scope'),
            html.H3(LIVE_DEMO['title'], className='case-study-title'),
            html.P(LIVE_DEMO['problem_line'], className='case-study-problem'),
            html.Div(
                className='skill-cloud case-tag-cloud',
                children=[html.Span(tag, className='skill-pill')
                          for tag in LIVE_DEMO['tags']],
            ),
            html.Div(
                className='demo-shot-grid',
                children=[
                    html.Figure(
                        className='demo-shot',
                        children=[
                            html.A(
                                href=shot['src'],
                                target='_blank',
                                rel='noreferrer',
                                className='case-study-image-link',
                                **{
                                    'data-track': 'demo_image_expand',
                                    'data-track-location': 'case_studies_page',
                                    'data-track-label': shot['src'].rsplit('/', 1)[-1],
                                },
                                children=html.Img(
                                    src=shot['src'],
                                    className='case-study-image',
                                    alt=shot['alt'],
                                ),
                            ),
                            html.Figcaption(shot['caption'],
                                            className='case-study-caption'),
                        ],
                    )
                    for shot in LIVE_DEMO['shots']
                ],
            ),
            html.Ul(
                className='case-study-list',
                children=[html.Li(item) for item in LIVE_DEMO['highlights']],
            ),
            html.A(
                'Open the live demo \u2192',
                href=LIVE_DEMO['href'],
                className='cta-secondary',
                **{
                    'data-track': 'case_study_demo_click',
                    'data-track-location': 'case_studies_page',
                },
            ),
        ],
    )


def _work_card(item):
    children = [
        html.Div(item['scope'], className='project-scope'),
        html.H3(item['title'], className='case-study-title'),
        html.P(item['problem_line'], className='case-study-problem'),
        html.Div(
            className='skill-cloud case-tag-cloud',
            children=[html.Span(tag, className='skill-pill') for tag in item['tags']],
        ),
    ]

    if item.get('thumbnail_src'):
        children.append(
            html.Figure(
                className='case-study-figure',
                children=[
                    html.A(
                        href=item['thumbnail_src'],
                        target='_blank',
                        rel='noreferrer',
                        className='case-study-image-link',
                        **{
                            'data-track': 'case_study_image_expand',
                            'data-track-location': 'case_studies_page',
                            'data-track-label': item['slug'],
                        },
                        children=html.Img(
                            src=item['thumbnail_src'],
                            className='case-study-image',
                            alt=item['thumbnail_alt'],
                        ),
                    ),
                    html.Figcaption(item['image_caption'], className='case-study-caption'),
                ],
            )
        )

    children.extend(
        [
            html.Div(
                className='case-detail-grid',
                children=[
                    _text_section('Overview', item['overview']),
                    _text_section('Problem / need', item['problem_statement']),
                    _list_section('Data / system inputs', item['data_inputs']),
                    _list_section('What I built', item['what_i_built']),
                    _list_section('Methods / evaluation', item['methods']),
                    _list_section('Outcome / impact', item['impact']),
                ],
            ),
            html.Div(
                className='case-tools-wrap',
                children=[
                    html.H4('Tools used', className='case-detail-label'),
                    html.Div(
                        className='skill-cloud',
                        children=[html.Span(tool, className='skill-pill') for tool in item['tools']],
                    ),
                ],
            ),
        ]
    )

    return html.Article(
        id=item['slug'],
        className='glass-card case-study-card reveal-up',
        children=children,
    )


layout = html.Div(
    className='content-stack',
    children=[
        html.Section(
            className='reveal-up',
            children=[
                html.Div('SELECTED WORK', className='eyebrow'),
                html.H2('Product Systems, Analytics, and Research Work', className='section-hero-title'),
                html.P(
                    'Selected examples spanning KPI operating systems, analytics engineering, behavioral diagnostics, '
                    'LiDAR research infrastructure, 3D vision experimentation, and evaluation methodology.',
                    className='section-hero-subtitle',
                ),
                html.Nav(
                    className='case-jump-nav',
                    **{'aria-label': 'Jump to work sample'},
                    children=[
                        html.A('Live Demo', href='#tidepool-commerce-analytics', className='case-jump-link'),
                        html.A('Executive KPI Monitoring', href='#executive-kpi-monitoring', className='case-jump-link'),
                        html.A('Behavior & Geography', href='#behavior-geography-correlation', className='case-jump-link'),
                        html.A('Geo-Segmented Intelligence', href='#geo-segmented-user-intelligence', className='case-jump-link'),
                        html.A('LiDAR Benchmarking', href='#lidar-benchmark-engineering', className='case-jump-link'),
                        html.A('3D Vision Evaluation', href='#volumetric-3d-vision-evaluation', className='case-jump-link'),
                        html.A('Segmentation Analysis', href='#segmentation-scene-understanding', className='case-jump-link'),
                    ],
                ),
            ],
        ),
        html.Section(
            className='case-study-stack',
            children=[
                html.Div('LIVE DEMO', className='eyebrow section-subhead'),
                html.P(
                    'A dashboard built end to end for this portfolio, from the data '
                    'generator up. Interactive, and running on generated data.',
                    className='subsection-note',
                ),
                _demo_showcase(),
                html.Div('PRODUCT ANALYTICS / DECISION SYSTEMS', className='eyebrow section-subhead'),
                html.P(
                    'Production-facing work in KPI systems, behavioral analysis, segmentation, and decision support.',
                    className='subsection-note',
                ),
                *[_work_card(case) for case in CASE_STUDIES],
                html.Div('AI / ML / RESEARCH WORK', className='eyebrow section-subhead'),
                html.P(
                    'Research-oriented technical work in LiDAR, point clouds, deep learning experimentation, and benchmark design.',
                    className='subsection-note',
                ),
                *[_work_card(item) for item in RESEARCH_HIGHLIGHTS],
            ],
        ),
    ],
)
