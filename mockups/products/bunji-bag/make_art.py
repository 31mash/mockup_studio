"""Bunji! bag artwork, laid out on the bag's real panels (1 unit = 0.1 mm).
Drawn in ink on white: the kraft material multiplies it over the paper, so
white is bare kraft.
Run: python3 products/bunji-bag/make_art.py && node tools/raster.mjs products/bunji-bag/art"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)

from brand.indigo import svg  # noqa: E402

import dims  # noqa: E402
from figure import INK, figure  # noqa: E402

U = 100  # units per cm
# Inks, chosen so that multiplied over the kraft they land on the photo's
# colours: a brown-black, a warm letterpress red and a dark maroon-brown rule.
RED = '#d65a52'  # the lettering's offset shadow
FRAME_INK = '#6f423d'  # the frame's rope rule
ART = os.path.join(HERE, 'art')
os.makedirs(ART, exist_ok=True)

W, H = dims.W * U, dims.H * U
fx, fy, fw, fh = (v * U for v in dims.FRAME)
band = dims.BAND * U


def frame() -> str:
    """The rope rule: a dark band with a chain of paper-coloured lozenges,
    the dark left between them reading as twisted crossings."""
    out = []
    c = band / 2
    x0, y0, x1, y1 = fx + c, fy + c, fx + fw - c, fy + fh - c
    out.append(
        f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" '
        f'fill="none" stroke="{FRAME_INK}" stroke-width="{band:.1f}"/>'
    )
    pitch = band * 1.05
    a = band * 0.30  # lozenge half-length along the band
    b = band * 0.17  # ... and half-width across it
    e = band * 0.16  # the edge notches between them

    def side(xa, ya, xb, yb):
        length = math.hypot(xb - xa, yb - ya)
        n = max(2, round(length / pitch))
        ux, uy = (xb - xa) / length, (yb - ya) / length
        vx, vy = -uy, ux
        for i in range(n):
            t = (i + 0.5) / n
            x, y = xa + (xb - xa) * t, ya + (yb - ya) * t
            pts = [(x + ux * a, y + uy * a), (x + vx * b, y + vy * b), (x - ux * a, y - uy * a), (x - vx * b, y - vy * b)]
            out.append('<path d="M ' + ' L '.join(f'{px:.1f},{py:.1f}' for px, py in pts) + ' Z" fill="#ffffff"/>')
            if i:  # notches on both edges, half-way between lozenges
                t2 = i / n
                x2, y2 = xa + (xb - xa) * t2, ya + (yb - ya) * t2
                for sgn in (1, -1):
                    ex, ey = x2 + vx * sgn * c * 0.98, y2 + vy * sgn * c * 0.98
                    tri = [(ex + ux * e, ey + uy * e), (ex - vx * sgn * e * 0.9, ey - vy * sgn * e * 0.9), (ex - ux * e, ey - uy * e)]
                    out.append('<path d="M ' + ' L '.join(f'{px:.1f},{py:.1f}' for px, py in tri) + ' Z" fill="#ffffff"/>')

    side(x0 + c, y0, x1 - c, y0)
    side(x0 + c, y1, x1 - c, y1)
    side(x0, y0 + c, x0, y1 - c)
    side(x1, y0 + c, x1, y1 - c)
    return ''.join(out)


def lettering() -> str:
    """'Bunji!' as the photo shows it: heavy italic sign-writing, sheared so
    the baseline climbs while the stems stay leaning forward, in brown-black
    with a red shadow offset straight to the right."""
    size = dims.LETTER_SIZE * U
    x, y = (v * U for v in dims.LETTER_AT)  # baseline start, from the frame's corner
    common = (
        f'font-family="Libre Baskerville" font-style="italic" font-weight="700" font-size="{size:.1f}" '
        f'letter-spacing="{0.07 * U:.1f}" stroke-linejoin="round" stroke-width="{0.1 * U:.1f}"'
    )
    # The shear lifts the baseline; skewX takes back a little of the font's
    # italic angle, as the original's stems lean less.
    shear = f'skewY({-dims.LETTER_RISE}) skewX({dims.LETTER_UNSLANT}) scale({dims.LETTER_WIDEN},1)'
    layers = []
    for (dx, dy), col in (((0.17 * U, 0.02 * U), RED), ((0, 0), INK)):
        layers.append(
            f'<g transform="translate({fx + x + dx:.1f},{fy + y + dy:.1f}) {shear}"><text {common} fill="{col}" stroke="{col}">Bunji!</text></g>'
        )
    return ''.join(layers)


COPY = [  # broken to the measured widths of Libre Baskerville at COPY_SIZE
    'It isn’t a new-fangled airline diet, nor is it a',
    'bungee jump. Bunji is simply our humble',
    'bun, dressed up with a little respect. In',
    'India we add a ‘ji’ to anyone we hold dear,',
    'so why not to the soft, golden, buttery bun',
    'that has kept us company over countless',
    'cups of chai? Ours is baked fresh every',
    'morning, split, filled generously and',
    'wrapped while it is still warm. It asks for',
    'nothing more than a window seat and a',
    'little of your attention. Handle it gently,',
    'share it only if you must, and enjoy every',
    'last bite before the seat-belt sign comes',
    'back on. Bunji. The pleasure is all ours.',
]


def paragraph() -> str:
    x = fx + dims.COPY_AT[0] * U
    y = fy + dims.COPY_AT[1] * U
    size = dims.COPY_SIZE * U
    lead = dims.COPY_LEAD * U
    font = 'font-family="Libre Baskerville"'
    out = [f'<text x="{x:.1f}" y="{y:.1f}" {font} font-weight="700" font-size="{size * 1.1:.1f}" fill="{INK}">No.</text>']
    for i, line in enumerate(COPY):
        out.append(f'<text x="{x:.1f}" y="{y + 0.05 * U + (i + 1) * lead:.1f}" {font} font-size="{size:.1f}" fill="{INK}">{line}</text>')
    return ''.join(out)


def front() -> str:
    body = (
        f'<rect width="{W:.0f}" height="{H:.0f}" fill="#ffffff"/>'
        + frame()
        + lettering()
        + paragraph()
        + figure(fx + 6.4 * U, fy + 4.0 * U, U, uid='boxer')
    )
    return svg(W, H, body)


def back() -> str:
    """Unprinted back: only the glue seam of the paper tube, a faint line
    with a soft shadow beside it."""
    sx = dims.SEAM_X * U
    body = (
        f'<defs><linearGradient id="seam" x1="0" x2="1"><stop offset="0" stop-color="#e9e1d6"/><stop offset="1" stop-color="#ffffff"/></linearGradient></defs>'
        f'<rect width="{W:.0f}" height="{H:.0f}" fill="#ffffff"/>'
        f'<rect x="{sx:.1f}" y="0" width="{0.22 * U:.1f}" height="{H:.0f}" fill="url(#seam)"/>'
        f'<rect x="{sx - 0.015 * U:.1f}" y="0" width="{0.03 * U:.1f}" height="{H:.0f}" fill="#d8cdbf"/>'
    )
    return svg(W, H, body, px=2048)


open(os.path.join(ART, 'front.svg'), 'w').write(front())
open(os.path.join(ART, 'back.svg'), 'w').write(back())
print('art written')
