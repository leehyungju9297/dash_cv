import base64
from pathlib import Path

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


def _experience_card(title: str, company: str, location: str, period: str, bullets: list[str]) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.H5(f'{title} | {company}', className='mb-1'),
                        html.Div(location, className='text-muted small'),
                    ],
                    className='mb-2',
                ),
                html.Div(period, className='fw-semibold mb-2'),
                html.Ul([html.Li(item) for item in bullets], className='mb-0'),
            ]
        ),
        className='mb-3 shadow-sm border-0',
    )


profile_image = _load_profile_image()

summary_text = (
    'Data-focused software engineer with production experience in analytics systems, '
    'reporting automation, and cross-source data reconciliation. Strong in Python, SQL, '
    'and statistical problem-solving with end-to-end ownership from KPI definition to '
    'stakeholder-facing delivery.'
)

core_skills = [
    'Python',
    'SQL',
    'R',
    'Pandas',
    'Polars',
    'Flask',
    'Dash',
    'Plotly',
    'SQLAlchemy',
    'Celery',
    'PostgreSQL',
    'MySQL',
]

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Img(
                        src=profile_image,
                        style={
                            'width': '180px',
                            'height': '180px',
                            'objectFit': 'cover',
                            'borderRadius': '50%',
                        },
                        className='shadow-sm',
                    ),
                    width='auto',
                ),
                dbc.Col(
                    [
                        html.H2('Hyungju Lee', className='mb-1'),
                        html.Div('Data Scientist | Backend & Analytics Engineer', className='text-muted mb-2'),
                        html.Div('Toronto, ON, Canada | +1 (416) 706-8011 | leehyungju9297@gmail.com', className='small'),
                        dcc.Link('linkedin.com/in/hyungju9297', href='https://www.linkedin.com/in/hyungju9297/', target='_blank'),
                    ],
                    className='align-self-center',
                ),
            ],
            className='g-4 mb-4',
            align='center',
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H4('Summary', className='mb-2'),
                    html.P(summary_text, className='mb-0'),
                ]
            ),
            className='mb-3 shadow-sm border-0',
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H4('Core Skills', className='mb-2'),
                    html.Div(
                        [
                            dbc.Badge(skill, color='secondary', className='me-2 mb-2 p-2')
                            for skill in core_skills
                        ]
                    ),
                ]
            ),
            className='mb-3 shadow-sm border-0',
        ),
        html.H4('Experience', className='mt-2 mb-3'),
        _experience_card(
            'Software Engineer (Backend & Analytics)',
            'MySeat Media',
            'Toronto, ON, Canada',
            '2023 - Present',
            [
                'Built and maintained Python analytics products (Flask, Dash, Plotly) for DAU/MAU, churn, engagement, geography, and revenue KPIs.',
                'Designed and stabilized scheduled reporting workflows using Flask, Celery, and SQLAlchemy for daily and weekly executive summaries.',
                'Improved subscription and revenue data reliability by reconciling Apple, Google Play, and Stripe/PWA data sources.',
                'Collaborated with product and operations stakeholders to define KPI logic and deliver decision-ready dashboards.',
            ],
        ),
        _experience_card(
            'Researcher',
            'AUSM Lab',
            'Toronto, ON, Canada',
            '2019 - 2024',
            [
                'Published and presented at ICPR on large-scale airborne LiDAR benchmarking with 5,000+ single-tree annotations.',
                'Built 3D-to-2D transformation pipelines for model development and evaluation in the Ontario Train Autonomy Collaboration (OnTRAC, $10M).',
                'Worked with cross-functional collaborators to refine dataset design and model evaluation priorities.',
            ],
        ),
        _experience_card(
            'Financial Analyst',
            'Ontario Ministry of Natural Resources and Forestry',
            'Peterborough, ON, Canada',
            '2017 - 2018',
            [
                'Built Oracle-based financial reporting workflows and supported process automation across ministry teams.',
                'Trained project managers and leadership stakeholders on reporting outputs and process usage.',
            ],
        ),
        html.H4('Education', className='mt-3 mb-2'),
        dbc.Card(
            dbc.CardBody(
                [
                    html.Ul(
                        [
                            html.Li('M.E.Sc., Earth and Space Science & Engineering, York University (2020 - 2022)'),
                            html.Li('H.B.Sc., Statistics (Quantitative Finance Stream), University of Toronto (2015 - 2020)'),
                        ],
                        className='mb-0',
                    )
                ]
            ),
            className='mb-4 shadow-sm border-0',
        ),
    ],
    className='py-4',
)
