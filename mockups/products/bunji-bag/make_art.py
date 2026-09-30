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
RED = '#c8372c'  # the red of the lettering's offset shadow
FRAME_RED = '#8f2b25'  # the frame's deeper red
ART = os.path.join(HERE, 'art')
os.makedirs(ART, exist_ok=True)

W, H = dims.W * U, dims.H * U
fx, fy, fw, fh = (v * U for v in dims.FRAME)
band = dims.BAND * U


def frame() -> str:
    """A thin red border with a row of reversed-out diamonds, like an old
    letterpress rule."""
    out = [
        f'<rect x="{fx + band / 2:.1f}" y="{fy + band / 2:.1f}" width="{fw - band:.1f}" height="{fh - band:.1f}" '
        f'fill="none" stroke="{FRAME_RED}" stroke-width="{band:.1f}"/>'
    ]
    d = band * 0.2  # diamond half-size
    pitch = band * 0.66

    def row(x0, y0, x1, y1):
        length = math.hypot(x1 - x0, y1 - y0)
        n = max(1, round(length / pitch))
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            out.append(f'<path d="M {x - d:.1f},{y:.1f} L {x:.1f},{y - d:.1f} L {x + d:.1f},{y:.1f} L {x:.1f},{y + d:.1f} Z" fill="#ffffff"/>')

    c = band / 2
    x0, y0, x1, y1 = fx + c, fy + c, fx + fw - c, fy + fh - c
    row(x0, y0, x1, y0)
    row(x0, y1, x1, y1)
    row(x0, y0, x0, y1)
    row(x1, y0, x1, y1)
    # Hairlines just inside and outside the band.
    for inset, sw in ((-band * 0.12, 1.6), (band * 1.12, 1.6)):
        out.append(
            f'<rect x="{fx + inset:.1f}" y="{fy + inset:.1f}" width="{fw - 2 * inset:.1f}" height="{fh - 2 * inset:.1f}" '
            f'fill="none" stroke="{FRAME_RED}" stroke-width="{sw}"/>'
        )
    return ''.join(out)


def lettering() -> str:
    """'Bunji!' in a heavy brush italic, set rising, in near-black with a
    red offset shadow to the right."""
    size = 2.5 * U
    cx, cy = fx + 4.5 * U, fy + 3.9 * U  # baseline centre
    common = f'font-family="Yatra One" font-size="{size:.1f}" text-anchor="middle" stroke-linejoin="round" letter-spacing="{0.06 * U:.1f}"'
    layers = []
    for dx, dy, col in ((0.13 * U, 0.05 * U, RED), (0, 0, INK)):
        layers.append(
            f'<text x="{dx:.1f}" y="{dy:.1f}" {common} fill="{col}" stroke="{col}" stroke-width="{0.085 * U:.1f}">Bunji!</text>'
        )
    return f'<g transform="translate({cx:.1f},{cy:.1f}) rotate(-19)">{"".join(layers)}</g>'


COPY = [
    'It isn’t a new-fangled airline diet, nor is it',
    'a bungee jump. Bunji is simply our humble bun,',
    'dressed up with a little respect. In India we',
    'add a ‘ji’ to anyone we hold dear, so why not',
    'to the soft, golden, buttery bun that has kept',
    'us company over countless cups of chai? Ours',
    'is baked fresh every morning, split, filled',
    'generously and wrapped while it is still warm.',
    'It asks for nothing more than a window seat',
    'and a little of your attention. Handle it',
    'gently, share it only if you must, and enjoy',
    'every last bite before the seat-belt sign',
    'comes back on. Bunji. The pleasure is all ours.',
]


def paragraph() -> str:
    x = fx + 1.0 * U
    y = fy + 6.25 * U
    size = 0.22 * U
    lead = 0.325 * U
    out = [f'<text x="{x:.1f}" y="{y:.1f}" font-family="Old Standard TT" font-weight="700" font-size="{size * 1.12:.1f}" fill="{INK}">No.</text>']
    for i, line in enumerate(COPY):
        out.append(
            f'<text x="{x:.1f}" y="{y + (i + 1) * lead + 0.06 * U:.1f}" font-family="Old Standard TT" font-size="{size:.1f}" fill="{INK}">{line}</text>'
        )
    return ''.join(out)


def front() -> str:
    body = (
        f'<rect width="{W:.0f}" height="{H:.0f}" fill="#ffffff"/>'
        + frame()
        + lettering()
        + paragraph()
        + figure(fx + 6.1 * U, fy + 4.17 * U, 7.0 * U, uid='boxer')
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
