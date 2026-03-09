from typing import List

import dash
from dash import html

from case_studies import CASE_STUDIES


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


def _skill_group(title: str, skills: List[str]):
    return html.Div(
        className='glass-card skill-level-card',
        children=[
            html.H4(title, className='skill-level-title'),
            html.Div(
                className='skill-cloud',
                children=[html.Span(skill, className='skill-pill') for skill in skills],
            ),
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
            html.A(
                href=f"/projects#{case['slug']}",
                className='featured-case-image-link',
                children=html.Img(
                    src=case['thumbnail_src'],
                    className='featured-case-image',
                    alt=case['thumbnail_alt'],
                ),
            ),
            html.Div(
                className='featured-case-body',
                children=[
                    html.H4(case['title'], className='featured-case-title'),
                    html.P(case['problem_line'], className='featured-case-summary'),
                    html.Ul(
                        className='featured-case-highlights',
                        children=[html.Li(item) for item in case['highlights']],
                    ),
                    html.P(case['homepage_caption'], className='featured-case-caption'),
                    html.A(
                        'View Case Study',
                        href=f"/projects#{case['slug']}",
                        className='cta-secondary featured-case-cta',
                    ),
                ],
            ),
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
                        html.H1('Product Data Scientist', className='hero-role'),
                        html.Div(
                            'Product Analytics • Analytics Engineering • Monetization',
                            className='hero-role-descriptor',
                        ),
                        html.P(
                            'I help product teams make better bets with decision-ready analytics.',
                            className='hero-title',
                        ),
                        html.P(
                            'I define product KPIs, productionize cross-platform metric pipelines, and turn noisy '
                            'usage data into clear operating signals for leadership and product teams.',
                            className='hero-subtitle',
                        ),
                        html.Div(
                            className='hero-cta',
                            children=[
                                html.A('View Case Studies', href='/projects', className='cta-primary'),
                                html.A(
                                    'Download Resume (PDF)',
                                    href='/assets/Hyungju_Lee_Resume.pdf',
                                    download='Hyungju_Lee_Resume.pdf',
                                    className='cta-secondary',
                                ),
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
                            'Toronto, ON, Canada | +1 (416) 706-8011 | leehyungju9297@gmail.com',
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
                _impact_chip('6', 'Years in analytics', 'Leading product analytics and KPI operating systems across app ecosystems'),
                _impact_chip('369K+', 'Users represented', 'Coverage across user-level behavior, geography, and membership segmentation'),
                _impact_chip(
                    '6.65M+',
                    'Sessions analyzed',
                    'Product behavior and engagement diagnostics across multi-client app ecosystems',
                ),
                _impact_chip(
                    '$733K+',
                    'Revenue analyzed',
                    'Subscription and IAP reporting used for monetization monitoring and planning',
                ),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H3('Featured Case Studies', className='section-title'),
                html.P(
                    'Proof-of-work dashboards showing how I define signals, build analytics systems, and drive product decisions.',
                    className='section-note',
                ),
                html.Div(
                    className='featured-case-grid',
                    children=[_case_preview_card(case, primary=index == 0) for index, case in enumerate(CASE_STUDIES)],
                ),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H3('Core Skills', className='section-title'),
                html.P(
                    'Three capability areas I use to move from raw product data to decisions.',
                    className='section-note',
                ),
                html.Div(
                    className='skill-level-grid',
                    children=[
                        _skill_group(
                            'Analytics Engineering',
                            ['Python', 'SQL', 'Flask', 'Celery', 'SQLAlchemy', 'Pandas', 'Polars'],
                        ),
                        _skill_group(
                            'Product Analytics',
                            [
                                'KPI Design',
                                'Product Diagnostics',
                                'Experiment and Quasi-Experiment Analysis',
                                'Retention and Churn Analysis',
                                'Monetization Analytics',
                                'Executive KPI Reporting',
                            ],
                        ),
                        _skill_group(
                            'Data Platforms',
                            ['PostgreSQL', 'MySQL', 'Parquet', 'Redis', 'Dash/Plotly', 'Data Quality Monitoring'],
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
                        'Built and owned KPI systems spanning engagement, retention, geography, livestream behavior, and subscription monetization across a 138-app client ecosystem.',
                        'Defined and productionized cross-platform subscription analytics across Apple, Google Play, and Stripe/PWA to unify monetization reporting logic and reduce reconciliation drift.',
                        'Built recurring KPI operating reviews across DAU, memberships, revenue, notifications, auctions, and timeline activity to support product and leadership decision cadence.',
                        'Turned noisy usage logs into decision-ready diagnostics for feature impact and trend shifts, enabling faster prioritization and more grounded intervention analysis.',
                    ],
                ),
                _experience_block(
                    'Researcher',
                    'AUSM Lab',
                    '2019 - 2024',
                    'Toronto, ON, Canada',
                    [
                        'Built reproducible LiDAR dataset and benchmark pipelines to solve inconsistent evaluation practices, enabling publication-ready experiments.',
                        'Produced 5,000+ single-tree benchmark annotations and co-authored peer-reviewed papers at ICPR 2022 and ISPRS 2023.',
                    ],
                ),
                _experience_block(
                    'Financial Analyst',
                    'Ontario Ministry of Natural Resources and Forestry',
                    '2017 - 2018',
                    'Peterborough, ON, Canada',
                    [
                        'Built Oracle-based reporting workflows to solve repetitive manual finance operations, enabling standardized monthly reporting across offices.',
                        'Defined reporting guidance and trained project teams to improve adoption and interpretation of financial performance outputs.',
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
