import dash
from dash import html


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
                        html.A('leehyungju9297@gmail.com', href='mailto:leehyungju9297@gmail.com', className='contact-value'),
                    ],
                ),
                html.Div(
                    className='glass-card contact-card reveal-up',
                    children=[
                        html.Div('LinkedIn', className='contact-label'),
                        html.A(
                            'linkedin.com/in/hyungju9297',
                            href='https://www.linkedin.com/in/hyungju9297/',
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
