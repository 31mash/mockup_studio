"""IndiGo 'Chandni Chowk to the Sky' samosa bag: a street-food newspaper bag
(lifafa) printed all over with a Hindi newspaper page and a blue rubber stamp,
lying on its back, puffed by the samosa inside, its top folded over once.
The 'with-samosa' variant sets a samosa beside it, as in the spread."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bag  # noqa: E402
import dims  # noqa: E402
import samosa  # noqa: E402

TITLE = 'Chandni Chowk samosa bag'
# The bag lies flat, so it gets a little more of the frame than a tin would,
# and 'front' and 'low' look down on it a little more than the presets.
SHOTS = [
    {'name': 'hero', 'preset': 'hero', 'fill': 0.6},
    {'name': 'hero-right', 'preset': 'hero-right', 'fill': 0.6},
    {'name': 'front', 'preset': 'front', 'elevation': 26, 'fill': 0.56},
    {'name': 'top', 'preset': 'top', 'fill': 0.6},
    {'name': 'low', 'preset': 'low', 'elevation': 15, 'fill': 0.64},
    {'name': 'samosa-hero', 'preset': 'hero', 'variant': 'with-samosa', 'fill': 0.64},
]
VARIANTS = ['bag', 'with-samosa']


def newsprint(m, name, art):
    """Uncoated newsprint: matte, with a fine fibre tooth."""
    return m.board(name, art=art, roughness=0.8, coat=0.0, tooth=0.05)


def build(ctx, variant=None):
    m = ctx.mat
    front = newsprint(m, 'bag front', ctx.art('front.png'))
    back = newsprint(m, 'bag back', ctx.art('back.png'))
    top = newsprint(m, 'bag flap', ctx.art('flap.png'))
    sh = bag.shape()
    objs = [bag.body(sh, front, back), bag.flap(sh, top)]
    if variant == 'with-samosa':
        objs.append(samosa.mesh('samosa', samosa.material(m), at=dims.SAMOSA_AT))
    return objs
