"""Smoked Almonds: IndiGo's shallow round slip-lid tin in deep matte black.
The lid top carries a pile of almonds in metallic bronze line art with the
title knocked out across it; a bare silver bead shows at the lid line and a
rolled seam at the foot."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402

TITLE = 'Smoked Almonds tin'
SHOTS = [
    'hero',
    'hero-right',
    'front',
    # The angle of the photo in the spread: straight on, a little above.
    {'name': 'spread-angle', 'preset': 'hero', 'azimuth': 0, 'elevation': 31, 'lens': 100, 'fill': 0.56},
    'top',
    'high',
    'low',
]

BLACK = '#141519'  # the print black of the artwork


def lid_top_material(ctx):
    """Print black under a satin lacquer, with the bronze ink metallic: the
    ink mask (lid-ink.png, white where the bronze prints) turns metallic on
    and roughness down under the ink only."""
    m = ctx.mat
    mat = m.printed_metal('lid top', art=ctx.art('lid-top.png'), roughness=0.42, coat=0.12)
    nt = mat.node_tree
    p = nt.nodes['Principled BSDF']
    mask = nt.nodes.new('ShaderNodeTexImage')
    mask.image = m.image(ctx.art('lid-ink.png'), alpha=False, colorspace='Non-Color')
    mask.interpolation = 'Cubic'
    mask.extension = 'EXTEND'
    nt.links.new(mask.outputs['Color'], p.inputs['Metallic'])
    rough = nt.nodes.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value = 0.42
    rough.inputs['To Max'].default_value = 0.3
    nt.links.new(mask.outputs['Color'], rough.inputs['Value'])
    nt.links.new(rough.outputs['Result'], p.inputs['Roughness'])
    return mat


def build(ctx):
    m, s = ctx.mat, ctx.shapes
    R = dims.R
    black = m.printed_metal('black', color=BLACK, roughness=0.42, coat=0.12)
    top = lid_top_material(ctx)
    silver = m.bare_metal()

    lid_z0 = dims.BODY_H + dims.LID_GAP
    lid = s.walled_shell(
        'lid',
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
    lip = s.torus_ring('lid-lip', s.circle(R - 0.05, 192), lid_z0 + 0.05, 0.06, black)
    # Body: its top half is hidden in the lid; its foot sits in the seam.
    body = s.walled_shell(
        'body',
        s.circle(dims.BODY_R, 192),
        dims.SEAM_H * 0.5,
        dims.HEIGHT - 0.3,
        mats=(black, black, black, None),
    )
    # The silver bead the lid rests on, and the rolled bottom seam.
    bead = s.torus_ring('bead', s.circle(dims.BODY_R + 0.02, 192), dims.BODY_H, dims.BEAD_TUBE, silver, seg=12)
    seam = s.walled_shell(
        'seam',
        s.circle(dims.BODY_R + dims.SEAM_PROUD, 192),
        0.0,
        dims.SEAM_H,
        top_radius=0.1,
        bottom_radius=0.08,
        edge_seg=6,
        mats=(black, black, black, None),
    )
    return [lid, lip, body, bead, seam]
