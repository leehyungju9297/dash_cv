import dash
from dash import html

from case_studies import CASE_STUDIES, LIVE_DEMO, RESEARCH_HIGHLIGHTS


dash.register_page(__name__, path='/projects', order=1, name='Selected Work')


# The page is an index over seven work items, then the seven case studies
# themselves. Index order and case-study order are the same list, so the two can
# never fall out of step.
WORK = [LIVE_DEMO] + CASE_STUDIES + RESEARCH_HIGHLIGHTS


def _is_research(item) -> bool:
    return item['scope'].startswith('AI / ML')


def _outcome(item) -> str:
    """The one sentence the index promises.

    The first impact line for a case study; the live demo has no impact list,
    so it uses the summary it is introduced with everywhere else.
    """
    impact = item.get('impact')
    return impact[0] if impact else item['problem_line']


def _index_card(item):
    """A compact index entry: what it was, what came of it, and a way in.

    The whole card is the link. The long description that used to sit here
    belongs in the case study below, not in a card a reader is scanning.
    """
    card_class = 'glass-card card-hover project-index-card'
    if _is_research(item):
        card_class += ' project-index-card--research'

    return html.A(
        href=f"#{item['slug']}",
        className=card_class,
        **{
            'data-track': 'project_index_click',
            'data-track-location': 'case_studies_page',
            'data-track-label': item['slug'],
        },
        children=[
            html.Div(item['scope'], className='project-scope'),
            html.H3(item['title'], className='project-index-title'),
            html.P(_outcome(item), className='project-index-outcome'),
            html.Div(item['role'], className='project-index-meta'),
            html.Div(
                className='skill-cloud',
                children=[html.Span(tag, className='skill-pill')
                          for tag in item['tags'][:4]],
            ),
            html.Span('Read the case study', className='project-index-link'),
        ],
    )


def _block(label: str, body):
    return html.Div(
        className='case-detail-block',
        children=[html.H3(label, className='case-detail-label'), body],
    )


def _prose(label: str, text: str):
    return _block(label, html.P(text, className='case-detail-copy'))


def _list(label: str, items):
    return _block(
        label,
        html.Ul(className='case-detail-list', children=[html.Li(i) for i in items]),
    )


def _meta(label: str, body):
    return html.Div(
        className='case-meta',
        children=[html.H3(label, className='case-meta-label'), body],
    )


def _case_head(item):
    return html.Header(
        className='case-study-head',
        children=[
            html.Div(item['scope'], className='project-scope'),
            html.H2(item['title'], className='case-study-title'),
            html.P(_outcome(item), className='case-study-problem'),
        ],
    )


def _demo_showcase():
    """The live demo, as its own work item.

    It is not an interactive version of the case studies below: it is a separate
    build in a different domain, and the honest way to show it is on its own
    terms with its own screenshots. It takes the same head and body template as
    every other item, minus the metadata rail — its evidence is the screenshots,
    which want the full plate.
    """
    return html.Article(
        id=LIVE_DEMO['slug'],
        className='glass-card case-study-card demo-showcase reveal-up',
        children=[
            _case_head(LIVE_DEMO),
            html.Div(
                className='case-study-body',
                children=html.Div(
                    className='case-study-main',
                    children=[
                        _prose('Overview', LIVE_DEMO['problem_line']),
                        _meta('Role and context',
                              html.P(LIVE_DEMO['role'], className='case-meta-copy')),
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
                        _list('What it does', LIVE_DEMO['highlights']),
                        html.Div(
                            className='skill-cloud',
                            children=[html.Span(tag, className='skill-pill')
                                      for tag in LIVE_DEMO['tags']],
                        ),
                        html.A(
                            'Open the live demo →',
                            href=LIVE_DEMO['href'],
                            className='cta-secondary',
                            **{
                                'data-track': 'case_study_demo_click',
                                'data-track-location': 'case_studies_page',
                            },
                        ),
                    ],
                ),
            ),
        ],
    )


def _case_study(item):
    """One case study, on the template every case study uses.

    Reading column: overview, problem, approach, what was built, results.
    Metadata rail: role and context, the inputs the work ran on, the tools.
    The split is what keeps the prose in a reading measure while the reference
    material stays beside it rather than interrupting it.
    """
    main = []

    if item.get('thumbnail_src'):
        main.append(
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

    main.extend([
        _prose('Overview', item['overview']),
        _prose('Problem', item['problem_statement']),
        _list('Approach', item['methods']),
        _list('What I built', item['what_i_built']),
        _list('Results', item['impact']),
    ])

    side = [
        _meta('Role and context', html.P(item['role'], className='case-meta-copy')),
        _meta('Data / system inputs',
              html.Ul(className='case-detail-list',
                      children=[html.Li(i) for i in item['data_inputs']])),
        _meta('Tools and methods',
              html.Div(className='skill-cloud',
                       children=[html.Span(t, className='skill-pill')
                                 for t in item['tools']])),
    ]

    # Research work is the same object in the same design language; the modifier
    # only moves the semantic accent from the primary accent to teal.
    card_class = 'glass-card case-study-card reveal-up'
    if _is_research(item):
        card_class += ' case-study-card--research'

    return html.Article(
        id=item['slug'],
        className=card_class,
        children=[
            _case_head(item),
            html.Div(
                className='case-study-body',
                children=[
                    html.Div(main, className='case-study-main'),
                    html.Aside(side, className='case-study-side'),
                ],
            ),
        ],
    )


layout = html.Div(
    className='content-stack',
    children=[
        html.Section(
            className='reveal-up',
            children=[
                html.Div('SELECTED WORK', className='eyebrow'),
                html.H1('Product Systems, Analytics, and Research Work',
                        className='section-hero-title'),
                html.P(
                    'Selected examples spanning KPI operating systems, analytics engineering, behavioral diagnostics, '
                    'LiDAR research infrastructure, 3D vision experimentation, and evaluation methodology.',
                    className='section-hero-subtitle',
                ),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H2('Index', className='section-title'),
                html.P(
                    'Seven work items, each with its case study below.',
                    className='section-note',
                ),
                html.Nav(
                    className='project-index-grid',
                    **{'aria-label': 'Work index'},
                    children=[_index_card(item) for item in WORK],
                ),
            ],
        ),
        html.Section(
            children=[
                html.H2('Case Studies', className='section-title'),
                html.P(
                    [
                        'Each one on the same template: overview and outcome, problem, '
                        'approach, what I built, and results, with role, inputs and tools '
                        'beside it. The live demo is ',
                        html.A('runnable', href='/dashboard', className='inline-link',
                               **{'data-track': 'live_demo_click',
                                  'data-track-location': 'case_studies_page'}),
                        '.',
                    ],
                    className='section-note',
                ),
                html.Div(
                    className='case-study-stack',
                    children=[_demo_showcase()] + [
                        _case_study(item) for item in CASE_STUDIES + RESEARCH_HIGHLIGHTS
                    ],
                ),
            ],
        ),
    ],
)
