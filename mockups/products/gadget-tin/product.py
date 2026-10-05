"""Gadget tin: IndiGo's second reusable tin, a sky-blue slip-lid tin printed
all over with white silhouettes of small everyday gadgets.

Construction: the lid's rolled bottom edge (bare tinplate, the silver line in
the photo) stands proud of the body by dims.OVERHANG all round; the body wall
runs on up inside the lid."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402

TITLE = 'Gadget tin'
SHOTS = ['hero', 'hero-right', 'front', 'side', 'back', 'top']


def _materials(ctx):
    m = ctx.mat
    return {
        'top': m.printed_metal('lid top', art=ctx.art('lid-top.png')),
        'body': m.printed_metal('body', art=ctx.art('body-side.png')),
        'blue': m.printed_metal('blue', color=dims.BLUE),
        'tin': m.bare_metal(),
    }


def _body(s, mt, outline, top_z):
    """The printed body wall from the floor to top_z. The wrap art covers the
    wall up to the lid line (BODY_H); above it, hidden under the lid, the
    strip's plain blue top row carries on up the neck."""
    body_outline = s.inset(outline, dims.OVERHANG)
    return s.walled_shell(
        'gadget-tin-body',
        body_outline,
        0.0,
        top_z,
        bottom_radius=dims.BODY_EDGE,
        mats=(mt['body'], mt['body'], mt['blue'], None),
        side_v=(0.0, (top_z - dims.BODY_EDGE) / (dims.BODY_H - dims.BODY_EDGE)),
        top_extent=(dims.W, dims.D),
    )


def _lid(s, mt, outline, z0):
    """The lid shell from its bottom edge (z0) to its top, and the roll below it."""
    top = z0 + dims.LID_H - dims.LID_GAP
    lid = s.walled_shell(
        'gadget-tin-lid',
        outline,
        z0,
        top,
        top_radius=dims.LID_EDGE,
        mats=(mt['blue'], mt['top'], None, mt['top']),
        top_extent=(dims.W, dims.D),
        cap_bottom=False,
    )
    # The roll hangs just below the lid wall, a little proud of it, and hides
    # the wall's cut edge: the silver line of the photo.
    lip = s.torus_ring('gadget-tin-lid-lip', s.inset(outline, dims.LIP_R - 0.03), z0 - dims.LIP_R * 0.3, dims.LIP_R, mt['tin'])
    return [lid, lip]


def build(ctx):
    s = ctx.shapes
    mt = _materials(ctx)
    outline = s.rounded_rect(dims.W, dims.D, dims.CORNER, seg=14)
    # The body runs up inside the lid, well short of its top.
    body = _body(s, mt, outline, dims.BODY_H + dims.LID_H * 0.6)
    return [body] + _lid(s, mt, outline, dims.BODY_H + dims.LID_GAP)
