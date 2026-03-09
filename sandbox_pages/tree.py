import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from .side_bar import sidebar

dash.register_page(__name__, title='results', order=1)

df = pd.read_csv('assets/test_result.csv')
df = df.loc[df['POV'] == 'BEV']


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
                    html.H3('AP Scores of Tested Networks in BEV POV', style={'textAlign':'center'}),
                    dcc.Dropdown(id='network_chosen',
                                 options=df['Network'].unique(),
                                 value=["SECOND", "PointPillars", "PointRCNN"],
                                 multi=True,
                                 style={'color':'black'}
                                 ),
                    html.Hr(),
                    dcc.Graph(id='line_chart', figure={}),

                ], xs=8, sm=8, md=10, lg=10, xl=10, xxl=10)
        ]
    )
])

@callback(
    Output("line_chart", "figure"),
    Input("network_chosen", "value")
)
def update_graph_card(networks):
    if len(networks) == 0:
        return dash.no_update
    else:
        df_filtered = df[df["Network"].isin(networks)]
        df_filtered = df_filtered.groupby(["IoU", "Network"])[['AP Score']].median().reset_index()
        fig = px.line(df_filtered, x="IoU", y="AP Score", color="Network",
                      labels={"AP Scores": "AP Scores"}).update_traces(mode='lines+markers')
        return fig
