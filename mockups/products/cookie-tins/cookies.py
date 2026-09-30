"""Chocolate chip cookies for the open-tin shot: irregular, domed discs with a
cracked, browned top and half-sunk chocolate chunks. Geometry is displaced
with seeded noise, so every cookie differs; colour and fine bump are
procedural (browning towards the rim and underneath, crack lines, grain).
"""

from __future__ import annotations

import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

GRID = 110  # top surface: a square grid mapped onto the disc (no pole at the centre)
F_TOP = 0.94  # the grid covers the top out to this fraction of the radius

# The rim, from the top's edge round to the bottom: (fraction of the outline
# radius, height as a fraction of the thickness).
_RIM = [
    (0.962, 0.86), (0.98, 0.76), (0.992, 0.63), (1.0, 0.48), (1.0, 0.32), (0.99, 0.17), (0.97, 0.065),
    (0.945, 0.014), (0.91, 0.0),
]


def _outline_r(a: float, off: Vector, R0: float) -> float:
    """Outline radius at angle a: round, but hand-made."""
    p = Vector((math.cos(a), math.sin(a), 0.0)) * 1.3 + off
    return R0 * (1.0 + 0.045 * noise.noise(p) + 0.018 * noise.noise(p * 3.1))


def _clumps(p, off):
    """Dough clumps: Voronoi cells domed in their middles, with fissures
    between them, like a baked drop cookie's craggy top."""
    d, _ = noise.voronoi(p * 1.15 + off, distance_metric='DISTANCE', exponent=2.5)
    ridge = min(1.0, (d[1] - d[0]) * 1.8)
    return 1.0 - (1.0 - ridge) ** 2


def _lumps(p, off):
    # Fissures open only in patches; elsewhere the top just undulates.
    patch = min(1.0, max(0.0, 0.45 + 1.3 * noise.noise(p * 0.45 + off * 0.37)))
    return (
        0.11 * patch * _clumps(p, off)
        + 0.12 * noise.fractal(p * 0.55 + off, 1.0, 2.0, 3)
        + 0.035 * noise.noise(p * 4.0 + off)
    )


def _rim_push(p, off):
    return 0.08 * noise.noise(p * 1.7 + off) + 0.015 * noise.noise(p * 4.0 + off)


def cookie_mesh(name: str, seed: int, R0: float = 3.35, h: float = 0.95):
    """A closed cookie mesh with its base at z = 0, centred on the origin."""
    rng = random.Random(seed)
    off = Vector((rng.uniform(0, 50), rng.uniform(0, 50), rng.uniform(0, 50)))
    shape = Vector((seed * 7.31, seed * 3.17, 0.0))
    bm = bmesh.new()
    n = GRID

    def top_vert(u, v):
        # Square to disc (elliptical grid mapping), then onto the outline.
        x = u * math.sqrt(max(0.0, 1 - v * v / 2))
        y = v * math.sqrt(max(0.0, 1 - u * u / 2))
        f = min(1.0, math.hypot(x, y))
        a = math.atan2(y, x)
        F = F_TOP * f
        r = _outline_r(a, shape, R0) * F
        px, py = r * math.cos(a), r * math.sin(a)
        p = Vector((px, py, 0.0))
        if F > 0.9:
            push = _rim_push(p, off) * (F - 0.9) / (F_TOP - 0.9)
            px += math.cos(a) * push
            py += math.sin(a) * push
        z = h * (1.0 - 0.1 * F * F) + h * _lumps(p, off)
        return bm.verts.new((px, py, z)), a

    grid = [[top_vert(-1 + 2 * i / n, -1 + 2 * j / n) for j in range(n + 1)] for i in range(n + 1)]
    for i in range(n):
        for j in range(n):
            f = bm.faces.new([grid[i][j][0], grid[i + 1][j][0], grid[i + 1][j + 1][0], grid[i][j + 1][0]])
            f.smooth = True
    # The grid's boundary, counter-clockwise.
    loop = [grid[i][0] for i in range(n)] + [grid[n][j] for j in range(n)]
    loop += [grid[i][n] for i in range(n, 0, -1)] + [grid[0][j] for j in range(n, 0, -1)]
    prev = [v for v, _ in loop]
    for f_s, zf in _RIM:
        ring = []
        for _, a in loop:
            r = _outline_r(a, shape, R0) * f_s
            px, py = r * math.cos(a), r * math.sin(a)
            p = Vector((px, py, 0.0))
            z = h * zf
            if zf > 0.1:
                push = _rim_push(p, off)
                px += math.cos(a) * push
                py += math.sin(a) * push
                z += h * _lumps(p, off) * max(0.0, (zf - 0.3) / 0.6)
            ring.append(bm.verts.new((px, py, max(0.0, z))))
        m = len(ring)
        for i in range(m):
            j = (i + 1) % m
            f = bm.faces.new([prev[i], prev[j], ring[j], ring[i]])
            f.smooth = True
        prev = ring
    bottom = bm.faces.new(prev)
    bottom.smooth = False
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def chip_mesh(name: str, seed: int, size: float):
    """An irregular chocolate chunk, softened in the oven: a lumpy blob whose
    top has slumped flat where it broke through the dough."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=size)
    off = Vector((rng.uniform(0, 90), rng.uniform(0, 90), rng.uniform(0, 90)))
    sx, sy = rng.uniform(0.9, 1.35), rng.uniform(0.7, 1.05)
    cap = size * rng.uniform(0.3, 0.45)
    for v in bm.verts:
        n = v.co.normalized()
        d = 1.0 + 0.32 * noise.noise(n * 1.6 + off) + 0.12 * noise.noise(n * 3.8 + off)
        co = Vector((n.x * sx, n.y * sy, n.z * 0.8)) * size * d
        if co.z > cap:  # softened in the oven: a low, rounded, glossy dome
            co.z = cap + (co.z - cap) * 0.38
        v.co = co
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob['cap'] = cap
    return ob


def surface_z(ob, x: float, y: float) -> float:
    """Height of the cookie's top at local (x, y), by ray cast from above."""
    ok, loc, _, _ = ob.ray_cast(Vector((x, y, 10.0)), Vector((0, 0, -1)))
    return loc.z if ok else 0.0


def cookie(name: str, seed: int, mats, R0: float = 3.35, h: float = 0.95, chips: int = 15):
    """A cookie with chocolate chunks; returns [cookie, chips...], all
    parented to the cookie so they move together."""
    dough, choc = mats
    ob = cookie_mesh(name, seed, R0, h)
    ob.data.materials.append(dough)
    bpy.context.view_layer.update()
    rng = random.Random(seed * 13 + 1)
    out = [ob]
    placed = []
    tries = 0
    while len(placed) < chips and tries < 400:
        tries += 1
        # Chips land more towards the middle; none right on the rim.
        r = R0 * 0.86 * math.sqrt(rng.random())
        a = rng.uniform(0, 2 * math.pi)
        x, y = r * math.cos(a), r * math.sin(a)
        s = rng.uniform(0.24, 0.45)
        if any(math.hypot(x - px, y - py) < (s + ps) * 1.15 for px, py, ps in placed):
            continue
        placed.append((x, y, s))
        c = chip_mesh(f'{name}-chip{len(placed)}', seed * 101 + len(placed), s)
        c.data.materials.append(choc)
        z = surface_z(ob, x, y)
        # Sunk in the dough so the slumped top shows just proud of it, or
        # barely breaks through.
        c.location = (x, y, z - c['cap'] + rng.uniform(-0.04, 0.07))
        c.rotation_euler = (rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), rng.uniform(0, 6.28))
        c.parent = ob
        out.append(c)
    return out


# ----------------------------------------------------------------- materials


def dough_material(m, name: str = 'cookie dough'):
    """Baked cookie dough, built on the studio's solid() base: golden, browning
    towards the rim, underneath and on the peaks of the crags (Cycles'
    pointiness), paler in the fissures; mottled, with a crumbly, sugary bump."""
    from studio.core import rgba

    mat = m.solid(name, '#c98c4c', roughness=0.7)
    nt = mat.node_tree
    p = nt.nodes['Principled BSDF']
    N = nt.nodes.new
    L = nt.links.new

    def maprange(src, a, b, c=0.0, d=1.0, clamp=True):
        n = N('ShaderNodeMapRange')
        n.clamp = clamp
        n.inputs['From Min'].default_value = a
        n.inputs['From Max'].default_value = b
        n.inputs['To Min'].default_value = c
        n.inputs['To Max'].default_value = d
        L(src, n.inputs['Value'])
        return n.outputs['Result']

    def math_(op, a, b):
        n = N('ShaderNodeMath')
        n.operation = op
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]

    coord = N('ShaderNodeTexCoord')
    geo = N('ShaderNodeNewGeometry')
    obj = coord.outputs['Object']

    # Browning towards the rim: distance from the cookie's axis.
    sep = N('ShaderNodeSeparateXYZ')
    L(obj, sep.inputs[0])
    flat = N('ShaderNodeCombineXYZ')
    L(sep.outputs['X'], flat.inputs['X'])
    L(sep.outputs['Y'], flat.inputs['Y'])
    ln = N('ShaderNodeVectorMath')
    ln.operation = 'LENGTH'
    L(flat.outputs[0], ln.inputs[0])
    rim = maprange(ln.outputs['Value'], 2.3, 3.5, 0.0, 0.45)
    # Underside and the steep sides: browner.
    nz = N('ShaderNodeSeparateXYZ')
    L(geo.outputs['Normal'], nz.inputs[0])
    under = maprange(nz.outputs['Z'], 0.5, -0.3, 0.0, 0.6)
    # Crag peaks brown, fissures stay pale.
    peak = maprange(geo.outputs['Pointiness'], 0.47, 0.54, -0.13, 0.13)
    # Mottling.
    mot = N('ShaderNodeTexNoise')
    mot.inputs['Scale'].default_value = 1.1
    mot.inputs['Detail'].default_value = 5.0
    L(obj, mot.inputs['Vector'])
    mott = maprange(mot.outputs['Fac'], 0.35, 0.65, -0.12, 0.12)
    f = math_('ADD', math_('ADD', math_('MAXIMUM', rim, under), peak), mott)
    f = math_('ADD', f, 0.42)

    ramp = N('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.elements[0].position = 0.12
    cr.elements[0].color = rgba('#e6bd83')
    cr.elements[1].position = 0.42
    cr.elements[1].color = rgba('#cf9454')
    e = cr.elements.new(0.66)
    e.color = rgba('#b0703a')
    e = cr.elements.new(0.92)
    e.color = rgba('#7e4622')
    L(f, ramp.inputs['Fac'])

    # Sugar and crumb speckle.
    grain = N('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 45.0
    grain.inputs['Detail'].default_value = 2.0
    L(obj, grain.inputs['Vector'])
    speck = N('ShaderNodeMix')
    speck.data_type = 'RGBA'
    speck.blend_type = 'OVERLAY'
    speck.inputs['Factor'].default_value = 0.3
    L(ramp.outputs['Color'], speck.inputs['A'])
    L(grain.outputs['Color'], speck.inputs['B'])
    L(speck.outputs['Result'], p.inputs['Base Color'])

    # Bump: small crags (Voronoi cells, domed) plus crumb.
    # Warp the lookup so cell edges wander instead of running straight.
    wob = N('ShaderNodeTexNoise')
    wob.inputs['Scale'].default_value = 2.2
    wob.inputs['Detail'].default_value = 3.0
    L(obj, wob.inputs['Vector'])
    warp = N('ShaderNodeVectorMath')
    warp.operation = 'MULTIPLY_ADD'
    L(wob.outputs['Color'], warp.inputs[0])
    warp.inputs[1].default_value = (0.3, 0.3, 0.3)
    L(obj, warp.inputs[2])
    vor = N('ShaderNodeTexVoronoi')
    vor.feature = 'DISTANCE_TO_EDGE'
    vor.inputs['Scale'].default_value = 3.2
    L(warp.outputs[0], vor.inputs['Vector'])
    crag = maprange(vor.outputs['Distance'], 0.0, 0.18, 0.0, 1.0)
    crumb = N('ShaderNodeTexNoise')
    crumb.inputs['Scale'].default_value = 14.0
    crumb.inputs['Detail'].default_value = 8.0
    crumb.inputs['Roughness'].default_value = 0.65
    L(obj, crumb.inputs['Vector'])
    hgt = math_('ADD', math_('MULTIPLY', crag, 0.4), crumb.outputs['Fac'])
    bump = N('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.5
    bump.inputs['Distance'].default_value = 0.035
    L(hgt, bump.inputs['Height'])
    L(bump.outputs['Normal'], p.inputs['Normal'])
    p.inputs['Specular IOR Level'].default_value = 0.28
    return mat


def chocolate_material(m, name: str = 'chocolate'):
    """Dark chocolate chunks, softened in the oven: a glossy skin over a
    slightly uneven surface, some chunks a shade milkier than others."""
    from studio.core import rgba

    mat = m.solid(name, '#3b2317', roughness=0.2)
    nt = mat.node_tree
    p = nt.nodes['Principled BSDF']
    coord = nt.nodes.new('ShaderNodeTexCoord')
    # Per-chunk tone: a coarse noise in world space, so each chunk (a few mm
    # across) takes one shade, from dark to a touch milkier.
    tone = nt.nodes.new('ShaderNodeTexNoise')
    tone.inputs['Scale'].default_value = 0.9
    nt.links.new(coord.outputs['Object'], tone.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = rgba('#2e190f')
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = rgba('#4d2d1b')
    nt.links.new(tone.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Specular IOR Level'].default_value = 0.6
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 25.0
    n.inputs['Detail'].default_value = 4.0
    nt.links.new(coord.outputs['Object'], n.inputs['Vector'])
    b = nt.nodes.new('ShaderNodeBump')
    b.inputs['Strength'].default_value = 0.18
    b.inputs['Distance'].default_value = 0.02
    nt.links.new(n.outputs['Fac'], b.inputs['Height'])
    nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    return mat


def settle(ob, R0: float = 3.35, clearance: float = 0.015):
    """Drops a placed cookie (and its chips) straight down until its underside
    rests on whatever is below it: the cookie beneath, a chip, or the tin's
    floor. Rays go down from a 2 mm grid over the whole flat underside and
    its rim; the smallest gap wins, so nothing below pokes into it."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    mw = ob.matrix_world
    pts = [mw @ v.co for v in ob.data.vertices if v.co.z <= 0.03]
    step = 0.2
    k = int(R0 / step)
    for i in range(-k, k + 1):
        for j in range(-k, k + 1):
            if math.hypot(i * step, j * step) < 0.88 * R0:
                pts.append(mw @ Vector((i * step, j * step, 0.0)))
    gap = 1e9
    for p in pts:
        hit, loc, _, _, hob, _ = sc.ray_cast(dg, p - Vector((0, 0, 0.001)), Vector((0, 0, -1)))
        if hit and hob is not None and hob.name != ob.name and hob.parent != ob:
            gap = min(gap, p.z - loc.z)
    if gap < 1e8:
        ob.location.z -= gap - clearance
        bpy.context.view_layer.update()
    return ob


def place(ob, loc, tilt=(0.0, 0.0), yaw=0.0):
    ob.matrix_world = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt[0], 4, 'X') @ Matrix.Rotation(tilt[1], 4, 'Y')
