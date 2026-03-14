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
                **{
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
                            'I build KPI frameworks, operational dashboards, and cross-platform analytics pipelines '
                            'that turn noisy usage data into decision-ready signals for product and leadership teams.',
                            className='hero-subtitle',
                        ),
                        html.Div(
                            className='hero-cta',
                            children=[
                                html.A(
                                    'View Case Studies',
                                    href='/projects',
                                    className='cta-primary',
                                    **{
                                        'data-track': 'hero_cta_click',
                                        'data-track-location': 'home_hero',
                                        'data-track-label': 'view_case_studies',
                                    },
                                ),
                                html.A(
                                    'Download Resume (PDF)',
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
                                    href='https://www.linkedin.com/in/hyungju9297/',
                                    className='cta-secondary',
                                    target='_blank',
                                    rel='noreferrer',
                                    **{
                                        'data-track': 'hero_cta_click',
                                        'data-track-location': 'home_hero',
                                        'data-track-label': 'linkedin',
                                    },
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
                    'Four capability areas I use to move from raw product data to decision-ready systems.',
                    className='section-note',
                ),
                html.Div(
                    className='skill-level-grid',
                    children=[
                        _skill_group(
                            'Languages & Tools',
                            ['SQL', 'Python', 'R', 'Dash/Plotly', 'Flask', 'Celery'],
                        ),
                        _skill_group(
                            'Product Analytics',
                            [
                                'KPI Frameworks',
                                'Success Metrics',
                                'Cohort Analysis',
                                'Segmentation',
                                'Retention & Churn Analytics',
                                'Monetization Analytics',
                                'Subscription Analytics',
                            ],
                        ),
                        _skill_group(
                            'Measurement',
                            [
                                'Impact Evaluation',
                                'Quasi-Experimental Analysis',
                                'Pre/Post Analysis',
                                'Statistical Analysis',
                                'Exploratory Data Analysis',
                                'Executive Reporting',
                            ],
                        ),
                        _skill_group(
                            'Analytics Systems',
                            [
                                'Analytics Pipelines',
                                'Dashboarding',
                                'Data Quality Monitoring',
                                'Metric Definitions/Contracts',
                                'Data Modeling',
                                'Scheduled Workflows',
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
                        'Built and standardized KPI frameworks spanning engagement, retention, churn, livestream activity, and revenue across a 138-client app ecosystem, enabling shared performance decisions across product, growth, and leadership.',
                        'Productionized SQL/Python analytics pipelines covering 6.65M+ sessions and 5.64B session-minutes to support release-cycle diagnostics and behavioral trend analysis.',
                        'Unified longitudinal analytics across 138 clients over a 6-year window (369K+ represented users), enabling cross-client benchmarking and planning discussions.',
                        'Led monetization reporting across $733K+ in subscription and in-app purchase revenue, linking revenue movement to membership and acquisition signals.',
                        'Quantified intervention impact across notifications, livestreams, content, and auction changes using quasi-experimental and pre/post methods to support rollout and iteration decisions.',
                        'Built executive dashboards and KPI operating reviews across daily active users (DAU), monthly active users (MAU), churn, engagement, and revenue to improve decision cadence and root-cause alignment.',
                    ],
                ),
                _experience_block(
                    'Researcher',
                    'AUSM Lab',
                    '2019 - 2024 (Concurrent Research)',
                    'Toronto, ON, Canada',
                    [
                        'Built reproducible LiDAR dataset and benchmark pipelines to resolve inconsistent evaluation practices, enabling publication-ready experiments and peer-reviewed outputs.',
                        'Produced 5,000+ single-tree benchmark annotations and co-authored peer-reviewed papers at ICPR 2022 and ISPRS 2023.',
                    ],
                ),
                _experience_block(
                    'Financial Analyst',
                    'Ontario Ministry of Natural Resources and Forestry',
                    '2017 - 2018',
                    'Peterborough, ON, Canada',
                    [
                        'Built Oracle-based financial reporting workflows to standardize recurring monthly reporting across offices.',
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
