"""Composite can geometry: solids of revolution with explicit UVs, in cm.

A profile is a list of (r, z) points traversed so that the visible side of the
surface lies to the right of the direction of travel in the r-z plane (going
up the outside wall, inwards across a top, down an inside wall). Faces are
wound to match, so normals point to the visible side without any guessing,
which matters for these open, sheet-like parts.

u runs counter-clockwise seen from above from the back (+Y): u = 0.5 is the
front centre (-Y), and the label strip reads left to right across the front.
"""

from __future__ import annotations

import math

import bmesh
import bpy

import dims

SEG = 256  # round the can: smooth silhouettes and highlights at any size


def _xy(r, u):
    a = math.radians(90.0 + 360.0 * u)
    return r * math.cos(a), r * math.sin(a)


def _finish(name, bm, materials, smooth_angle=38.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in materials:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    return ob


def arc(cx, cz, r, a0, a1, n):
    """Points on a circular arc from a0 to a1 (degrees), both ends included."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def dedupe(pts, eps=1e-6):
    out = []
    for p in pts:
        if not out or math.dist(p, out[-1]) > eps:
            out.append(p)
    return out


def revolve(name, profile, material, seg=SEG, smooth_angle=38.0, planar=None):
    """A surface of revolution from a profile. A point on the axis (r = 0)
    becomes a single vertex closed with a fan. With `planar` = R, UVs are a
    top-down projection over a disc of radius R (README "Caps": the image is
    the surface seen from above, the front edge at the bottom)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((0.0, 0.0, z))])
        else:
            rings.append([bm.verts.new((*_xy(r, i / seg), z)) for i in range(seg)])
    n = len(profile)
    for k in range(n - 1):
        a, b = rings[k], rings[k + 1]
        va, vb = k / (n - 1), (k + 1) / (n - 1)
        for i in range(seg):
            j = (i + 1) % seg
            if len(b) == 1:
                vs, uvs = [a[i], a[j], b[0]], [(i / seg, va), ((i + 1) / seg, va), ((i + 0.5) / seg, vb)]
            elif len(a) == 1:
                vs, uvs = [a[0], b[j], b[i]], [((i + 0.5) / seg, va), ((i + 1) / seg, vb), (i / seg, vb)]
            else:
                vs = [a[i], a[j], b[j], b[i]]
                uvs = [(i / seg, va), ((i + 1) / seg, va), ((i + 1) / seg, vb), (i / seg, vb)]
            f = bm.faces.new(vs)
            for loop, uv in zip(f.loops, uvs):
                if planar:
                    c = loop.vert.co
                    uv = (0.5 + c.x / (2 * planar), 0.5 + c.y / (2 * planar))
                loop[uvl].uv = uv
    return _finish(name, bm, [material], smooth_angle)


# ----------------------------------------------------------------- parts


def paper_tube(name, material):
    """The labelled tube. The label's outer end overlaps its start at the back
    by LABEL_OVERLAP: that strip stands LABEL_T proud, ramping up over the
    buried start edge at u = 0 and ending in a crisp step."""
    R, t = dims.R, dims.LABEL_T
    uo = dims.LABEL_OVERLAP / dims.CIRC
    cols = [(0.0, 0.0), (0.0025, t)]
    i = 1
    while i / SEG < uo:
        cols.append((i / SEG, t))
        i += 1
    cols += [(uo, t), (uo, 0.0)]
    while i < SEG:
        if i / SEG > uo + 1e-6:
            cols.append((i / SEG, 0.0))
        i += 1
    z0, z1 = dims.TUBE_Z0, dims.TUBE_Z1
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    lo = [bm.verts.new((*_xy(R + dr, u), z0)) for u, dr in cols]
    hi = [bm.verts.new((*_xy(R + dr, u), z1)) for u, dr in cols]
    n = len(cols)
    for k in range(n):
        m = (k + 1) % n
        u0 = cols[k][0]
        u1 = cols[m][0] if m else 1.0
        f = bm.faces.new([lo[k], lo[m], hi[m], hi[k]])
        for loop, uv in zip(f.loops, [(u0, 0.0), (u1, 0.0), (u1, 1.0), (u0, 1.0)]):
            loop[uvl].uv = uv
    return _finish(name, bm, [material], smooth_angle=30.0)


def seam_profile():
    """Top double seam and ring, from the curl's tip tucked under the paper,
    out and up over the seam, down the countersink wall, then in across the
    flange to the aperture's rolled edge."""
    H, SR, lip = dims.H, dims.SEAM_R, dims.SEAM_LIP
    zb = H - dims.SEAM_H + 0.005  # underside of the seam
    ch = dims.CHUCK_R
    fz = dims.FLANGE_Z - 0.01  # flange surface under the foil
    p = [(lip, zb), (SR - 0.04, zb)]
    p += arc(SR - 0.04, zb + 0.04, 0.04, 270, 360, 4)
    p += arc(SR - 0.08, H - 0.08, 0.08, 0, 90, 7)
    p += arc(ch + 0.075, H - 0.07, 0.07, 90, 180, 6)
    p += [(ch - 0.01, H - 0.2), (ch - 0.02, fz + 0.06)]
    p += arc(ch - 0.07, fz + 0.05, 0.05, 0, -90, 4)
    p += [(dims.APERTURE_R + 0.04, fz)]
    p += arc(dims.APERTURE_R + 0.04, fz - 0.035, 0.035, 90, 180, 4)
    p += [(dims.APERTURE_R + 0.005, fz - 0.1)]
    return dedupe(p)


def top_ring(name, gold):
    return revolve(name, seam_profile(), gold)


def bottom_end(name, gold):
    """The bottom end: the same seam, mirrored, with a plain recessed panel."""
    p = seam_profile()
    k = next(i for i, (r, z) in enumerate(p) if abs(r - (dims.APERTURE_R + 0.04)) < 1e-6)
    fz = p[k][1]
    p = p[: k + 1]
    # A shallow expansion bead in the panel, then flat to the centre.
    p += [(2.75, fz), (2.62, fz + 0.03), (2.5, fz), (0.0, fz)]
    mirrored = [(r, dims.H - z) for r, z in reversed(dedupe(p))]
    return revolve(name, mirrored, gold)


def foil(name, material):
    """The peel-off foil membrane: sealed flat on the flange, bulging a touch
    over the aperture."""
    z = dims.FLANGE_Z
    R, a = dims.FOIL_R, dims.APERTURE_R
    p = [(R, z - 0.008), (R, z)]
    for i in range(0, 13):
        r = a * (1 - i / 12)
        s = (r / a) ** 2
        p.append((r, z + dims.FOIL_DOME * (1 - s) ** 1.5))
    return revolve(name, dedupe(p), material, planar=R)


def pull_tab(name, material):
    """The foil's pull tab, folded back over the membrane at the rim: a thin
    tongue with a straight fold edge and a rounded free end, springing up a
    few degrees from the fold as a folded foil tab does."""
    w, d = dims.TAB
    th = 0.018  # two layers of lacquered foil, a touch generous
    rr, rf = 0.26, 0.03  # corner radii: free end, fold end
    # Outline counter-clockwise from above: fold edge along y = 0, the tongue
    # reaching towards -y.
    pts = [(-w / 2 + rf, 0.0)]
    pts += arc(-w / 2 + rf, -rf, rf, 90, 180, 3)[1:]
    pts += arc(-w / 2 + rr, -d + rr, rr, 180, 270, 8)
    pts += arc(w / 2 - rr, -d + rr, rr, 270, 360, 8)
    pts += arc(w / 2 - rf, -rf, rf, 0, 90, 3)
    pts = dedupe(pts)
    if math.dist(pts[0], pts[-1]) < 1e-6:
        pts.pop()
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    lo = [bm.verts.new((x, y, 0.0)) for x, y in pts]
    hi = [bm.verts.new((x, y, th)) for x, y in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    bm.faces.new(hi)
    bm.faces.new(list(reversed(lo)))
    for f in bm.faces:
        for loop in f.loops:
            loop[uvl].uv = (0.5 + loop.vert.co.x / w, 1.0 + loop.vert.co.y / d)
    ob = _finish(name, bm, [material], smooth_angle=38.0)
    a = math.radians(dims.TAB_AT)
    r = dims.FOIL_R - 0.06
    ob.rotation_euler = (math.radians(-dims.TAB_LIFT), 0.0, a + math.pi)
    ob.location = (r * math.sin(a), -r * math.cos(a), dims.FLANGE_Z + 0.001)
    return ob
