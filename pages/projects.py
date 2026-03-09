import dash
from dash import html

from case_studies import CASE_STUDIES


dash.register_page(__name__, path='/projects', order=1, name='Case Studies')


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


def _case_study_card(case):
    return html.Article(
        id=case['slug'],
        className='glass-card case-study-card reveal-up',
        children=[
            html.Div('FEATURED CASE STUDY', className='project-scope'),
            html.H3(case['title'], className='case-study-title'),
            html.P(case['problem_line'], className='case-study-problem'),
            html.Figure(
                className='case-study-figure',
                children=[
                    html.A(
                        href=case['thumbnail_src'],
                        target='_blank',
                        rel='noreferrer',
                        className='case-study-image-link',
                        **{
                            'data-track': 'case_study_image_expand',
                            'data-track-location': 'case_studies_page',
                            'data-track-label': case['slug'],
                        },
                        children=html.Img(
                            src=case['thumbnail_src'],
                            className='case-study-image',
                            alt=case['thumbnail_alt'],
                        ),
                    ),
                    html.Figcaption(case['image_caption'], className='case-study-caption'),
                ],
            ),
            html.Div(
                className='case-detail-grid',
                children=[
                    _text_section('Overview', case['overview']),
                    _text_section('Business problem', case['business_problem']),
                    _list_section('Data / system inputs', case['data_inputs']),
                    _list_section('What I built', case['what_i_built']),
                    _list_section('Analytical methods / logic', case['methods']),
                    _list_section('Outcome / impact', case['impact']),
                ],
            ),
            html.Div(
                className='case-tools-wrap',
                children=[
                    html.H4('Tools used', className='case-detail-label'),
                    html.Div(
                        className='skill-cloud',
                        children=[html.Span(tool, className='skill-pill') for tool in case['tools']],
                    ),
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
                html.Div('PROOF OF WORK', className='eyebrow'),
                html.H2('Case Studies', className='section-hero-title'),
                html.P(
                    'Production dashboards and analytics systems built to solve concrete product questions, '
                    'improve decision quality, and establish operational metric trust.',
                    className='section-hero-subtitle',
                ),
            ],
        ),
        html.Section(
            className='case-study-stack',
            children=[_case_study_card(case) for case in CASE_STUDIES],
        ),
    ],
)
