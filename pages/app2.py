import dash
from dash import html, dcc, Dash, Input, Output, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px
from .side_bar import sidebar
import pandas as pd


dash.register_page(__name__)

df_data = pd.read_csv('assets/tree_boxes.csv')

def layout():
    return html.Div(
        [
            html.P("Choose data1:"),
            dcc.Dropdown(
                id="x_axis",
                options=[{"value": x, "label": x} for x in df_data.keys()],
                clearable=False,
                style={"width": "40%"},
            ),
            html.P("Choose data2:"),
            dcc.Dropdown(
                id="y_axis",
                options=[{"value": x, "label": x} for x in df_data.keys()],
                clearable=False,
                style={"width": "40%"},
            ),
            html.P("Choose a graph to display:"),
            dcc.Dropdown(
                id="graph",
                options=[
                    {"value": "pie", "label": "Pie chart"},
                    {"value": "line", "label": "Line chart"},
                    {"value": "bar", "label": "Bar chart"},
                    {"value": "scatter", "label": "Scatter chart"},
                    {"value": "2dhistogram", "label": "2dhistogram chart"},
                ],
                clearable=True,
                style={"width": "40%"},
                multi=True,
        ),
        dcc.Graph(id="my_graph_1", figure={}),
        dcc.Graph(id="my_graph_2", figure={}),
        dcc.Graph(id="my_graph_3", figure={}),
        dcc.Graph(id="my_graph_4", figure={}),
        dcc.Graph(id="my_graph_5", figure={}),
        ]
    )

@callback(
    [
        Output("my_graph_1", "figure"),
        Output("my_graph_2", "figure"),
        Output("my_graph_3", "figure"),
        Output("my_graph_4", "figure"),
        Output("my_graph_5", "figure"),
    ],
    [
        Input("x_axis", "value"),
        Input("y_axis", "value"),
        Input("graph", "value"),
    ],
)

def generate_chart(x_axis, y_axis, graph):
    if not all([x_axis, y_axis]):
        raise PreventUpdate
    if not graph:
        return [{}] * 5
    dff = df_data
    graphs = []

    if "pie" in graph:
        fig = px.pie(dff, values=y_axis, names=x_axis, title="Pie Chart")
        graphs.append(fig)
    if "line" in graph:
        fig = px.line(dff, x=x_axis, y=y_axis, title="Line Chart")
        graphs.append(fig)
    if "bar" in graph:
        fig = px.bar(dff, x=x_axis, y=y_axis, title="Bar Chart")
        graphs.append(fig)
    if "scatter" in graph:
        fig = px.scatter(dff, x=x_axis, y=y_axis, title="Scatter Chart")
        graphs.append(fig)
    if "2dhistogram" in graph:
        fig = px.density_heatmap(
            dff,
            x=x_axis,
            y=y_axis,
            nbinsx=20,
            nbinsy=20,
            color_continuous_scale="Viridis",
            title="2D Histogram Chart",
        )
        graphs.append(fig)

    graphs += (5 - len(graphs)) * [{}] # or can use `[no_update]` here

    g1, g2, g3, g4, g5 = graphs

    return g1, g2, g3, g4, g5


# def layout():
#     return html.Div([
#     dbc.Row(
#         [
#             dbc.Col(
#                 [
#                     sidebar()
#                 ], xs=4, sm=4, md=2, lg=2, xl=2, xxl=2),
                
#             dbc.Col(
#                 [    
#                     html.H3("Analysis of Tree Size / Height", style={'textAlign':'center'}),
#                     html.P("Select Distribution:",style={'textAlign':'center'}),
#                     dcc.RadioItems(
#                         id='distribution1',
#                         options=['box', 'violin', 'rug'],
#                         value='box',
#                         style={'textAlign':'center'},
#                         inline=True
#                     ),
#                     dcc.Graph(id="graph1"),
#                 ], xs=8, sm=8, md=10, lg=10, xl=10, xxl=10)
#         ]
#     ),   

# ])


# @callback(   
#         Output("graph1", "figure"),
#         Input("distribution1", 'value')
# )

# def display_graph(distribution):
#     fig1 = px.histogram(
#         df, x="Height(zrange)", y="BEV Tree Size(orig_area)", color="Tile Type",
#         marginal=distribution,
#         range_x=[-5, 30],
#         hover_data=df.columns)

#     return fig1