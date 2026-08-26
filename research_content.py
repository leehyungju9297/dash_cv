"""Research page content that is data, not layout.

Kept beside ``case_studies.py`` and out of the page module for the same reason:
the Dash page and the hand-written static mirror in ``docs/`` both read from
here, so the two cannot describe the same figure differently.
"""

from typing import Dict, List


# Figures lifted from the thesis and the project report, kept whole rather than
# cropped: they are diagrams, and a crop would remove the panel a caption refers
# to. Captions state what each one shows, including when it shows a failure.
RESEARCH_FIGURES = [
    {
        'src': '/assets/research/segmentation-failure-modes.jpg',
        # A nine-panel portrait figure among three wide strips: it takes the
        # left column across two rows so nothing has to be cropped to fit.
        'span': 'tall',
        'alt': 'Nine street-level photographs with overlaid instance masks, labelled '
               'combined, double, hedge, small, occluded, shadow, other, encapsulated '
               'and leaf-off.',
        'caption': 'Why single-tree detection is hard: Mask R-CNN instance segmentation '
                   'failing across nine categories \u2014 merged crowns, hedges, '
                   'occlusion, shadow, leaf-off. These are error cases, not results, and '
                   'they set what the benchmark had to isolate.',
    },
    {
        'src': '/assets/research/yuto-benchmark-items.jpg',
        'alt': 'Four panels over one scene: semantic classification, aerial reference '
               'photo, tree instance polygons, and 3D bounding boxes on the point cloud.',
        'caption': 'YUTO Tree-5000 benchmark items \u2014 the same scene as a semantic '
                   'classification, an aerial reference, hand-drawn instance polygons, '
                   'and 3D boxes on the point cloud.',
    },
    {
        'src': '/assets/research/point-density-comparison.jpg',
        'alt': 'Two normalised point-density maps side by side, ground-vehicle LiDAR '
               'against airborne LiDAR, with a shared colour scale.',
        'caption': 'Point density, ground-vehicle LiDAR against airborne \u2014 the '
                   'sparsity that makes an airborne single-tree benchmark a different '
                   'problem from an automotive one.',
    },
    {
        'src': '/assets/research/detection-model-comparison.jpg',
        'span': 'wide',
        'alt': 'Two line charts of average precision against IoU threshold for eight 3D '
               'detection networks, in bird\u2019s-eye view and in 3D.',
        'caption': 'Average precision against IoU for eight 3D detectors, in '
                   'bird\u2019s-eye view and full 3D \u2014 the comparison the '
                   'benchmark exists to make possible.',
    },
]


FIELD_WORK = {
    'title': 'Multi-Sensor Field Dataset for Autonomous Rail',
    'meta': 'York-Durham Heritage Railway \u00b7 October 2019',
    'image': '/assets/research/ydhr-field-test.jpg',
    'alt': 'Three engineers in high-visibility vests beside a railway track, working at '
           'an instrumented sensor mast mounted on a rail cart, with heritage railcars '
           'behind them.',
    'caption': 'Building and running the sensor rig on the track \u2014 the cart carried '
               'the camera and LiDAR through each test run.',
    'copy': 'Field data collection for object detection on rail: a camera, a Cepton '
            'LiDAR and radar mounted on a cart and run along a heritage railway across '
            'seven tests of two to four runs each.',
    'points': [
        'Extracted frames at 10 Hz with ffmpeg and converted each recording timestamp '
        'to Unix time, which is what let the camera, LiDAR and radar streams be lined '
        'up at all.',
        'Cut the raw LiDAR into 0.1-second scenes so every scene had exactly one frame '
        'to match, then solved the per-test time offset and the camera intrinsics and '
        'extrinsics by hand \u2014 the delivered data was missing mounting geometry '
        '\u2014 and checked the alignment against rendered depth maps.',
        'Hand-labelled roughly 19,000 bounding boxes with a colleague across six '
        'classes (person, car, train, box, bicycle, switch position indicator), '
        'exported in both YOLO and PascalVOC layouts.',
    ],
    'tags': ['Sensor Fusion', 'LiDAR', 'Field Data Collection', 'Annotation Pipelines',
             'Camera Calibration', 'Object Detection'],
}
