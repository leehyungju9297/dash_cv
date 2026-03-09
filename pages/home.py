import base64
from pathlib import Path
from typing import List

import dash
from dash import html
import dash_bootstrap_components as dbc


dash.register_page(__name__, path='/', order=0, name='Home')


def _load_profile_image() -> str:
    image_path = Path(__file__).resolve().parents[1] / 'assets' / 'my_pic.jpg'
    if not image_path.exists():
        return ''
    encoded = base64.b64encode(image_path.read_bytes()).decode()
    return f'data:image/jpeg;base64,{encoded}'


def _impact_chip(value: str, label: str, detail: str):
    return html.Div(
        className='impact-chip',
        children=[
            html.Div(value, className='impact-value'),
            html.Div(label, className='impact-label'),
            html.Div(detail, className='impact-detail'),
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
                            html.H5(title, className='exp-title'),
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
                        html.Div('SOFTWARE ENGINEERING • DATA • ANALYTICS', className='eyebrow'),
                        html.H1('Hyungju Lee', className='hero-title'),
                        html.P(
                            'I build production analytics and backend systems that turn messy multi-source data '
                            'into decision-ready signals. My work spans KPI design, reporting automation, and '
                            'data quality operations for engineering and business teams.',
                            className='hero-subtitle',
                        ),
                        html.Div(
                            className='hero-cta',
                            children=[
                                html.A('Email', href='mailto:leehyungju9297@gmail.com', className='cta-primary'),
                                html.A(
                                    'LinkedIn',
                                    href='https://www.linkedin.com/in/hyungju9297/',
                                    className='cta-secondary',
                                    target='_blank',
                                    rel='noreferrer',
                                ),
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
                    children=html.Img(
                        src=profile_image,
                        className='hero-photo',
                        alt='Portrait of Hyungju Lee',
                    )
                    if profile_image
                    else None,
                ),
            ],
        ),
        html.Section(
            className='impact-row reveal-up',
            children=[
                _impact_chip('300+', 'iOS targets', 'Supported in a white-label release ecosystem'),
                _impact_chip('120+', 'Android flavors', 'Managed across client-specific builds and releases'),
                _impact_chip('5,000+', 'LiDAR annotations', 'Used in ICPR benchmark dataset work'),
                _impact_chip('2', 'Peer-reviewed publications', 'ICPR 2022 and ISPRS 2023'),
                _impact_chip('$10M', 'Program context', 'OnTRAC collaboration research contribution'),
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
                html.H3('Selected Outcomes', className='section-title'),
                html.Div(
                    className='outcome-grid',
                    children=[
                        html.Div(
                            className='glass-card outcome-card',
                            children=[
                                html.Div('Reporting Reliability', className='outcome-title'),
                                html.P(
                                    'Implemented scheduled workflows with Flask, Celery, and SQLAlchemy for '
                                    'daily/weekly executive reporting.',
                                    className='mb-0',
                                ),
                            ],
                        ),
                        html.Div(
                            className='glass-card outcome-card',
                            children=[
                                html.Div('Data Trust', className='outcome-title'),
                                html.P(
                                    'Reconciled Apple, Google Play, and Stripe/PWA subscription signals to '
                                    'improve revenue and subscription data consistency.',
                                    className='mb-0',
                                ),
                            ],
                        ),
                        html.Div(
                            className='glass-card outcome-card',
                            children=[
                                html.Div('Research to Production Thinking', className='outcome-title'),
                                html.P(
                                    'Applied large-scale dataset design and model evaluation practices from '
                                    'research environments to production analytics problem framing.',
                                    className='mb-0',
                                ),
                            ],
                        ),
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
                        'Built Python analytics and reporting products covering DAU/MAU, churn, engagement, geography, and revenue KPIs.',
                        'Automated recurring executive reporting with Flask, Celery, and SQLAlchemy scheduling workflows.',
                        'Supported release operations across a white-label environment with 300+ iOS targets and 120+ Android flavors.',
                        'Translated stakeholder requirements into KPI definitions and decision-ready dashboards.',
                    ],
                ),
                _experience_block(
                    'Researcher',
                    'AUSM Lab',
                    '2019 - 2024',
                    'Toronto, ON, Canada',
                    [
                        'Published and presented at ICPR on airborne LiDAR benchmarking with 5,000+ single-tree annotations.',
                        'Built 3D-to-2D transformation pipelines for model development and evaluation in OnTRAC ($10M context).',
                        'Coordinated with cross-functional collaborators to adapt dataset design and evaluation priorities.',
                    ],
                ),
                _experience_block(
                    'Financial Analyst',
                    'Ontario Ministry of Natural Resources and Forestry',
                    '2017 - 2018',
                    'Peterborough, ON, Canada',
                    [
                        'Built Oracle-based reporting workflows and supported process automation across ministry teams.',
                        'Delivered training for project managers and leadership teams on reporting workflows and usage.',
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
