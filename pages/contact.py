"""The Contact page.

The last page in the portfolio, and written as an ending rather than as a
directory. One statement, one availability line, one row of actions with a
single button in it, and a face. The addresses that used to be repeated in a
four-row table underneath are gone: they were the same four destinations the
action row already carries, set as records so a reader had to read them twice
to learn nothing new.
"""

import dash
from dash import html

from profile_data import EMAIL_HREF, GITHUB_URL, LINKEDIN_URL


dash.register_page(__name__, order=4, name='Contact')


RESUME_HREF = '/assets/Hyungju_Lee_Resume.pdf'

# The closing strip. Two short columns, both facts, neither of them a section
# about itself. "Outside of data" is four words and stays four words — the
# point is one human detail at the end of a professional document, not a
# hobbies page.
BASED_IN = ['Toronto, Canada', 'Open to hybrid & remote']

OUTSIDE = 'Brazilian jiu-jitsu · Running · Espresso · Cars'


def _track(label: str, location: str = 'contact_intro') -> dict:
    return {
        'data-track': 'contact_cta_click',
        'data-track-location': location,
        'data-track-label': label,
    }


def _action(text: str, href: str, label: str, **kwargs):
    """A secondary action: a text link with an outbound mark, not a button.

    Three of the four ways to reach me are destinations rather than messages.
    Setting them as links is what keeps the one that is a message legible as
    the only button on the page.
    """
    return html.A(text, href=href, className='contact-action',
                  **_track(label), **kwargs)


def _closing_column(label: str, lines):
    return html.Div(
        className='contact-closing-column',
        children=[
            html.Div(label, className='contact-label'),
            html.Div([html.Div(line, className='contact-closing-line')
                      for line in lines],
                     className='contact-closing-body'),
        ],
    )


layout = html.Div(
    className='content-stack content-stack--narrow',
    children=[
        html.Section(
            className='contact-intro reveal-up',
            children=[
                html.Div(
                    className='contact-intro-copy',
                    children=[
                        html.Div('Contact', className='eyebrow'),
                        html.H1('Let’s work on hard data problems.',
                                className='section-hero-title'),
                        html.P(
                            'I’m a Toronto-based product data scientist and '
                            'analytics engineer focused on turning messy '
                            'product data into measurement systems, decisions, '
                            'and reliable data products.',
                            className='section-hero-subtitle',
                        ),
                        html.P(
                            'Currently open to Product Data Scientist and '
                            'Analytics Engineer opportunities in Toronto, '
                            'hybrid, or remote settings.',
                            className='contact-availability',
                        ),
                        # One button, three links. Email is the action; the
                        # rest are places to go, including the resume, which
                        # now lives here rather than in a second sentence at
                        # the foot of the page.
                        html.Div(
                            className='contact-actions',
                            children=[
                                html.A('Email Hyungju', href=EMAIL_HREF,
                                       className='cta-primary',
                                       **_track('email')),
                                _action('LinkedIn', LINKEDIN_URL, 'linkedin',
                                        target='_blank', rel='noreferrer'),
                                _action('GitHub', GITHUB_URL, 'github',
                                        target='_blank', rel='noreferrer'),
                                _action('Resume', RESUME_HREF,
                                        'download_resume',
                                        download='Hyungju_Lee_Resume.pdf'),
                            ],
                        ),
                    ],
                ),
                html.Img(
                    src='/assets/my_pic_web.jpg',
                    className='contact-portrait',
                    alt='Portrait of Hyungju Lee',
                    width=168,
                    height=168,
                ),
            ],
        ),
        html.Section(
            className='contact-closing',
            **{'aria-label': 'Location and interests'},
            children=[
                _closing_column('Based in', BASED_IN),
                _closing_column('Outside of data', [OUTSIDE]),
            ],
        ),
    ],
)
