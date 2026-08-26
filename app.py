import json

import dash
from dash import Dash, Input, Output, dcc, html

from profile_data import EMAIL_HREF, GITHUB_URL, LINKEDIN_URL, PHONE_SCHEMA


app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title='Hyungju Lee | Product Data Scientist, Analytics Engineer',
    update_title=None,
    meta_tags=[
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'},
        {
            'name': 'description',
            'content': 'Hyungju Lee — product data scientist and analytics engineer. KPI architecture, event instrumentation, and the pipelines and reporting behind a 138-client subscription portfolio, plus peer-reviewed LiDAR 3D detection research.',
        },
    ],
)
server = app.server

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
        {%favicon%}
        {%css%}
    </head>
    <body>
        <div id="fallback-shell" class="fallback-shell">
            <div class="fallback-card">
                <h1>Hyungju Lee</h1>
                <p>If the interactive app takes time to load, use these direct links:</p>
                <p class="fallback-links">
                    <a href="/assets/Hyungju_Lee_Resume.pdf">Resume (PDF)</a>
                    <a href="/projects">Selected Work</a>
                    <a href="/publications">Research</a>
                    <a href="mailto:leehyungju9297@gmail.com">Email</a>
                    <a href="https://github.com/leehyungju9297" target="_blank" rel="noreferrer">GitHub</a>
                </p>
            </div>
        </div>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
        <script>
            (function () {
                function hideFallbackWhenDashReady() {
                    var root = document.getElementById("react-entry-point");
                    var fallback = document.getElementById("fallback-shell");
                    if (!root || !fallback) {
                        return false;
                    }
                    if (!root.querySelector("._dash-loading")) {
                        fallback.style.display = "none";
                        return true;
                    }
                    return false;
                }

                if (hideFallbackWhenDashReady()) {
                    return;
                }

                var root = document.getElementById("react-entry-point");
                if (!root) {
                    return;
                }

                var observer = new MutationObserver(function () {
                    if (hideFallbackWhenDashReady()) {
                        observer.disconnect();
                    }
                });
                observer.observe(root, { childList: true, subtree: true });
                setTimeout(function () { observer.disconnect(); }, 20000);
            })();
        </script>
    </body>
</html>
"""

# '/' is deliberately absent: the brand mark in the header is the link home,
# so a Home item would be the same destination twice in one bar.
VISIBLE_PATHS = {'/projects', '/dashboard', '/publications', '/contact'}

PERSON_JSON_LD = {
    '@context': 'https://schema.org',
    '@type': 'Person',
    'name': 'Hyungju Lee',
    'jobTitle': 'Data Scientist / Analytics Engineer / Applied ML Researcher',
    'address': {
        '@type': 'PostalAddress',
        'addressLocality': 'Toronto',
        'addressRegion': 'ON',
        'addressCountry': 'CA',
    },
    'email': EMAIL_HREF,
    'telephone': PHONE_SCHEMA,
    'url': LINKEDIN_URL,
    'sameAs': [LINKEDIN_URL, GITHUB_URL],
}


def _normalize_path(pathname):
    if not pathname:
        return '/'

    normalized = pathname.split('?', 1)[0].split('#', 1)[0]
    if normalized != '/' and normalized.endswith('/'):
        normalized = normalized[:-1]
    return normalized or '/'


def _nav_links(current_path='/'):
    normalized_path = _normalize_path(current_path)
    pages = [page for page in dash.page_registry.values() if page['path'] in VISIBLE_PATHS]
    pages.sort(key=lambda x: x.get('order', 999))
    links = []
    for page in pages:
        class_name = 'top-nav-link active' if normalized_path == page['path'] else 'top-nav-link'
        links.append(dcc.Link(page['name'], href=page['path'], className=class_name))
    return links


app.layout = html.Div(
    id='site-shell',
    className='site-shell',
    children=[
        dcc.Location(id='app-location', refresh=False),
        html.Script(json.dumps(PERSON_JSON_LD), type='application/ld+json'),
        html.Div(id='scroll-progress'),
        html.Div(className='bg-orb orb-1'),
        html.Div(className='bg-orb orb-2'),
        html.Header(
            className='site-header',
            children=[
                html.Div(
                    className='header-inner',
                    children=[
                        # dcc.Link takes no arbitrary attributes, so the
                        # accessible name is carried by hidden text rather than
                        # an aria-label: the visible mark reads "HJ", which on
                        # its own does not tell a screen reader where it goes.
                        dcc.Link(
                            [
                                html.Span('HJ', **{'aria-hidden': 'true'}),
                                html.Span('Home', className='visually-hidden'),
                            ],
                            href='/',
                            className='brand-chip',
                            title='Home',
                        ),
                        html.Nav(id='top-nav', className='top-nav', children=_nav_links('/')),
                    ],
                )
            ],
        ),
        html.Main(className='page-wrap', children=[dash.page_container]),
        html.Button(
            '\u2191',
            id='back-to-top',
            className='back-to-top',
            **{'aria-label': 'Back to top'},
        ),
    ],
)


@app.callback(Output('top-nav', 'children'), Input('app-location', 'pathname'))
def _refresh_nav(pathname):
    return _nav_links(pathname)


if __name__ == '__main__':
    app.run_server(debug=True)
