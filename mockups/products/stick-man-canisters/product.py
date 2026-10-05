"""IndiGo 'Stick Man' potato-stick canisters: three composite cans (chocolate
brown, magenta pink and deep navy) with gold double-seamed tinplate ends, a
silver peel-off foil under the top seam, and printed paper labels on which a
parade of potato-stick men gets eaten from can to can.

Variants: 'brown', 'pink', 'navy', and 'set' (the three in a row, as in the
spread), optionally turned:

    'navy@31'           the label's front as in the spread faces a camera at azimuth 31
    'navy:100@31'       the label at 100 degrees right of that front faces it instead
    'set:-20,0,95@31'   the same, one angle per can (brown, pink, navy)
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import can  # noqa: E402
import dims  # noqa: E402

TITLE = 'Stick Man potato-stick canisters'


def _turned(name, at, azimuth):
    return f'{name}:{at:g}@{azimuth:g}'


SHOTS = [
    # Each can's hero turns its title panel to the lens, with the first stick
    # man coming round on the right.
    {'name': 'hero', 'preset': 'hero', 'variant': _turned('brown', dims.HERO_AT['brown'], 31)},
    {'name': 'front', 'preset': 'front', 'variant': _turned('brown', -12, 0)},
    {'name': 'pink-hero', 'preset': 'hero', 'variant': _turned('pink', dims.HERO_AT['pink'], 31)},
    {'name': 'navy-hero', 'preset': 'hero', 'variant': _turned('navy', dims.HERO_AT['navy'], 31)},
    # The set as a story: the brown's title and whole men, the pink's men
    # losing their limbs, the navy's title beside the last heads.
    {'name': 'set-hero', 'preset': 'hero', 'variant': 'set:-20,0,95@31', 'fill': 0.66},
    # As in the spread: each can shows the same stretch of label as the photo.
    {'name': 'set-front', 'preset': 'front', 'variant': 'set', 'fill': 0.74},
    {'name': 'set-top', 'preset': 'top', 'variant': 'set', 'fill': 0.74},
]
VARIANTS = ['brown', 'pink', 'navy', 'set']


def _linear(hexc):
    c = int(hexc[1:3], 16) / 255, int(hexc[3:5], 16) / 255, int(hexc[5:7], 16) / 255
    return [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]


def _srgb_hex(lin):
    out = []
    for v in lin:
        v = max(0.0, min(1.0, v))
        s = v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
        out.append(round(s * 255))
    return '#%02x%02x%02x' % tuple(out)


def printed_foil(ctx, name, art):
    """The peel-off membrane: lacquered aluminium foil printed in one colour.
    Bare foil (the artwork's silver and its pressed seal rings) is metallic;
    the ink is opaque and diffuse. The ink is found by its distance from the
    bare foil's colour in the artwork."""
    m = ctx.mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    p = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = m.image(art)
    tex.interpolation = 'Cubic'
    tex.extension = 'EXTEND'
    silver = nt.nodes.new('ShaderNodeCombineXYZ')
    for i, v in enumerate(_linear(dims.FOIL_SILVER)):
        silver.inputs[i].default_value = v
    dist = nt.nodes.new('ShaderNodeVectorMath')
    dist.operation = 'DISTANCE'
    nt.links.new(tex.outputs['Color'], dist.inputs[0])
    nt.links.new(silver.outputs[0], dist.inputs[1])
    ink = nt.nodes.new('ShaderNodeMapRange')  # 0 on bare foil (seal rings included), 1 on ink
    ink.inputs['From Min'].default_value = 0.3
    ink.inputs['From Max'].default_value = 0.55
    nt.links.new(dist.outputs['Value'], ink.inputs['Value'])
    tint = nt.nodes.new('ShaderNodeMix')
    tint.data_type = 'RGBA'
    tint.blend_type = 'MULTIPLY'
    tint.inputs['Factor'].default_value = 1.0
    # Mix node sockets by index: 6 and 7 are the colour inputs A and B, 2 the colour result.
    nt.links.new(tex.outputs['Color'], tint.inputs[6])
    tint.inputs[7].default_value = (dims.FOIL_TINT, dims.FOIL_TINT, dims.FOIL_TINT * 1.01, 1.0)
    base = nt.nodes.new('ShaderNodeMix')
    base.data_type = 'RGBA'
    nt.links.new(ink.outputs['Result'], base.inputs[0])
    nt.links.new(tint.outputs[2], base.inputs[6])
    nt.links.new(tex.outputs['Color'], base.inputs[7])
    nt.links.new(base.outputs[2], p.inputs['Base Color'])
    metal = nt.nodes.new('ShaderNodeMapRange')
    metal.inputs['To Min'].default_value = dims.FOIL_METALLIC
    metal.inputs['To Max'].default_value = 0.0
    nt.links.new(ink.outputs['Result'], metal.inputs['Value'])
    nt.links.new(metal.outputs['Result'], p.inputs['Metallic'])
    rough = nt.nodes.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value = dims.FOIL_ROUGH
    rough.inputs['To Max'].default_value = 0.42
    nt.links.new(ink.outputs['Result'], rough.inputs['Value'])
    nt.links.new(rough.outputs['Result'], p.inputs['Roughness'])
    p.inputs['Coat Weight'].default_value = 0.05
    p.inputs['Coat Roughness'].default_value = 0.2
    return mat


def materials(ctx, colour, cache):
    m = ctx.mat
    if 'gold' not in cache:
        # Gold-lacquered tinplate ends, as in the photo.
        cache['gold'] = m.bare_metal('gold lacquer', color='#cdb67c', roughness=0.24)
        # The pull tab: the membrane's unprinted foil, folded back.
        bare = _srgb_hex([v * dims.FOIL_TINT for v in _linear(dims.FOIL_SILVER)])
        cache['foil'] = m.printed_metal('peel foil', color=bare, roughness=dims.FOIL_ROUGH, coat=0.05, metallic=dims.FOIL_METALLIC)
    if colour not in cache:
        # Uncoated label paper: a soft sheen but no varnish, so the dark
        # browns and navies keep their depth instead of greying over.
        paper = m.board(f'label {colour}', art=ctx.art(f'label-{colour}.png'), roughness=0.5, coat=0.0, tooth=0.025)
        paper.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.2
        lid = printed_foil(ctx, f'foil {colour}', ctx.art(f'lid-{colour}.png'))
        cache[colour] = (paper, lid)
    paper, lid = cache[colour]
    return paper, lid, cache['gold'], cache['foil']


def one_can(ctx, cache, colour, x=0.0, face=0.0):
    """A closed can standing on z = 0 at (x, 0). `face` is the camera azimuth
    the label's front should face (degrees, + towards the product's left)."""
    paper, lid, gold, foil = materials(ctx, colour, cache)
    body = [
        can.paper_tube(f'{colour}-label', paper),
        can.top_ring(f'{colour}-top-ring', gold),
        can.bottom_end(f'{colour}-bottom', gold),
    ]
    bpy.ops.object.empty_add(location=(x, 0.0, 0.0))
    pivot = bpy.context.object
    pivot.name = f'{colour}-can'
    pivot.rotation_euler.z = math.radians(-face)
    for p in body:
        p.parent = pivot
    # The end is seamed on at no particular turn, so its printed foil keeps
    # facing the front (-Y) like the Nut Case lid, whichever way the label turns.
    top = [can.foil(f'{colour}-foil', lid), can.pull_tab(f'{colour}-tab', foil)]
    for p in top:
        p.location.x += x
    return body + top


def parse(variant):
    """'name[:a[,b,c]][@azimuth]' -> name, label angles facing the camera, azimuth."""
    name, _, az = (variant or 'brown').partition('@')
    name, _, at = name.partition(':')
    angles = [float(v) for v in at.split(',')] if at else []
    return name, angles, float(az) if az else 0.0


def build(ctx, variant=None):
    name, angles, az = parse(variant)
    cache = {}
    if name == 'set':
        angles = angles or [0.0] * len(dims.SET_ORDER)
        objs = []
        for i, colour in enumerate(dims.SET_ORDER):
            # A label angle `a` faces the camera when the can turns by a + azimuth.
            objs += one_can(ctx, cache, colour, x=(i - 1) * dims.SET_STEP, face=angles[i] + az)
    elif name in dims.CANS:
        objs = one_can(ctx, cache, name, face=(angles[0] if angles else 0.0) + az)
    else:
        raise ValueError(f'unknown variant {variant!r}')
    bpy.context.view_layer.update()
    return objs
