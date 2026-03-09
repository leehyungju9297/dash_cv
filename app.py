import json

import dash
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc


app = Dash(
    __name__,
    use_pages=True,
    title='Hyungju Lee | Product Data Scientist',
    update_title='Loading...',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'},
        {
            'name': 'description',
            'content': 'Hyungju Lee portfolio: Product Data Scientist focused on KPI design, executive reporting, engagement and retention analytics, and subscription monetization systems.',
        },
    ],
)
server = app.server

VISIBLE_PATHS = {'/', '/projects', '/publications', '/contact'}

PERSON_JSON_LD = {
    '@context': 'https://schema.org',
    '@type': 'Person',
    'name': 'Hyungju Lee',
    'jobTitle': 'Product Data Scientist',
    'address': {
        '@type': 'PostalAddress',
        'addressLocality': 'Toronto',
        'addressRegion': 'ON',
        'addressCountry': 'CA',
    },
    'email': 'mailto:leehyungju9297@gmail.com',
    'telephone': '+1-416-706-8011',
    'url': 'https://www.linkedin.com/in/hyungju9297/',
    'sameAs': ['https://www.linkedin.com/in/hyungju9297/'],
}


def _nav_links():
    pages = [page for page in dash.page_registry.values() if page['path'] in VISIBLE_PATHS]
    pages.sort(key=lambda x: x.get('order', 999))
    return [dcc.Link(page['name'], href=page['path'], className='top-nav-link') for page in pages]


app.layout = html.Div(
    className='site-shell',
    children=[
        html.Script(json.dumps(PERSON_JSON_LD), type='application/ld+json'),
        html.Div(className='bg-orb orb-1'),
        html.Div(className='bg-orb orb-2'),
        html.Header(
            className='site-header',
            children=[
                html.Div(
                    className='header-inner',
                    children=[
                        dcc.Link('HJ', href='/', className='brand-chip'),
                        html.Nav(className='top-nav', children=_nav_links()),
                    ],
                )
            ],
        ),
        html.Main(className='page-wrap', children=[dash.page_container]),
    ],
)


if __name__ == '__main__':
    app.run_server(debug=True)
