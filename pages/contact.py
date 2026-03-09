import dash
from dash import dcc
import dash_bootstrap_components as dbc


dash.register_page(__name__, order=3, name='Contact')


def layout():
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    [
                        dcc.Markdown('# Hyungju Lee'),
                        dcc.Markdown('### Data Scientist | Backend & Analytics Engineer', className='mb-4'),
                        dcc.Markdown('**Location**\nToronto, ON, Canada'),
                        dcc.Markdown('**Phone**\n+1 (416) 706-8011'),
                        dcc.Markdown('**Email**\n[leehyungju9297@gmail.com](mailto:leehyungju9297@gmail.com)'),
                        dcc.Markdown('**LinkedIn**\n[linkedin.com/in/hyungju9297](https://www.linkedin.com/in/hyungju9297/)'),
                        dcc.Markdown('**Target Roles**\nData Scientist, Fraud/Risk Analytics, Backend Analytics Engineer'),
                    ],
                    width=8,
                    lg=6,
                ),
                justify='center',
            )
        ],
        className='py-4',
    )
