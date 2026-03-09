import dash
from dash import html
import dash_bootstrap_components as dbc

def sidebar():
    nav_links = []
    for page in dash.page_registry.values():
        if page["path"]=="/tree":
            nav_links.append(
                dbc.NavLink(
                    [
                        html.Div("Test results", className="ms-2"),
                    ],
                    href=page["path"],
                    active="exact",
                )
            )
        elif page["path"]=="/app2":
            nav_links.append(
                dbc.NavLink(
                    [
                        html.Div('Tree BBs', className="ms-2"),
                    ],
                    href=page["path"],
                    active="exact",
                )
            ) 
        elif page["path"]=="/app3":
            nav_links.append(
                dbc.NavLink(
                    [
                        html.Div('App3', className="ms-2"),
                    ],
                    href=page["path"],
                    active="exact",
                )
            )           
    return dbc.Nav(children=nav_links,
                   vertical=True,
                   pills=True,
                   className="bg-dark")