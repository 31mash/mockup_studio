"""Round cookie tin geometry: closed solids of revolution with explicit UVs.

Profiles are lists of (r, z, mat, uv) points; the band from a point to the next
takes that point's material index and UV mode:

- ('planar', R): the lid-top image over a disc of radius R, seen from above,
  front (-Y) at the bottom of the image (README "Caps").
- ('wrap', z0, z1): the body wrap strip: u = 0 at the front centre running
  counter-clockwise seen from above (to the right from the front), v from z0
  to z1 (README "Walls").
- ('flat',): unprinted metal, no artwork.

Every profile runs from one cap ring to another, so each part is a closed,
manifold solid with outward normals.
"""

from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import dims

SEG = 256  # around the tin: smooth silhouettes and highlights at any size


def arc(cx, cz, r, a0, a1, n, mat, uv):
    """Points on a circular arc from a0 to a1 (degrees), inclusive."""
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + r * math.cos(a), cz + r * math.sin(a), mat, uv))
    return out


def _angle(i, seg):
    return math.radians(-90 + 360 * i / seg)


def _uv(mode, x, y, z, i, seg):
    kind = mode[0]
    if kind == 'planar':
        R = mode[1]
        return (0.5 + x / (2 * R), 0.5 + y / (2 * R))
    if kind == 'wrap':
        z0, z1 = mode[1], mode[2]
        return (i / seg, (z - z0) / (z1 - z0))
    return (0.5, 0.5)


def revolve(name, profile, materials, cap_start, cap_end, seg=SEG, smooth_angle=38.0):
    """A solid of revolution. cap_start / cap_end: (mat, uv) for the flat
    discs closing the first and last rings."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for r, z, _, _ in profile:
        ring = []
        for i in range(seg):
            a = _angle(i, seg)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)

    for k in range(len(profile) - 1):
        r0, z0, mat, mode = profile[k]
        r1, z1 = profile[k + 1][:2]
        if abs(r0 - r1) < 1e-7 and abs(z0 - z1) < 1e-7:
            continue
        lo, hi = rings[k], rings[k + 1]
        for i in range(seg):
            j = (i + 1) % seg
            vs = [lo[i], lo[j], hi[j], hi[i]]
            ii = [i, i + 1, i + 1, i]
            f = bm.faces.new(vs)
            f.material_index = mat
            f.smooth = True
            for loop, v, idx in zip(f.loops, vs, ii):
                loop[uvl].uv = _uv(mode, v.co.x, v.co.y, v.co.z, idx, seg)

    for ring, (mat, mode) in ((rings[0], cap_start), (rings[-1], cap_end)):
        f = bm.faces.new(ring)
        f.material_index = mat
        f.smooth = False
        for loop in f.loops:
            c = loop.vert.co
            loop[uvl].uv = _uv(mode, c.x, c.y, c.z, 0, seg)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in materials:
        me.materials.append(m)
    # Smooth curved surfaces, keep the creases (cap edges) sharp.
    me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    return ob


# ----------------------------------------------------------------- parts

PRINT, GOLD = 0, 1


def body_profile():
    """Underside centre -> bottom double seam -> printed wall -> shoulder and
    neck (hidden under the lid) -> rolled neck edge -> inside wall -> inside
    floor. Materials: 0 = printed body, 1 = gold lacquer."""
    RB, RN, T = dims.RB, dims.RN, dims.T
    SH, SO = dims.SEAM_H, dims.SEAM_OUT
    wrap = ('wrap', dims.ART_Z0, dims.ART_Z1)
    flat = ('flat',)
    g = GOLD
    p = []
    # Underside: recessed bottom panel and its countersink down to the seam.
    p += [(RB - 0.30, dims.BOTTOM_Z, g, flat), (RB - 0.19, dims.BOTTOM_Z, g, flat)]
    p += arc(RB - 0.19, dims.BOTTOM_Z - 0.05, 0.05, 90, 0, 3, g, flat)[1:]
    p += [(RB - 0.14, 0.05, g, flat)]
    p += arc(RB - 0.09, 0.05, 0.05, 180, 270, 3, g, flat)[1:]
    # The double seam: flat foot, rounded outer corners, stands SO proud.
    p += arc(RB + SO - 0.07, 0.07, 0.07, 270, 360, 4, g, flat)
    p += arc(RB + SO - 0.08, SH - 0.08, 0.08, 0, 90, 5, g, flat)
    p += [(RB + 0.012, SH, g, flat), (RB + 0.002, SH + 0.006, g, flat)]
    # Printed wall, from the seam up to the shoulder.
    rs = dims.SHOULDER_R
    za = dims.Z_SHOULDER - rs
    p += [(RB, SH + 0.016, PRINT, wrap), (RB, za, PRINT, wrap)]
    # The shoulder rounds inwards to the neck just under the lid curl: the
    # curl overhangs it, so a narrow dark crease shows below the gold line.
    a_end = math.degrees(math.acos((RN - (RB - rs)) / rs))
    p += arc(RB - rs, za, rs, 0, a_end, 6, PRINT, wrap)[1:]
    # The neck, hidden under the lid.
    p += [(RN, dims.Z_SHOULDER + 0.03, PRINT, wrap), (RN, dims.Z_NECK, g, flat)]
    # Rolled top edge of the neck, then the inside, all gold lacquer.
    p += arc(RN - 0.035, dims.Z_NECK, 0.035, 0, 180, 6, g, flat)[1:]
    p += [(RN - 0.07, dims.Z_NECK - 0.06, g, flat), (RN - T - 0.02, dims.Z_NECK - 0.12, g, flat)]
    p += [(RN - T - 0.02, dims.INNER_BOTTOM_Z + 0.06, g, flat)]
    p += arc(RN - T - 0.08, dims.INNER_BOTTOM_Z + 0.06, 0.06, 0, -90, 3, g, flat)[1:]
    p += [(RN - T - 0.2, dims.INNER_BOTTOM_Z, g, flat)]
    return p


def lid_profile():
    """Top panel edge -> rounded shoulder -> skirt -> outward curl (gold) ->
    inside of the skirt and top (gold). Materials: 0 = printed lid, 1 = gold."""
    RL, T, LS = dims.RL, dims.T, dims.LID_SHOULDER
    cr = dims.CURL_R
    zc = dims.ZC
    planar = ('planar', RL)
    flat = ('flat',)
    p = []
    p += arc(RL - LS, dims.H - LS, LS, 90, 0, 10, PRINT, planar)
    # The skirt rolls outwards into a tube-like curl at its open edge: the
    # tube's inner side is the skirt's inner surface, so it stands about
    # 2 * CURL_R - T proud of the skirt. Unprinted, gold lacquered.
    cx = RL - T + cr
    a_join = math.degrees(math.acos((RL - cx) / cr))  # where the skirt meets the curl
    zj = zc + cr * math.sin(math.radians(a_join))
    p += [(RL, (dims.H - LS + zj) / 2, PRINT, planar), (RL, zj + 0.012, PRINT, planar)]
    p += arc(cx, zc, cr, a_join, -180, 18, GOLD, flat)
    p += [(RL - T, zc + 0.06, GOLD, flat), (RL - T, dims.H - LS, GOLD, flat)]
    p += arc(RL - LS, dims.H - LS, LS - T, 0, 90, 8, GOLD, flat)[1:]
    return p


def body(name, mats):
    return revolve(name, body_profile(), mats, cap_start=(GOLD, ('flat',)), cap_end=(GOLD, ('flat',)))


def lid(name, mats):
    """The lid, with its origin at the centre of its top (UVs are unchanged):
    place it at z = H to close the tin."""
    ob = revolve(name, lid_profile(), mats, cap_start=(PRINT, ('planar', dims.RL)), cap_end=(GOLD, ('flat',)))
    ob.data.transform(Matrix.Translation((0.0, 0.0, -dims.H)))
    ob.location.z = dims.H
    return ob


def tin_radius_at(z):
    """The closed-off body's outer radius at height z (None above the neck)."""
    if z < dims.SEAM_H:
        return dims.RB + dims.SEAM_OUT
    if z < dims.Z_SHOULDER - dims.SHOULDER_R:
        return dims.RB
    if z < dims.Z_SHOULDER:
        dz = z - (dims.Z_SHOULDER - dims.SHOULDER_R)
        return dims.RB - dims.SHOULDER_R + math.sqrt(max(0.0, dims.SHOULDER_R**2 - dz * dz))
    if z < dims.Z_NECK + 0.035:
        return dims.RN
    return None


def lean_lid(lid_ob, bearing, alpha, centre=(0.0, 0.0), tilt_art=0.0):
    """Stands the lid on its curled edge on the floor, top facing outwards
    along `bearing` (degrees from the front, towards +X), leaning back by
    `alpha` degrees against the open tin at `centre`; `tilt_art` turns the
    lid in its own plane (degrees, clockwise as seen from outside), since a
    round lid can be set down at any turn. Solves the position so it rests on
    the floor (min z = 0) and just touches the tin."""
    b = math.radians(bearing)
    a = math.radians(alpha)
    d = Vector((math.sin(b), -math.cos(b), 0.0))
    n = d * math.cos(a) + Vector((0, 0, 1)) * math.sin(a)
    up = -d * math.sin(a) + Vector((0, 0, 1)) * math.cos(a)
    # Turn the artwork a little within the lid's plane, if asked.
    t = math.radians(tilt_art)
    side = up.cross(n)
    up, side = up * math.cos(t) + side * math.sin(t), side * math.cos(t) - up * math.sin(t)
    rot = Matrix((side, up, n)).transposed().to_4x4()  # columns: art right, art up, top normal
    cx, cy = centre
    lid_ob.matrix_world = Matrix.Translation((cx + d.x * 9.0, cy + d.y * 9.0, 5.0)) @ rot
    bpy.context.view_layer.update()
    me = lid_ob.data
    mw = lid_ob.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    lid_ob.location.z -= min(p.z for p in pts)
    bpy.context.view_layer.update()
    for _ in range(3):
        mw = lid_ob.matrix_world
        gap = 1e9
        for v in me.vertices:
            p = mw @ v.co
            r = tin_radius_at(p.z)
            if r is None:
                continue
            gap = min(gap, math.hypot(p.x - cx, p.y - cy) - r)
        lid_ob.location.x -= d.x * (gap - 0.004)
        lid_ob.location.y -= d.y * (gap - 0.004)
        bpy.context.view_layer.update()
    return lid_ob
