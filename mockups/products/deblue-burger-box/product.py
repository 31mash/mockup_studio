"""DaBlue Burger: IndiGo's printed paperboard clamshell for the Dabeli burger.

Modelled closed. The lid is a flat top over four walls that flare out down
to the parting line; the short base tray's walls slope back in to a smaller
footprint and turn up at the parting line into a flange that sits just
inside the lid. The side profile is a hexagon, and only a narrow band of the
base shows under the lid, as in the photo. The lid's two front corners are
V-notched at the bottom, showing the base's corner.

Every panel is a flat piece of board with its own artwork image, mapped at
true size (no stretch). The folds are creased with a small radius, and each
half of a fold's curve carries its own panel's print, as a bleed would.
A Solidify gives the board its thickness; cut edges and the inside are the
board's white core.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402

TITLE = 'DaBlue Burger box'
SHOTS = [
    'hero',
    'hero-right',
    # the source photo's viewpoint: both illustrated walls in equal measure
    {'name': 'three-quarter', 'preset': 'hero', 'azimuth': 45, 'elevation': 34},
    'front',
    'side',
    'top',
    'back',
    'low',
]

# name, outward normal, right-hand direction seen from outside. The wall
# between corners k and k+1 (corners CCW from front-left) is SIDES[k].
SIDES = [
    ('front', (0.0, -1.0), (1.0, 0.0)),
    ('right', (1.0, 0.0), (0.0, 1.0)),
    ('back', (0.0, 1.0), (-1.0, 0.0)),
    ('left', (-1.0, 0.0), (0.0, -1.0)),
]
CORNERS = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
NOTCHED = (0, 1)  # the lid's front corners
WHITE_SLOT = 5  # material slots from here on are the board's white core


def _new_bm():
    """A bmesh with the UV and panel layers made up front (adding a layer
    later invalidates face references)."""
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    bm.faces.layers.int.new('part')
    return bm


def _ring(bm, half, z):
    return [bm.verts.new((sx * half, sy * half, z)) for sx, sy in CORNERS]


def _face(bm, verts, part, part_of):
    f = bm.faces.new(verts)
    part_of[f] = part
    return f


def _finish(name, bm, part_of, uv_of, materials, fold_edges, dirs):
    """Bevels the fold edges, gives every face its panel's material and a
    true-size UV from that panel's mapping, adds the board thickness and
    makes the object. dirs: (part, outward direction) used to hand each bevel
    face to the nearer of the two panels it joins."""
    uv = bm.loops.layers.uv['UVMap']
    part = bm.faces.layers.int['part']
    for f, p in part_of.items():
        f[part] = p
    res = bmesh.ops.bevel(
        bm,
        geom=list(fold_edges),
        offset=dims.FOLD_R,
        offset_type='OFFSET',
        segments=4,
        profile=0.5,
        affect='EDGES',
        clamp_overlap=True,
        loop_slide=True,
    )
    new = set(res['faces'])
    bm.normal_update()
    for f in bm.faces:
        if f in new:
            f[part] = max(dirs, key=lambda kv: f.normal.dot(kv[1]))[0]
            f.smooth = True
        else:
            f.smooth = False
        f.material_index = f[part]
        for loop in f.loops:
            loop[uv].uv = uv_of(f[part], loop.vert.co)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in materials:
        me.materials.append(m)
    sol = ob.modifiers.new('board', 'SOLIDIFY')
    sol.thickness = dims.BOARD
    sol.offset = -1.0  # inward: the outside stays at the modelled size
    sol.use_even_offset = True
    sol.use_quality_normals = True
    sol.use_rim = True
    sol.material_offset = WHITE_SLOT
    sol.material_offset_rim = WHITE_SLOT
    return ob


def build_lid(mats):
    """mats: [top, front, right, back, left] + white core. Returns the lid."""
    A0, A1, zp, H = dims.A0, dims.A1, dims.Z_PART, dims.H
    bm = _new_bm()
    b = [Vector((sx * A0, sy * A0, zp)) for sx, sy in CORNERS]
    t = _ring(bm, A1, H)
    # Where each hip fold starts: the bottom corner, or the top of its notch.
    hip = []
    for k in range(4):
        p = b[k] + (t[k].co - b[k]) * (dims.NOTCH_H / (H - zp)) if k in NOTCHED else b[k]
        hip.append(bm.verts.new(p))
    part_of = {}
    _face(bm, t, 0, part_of)
    for k in range(4):
        j = (k + 1) % 4
        # Round the wall as seen from outside: bottom left, bottom right, up
        # the right hip, along the top fold, down the left hip.
        if k in NOTCHED:
            vs = [bm.verts.new(b[k] + (b[j] - b[k]).normalized() * dims.NOTCH_W)]
        else:
            vs = [hip[k]]
        if j in NOTCHED:
            vs += [bm.verts.new(b[j] + (b[k] - b[j]).normalized() * dims.NOTCH_W), hip[j]]
        else:
            vs.append(hip[j])
        vs += [t[j], t[k]]
        if k in NOTCHED:
            vs.append(hip[k])
        _face(bm, vs, 1 + k, part_of)
    bm.edges.ensure_lookup_table()
    folds = [bm.edges.get([t[k], t[(k + 1) % 4]]) for k in range(4)] + [bm.edges.get([hip[k], t[k]]) for k in range(4)]
    dirs = [(0, Vector((0, 0, 1)))] + [(1 + k, Vector((n[0], n[1], dims.LID_TAPER)).normalized()) for k, (_, n, _) in enumerate(SIDES)]

    def uv_of(p, co):
        if p == 0:
            return ((co.x + A1) / (2 * A1), (co.y + A1) / (2 * A1))
        if 1 <= p <= 4:
            _, _, r = SIDES[p - 1]
            return ((co.x * r[0] + co.y * r[1] + A0) / (2 * A0), (co.z - zp) / (H - zp))
        return (0.5, 0.5)

    return _finish('burger-box-lid', bm, part_of, uv_of, mats, folds, dirs)


def build_base(mats):
    """mats: [front, right, back, left walls, bottom] + white core."""
    C0, CK, C1, zp, zt = dims.C0, dims.CK, dims.C1, dims.Z_PART, dims.Z_BASE_TOP
    bm = _new_bm()
    bb = _ring(bm, C0, 0.0)
    bk = _ring(bm, CK, zp)
    bt = _ring(bm, C1, zt)
    part_of = {}
    _face(bm, list(reversed(bb)), 4, part_of)
    for k in range(4):
        j = (k + 1) % 4
        _face(bm, [bb[k], bb[j], bk[j], bk[k]], k, part_of)
        _face(bm, [bk[k], bk[j], bt[j], bt[k]], k, part_of)
    bm.edges.ensure_lookup_table()
    folds = [bm.edges.get([bb[k], bb[(k + 1) % 4]]) for k in range(4)]
    folds += [bm.edges.get([bb[k], bk[k]]) for k in range(4)] + [bm.edges.get([bk[k], bt[k]]) for k in range(4)]
    dirs = [(4, Vector((0, 0, -1)))] + [(k, Vector((n[0], n[1], -dims.BASE_SLOPE)).normalized()) for k, (_, n, _) in enumerate(SIDES)]
    k_lower = math.hypot(1, dims.BASE_SLOPE)
    k_flange = math.hypot(1, dims.LID_TAPER)

    def uv_of(p, co):
        if p < 4:
            _, _, r = SIDES[p]
            # v follows the board's length up the wall, across the kink.
            s = co.z * k_lower if co.z <= zp else dims.BASE_LOWER + (co.z - zp) * k_flange
            return ((co.x * r[0] + co.y * r[1] + CK) / (2 * CK), s / dims.BASE_SLANT)
        if p == 4:
            return ((co.x + C0) / (2 * C0), (co.y + C0) / (2 * C0))
        return (0.5, 0.5)

    return _finish('burger-box-base', bm, part_of, uv_of, mats, folds, dirs)


def build(ctx, variant=None):
    m = ctx.mat
    white = m.board('board core', color='#f2f0ea', coat=0.0, tooth=0.03)
    lid_mats = [m.board('top panel', art=ctx.art('top.png'))]
    lid_mats += [m.board(f'{name} wall', art=ctx.art(f'wall-{name}.png')) for name, _, _ in SIDES]
    base_wall = m.board('base walls', art=ctx.art('base-side.png'))
    base_mats = [base_wall] * 4 + [m.board('base bottom', color='#cbd4d9')]
    lid = build_lid(lid_mats + [white] * WHITE_SLOT)
    base = build_base(base_mats + [white] * WHITE_SLOT)
    return [lid, base]
