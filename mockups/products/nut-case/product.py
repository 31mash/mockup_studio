"""Nut Case: IndiGo's slip-lid nut tin. Calibration product for the studio:
its hero shot is matched against source/nut-case-reference.jpg."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402

TITLE = 'Nut Case tin'
SHOTS = ['hero', 'hero-right', 'front', 'side', 'back', 'top', 'low']


def build(ctx):
    m, s = ctx.mat, ctx.shapes
    green = m.printed_metal('green lid', color='#9fcc3b')
    top = m.printed_metal('lid top', art=ctx.art('lid-top.png'))
    body = m.printed_metal('body', art=ctx.art('body-side.png'))
    blue = m.printed_metal('blue', color='#3d4399')
    outline = s.rounded_rect(dims.W, dims.D, dims.CORNER, seg=12)
    lid, bod, bead, lip = s.slip_lid_tin(
        'nut-case',
        outline,
        body_h=dims.BODY_H,
        lid_h=dims.LID_H,
        lid_edge=dims.LID_EDGE,
        body_edge=dims.BODY_EDGE,
        wall=dims.WALL,
        mats={'lid_top': top, 'lid_side': green, 'lid_edge': top, 'body_side': body, 'bottom': blue, 'bead': m.bare_metal()},
        top_extent=(dims.W, dims.D),
    )
    return [lid, bod, bead, lip]
