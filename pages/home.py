from typing import List

import dash
from dash import html


dash.register_page(__name__, path='/', order=0, name='Home')


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
                        html.Div('PRODUCT DATA SCIENTIST / PRODUCT ANALYST', className='eyebrow'),
                        html.H1(
                            'I help product teams make better bets with decision-ready analytics.',
                            className='hero-title',
                        ),
                        html.P(
                            'Product Data Scientist with 6 years of experience turning ambiguous product questions '
                            'into KPI frameworks, trustworthy reporting, and clear recommendations across '
                            'engagement, retention, and subscription monetization.',
                            className='hero-subtitle',
                        ),
                        html.Ul(
                            className='hero-points',
                            children=[
                                html.Li('Built KPI systems used by product and leadership teams across 138 client apps.'),
                                html.Li('Analyzed 6.65M+ sessions and 5.64B+ session-minutes to diagnose user behavior.'),
                                html.Li('Normalized Apple, Google Play, and Stripe subscription data into one metric layer.'),
                                html.Li('Automated recurring executive reporting for DAU, churn, engagement, and revenue.'),
                            ],
                        ),
                        html.Div(
                            className='hero-cta',
                            children=[
                                html.A(
                                    'Download Resume (PDF)',
                                    href='/assets/Hyungju_Lee_Resume.pdf',
                                    download='Hyungju_Lee_Resume.pdf',
                                    className='cta-primary',
                                ),
                                html.A('View Projects', href='/projects', className='cta-secondary'),
                                html.A('Email', href='mailto:leehyungju9297@gmail.com', className='cta-secondary'),
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
                        src='/assets/my_pic_web.jpg',
                        className='hero-photo',
                        alt='Portrait of Hyungju Lee',
                    ),
                ),
            ],
        ),
        html.Section(
            className='impact-row reveal-up',
            children=[
                _impact_chip('6', 'Years in analytics', 'Product analytics and measurement ownership across app ecosystems'),
                _impact_chip('369K+', 'Users represented', 'Behavioral, geographic, and monetization analysis at user level'),
                _impact_chip('6.65M+', 'Sessions analyzed', 'Modeled usage patterns over 5.64B cumulative session-minutes'),
                _impact_chip('$733K+', 'Revenue analyzed', 'Subscription and IAP trend tracking with daily peaks above $15K'),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H3('Core Skills', className='section-title'),
                html.P(
                    'A practical blend of product sense, statistical rigor, and production analytics engineering.',
                    className='section-note',
                ),
                html.Div(
                    className='skill-level-grid',
                    children=[
                        html.Div(
                            className='glass-card skill-level-card',
                            children=[
                                html.Div('Analytics Engineering', className='skill-level-title'),
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
                                        ]
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className='glass-card skill-level-card',
                            children=[
                                html.Div('Product Measurement', className='skill-level-title'),
                                html.Div(
                                    className='skill-cloud',
                                    children=[
                                        html.Span(skill, className='skill-pill')
                                        for skill in [
                                            'Product Analytics',
                                            'KPI Design',
                                            'Experiment/Quasi-Experiment Analysis',
                                            'Executive Reporting',
                                            'Retention & Churn Analysis',
                                            'Monetization Analytics',
                                        ]
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            className='glass-card skill-level-card',
                            children=[
                                html.Div('Data Platforms', className='skill-level-title'),
                                html.Div(
                                    className='skill-cloud',
                                    children=[
                                        html.Span(skill, className='skill-pill')
                                        for skill in [
                                            'PostgreSQL',
                                            'MySQL',
                                            'Parquet',
                                            'Redis',
                                            'Dash/Plotly',
                                            'Monitoring & Data Quality',
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
                                html.Div('Executive KPI Operating Rhythm', className='outcome-title'),
                                html.P(
                                    'Established recurring KPI reviews spanning DAU/MAU, churn, engagement, '
                                    'membership, and revenue to support weekly product and leadership decisions.',
                                    className='mb-0',
                                ),
                            ],
                        ),
                        html.Div(
                            className='glass-card outcome-card',
                            children=[
                                html.Div('Cross-Platform Subscription Visibility', className='outcome-title'),
                                html.P(
                                    'Unified Apple App Store, Google Play, and Stripe/PWA data into one '
                                    'normalized subscription model for consistent monetization analytics.',
                                    className='mb-0',
                                ),
                            ],
                        ),
                        html.Div(
                            className='glass-card outcome-card',
                            children=[
                                html.Div('Decision-Ready Product Diagnostics', className='outcome-title'),
                                html.P(
                                    'Converted noisy usage and revenue logs into actionable narratives that helped '
                                    'teams prioritize experiments and validate product interventions.',
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
                        'Owned KPI definition and delivery across engagement, retention, geography, livestream, and subscription revenue metrics.',
                        'Automated weekly and monthly executive reporting pipelines used by product and business stakeholders.',
                        'Built cross-platform subscription reconciliation logic for Apple, Google Play, and Stripe/PWA sources.',
                        'Led pre/post impact analyses to evaluate notification, livestream, content, and auction feature changes.',
                    ],
                ),
                _experience_block(
                    'Researcher',
                    'AUSM Lab',
                    '2019 - 2024',
                    'Toronto, ON, Canada',
                    [
                        'Published peer-reviewed research at ICPR 2022 and ISPRS 2023 with reproducible evaluation workflows.',
                        'Built dataset transformation pipelines and benchmark logic for large-scale LiDAR annotation and detection work.',
                    ],
                ),
                _experience_block(
                    'Financial Analyst',
                    'Ontario Ministry of Natural Resources and Forestry',
                    '2017 - 2018',
                    'Peterborough, ON, Canada',
                    [
                        'Developed Oracle-based reporting workflows to reduce manual finance operations.',
                        'Trained project managers and leadership teams on standardized reporting usage and interpretation.',
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
