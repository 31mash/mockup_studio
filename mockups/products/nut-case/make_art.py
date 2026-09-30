"""Nut Case artwork, laid out on the tin's real dimensions (1 unit = 0.1 mm).
Run: python3 products/nut-case/make_art.py && node tools/raster.mjs products/nut-case/art"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

from brand.indigo import FONT, INDIGO_BLUE, INDIGO_GREEN, plane_svg, svg, veg_mark  # noqa: E402
from studio.layout import wrap_layout  # noqa: E402

import dims  # noqa: E402

U = 100  # units per cm
W, D = dims.W * U, dims.D * U

# Lid top: green rim (it also wraps over the rounded edge) around a blue panel.
rim = dims.RIM * U
panel_r = dims.PANEL_R * U
top = (
    f'<rect width="{W}" height="{D}" fill="{INDIGO_GREEN}"/>'
    f'<rect x="{rim}" y="{rim}" width="{W - 2 * rim}" height="{D - 2 * rim}" rx="{panel_r}" fill="{INDIGO_BLUE}"/>'
    f'<text x="{W * 0.215}" y="{D * 0.47}" font-family="{FONT}" font-weight="700" font-size="{0.95 * U}" fill="{INDIGO_GREEN}" letter-spacing="-2">Nut Case</text>'
    + plane_svg(W * 0.775, D * 0.29, 1.55 * U)
    + veg_mark(W * 0.265, D * 0.645, 0.62 * U)
)
open(os.path.join(HERE, 'art', 'lid-top.svg'), 'w').write(svg(W, D, top))

# Body wall: wrap strip starting at the front face's left end.
bw, bd, br = dims.body_outline()
lay = wrap_layout(bw, bd, br)
L = lay['length'] * U
H = (dims.BODY_H - dims.BODY_EDGE) * U


def centre(face):
    u0, u1 = lay[face]
    return (u0 + u1) / 2 * L, (u1 - u0) * L


fx, fw = centre('front')
lx, lw = centre('left')
body = (
    f'<rect width="{L}" height="{H}" fill="{INDIGO_BLUE}"/>'
    f'<text x="{fx}" y="{H * 0.66}" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="{1.05 * U}" fill="{INDIGO_GREEN}" letter-spacing="-3">IndiGo</text>'
    f'<text x="{lx}" y="{H * 0.47}" text-anchor="middle" font-family="{FONT}" font-weight="500" font-size="{0.3 * U}" fill="{INDIGO_GREEN}" letter-spacing="-0.5">Over 200 million passengers are nuts about IndiGo.</text>'
)
open(os.path.join(HERE, 'art', 'body-side.svg'), 'w').write(svg(L, H, body, px=12288))
print('art written')
