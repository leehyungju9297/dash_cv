"""Build the land mask the order generator uses to keep points out of water.

The demo scatters one marker per order around each market centroid. Without a
land test those markers land in the Atlantic off New York, in the Gulf below
Houston, in Puget Sound and in the Great Lakes — obviously invalid locations
for a delivery, and the first thing anyone notices about the map.

Testing a point against real polygons at generation time would mean shipping
polygons to the browser and running point-in-polygon there, twice (the Dash app
and its JavaScript twin generate the same points and must agree bit for bit).
Instead this rasterises Natural Earth's land and lakes once, offline, into a
boolean grid, and both runtimes do an O(1) array lookup.

    python3 -m tools.build_land_mask [--source DIR] [--out PATH]

The output is checked in, so the app never needs the source polygons or a
network connection. Re-run it only to change the resolution or the source data.

Source: Natural Earth 1:10m `land` and `lakes`, public domain.
    https://github.com/nvkelso/natural-earth-vector/tree/master/geojson
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import urllib.request

from PIL import Image, ImageDraw


# 0.05 degrees is about 5.5 km. A cell is land when the majority of it is, so a
# generated point sits at most half a cell — under three kilometres — off a true
# coastline, which is inside the width of a waterfront district and far inside
# what the map can show. The clouds this replaces reached hundreds of kilometres
# out to sea.
CELLS_PER_DEGREE = 20

# Each cell is judged by sampling it SUBSAMPLE x SUBSAMPLE times, so the
# coastline follows the polygon rather than snapping to the grid.
SUBSAMPLE = 4

# A cell counts as land when the majority of it is — the truest coastline this
# grid can draw. Four waterfront city centres come out of that vote as sea
# (Toronto, Miami, Detroit, Anchorage all sit on a shore), so the cells holding
# a market centroid are marked land afterwards: those are the places the demo
# ships to, and a city is on land by definition.
LAND_THRESHOLD = 0.5

# Beyond a market's own reach the mask carries no information any point will
# ever ask for, so it is cleared — which costs nothing in accuracy and lets the
# run-length encoding collapse the empty half of the world into a few runs.
#
# The reach is the generator's own worst case, not a guess: an offset is the
# satellite-centre term plus the radial term, each scaled by the elliptical
# stretch, and longitude takes a further 1.3. See _market_shape and
# scatter_orders in demo_dashboard/geo.py for each factor.
_MAX_STRETCH = 1.65          # 0.75 + 0.9
_MAX_TAIL = 7.0              # 3 + 4, the far-delivery multiplier
_CENTRE_OFFSET = 0.34
_LON_STRETCH = 1.3

_REACH_LAT = _MAX_STRETCH * (_CENTRE_OFFSET + _MAX_TAIL)
_REACH_LON = _REACH_LAT * _LON_STRETCH

# The two spreads scatter_orders uses, keyed the way it keys them.
_SPREAD = {'United States': 0.95}
_SPREAD_DEFAULT = 1.35

BASE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson'
LAYERS = ('ne_10m_land', 'ne_10m_lakes')


def _load(name: str, source: pathlib.Path | None) -> dict:
    if source is not None:
        return json.loads((source / f'{name}.geojson').read_text())
    with urllib.request.urlopen(f'{BASE}/{name}.geojson', timeout=120) as response:
        return json.loads(response.read().decode())


def _polygons(collection: dict):
    """Every polygon in a FeatureCollection, as [outer_ring, *holes]."""
    for feature in collection['features']:
        geometry = feature['geometry']
        if geometry['type'] == 'MultiPolygon':
            yield from geometry['coordinates']
        else:
            yield geometry['coordinates']


def rasterize(source: pathlib.Path | None) -> Image.Image:
    land = _load('ne_10m_land', source)
    lakes = _load('ne_10m_lakes', source)

    width = 360 * CELLS_PER_DEGREE * SUBSAMPLE
    height = 180 * CELLS_PER_DEGREE * SUBSAMPLE
    canvas = Image.new('1', (width, height), 0)
    pen = ImageDraw.Draw(canvas)

    def to_pixels(ring):
        return [((lon + 180.0) / 360.0 * width, (90.0 - lat) / 180.0 * height)
                for lon, lat in ring]

    for polygon in _polygons(land):
        pen.polygon(to_pixels(polygon[0]), fill=1)
        for hole in polygon[1:]:
            pen.polygon(to_pixels(hole), fill=0)

    # Lakes are land in the `land` layer, so they are cut back out. The Great
    # Lakes are the reason: Chicago, Detroit and Toronto all sit on one.
    for polygon in _polygons(lakes):
        pen.polygon(to_pixels(polygon[0]), fill=0)

    # Majority vote: BOX resampling averages the sub-samples, and the threshold
    # turns that average back into a boolean.
    averaged = canvas.convert('L').resize(
        (width // SUBSAMPLE, height // SUBSAMPLE), Image.BOX)
    cut = 255 * LAND_THRESHOLD
    return averaged.point(lambda level: 255 if level >= cut else 0).convert('1')


def _market_cells(mask: Image.Image):
    """Grid cells holding a market centroid, and each market's reach box."""
    from demo_dashboard.data import CITY_TABLE
    width, height = mask.size
    cells = []
    boxes = []
    for _city, _region, country, lat, lon, _weight in CITY_TABLE:
        column = int((lon + 180.0) * CELLS_PER_DEGREE)
        row = int((90.0 - lat) * CELLS_PER_DEGREE)
        if 0 <= column < width and 0 <= row < height:
            cells.append((column, row))
        spread = _SPREAD.get(country, _SPREAD_DEFAULT)
        reach_row = int(spread * _REACH_LAT * CELLS_PER_DEGREE) + 1
        reach_column = int(spread * _REACH_LON * CELLS_PER_DEGREE) + 1
        boxes.append((max(0, column - reach_column), max(0, row - reach_row),
                      min(width - 1, column + reach_column),
                      min(height - 1, row + reach_row)))
    return cells, boxes


def _focus(mask: Image.Image) -> Image.Image:
    """Keep real geography near the markets; clear everything else."""
    cells, boxes = _market_cells(mask)
    keep = Image.new('1', mask.size, 0)
    pen = ImageDraw.Draw(keep)
    for box in boxes:
        pen.rectangle(box, fill=1)
    focused = Image.new('1', mask.size, 0)
    focused.paste(mask, (0, 0), keep)
    pen = ImageDraw.Draw(focused)
    for column, row in cells:
        pen.point((column, row), fill=1)
    return focused


def _varint(value: int, out: bytearray) -> None:
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)


def encode(mask: Image.Image) -> str:
    """Run-length encode the grid, row-major, as base64 varints.

    A boolean world map is mostly very long runs — the Pacific is one — so the
    run lengths compress the grid by more than twenty to one before base64
    undoes a third of it. The first run is always water, with a zero-length run
    in front of it when the grid happens to start on land.
    """
    bits = list(mask.getdata())
    runs = []
    current = 0
    length = 0
    for bit in bits:
        value = 1 if bit else 0
        if value == current:
            length += 1
        else:
            runs.append(length)
            current = value
            length = 1
    runs.append(length)

    payload = bytearray()
    for run in runs:
        _varint(run, payload)
    return base64.b64encode(bytes(payload)).decode('ascii')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=pathlib.Path, default=None,
                        help='directory holding the Natural Earth geojson files; '
                             'downloads them when omitted')
    parser.add_argument('--out', type=pathlib.Path,
                        default=pathlib.Path(__file__).parent.parent
                        / 'demo_dashboard' / 'land_mask.txt')
    args = parser.parse_args()

    mask = _focus(rasterize(args.source))
    width, height = mask.size
    encoded = encode(mask)
    args.out.write_text(
        f'{CELLS_PER_DEGREE} {width} {height}\n{encoded}\n')

    cells = width * height
    land = sum(1 for bit in mask.getdata() if bit)
    print(f'grid {width}x{height} ({cells:,} cells, {land / cells:.1%} land)')
    print(f'encoded {len(encoded) / 1024:.0f} KB -> {args.out}')


if __name__ == '__main__':
    main()
