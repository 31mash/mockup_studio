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
    # A flat napkin at the presets' 10 and 7 degrees is only a sliver: lift
    # the front view until the line reads, and bring the low view in close
    # as a detail of the layers and the torn edge.
    {'name': 'front', 'preset': 'front', 'elevation': 28, 'fill': 0.6},
    {'name': 'low', 'preset': 'low', 'elevation': 12, 'fill': 0.74},
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
    emb.inputs['Strength'].default_value = 1.0
    emb.inputs['Distance'].default_value = 0.03
    nt.links.new(tex.outputs['Color'], emb.inputs['Height'])
    nt.links.new(emb.outputs['Normal'], grain.inputs['Normal'])

    # Crepe: the fine parallel wrinkles of creped tissue, running along the
    # sheet's width (about 0.4 mm apart, a few mm long), laid on the unfolded
    # sheet through the UVs so they follow every layer and fold.
    sc = nt.nodes.new('ShaderNodeVectorMath')
    sc.operation = 'MULTIPLY'
    sc.inputs[1].default_value = (dims.SHEET_W * 2.2, dims.SHEET_H * 24.0, 0.0)
    nt.links.new(uv.outputs['UV'], sc.inputs[0])
    crepe = nt.nodes.new('ShaderNodeTexNoise')
    crepe.inputs['Scale'].default_value = 1.0
    crepe.inputs['Detail'].default_value = 1.0
    crepe.inputs['Roughness'].default_value = 0.55
    nt.links.new(sc.outputs['Vector'], crepe.inputs['Vector'])
    cb = nt.nodes.new('ShaderNodeBump')
    cb.inputs['Strength'].default_value = 0.09
    cb.inputs['Distance'].default_value = 0.004
    nt.links.new(crepe.outputs['Fac'], cb.inputs['Height'])
    nt.links.new(cb.outputs['Normal'], emb.inputs['Normal'])
    return m


def _survive_variant_switch(core):
    """render.py resets the scene when the variant changes, but studio.core
    keeps a module-level handle on the old light-target empty, and reading a
    freed object raises ReferenceError in the next studio() call. Forget that
    handle after every reset (runtime only; the shared file is untouched)."""
    if getattr(core.reset, 'forgets_origin', False):
        return
    reset = core.reset

    def reset_and_forget():
        reset()
        core._ORIGIN = None

    reset_and_forget.forgets_origin = True
    core.reset = reset_and_forget


def build(ctx, variant=None):
    _survive_variant_switch(ctx.core)
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
