"""IndiGo paper napkin: an offset-folded, embossed white tissue napkin with
one line of IndiGo-blue Hindi, lying flat. A 'stack' variant lays three
napkins loosely on top of each other."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402
import fold  # noqa: E402

TITLE = 'IndiGo paper napkin'
SHOTS = [
    'top',
    'hero',
    'hero-right',
    {'name': 'front', 'preset': 'front', 'elevation': 24},
    {'name': 'low', 'preset': 'low', 'elevation': 13},
    {'name': 'stack-hero', 'preset': 'hero', 'variant': 'stack'},
    {'name': 'stack-top', 'preset': 'top', 'variant': 'stack'},
]
VARIANTS = [None, 'stack']

# Stack: (dx, dy, rotation) of each napkin from the bottom up, and its seed.
STACK = [
    (-0.55, 0.45, -5.5, 11),
    (0.5, 0.05, 3.0, 12),
    (0.0, -0.35, -0.8, 13),
]


def napkin_material(ctx):
    """The shared tissue material with the embossed pattern added as a bump
    on top of its own paper grain."""
    import bpy

    m = ctx.mat.tissue('napkin', art=ctx.art('sheet.png'))
    nt = m.node_tree
    grain = next(n for n in nt.nodes if n.type == 'BUMP')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = ctx.mat.image(ctx.art('emboss.png'), alpha=False, colorspace='Non-Color')
    tex.interpolation = 'Cubic'
    tex.extension = 'EXTEND'
    uv = nt.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'
    nt.links.new(uv.outputs['UV'], tex.inputs['Vector'])
    emb = nt.nodes.new('ShaderNodeBump')
    emb.inputs['Strength'].default_value = 0.55
    emb.inputs['Distance'].default_value = 0.012
    nt.links.new(tex.outputs['Color'], emb.inputs['Height'])
    nt.links.new(emb.outputs['Normal'], grain.inputs['Normal'])
    _ = bpy
    return m


def build(ctx, variant=None):
    mat = napkin_material(ctx)
    if variant == 'stack':
        objs, placed = [], []
        for i, (dx, dy, rot, seed) in enumerate(STACK):
            verts, uv = fold.napkin(seed=seed)
            verts = fold.drape(fold.place(verts, dx, dy, rot), placed)
            placed.append(verts)
            objs.append(fold.mesh(f'napkin-{i + 1}', verts, uv, mat))
        return objs
    verts, uv = fold.napkin(seed=7)
    return [fold.mesh('napkin', verts, uv, mat)]
