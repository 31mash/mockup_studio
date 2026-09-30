"""Smoked Almonds: IndiGo's shallow round slip-lid tin in deep matte black.
The lid top carries a pile of almonds in metallic bronze line art with the
title knocked out across it; a bare silver bead shows at the lid line and a
rolled seam at the foot."""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402

TITLE = 'Smoked Almonds tin'
SHOTS = [
    'hero',
    'hero-right',
    'front',
    # The angle of the photo in the spread: straight on, a little above.
    {'name': 'spread-angle', 'preset': 'hero', 'azimuth': 0, 'elevation': 36, 'lens': 100, 'fill': 0.56},
    'top',
    'high',
    'low',
    # Two tins stacked, as on a shelf.
    {'name': 'stack', 'preset': 'hero', 'elevation': 26, 'variant': 'stack', 'fill': 0.5},
]
VARIANTS = [None, 'stack']


@bpy.app.handlers.persistent
def _forget_light_target(*_):
    """studio.core caches its light-target empty in core._ORIGIN. core.reset()
    frees that object, so when render.py rebuilds the scene for a second
    variant, core.studio() trips over the stale reference (ReferenceError).
    Clearing the cache right after each reset fixes it without touching the
    studio; drop this once core.reset() does it itself."""
    from studio import core

    core._ORIGIN = None


for _h in (bpy.app.handlers.load_factory_startup_post, bpy.app.handlers.load_post):
    if not any(getattr(f, '__name__', '') == '_forget_light_target' for f in _h):
        _h.append(_forget_light_target)

BLACK = '#0e1015'  # the print black of the artwork (make_art.BLACK)
SATIN = dict(roughness=0.5, coat=0.05)  # deep matte black: a low-sheen lacquer


def lid_top_material(ctx):
    """Print black under a satin lacquer, with the bronze ink metallic: the
    ink mask (lid-ink.png, white where the bronze prints) turns metallic on
    and roughness down under the ink only."""
    m = ctx.mat
    mat = m.printed_metal('lid top', art=ctx.art('lid-top.png'), **SATIN)
    nt = mat.node_tree
    p = nt.nodes['Principled BSDF']
    p.inputs['Specular IOR Level'].default_value = 0.12
    mask = nt.nodes.new('ShaderNodeTexImage')
    mask.image = m.image(ctx.art('lid-ink.png'), alpha=False, colorspace='Non-Color')
    mask.interpolation = 'Cubic'
    mask.extension = 'EXTEND'
    nt.links.new(mask.outputs['Color'], p.inputs['Metallic'])
    rough = nt.nodes.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value = SATIN['roughness']
    rough.inputs['To Max'].default_value = 0.28
    nt.links.new(mask.outputs['Color'], rough.inputs['Value'])
    nt.links.new(rough.outputs['Result'], p.inputs['Roughness'])
    return mat


def tin(ctx, mats, name):
    """One closed tin standing on z = 0, front to -Y. Returns its parts."""
    s = ctx.shapes
    black, top, silver = mats
    R = dims.R
    lid_z0 = dims.BODY_H + dims.LID_GAP
    lid = s.walled_shell(
        f'{name}-lid',
        s.circle(R, 192),
        lid_z0,
        dims.HEIGHT,
        top_radius=dims.LID_EDGE,
        edge_seg=8,
        mats=(black, top, None, top),
        top_extent=(2 * R, 2 * R),
        cap_bottom=False,
    )
    # The lid's open edge is curled inwards.
    lip = s.torus_ring(f'{name}-lid-lip', s.circle(R - 0.05, 192), lid_z0 + 0.05, 0.06, black)
    # Body: its top half is hidden in the lid; its foot sits in the seam.
    body = s.walled_shell(
        f'{name}-body',
        s.circle(dims.BODY_R, 192),
        dims.SEAM_H * 0.5,
        dims.HEIGHT - 0.3,
        mats=(black, black, black, None),
    )
    # The silver bead the lid rests on, and the rolled bottom seam.
    bead = s.torus_ring(f'{name}-bead', s.circle(dims.BODY_R + 0.02, 192), dims.BODY_H, dims.BEAD_TUBE, silver, seg=12)
    seam = s.walled_shell(
        f'{name}-seam',
        s.circle(dims.BODY_R + dims.SEAM_PROUD, 192),
        0.0,
        dims.SEAM_H,
        top_radius=0.1,
        bottom_radius=0.08,
        edge_seg=6,
        mats=(black, black, black, None),
    )
    return [lid, lip, body, bead, seam]


def build(ctx, variant=None):
    m = ctx.mat
    black = m.printed_metal('black', color=BLACK, **SATIN)
    black.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.12
    mats = (black, lid_top_material(ctx), m.bare_metal())
    objs = tin(ctx, mats, 'tin')
    if variant == 'stack':
        # A second tin resting on the first, its seam on the lid top, set
        # down a little off-centre and turned, as a hand would stack them.
        upper = tin(ctx, mats, 'tin-2')
        for o in upper:
            o.location = (0.12, 0.08, dims.HEIGHT + 0.002)
            o.rotation_euler = (0.0, 0.0, math.radians(-38))
        objs += upper
        bpy.context.view_layer.update()
    return objs
