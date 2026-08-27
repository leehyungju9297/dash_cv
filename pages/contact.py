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


dash.register_page(__name__, order=4, name='Contact')


layout = html.Div(
    className='content-stack content-stack--narrow',
    children=[
        # The portrait belongs on the page where someone is deciding whether to
        # get in touch, not above the proposition on the home page. It sits
        # beside the introduction on desktop and under it on a phone, and stays
        # secondary to the links either way.
        html.Section(
            className='contact-intro reveal-up',
            children=[
                html.Div(
                    className='contact-intro-copy',
                    children=[
                        html.Div('CONTACT', className='eyebrow'),
                        html.H1('Contact', className='section-hero-title'),
                        html.P(
                            'I work across product analytics, analytics engineering, data systems, and AI/ML-oriented '
                            'research engineering. Email is the fastest path for role discussions and technical opportunities.',
                            className='section-hero-subtitle',
                        ),
                    ],
                ),
                html.Img(
                    src='/assets/my_pic_web.jpg',
                    className='contact-portrait',
                    alt='Portrait of Hyungju Lee',
                    width=136,
                    height=136,
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
