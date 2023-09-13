import dash
from dash import html, dcc, Dash, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
from .side_bar import sidebar
import pandas as pd


dash.register_page(__name__)

df = pd.read_csv('assets/tree_boxes.csv')
# df = px.data.tips() # replace with your own data source


def layout():
    return html.Div([
    dbc.Row(
        [
            dbc.Col(
                [
                    sidebar()
                ], xs=4, sm=4, md=2, lg=2, xl=2, xxl=2),
                
            dbc.Col(
                [    
                    html.H3("Analysis of Tree Size / Height", style={'textAlign':'center'}),
                    html.P("Select Distribution:",style={'textAlign':'center'}),
                    dcc.RadioItems(
                        id='distribution',
                        options=['box', 'violin', 'rug'],
                        value='box',
                        style={'textAlign':'center'},
                        inline=True
                    ),
                    dcc.Graph(id="graph"),
                ], xs=8, sm=8, md=10, lg=10, xl=10, xxl=10)
        ]
    )
])


@callback(
    Output("graph", "figure"), 
    Input("distribution", "value"))

def display_graph(distribution):
    fig = px.histogram(
        df, x="Height(zrange)", y="BEV Tree Size(orig_area)", color="Tile Type",
        marginal=distribution,
        range_x=[-5, 30],
        hover_data=df.columns)
    return fig