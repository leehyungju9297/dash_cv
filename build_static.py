"""Render the Dash page layouts into the static `docs/` mirror.

`docs/` is the published GitHub Pages build, where a Dash server cannot run.
Its four portfolio pages used to be maintained by hand alongside `pages/*.py`,
which meant every markup change had to be made twice and the two could drift
without anything noticing.

This renders the real Dash layout to HTML instead, so the mirror cannot say
anything the app does not. It rewrites only the contents of `<main
class="page-wrap">`; the document head, the header and the closing scripts stay
hand-maintained in `docs/**/index.html`, because they differ per page (meta
descriptions, Open Graph tags, the active nav item) and change rarely.

Run it after editing any of `pages/home.py`, `projects.py`, `publications.py`
or `contact.py`::

    python3 -m build_static

`pages/dashboard.py` is deliberately not rendered: the static dashboard builds
its own panels client-side from the exported dataset (see
`docs/assets/demo/tidepool.js`), so it has no server-rendered markup to mirror.
"""

from __future__ import annotations

import html as html_lib
import re
from pathlib import Path

import dash


ROOT = Path(__file__).parent
DOCS = ROOT / 'docs'

# Void elements take no closing tag.
VOID = {'img', 'br', 'hr', 'input', 'meta', 'link'}

# Dash component type -> HTML tag. dcc.Link is an anchor in the static build,
# where there is no client-side router to intercept it.
TAGS = {'Link': 'a'}

# Props that are not attributes.
SKIP = {'children', 'loading_state', 'key'}

# Dash prop name -> HTML attribute name. Everything else is lower-cased, and
# anything already containing a hyphen (data-*, aria-*) passes through as is.
ATTRS = {
    'className': 'class',
    'htmlFor': 'for',
    'tabIndex': 'tabindex',
    'n_clicks': None,
    'n_clicks_timestamp': None,
}


def _camel_to_kebab(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '-', name).lower()


def _style(value) -> str:
    if isinstance(value, str):
        return value
    return ';'.join(f'{_camel_to_kebab(k)}:{v}' for k, v in value.items())


def _attrs(props: dict, rewrite) -> str:
    out = []
    for name, value in props.items():
        if name in SKIP or value is None:
            continue
        attr = ATTRS.get(name, name)
        if attr is None:
            continue
        if name == 'style':
            value = _style(value)
        elif name in ('href', 'src'):
            value = rewrite(value)
        if value is True:
            out.append(attr)
            continue
        if value is False:
            continue
        out.append(f'{attr}="{html_lib.escape(str(value), quote=True)}"')
    return (' ' + ' '.join(out)) if out else ''


def _render(node, rewrite, depth=0) -> str:
    if node is None:
        return ''
    if isinstance(node, (list, tuple)):
        return ''.join(_render(n, rewrite, depth) for n in node)
    if isinstance(node, (str, int, float)):
        return html_lib.escape(str(node), quote=False)

    props = {k: v for k, v in node.to_plotly_json().get('props', {}).items()}
    kind = node.to_plotly_json()['type']
    tag = TAGS.get(kind, kind.lower())

    # The static build can lazy-load images; dash.html.Img rejects the
    # attribute, so it is added here rather than in the page.
    if tag == 'img':
        props.setdefault('loading', 'lazy')

    attrs = _attrs(props, rewrite)
    if tag in VOID:
        return f'{"  " * depth}<{tag}{attrs} />\n'

    inner = props.get('children')
    rendered = _render(inner, rewrite, depth + 1)

    # Text-only elements stay on one line; containers get indented children.
    if rendered and '<' not in rendered:
        return f'{"  " * depth}<{tag}{attrs}>{rendered.strip()}</{tag}>\n'
    if not rendered:
        return f'{"  " * depth}<{tag}{attrs}></{tag}>\n'
    return f'{"  " * depth}<{tag}{attrs}>\n{rendered}{"  " * depth}</{tag}>\n'


def _rewriter(prefix: str):
    """Turn the app's absolute routes into the mirror's relative ones."""
    routes = {
        '/': prefix or './',
        '/projects': f'{prefix}projects/',
        '/dashboard': f'{prefix}dashboard/',
        '/publications': f'{prefix}publications/',
        '/contact': f'{prefix}contact/',
    }

    def rewrite(value):
        if not isinstance(value, str):
            return value
        if value.startswith('/assets/'):
            return prefix + value[1:]
        if value in routes:
            return routes[value]
        for route, target in routes.items():
            if route != '/' and value.startswith(route + '#'):
                return target + value[len(route):]
        return value

    return rewrite


PAGES = [
    ('pages.home', 'index.html', './'),
    ('pages.projects', 'projects/index.html', '../'),
    ('pages.publications', 'publications/index.html', '../'),
    ('pages.contact', 'contact/index.html', '../'),
]

MAIN = re.compile(r'(<main class="page-wrap">\n).*?(^\s*</main>)', re.S | re.M)


def main() -> None:
    import app  # noqa: F401  — importing the app is what registers the pages.

    for module, target, prefix in PAGES:
        layout = dash.page_registry[module]['layout']
        body = _render(layout, _rewriter(prefix), depth=4)

        path = DOCS / target
        source = path.read_text()
        replaced, count = MAIN.subn(
            lambda m: m.group(1) + body + m.group(2), source, count=1)
        if count != 1:
            raise SystemExit(f'{target}: could not find the <main class="page-wrap"> block')
        path.write_text(replaced)
        print(f'rendered docs/{target}')


if __name__ == '__main__':
    main()
