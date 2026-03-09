import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from typing import Optional


dash.register_page(__name__, order=2, name='Publications')


def _pub_row(
    left_title: str,
    left_subtitle: str,
    location: str,
    right_title: str,
    right_link: Optional[str] = None,
):
    right_content = [dcc.Markdown(f'##### {right_title}', className='ms-1')]
    if right_link:
        right_content.append(dcc.Markdown(f'[DOI / Link]({right_link})', className='ms-1'))

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Markdown(f'#### {left_title}  \\n{left_subtitle}'),
                            dcc.Markdown(location),
                        ],
                        width=3,
                    ),
                    dbc.Col(right_content, width=8),
                ],
                justify='center',
            ),
            html.Hr(),
        ]
    )


def layout():
    return dbc.Container(
        [
            html.H3('Publications', className='mb-3'),
            _pub_row(
                'ISPRS 2023',
                'International Society for Photogrammetry and Remote Sensing',
                'Cairo, Egypt',
                'YUTO: A Large Scale Aerial LiDAR Data Set for Semantic Segmentation',
                None,
            ),
            _pub_row(
                'ICPR 2022',
                'International Conference on Pattern Recognition',
                'Montreal, Canada',
                'YUTO Tree-5000: A Large-scale Airborne LiDAR Data for Single Tree Detection',
                'https://doi.org/10.1007/978-3-031-37731-0_28',
            ),
            _pub_row(
                'Master Thesis',
                'York University',
                'Toronto, Canada',
                'Deep convolutional neural network based single tree detection using volumetric module from airborne LiDAR data',
                'https://yorkspace.library.yorku.ca/items/8c15e8bb-8672-4615-be4a-6b66ca6bdfdf',
            ),
        ],
        className='py-4',
    )
