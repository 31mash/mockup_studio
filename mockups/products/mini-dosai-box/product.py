"""Mini Dosai: IndiGo's matchbox-style dosa pack. A printed cream paperboard
sleeve lying flat, printed face up, with its white card drawer pulled out
towards the front (-Y); in the drawer, a pleated aluminium foil tray holding
folded mini dosai. Variants: 'chicken' (red print, a hen) and 'veg' (green
print, a potato plant), and 'pair' with both side by side."""

import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402


def _guard_studio_reset():
    """Workaround for a studio bug hit by any product with VARIANTS: after
    core.reset() empties the scene, core._ORIGIN still points at the removed
    light-target empty, and core.studio() raises ReferenceError on it when
    render.py rebuilds for the next variant. Clearing it after each reset
    lets studio() make a fresh one. Changes nothing else; remove once
    studio/core.py resets _ORIGIN itself."""
    from studio import core

    if getattr(core.reset, 'clears_origin', False):
        return
    original = core.reset

    def reset():
        original()
        core._ORIGIN = None

    reset.clears_origin = True
    core.reset = reset


_guard_studio_reset()

TITLE = 'Mini Dosai box'
VARIANTS = [None, 'veg', 'pair']
SHOTS = [
    'hero',
    'hero-right',
    {'name': 'front', 'preset': 'front', 'elevation': 30, 'fill': 0.5},
    'top',
    {'name': 'low', 'preset': 'low', 'elevation': 16, 'azimuth': 34},
    {'name': 'veg-hero', 'preset': 'hero', 'variant': 'veg'},
    {'name': 'pair-hero', 'preset': 'hero', 'variant': 'pair', 'fill': 0.62},
    {'name': 'pair-top', 'preset': 'top', 'variant': 'pair', 'fill': 0.52},
]


# ----------------------------------------------------------------- helpers


def _new_object(name, bm, mats, smooth_angle=40.0):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in mats:
        me.materials.append(m)
    # Smooth shading with sharp creases above the angle (no operator, so no
    # dependence on the active object).
    for p in me.polygons:
        p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    return ob


def _section(w, h, r, z0=0.0, seg=dims.FOLD_SEG):
    """Cross-section of the sleeve (x, z), starting at the bottom centre and
    heading towards -X, then up the left side, across the top and down the
    right side, as dims.sleeve_layout.
    Returns points (without the closing duplicate) and the arc length at each
    point plus the total at the end."""
    hw = w / 2
    pts = [(0.0, z0)]

    def arc(cx, cz, a0, a1):
        for i in range(1, seg + 1):
            a = math.radians(a0 + (a1 - a0) * i / seg)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))

    pts.append((-hw + r, z0))
    arc(-hw + r, z0 + r, -90, -180)
    pts.append((-hw, z0 + h - r))
    arc(-hw + r, z0 + h - r, 180, 90)
    pts.append((hw - r, z0 + h))
    arc(hw - r, z0 + h - r, 90, 0)
    pts.append((hw, z0 + r))
    arc(hw - r, z0 + r, 0, -90)
    # Drop duplicates where a straight run has zero length.
    clean = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, clean[-1]) > 1e-6:
            clean.append(p)
    acc = [0.0]
    for i in range(1, len(clean) + 1):
        acc.append(acc[-1] + math.dist(clean[i - 1], clean[i % len(clean)]))
    return clean, acc


def sleeve(name, art_mat, inside_mat, edge_mat, x=0.0):
    """The printed tube: outside with the wrap-strip artwork, the unprinted
    inside, and the cut card edges at both open ends."""
    W, H, L, T, R = dims.W, dims.H, dims.L, dims.T, dims.R
    outer, acc = _section(W, H, R)
    inner, _ = _section(W - 2 * T, H - 2 * T, R - T * 0.9, z0=T)
    assert len(outer) == len(inner)
    total = acc[-1]
    y0, y1 = -L / 2, L / 2
    n = len(outer)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    o0 = [bm.verts.new((x + px, y0, pz)) for px, pz in outer]
    o1 = [bm.verts.new((x + px, y1, pz)) for px, pz in outer]
    i0 = [bm.verts.new((x + px, y0, pz)) for px, pz in inner]
    i1 = [bm.verts.new((x + px, y1, pz)) for px, pz in inner]

    def quad(vs, uvs, mat):
        f = bm.faces.new(vs)
        f.material_index = mat
        for loop, c in zip(f.loops, uvs):
            loop[uv].uv = c
        return f

    for i in range(n):
        j = (i + 1) % n
        ua, ub = acc[i] / total, acc[i + 1] / total
        quad([o0[i], o1[i], o1[j], o0[j]], [(ua, 0), (ua, 1), (ub, 1), (ub, 0)], 0)
        quad([i0[i], i0[j], i1[j], i1[i]], [(ua, 0), (ub, 0), (ub, 1), (ua, 1)], 1)
        quad([o0[i], o0[j], i0[j], i0[i]], [(ua, 0), (ub, 0), (ub, 0.02), (ua, 0.02)], 2)
        quad([o1[i], i1[i], i1[j], o1[j]], [(ua, 0), (ua, 0.02), (ub, 0.02), (ub, 0)], 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _new_object(name, bm, [art_mat, inside_mat, edge_mat], smooth_angle=35)


def drawer(name, mat, x, y_front, z0):
    """The white card drawer: an open box of folded board, softly rounded."""
    w, l, h = dims.DW, dims.DL, dims.DH
    bm = bmesh.new()
    A, B, C, D = (x - w / 2, y_front), (x + w / 2, y_front), (x + w / 2, y_front + l), (x - w / 2, y_front + l)
    v0 = {k: bm.verts.new((p[0], p[1], z0)) for k, p in zip('ABCD', (A, B, C, D))}
    v1 = {k: bm.verts.new((p[0], p[1], z0 + h)) for k, p in zip('ABCD', (A, B, C, D))}
    bm.faces.new([v0['A'], v0['D'], v0['C'], v0['B']])
    for a, b in ('AB', 'BC', 'CD', 'DA'):
        bm.faces.new([v0[a], v0[b], v1[b], v1[a]])
    ob = _new_object(name, bm, [mat], smooth_angle=30)
    so = ob.modifiers.new('card', 'SOLIDIFY')
    so.thickness = dims.DWALL
    so.offset = -1.0
    so.use_even_offset = True
    bv = ob.modifiers.new('round', 'BEVEL')
    bv.width = 0.03
    bv.segments = 3
    bv.limit_method = 'ANGLE'
    bv.harden_normals = False
    return ob


def _rrect(w, d, r, seg):
    """Rounded rectangle outline (CCW from above) with, per point, its
    phase along its corner arc (0..1) for the foil pleats, and outward normal."""
    hw, hd = w / 2, d / 2
    out = []
    for (cx, cy), a0 in (((hw - r, -hd + r), -90), ((hw - r, hd - r), 0), ((-hw + r, hd - r), 90), ((-hw + r, -hd + r), 180)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            out.append((cx + r * math.cos(a), cy + r * math.sin(a), i / seg, math.cos(a), math.sin(a)))
    return out


def foil_tray(ctx, name, mat, x, y, z0):
    """A rectangular aluminium container: tapered walls with pleated corners,
    a flat rim and a rolled edge."""
    seg = 28
    pleats = 7
    rim_w = dims.TRAY_W - 2 * (dims.FLANGE + dims.BEAD)
    rim_l = dims.TRAY_L - 2 * (dims.FLANGE + dims.BEAD)
    rim_r = max(0.3, dims.TRAY_R - dims.FLANGE - dims.BEAD)
    dr = dims.TRAY_DRAFT
    fil = 0.22  # floor fillet
    h = dims.TRAY_H
    rings = []  # (w, l, r, z, pleat amplitude radial, pleat amplitude z)
    rings.append((rim_w - 2 * dr - 2 * fil, rim_l - 2 * dr - 2 * fil, max(0.2, rim_r - dr - fil), 0.0, 0.0, 0.0))
    for k in range(1, 4):
        a = math.radians(90 * k / 3)
        off = fil * (1 - math.sin(a)) + dr
        rings.append((rim_w - 2 * off, rim_l - 2 * off, max(0.2, rim_r - off), fil * (1 - math.cos(a)), 0.0, 0.0))
    for k in range(1, 7):
        t = k / 6
        off = dr * (1 - t)
        rings.append((rim_w - 2 * off, rim_l - 2 * off, rim_r - off, fil + (h - fil) * t, 0.035 * t ** 1.5, 0.0))
    for k in range(1, 4):
        f = dims.FLANGE * k / 3
        rings.append((rim_w + 2 * f, rim_l + 2 * f, rim_r + f, h, 0.03, 0.022 * (k / 3)))
    bm = bmesh.new()
    vrings = []
    for rw, rl, rr, rz, amp, zamp in rings:
        ring = []
        for px, py, ph, nx, ny in _rrect(rw, rl, rr, seg):
            s = math.sin(ph * math.pi * pleats * 2)
            ring.append(bm.verts.new((x + px + nx * amp * s, y + py + ny * amp * s, z0 + rz + zamp * s)))
        vrings.append(ring)
    bm.faces.new(list(reversed(vrings[0])))
    n = len(vrings[0])
    for a, b in zip(vrings[:-1], vrings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([a[i], a[j], b[j], b[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _new_object(name, bm, [mat], smooth_angle=60)
    so = ob.modifiers.new('foil', 'SOLIDIFY')
    so.thickness = 0.012
    so.offset = 0.0
    # Rolled edge round the rim.
    edge = [(x + px, y + py) for px, py, *_ in _rrect(rim_w + 2 * dims.FLANGE + dims.BEAD * 0.8, rim_l + 2 * dims.FLANGE + dims.BEAD * 0.8, rim_r + dims.FLANGE, 12)]
    bead = ctx.shapes.torus_ring(name + '-bead', edge, z0 + h - dims.BEAD * 0.75, dims.BEAD, mat, seg=10)
    return [ob, bead]


def dosa_material(ctx, name='dosa'):
    """A crisp dosa, procedurally, matched to the photo's piece: an orange-
    golden crepe (about #c87f38 printed flat) mottled with deeper browning,
    a lacy network where the batter caught, and a dense scatter of small dark
    specks (browned pores and podi). Relief: the specks are tiny pits, the
    lace a slight ridge, plus a soft undulation. A thin sheen of ghee."""
    m = ctx.mat.solid(name, '#c98035', roughness=0.5)
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    N = nt.nodes.new
    L = nt.links.new
    coord = N('ShaderNodeTexCoord').outputs['Object']

    def noise(scale, detail=4.0, rough=0.55, distortion=0.0, vec=None):
        n = N('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        n.inputs['Distortion'].default_value = distortion
        L(vec or coord, n.inputs['Vector'])
        return n.outputs['Fac']

    def ramp(src, stops, interp='LINEAR'):
        r = N('ShaderNodeValToRGB')
        r.color_ramp.interpolation = interp
        els = r.color_ramp.elements
        while len(els) < len(stops):
            els.new(0.5)
        for e, (pos, col) in zip(els, stops):
            e.position = pos
            e.color = ctx.core.rgba(col) if isinstance(col, str) else (col, col, col, 1)
        L(src, r.inputs['Fac'])
        return r.outputs['Color']

    def mix(a, b, fac):
        mx = N('ShaderNodeMix')
        mx.data_type = 'RGBA'
        L(fac, mx.inputs['Factor'])
        L(a, mx.inputs['A'])
        L(b, mx.inputs['B'])
        return mx.outputs['Result']

    def math_(op, a, b=None):
        n = N('ShaderNodeMath')
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs['Value']

    # Warp the coordinates a little so nothing reads as a regular pattern.
    warp = N('ShaderNodeTexNoise')
    warp.inputs['Scale'].default_value = 1.4
    warp.inputs['Detail'].default_value = 2.0
    L(coord, warp.inputs['Vector'])
    wv = N('ShaderNodeVectorMath')
    wv.operation = 'MULTIPLY_ADD'
    L(warp.outputs['Color'], wv.inputs[0])
    wv.inputs[1].default_value = (0.35, 0.35, 0.35)
    L(coord, wv.inputs[2])
    wc = wv.outputs['Vector']

    def specks(scale, size, keep, seed_off):
        """Round dark dots from a Voronoi field: `size` is the dot radius as a
        fraction of the cell, `keep` the share of cells that get one."""
        v = N('ShaderNodeTexVoronoi')
        v.voronoi_dimensions = '4D'
        v.inputs['Scale'].default_value = scale
        v.inputs['W'].default_value = seed_off
        v.inputs['Randomness'].default_value = 1.0
        L(wc, v.inputs['Vector'])
        # Dot radius varies per cell.
        sep = N('ShaderNodeSeparateColor')
        L(v.outputs['Color'], sep.inputs['Color'])
        r = math_('MULTIPLY_ADD', sep.outputs['Green'], size * 0.8)
        L_in = r.node.inputs
        L_in[2].default_value = size * 0.6
        edge = math_('SUBTRACT', r, v.outputs['Distance'])
        dot = math_('MULTIPLY', edge, 6.0 / size)
        dot = math_('MINIMUM', math_('MAXIMUM', dot, 0.0), 1.0)
        on = math_('LESS_THAN', sep.outputs['Red'], keep)
        return math_('MULTIPLY', dot, on)

    broad = noise(0.7, 3.0)
    patch = noise(2.4, 5.0, 0.62, distortion=0.4)
    lace_n = noise(7.0, 6.0, 0.66, distortion=1.1, vec=wc)

    # Base: golden where thin, deeper amber where it browned.
    base = ramp(broad, [(0.3, '#f6ab50'), (0.52, '#eb9439'), (0.75, '#d57e2c')])
    amber = ramp(broad, [(0.2, '#bf601c'), (0.8, '#a44f16')])
    col = mix(base, amber, ramp(patch, [(0.45, 0.0), (0.74, 0.65)]))
    # Pale golden flecks where the batter bubbled thin.
    pale = ramp(broad, [(0.0, '#f3bf6e'), (1.0, '#e9ad5c')])
    col = mix(col, pale, ramp(noise(11.0, 3.0, 0.5, vec=wc), [(0.62, 0.0), (0.7, 0.55)]))
    # Lace: a fine brown network.
    lace = ramp(lace_n, [(0.44, 0.0), (0.52, 0.85), (0.6, 0.0)])
    lace_col = ramp(broad, [(0.0, '#8c3f10'), (1.0, '#74330c')])
    col = mix(col, lace_col, lace)
    # Specks: many small, some larger.
    s1 = specks(4.0, 0.22, 0.85, 0.3)
    s2 = specks(2.0, 0.15, 0.6, 7.7)
    s3 = specks(8.0, 0.24, 0.55, 3.3)
    sp = math_('MAXIMUM', math_('MAXIMUM', s1, s2), s3)
    dark = ramp(broad, [(0.0, '#5a250a'), (1.0, '#441c07')])
    col = mix(col, dark, math_('MULTIPLY', sp, 0.92))
    L(col, p.inputs['Base Color'])

    # Relief.
    b1 = N('ShaderNodeBump')
    b1.inputs['Strength'].default_value = 0.45
    b1.inputs['Distance'].default_value = 0.012
    b1.invert = True
    L(sp, b1.inputs['Height'])
    b2 = N('ShaderNodeBump')
    b2.inputs['Strength'].default_value = 0.25
    b2.inputs['Distance'].default_value = 0.01
    L(lace, b2.inputs['Height'])
    b3 = N('ShaderNodeBump')
    b3.inputs['Strength'].default_value = 0.3
    b3.inputs['Distance'].default_value = 0.05
    L(noise(3.0, 6.0, 0.6), b3.inputs['Height'])
    L(b3.outputs['Normal'], b2.inputs['Normal'])
    L(b2.outputs['Normal'], b1.inputs['Normal'])
    L(b1.outputs['Normal'], p.inputs['Normal'])
    # Ghee: glossier in patches, matt in the dark specks.
    rough = ramp(patch, [(0.3, 0.38), (0.75, 0.58)])
    rough = mix(rough, ramp(sp, [(0.0, 0.7), (1.0, 0.7)]), sp)
    L(rough, p.inputs['Roughness'])
    p.inputs['Specular IOR Level'].default_value = 0.36
    return m


def dosa_parcel(name, mat, x, y_front, z_floor, seed):
    """A mini dosa rolled round its filling, flattened and lying across the
    tray, as in the photo: a rounded-rectangle section, both ends tucked
    under, and the crepe's outer edge showing as a thin lap along the front
    shoulder. Slightly irregular. Placed with its front-most point at
    y_front, resting on z_floor; returns the object and its back-most y."""
    import random

    from mathutils import Vector
    from mathutils.noise import noise

    rnd = random.Random(seed * 7919 + 13)
    A = dims.PIECE_L / 2 * (1 + rnd.uniform(-0.03, 0.015))
    B = dims.PIECE_D / 2 * (1 + rnd.uniform(-0.04, 0.02))
    C = dims.PIECE_H / 2 * (1 + rnd.uniform(-0.05, 0.03))
    E = 1.05  # length of each rounded, tucked end
    ex = 3.5  # section squareness (2 = ellipse)
    lap = 0.075  # crepe thickness: the step at its outer edge
    seam0 = math.radians(128 + rnd.uniform(-8, 8))  # front shoulder
    bow = rnd.uniform(-0.09, 0.09)
    yaw = math.radians(rnd.uniform(-1.6, 1.6))
    pivot = 0.28 * C  # the tucked ends fold down towards the floor

    # Rows along x: dense on the rounded ends.
    xs = []
    for i in range(12):
        a = math.radians(84) * (1 - i / 12)
        xs.append((-(A - E + E * math.sin(a)), math.cos(a)))
    for i in range(41):
        xs.append((-(A - E) + 2 * (A - E) * i / 40, 1.0))
    for i in range(1, 13):
        a = math.radians(84) * i / 12
        xs.append(((A - E + E * math.sin(a)), math.cos(a)))

    nsec = 132
    span = 2 * math.pi - 0.012  # the last column sits just short of the lap edge
    rows = []
    for xx, s in xs:
        sy = s ** 0.42
        sz = s ** 0.85
        seam = seam0 + 0.1 * noise(Vector((xx * 0.8 + seed, 0.3, 1.7)))
        row = []
        for k in range(nsec):
            psi = span * k / (nsec - 1)
            phi = seam - psi
            c, sn = math.cos(phi), math.sin(phi)
            py = B * math.copysign(abs(c) ** (2 / ex), c)
            pz = C * math.copysign(abs(sn) ** (2 / ex), sn)
            # The outer layer ends at the seam: one crepe thickness higher
            # just after it, winding down to the layer below all the way round.
            rad = math.hypot(py, pz) or 1e-6
            off = lap * (1 - psi / (2 * math.pi)) + 0.025 * math.exp(-psi / 0.09)  # the loose edge lifts a little
            wob = 0.05 * noise(Vector((xx * 0.7 + seed * 3.1, py * 0.8, pz * 0.8))) + 0.018 * noise(Vector((xx * 2.6, py * 2.6 + seed, pz * 2.6)))
            # Folds where the crepe is tucked under at the ends.
            fold = 0.045 * (1 - s) ** 0.8 * math.sin(7 * phi + 2.5 * noise(Vector((xx * 0.4, seed * 1.3, 0.0))))
            f = 1 + (off + wob + fold) / rad
            py, pz = py * f * sy, pz * f
            # Ends: the section shrinks towards a low pivot.
            zz = C + pz
            zz = pivot + (zz - pivot) * sz
            # Soft flat where it rests on the floor.
            if zz < 0.22:
                zz = 0.22 - (0.22 - zz) * 0.35
            yy = py + bow * (1 - (xx / A) ** 2)
            row.append((xx * math.cos(yaw) - yy * math.sin(yaw), xx * math.sin(yaw) + yy * math.cos(yaw), zz))
        rows.append(row)
    pts = [p for row in rows for p in row]
    ymin = min(p[1] for p in pts)
    ymax = max(p[1] for p in pts)
    zmin = min(p[2] for p in pts)
    dy = y_front - ymin
    dz = z_floor - zmin + 0.002

    bm = bmesh.new()
    grid = [[bm.verts.new((x + px, py + dy, pz + dz)) for px, py, pz in row] for row in rows]
    for a, b in zip(grid[:-1], grid[1:]):
        for k in range(nsec):
            j = (k + 1) % nsec
            bm.faces.new([a[k], a[j], b[j], b[k]])
    # Close each end with a small fan.
    for ring, sgn in ((grid[0], -1), (grid[-1], 1)):
        cx = sum(v.co.x for v in ring) / nsec
        cy = sum(v.co.y for v in ring) / nsec
        cz = sum(v.co.z for v in ring) / nsec
        pole = bm.verts.new((cx + sgn * 0.035, cy, cz))
        for k in range(nsec):
            j = (k + 1) % nsec
            bm.faces.new([ring[k], ring[j], pole] if sgn > 0 else [ring[j], ring[k], pole])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = _new_object(name, bm, [mat], smooth_angle=55)
    return ob, y_front + (ymax - ymin)


# ----------------------------------------------------------------- product


def pack(ctx, variant, x=0.0, suffix=''):
    m = ctx.mat
    art = m.board(f'sleeve {variant}{suffix}', art=ctx.art(f'sleeve-{variant}.png'), roughness=0.6, coat=0.08, tooth=0.04)
    inside = m.board('board inside' + suffix, color='#e9e5da', roughness=0.8, coat=0.0, tooth=0.05)
    edge = m.board('board edge' + suffix, color='#d8d0bf', roughness=0.85, coat=0.0, tooth=0.08)
    white = m.board('drawer board' + suffix, color='#f3f2ee', roughness=0.7, coat=0.04, tooth=0.04)
    foil = m.foil('foil' + suffix)
    dosa = dosa_material(ctx, 'dosa' + suffix)

    objs = [sleeve(f'sleeve{suffix}', art, inside, edge, x=x)]
    y_front = -dims.L / 2 - dims.OUT
    dz = dims.T + 0.004
    objs.append(drawer(f'drawer{suffix}', white, x, y_front, dz))
    tray_z = dz + dims.DWALL + 0.012
    tray_y = y_front + dims.DL / 2
    objs += foil_tray(ctx, f'tray{suffix}', foil, x, tray_y, tray_z)
    # Folded dosai across the tray, packed from the front wall back.
    floor_len = dims.TRAY_L - 2 * (dims.FLANGE + dims.BEAD) - 2 * dims.TRAY_DRAFT
    yf = tray_y - floor_len / 2 + 0.12
    for k in range(dims.PIECES):
        seed = k + (7 if suffix == '-b' else 0)
        ob, yf = dosa_parcel(f'dosa{suffix}-{k}', dosa, x, yf, tray_z + 0.012, seed)
        objs.append(ob)
        yf += 0.06
    return objs


def build(ctx, variant=None):
    if variant == 'pair':
        gap = 1.3
        off = dims.W / 2 + gap / 2
        return pack(ctx, 'chicken', x=-off, suffix='-a') + pack(ctx, 'veg', x=off, suffix='-b')
    return pack(ctx, variant or 'chicken')
