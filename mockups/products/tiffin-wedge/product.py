"""IndiGo Tiffin: a triangular sandwich wedge in two colourways.

The carton is one printed sheet folded into a right-triangle prism: base, back
and slanted front form a tube with rounded folds, closed by the two triangle
ends. It is built as the outer skin (with a die-cut window in the front),
then given the board's thickness with Solidify, so the window shows a real
cut edge. A clear film is glued behind the window; behind it, the cut faces
of two sandwich halves (white and brown bread) with corn and chutney.
"""

import importlib.util
import math
import os
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))


def _sibling(name):
    spec = importlib.util.spec_from_file_location(f'tiffin_wedge_{name}', os.path.join(HERE, f'{name}.py'))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


dims = _sibling('dims')
food = _sibling('food')


# render.py rebuilds the scene with core.reset() when the variant changes, but
# studio.core keeps a Python reference to the old light-target empty, and the
# next core.studio() fails on it (ReferenceError). Until core.reset() clears
# it, forget it here whenever the factory scene is reloaded.
@bpy.app.handlers.persistent
def _forget_light_target(*_):
    from studio import core

    core._ORIGIN = None


if not any(getattr(h, '__name__', '') == '_forget_light_target' for h in bpy.app.handlers.load_factory_startup_post):
    bpy.app.handlers.load_factory_startup_post.append(_forget_light_target)

from studio.layout import inset  # noqa: E402

TITLE = 'Tiffin sandwich wedge'
VARIANTS = [None, 'big-don', 'set']
SHOTS = [
    'hero',
    'hero-right',
    {'name': 'front', 'preset': 'front', 'elevation': 14, 'fill': 0.58},
    {'name': 'back', 'preset': 'back', 'azimuth': 148, 'elevation': 24},
    {'name': 'side', 'preset': 'side', 'elevation': 18},
    {'name': 'big-don-hero', 'preset': 'hero', 'variant': 'big-don'},
    {'name': 'big-don-back', 'preset': 'back', 'azimuth': 148, 'elevation': 24, 'variant': 'big-don'},
    {'name': 'set-hero', 'preset': 'hero', 'variant': 'set', 'fill': 0.6},
]

W, L, T = dims.W, dims.L, dims.T

# (variant, location, turn in degrees) of each pack in the set shot.
SET_LAYOUT = (
    ('love-story', (-4.6, -2.2, 0.0), -6.0),
    ('big-don', (9.3, 5.0, 0.0), 116.0),
)


def _world(x_art, p, depth=0.0):
    """Front-panel art coordinates to the world (x_art from the -X end)."""
    y, z = dims.front_point(p, depth)
    return (x_art - W / 2, y, z)


# ----------------------------------------------------------------- carton


def carton_skin(name):
    """Outer surface of the carton with the window hole. Material slots:
    0 tube wrap, 1 -X end, 2 +X end."""
    prof = dims.profile()
    yz = [(y, z) for y, z, _ in prof]
    us = [u / dims.PERIMETER for _, _, u in prof] + [1.0]
    n = len(yz)
    i_cell = next(i for i in range(n) if abs(prof[i][2] - (dims.U_APEX + dims.CELL_P[0])) < 0.01)
    x_cell = (dims.CELL_X[0] - W / 2, dims.CELL_X[1] - W / 2)

    # Rings along X: the end folds, then the flat tube with the window cell's edges.
    re = dims.R_END
    rings = []  # (x, profile, kind)
    for i in range(dims.END_SEG, 0, -1):
        a = math.radians(90 * i / dims.END_SEG)
        rings.append((-(W / 2 - re + re * math.sin(a)), inset(yz, re * (1 - math.cos(a)))))
    for x in (-(W / 2 - re), x_cell[0], x_cell[1], W / 2 - re):
        rings.append((x, yz))
    for i in range(1, dims.END_SEG + 1):
        a = math.radians(90 * i / dims.END_SEG)
        rings.append(((W / 2 - re + re * math.sin(a)), inset(yz, re * (1 - math.cos(a)))))

    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    verts = [[bm.verts.new((x, y, z)) for y, z in pr] for x, pr in rings]

    def face(vs, uvs, mat):
        f = bm.faces.new(vs)
        f.material_index = mat
        f.smooth = True
        for loop, t in zip(f.loops, uvs):
            loop[uv].uv = t
        return f

    cell_ring = dims.END_SEG + 1  # ring index of x_cell[0]
    for r in range(len(rings) - 1):
        va, vb = verts[r], verts[r + 1]
        ta, tb = (rings[r][0] + W / 2) / W, (rings[r + 1][0] + W / 2) / W
        for i in range(n):
            j = (i + 1) % n
            if r == cell_ring and i == i_cell:
                continue  # the window cell, built below
            face([va[i], va[j], vb[j], vb[i]], [(us[i], ta), (us[i + 1], ta), (us[i + 1], tb), (us[i], tb)], 0)

    # Window cell: a frame of quads and corner fans around a rounded hole.
    O = [verts[cell_ring][i_cell], verts[cell_ring + 1][i_cell], verts[cell_ring + 1][i_cell + 1], verts[cell_ring][i_cell + 1]]
    (x0, x1), (p0, p1), rw = dims.WIN_X, dims.WIN_P, dims.WIN_R
    # Hole corners in the same order as O: (x0,p0) (x1,p0) (x1,p1) (x0,p1).
    centres = [(x0 + rw, p0 + rw), (x1 - rw, p0 + rw), (x1 - rw, p1 - rw), (x0 + rw, p1 - rw)]
    starts = [180, 270, 0, 90]  # arc start angle (degrees) in (x, p) space
    k = 5
    arcs = []
    for (cx, cp), a0 in zip(centres, starts):
        pts = []
        for s in range(k + 1):
            a = math.radians(a0 + 90 * s / k)
            pts.append((cx + rw * math.cos(a), cp + rw * math.sin(a)))
        arcs.append(pts)

    # u along the front is linear in p between the cell's two profile vertices.
    ua, ub = us[i_cell], us[i_cell + 1]

    def u_at(p):
        return ua + (ub - ua) * (p - dims.CELL_P[0]) / (dims.CELL_P[1] - dims.CELL_P[0])

    def hv(xa, p):
        v = bm.verts.new(_world(xa, p))
        return v, (u_at(p), xa / W)

    harcs = [[hv(xa, p) for xa, p in pts] for pts in arcs]

    def uv_of_outer(v):
        # Outer cell corners sit on the tube grid.
        xa = v.co.x + W / 2
        return (ua if v in (O[0], O[1]) else ub, xa / W)

    for c in range(4):
        o = O[c]
        for s in range(k):
            (va, ta), (vb, tb) = harcs[c][s], harcs[c][s + 1]
            face([o, va, vb], [uv_of_outer(o), ta, tb], 0)
        nxt = (c + 1) % 4
        (va, ta), (vb, tb) = harcs[c][k], harcs[nxt][0]
        face([o, O[nxt], vb, va], [uv_of_outer(o), uv_of_outer(O[nxt]), tb, ta], 0)

    # Flat triangle ends (the last inset rings).
    def end_uv(side):
        if side < 0:  # seen from -X: the back (+Y) is on the left
            return lambda co: ((L / 2 - co.y) / L, co.z / L)
        return lambda co: ((co.y + L / 2) / L, co.z / L)

    for side, ring, mat in ((-1, verts[0], 1), (1, verts[-1], 2)):
        f = bm.faces.new(ring)
        f.material_index = mat
        f.smooth = True
        fn = end_uv(side)
        for loop in f.loops:
            loop[uv].uv = fn(loop.vert.co)

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name + '-skin')
    bm.to_mesh(me)
    bm.free()
    return me


def carton(name, ctx, variant):
    mm = ctx.mat
    printed = []
    for label, img in (('print', f'tube-{variant}.png'), ('end -X', f'end-{variant}-l.png'), ('end +X', f'end-{variant}-r.png')):
        mat = mm.board(f'{name} {label}', art=ctx.art(img), roughness=0.56, coat=0.05, tooth=0.04)
        # A matte food-carton varnish: less sheen than the tins, so the dark
        # IndiGo blue is not veiled by reflected studio grey.
        mat.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.24
        printed.append(mat)
    tube, end_l, end_r = printed
    inside = mm.board(f'{name} inside', color='#e6e1d6', roughness=0.85, coat=0.0, tooth=0.08)
    edge = mm.board(f'{name} cut edge', color='#d8d1c1', roughness=0.9, coat=0.0, tooth=0.0)

    me = carton_skin(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for mat in (tube, end_l, end_r, inside, inside, inside, edge, edge, edge):
        me.materials.append(mat)
    sol = ob.modifiers.new('board', 'SOLIDIFY')
    sol.thickness = T
    sol.offset = -1.0
    sol.use_even_offset = True
    sol.use_quality_normals = True
    sol.use_rim = True
    sol.material_offset = 3
    sol.material_offset_rim = 6
    # Bake the thickness in, then split normals at the cut edges only.
    dg = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear()
    ob.data = baked
    bpy.data.meshes.remove(me)
    for poly in baked.polygons:
        poly.use_smooth = True
    baked.set_sharp_from_angle(angle=math.radians(35))
    return ob


# ----------------------------------------------------------------- film


def window_film(name='window film'):
    """Thin cello window: see-through (light and shadow pass, no refraction
    offset for a film this thin) with a glossy reflection that rises at
    grazing angles, and a faint unevenness so reflections are not perfect."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes['Principled BSDF'])
    out = nt.nodes['Material Output']
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = (0.97, 0.97, 0.97, 1)
    gl = nt.nodes.new('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.05
    # Keep the overhead softbox's reflection a soft sheen, not a grey veil.
    gl.inputs['Color'].default_value = (0.7, 0.7, 0.7, 1)
    fr = nt.nodes.new('ShaderNodeFresnel')
    fr.inputs['IOR'].default_value = 1.5
    tc = nt.nodes.new('ShaderNodeTexCoord')
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 0.9
    noise.inputs['Detail'].default_value = 2.0
    nt.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.02
    bump.inputs['Distance'].default_value = 0.05
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], gl.inputs['Normal'])
    nt.links.new(bump.outputs['Normal'], fr.inputs['Normal'])
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fr.outputs['Fac'], mix.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
    nt.links.new(gl.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return m


def film(name, mat):
    """Glued behind the window, a little larger than it, pulled slightly taut
    over the sandwich (a faint inward bow)."""
    (x0, x1), (p0, p1) = dims.WIN_X, dims.WIN_P
    x0, x1, p0, p1 = x0 - 0.45, x1 + 0.45, p0 - 0.45, p1 + 0.45
    nx, npp = 14, 30
    d0 = T + 0.006
    bm = bmesh.new()
    grid = []
    for i in range(npp + 1):
        row = []
        for j in range(nx + 1):
            fx, fp = j / nx, i / npp
            bow = 0.022 * math.sin(math.pi * fx) * math.sin(math.pi * fp)
            row.append(bm.verts.new(_world(x0 + (x1 - x0) * fx, p0 + (p1 - p0) * fp, d0 + bow)))
        grid.append(row)
    for i in range(npp):
        for j in range(nx):
            # Wound so the normal faces out of the pack: seen from its back,
            # the Fresnel node inverts the IOR and the film turns into a
            # grey mirror (total internal reflection) at grazing angles.
            f = bm.faces.new([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]])
            f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


# ----------------------------------------------------------------- build


def wedge(ctx, variant, food_mats, film_mat, tag=''):
    name = f'tiffin-{variant}{tag}'
    box = carton(name, ctx, variant)
    win = film(name + '-film', film_mat)
    (p0, p1) = dims.WIN_P
    sheet, corn = food.build(name + '-sandwich', _world, (p0 - 0.7, p1 + 0.7), 0.16, food_mats, seed=7 if variant == 'love-story' else 11)
    return [box, win, sheet, corn]


def build(ctx, variant=None):
    food_mats = food.materials()
    film_mat = window_film()
    if variant in (None, 'love-story', 'big-don'):
        return wedge(ctx, variant or 'love-story', food_mats, film_mat)
    # The set: Love Story in front, showing its window; Big Don behind and to
    # the right, turned so the camera sees its story panel and its Aero-bics
    # end at once, so both read as wedges.
    objs = []
    for v, loc, rot in SET_LAYOUT:
        parts = wedge(ctx, v, food_mats, film_mat)
        root = bpy.data.objects.new(f'{v}-root', None)
        bpy.context.collection.objects.link(root)
        root.location = loc
        root.rotation_euler = (0, 0, math.radians(rot))
        for o in parts:
            o.parent = root
        objs += parts
    bpy.context.view_layer.update()
    return objs
