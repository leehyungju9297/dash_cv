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


def _row(label: str, value, muted: bool = False):
    """One record in the contact list.

    Not a grid of equal cards: the four are not equally useful, and a reader
    looking for the way in should not have to weigh email against phone.
    """
    class_name = 'contact-row contact-row--muted' if muted else 'contact-row'
    return html.Div(
        className=class_name,
        children=[
            html.Div(label, className='contact-label'),
            html.Div(value, className='contact-value'),
        ],
    )


layout = html.Div(
    className='content-stack content-stack--narrow',
    children=[
        # The opening: what I do, what I am open to, and one obvious action.
        # The portrait sits beside it — this is the page where a face is
        # useful — and stays secondary to the button.
        html.Section(
            className='contact-intro reveal-up',
            children=[
                html.Div(
                    className='contact-intro-copy',
                    children=[
                        html.Div('CONTACT', className='eyebrow'),
                        html.H1('Contact', className='section-hero-title'),
                        html.P(
                            'I work across product analytics, analytics engineering, data systems, '
                            'and AI/ML-oriented research engineering.',
                            className='section-hero-subtitle',
                        ),
                        html.P(
                            'Open to Product Data Scientist and Analytics Engineer opportunities '
                            'in Toronto, hybrid, or remote settings.',
                            className='contact-availability',
                        ),
                        html.Div(
                            className='contact-actions',
                            children=[
                                html.A(
                                    'Email Hyungju',
                                    href=EMAIL_HREF,
                                    className='cta-primary',
                                    **{
                                        'data-track': 'contact_cta_click',
                                        'data-track-location': 'contact_intro',
                                        'data-track-label': 'email',
                                    },
                                ),
                                html.A(
                                    'LinkedIn',
                                    href=LINKEDIN_URL,
                                    className='hero-link',
                                    target='_blank',
                                    rel='noreferrer',
                                    **{
                                        'data-track': 'contact_cta_click',
                                        'data-track-location': 'contact_intro',
                                        'data-track-label': 'linkedin',
                                    },
                                ),
                                html.A(
                                    'GitHub',
                                    href=GITHUB_URL,
                                    className='hero-link',
                                    target='_blank',
                                    rel='noreferrer',
                                    **{
                                        'data-track': 'contact_cta_click',
                                        'data-track-location': 'contact_intro',
                                        'data-track-label': 'github',
                                    },
                                ),
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
            className='contact-details reveal-up',
            children=[
                _row('Primary contact',
                     html.A(EMAIL, href=EMAIL_HREF, className='contact-link')),
                _row('Professional links', [
                    html.A(LINKEDIN_LABEL, href=LINKEDIN_URL, target='_blank',
                           rel='noreferrer', className='contact-link'),
                    html.Span('·', className='contact-sep'),
                    html.A(GITHUB_LABEL, href=GITHUB_URL, target='_blank',
                           rel='noreferrer', className='contact-link'),
                ]),
                _row('Location', LOCATION),
                _row('Phone', PHONE_DISPLAY, muted=True),
            ],
        ),
        # A deliberate endpoint rather than a page that simply stops.
        html.Section(
            className='contact-close',
            children=html.P(
                [
                    'Prefer the short version? ',
                    html.A('Download the resume (PDF)',
                           href='/assets/Hyungju_Lee_Resume.pdf',
                           download='Hyungju_Lee_Resume.pdf',
                           className='contact-link',
                           **{
                               'data-track': 'contact_cta_click',
                               'data-track-location': 'contact_close',
                               'data-track-label': 'download_resume',
                           }),
                    '.',
                ],
                className='contact-close-note',
            ),
        ),
    ],
)
