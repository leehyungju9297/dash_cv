"""One route per project.

Dash discovers pages by module, but a module may register more than one — so
this registers `/projects/<slug>` for every item in ``WORK`` from a single
loop, and every one of them renders through the same template. A new project
needs an entry in ``case_studies.py`` and nothing else.
"""

import dash
from dash import html

from work_ui import WORK, detail_href, is_research, neighbours, outcome, tags


def _block(label: str, body):
    return html.Section(
        className='case-detail-block',
        children=[html.H2(label, className='case-detail-label'), body],
    )


def _prose(label: str, text: str):
    return _block(label, html.P(text, className='case-detail-copy'))


def _list(label: str, items):
    return _block(
        label,
        html.Ul(className='case-detail-list', children=[html.Li(i) for i in items]),
    )


def _results(items):
    """Results, pulled out of the prose and set as scannable statements.

    These are the lines a reader is looking for, so they do not sit in a
    bulleted list styled like every other bulleted list on the page.
    """
    return html.Section(
        className='case-detail-block',
        children=[
            html.H2('Results', className='case-detail-label'),
            html.Ul(
                className='result-list',
                children=[html.Li(item, className='result-item') for item in items],
            ),
        ],
    )


def _meta_row(label: str, value):
    return html.Div(
        className='case-meta',
        children=[
            html.Div(label, className='case-meta-label'),
            html.Div(value, className='case-meta-value'),
        ],
    )


def _sidebar(item):
    return html.Aside(
        className='case-study-side',
        **{'aria-label': 'Project metadata'},
        children=[
            _meta_row('Role', item['role']),
            _meta_row('Timeframe', item['period']),
            _meta_row('Domain', item['domain']),
            _meta_row('Data / system inputs',
                      html.Ul(className='case-meta-list',
                              children=[html.Li(i) for i in item['data_inputs']])),
            _meta_row('Tools and methods',
                      html.Div(className='skill-cloud',
                               children=[html.Span(t, className='skill-pill')
                                         for t in item['tools']])),
        ],
    )


def _demo_sidebar(item):
    return html.Aside(
        className='case-study-side',
        **{'aria-label': 'Project metadata'},
        children=[
            _meta_row('Role', item['role']),
            _meta_row('Timeframe', item['period']),
            _meta_row('Domain', item['domain']),
            _meta_row('Tools and methods',
                      html.Div(className='skill-cloud',
                               children=[html.Span(t, className='skill-pill')
                                         for t in item['tags']])),
        ],
    )


def _figure(item):
    return html.Figure(
        className='case-study-figure',
        children=[
            html.A(
                href=item['thumbnail_src'],
                target='_blank',
                rel='noreferrer',
                className='case-study-image-link',
                **{
                    'data-track': 'case_study_image_expand',
                    'data-track-location': 'case_study_page',
                    'data-track-label': item['slug'],
                },
                children=html.Img(src=item['thumbnail_src'],
                                  className='case-study-image',
                                  alt=item['thumbnail_alt']),
            ),
            html.Figcaption(item['image_caption'], className='case-study-caption'),
        ],
    )


def _demo_shots(item):
    return html.Div(
        className='demo-shot-grid',
        children=[
            html.Figure(
                className='demo-shot',
                children=[
                    html.A(
                        href=shot['src'],
                        target='_blank',
                        rel='noreferrer',
                        className='case-study-image-link',
                        **{
                            'data-track': 'demo_image_expand',
                            'data-track-location': 'case_study_page',
                            'data-track-label': shot['src'].rsplit('/', 1)[-1],
                        },
                        children=html.Img(src=shot['src'],
                                          className='case-study-image',
                                          alt=shot['alt']),
                    ),
                    html.Figcaption(shot['caption'], className='case-study-caption'),
                ],
            )
            for shot in item['shots']
        ],
    )


def _pager(item):
    previous, following = neighbours(item['slug'])
    return html.Nav(
        className='case-pager',
        **{'aria-label': 'Project navigation'},
        children=[
            html.A(
                href=detail_href(previous),
                className='case-pager-link case-pager-prev',
                children=[
                    html.Span('Previous project', className='case-pager-label'),
                    html.Span(previous['title'], className='case-pager-title'),
                ],
            ),
            html.A(
                href=detail_href(following),
                className='case-pager-link case-pager-next',
                children=[
                    html.Span('Next project', className='case-pager-label'),
                    html.Span(following['title'], className='case-pager-title'),
                ],
            ),
        ],
    )


def _layout(item):
    main = []

    if item['slug'] == 'tidepool-commerce-analytics':
        main.extend([
            _prose('Overview', item['problem_line']),
            _demo_shots(item),
            _list('What it does', item['highlights']),
            html.A('Open the live demo →', href=item['href'],
                   className='cta-primary case-detail-cta',
                   **{'data-track': 'case_study_demo_click',
                      'data-track-location': 'case_study_page'}),
        ])
        side = _demo_sidebar(item)
    else:
        if item.get('thumbnail_src'):
            main.append(_figure(item))
        main.extend([
            _prose('Overview', item['overview']),
            _prose('Problem', item['problem_statement']),
            _list('Approach', item['methods']),
            _list('What I built', item['what_i_built']),
            _results(item['impact']),
        ])
        side = _sidebar(item)

    page_class = 'content-stack case-study-page'
    if is_research(item):
        page_class += ' case-study-page--research'

    return html.Div(
        className=page_class,
        children=[
            html.Section(
                className='case-study-header reveal-up',
                children=[
                    html.A('Selected Work', href='/projects', className='case-backlink'),
                    html.Div(item['scope'], className='project-scope'),
                    html.H1(item['title'], className='section-hero-title'),
                    html.P(outcome(item), className='case-lede'),
                    tags(item),
                ],
            ),
            html.Section(
                className='case-study-body',
                children=[
                    html.Div(main, className='case-study-main'),
                    side,
                ],
            ),
            _pager(item),
        ],
    )


for _item in WORK:
    dash.register_page(
        f"{__name__}.{_item['slug'].replace('-', '_')}",
        path=detail_href(_item),
        name=_item['title'],
        title=f"{_item['title']} | Hyungju Lee",
        description=outcome(_item),
        layout=_layout(_item),
    )
