from typing import Optional

import dash
from dash import html


dash.register_page(__name__, order=2, name='Research')


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
)
