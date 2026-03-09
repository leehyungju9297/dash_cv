import dash
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc


app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

VISIBLE_PATHS = {"/", "/publications", "/contact"}


def _nav_links():
    pages = [
        page for page in dash.page_registry.values() if page["path"] in VISIBLE_PATHS
    ]
    pages.sort(key=lambda x: x.get("order", 999))
    return [
        dcc.Link(page["name"], href=page["path"], className="top-nav-link")
        for page in pages
    ]


app.layout = html.Div(
    className="site-shell",
    children=[
        html.Div(className="bg-orb orb-1"),
        html.Div(className="bg-orb orb-2"),
        html.Header(
            className="site-header",
            children=[
                html.Div(
                    className="header-inner",
                    children=[
                        dcc.Link("HJ", href="/", className="brand-chip"),
                        html.Div(className="top-nav", children=_nav_links()),
                    ],
                )
            ],
        ),
        html.Main(className="page-wrap", children=[dash.page_container]),
    ],
)


if __name__ == "__main__":
    app.run_server(debug=True)
