"""Cookie tin artwork, laid out on the tin's real dimensions (1 unit = 0.1 mm).
Run: python3 products/cookie-tins/make_art.py && node tools/raster.mjs products/cookie-tins/art

Per flavour:
- lid-<flavour>.svg: the lid seen from above (front edge at the bottom), over
  the full lid diameter. The white dotted plane sits in the upper half, the
  flavour name in two lines of Comfortaa below it, in a deeper shade of the
  tin colour. The ring outside the top panel stays flat tin colour: it covers
  the rounded shoulder and the skirt.
- body-<flavour>.svg: the body wrap strip, u = 0 at the front centre running
  right (counter-clockwise from above), v from the seam top to the neck top.
  One white sentence runs most of the way round; its ends meet at the back,
  where the side seam is. The seam is left unmarked: the photo shows none,
  and at the tin's edges a printed stripe reads as a texture seam.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)

from brand.indigo import FONT, plane_svg, svg  # noqa: E402

import dims  # noqa: E402

U = 100  # units per cm

# Print colours: the tins sampled from the photo's lit lid tops. The inks are
# set so that, under the studio's satin lacquer (whose sheen lifts dark inks
# by about 0.04 in linear light), the lettering renders close to the photo's
# clear mid blue (not navy) and its crimson, about (160, 45, 72).
FLAVOURS = {
    'chocolate-chip': dict(tin='#91d5ea', ink='#00569e', lines=(['Chocolate chip'], ['cookies'])),
    # The photo sets the plus tight: narrow gaps, not word spaces.
    'oatmeal-honey': dict(tin='#e27a9e', ink='#a00a3c', lines=(['Oatmeal', '+', 'Honey'], ['cookies'])),
}
PLUS_GAP = 0.13  # em, either side of the '+'
SENTENCE = 'For the first time in the history of aviation, IndiGo presents reusable cookie tins. Enjoy.'


def lid(f):
    D = 2 * dims.RL * U
    cy = dims.PLANE_CY * D
    fs = dims.LID_TEXT_SIZE * D
    def line(words, base):
        # Words after the first are tspans nudged by PLUS_GAP (one text chunk,
        # so text-anchor centres the whole line, gaps included).
        inner = words[0] + ''.join(f'<tspan dx="{PLUS_GAP * fs:.1f}">{w}</tspan>' for w in words[1:])
        return f'<text x="{D / 2:.1f}" y="{base * D:.1f}">{inner}</text>'

    l1, l2 = f['lines']
    body = (
        f'<rect width="{D:.0f}" height="{D:.0f}" fill="{f["tin"]}"/>'
        # The photo's dots are about 0.6 of their spacing across.
        + plane_svg(D / 2, cy, dims.PLANE_W * D, color='#ffffff', dot=0.29)
        # Comfortaa Bold: the photo's lid lettering is heavier than its body line.
        + f'<g font-family="{FONT}" font-weight="700" font-size="{fs:.1f}" fill="{f["ink"]}" text-anchor="middle">'
        + line(l1, dims.LID_BASE1)
        + line(l2, dims.LID_BASE2)
        + '</g>'
    )
    return svg(D, D, body, px=4096)


def body_strip(f):
    L = dims.CIRC * U
    Hs = (dims.ART_Z1 - dims.ART_Z0) * U
    fs = dims.TEXT_SIZE * U
    # Visually centre the lowercase line on TEXT_Z (Comfortaa's x-height is 0.46 em).
    base = (dims.ART_Z1 - dims.TEXT_Z) * U + 0.23 * fs

    def sentence(x):
        return (
            f'<text x="{x:.1f}" y="{base:.1f}" text-anchor="middle" font-family="{FONT}" font-weight="500" '
            f'font-size="{fs:.1f}" fill="#ffffff">{SENTENCE}</text>'
        )

    body = (
        f'<rect width="{L:.0f}" height="{Hs:.0f}" fill="{f["tin"]}"/>'
        # Centred on the front (u = 0), drawn twice so it wraps across the strip's ends.
        + sentence(0)
        + sentence(L)
    )
    return svg(L, Hs, body, px=8192)


os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
for name, f in FLAVOURS.items():
    open(os.path.join(HERE, 'art', f'lid-{name}.svg'), 'w').write(lid(f))
    open(os.path.join(HERE, 'art', f'body-{name}.svg'), 'w').write(body_strip(f))
print('art written')
