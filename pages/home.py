import base64
from pathlib import Path
from typing import List

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc


dash.register_page(__name__, path='/', order=0, name='Home')


def _load_profile_image() -> str:
    image_path = Path(__file__).resolve().parents[1] / 'assets' / 'my_pic.jpg'
    if not image_path.exists():
        return ''
    encoded = base64.b64encode(image_path.read_bytes()).decode()
    return f'data:image/jpeg;base64,{encoded}'


def _impact_chip(value: str, label: str):
    return html.Div(
        className='impact-chip',
        children=[
            html.Div(value, className='impact-value'),
            html.Div(label, className='impact-label'),
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
                            html.H5(f'{title}', className='exp-title'),
                            html.Div(company, className='exp-company'),
                        ]
                    ),
                    html.Div([html.Div(period), html.Div(location)], className='exp-meta'),
                ],
            ),
            html.Ul([html.Li(b) for b in bullets], className='exp-bullets'),
        ],
    )


profile_image = _load_profile_image()

layout = dbc.Container(
    className='content-stack',
    children=[
        html.Section(
            className='hero reveal-up',
            children=[
                html.Div(
                    className='hero-copy',
                    children=[
                        html.Div('DATA SCIENTIST / BACKEND ANALYTICS', className='eyebrow'),
                        html.H1('Hyungju Lee', className='hero-title'),
                        html.P(
                            'Production analytics engineer with strong Python/SQL foundations, '
                            'focused on KPI systems, reporting automation, and high-trust data pipelines.',
                            className='hero-subtitle',
                        ),
                        html.Div(
                            className='hero-cta',
                            children=[
                                dcc.Link('Email', href='mailto:leehyungju9297@gmail.com', className='cta-primary'),
                                dcc.Link('LinkedIn', href='https://www.linkedin.com/in/hyungju9297/', className='cta-secondary', target='_blank'),
                            ],
                        ),
                        html.Div(
                            'Toronto, ON, Canada  |  +1 (416) 706-8011  |  leehyungju9297@gmail.com',
                            className='hero-contact',
                        ),
                    ],
                ),
                html.Div(
                    className='hero-photo-wrap',
                    children=html.Img(src=profile_image, className='hero-photo') if profile_image else None,
                ),
            ],
        ),
        html.Section(
            className='impact-row reveal-up',
            children=[
                _impact_chip('300+', 'iOS targets supported'),
                _impact_chip('120+', 'Android flavors supported'),
                _impact_chip('5,000+', 'LiDAR annotations (ICPR)'),
                _impact_chip('$10M', 'OnTRAC collaboration context'),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H3('Core Skills', className='section-title'),
                html.Div(
                    className='skill-cloud',
                    children=[
                        html.Span(skill, className='skill-pill')
                        for skill in [
                            'Python',
                            'SQL',
                            'R',
                            'Flask',
                            'Dash',
                            'Plotly',
                            'SQLAlchemy',
                            'Celery',
                            'Pandas',
                            'Polars',
                            'PostgreSQL',
                            'MySQL',
                            'Redis',
                            'Parquet',
                        ]
                    ],
                ),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H3('Experience', className='section-title'),
                _experience_block(
                    'Software Engineer (Backend & Analytics)',
                    'MySeat Media',
                    '2023 - Present',
                    'Toronto, ON, Canada',
                    [
                        'Built Python analytics/reporting products for DAU/MAU, churn, engagement, geography, and revenue KPIs.',
                        'Designed scheduled reporting workflows using Flask, Celery, and SQLAlchemy for daily/weekly executive summaries.',
                        'Improved revenue data reliability by reconciling Apple, Google Play, and Stripe/PWA sources.',
                        'Partnered with product and operations stakeholders to define KPI logic and deliver decision-ready dashboards.',
                    ],
                ),
                _experience_block(
                    'Researcher',
                    'AUSM Lab',
                    '2019 - 2024',
                    'Toronto, ON, Canada',
                    [
                        'Published and presented at ICPR on large-scale airborne LiDAR benchmarking with 5,000+ single-tree annotations.',
                        'Built 3D-to-2D transformation pipelines for model development and evaluation in OnTRAC ($10M).',
                        'Aligned dataset design and model evaluation with changing cross-functional research requirements.',
                    ],
                ),
                _experience_block(
                    'Financial Analyst',
                    'Ontario Ministry of Natural Resources and Forestry',
                    '2017 - 2018',
                    'Peterborough, ON, Canada',
                    [
                        'Built Oracle-based reporting workflows and supported process automation across ministry teams.',
                        'Trained project managers and leadership stakeholders on reporting outputs and adoption.',
                    ],
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
                        html.Div('Best Master\'s Thesis Award (2022)', className='edu-note'),
                        html.Hr(),
                        html.Div('H.B.Sc., Statistics (Quantitative Finance Stream)', className='edu-title'),
                        html.Div('University of Toronto | 2015 - 2020', className='edu-meta'),
                    ],
                ),
            ],
        ),
    ],
)
