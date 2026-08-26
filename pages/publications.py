from typing import Optional

import dash
from dash import html

from research_content import FIELD_WORK, RESEARCH_FIGURES


dash.register_page(__name__, order=3, name='Research')


RESEARCH_THEMES = [
    {
        'title': '3D Vision and LiDAR',
        'copy': 'Airborne LiDAR, point cloud representations, volumetric modeling, detection workflows, and scene-level spatial reasoning.',
        'tags': ['LiDAR', 'Point Clouds', '3D Vision', 'Detection'],
    },
    {
        'title': 'Benchmarking and Evaluation',
        'copy': 'Dataset design, annotation QA, benchmark protocol definition, comparative model analysis, and reproducible evaluation logic.',
        'tags': ['Benchmark Design', 'Evaluation', 'Annotation QA', 'Comparative Analysis'],
    },
    {
        'title': 'Research Engineering',
        'copy': 'Technical experimentation, preprocessing pipelines, methodological synthesis, and publication-grade communication of results.',
        'tags': ['Experimentation', 'Pipelines', 'Research Synthesis', 'Technical Writing'],
    },
]


def _figure_card(figure):
    span = figure.get('span')
    className = 'research-figure' + (f' research-figure--{span}' if span else '')
    return html.Figure(
        className=className,
        children=[
            html.Div(
                className='research-figure-plate',
                # No loading="lazy" here: dash.html.Img rejects the attribute.
                # The static build, which is the one that ships, sets it.
                children=html.Img(src=figure['src'], alt=figure['alt'],
                                  className='research-figure-image'),
            ),
            html.Figcaption(figure['caption'], className='research-figure-caption'),
        ],
    )


def _field_work_card(item):
    return html.Article(
        className='glass-card field-work-card reveal-up',
        children=[
            html.Figure(
                className='field-work-figure',
                children=[
                    html.Img(src=item['image'], alt=item['alt'],
                             className='field-work-image'),
                    html.Figcaption(item['caption'], className='research-figure-caption'),
                ],
            ),
            html.Div(
                className='field-work-body',
                children=[
                    html.Div(item['meta'], className='paper-venue'),
                    html.H4(item['title'], className='research-theme-title'),
                    html.P(item['copy'], className='research-theme-copy'),
                    html.Ul(
                        className='case-detail-list',
                        children=[html.Li(point) for point in item['points']],
                    ),
                    html.Div(
                        className='skill-cloud',
                        children=[html.Span(tag, className='skill-pill')
                                  for tag in item['tags']],
                    ),
                ],
            ),
        ],
    )


def _paper_block(venue: str, place: str, title: str, abstract: str, link: Optional[str] = None):
    link_node = html.A('Open link', href=link, target='_blank', rel='noreferrer', className='paper-link') if link else None
    return html.Article(
        className='glass-card paper-card reveal-up',
        children=[
            html.Div(venue, className='paper-venue'),
            html.Div(place, className='paper-place'),
            html.H5(title, className='paper-title'),
            html.P(abstract, className='paper-abstract'),
            link_node,
        ],
    )


def _theme_card(title: str, copy: str, tags):
    return html.Article(
        className='glass-card research-theme-card reveal-up',
        children=[
            html.H4(title, className='research-theme-title'),
            html.P(copy, className='research-theme-copy'),
            html.Div(
                className='skill-cloud',
                children=[html.Span(tag, className='skill-pill') for tag in tags],
            ),
        ],
    )


layout = html.Div(
    className='content-stack',
    children=[
        html.Section(
            className='reveal-up',
            children=[
                html.Div('RESEARCH', className='eyebrow'),
                html.H2('Research and Publications', className='section-hero-title'),
                html.P(
                    'Selected work in LiDAR, computer vision, benchmark datasets, segmentation-oriented analysis, '
                    'and research engineering workflows.',
                    className='section-hero-subtitle',
                ),
            ],
        ),
        html.Section(
            className='research-theme-grid',
            children=[_theme_card(theme['title'], theme['copy'], theme['tags']) for theme in RESEARCH_THEMES],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H3('Field Work', className='section-title'),
                html.P(
                    'Data collection and pipeline work done on site, not from a desk.',
                    className='section-note',
                ),
                _field_work_card(FIELD_WORK),
            ],
        ),
        html.Section(
            className='reveal-up',
            children=[
                html.H3('Selected Figures', className='section-title'),
                html.P(
                    'From the thesis and the project report, with what each one is '
                    'actually showing.',
                    className='section-note',
                ),
                # Wrapped in the same surface the field-work entry uses: without
                # it the plates floated loose on the page while every other
                # block on the site sat on a card.
                html.Div(
                    className='glass-card research-figure-card reveal-up',
                    children=html.Div(
                        className='research-figure-grid',
                        children=[_figure_card(figure) for figure in RESEARCH_FIGURES],
                    ),
                ),
            ],
        ),
        html.Section(
            className='paper-stack',
            children=[
                _paper_block(
                    'ISPRS 2023',
                    'Cairo, Egypt',
                    'YUTO: A Large Scale Aerial LiDAR Data Set for Semantic Segmentation',
                    'Introduced a large-scale aerial LiDAR benchmark dataset for semantic segmentation of urban forest scenes, '
                    'supporting more standardized evaluation across deep learning methods.',
                ),
                _paper_block(
                    'ICPR 2022',
                    'Montreal, Canada',
                    'YUTO Tree-5000: A Large-scale Airborne LiDAR Data for Single Tree Detection',
                    'Presented a large-scale annotated airborne LiDAR dataset of 5,000+ individually labeled tree instances, '
                    'designed to establish a reproducible benchmark for single-tree detection algorithms.',
                    'https://doi.org/10.1007/978-3-031-37731-0_28',
                ),
                _paper_block(
                    'Master Thesis',
                    'York University, Toronto',
                    'Deep convolutional neural network based single tree detection using volumetric module from airborne LiDAR data',
                    'Developed a volumetric deep CNN workflow for detecting individual trees from airborne LiDAR point clouds, '
                    'with strong benchmark performance and a Best Master\'s Thesis award at York University.',
                    'https://yorkspace.library.yorku.ca/items/8c15e8bb-8672-4615-be4a-6b66ca6bdfdf',
                ),
            ],
        ),
    ],
)
