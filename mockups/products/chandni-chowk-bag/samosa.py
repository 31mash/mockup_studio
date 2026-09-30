"""A Punjabi samosa sitting on its base: shape in numpy, a procedural
fried-pastry material.

Shape. Horizontal slices are rounded triangles that shrink to the tip: the
pastry is a cone of dough folded round the filling, so the three faces bulge,
two corners are soft folds and the third, at the back, is the pinched seam
where the cone was sealed: a thin crimped fin running up to the tip. At the
base the corners flatten out into thin crisp feet. Low-frequency lumps (the
filling pushing through) move the surface; blisters, grain and browning are
in the shader.
"""

from __future__ import annotations

import math

import numpy as np

import dims

NA = 256  # samples round each slice
NZ = 120  # slices
TOP = 0.985  # the last ring's height, as a fraction of the samosa's height


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


def rings():
    """Vertex rings (NZ x NA x 3), bottom to tip, before placement."""
    R0, H = dims.SAMOSA_R, dims.SAMOSA_H
    th = np.linspace(0, 2 * np.pi, NA, endpoint=False)
    # Corners: the seam at the back (+Y), soft folds front-left and front-right.
    corners = np.radians([90.0, 210.0, 330.0])
    scale = np.array([1.04, 0.97, 1.0])
    # Distance (deg) to the nearest corner and which one it is.
    dd = np.degrees(np.abs((th[:, None] - corners[None, :] + np.pi) % (2 * np.pi) - np.pi))
    near = np.argmin(dd, axis=1)
    dmin = dd[np.arange(NA), near]
    face = np.radians(60.0 - dmin)  # 0 at a corner, 60 deg at a face centre
    tri = math.cos(math.radians(60)) / np.cos(face)  # 1 at corners, 0.5 mid-face
    seam = near == 0

    zs = np.linspace(0, 1, NZ) ** 1.15 * H * TOP  # denser at the base; the tip is a single point
    out = []
    for z in zs:
        h = z / H
        bulge = 0.24 + 0.07 * math.sin(math.pi * min(1.0, h * 1.3))  # faces fill out
        r = (1 - bulge) * tri + bulge
        r = r * scale[near]
        # Round the folds (more so higher up), keep the seam and the feet sharp.
        soft = _gauss_smooth(r, 3.0 + 4.0 * min(1.0, h * 2.2))
        sharp = _gauss_smooth(r, 2.2 + 2.0 * h)
        wsharp = np.where(seam, 1.0, 0.0) * np.exp(-(dmin / 26.0) ** 2)
        r = soft * (1 - wsharp) + sharp * wsharp
        # Profile up to the tip: slightly convex faces, a rounded point.
        prof = (1 - h) ** 0.82 * (1 + 0.08 * math.sin(math.pi * h))
        rr = R0 * r * prof
        # Base: a tight roll under the edge and flat, flared feet at the corners.
        rb = 0.3
        if z < rb:
            rr = rr - (rb - math.sqrt(max(0.0, rb * rb - (rb - z) ** 2))) * 0.9
        # A thin crisp lip all round the base, where the pastry edge sits on the plate.
        rr = rr + 0.2 * math.exp(-z / 0.07)
        feet = 0.55 * math.exp(-z / 0.17) * np.exp(-(dmin / 11.0) ** 2) * np.where(seam, 0.6, 1.0)
        rr = rr + feet
        # The seam fin: pressed pastry standing proud of the back corner, crimped.
        ph = z * 2 * math.pi / 0.9 + 1.3 * math.sin(z * 1.9) + 0.7 * math.sin(z * 4.3 + 1.0)
        pleat = 1 + 0.2 * math.sin(ph) * (0.6 + 0.4 * math.sin(z * 2.7 + 0.4))
        fin = 0.34 * (1 - h) ** 0.45 * pleat * np.exp(-(dmin / 2.8) ** 2) * seam
        rr = rr + fin
        # Lean: the tip sits over the back half, a little off to one side.
        cx = 0.25 * h ** 1.6
        cy = 0.9 * h ** 1.4
        ring = np.stack([cx + rr * np.cos(th), cy + rr * np.sin(th), np.full(NA, z)], axis=1)
        out.append(ring)
    P = np.array(out)
    # Lumps of filling under the pastry, and small ones; nothing moves at the base plane.
    flat = P.reshape(-1, 3)
    centre = np.array([0.0, 0.3, H * 0.3])
    radial = flat - centre
    radial[:, 2] *= 0.35
    radial /= np.linalg.norm(radial, axis=1, keepdims=True) + 1e-9
    zfac = np.clip(flat[:, 2] / 0.5, 0, 1) * np.clip((H - flat[:, 2]) / 0.8, 0, 1)
    disp = (0.07 * _lumps(flat) + 0.025 * _small(flat)) * zfac
    flat += radial * disp[:, None]
    return P


def mesh(name, mat, at=(0.0, 0.0, 0.0)):
    import bpy

    P = rings()
    nz, na = P.shape[:2]
    # Bottom cap: concentric rings to the centre so the base stays flat.
    base = P[0]
    c = base.mean(axis=0)
    caps = [c + (base - c) * f for f in (0.8, 0.55, 0.3, 0.1)]
    rows = caps[::-1] + list(P)
    tip = P[-1].mean(axis=0)
    tip[2] = dims.SAMOSA_H
    verts = [tuple(c)] + [tuple(v) for row in rows for v in row] + [tuple(tip)]
    nr = len(rows)
    faces = []
    for j in range(na):  # centre fan
        faces.append((0, 1 + (j + 1) % na, 1 + j))
    for r in range(nr - 1):
        for j in range(na):
            a = 1 + r * na + j
            b = 1 + r * na + (j + 1) % na
            faces.append((a, b, b + na, a + na))
    tip = len(verts) - 1
    last = 1 + (nr - 1) * na
    for j in range(na):
        faces.append((last + j, last + (j + 1) % na, tip))
    V = np.array(verts)
    # Place: rotate about z, move beside the bag.
    x, y, rot = at
    a = math.radians(rot)
    Rm = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    V = V @ Rm.T + np.array([x, y, 0.0])
    V[:, 2] -= V[:, 2].min()
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], faces)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def material(m):
    """Deep-fried pastry: golden brown, deeper on the folds, the seam and the
    base; covered in small raised blisters (paler on top, browner between);
    a few carom seeds; a light oily sheen."""
    from studio.core import rgba

    mat = m.solid('samosa', '#b77a3c', roughness=0.5)
    nt = mat.node_tree
    N, Lk = nt.nodes, nt.links
    p = N['Principled BSDF']
    obj = N.new('ShaderNodeTexCoord').outputs['Object']

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

    def noise(scale, detail=4.0, rough=0.55):
        n = N.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        Lk.new(obj, n.inputs['Vector'])
        return n.outputs['Fac']

    def ramp01(x, lo, hi):  # (x - lo) / (hi - lo), clamped
        return op('MULTIPLY', op('SUBTRACT', x, lo), 1.0 / (hi - lo), clamp=True)

    # Wobbled coordinates, so blisters are irregular rather than round.
    wob = N.new('ShaderNodeTexNoise')
    wob.inputs['Scale'].default_value = 3.0
    wob.inputs['Detail'].default_value = 2.0
    Lk.new(obj, wob.inputs['Vector'])
    wv = N.new('ShaderNodeVectorMath')
    wv.operation = 'SCALE'
    wv.inputs['Scale'].default_value = 0.09
    Lk.new(wob.outputs['Color'], wv.inputs[0])
    warped = N.new('ShaderNodeVectorMath')
    warped.operation = 'ADD'
    Lk.new(obj, warped.inputs[0])
    Lk.new(wv.outputs['Vector'], warped.inputs[1])

    def blisters(scale, r0, r1):
        v = N.new('ShaderNodeTexVoronoi')
        v.feature = 'F1'
        v.inputs['Scale'].default_value = scale
        Lk.new(warped.outputs['Vector'], v.inputs['Vector'])
        size = N.new('ShaderNodeSeparateColor')
        Lk.new(v.outputs['Color'], size.inputs['Color'])
        rad = op('ADD', op('MULTIPLY', size.outputs[0], r1 - r0), r0)
        dome = op('SUBTRACT', 1.0, op('DIVIDE', v.outputs['Distance'], rad), clamp=True)
        return op('POWER', dome, 0.45), size.outputs[1]

    geo = N.new('ShaderNodeNewGeometry')
    sep = N.new('ShaderNodeSeparateXYZ')
    Lk.new(geo.outputs['Position'], sep.inputs['Vector'])

    big, pick = blisters(2.8, 0.12, 0.5)
    small, _ = blisters(8.0, 0.2, 0.5)
    cluster = ramp01(noise(0.8, 2.0), 0.36, 0.6)
    bl = op('MAXIMUM', op('MULTIPLY', big, cluster), op('MULTIPLY', small, 0.55))
    grain = noise(30.0, 6.0, 0.6)
    height = op('ADD', bl, op('MULTIPLY', grain, 0.25))

    # Colour: golden with broad browner patches and a finer mottle.
    col = mix(op('MULTIPLY', ramp01(noise(0.55, 4.0), 0.38, 0.64), 0.7), '#d99a50', '#a8642a')
    col = mix(op('MULTIPLY', ramp01(noise(1.8, 3.0), 0.48, 0.66), 0.45), col, '#8f5024')
    # Folds, seam and tip brown deeper; so does the base, where it sat in the oil.
    edge = ramp01(geo.outputs['Pointiness'], 0.51, 0.56)
    col = mix(op('MULTIPLY', edge, 0.9), col, '#6e3a12')
    low = op('SUBTRACT', 1.0, ramp01(sep.outputs['Z'], 0.05, 0.6))
    col = mix(op('MULTIPLY', low, 0.65), col, '#6d3a16')
    # Blisters: most with pale tops, some fried a deeper brown; browner hollows between.
    tone = mix(op('GREATER_THAN', pick, 0.7), '#e8b56c', '#7c4015')
    col = mix(op('MULTIPLY', op('POWER', bl, 1.5), 0.6), col, tone)
    col = mix(op('MULTIPLY', op('SUBTRACT', 1.0, bl), 0.2), col, '#7f4518')
    # A few carom seeds.
    seeds = N.new('ShaderNodeTexVoronoi')
    seeds.inputs['Scale'].default_value = 3.1
    Lk.new(obj, seeds.inputs['Vector'])
    sd = op('LESS_THAN', seeds.outputs['Distance'], 0.05)
    which = N.new('ShaderNodeSeparateColor')
    Lk.new(seeds.outputs['Color'], which.inputs['Color'])
    sd = op('MULTIPLY', sd, op('GREATER_THAN', which.outputs[2], 0.6))
    col = mix(op('MULTIPLY', sd, 0.8), col, '#3b2414')
    Lk.new(col, p.inputs['Base Color'])

    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 1.0
    bump.inputs['Distance'].default_value = 0.07
    Lk.new(height, bump.inputs['Height'])
    Lk.new(bump.outputs['Normal'], p.inputs['Normal'])
    Lk.new(bump.outputs['Normal'], p.inputs['Coat Normal'])

    # Oil: a light sheen, glossier in patches.
    rough = op('ADD', 0.3, op('MULTIPLY', noise(1.3, 3.0), 0.34))
    Lk.new(rough, p.inputs['Roughness'])
    p.inputs['Specular IOR Level'].default_value = 0.5
    p.inputs['Coat Weight'].default_value = 0.22
    p.inputs['Coat Roughness'].default_value = 0.32
    p.inputs['Subsurface Weight'].default_value = 0.05
    p.inputs['Subsurface Radius'].default_value = (1.0, 0.45, 0.2)
    p.inputs['Subsurface Scale'].default_value = 0.1
    return mat
