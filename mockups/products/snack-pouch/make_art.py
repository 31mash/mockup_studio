"""Namkeen pouch artwork, laid out on the flat film panel (1 unit = 0.1 mm).

- front.png: the white ink of the front (alpha = ink; the rest is clear film):
  the story of the namkeen maker, set line for line as printed.
- back.png: the white ink of the back, drawn as seen from behind.
- seals.png: the heat seals (side and top seals, the gusset's curved corner
  seals, the zip band) as a mask: alpha = how milky the film is there, with
  the fine ribbing the sealing jaws press into it. Used by film.sheet().

Run:

    python3 products/snack-pouch/make_art.py && node tools/raster.mjs products/snack-pouch/art
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

from brand.indigo import FONT, plane_svg, veg_mark  # noqa: E402

import dims  # noqa: E402

U = 100  # units per cm
W, H = dims.W * U, dims.H * U
ART = os.path.join(HERE, 'art')
os.makedirs(ART, exist_ok=True)

# The copy on the front, line for line as printed on the pouch (the photo's
# words; the few it hides are filled in to match what shows).
LINES = [
    'Omprakash Vaishnav has been',
    'dedicated to Namkeen for 30 years.',
    'And it doesn’t stop there. His father',
    'started making it in 1962 and it’s',
    'been running ever since. Omprakash',
    'doesn’t want to make anything else.',
    'He doesn’t want to expand into other',
    'snack varieties. Omprakash wants to',
    'focus and continue to focus on the',
    'very Namkeen you are holding. By the',
    'way, it’s quite simple for Omprakash.',
    'Use the best ingredients, no colours',
    'and artificial preservatives. Just pure',
    'natural ingredients and pure oil.',
    'Made in a small village in Jodhpur,',
    'this is quite possibly the best Namkeen',
    'ever in the sky.',
]
# Measured on the photo: capitals 0.32 cm tall (Comfortaa's are 0.79 em), a
# 0.595 cm line pitch, a 8.1 cm measure starting 2.2 cm from the left edge
# (the longest line, 20.25 em, sets it with a little word spacing to spare),
# capitals of the first line 3.6 cm below the top edge.
TEXT_SIZE = 0.395 * U
TEXT_PITCH = 0.595 * U
TEXT_LEFT = 2.2 * U
TEXT_WIDTH = 8.1 * U
TEXT_CAP_TOP = 3.6 * U


def page(inner_svg: str, html_body: str = '', width: int = 4096) -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
#art {{ position: relative; overflow: hidden; background: transparent; }}
#art svg {{ position: absolute; left: 0; top: 0; }}
.story {{ position: absolute; font-family: '{FONT}'; font-weight: 600; color: #ffffff;
         font-size: {TEXT_SIZE:.1f}px; line-height: {TEXT_PITCH:.1f}px; }}
.story div {{ white-space: nowrap; text-align: justify; text-align-last: justify; }}
.story div.last {{ text-align-last: left; }}
.small {{ position: absolute; font-family: '{FONT}'; font-weight: 700; color: #ffffff;
         text-align: center; width: 100%; left: 0; }}
</style></head>
<body><div id="art" data-width="{width}" style="width:{W:.0f}px;height:{H:.0f}px">
<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">{inner_svg}</svg>
{html_body}
</div></body></html>
"""


def seals_svg() -> str:
    """The heat seals as a mask. Solid milky bands with fine ribs across them
    (pressed by the serrated sealing jaws), a crisper line where each seal
    ends, the gusset's curved corner seals and a faint zip band."""
    s = dims.SEAL * U
    top = dims.TOP_SEAL * U
    bot = dims.BOTTOM_SEAL * U
    zc = dims.ZIP * U
    zg = dims.ZIP_GAP * U
    gc = dims.GUSSET_CURVE * U
    gx = 3.3 * U  # where the gusset curve meets the bottom seal
    pitch = 0.1 * U  # 1 mm ribs

    def gusset(sign):
        x0 = 0 if sign > 0 else W
        xs = x0 + sign * s
        return (f'M{xs:.1f},{H - gc:.1f} C{xs + sign * 0.2 * U:.1f},{H - gc * 0.38:.1f} '
                f'{x0 + sign * gx * 0.55:.1f},{H - bot * 1.05:.1f} {x0 + sign * gx:.1f},{H - bot:.1f} '
                f'L{x0:.1f},{H - bot:.1f} L{x0:.1f},{H - gc:.1f} Z')

    area = (
        f'<rect x="0" y="0" width="{s}" height="{H}"/>'
        f'<rect x="{W - s}" y="0" width="{s}" height="{H}"/>'
        f'<rect x="0" y="0" width="{W}" height="{top}"/>'
        f'<rect x="0" y="{H - bot}" width="{W}" height="{bot}"/>'
        f'<path d="{gusset(1)}"/><path d="{gusset(-1)}"/>'
    )
    defs = (
        '<defs>'
        f'<pattern id="ribs-v" width="{pitch}" height="{pitch}" patternUnits="userSpaceOnUse">'
        f'<rect x="0" y="0" width="{pitch * 0.45:.1f}" height="{pitch}" fill="#fff" fill-opacity="0.35"/></pattern>'
        f'<pattern id="ribs-h" width="{pitch}" height="{pitch}" patternUnits="userSpaceOnUse">'
        f'<rect x="0" y="0" width="{pitch}" height="{pitch * 0.45:.1f}" fill="#fff" fill-opacity="0.35"/></pattern>'
        f'<clipPath id="seal-area">{area}</clipPath>'
        '</defs>'
    )
    # Opaque shapes in a faded group: where seals overlap (the corners) they
    # are not doubled up.
    parts = [defs, f'<g fill="#fff" opacity="0.62">{area}</g>']
    # Ribs run across each seal: horizontal on the side seals, vertical on
    # the top and bottom seals.
    parts.append(f'<g clip-path="url(#seal-area)">'
                 f'<rect x="0" y="{top}" width="{s}" height="{H - top - bot}" fill="url(#ribs-h)"/>'
                 f'<rect x="{W - s}" y="{top}" width="{s}" height="{H - top - bot}" fill="url(#ribs-h)"/>'
                 f'<rect x="0" y="0" width="{W}" height="{top}" fill="url(#ribs-v)"/>'
                 f'<rect x="0" y="{H - bot}" width="{W}" height="{bot}" fill="url(#ribs-v)"/>'
                 '</g>')
    # Where the seal ends, the film is pinched: a crisp line.
    edge = 0.035 * U
    parts.append(
        f'<g fill="#fff" fill-opacity="0.9">'
        f'<rect x="{s - edge}" y="{top}" width="{edge}" height="{H - top - gc + 5}"/>'
        f'<rect x="{W - s}" y="{top}" width="{edge}" height="{H - top - gc + 5}"/>'
        f'<rect x="{s - edge}" y="{top - edge}" width="{W - 2 * s + 2 * edge}" height="{edge}"/>'
        '</g>'
    )
    parts.append(f'<path d="{gusset(1)}" fill="none" stroke="#fff" stroke-opacity="0.9" stroke-width="{edge}"/>')
    parts.append(f'<path d="{gusset(-1)}" fill="none" stroke="#fff" stroke-opacity="0.9" stroke-width="{edge}"/>')
    # The zip: the film is welded to the two profiles; faintly milky between them.
    parts.append(f'<rect x="{s}" y="{zc - zg / 2 - 0.06 * U}" width="{W - 2 * s}" height="{zg + 0.12 * U}" fill="#fff" fill-opacity="0.22"/>')
    return ''.join(parts)


def story_html() -> str:
    # Place the block so the first line's capitals start at TEXT_CAP_TOP: in
    # a line box of TEXT_PITCH, Comfortaa's cap top sits `offset` below the
    # top of the box (measured on the rasterized artwork).
    offset = (TEXT_PITCH - 1.115 * TEXT_SIZE) / 2 + 0.09 * TEXT_SIZE
    top = TEXT_CAP_TOP - offset
    rows = ''.join(
        f'<div class="{"last" if i == len(LINES) - 1 else ""}">{line}</div>' for i, line in enumerate(LINES)
    )
    return f'<div class="story" style="left:{TEXT_LEFT:.0f}px;top:{top:.1f}px;width:{TEXT_WIDTH:.0f}px">{rows}</div>'


# Front: the story in white ink.
open(os.path.join(ART, 'front.html'), 'w').write(page('', story_html()))

# Back (drawn as seen from behind): the plane mark, the name, the veg mark and
# a few small lines, low on the panel where the namkeen is behind them.
cx = W / 2
back_svg = plane_svg(cx, 9.3 * U, 1.7 * U, color='#ffffff') + veg_mark(cx - 0.3 * U, 12.35 * U, 0.6 * U)
back_text = (
    f'<div class="small" style="top:{10.45 * U:.0f}px;font-size:{0.62 * U:.0f}px;letter-spacing:-1px">Namkeen</div>'
    f'<div class="small" style="top:{11.3 * U:.0f}px;font-size:{0.25 * U:.0f}px;line-height:{0.38 * U:.0f}px;font-weight:600">'
    'Handmade in Jodhpur for IndiGo<br>Gram flour, vegetable oil, salt and spices</div>'
    f'<div class="small" style="top:{13.25 * U:.0f}px;font-size:{0.22 * U:.0f}px;font-weight:600">Net wt. 60 g</div>'
)
open(os.path.join(ART, 'back.html'), 'w').write(page(back_svg, back_text))

# The seal mask, at the panel's size.
open(os.path.join(ART, 'seals.svg'), 'w').write(
    f'<svg xmlns="http://www.w3.org/2000/svg" data-width="4096" width="{W:.0f}" height="{H:.0f}" '
    f'viewBox="0 0 {W:.0f} {H:.0f}">{seals_svg()}</svg>'
)
print('art written')
