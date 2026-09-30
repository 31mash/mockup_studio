"""An open SOS paper bag (square bottom, side gussets) as one sheet of kraft.

The walls are a single grid over (s, z): s runs around the bag counter-
clockwise seen from above, starting at the front panel's left edge (front,
right gusset, back, left gusset), z runs up. At every height the cross-section
keeps the paper's true width: when the gussets fold inward towards the open
top, the front and back panels are drawn closer together instead of the
paper stretching. The folds are slightly rounded, the top edge is pinked,
and a Solidify modifier gives the sheet its thickness. The square bottom is a
separate flat piece inside the walls.
"""

from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector, noise

import dims

W, D, H = dims.W, dims.D, dims.H
P = 2 * W + 2 * D  # the paper tube's circumference
# Arc-length positions of the vertical folds: panel corners and gusset centres.
FOLDS = [0.0, W, W + D / 2, W + D, 2 * W + D, 2 * W + 1.5 * D, P]
CORNERS = [0.0, W, W + D, 2 * W + D, P]
GUSSET_CENTRES = [W + D / 2, 2 * W + 1.5 * D]


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def gusset_in(z: float) -> float:
    """How far each gusset's centre fold is pushed into the bag at height z."""
    if z <= dims.GUSSET_START:
        return 0.0
    if z <= dims.CREASE_Z:
        t = (z - dims.GUSSET_START) / (dims.CREASE_Z - dims.GUSSET_START)
        return dims.GUSSET_IN_CREASE * t ** 1.6
    t = (z - dims.CREASE_Z) / (H - dims.CREASE_Z)
    return dims.GUSSET_IN_CREASE + (dims.GUSSET_IN_TOP - dims.GUSSET_IN_CREASE) * t


def section(z: float):
    """Sharp-cornered cross-section at height z: (arc position, point) pairs."""
    g = gusset_in(z)
    h = math.sqrt(max(0.0, (D / 2) ** 2 - g * g))
    pts = [
        (-W / 2, -h), (W / 2, -h), (W / 2 - g, 0.0), (W / 2, h),
        (-W / 2, h), (-W / 2 + g, 0.0), (-W / 2, -h),
    ]
    return list(zip(FOLDS, pts))


def _lerp_section(sec, s: float):
    s = s % P
    for (s0, p0), (s1, p1) in zip(sec, sec[1:]):
        if s0 <= s <= s1:
            t = (s - s0) / (s1 - s0)
            return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)
    return sec[0][1]


def point(sec, s: float):
    """A point on the section with its folds rounded (radius FOLD_R)."""
    r = dims.FOLD_R
    for f in FOLDS:
        if abs(s - f) < r:
            a = _lerp_section(sec, f - r)
            c = _lerp_section(sec, f)
            b = _lerp_section(sec, f + r)
            t = (s - (f - r)) / (2 * r)
            return tuple((1 - t) ** 2 * a[i] + 2 * (1 - t) * t * c[i] + t * t * b[i] for i in range(2))
    return _lerp_section(sec, s)


def panel_of(s: float):
    """(panel name, local coordinate from the panel's start, panel width)."""
    s = s % P
    if s < W:
        return 'front', s, W
    if s < W + D:
        return 'right', s - W, D
    if s < 2 * W + D:
        return 'back', s - W - D, W
    return 'left', s - 2 * W - D, D


def columns():
    """Arc positions of the grid columns: every half pinking tooth, plus
    extra columns to round each fold."""
    n = round(P / (dims.PINK_PERIOD / 2))
    ds = P / n
    cols = [i * ds for i in range(n)]
    r = dims.FOLD_R
    for f in FOLDS[:-1]:
        for o in (-r, -r / 2, 0.0, r / 2, r):
            cols.append((f + o) % P)
    cols.sort()
    out = []
    for c in cols:
        if not out or c - out[-1] > 0.012:
            out.append(c)
    if P - out[-1] < 0.012:
        out.pop()
    return out, ds * 2  # the tooth period actually used


def rows():
    zs = []
    z = 0.0
    while z < dims.GUSSET_START + 0.6:  # fine rows for the bottom creases
        zs.append(z)
        z += 0.16
    while z < dims.CREASE_Z - 0.4:
        zs.append(z)
        z += 0.3
    zs += [dims.CREASE_Z + o for o in (-0.3, -0.15, -0.06, 0.0, 0.06, 0.15, 0.3)]
    z = dims.CREASE_Z + 0.5
    while z < H - 0.3:
        zs.append(z)
        z += 0.2
    zs += [H - 0.14]
    return sorted(set(round(v, 4) for v in zs))


def fold_distance(s: float) -> float:
    s = s % P
    return min(abs(s - f) for f in FOLDS)


def displacement(s: float, z: float) -> float:
    """Outward offset of the paper from its ideal shape: a gentle bow in the
    wide panels, soft irregular undulation, and the SOS gusset's two
    diagonal bottom creases."""
    name, u, width = panel_of(s)
    edge = smoothstep(0.0, 0.9, fold_distance(s))
    base = smoothstep(0.0, 2.2, z)
    d = 0.0
    if name in ('front', 'back'):
        d += 0.09 * math.sin(math.pi * u / width) * smoothstep(2.0, 9.0, z)
    wob = noise.noise(Vector((s * 0.28, z * 0.2, 3.7))) * 0.09
    wob += noise.noise(Vector((s * 0.9, z * 0.7, 11.2))) * 0.016
    if z > dims.CREASE_Z:
        wob += noise.noise(Vector((s * 0.7, 5.0, 1.3))) * 0.05 * smoothstep(dims.CREASE_Z, H, z)
    d += wob * edge * base
    # The crease left by folding the top over once: a soft mountain fold.
    d += 0.022 * math.exp(-(((z - dims.CREASE_Z) / 0.07) ** 2)) * smoothstep(0.0, 0.3, fold_distance(s))
    if name in ('left', 'right'):
        t = abs(u - D / 2)  # distance from the gusset's centre line
        line = D / 2 - t  # the diagonal crease's height here
        groove = math.exp(-(((z - line) / 0.11) ** 2)) * (1 - smoothstep(D / 2 - 0.3, D / 2 + 0.2, z))
        d -= 0.03 * groove * smoothstep(0.0, 0.3, t) * smoothstep(0.0, 0.4, D / 2 - t + 0.4)
        # The centre fold from flat-packing, a soft valley above the creases' apex.
        d -= 0.035 * math.exp(-((t / 0.09) ** 2)) * smoothstep(D / 2 - 0.2, D / 2 + 0.6, z)
    return d


def top_z(s: float, period: float) -> float:
    """The pinked top edge: a triangle wave, peaks every `period`."""
    f = (s / period) % 1.0
    tri = abs(2 * f - 1)  # 1 at a peak, 0 mid-way
    return H - dims.PINK_DEPTH * (1 - tri)


def build_walls(name: str, mats: dict) -> bpy.types.Object:
    """mats: front, plain, back, inside, edge (the cut edge)."""
    cols, period = columns()
    zs = rows()
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    grid = []
    for j, z in enumerate(zs + [None]):
        row = []
        for s in cols:
            zz = top_z(s, period) if z is None else z
            sec = section(zz)
            x, y = point(sec, s)
            a = point(sec, s - 0.01)
            b = point(sec, s + 0.01)
            tx, ty = b[0] - a[0], b[1] - a[1]
            L = math.hypot(tx, ty) or 1.0
            nx, ny = ty / L, -tx / L  # outward, for a CCW outline
            d = displacement(s, zz)
            row.append(bm.verts.new((x + nx * d, y + ny * d, zz)))
        grid.append(row)

    slot = {'front': 0, 'right': 1, 'back': 2, 'left': 1}
    n = len(cols)
    all_z = zs + [H]
    for j in range(len(grid) - 1):
        for k in range(n):
            k2 = (k + 1) % n
            s0 = cols[k]
            s1 = cols[k2] if k2 else P
            f = bm.faces.new((grid[j][k], grid[j][k2], grid[j + 1][k2], grid[j + 1][k]))
            pname, u0, width = panel_of((s0 + s1) / 2)
            f.material_index = slot[pname]
            f.smooth = True
            start = {'front': 0.0, 'right': W, 'back': W + D, 'left': 2 * W + D}[pname]
            for loop, (ss, jj) in zip(f.loops, ((s0, j), (s1, j), (s1, j + 1), (s0, j + 1))):
                zz = loop.vert.co.z
                loop[uv].uv = ((ss - start) / width, zz / H)

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    inside, edge = mats['inside'], mats['edge']
    for m in (mats['front'], mats['plain'], mats['back'], inside, inside, inside, edge, edge, edge):
        me.materials.append(m)

    sol = ob.modifiers.new('paper', 'SOLIDIFY')
    sol.thickness = dims.PAPER
    sol.offset = -1.0  # grow inward: the modelled surface is the outside
    sol.use_even_offset = True
    sol.use_quality_normals = True
    sol.use_rim = True
    sol.material_offset = 3
    sol.material_offset_rim = 6
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
    # Solidify's inner shell dips a few microns below the base; rest the
    # finished sheet exactly on the floor.
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    low = min(v.co.z for v in ev.to_mesh().vertices)
    ev.to_mesh_clear()
    ob.location.z -= low
    return ob
