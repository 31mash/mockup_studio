"""Bunji!: IndiGo's kraft paper bag for its buns. An open SOS bag (square
bottom, side gussets) with a pinked top edge, printed on the front in two
inks: a rope-rule frame, 'Bunji!' in heavy italic sign-writing with a red
offset shadow, a vintage engraved pugilist and a short paragraph."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402
import sos_bag  # noqa: E402

TITLE = 'Bunji! paper bag'
# 'top' looks straight down into the open mouth; a little more fill keeps
# the pinked rim large and the floor around it small.
SHOTS = ['hero', 'hero-right', 'front', 'side', 'low']  # top-down dropped: it shows only the empty interior

# Thin kraft lets a little light through: it is what keeps the inside of an
# open bag a warm brown rather than a black hole.
TRANSLUCENCY = 0.22
MOTTLE = 0.035


def paper(ctx, name, art=None):
    """The bag's sheet: kraft (with its print) outside, plain kraft on the
    back faces inside, and a share of diffuse transmission. The reflected
    share is raised to make up for it, so the outside keeps its printed
    colour."""
    m = ctx.mat
    mat = m.kraft(name, art=art, color=dims.KRAFT)
    nt = mat.node_tree
    p = nt.nodes['Principled BSDF']
    out = nt.nodes['Material Output']
    outside = p.inputs['Base Color'].links[0].from_socket

    geo = nt.nodes.new('ShaderNodeNewGeometry')
    inside = nt.nodes.new('ShaderNodeRGB')
    inside.outputs[0].default_value = ctx.core.rgba(dims.KRAFT_INSIDE)
    side = nt.nodes.new('ShaderNodeMix')
    side.data_type = 'RGBA'
    nt.links.new(geo.outputs['Backfacing'], side.inputs['Factor'])
    nt.links.new(outside, side.inputs['A'])
    nt.links.new(inside.outputs[0], side.inputs['B'])
    # Kraft's cloudy formation: soft blotches a few millimetres across, a
    # few percent lighter or darker.
    coord = nt.nodes.new('ShaderNodeTexCoord')
    cloud = nt.nodes.new('ShaderNodeTexNoise')
    cloud.inputs['Scale'].default_value = 1.6
    cloud.inputs['Detail'].default_value = 8.0
    cloud.inputs['Roughness'].default_value = 0.62
    nt.links.new(coord.outputs['Object'], cloud.inputs['Vector'])
    amount = nt.nodes.new('ShaderNodeMapRange')
    amount.inputs['From Min'].default_value = 0.3
    amount.inputs['From Max'].default_value = 0.7
    amount.inputs['To Min'].default_value = 1.0 - MOTTLE
    amount.inputs['To Max'].default_value = 1.0 + MOTTLE
    nt.links.new(cloud.outputs['Fac'], amount.inputs['Value'])
    mottled = nt.nodes.new('ShaderNodeVectorMath')
    mottled.operation = 'SCALE'
    nt.links.new(side.outputs['Result'], mottled.inputs[0])
    nt.links.new(amount.outputs['Result'], mottled.inputs['Scale'])
    lift = nt.nodes.new('ShaderNodeVectorMath')
    lift.operation = 'SCALE'
    lift.inputs['Scale'].default_value = 1.0 / (1.0 - TRANSLUCENCY)
    nt.links.new(mottled.outputs['Vector'], lift.inputs[0])
    nt.links.new(lift.outputs['Vector'], p.inputs['Base Color'])

    through = nt.nodes.new('ShaderNodeBsdfTranslucent')
    through.inputs['Color'].default_value = ctx.core.rgba(dims.KRAFT)
    both = nt.nodes.new('ShaderNodeMixShader')
    both.inputs['Fac'].default_value = TRANSLUCENCY
    nt.links.new(p.outputs['BSDF'], both.inputs[1])
    nt.links.new(through.outputs['BSDF'], both.inputs[2])
    nt.links.new(both.outputs['Shader'], out.inputs['Surface'])
    return mat


def build(ctx):
    m, s = ctx.mat, ctx.shapes
    front = paper(ctx, 'bunji front', ctx.art('front.png'))
    back = paper(ctx, 'bunji back', ctx.art('back.png'))
    plain = paper(ctx, 'bunji kraft')
    inside = m.kraft('bunji inside', color=dims.KRAFT_INSIDE)
    walls = sos_bag.build_walls('bunji-bag', {'front': front, 'plain': plain, 'back': back, 'inside': inside, 'edge': plain}, solid=False)

    # The square bottom: two plies of kraft lying flat inside the walls.
    inner = 0.02
    base = s.walled_shell(
        'bunji-bag-bottom',
        s.rounded_rect(dims.W - 2 * inner, dims.D - 2 * inner, dims.FOLD_R, seg=4),
        0.0,
        2 * dims.PAPER,
        mats=(inside, inside, plain, None),
    )
    return [walls, base]
