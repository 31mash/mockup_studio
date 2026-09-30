"""Folded tissue napkin geometry, in cm.

The napkin is built the way it is made: one flat sheet with exact UVs (the
artwork covers the unfolded sheet), folded twice by a bend deformer. Each fold
wraps the paper round a cylinder whose axis sits just above the stack, so every
layer bends on its own radius, the outer layers use a little more paper, and
the free edges end up slightly staggered, as on a real napkin. The result is a
single continuous surface: the folds are real, rounded paper folds.

Pure numpy for the shape; `mesh()` turns it into a Blender object.
"""

from __future__ import annotations

import math

import numpy as np

import dims


def _samples(total, step, dense=(), edge=None):
    """Monotonic samples over [0, total]: `step` apart, and finer inside each
    (centre, half_width, fine_step) band of `dense`."""
    pts = [np.linspace(0.0, total, int(round(total / step)) + 1)]
    keep = np.ones_like(pts[0], dtype=bool)
    for c, hw, fs in dense:
        keep &= np.abs(pts[0] - c) > hw
        pts.append(np.arange(max(0.0, c - hw), min(total, c + hw) + 1e-9, fs))
    pts[0] = pts[0][keep]
    if edge:
        pts.append(np.arange(0.0, edge[0], edge[1]))
        pts.append(np.array([0.0, total]))
    return np.unique(np.round(np.concatenate(pts), 6))


def deckle(u, rng, depth):
    """A torn perforation line: how far (cm) the edge is torn back at each u.
    Irregular teeth, mostly shallow with the odd deeper bite, a slow wander,
    and fibre-scale jitter."""
    L = float(u.max()) + 1.0
    xs = [0.0]
    while xs[-1] < L:
        xs.append(xs[-1] + rng.uniform(0.07, 0.34))
    xs = np.array(xs)
    ys = rng.uniform(0.0, 1.0, len(xs)) ** 2.2 * depth * 0.75
    bites = rng.random(len(xs)) < 0.07
    ys[bites] = rng.uniform(0.6, 1.0, bites.sum()) * depth
    e = np.interp(u, xs, ys)
    fx = np.arange(0.0, L, 0.035)
    e += np.interp(u, fx, rng.normal(0.0, depth * 0.05, len(fx)))
    ph = rng.uniform(0, 2 * math.pi, 2)
    e += depth * 0.22 * (1 + 0.6 * np.sin(u * 0.55 + ph[0]) + 0.4 * np.sin(u * 1.7 + ph[1])) / 2
    return np.clip(e, 0.0, depth * 1.1)


def _fold(P, z, p0, n, h):
    """Folds everything on the +n side of the line through p0 (plan, 2D) over
    onto the stack, round an axis at height h. Returns new (P, z)."""
    d = (P - p0) @ n
    rho = h - z
    P2, z2 = P.copy(), z.copy()
    m = d > 0
    if not m.any():
        return P2, z2
    dm, rm = d[m], rho[m]
    foot = P[m] - dm[:, None] * n  # on the fold line
    th = np.minimum(dm / rm, math.pi)
    flat = dm > math.pi * rm
    out = np.where(flat, 0.0, rm * np.sin(th)) - np.where(flat, dm - math.pi * rm, 0.0)
    P2[m] = foot + out[:, None] * n
    z2[m] = h - rm * np.cos(th)
    return P2, z2


def _smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def napkin(seed: int = 1, loft: float = 0.1):
    """The folded napkin: vertices (rows, cols, 3) in cm, centred on the
    origin, front edge at -Y, bottom face resting on z = 0 once solidified,
    and UVs (rows, cols, 2) over the unfolded sheet."""
    rng = np.random.default_rng(seed)
    W, D, L, k = dims.W, dims.D, dims.LAYER, dims.SKEW
    SW, SH = dims.SHEET_W, dims.SHEET_H

    # Parameter grid: s across the sheet (0..1, fold 1 exactly at s = 0.5),
    # v up the sheet. Finer where the paper bends and along the torn edge.
    s = _samples(SW, 0.05, dense=[(W, 0.32, 0.012)]) / SW
    v = _samples(SH, 0.1, dense=[(D, 0.42, 0.014)], edge=(0.6, 0.04))
    S, V = np.meshgrid(s, v)

    # The sheet is cut a hair out of square so the skewed fold 1 still brings
    # the two left edges together.
    u = S * (SW + 2 * k * (V - D))

    # The torn front edge: pull the first rows back along the tear.
    e = deckle(u[0], rng, dims.DECKLE)
    blend = np.clip(1.0 - V / 0.55, 0.0, 1.0)
    V = V + e[None, :] * blend

    uv = np.stack([u / SW, V / SH], axis=-1)

    P = np.stack([u, V], axis=-1).reshape(-1, 2)
    z = np.zeros(len(P))

    # Fold 1: the right half over the left, along a line a touch off vertical.
    n1 = np.array([1.0, -k]) / math.hypot(1.0, k)
    P, z = _fold(P, z, np.array([W, D]), n1, 0.5 * L)
    # Fold 2: the back part down over the front.
    P, z = _fold(P, z, np.array([0.0, D]), np.array([0.0, 1.0]), 1.5 * L)

    X = P[:, 0] - W / 2
    Y = P[:, 1] - D / 2

    # Loft: pressed flat at the folds, the layers relax apart towards the free
    # edges, the top ones most, with a soft, uneven swell across the flap.
    frac = np.clip(z / (3 * L), 0.0, 1.0)
    to_right = W / 2 - X
    edge_f = _smoothstep(0.0, 4.5, D / 2 - Y) * _smoothstep(0.0, 2.5, to_right) * (0.6 + 0.4 * _smoothstep(0.0, 13.0, to_right))
    ph = rng.uniform(0, 2 * math.pi, 4)
    swell = 0.5 + 0.25 * np.sin(X * 0.42 + ph[0]) * np.cos(Y * 0.5 + ph[1]) + 0.25 * np.sin(X * 0.9 + Y * 0.7 + ph[2])
    z = z + frac * loft * edge_f * (0.55 + 0.45 * swell)

    # The loose corner at the front left lifts off the table a little.
    corner = _smoothstep(4.0, 0.0, np.hypot(X + W / 2, Y + D / 2)) ** 2
    z = z + 0.09 * corner * (0.8 + 0.2 * np.sin(ph[3] + X))

    z = z + dims.PLY / 2
    verts = np.stack([X, Y, z], axis=-1).reshape(len(v), len(s), 3)
    return verts, uv


def drape(verts, under, cell: float = 0.2, clearance: float = 0.006):
    """Lays a napkin (verts, world XY) over the napkins in `under` (a list of
    vertex arrays): every point is raised by the smoothed height of what lies
    beneath it, so the paper settles over them without touching."""
    if not under:
        return verts
    pts = np.concatenate([u.reshape(-1, 3) for u in under])
    flat = verts.reshape(-1, 3)
    lo = np.minimum(pts[:, :2].min(0), flat[:, :2].min(0)) - 1.0
    hi = np.maximum(pts[:, :2].max(0), flat[:, :2].max(0)) + 1.0
    shape = tuple(np.ceil((hi - lo) / cell).astype(int) + 1)
    H = np.zeros(shape)
    ij = np.floor((pts[:, :2] - lo) / cell).astype(int)
    np.maximum.at(H, (ij[:, 0], ij[:, 1]), pts[:, 2] + dims.PLY / 2)
    # Dilate (so the smoothed field never dips below the paper under it),
    # then smooth into a gentle drape.
    r = 2
    Hd = H.copy()
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            Hd = np.maximum(Hd, np.roll(np.roll(H, di, 0), dj, 1))
    for _ in range(2):
        Hs = np.zeros_like(Hd)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                Hs += np.roll(np.roll(Hd, di, 0), dj, 1)
        Hd = Hs / 9.0
    # Bilinear sample under every vertex.
    g = (flat[:, :2] - lo) / cell
    i0 = np.clip(np.floor(g).astype(int), 0, np.array(shape) - 2)
    t = g - i0
    h = (
        Hd[i0[:, 0], i0[:, 1]] * (1 - t[:, 0]) * (1 - t[:, 1])
        + Hd[i0[:, 0] + 1, i0[:, 1]] * t[:, 0] * (1 - t[:, 1])
        + Hd[i0[:, 0], i0[:, 1] + 1] * (1 - t[:, 0]) * t[:, 1]
        + Hd[i0[:, 0] + 1, i0[:, 1] + 1] * t[:, 0] * t[:, 1]
    )
    out = flat.copy()
    out[:, 2] += h + clearance
    return out.reshape(verts.shape)


def place(verts, dx=0.0, dy=0.0, rot_deg=0.0):
    a = math.radians(rot_deg)
    c, s_ = math.cos(a), math.sin(a)
    out = verts.copy()
    x, y = verts[..., 0], verts[..., 1]
    out[..., 0] = c * x - s_ * y + dx
    out[..., 1] = s_ * x + c * y + dy
    return out


def mesh(name, verts, uv, material, thickness=dims.PLY):
    """A Blender object from the grid, with the paper's thickness as a
    Solidify modifier (centred, so the layers never touch)."""
    import bpy

    rows, cols, _ = verts.shape
    me = bpy.data.meshes.new(name)
    me.vertices.add(rows * cols)
    me.vertices.foreach_set('co', verts.reshape(-1).astype(np.float32))
    idx = np.arange(rows * cols).reshape(rows, cols)
    quads = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], axis=-1).reshape(-1, 4)
    F = len(quads)
    me.loops.add(F * 4)
    me.loops.foreach_set('vertex_index', quads.reshape(-1).astype(np.int32))
    me.polygons.add(F)
    me.polygons.foreach_set('loop_start', np.arange(0, F * 4, 4, dtype=np.int32))
    uvl = me.uv_layers.new(name='UVMap')
    uvl.data.foreach_set('uv', uv.reshape(-1, 2)[quads.reshape(-1)].reshape(-1).astype(np.float32))
    me.update(calc_edges=True)
    me.validate()
    me.shade_smooth()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    sol = ob.modifiers.new('paper', 'SOLIDIFY')
    sol.thickness = thickness
    sol.offset = 0.0
    sol.use_even_offset = True
    sol.use_quality_normals = True
    return ob
