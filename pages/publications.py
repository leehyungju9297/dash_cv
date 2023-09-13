import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, order=2)

def layout():
    return html.Div([
    html.Hr(),

    dbc.Row([
        dbc.Col([
            dcc.Markdown('#### ISPRS 2023 \n'
                         'International Society for Photogrammetry and Remote Sensing'),
            dcc.Markdown('Cairo, Egypt')
        ], width=3),
        dbc.Col([
            dcc.Markdown('##### YUTO: A Large Scale Aerial LiDAR Data Set for Semantic Segmentation \n',
                        # '[DOI link](https://doi.org/10.1007/978-3-031-37731-0_28)',
                        # add DOI link later
                         className='ms-3'),
        ], width=6)
    ], justify='center'),
    html.Hr(),

    dbc.Row([
        dbc.Col([
            dcc.Markdown('#### ICPR 2022 \n'
                         'International Conference on Pattern Recognition'),
            dcc.Markdown('Montreal, Canada')
        ], width=3),
        dbc.Col([
            dcc.Markdown('##### YUTO Tree-5000: A Large-scale Airborne LiDAR Data for Single Tree Detection \n'
                         '[DOI link](https://doi.org/10.1007/978-3-031-37731-0_28)',
                         className='ms-3')
        ], width=6)
    ], justify='center'),
    html.Hr(),

    dbc.Row([
        dbc.Col([
            dcc.Markdown('#### Master Thesis \n'
                         'York University'),
            dcc.Markdown('Toronto, Canada')
        ], width=3),
        dbc.Col([
            dcc.Markdown('##### Deep convolutional neural network based single tree detection using volumetric module from airborne liar data \n'
                         '[link](https://yorkspace.library.yorku.ca/items/8c15e8bb-8672-4615-be4a-6b66ca6bdfdf)',
                         className='ms-3')
        ], width=6)
    ], justify='center')
])
