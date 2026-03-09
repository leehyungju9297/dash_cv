import dash
from dash import html
import dash_bootstrap_components as dbc


dash.register_page(__name__, path='/projects', order=1, name='Projects')


def _project_card(title: str, scope: str, tech: str, problem: str, action: str, result: str):
    return html.Article(
        className='glass-card project-card reveal-up',
        children=[
            html.Div(scope, className='project-scope'),
            html.H4(title, className='project-title'),
            html.Div(tech, className='project-tech'),
            html.Div('Problem', className='project-label'),
            html.P(problem, className='project-copy'),
            html.Div('Action', className='project-label'),
            html.P(action, className='project-copy'),
            html.Div('Result', className='project-label'),
            html.P(result, className='project-copy mb-0'),
        ],
    )


layout = dbc.Container(
    className='content-stack',
    children=[
        html.Section(
            className='reveal-up',
            children=[
                html.Div('SELECTED WORK', className='eyebrow'),
                html.H2('Projects', className='section-hero-title'),
                html.P(
                    'Case studies from production engineering and research work. '
                    'Each project is framed by problem, action, and measurable context.',
                    className='section-hero-subtitle',
                ),
            ],
        ),
        html.Section(
            className='project-grid',
            children=[
                _project_card(
                    'Subscription & Revenue Reporting Platform',
                    'Production Analytics',
                    'Python, Flask, Celery, SQLAlchemy, Pandas/Polars, Dash/Plotly',
                    'Billing and subscription events were spread across Apple, Google Play, and Stripe/PWA, making KPI reporting and reconciliation inconsistent.',
                    'Implemented scheduled backend workflows and reconciliation logic, and aligned KPI definitions with product/operations stakeholders for recurring executive reporting.',
                    'Enabled reliable daily/weekly reporting workflows in a white-label ecosystem supporting 300+ iOS targets and 120+ Android flavors.',
                ),
                _project_card(
                    'Airborne LiDAR Benchmark Pipeline (YUTO)',
                    'Applied ML Research',
                    'Python, point-cloud preprocessing, dataset engineering, object detection evaluation',
                    'Research teams needed a large-scale benchmark and consistent transformation pipelines for single-tree detection and semantic segmentation work.',
                    'Built 3D-to-2D transformation workflows and dataset preparation/evaluation flows; collaborated across stakeholders to refine benchmark design.',
                    'Produced a benchmark containing 5,000+ single-tree annotations and supported 2 peer-reviewed publications (ICPR 2022, ISPRS 2023).',
                ),
                _project_card(
                    'Financial Workflow Automation',
                    'Public Sector Reporting',
                    'Oracle, financial reporting design, stakeholder enablement',
                    'Financial reporting processes were repetitive and manually intensive across multiple offices.',
                    'Created an Oracle-driven reporting workflow and trained project managers and leadership teams on adoption and operational usage.',
                    'Improved reporting consistency and enabled practical rollout through training sessions in multiple locations (including Sudbury, Guelph, and Peterborough).',
                ),
            ],
        ),
    ],
)
