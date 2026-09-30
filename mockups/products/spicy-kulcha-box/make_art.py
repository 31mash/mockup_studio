"""Spicy Kulcha artwork, laid out on the pack's real dimensions (1 unit = 0.1 mm).
Run: python3 products/spicy-kulcha-box/make_art.py && node tools/raster.mjs products/spicy-kulcha-box/art

Files:
  top-red.svg, top-green.svg   sleeve top: white card with the vintage matchbox
                               label, portrait, 'SPICY' at the top (the -x end)
  side.svg                     sleeve long side: brown striker panel on white card
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

from brand.indigo import FONT, INDIGO_BLUE, plane_svg, svg  # noqa: E402

import dims  # noqa: E402
from portrait import portrait  # noqa: E402

U = 100
ART = os.path.join(HERE, 'art')
os.makedirs(ART, exist_ok=True)

CARD = '#f4f2eb'  # the sleeve's white board
PAPER = '#fbf8ef'  # white ink panels on the label
NAVY = '#27213f'  # keylines and 'KULCHA'
YELLOW = '#f2c224'
INK = '#3d3419'  # small print on the yellow

COLOURWAYS = {
    'red': dict(frame='#b8242c', ring='#8e1b22', oval='#3d4399'),
    'green': dict(frame='#72a03a', ring='#4c7a26', oval='#f6d65a'),
}


def label(cw):
    """The printed label, portrait, origin at its top-left corner."""
    lw, lh = dims.LABEL_W * U, dims.LABEL_H * U
    c = COLOURWAYS[cw]
    ins = 42  # yellow field and white panel inset from the label edge
    arch_side, arch_peak = 0.268 * lh, 0.198 * lh
    yel_bot = 0.806 * lh
    pan_top, pan_bot = yel_bot + 22, lh - ins
    out = [
        f'<rect width="{lw}" height="{lh}" fill="{c["frame"]}"/>',
        # fine keyline just inside the edge
        f'<rect x="14" y="14" width="{lw - 28}" height="{lh - 28}" fill="none" stroke="{NAVY}" stroke-width="3.5"/>',
    ]
    # yellow field with an arched top
    ctrl = 2 * arch_peak - arch_side
    out.append(
        f'<path d="M{ins},{yel_bot} L{ins},{arch_side} Q{lw / 2},{ctrl} {lw - ins},{arch_side} L{lw - ins},{yel_bot} Z" fill="{YELLOW}"/>'
    )
    # SPICY: white slab capitals on the colour band
    out.append(
        f'<text x="{lw / 2}" y="{0.178 * lh}" text-anchor="middle" font-family="Alfa Slab One" font-size="{1.72 * U}" '
        f'fill="{PAPER}" textLength="{lw - 2 * 62}" lengthAdjust="spacingAndGlyphs" '
        f'transform="translate(0,{0.178 * lh}) scale(1,1.12) translate(0,{-0.178 * lh})">SPICY</text>'
    )
    # white KULCHA panel with a navy keyline
    out.append(f'<rect x="{ins}" y="{pan_top}" width="{lw - 2 * ins}" height="{pan_bot - pan_top}" fill="{PAPER}"/>')
    out.append(
        f'<rect x="{ins + 9}" y="{pan_top + 9}" width="{lw - 2 * ins - 18}" height="{pan_bot - pan_top - 18}" fill="none" stroke="{NAVY}" stroke-width="3.5"/>'
    )
    kb = pan_top + (pan_bot - pan_top) * 0.8
    out.append(
        f'<text x="{lw / 2}" y="{kb}" text-anchor="middle" font-family="Archivo Black" font-size="{1.5 * U}" '
        f'fill="{NAVY}" textLength="{lw - 2 * ins - 70}" lengthAdjust="spacingAndGlyphs">KULCHA</text>'
    )
    # the portrait in its ringed oval
    ox, oy = lw / 2, 0.487 * lh
    rx, ry = 0.372 * lw, 0.246 * lh
    out.append(f'<ellipse cx="{ox}" cy="{oy}" rx="{rx + 13}" ry="{ry + 13}" fill="{NAVY}"/>')
    out.append(f'<ellipse cx="{ox}" cy="{oy}" rx="{rx + 10}" ry="{ry + 10}" fill="{YELLOW}"/>')
    out.append(f'<ellipse cx="{ox}" cy="{oy}" rx="{rx + 3}" ry="{ry + 3}" fill="{c["ring"]}"/>')
    out.append(f'<ellipse cx="{ox}" cy="{oy}" rx="{rx - 9}" ry="{ry - 9}" fill="{NAVY}"/>')
    out.append(f'<clipPath id="oval-{cw}"><ellipse cx="0" cy="0" rx="{rx - 12}" ry="{ry - 12}"/></clipPath>')
    out.append(
        f'<g transform="translate({ox},{oy})"><g clip-path="url(#oval-{cw})">'
        + portrait(rx - 12, ry - 12, c['oval'], cw)
        + '</g></g>'
    )
    # the round 6E emblem, overlapping the oval's lower left
    out.append(emblem(0.248 * lw, 0.722 * lh, 0.148 * lw, cw))
    # the IndiGo plane and a line of small print
    out.append(plane_svg(0.835 * lw, 0.742 * lh, 1.05 * U, color=INK, dot=0.3, rotate=0))
    out.append(
        f'<text transform="translate({0.935 * lw},{0.60 * lh}) rotate(-90)" text-anchor="middle" font-family="{FONT}" '
        f'font-weight="700" font-size="{0.2 * U}" letter-spacing="1.5" fill="{INK}">IndiGo · 6E</text>'
    )
    return ''.join(out)


def emblem(cx, cy, r, cw):
    """A round seal: IndiGo blue ring with lettering, white centre, '6E'."""
    rt = r * 0.79  # text baseline radius
    top = f'M{cx - rt},{cy} A{rt},{rt} 0 0 1 {cx + rt},{cy}'
    rb = r * 0.79 + 13
    bot = f'M{cx - rb},{cy} A{rb},{rb} 0 0 0 {cx + rb},{cy}'
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r + 5}" fill="{NAVY}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r + 1}" fill="{PAPER}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r - 5}" fill="{INDIGO_BLUE}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r * 0.62}" fill="{PAPER}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r * 0.62 - 7}" fill="none" stroke="{INDIGO_BLUE}" stroke-width="2.5"/>'
        f'<path id="em-top-{cw}" d="{top}" fill="none"/><path id="em-bot-{cw}" d="{bot}" fill="none"/>'
        f'<text font-family="{FONT}" font-weight="700" font-size="{r * 0.21}" letter-spacing="3" fill="{PAPER}">'
        f'<textPath href="#em-top-{cw}" startOffset="50%" text-anchor="middle">INDIGO</textPath></text>'
        f'<text font-family="{FONT}" font-weight="700" font-size="{r * 0.17}" letter-spacing="2.5" fill="{PAPER}">'
        f'<textPath href="#em-bot-{cw}" startOffset="50%" text-anchor="middle">SINCE 2006</textPath></text>'
        f'<circle cx="{cx - r * 0.79}" cy="{cy + 4}" r="4" fill="{PAPER}"/><circle cx="{cx + r * 0.79}" cy="{cy + 4}" r="4" fill="{PAPER}"/>'
        f'<text x="{cx}" y="{cy + r * 0.24}" text-anchor="middle" font-family="Alfa Slab One" font-size="{r * 0.72}" fill="{INDIGO_BLUE}">6E</text>'
    )


def top(cw):
    """Sleeve top seen from above, portrait: image top = the sleeve's -x end,
    image left = the front (-y) side. The card margin frames the label."""
    w, h = dims.W * U, dims.L * U
    m = dims.MARGIN * U
    body = f'<rect width="{w}" height="{h}" fill="{CARD}"/>' f'<g transform="translate({m},{m})">{label(cw)}</g>'
    return svg(w, h, body, px=4096)


def side():
    """A long side of the sleeve, seen from outside: the striker panel."""
    w, h = dims.L * U, dims.H * U
    sx, sz = dims.STRIKER_X * U, dims.STRIKER_Z * U
    pw, ph = w - 2 * sx, h - 2 * sz
    defs = (
        '<defs>'
        '<pattern id="knurl" patternUnits="userSpaceOnUse" width="9" height="9" patternTransform="rotate(45)">'
        '<rect width="9" height="9" fill="#8b6f66"/>'
        '<rect width="9" height="2.2" fill="#6c524b"/><rect width="2.2" height="9" fill="#6c524b"/>'
        '<rect x="4" y="4" width="2.4" height="2.4" fill="#9c8177"/>'
        '</pattern>'
        '<filter id="grit" x="0" y="0" width="1" height="1">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.35" numOctaves="2" seed="7" result="n"/>'
        '<feColorMatrix in="n" type="matrix" values="0 0 0 0 0.25  0 0 0 0 0.17  0 0 0 0 0.14  0 0 0 0.55 -0.12"/>'
        '<feComposite in2="SourceGraphic" operator="in"/>'
        '</filter>'
        '</defs>'
    )
    body = (
        defs
        + f'<rect width="{w}" height="{h}" fill="{CARD}"/>'
        + f'<rect x="{sx}" y="{sz}" width="{pw}" height="{ph}" fill="url(#knurl)"/>'
        + f'<rect x="{sx}" y="{sz}" width="{pw}" height="{ph}" fill="#000" filter="url(#grit)"/>'
    )
    return svg(w, h, body, px=6144)


def write(name, text):
    open(os.path.join(ART, name), 'w').write(text)


if __name__ == '__main__':
    for cw in COLOURWAYS:
        write(f'top-{cw}.svg', top(cw))
    write('side.svg', side())
    # a stand-alone proof of the portrait, for checking the drawing
    rx, ry = dims.LABEL_W * U * 0.372 - 12, dims.LABEL_H * U * 0.246 - 12
    write(
        '_portrait-proof.svg',
        svg(2 * rx, 2 * ry, f'<g transform="translate({rx},{ry})">{portrait(rx, ry, COLOURWAYS["red"]["oval"], "proof")}</g>', px=1600),
    )
    print('art written')
