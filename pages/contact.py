import dash
from dash import dcc, html
import dash_bootstrap_components as dbc


dash.register_page(__name__, order=3, name='Contact')


layout = dbc.Container(
    className='content-stack',
    children=[
        html.Section(
            className='reveal-up',
            children=[
                html.Div('LET\'S CONNECT', className='eyebrow'),
                html.H2('Contact', className='section-hero-title'),
                html.P(
                    'Open to Data Scientist and Backend Analytics opportunities in Toronto (hybrid or remote-friendly).',
                    className='section-hero-subtitle',
                ),
            ],
        ),
        html.Section(
            className='contact-grid',
            children=[
                html.Div(
                    className='glass-card contact-card reveal-up',
                    children=[
                        html.Div('Email', className='contact-label'),
                        dcc.Link('leehyungju9297@gmail.com', href='mailto:leehyungju9297@gmail.com', className='contact-value'),
                    ],
                ),
                html.Div(
                    className='glass-card contact-card reveal-up',
                    children=[
                        html.Div('LinkedIn', className='contact-label'),
                        dcc.Link('linkedin.com/in/hyungju9297', href='https://www.linkedin.com/in/hyungju9297/', target='_blank', className='contact-value'),
                    ],
                ),
                html.Div(
                    className='glass-card contact-card reveal-up',
                    children=[
                        html.Div('Phone', className='contact-label'),
                        html.Div('+1 (416) 706-8011', className='contact-value'),
                    ],
                ),
                html.Div(
                    className='glass-card contact-card reveal-up',
                    children=[
                        html.Div('Location', className='contact-label'),
                        html.Div('Toronto, ON, Canada', className='contact-value'),
                    ],
                ),
            ],
        ),
    ],
)
