"""The two sandwich halves seen through the Tiffin window: only their cut faces
are ever visible, so the model is the cut face itself, built as bands of
bread / butter / filling / cheese with wavy boundaries, plus corn kernels that
bulge out of the green chutney. Bread crumb, chutney and corn are procedural.

Coordinates: art space of the front panel (x across from the -X end, p down
the slope from the apex fold, depth in from the outer surface), mapped to the
world by `to_world`.
"""

from __future__ import annotations

import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from studio.core import rgba

# Across the pack (cm from the -X end): white-bread half, then brown-bread half.
# (name, x_left) in order; the last entry closes the band.
# Widths measured across the window in the front crop: white 1.05 | filling
# 0.5 | white 0.9 || brown 0.9 | cheese 0.45 | filling 0.65 | brown 0.6 (to
# the window edge); the outer slices run on under the printed strips.
LAYERS = [
    ('white', 0.2),
    ('butter', 1.93),
    ('filling', 2.01),
    ('white', 2.55),
    ('groove', 3.44),
    ('brown', 3.51),
    ('cheese', 4.4),
    ('filling', 4.86),
    ('brown', 5.5),
    (None, 6.85),
]
DEPTH = {'white': 0.0, 'brown': 0.0, 'butter': 0.014, 'cheese': 0.01, 'filling': 0.045, 'groove': 0.3}


def _waves(seed, amp, lengths):
    rnd = random.Random(seed)
    comps = [(amp * rnd.uniform(0.5, 1.0), 2 * math.pi / lam, rnd.uniform(0, 2 * math.pi)) for lam in lengths]
    return lambda p: sum(a * math.sin(k * p + ph) for a, k, ph in comps)


def build(name, to_world, p_range, d0, mats, seed=7):
    """The cut-face sheet. mats: dict layer -> material. Returns (sheet, kernels)."""
    p0, p1 = p_range
    pm = (p0 + p1) / 2
    rows = int((p1 - p0) / 0.045)
    tilt = 0.055  # the halves lean a few degrees in the pack

    # Boundary functions x_k(p).
    bounds = []
    for k, (lname, x0) in enumerate(LAYERS):
        prev = LAYERS[k - 1][0] if k else None
        wobble = 0.0 if k in (0, len(LAYERS) - 1) else 0.045
        # Chutney is spread by hand: its edges wander and are ragged where
        # kernels push into the bread.
        ragged = 'filling' in (lname, prev)
        fine = 0.02 if ragged else 0.006
        w = _waves(seed * 31 + k, wobble, (7.5, 3.1, 1.6) if ragged else (7.5, 3.1)) if wobble else (lambda p: 0.0)
        f = _waves(seed * 57 + k, fine, (0.9, 0.55, 0.37, 0.27) if ragged else (0.9, 0.55))
        edge = k in (0, len(LAYERS) - 1)
        bounds.append((lambda p, x0=x0, w=w, f=f, edge=edge: x0 if edge else x0 - tilt * (p - pm) + w(p) + f(p)))

    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    slots = list(dict.fromkeys(mats[l] for l, _ in LAYERS[:-1]))
    index = {id(m): i for i, m in enumerate(slots)}
    grain = _waves(seed + 3, 0.012, (0.7, 0.33, 1.9))

    # Columns: each layer is split into a few columns between its boundaries.
    cols = []  # (layer index, fraction within layer)
    for k, (lname, _) in enumerate(LAYERS[:-1]):
        n = {'white': 7, 'brown': 7, 'filling': 5, 'cheese': 3, 'butter': 1, 'groove': 2}[lname]
        for j in range(n):
            cols.append((k, j / n))
    cols.append((len(LAYERS) - 1, 0.0))

    def depth_at(k, fr, p):
        lname = LAYERS[k][0] if k < len(LAYERS) - 1 else LAYERS[k - 1][0]
        prev = LAYERS[k - 1][0] if k > 0 else lname
        d = DEPTH.get(lname, 0.0)
        if fr == 0.0 and k > 0:  # a shared boundary vertex: between the two layers
            d = (d + DEPTH.get(prev, 0.0)) / 2
            if 'groove' in (lname, prev):  # bread edges round off into the gap
                d = 0.05
        # Bread springs a little towards the film in the middle of a slice.
        if lname in ('white', 'brown') and fr > 0:
            d -= 0.018 * math.sin(math.pi * fr)
        # The chutney is a lumpy paste, pushed about by the kernels.
        if lname == 'filling' and fr > 0:
            d += 0.012 * math.sin(p * 9.1 + fr * 5.0 + k) * math.sin(p * 4.3 + 2.1 * fr + k)
        return d0 + d + grain(p + 3.7 * k)

    grid = []
    for i in range(rows + 1):
        p = p0 + (p1 - p0) * i / rows
        row = []
        for k, fr in cols:
            if k == len(LAYERS) - 1:
                x = bounds[k](p)
            else:
                xa, xb = bounds[k](p), bounds[k + 1](p)
                x = xa + (xb - xa) * fr
            row.append(bm.verts.new(to_world(x, p, depth_at(k, fr, p))))
        grid.append(row)
    for i in range(rows):
        for c in range(len(cols) - 1):
            k = cols[c][0]
            f = bm.faces.new([grid[i][c], grid[i][c + 1], grid[i + 1][c + 1], grid[i + 1][c]])
            f.material_index = index[id(mats[LAYERS[k][0]])]
            f.smooth = True
            for loop in f.loops:
                co = loop.vert.co
                loop[uv].uv = (co.x, co.y + co.z)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # The cut face must face the window (out of the pack).
    out_dir = Vector(to_world(0.0, p0, 0.0)) - Vector(to_world(0.0, p0, 1.0))
    if sum((f.normal for f in bm.faces), Vector()).dot(out_dir) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    sheet = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(sheet)
    for m in slots:
        me.materials.append(m)

    # Sweet corn kernels packed in the two fillings, touching and jostled, as
    # in the photo: a rounded wedge each (blunt crown, tapering to the tip),
    # flattened front to back, some sliced flat by the knife. Per-vertex
    # attributes give each kernel its own shade ('kr'), a paler tip ('kt')
    # and a paler, more opaque cut face ('kc').
    rnd = random.Random(seed * 13)
    kb = bmesh.new()
    lay_r = kb.verts.layers.float.new('kr')
    lay_t = kb.verts.layers.float.new('kt')
    lay_c = kb.verts.layers.float.new('kc')

    def kernel(x, p, dep, sx, sp, sd, ang, cut):
        res = bmesh.ops.create_uvsphere(kb, u_segments=16, v_segments=10, radius=1.0)
        ca, sa = math.cos(ang), math.sin(ang)
        ax = Vector((ca, sa, 0.0))
        ap = Vector((-sa, ca, 0.0))
        centre = Vector(to_world(x, p, dep))
        e_x = Vector(to_world(x + 1, p, dep)) - centre
        e_p = Vector(to_world(x, p + 1, dep)) - centre
        e_d = Vector(to_world(x, p, dep + 1)) - centre
        u_ax = (e_x * ax.x + e_p * ax.y).normalized()
        u_ap = (e_x * ap.x + e_p * ap.y).normalized()
        M = Matrix((
            (u_ax.x * sx, u_ap.x * sp, e_d.x * sd, centre.x),
            (u_ax.y * sx, u_ap.y * sp, e_d.y * sd, centre.y),
            (u_ax.z * sx, u_ap.z * sp, e_d.z * sd, centre.z),
            (0, 0, 0, 1),
        ))
        shade = rnd.random()
        ph = [rnd.uniform(0, 6.3) for _ in range(3)]
        for vtx in res['verts']:
            lc = vtx.co.copy()
            # Lumpy, not a perfect ellipsoid.
            lc *= 1.0 + 0.05 * math.sin(3 * lc.x + ph[0]) * math.sin(3 * lc.y + ph[1]) + 0.03 * math.sin(4 * lc.z + ph[2])
            tip = max(0.0, -lc.y)
            lc.x *= 1.0 - 0.38 * tip ** 1.5  # tapers to the tip
            if lc.y > 0:
                lc.y *= 0.82  # blunt crown
                lc.y -= 0.12 * max(0.0, 1 - 3 * abs(lc.x)) * lc.y  # a shallow dent in it
            cut_face = 0.0
            if lc.z < cut:
                lc.z = cut
                cut_face = 1.0
            vtx.co = M @ lc
            vtx[lay_r] = shade
            vtx[lay_t] = min(1.0, tip * 1.3)
            vtx[lay_c] = cut_face

    for k, (lname, _) in enumerate(LAYERS[:-1]):
        if lname != 'filling':
            continue
        p = p0 + rnd.uniform(0.0, 0.2)
        while p < p1:
            xa, xb = bounds[k](p), bounds[k + 1](p)
            wdt = xb - xa
            broken = rnd.random() < 0.12
            size = rnd.uniform(0.5, 0.65) if broken else rnd.uniform(0.85, 1.1)
            sx = min(rnd.uniform(0.23, 0.29), wdt * 0.52) * size
            sp = rnd.uniform(0.25, 0.33) * size
            sd = rnd.uniform(0.13, 0.16) * max(0.8, size)
            x = (xa + xb) / 2 + rnd.uniform(-0.5, 0.5) * max(0.0, wdt - 2 * sx) + rnd.uniform(-0.04, 0.04)
            # Kernels bulge out of the chutney towards the film, never through
            # it; about a third sit deeper, only their crowns showing.
            surface = d0 + DEPTH['filling']
            if rnd.random() < 0.3:
                dep = surface + sd - rnd.uniform(0.03, 0.07)
            else:
                dep = surface + rnd.uniform(0.02, 0.05)
            dep = max(dep, 0.085 + sd)
            ang = rnd.uniform(-0.7, 0.7) + (math.pi if rnd.random() < 0.5 else 0.0)
            cut = -rnd.uniform(0.35, 0.65) if rnd.random() < 0.4 else -1.0
            kernel(x, p, dep, sx, sp, sd, ang, cut)
            # Now and then a small kernel wedged in beside the others.
            if not broken and rnd.random() < 0.3 and wdt > 0.5:
                side = rnd.choice((-1, 1))
                kernel(x + side * sx * 0.95, p + sp * rnd.uniform(0.5, 0.9), dep + 0.02, sx * 0.6, sp * 0.6, sd * 0.8, rnd.uniform(0, 6.3), -1.0)
            p += sp * rnd.uniform(1.55, 1.85) + (rnd.uniform(0.12, 0.3) if rnd.random() < 0.12 else 0.0)
    for f in kb.faces:
        f.smooth = True
    km = bpy.data.meshes.new(name + '-corn')
    kb.to_mesh(km)
    kb.free()
    kernels = bpy.data.objects.new(name + '-corn', km)
    bpy.context.collection.objects.link(kernels)
    km.materials.append(mats['corn'])
    return sheet, kernels


# ----------------------------------------------------------------- materials


def _nodes(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes['Principled BSDF']


def _smooth(nt, src, a, b):
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.interpolation_type = 'SMOOTHSTEP'
    mr.inputs['From Min'].default_value = a
    mr.inputs['From Max'].default_value = b
    nt.links.new(src, mr.inputs['Value'])
    return mr.outputs['Result']


def _math(nt, op, a, b=None, value=None):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    for i, s in enumerate((a, b)):
        if s is None:
            continue
        if isinstance(s, (int, float)):
            n.inputs[i].default_value = s
        else:
            nt.links.new(s, n.inputs[i])
    return n.outputs[0]


def _mix(nt, fac, a, b):
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    if isinstance(fac, (int, float)):
        n.inputs['Factor'].default_value = fac
    else:
        nt.links.new(fac, n.inputs['Factor'])
    for key, v in (('A', a), ('B', b)):
        if isinstance(v, str):
            n.inputs[key].default_value = rgba(v)
        else:
            nt.links.new(v, n.inputs[key])
    return n.outputs['Result']


def bread(name, crumb, hole, deep, speck=None, scale=1.0, open_big=0.62):
    """Sliced bread crumb: soft crumb with rounded air holes of mixed sizes
    (a few deep, most shallow), a fibrous tone, and bran flecks if asked."""
    m, nt, p = _nodes(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    # Holes stretch a little along the rise of the loaf.
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0 * scale, 0.75 * scale, 1.25 * scale)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    warp = nt.nodes.new('ShaderNodeTexNoise')
    warp.inputs['Scale'].default_value = 3.0
    warp.inputs['Detail'].default_value = 4.0
    nt.links.new(mp.outputs['Vector'], warp.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeVectorMath')
    wv.operation = 'MULTIPLY_ADD'
    nt.links.new(warp.outputs['Color'], wv.inputs[0])
    wv.inputs[1].default_value = (0.22, 0.22, 0.22)
    nt.links.new(mp.outputs['Vector'], wv.inputs[2])
    vec = wv.outputs['Vector']

    def holes(sc, rmin, rmax, open_p):
        v = nt.nodes.new('ShaderNodeTexVoronoi')
        v.inputs['Scale'].default_value = sc
        nt.links.new(vec, v.inputs['Vector'])
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(v.outputs['Color'], sep.inputs['Color'])
        radius = _math(nt, 'MULTIPLY_ADD', sep.outputs['Red'], rmax - rmin)
        radius.node.inputs[2].default_value = rmin
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.interpolation_type = 'SMOOTHSTEP'
        nt.links.new(v.outputs['Distance'], mr.inputs['Value'])
        nt.links.new(_math(nt, 'MULTIPLY', radius, 0.55), mr.inputs['From Min'])
        nt.links.new(radius, mr.inputs['From Max'])
        mr.inputs['To Min'].default_value = 1.0
        mr.inputs['To Max'].default_value = 0.0
        openness = _smooth(nt, sep.outputs['Green'], open_p, open_p + 0.12)
        return _math(nt, 'MULTIPLY', mr.outputs['Result'], openness), sep.outputs['Blue']

    big, depth = holes(3.0, 0.14, 0.42, open_big)
    small, _ = holes(8.5, 0.12, 0.36, 0.3)
    tiny, _ = holes(22.0, 0.1, 0.34, 0.22)
    pores = _math(nt, 'MAXIMUM', big, _math(nt, 'MULTIPLY', small, 0.7))
    pores = _math(nt, 'MAXIMUM', pores, _math(nt, 'MULTIPLY', tiny, 0.45))
    col = _mix(nt, pores, crumb, hole)
    col = _mix(nt, _math(nt, 'MULTIPLY', big, _math(nt, 'MULTIPLY', depth, 0.8)), col, deep)
    # Millimetre-scale mottling: the light and shade of an open crumb.
    mot = nt.nodes.new('ShaderNodeTexNoise')
    mot.inputs['Scale'].default_value = 9.0
    mot.inputs['Detail'].default_value = 6.0
    mot.inputs['Roughness'].default_value = 0.65
    nt.links.new(vec, mot.inputs['Vector'])
    mott = _smooth(nt, mot.outputs['Fac'], 0.38, 0.68)
    col = _mix(nt, _math(nt, 'MULTIPLY', mott, 0.55), col, hole)
    # Fibrous tone: the crumb is never one flat colour.
    fib = nt.nodes.new('ShaderNodeTexNoise')
    fib.inputs['Scale'].default_value = 45.0
    fib.inputs['Detail'].default_value = 8.0
    fib.inputs['Roughness'].default_value = 0.7
    nt.links.new(vec, fib.inputs['Vector'])
    col = _mix(nt, _math(nt, 'MULTIPLY', _smooth(nt, fib.outputs['Fac'], 0.35, 0.75), 0.5), _mix(nt, 0.07, col, '#6b5a40'), col)
    if speck:
        sv = nt.nodes.new('ShaderNodeTexVoronoi')
        sv.inputs['Scale'].default_value = 16.0
        nt.links.new(vec, sv.inputs['Vector'])
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(sv.outputs['Color'], sep.inputs['Color'])
        dot = _math(nt, 'MULTIPLY', _smooth(nt, sv.outputs['Distance'], 0.2, 0.08), _smooth(nt, sep.outputs['Blue'], 0.72, 0.8))
        col = _mix(nt, dot, col, speck)
    nt.links.new(col, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.92
    p.inputs['Specular IOR Level'].default_value = 0.25
    p.inputs['Subsurface Weight'].default_value = 0.1
    p.inputs['Subsurface Radius'].default_value = (0.05, 0.04, 0.025)
    p.inputs['Subsurface Scale'].default_value = 1.0
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.8
    bump.inputs['Distance'].default_value = 0.03
    nt.links.new(_math(nt, 'SUBTRACT', _math(nt, 'SUBTRACT', 1.0, pores), _math(nt, 'MULTIPLY', mott, 0.35)), bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


def chutney(name='green chutney'):
    """Spinach and mint chutney with a little mayonnaise: a dark olive paste,
    lighter where it is thin, with leafy flecks and creamy smears."""
    m, nt, p = _nodes(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 11.0
    n.inputs['Detail'].default_value = 6.0
    n.inputs['Roughness'].default_value = 0.62
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    v = nt.nodes.new('ShaderNodeTexVoronoi')
    v.inputs['Scale'].default_value = 26.0
    nt.links.new(tc.outputs['Object'], v.inputs['Vector'])
    mayo = nt.nodes.new('ShaderNodeTexNoise')
    mayo.inputs['Scale'].default_value = 4.5
    mayo.inputs['Detail'].default_value = 5.0
    mayo.inputs['Roughness'].default_value = 0.6
    nt.links.new(tc.outputs['Object'], mayo.inputs['Vector'])
    col = _mix(nt, _smooth(nt, n.outputs['Fac'], 0.32, 0.72), '#2c3a15', '#5a7228')
    # Leafy flecks, darker.
    col = _mix(nt, _math(nt, 'MULTIPLY', _smooth(nt, v.outputs['Distance'], 0.24, 0.06), 0.55), col, '#1c230f')
    # Creamy smears of mayonnaise, tinted green where they mix in.
    smear = _smooth(nt, mayo.outputs['Fac'], 0.6, 0.7)
    col = _mix(nt, _math(nt, 'MULTIPLY', smear, 0.8), col, _mix(nt, _smooth(nt, n.outputs['Fac'], 0.3, 0.7), '#b9b98a', '#dcd9bd'))
    nt.links.new(col, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.42
    p.inputs['Specular IOR Level'].default_value = 0.4
    p.inputs['Subsurface Weight'].default_value = 0.08
    p.inputs['Subsurface Radius'].default_value = (0.03, 0.05, 0.02)
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.45
    bump.inputs['Distance'].default_value = 0.02
    nt.links.new(_math(nt, 'ADD', n.outputs['Fac'], _math(nt, 'MULTIPLY', smear, 0.3)), bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


def corn(name='sweet corn'):
    """Sweet corn: pale butter-yellow, translucent, each kernel its own shade,
    a paler tip, and a creamier, more opaque face where the knife cut it."""
    m, nt, p = _nodes(name)

    def attr(nm):
        a = nt.nodes.new('ShaderNodeAttribute')
        a.attribute_name = nm
        return a.outputs['Fac']

    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 14.0
    n.inputs['Detail'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    col = _mix(nt, attr('kr'), '#dfa928', '#f0c850')
    col = _mix(nt, _math(nt, 'MULTIPLY', _smooth(nt, n.outputs['Fac'], 0.35, 0.7), 0.2), col, '#f4d77a')
    col = _mix(nt, _math(nt, 'MULTIPLY', attr('kt'), 0.4), col, '#efdca2')
    col = _mix(nt, _math(nt, 'MULTIPLY', attr('kc'), 0.45), col, '#f5dc86')
    nt.links.new(col, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.34
    p.inputs['Specular IOR Level'].default_value = 0.4
    p.inputs['Subsurface Weight'].default_value = 0.35
    p.inputs['Subsurface Radius'].default_value = (0.08, 0.06, 0.02)
    p.inputs['Subsurface Scale'].default_value = 1.0
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.2
    bump.inputs['Distance'].default_value = 0.01
    nt.links.new(n.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


def creamy(name, color, sss=0.25, roughness=0.45):
    """Butter, cheese, mayonnaise: soft, smooth, slightly translucent."""
    m, nt, p = _nodes(name)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 9.0
    n.inputs['Detail'].default_value = 4.0
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    nt.links.new(_mix(nt, _smooth(nt, n.outputs['Fac'], 0.3, 0.75), _mix(nt, 0.08, color, '#b89c60'), color), p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Subsurface Weight'].default_value = sss
    p.inputs['Subsurface Radius'].default_value = (0.08, 0.07, 0.05)
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.15
    bump.inputs['Distance'].default_value = 0.02
    nt.links.new(n.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


def materials():
    white = bread('white bread', '#f5efe3', '#dccfb5', '#bba786', open_big=0.56)
    # Whole-wheat sandwich bread: a light tan crumb with bran flecks (the
    # photo shows it much paler than a dark rye).
    brown = bread('brown bread', '#c89d70', '#9c6e46', '#6e4a2b', speck='#e6cda4', scale=0.9, open_big=0.64)
    return {
        'white': white,
        'brown': brown,
        'groove': white,
        'butter': creamy('butter', '#f2ead0', 0.2, 0.35),
        'cheese': creamy('cheese', '#f4f0e2', 0.3, 0.5),
        'filling': chutney(),
        'corn': corn(),
    }
