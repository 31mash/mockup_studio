"""A Punjabi samosa sitting on its base: shape and blisters in numpy, a
fried-pastry material that reads them back.

Shape. Horizontal slices are rounded triangles shrinking to the tip: the
pastry is a cone of dough folded round the filling, so the three faces fill
out, the two front corners are soft folds and the third, at the back, is the
pinched seam where the cone was sealed (a thin crimped fin up to the tip).
The cone's overlap shows as a faint step running down one face from the tip.
At the base the corners flatten into thin, crisp feet, one longer than the
others, and a narrow lip runs round the base where the pastry sat in the oil.

Surface. Deep-fried dough is covered in blisters: a dense field of small
ones, fewer medium ones and a few big bubbles. They are real geometry
(domes pushed out along the normal), so the studio light rakes across them
and the oily coat glints on their tops. The blister height and the folds are
stored as mesh attributes ('blister', 'edge') for the shader: blister tops
fry paler and golden, the folds, the seam and the base fry darker.
"""

from __future__ import annotations

import math

import numpy as np

import dims

NA = 800  # samples round each slice (about 0.35 mm apart at the base)
NZ = 280  # slices
TOP = 0.985  # the last ring's height, as a fraction of the samosa's height

CORNERS = (90.0, 210.0, 330.0)  # the seam at the back (+Y), folds front-left and front-right
CORNER_SCALE = (1.0, 1.07, 0.97)
FEET = (0.30, 0.95, 0.55)  # how far each corner's foot runs out at the base (cm)
OVERLAP_AT = 229.0  # the cone's overlap: a faint step down the front face, near the front-left fold


def _gauss_smooth(r, sigma_deg):
    """Periodic Gaussian smoothing of r(theta) sampled at NA angles."""
    if sigma_deg <= 0:
        return r
    n = len(r)
    k = np.arange(-n // 2, n // 2)
    g = np.exp(-0.5 * (k * 360.0 / n / sigma_deg) ** 2)
    g /= g.sum()
    return np.real(np.fft.ifft(np.fft.fft(r) * np.fft.fft(np.fft.ifftshift(g))))


def _noise3(seed, n, scale):
    rnd = np.random.default_rng(seed)
    d = rnd.normal(size=(n, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    k = 2 * np.pi / (scale * rnd.uniform(0.7, 1.4, n))
    ph = rnd.uniform(0, 2 * np.pi, n)
    a = rnd.uniform(0.5, 1.0, n) / math.sqrt(n / 2)

    def f(P):
        return sum(a[i] * np.sin(k[i] * (P @ d[i]) + ph[i]) for i in range(n))

    return f


_lumps = _noise3(5, 14, 2.6)
_small = _noise3(9, 18, 0.9)
_patch = _noise3(17, 10, 1.6)


def _hash(c, seed, k):
    """Uniform [0, 1) per integer cell (N x 3) and stream k."""
    h = (c[:, 0].astype(np.uint64) * np.uint64(0x9E3779B1)
         ^ c[:, 1].astype(np.uint64) * np.uint64(0x85EBCA77)
         ^ c[:, 2].astype(np.uint64) * np.uint64(0xC2B2AE3D)
         ^ np.uint64((seed * 7919 + k * 104729) & 0xFFFFFFFF))
    h ^= h >> np.uint64(15)
    h *= np.uint64(0x2C1B3C6D)
    h &= np.uint64(0xFFFFFFFFFFFF)
    h ^= h >> np.uint64(12)
    h *= np.uint64(0x297A2D39)
    h &= np.uint64(0xFFFFFFFFFFFF)
    h ^= h >> np.uint64(15)
    return (h & np.uint64(0xFFFFFF)).astype(np.float64) / float(0x1000000)


def _blisters(P, cell, prob, r0, r1, h0, h1, seed):
    """Domes of fried dough: one candidate per cell of a jittered 3D grid,
    kept with probability `prob`, radius r0..r1 and height h0..h1 (cm).
    Overlapping domes merge (the higher one wins)."""
    offset = np.array([0.37, 0.61, 0.13]) * seed
    Q = P / cell + offset
    g = np.floor(Q).astype(np.int64)
    best = np.zeros(len(P))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = g + np.array([dx, dy, dz])
                cc = c + (1 << 20)
                fp = c + np.stack([_hash(cc, seed, k) for k in range(3)], axis=1)
                d = np.linalg.norm(Q - fp, axis=1) * cell
                rad = r0 + (r1 - r0) * _hash(cc, seed, 3)
                hgt = (h0 + (h1 - h0) * _hash(cc, seed, 4)) * (_hash(cc, seed, 5) < prob)
                dome = hgt * np.clip(1.0 - (d / rad) ** 2, 0.0, 1.0) ** 0.9
                best = np.maximum(best, dome)
    return best


def rings():
    """Vertex rings (NZ x NA x 3) from the base to the tip, before blisters,
    and per-vertex fold weights (NZ x NA)."""
    R0, H = dims.SAMOSA_R, dims.SAMOSA_H
    th = np.linspace(0, 2 * np.pi, NA, endpoint=False)
    corners = np.radians(CORNERS)
    scale = np.array(CORNER_SCALE)
    feet = np.array(FEET)
    dd = np.degrees(np.abs((th[:, None] - corners[None, :] + np.pi) % (2 * np.pi) - np.pi))
    near = np.argmin(dd, axis=1)
    dmin = dd[np.arange(NA), near]
    face = np.radians(60.0 - dmin)  # 0 at a corner, 60 deg at a face centre
    tri = math.cos(math.radians(60)) / np.cos(face)  # 1 at corners, 0.5 mid-face
    seam = near == 0
    # The cone's overlap: a step (the upper layer's edge) that thins out across the face.
    rel = (np.degrees(th) - OVERLAP_AT + 180.0) % 360.0 - 180.0
    overlap = 1.0 / (1.0 + np.exp(-rel / 0.5)) * np.exp(-np.maximum(rel, 0.0) / 14.0)

    zs = np.linspace(0, 1, NZ) ** 1.2 * H * TOP  # denser at the base; the tip is a single point
    out, edge = [], []
    for z in zs:
        h = z / H
        bulge = 0.2 + 0.1 * math.sin(math.pi * min(1.0, h * 1.25))  # the faces fill out
        r = (1 - bulge) * tri + bulge
        r = r * scale[near]
        # Round the folds (more so higher up), keep the seam and the feet crisper.
        soft = _gauss_smooth(r, 2.0 + 3.6 * min(1.0, h * 2.0))
        sharp = _gauss_smooth(r, 1.8 + 2.0 * h)
        wsharp = np.where(seam, 1.0, 0.0) * np.exp(-(dmin / 26.0) ** 2)
        r = soft * (1 - wsharp) + sharp * wsharp
        # Profile to the tip: nearly straight faces, a little fuller low down.
        prof = (1 - h) ** 0.85 * (1 + 0.16 * math.sin(math.pi * h ** 0.75))
        rr = R0 * r * prof
        # Base: a tight roll under the edge, a thin lip, and flat feet at the corners.
        rb = 0.35
        if z < rb:
            rr = rr - (rb - math.sqrt(max(0.0, rb * rb - (rb - z) ** 2))) * 0.8
        rr = rr + 0.16 * math.exp(-z / 0.06)
        rr = rr + feet[near] * math.exp(-z / 0.14) * np.exp(-(dmin / 12.0) ** 2)
        # The seam fin: pressed pastry standing proud of the back corner, crimped.
        ph = z * 2 * math.pi / 0.9 + 1.3 * math.sin(z * 1.9) + 0.7 * math.sin(z * 4.3 + 1.0)
        pleat = 1 + 0.2 * math.sin(ph) * (0.6 + 0.4 * math.sin(z * 2.7 + 0.4))
        rr = rr + 0.3 * (1 - h) ** 0.45 * pleat * np.exp(-(dmin / 2.8) ** 2) * seam
        # The overlap step, fading out towards the base and the tip.
        rr = rr + 0.07 * overlap * min(1.0, z / 0.8) * (1 - h) ** 0.3
        # Lean: the tip sits over the back half, a little off to one side.
        cx = 0.3 * h ** 1.6
        cy = 0.75 * h ** 1.4
        out.append(np.stack([cx + rr * np.cos(th), cy + rr * np.sin(th), np.full(NA, z)], axis=1))
        fold = np.exp(-(dmin / (7.0 + 5.0 * h)) ** 2) * min(1.0, 0.35 + h)
        edge.append(np.clip(np.maximum(fold, math.exp(-z / 0.45)), 0.0, 1.0))
    return np.array(out), np.array(edge)


def _normals(P):
    tu = np.roll(P, -1, axis=1) - np.roll(P, 1, axis=1)
    tv = np.empty_like(P)
    tv[1:-1] = P[2:] - P[:-2]
    tv[0] = P[1] - P[0]
    tv[-1] = P[-1] - P[-2]
    n = np.cross(tu, tv)
    return n / (np.linalg.norm(n, axis=2, keepdims=True) + 1e-12)


def surface():
    """Final rings with lumps and blisters, plus the 'blister' and 'edge' weights."""
    P, edge = rings()
    H = dims.SAMOSA_H
    N = _normals(P)
    flat = P.reshape(-1, 3)
    n = N.reshape(-1, 3)
    z = flat[:, 2]
    # Fade the relief out at the very base (it sits flat) and near the tip.
    fade = np.clip(z / 0.12, 0, 1) * np.clip((H - z) / 0.5, 0, 1)
    lumps = (0.12 * _lumps(flat) + 0.035 * _small(flat)) * np.clip(z / 0.5, 0, 1) * np.clip((H - z) / 0.8, 0, 1)
    # Blisters are denser where the dough was thinner (patches), sparse on the folds.
    dense = np.clip(0.55 + 0.9 * _patch(flat), 0.15, 1.0)
    b = np.maximum.reduce([
        _blisters(flat, 0.17, 0.9, 0.04, 0.085, 0.012, 0.028, 1) * dense,
        _blisters(flat, 0.36, 0.5, 0.07, 0.15, 0.028, 0.06, 2) * dense,
        _blisters(flat, 0.9, 0.22, 0.15, 0.3, 0.045, 0.08, 3),
    ]) * fade
    flat = flat + n * (lumps + b)[:, None]
    blister = np.clip(b / 0.055, 0, 1)
    return flat.reshape(P.shape), blister.reshape(P.shape[:2]), edge


def mesh(name, mat, at=(0.0, 0.0, 0.0)):
    import bpy

    P, blister, edge = surface()
    nz, na = P.shape[:2]
    # Bottom cap: concentric rings to the centre so the base stays flat.
    base = P[0].copy()
    base[:, 2] = 0.0
    c = base.mean(axis=0)
    caps = [c + (base - c) * f for f in (0.85, 0.6, 0.35, 0.12)]
    rows = caps[::-1] + list(P)
    brow = [np.zeros(na)] * 4 + list(blister)
    erow = [np.ones(na)] * 4 + list(edge)
    tip = P[-1].mean(axis=0)
    tip[2] = dims.SAMOSA_H
    V = np.array([c] + [v for row in rows for v in row] + [tip])
    Bw = np.concatenate([[0.0]] + [r for r in brow] + [[0.0]])
    Ew = np.concatenate([[1.0]] + [r for r in erow] + [[1.0]])
    nr = len(rows)
    idx = np.arange(na)
    faces = [np.stack([np.zeros(na, int), 1 + (idx + 1) % na, 1 + idx], axis=1)]
    quads = []
    for r in range(nr - 1):
        a = 1 + r * na + idx
        b = 1 + r * na + (idx + 1) % na
        quads.append(np.stack([a, b, b + na, a + na], axis=1))
    quads = np.concatenate(quads)
    t = len(V) - 1
    last = 1 + (nr - 1) * na
    tris = [faces[0], np.stack([last + idx, last + (idx + 1) % na, np.full(na, t)], axis=1)]
    # Place: rotate about z, move beside the bag.
    x, y, rot = at
    a = math.radians(rot)
    Rm = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    V = V @ Rm.T + np.array([x, y, 0.0])
    V[:, 2] -= V[:, 2].min()
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], [tuple(f) for f in tris[0]] + [tuple(f) for f in quads] + [tuple(f) for f in tris[1]])
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    for key, vals in (('blister', Bw), ('edge', Ew)):
        at_ = me.attributes.new(key, 'FLOAT', 'POINT')
        at_.data.foreach_set('value', vals.astype(np.float32))
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def material(m):
    """Deep-fried pastry, as in the photo: golden tan with paler, less-fried
    dough where the filling pushes the faces out and deeper caramel towards
    the folds, the seam and the base; a dense, clustered field of tiny pale
    blisters with darker pores between them; a few carom seeds; a thin oily
    sheen."""
    from studio.core import rgba

    mat = m.solid('samosa', '#bf8642', roughness=0.55)
    nt = mat.node_tree
    N, Lk = nt.nodes, nt.links
    p = N['Principled BSDF']
    obj = N.new('ShaderNodeTexCoord').outputs['Object']

    def attr(name):
        a = N.new('ShaderNodeAttribute')
        a.attribute_type = 'GEOMETRY'
        a.attribute_name = name
        return a.outputs['Fac']

    def op(kind, a, b=None, clamp=False):
        n = N.new('ShaderNodeMath')
        n.operation = kind
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                Lk.new(v, n.inputs[i])
        return n.outputs[0]

    def mix(fac, a, b):
        n = N.new('ShaderNodeMix')
        n.data_type = 'RGBA'
        if isinstance(fac, (int, float)):
            n.inputs['Factor'].default_value = fac
        else:
            Lk.new(fac, n.inputs['Factor'])
        for sock, v in (('A', a), ('B', b)):
            if isinstance(v, str):
                n.inputs[sock].default_value = rgba(v)
            else:
                Lk.new(v, n.inputs[sock])
        return n.outputs['Result']

    def noise(scale, detail=4.0, rough=0.55, vec=None):
        n = N.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        Lk.new(vec or obj, n.inputs['Vector'])
        return n.outputs['Fac']

    def ramp01(x, lo, hi):  # smoothstep(lo, hi, x)
        t = op('MULTIPLY', op('SUBTRACT', x, lo), 1.0 / (hi - lo), clamp=True)
        return op('MULTIPLY', op('MULTIPLY', t, t), op('SUBTRACT', 3.0, op('MULTIPLY', t, 2.0)))

    bl = attr('blister')
    edge = attr('edge')
    inner = op('SUBTRACT', 1.0, op('POWER', edge, 0.8))  # 1 mid-face, 0 on folds and base

    # Coordinates warped a little, so nothing looks like a regular lattice.
    wob = N.new('ShaderNodeTexNoise')
    wob.inputs['Scale'].default_value = 3.0
    wob.inputs['Detail'].default_value = 3.0
    Lk.new(obj, wob.inputs['Vector'])
    wv = N.new('ShaderNodeVectorMath')
    wv.operation = 'SCALE'
    wv.inputs['Scale'].default_value = 0.12
    Lk.new(wob.outputs['Color'], wv.inputs[0])
    warped = N.new('ShaderNodeVectorMath')
    warped.operation = 'ADD'
    Lk.new(obj, warped.inputs[0])
    Lk.new(wv.outputs['Vector'], warped.inputs[1])
    W = warped.outputs['Vector']

    # Colour: golden tan in broad, soft zones.
    col = mix(ramp01(noise(0.42, 3.0, vec=W), 0.38, 0.64), '#b2702c', '#c68a3e')
    # Paler dough where the faces bulge and fried less.
    pale = op('MULTIPLY', ramp01(noise(0.6, 4.0, 0.6, vec=W), 0.5, 0.72), inner)
    col = mix(op('MULTIPLY', pale, 0.6), col, '#d6ac64')
    # Deeper caramel patches.
    col = mix(op('MULTIPLY', ramp01(noise(1.3, 4.0, vec=W), 0.54, 0.76), 0.6), col, '#935220')
    # Folds, the seam, the tip and the base fry darker.
    col = mix(op('MULTIPLY', op('POWER', edge, 1.3), 0.78), col, '#743d14')
    col = mix(op('MULTIPLY', bl, 0.3), col, '#d3a865')

    # Blisters: tiny irregular bubbles of paler, crisp dough, clustered.
    def bubbles(scale, r0, r1, keep):
        v = N.new('ShaderNodeTexVoronoi')
        v.inputs['Scale'].default_value = scale
        v.inputs['Randomness'].default_value = 1.0
        Lk.new(W, v.inputs['Vector'])
        pick = N.new('ShaderNodeSeparateColor')
        Lk.new(v.outputs['Color'], pick.inputs['Color'])
        size = op('ADD', r0, op('MULTIPLY', pick.outputs[0], r1 - r0))
        dome = op('SUBTRACT', 1.0, op('DIVIDE', v.outputs['Distance'], size), clamp=True)
        return op('MULTIPLY', op('POWER', dome, 0.6), op('GREATER_THAN', pick.outputs[1], 1.0 - keep))

    cluster = ramp01(noise(1.7, 3.0, vec=W), 0.36, 0.62)
    fine = op('MAXIMUM', bubbles(13.0, 0.22, 0.42, 0.75), op('MULTIPLY', bubbles(26.0, 0.25, 0.45, 0.7), 0.8))
    fine = op('MULTIPLY', fine, op('ADD', 0.25, op('MULTIPLY', cluster, 0.75)))
    mid = op('MULTIPLY', bubbles(7.0, 0.25, 0.48, 0.6), op('ADD', 0.35, op('MULTIPLY', cluster, 0.65)))
    big = op('MULTIPLY', bubbles(4.0, 0.14, 0.32, 0.35), inner)
    blis = op('MAXIMUM', op('MAXIMUM', fine, op('MULTIPLY', mid, 0.85)), big)
    col = mix(op('MULTIPLY', blis, 0.5), col, '#e0bd7a')
    # Pores between the bubbles: small darker pits.
    pores = N.new('ShaderNodeTexVoronoi')
    pores.inputs['Scale'].default_value = 34.0
    Lk.new(W, pores.inputs['Vector'])
    pk = N.new('ShaderNodeSeparateColor')
    Lk.new(pores.outputs['Color'], pk.inputs['Color'])
    pit = op('MULTIPLY', op('LESS_THAN', pores.outputs['Distance'], 0.16), op('GREATER_THAN', pk.outputs[2], 0.78))
    col = mix(op('MULTIPLY', pit, 0.45), col, '#7a4519')
    # A few carom seeds.
    seeds = N.new('ShaderNodeTexVoronoi')
    seeds.inputs['Scale'].default_value = 2.4
    Lk.new(W, seeds.inputs['Vector'])
    sd = op('LESS_THAN', seeds.outputs['Distance'], 0.04)
    which = N.new('ShaderNodeSeparateColor')
    Lk.new(seeds.outputs['Color'], which.inputs['Color'])
    sd = op('MULTIPLY', sd, op('GREATER_THAN', which.outputs[2], 0.7))
    col = mix(op('MULTIPLY', sd, 0.8), col, '#3e2511')
    Lk.new(col, p.inputs['Base Color'])

    # Relief on top of the geometric blisters: the bubbles stand proud, the
    # pores sink, and a fine crumb texture over everything.
    height = op('ADD', op('MULTIPLY', op('MAXIMUM', blis, mid), 0.6), op('MULTIPLY', noise(48.0, 6.0, 0.65), 0.3))
    height = op('ADD', height, op('MULTIPLY', noise(9.0, 4.0), 0.3))
    height = op('SUBTRACT', height, op('MULTIPLY', pit, 0.3))
    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 1.0
    bump.inputs['Distance'].default_value = 0.03
    Lk.new(height, bump.inputs['Height'])
    Lk.new(bump.outputs['Normal'], p.inputs['Normal'])
    Lk.new(bump.outputs['Normal'], p.inputs['Coat Normal'])

    # A thin film of oil: slicker on the bubbles, drier in the pores.
    rough = op('ADD', 0.5, op('MULTIPLY', noise(1.3, 3.0), 0.16))
    rough = op('SUBTRACT', rough, op('MULTIPLY', blis, 0.12))
    Lk.new(rough, p.inputs['Roughness'])
    p.inputs['Specular IOR Level'].default_value = 0.42
    p.inputs['Coat Weight'].default_value = 0.14
    p.inputs['Coat Roughness'].default_value = 0.28
    p.inputs['Coat IOR'].default_value = 1.47
    p.inputs['Subsurface Weight'].default_value = 0.08
    p.inputs['Subsurface Radius'].default_value = (1.0, 0.5, 0.22)
    p.inputs['Subsurface Scale'].default_value = 0.12
    return mat
