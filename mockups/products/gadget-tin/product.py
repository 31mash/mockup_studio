"""Gadget tin: IndiGo's second reusable tin, a sky-blue slip-lid tin printed
all over with white silhouettes of small everyday gadgets.

Variants: None (closed, as in the photo) and 'open' (the lid set down beside
the empty tin, showing its bare tinplate inside and rolled rim).

Construction: the lid's rolled bottom edge (bare tinplate, the silver line in
the photo) stands proud of the body by dims.OVERHANG all round; the body wall
runs on up inside the lid."""

import math
import os
import sys

from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402

TITLE = 'Gadget tin'
VARIANTS = [None, 'open']
SHOTS = [
    'hero',
    'hero-right',
    'front',
    'side',
    'back',
    'top',
    {'name': 'open', 'preset': 'hero', 'variant': 'open', 'azimuth': 24, 'elevation': 44, 'fill': 0.66},
]

SHEET = 0.05  # tinplate thickness, as far as the eye can tell


def _materials(ctx):
    m = ctx.mat
    return {
        'top': m.printed_metal('lid top', art=ctx.art('lid-top.png')),
        'body': m.printed_metal('body', art=ctx.art('body-side.png')),
        'blue': m.printed_metal('blue', color=dims.BLUE),
        'tin': m.bare_metal(),
        'inside': m.bare_metal('tin inside', color='#d3d4d6', roughness=0.3),
    }


def _guard_variant_rebuild(core):
    """render.py rebuilds the scene with core.reset() when the variant changes,
    but core._ORIGIN still points at the deleted light-target empty, so
    core.studio() raises ReferenceError. Clear it after each reset (a runtime
    wrapper only; reported as a shared fix, harmless once studio/core.py does it)."""
    if getattr(core.reset, 'clears_origin', False):
        return
    reset = core.reset

    def reset_and_clear():
        reset()
        core._ORIGIN = None

    reset_and_clear.clears_origin = True
    core.reset = reset_and_clear


def _body(s, mt, outline, top_z, open_top=False):
    """The printed body wall from the floor to top_z. The wrap art covers the
    wall up to the lid line (BODY_H); above it the strip's plain blue top row
    carries on up the neck."""
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
        cap_top=not open_top,
    )


def _lid(s, mt, outline, z0, inside=False):
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
    parts = [lid, lip]
    if inside:
        parts.append(
            s.walled_shell(
                'gadget-tin-lid-inside',
                s.inset(outline, SHEET),
                z0,
                top - SHEET,
                top_radius=dims.LID_EDGE - SHEET,
                mats=(mt['inside'], mt['inside'], None, mt['inside']),
                cap_bottom=False,
            )
        )
    return parts


def build(ctx, variant=None):
    _guard_variant_rebuild(ctx.core)
    s = ctx.shapes
    mt = _materials(ctx)
    outline = s.rounded_rect(dims.W, dims.D, dims.CORNER, seg=14)
    if variant == 'open':
        return _open(s, mt, outline)
    # Closed: the body runs up inside the lid, well short of its top.
    body = _body(s, mt, outline, dims.BODY_H + dims.LID_H * 0.6)
    return [body] + _lid(s, mt, outline, dims.BODY_H + dims.LID_GAP)


def _open(s, mt, outline):
    """The empty tin with its lid set down, top up, to its right."""
    body_outline = s.inset(outline, dims.OVERHANG)
    rim_z = dims.BODY_H + dims.LID_H - 0.3  # the body's rim sits just under the lid's top when closed
    outer = _body(s, mt, outline, rim_z, open_top=True)
    inner = s.walled_shell(
        'gadget-tin-inside',
        s.inset(body_outline, SHEET),
        0.14,
        rim_z,
        bottom_radius=dims.BODY_EDGE * 0.7,
        mats=(mt['inside'], mt['inside'], mt['inside'], None),
        cap_top=False,
    )
    rim = s.torus_ring('gadget-tin-rim', s.inset(body_outline, SHEET / 2), rim_z, 0.06, mt['tin'])

    # The lid, resting on its rolled edge.
    lid_parts = _lid(s, mt, outline, dims.LIP_R * 1.3, inside=True)

    # Body a little left of centre, lid to its right and slightly behind,
    # turned a touch so the pair doesn't look lined up.
    body_parts = [outer, inner, rim]
    for ob in body_parts:
        ob.data.transform(Matrix.Translation((-6.6, -1.2, 0.0)))
    place = Matrix.Translation((7.6, 2.4, 0.0)) @ Matrix.Rotation(math.radians(-12), 4, "Z")
    for ob in lid_parts:
        ob.data.transform(place)
    return body_parts + lid_parts
