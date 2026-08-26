import dash
from dash import html

from work_ui import WORK, work_card


dash.register_page(__name__, path='/projects', order=1, name='Selected Work')


layout = html.Div(
    className='content-stack',
    children=[
        html.Section(
            className='reveal-up',
            children=[
                html.Div('SELECTED WORK', className='eyebrow'),
                html.H1('Product Systems, Analytics, and Research Work',
                        className='section-hero-title'),
                html.P(
                    'Seven projects across KPI operating systems, analytics engineering, '
                    'behavioral diagnostics, LiDAR research infrastructure, and evaluation '
                    'methodology. Each one opens onto its own case study.',
                    className='section-hero-subtitle',
                ),
            ],
        ),
        html.Section(
            children=[
                # An index, not a table of contents: every card carries the
                # result, the role and the timeframe, so the seven can be
                # compared without opening any of them.
                html.Div(
                    className='work-grid',
                    children=[work_card(item, track_location='project_index',
                                        tag_limit=4, link_label='View case study',
                                        heading=html.H2)
                              for item in WORK],
                ),
            ],
        ),
    ],
)
