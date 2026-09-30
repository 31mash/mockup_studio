"""Geometry builders with exact UVs, in centimetres. Every product faces -Y.

Artwork conventions (see README "Artwork"):

- Top and bottom caps use a planar projection: the image is the lid seen from
  above, with the product's front edge at the bottom of the image.
- Side walls use one wrap strip per wall: u runs around the perimeter,
  counter-clockwise seen from above, starting where the front face begins at
  its left end (for round shapes: at the front centre, going right). v runs up.
  `wrap_layout()` gives where each flat face and corner lands in the strip.
- Cartons use one image per face, drawn as seen from outside, upright.
"""

from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector

from .layout import circle, inset, perimeter, rounded_rect, wrap_layout  # noqa: F401


# ----------------------------------------------------------------- mesh building


class MeshBuilder:
    """Collects rings of vertices into quads with UVs and material slots."""

    def __init__(self, name: str):
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')

    def ring(self, profile, z: float):
        return [self.bm.verts.new((x, y, z)) for x, y in profile]

    def band(self, lower, upper, uv_lower, uv_upper, mat: int, closed: bool = True, flip: bool = False):
        """Quads between two vertex rings. uv_* are per-vertex (u, v) lists with
        one extra entry at the end for the seam (u = 1)."""
        n = len(lower)
        count = n if closed else n - 1
        for i in range(count):
            j = (i + 1) % n
            vs = [lower[i], lower[j], upper[j], upper[i]]
            uvs = [uv_lower[i], uv_lower[i + 1], uv_upper[i + 1], uv_upper[i]]
            if flip:
                vs.reverse()
                uvs.reverse()
            try:
                f = self.bm.faces.new(vs)
            except ValueError:
                continue
            f.material_index = mat
            f.smooth = True
            for loop, uv in zip(f.loops, uvs):
                loop[self.uv].uv = uv

    def cap(self, ring_verts, uv_of, mat: int, up: bool = True):
        vs = ring_verts if up else list(reversed(ring_verts))
        f = self.bm.faces.new(vs)
        f.material_index = mat
        f.smooth = False
        for loop in f.loops:
            loop[self.uv].uv = uv_of(loop.vert.co)
        return f

    def finish(self, materials, auto_smooth: float = 40.0) -> bpy.types.Object:
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me)
        self.bm.free()
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.collection.objects.link(ob)
        for m in materials:
            me.materials.append(m)
        # Smooth curved walls, keep crisp creases.
        mod = ob.modifiers.new('smooth', 'NODES') if False else None
        try:
            with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
                bpy.ops.object.shade_auto_smooth(angle=math.radians(auto_smooth))
        except Exception:
            for p in me.polygons:
                p.use_smooth = True
        return ob


def _strip_uvs(profile, u_offset: float = 0.0):
    acc = perimeter(profile)
    total = acc[-1]
    return [(u_offset + a / total) for a in acc], total


def _planar(w: float, d: float, cx: float = 0.0, cy: float = 0.0):
    return lambda co: ((co.x - cx) / w + 0.5, (co.y - cy) / d + 0.5)


def walled_shell(
    name: str,
    profile,
    z0: float,
    z1: float,
    top_radius: float = 0.0,
    bottom_radius: float = 0.0,
    edge_seg: int = 6,
    mats=(None, None, None, None),
    top_extent: tuple[float, float] | None = None,
    side_v: tuple[float, float] = (0.0, 1.0),
    edge_uv: str = 'top',
    cap_top: bool = True,
    cap_bottom: bool = True,
):
    """A closed solid from an outline: side wall between z0 and z1, rounded top
    and bottom edges, flat caps. mats = (side, top, bottom, edge) materials;
    `edge` defaults to the top material. Returns the object.

    UVs: side wall = wrap strip (u around, v from side_v[0] at z0+bottom_radius
    to side_v[1] at z1-top_radius); top/bottom = planar over top_extent (w, d),
    default the outline's bounding box; edge rings follow `edge_uv`
    ('top' = planar like the cap, 'side' = continue the wrap strip)."""
    side_m, top_m, bottom_m, edge_m = mats
    edge_m = edge_m or top_m
    mat_list = [m for m in (side_m, top_m, bottom_m, edge_m) if m is not None]
    idx = {id(m): i for i, m in enumerate(dict.fromkeys(mat_list))}
    uniq = list(dict.fromkeys(mat_list))

    def mi(m):
        return idx.get(id(m), 0)

    xs = [p[0] for p in profile]
    ys = [p[1] for p in profile]
    w = top_extent[0] if top_extent else (max(xs) - min(xs))
    d = top_extent[1] if top_extent else (max(ys) - min(ys))
    planar = _planar(w, d)

    mb = MeshBuilder(name)
    us, _ = _strip_uvs(profile)

    zs0 = z0 + bottom_radius
    zs1 = z1 - top_radius
    v0, v1 = side_v

    def v_at(z):
        return v0 + (v1 - v0) * (z - zs0) / max(1e-6, (zs1 - zs0))

    # Rings from the bottom cap up to the top cap. Each ring records the kind
    # of band that leads up to it: 'bedge' (rounded bottom edge), 'side'
    # (the wall) or 'tedge' (rounded top edge).
    rings = []
    if bottom_radius > 0:
        for i in range(edge_seg + 1):
            a = math.radians(90 * i / edge_seg)  # 0 = bottom, 90 = side
            off = bottom_radius * (1 - math.sin(a))
            z = zs0 - bottom_radius * math.cos(a)
            rings.append(('bedge' if i else None, inset(profile, off) if off > 1e-6 else profile, z))
    else:
        rings.append((None, profile, z0))
    rings.append(('side', profile, zs1 if top_radius > 0 else z1))
    if top_radius > 0:
        for i in range(1, edge_seg + 1):
            a = math.radians(90 * i / edge_seg)  # 0 = side, 90 = top
            off = top_radius * (1 - math.cos(a))
            z = zs1 + top_radius * math.sin(a)
            rings.append(('tedge', inset(profile, off), z))

    verts = [mb.ring(p, z) for _, p, z in rings]

    def ring_uv(kind, prof, z):
        if kind == 'side' or (edge_uv == 'side' and kind in ('tedge', 'bedge')):
            vv = v_at(z)
            return [(u, vv) for u in us]
        uvs = [planar(Vector((x, y, z))) for x, y in prof]
        return uvs + [uvs[0]]

    for k in range(len(rings) - 1):
        _, pa, za = rings[k]
        kind, pb, zb = rings[k + 1]
        if kind == 'side':
            m = side_m
        elif kind == 'tedge':
            m = edge_m if edge_uv == 'top' else side_m
        else:
            m = bottom_m or side_m
        mb.band(verts[k], verts[k + 1], ring_uv(kind, pa, za), ring_uv(kind, pb, zb), mi(m))

    if cap_top:
        mb.cap(verts[-1], planar, mi(top_m), up=True)
    if cap_bottom and bottom_m is not None:
        mb.cap(verts[0], lambda co: (1 - planar(co)[0], planar(co)[1]), mi(bottom_m), up=False)
    elif cap_bottom:
        mb.cap(verts[0], planar, mi(side_m), up=False)
    return mb.finish(uniq)


def torus_ring(name: str, profile, z: float, tube: float, mat, seg: int = 8):
    """A rolled bead (like a tin's seam) following an outline at height z."""
    mb = MeshBuilder(name)
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        off = -tube * math.cos(a)  # outward at a=pi
        rings.append((inset(profile, off), z + tube * math.sin(a)))
    verts = [mb.ring(p, zz) for p, zz in rings]
    us, _ = _strip_uvs(profile)
    for k in range(seg):
        a = verts[k]
        b = verts[(k + 1) % seg]
        mb.band(a, b, [(u, k / seg) for u in us], [(u, (k + 1) / seg) for u in us], 0)
    return mb.finish([mat], auto_smooth=80)


# ----------------------------------------------------------------- products


def slip_lid_tin(
    name: str,
    outline,
    body_h: float,
    lid_h: float,
    lid_gap: float = 0.17,
    lid_edge: float = 0.9,
    body_edge: float = 0.35,
    wall: float = 0.08,
    mats: dict | None = None,
    top_extent: tuple[float, float] | None = None,
    edge_uv: str = 'top',
):
    """A tin with a slip-on lid: body wall, rolled bead just below the lid, and
    a lid slightly larger than the body with a rounded top edge.

    outline: the lid's outer outline (rounded_rect or circle). mats keys:
    lid_top, lid_side, body_side, bottom, bead. Returns (lid, body, bead)."""
    mats = mats or {}
    total = body_h + lid_h
    body_outline = inset(outline, wall + 0.04)
    # The body is hidden under the lid for its top part.
    body = walled_shell(
        f'{name}-body',
        body_outline,
        0.0,
        body_h + lid_h * 0.6,
        top_radius=0.0,
        bottom_radius=body_edge,
        mats=(mats.get('body_side'), mats.get('body_side'), mats.get('bottom'), None),
        side_v=(0.0, (body_h + lid_h * 0.6 - body_edge) / max(1e-6, body_h - body_edge)),
        top_extent=top_extent,
    )
    lid = walled_shell(
        f'{name}-lid',
        outline,
        body_h + lid_gap,
        total,
        top_radius=lid_edge,
        bottom_radius=0.0,
        mats=(mats.get('lid_side'), mats.get('lid_top'), None, mats.get('lid_edge')),
        top_extent=top_extent,
        edge_uv=edge_uv,
        cap_bottom=False,
    )
    # A rolled lip at the lid's open edge, and the body's silver bead in the gap.
    lip = torus_ring(f'{name}-lid-lip', inset(outline, 0.05), body_h + lid_gap + 0.05, 0.06, mats.get('lid_side'))
    bead = torus_ring(f'{name}-bead', inset(outline, 0.07), body_h + lid_gap * 0.5, 0.09, mats.get('bead'))
    return lid, body, bead, lip


def carton(name: str, w: float, d: float, h: float, faces: dict, bevel: float = 0.06):
    """A closed card box. faces: front/back/left/right/top/bottom -> material,
    each with a 0-1 UV over the whole face, drawn upright as seen from outside
    (top: front edge at the bottom of the image; bottom: front edge at the top)."""
    hw, hd = w / 2, d / 2
    mats = list(dict.fromkeys(faces.values()))
    idx = {id(m): i for i, m in enumerate(mats)}
    mb = MeshBuilder(name)
    V = lambda x, y, z: mb.bm.verts.new((x, y, z))  # noqa: E731
    c = {
        'lfb': V(-hw, -hd, 0), 'rfb': V(hw, -hd, 0), 'rbb': V(hw, hd, 0), 'lbb': V(-hw, hd, 0),
        'lft': V(-hw, -hd, h), 'rft': V(hw, -hd, h), 'rbt': V(hw, hd, h), 'lbt': V(-hw, hd, h),
    }
    quads = {
        'front': (['lfb', 'rfb', 'rft', 'lft'], [(0, 0), (1, 0), (1, 1), (0, 1)]),
        'right': (['rfb', 'rbb', 'rbt', 'rft'], [(0, 0), (1, 0), (1, 1), (0, 1)]),
        'back': (['rbb', 'lbb', 'lbt', 'rbt'], [(0, 0), (1, 0), (1, 1), (0, 1)]),
        'left': (['lbb', 'lfb', 'lft', 'lbt'], [(0, 0), (1, 0), (1, 1), (0, 1)]),
        'top': (['lft', 'rft', 'rbt', 'lbt'], [(0, 0), (1, 0), (1, 1), (0, 1)]),
        'bottom': (['lbb', 'rbb', 'rfb', 'lfb'], [(0, 1), (1, 1), (1, 0), (0, 0)]),
    }
    for fname, (keys, uvs) in quads.items():
        f = mb.bm.faces.new([c[k] for k in keys])
        m = faces.get(fname)
        f.material_index = idx.get(id(m), 0)
        for loop, uv in zip(f.loops, uvs):
            loop[mb.uv].uv = uv
    ob = mb.finish(mats, auto_smooth=30)
    if bevel > 0:
        b = ob.modifiers.new('bevel', 'BEVEL')
        b.width = bevel
        b.segments = 3
        b.limit_method = 'ANGLE'
        b.harden_normals = True
    return ob
