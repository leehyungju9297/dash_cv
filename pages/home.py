import base64
from pathlib import Path
from typing import List

import dash
from dash import html
import dash_bootstrap_components as dbc


dash.register_page(__name__, path='/', order=0, name='Home')


def _load_profile_image() -> str:
    asset_root = Path(__file__).resolve().parents[1] / 'assets'
    image_path = asset_root / 'my_pic_web.jpg'
    if not image_path.exists():
        image_path = asset_root / 'my_pic.jpg'
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
                        html.Div('HYUNGJU LEE', className='hero-name'),
                        html.Div('PRODUCT DATA SCIENTIST • PRODUCT ANALYTICS', className='eyebrow'),
                        html.H1(
                            'Building KPI systems for engagement, retention, and monetization',
                            className='hero-title',
                        ),
                        html.P(
                            'Product Data Scientist with 6 years of experience building decision-ready analytics '
                            'for product and business teams. I drive KPI design, executive reporting automation, '
                            'engagement and retention analysis, monetization analytics, and cross-platform '
                            'subscription reconciliation across Apple, Google Play, and Stripe/PWA.',
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
                                html.A('Projects', href='/projects', className='cta-secondary'),
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
                _impact_chip('369K+', 'Users represented', 'User-level behavioral, geographic, and monetization analytics'),
                _impact_chip('6.65M+', 'Sessions analyzed', 'Modeled engagement across 5.64B cumulative session-minutes'),
                _impact_chip('$733K+', 'Revenue analyzed', 'Measured subscription and IAP trends with daily peaks above $15K'),
                _impact_chip('138', 'Clients covered', 'Delivered longitudinal analytics across a 6-year reporting window'),
                _impact_chip('34', 'Scheduled jobs', 'Operated recurring analytics infrastructure from sub-minute to weekly'),
                _impact_chip('19.6K', 'Subscription records', 'Consolidated monthly and annual subscription records across platforms'),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H3('Core Skills', className='section-title'),
                html.P(
                    'Production depth in analytics systems, paired with strong product measurement and KPI execution.',
                    className='section-note',
                ),
                html.Div(
                    className='skill-level-grid',
                    children=[
                        html.Div(
                            className='glass-card skill-level-card',
                            children=[
                                html.Div('Strong (Production)', className='skill-level-title'),
                                html.Div(
                                    className='skill-cloud',
                                    children=[
                                        html.Span(skill, className='skill-pill')
                                        for skill in [
                                            'Python',
                                            'SQL',
                                            'Flask',
                                            'Celery',
                                            'SQLAlchemy',
                                            'Pandas',
                                            'Polars',
                                            'PostgreSQL',
                                            'MySQL',
                                        ]
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className='glass-card skill-level-card',
                            children=[
                                html.Div('Product & Analytics', className='skill-level-title'),
                                html.Div(
                                    className='skill-cloud',
                                    children=[
                                        html.Span(skill, className='skill-pill')
                                        for skill in [
                                            'Product Analytics',
                                            'KPI Design',
                                            'Executive Reporting',
                                            'Revenue Analytics',
                                            'Subscription Analytics',
                                            'Data Reconciliation',
                                            'Quasi-Experimental Analysis',
                                            'Dashboarding',
                                            'Monitoring & Data Quality',
                                        ]
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className='glass-card skill-level-card',
                            children=[
                                html.Div('Working Knowledge', className='skill-level-title'),
                                html.Div(
                                    className='skill-cloud',
                                    children=[
                                        html.Span(skill, className='skill-pill')
                                        for skill in [
                                            'R',
                                            'Dash/Plotly',
                                            'Redis',
                                            'Parquet',
                                            'Kotlin',
                                            'Swift',
                                            'CI/CD Tooling',
                                        ]
                                    ],
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
                html.H3('Selected Outcomes', className='section-title'),
                html.Div(
                    className='outcome-grid',
                    children=[
                        html.Div(
                            className='glass-card outcome-card',
                            children=[
                                html.Div('Executive Decision Support', className='outcome-title'),
                                html.P(
                                    'Automated recurring executive reporting across DAU, MAU, churn, engagement, '
                                    'geography, membership, and revenue KPIs.',
                                    className='mb-0',
                                ),
                            ],
                        ),
                        html.Div(
                            className='glass-card outcome-card',
                            children=[
                                html.Div('Revenue & Subscription Analytics', className='outcome-title'),
                                html.P(
                                    'Unified Apple App Store, Google Play, and Stripe/PWA subscription data into a '
                                    'normalized model for cross-platform monetization visibility.',
                                    className='mb-0',
                                ),
                            ],
                        ),
                        html.Div(
                            className='glass-card outcome-card',
                            children=[
                                html.Div('Product Measurement Systems', className='outcome-title'),
                                html.P(
                                    'Translated ambiguous product questions into KPI definitions, reporting logic, '
                                    'and decision-ready dashboards spanning behavior, livestream, and membership.',
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
                    'Product Data Scientist / Software Engineer, Analytics',
                    'MySeat Media',
                    '2023 - Present',
                    'Toronto, ON, Canada',
                    [
                        'Built production analytics and reporting systems across engagement, retention, geography, livestream, and subscription revenue KPIs for white-label mobile and streaming products.',
                        'Analyzed 6.65M+ sessions and 5.64B cumulative session-minutes to model user engagement across a multi-client app ecosystem.',
                        'Measured $733K+ in subscription and in-app purchase revenue, including daily peaks above $15K, and linked monetization trends to 33.8K membership adds and 729K downloads.',
                        'Built a normalized subscription analytics model across Apple IAP, Google Play, and Stripe/PWA to improve cross-platform metric consistency.',
                        'Designed quasi-experimental pre/post impact analyses for product interventions across notifications, livestreams, content, and auctions.',
                        'Automated recurring executive reporting with Python, Flask, Celery, and SQLAlchemy for leadership visibility across DAU/MAU, churn, engagement, and revenue trends.',
                        'Operationalized analytics delivery with curated parquet outputs and 34 scheduled jobs for dependable downstream reporting.',
                    ],
                ),
                _experience_block(
                    'Researcher',
                    'AUSM Lab',
                    '2019 - 2024',
                    'Toronto, ON, Canada',
                    [
                        'Published peer-reviewed work at ICPR 2022 and ISPRS 2023, applying rigorous experimental design and model evaluation to real-world spatial data.',
                        'Built data transformation pipelines and collaborated cross-functionally on dataset design and evaluation priorities in an applied research environment.',
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
