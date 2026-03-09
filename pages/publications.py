import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from typing import Optional


dash.register_page(__name__, order=2, name='Publications')


def _paper_block(venue: str, place: str, title: str, link: Optional[str] = None):
    link_node = dcc.Link('Open link', href=link, target='_blank', className='paper-link') if link else None
    return html.Article(
        className='glass-card paper-card reveal-up',
        children=[
            html.Div(venue, className='paper-venue'),
            html.Div(place, className='paper-place'),
            html.H5(title, className='paper-title'),
            link_node,
        ],
    )


layout = dbc.Container(
    className='content-stack',
    children=[
        html.Section(
            className='reveal-up',
            children=[
                html.Div('RESEARCH OUTPUTS', className='eyebrow'),
                html.H2('Publications', className='section-hero-title'),
                html.P(
                    'Selected work in LiDAR data, computer vision, and large-scale annotation benchmarks.',
                    className='section-hero-subtitle',
                ),
            ],
        ),
        _paper_block(
            'ISPRS 2023',
            'Cairo, Egypt',
            'YUTO: A Large Scale Aerial LiDAR Data Set for Semantic Segmentation',
        ),
        _paper_block(
            'ICPR 2022',
            'Montreal, Canada',
            'YUTO Tree-5000: A Large-scale Airborne LiDAR Data for Single Tree Detection',
            'https://doi.org/10.1007/978-3-031-37731-0_28',
        ),
        _paper_block(
            'Master Thesis',
            'York University, Toronto',
            'Deep convolutional neural network based single tree detection using volumetric module from airborne LiDAR data',
            'https://yorkspace.library.yorku.ca/items/8c15e8bb-8672-4615-be4a-6b66ca6bdfdf',
        ),
    ],
)
