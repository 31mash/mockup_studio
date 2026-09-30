"""Gadget tin: IndiGo's second reusable tin, a sky-blue slip-lid tin printed
all over with white silhouettes of small everyday gadgets."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402

TITLE = 'Gadget tin'
SHOTS = ['hero', 'hero-right', 'front', 'side', 'back', 'top']


def build(ctx, variant=None):
    m, s = ctx.mat, ctx.shapes
    top = m.printed_metal('lid top', art=ctx.art('lid-top.png'))
    body = m.printed_metal('body', art=ctx.art('body-side.png'))
    blue = m.printed_metal('blue', color=dims.BLUE)
    tin = m.bare_metal()
    outline = s.rounded_rect(dims.W, dims.D, dims.CORNER, seg=14)
    lid, bod, bead, lip = s.slip_lid_tin(
        'gadget-tin',
        outline,
        body_h=dims.BODY_H,
        lid_h=dims.LID_H,
        lid_edge=dims.LID_EDGE,
        body_edge=dims.BODY_EDGE,
        wall=dims.WALL,
        mats={'lid_top': top, 'lid_side': blue, 'lid_edge': top, 'body_side': body, 'bottom': blue, 'bead': tin},
        top_extent=(dims.W, dims.D),
    )
    # The lid's rolled edge shows bare tinplate, as in the photo.
    lip.data.materials[0] = tin
    return [lid, bod, bead, lip]
