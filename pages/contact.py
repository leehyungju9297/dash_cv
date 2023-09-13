import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, order=3)

text_color = {'color':'grey'}

def layout():
    return dbc.Row([
        dbc.Col([
    dcc.Markdown('# Hyungju Lee', className='mt-3'),
    dcc.Markdown('### AI Engineer / Researcher', className='mb-5'),
    dcc.Markdown('## Personal info'),
    dcc.Markdown('### Address'),
    dcc.Markdown('763 Bay St, Toronto, Canada'),
    dcc.Markdown('### Phone Number'),
    dcc.Markdown('416-706-8011'),
    dcc.Markdown('### Email'),
    dcc.Markdown('leehyungju9297@gmail.com'),
    dcc.Markdown('### Linkedin'),
    dcc.Markdown('[www.linkedin.com/in/hyungju9297/](https://www.linkedin.com/in/hyungju9297/)',
                 link_target='_blank'),
    
        ], width={'size':6, 'offset':2})
], justify='center')