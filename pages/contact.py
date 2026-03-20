import dash
from dash import html

from profile_data import (
    EMAIL,
    EMAIL_HREF,
    GITHUB_LABEL,
    GITHUB_URL,
    LINKEDIN_LABEL,
    LINKEDIN_URL,
    LOCATION,
    PHONE_DISPLAY,
)


dash.register_page(__name__, order=3, name='Contact')


layout = html.Div(
    className='content-stack',
    children=[
        html.Section(
            className='reveal-up',
            children=[
                html.Div('LET\'S CONNECT', className='eyebrow'),
                html.H2('Contact', className='section-hero-title'),
                html.P(
                    'I bring both the analytical depth to define what to measure and the engineering skills to build the systems that do it.',
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
                        html.A(EMAIL, href=EMAIL_HREF, className='contact-value'),
                    ],
                ),
                html.Div(
                    className='glass-card contact-card reveal-up',
                    children=[
                        html.Div('LinkedIn', className='contact-label'),
                        html.A(
                            LINKEDIN_LABEL,
                            href=LINKEDIN_URL,
                            target='_blank',
                            rel='noreferrer',
                            className='contact-value',
                        ),
                    ],
                ),
                html.Div(
                    className='glass-card contact-card reveal-up',
                    children=[
                        html.Div('GitHub', className='contact-label'),
                        html.A(
                            GITHUB_LABEL,
                            href=GITHUB_URL,
                            target='_blank',
                            rel='noreferrer',
                            className='contact-value',
                        ),
                    ],
                ),
                html.Div(
                    className='glass-card contact-card reveal-up',
                    children=[
                        html.Div('Phone', className='contact-label'),
                        html.Div(PHONE_DISPLAY, className='contact-value'),
                    ],
                ),
                html.Div(
                    className='glass-card contact-card reveal-up',
                    children=[
                        html.Div('Location', className='contact-label'),
                        html.Div(LOCATION, className='contact-value'),
                    ],
                ),
            ],
        ),
    ],
)
