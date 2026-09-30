"""Napkin artwork, laid out on the unfolded sheet (1 unit = 0.1 mm).
Run: python3 products/napkin/make_art.py && node tools/raster.mjs products/napkin/art

Two maps, both covering the whole unfolded sheet (see dims.py):
- sheet.svg: paper colour and the printed Hindi line;
- emboss.svg: the height map of the embossed pattern (white = raised).

Mapping: sheet u runs left to right, v bottom to top (the image's top edge is
the flap's free edge). After fold 2 the flap lies face down over the base, so
the line is drawn mirrored top-to-bottom here and reads correctly on the pack.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

from brand.indigo import INDIGO_BLUE, svg  # noqa: E402

import dims  # noqa: E402

U = 100  # units per cm
SW, SH = dims.SHEET_W * U, dims.SHEET_H * U
PAPER = '#f6f5f1'
INK = INDIGO_BLUE
os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)

# ---------------------------------------------------------------- printed sheet
# The line, set as on the napkin: the proverb in a heavy weight, its last two
# words lighter and a little smaller. Mukta is the closest open face to the
# printed Devanagari (narrow, tight, strong headline).
size = 0.735 * U  # sized so the whole line spans dims.TEXT_WIDTH
x0 = dims.TEXT_LEFT * U
y0 = dims.TEXT_BASELINE * U  # from the flap's free edge (the image's top)
line = (
    f'<text x="0" y="0" font-family="Mukta" font-weight="700" font-size="{size:.1f}" fill="{INK}" letter-spacing="-0.4">'
    'दाने दाने पे लिखा है खाने वाले '
    f'<tspan font-weight="400" font-size="{size * 0.9:.1f}">का नाम।</tspan>'
    '</text>'
)
sheet = (
    '<defs><filter id="ink" x="-5%" y="-50%" width="110%" height="200%">'
    '<feGaussianBlur stdDeviation="0.45"/></filter></defs>'
    f'<rect width="{SW:.0f}" height="{SH:.0f}" fill="{PAPER}"/>'
    f'<g transform="translate({x0:.1f} {y0:.1f}) scale(1 -1)" filter="url(#ink)">{line}</g>'
)
open(os.path.join(HERE, 'art', 'sheet.svg'), 'w').write(svg(SW, SH, sheet, px=6144))

# ---------------------------------------------------------------- emboss
# Pairs of concentric dotted rings on a square lattice, the pattern pressed
# into the tissue. Neighbouring rings just overlap, like links of a chain;
# where two rings cross, the second dot is left out so crossings stay clean.
R = dims.RING_R * U
P = dims.RING_PITCH * U
placed = []
cell = {}
min_gap = 0.2 * U


def free(x, y):
    cx, cy = int(x // min_gap), int(y // min_gap)
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for px, py, _ in cell.get((cx + i, cy + j), ()):
                if (px - x) ** 2 + (py - y) ** 2 < min_gap**2:
                    return False
    return True


y = -P / 2
while y < SH + P:
    x = -P / 2
    while x < SW + P:
        for r in (R, R * 0.58):  # each ring has a smaller one inside it
            n = max(8, round(2 * math.pi * r / (dims.DOT_PITCH * U)))
            for k in range(n):
                a = 2 * math.pi * (k + 0.5) / n
                dx, dy = x + r * math.cos(a), y + r * math.sin(a)
                if -20 < dx < SW + 20 and -20 < dy < SH + 20 and free(dx, dy):
                    placed.append((dx, dy, math.degrees(a) + 90))
                    cell.setdefault((int(dx // min_gap), int(dy // min_gap)), []).append(placed[-1])
        x += P
    y += P
# Each dot is a short dash along its ring, as the embossing pins press it.
dots = [f'<ellipse cx="0" cy="0" rx="7" ry="4.4" transform="translate({x:.1f} {y:.1f}) rotate({t:.1f})"/>' for x, y, t in placed]
emboss = (
    '<defs><filter id="soft" x="0" y="0" width="100%" height="100%">'
    '<feGaussianBlur stdDeviation="2.6"/></filter></defs>'
    f'<rect width="{SW:.0f}" height="{SH:.0f}" fill="#000"/>'
    f'<g fill="#fff" filter="url(#soft)">{"".join(dots)}</g>'
)
open(os.path.join(HERE, 'art', 'emboss.svg'), 'w').write(svg(SW, SH, emboss, px=6144))
print(f'art written ({len(dots)} emboss dots)')
