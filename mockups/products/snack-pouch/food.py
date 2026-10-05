"""Namkeen sticks: crinkly fried gram-flour sticks, packed into the pouch.

A few dozen stick meshes (bent, knobbly, with broken blunt ends) are
instanced a few hundred times. Placement is a seeded packing of capsules that
never overlap each other or the film: a dense layer against the front and
back film (what you see through the pouch), relaxed on the unrolled film so
the sticks lie close like settled namkeen, sticks lying on top of the heap
and on the gusset, a second layer further in, broken pieces in the gaps, and
some in the middle. A hidden core, painted as more sticks packed tight,
fills what is left, so gaps show namkeen further in, not daylight.
"""

from __future__ import annotations

import math

import numpy as np

import dims
import pouch


# ----------------------------------------------------------------- geometry


def stick_mesh(name: str, L: float, r: float, bend: float, seed: int):
    """A stick along local X, chord from -L/2 to L/2, bowed towards +Y by
    `bend`. Extruded and fried dough: a few soft ridges from the die running
    along it (twisting a little), crinkled into small bulges every few
    millimetres, gently kinked, with blunt broken ends."""
    import bpy
    from mathutils import Vector, noise

    rng = np.random.default_rng(seed)
    ring_n = 20
    cap = 0.45 * r
    body = L - 2 * cap
    n_body = max(10, int(body / 0.035))
    xs = list(np.linspace(-body / 2, body / 2, n_body + 1))
    # End caps: blunt, slightly irregular breaks.
    cap_steps = [(0.12, 0.97), (0.25, 0.88), (0.35, 0.68), (0.41, 0.34)]
    rings = []  # (x, scale, end_roughness)
    for dx, s in reversed(cap_steps):
        rings.append((-body / 2 - dx * r, s, 1.0))
    for x in xs:
        rings.append((x, 1.0, 0.0))
    for dx, s in cap_steps:
        rings.append((body / 2 + dx * r, s, 1.0))
    off = Vector((rng.uniform(0, 50), rng.uniform(0, 50), rng.uniform(0, 50)))
    ridges = int(rng.integers(6, 9))
    ridge_amp = float(rng.uniform(0.03, 0.055))
    twist = float(rng.uniform(-1.4, 1.4))  # radians per cm
    crinkle = float(rng.uniform(0.085, 0.13))
    flat = float(rng.uniform(0.86, 0.97))

    def centre(x):
        cy = bend * (1 - (2 * x / L) ** 2) - bend / 2
        cy += 0.04 * noise.noise(Vector((x * 0.8, 1.7, seed * 0.37)))
        cz = 0.035 * noise.noise(Vector((x * 0.8, 6.1, seed * 0.53)))
        return cy, cz

    verts = []
    for x, s, rough in rings:
        cy, cz = centre(x)
        taper = 1.0 + 0.07 * noise.noise(Vector((x * 1.1, 0.3, seed * 1.7))) + 0.04 * noise.noise(Vector((x * 3.0, 0.7, seed * 2.9)))
        for j in range(ring_n):
            t = 2 * math.pi * j / ring_n
            ct, st = math.cos(t), math.sin(t)
            p = Vector((x * 3.3, ct * 0.85, st * 0.85)) + off
            k = 1.0 + ridge_amp * s * math.cos(ridges * t + twist * x)
            k += crinkle * noise.noise(p) + 0.05 * noise.noise(p * 2.4) + 0.025 * noise.noise(p * 6.0)
            k += rough * 0.2 * noise.noise(p * 1.9 + Vector((4, 4, 4)))
            rad = r * s * taper * k
            verts.append((x, cy + rad * ct, cz + rad * st * flat))
    # Tip vertices close the ends.
    x0 = rings[0][0] - 0.04 * r
    x1 = rings[-1][0] + 0.04 * r
    c0 = centre(x0)
    c1 = centre(x1)
    verts.append((x0, c0[0], c0[1]))
    verts.append((x1, c1[0], c1[1]))
    nr = len(rings)
    faces = []
    for i in range(nr - 1):
        for j in range(ring_n):
            j2 = (j + 1) % ring_n
            faces.append((i * ring_n + j, i * ring_n + j2, (i + 1) * ring_n + j2, (i + 1) * ring_n + j))
    t0 = nr * ring_n
    t1 = t0 + 1
    for j in range(ring_n):
        j2 = (j + 1) % ring_n
        faces.append((t0, j2, j))
        faces.append(((nr - 1) * ring_n + j, (nr - 1) * ring_n + j2, t1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.update()
    return me


def crumb_mesh(name: str, r: float, seed: int):
    import bmesh
    import bpy
    from mathutils import Vector, noise

    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    off = Vector((seed * 3.3, seed * 1.1, seed * 7.7))
    for v in bm.verts:
        d = v.co.normalized()
        v.co = d * r * (1 + 0.45 * noise.noise(d * 1.6 + off) + 0.15 * noise.noise(d * 4.0 + off))
        v.co.x *= 1.25
        v.co.z *= 0.55
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    return me


# ----------------------------------------------------------------- packing


def segdist(p0, p1, A, B):
    """Distances between segment p0-p1 and each segment A[i]-B[i]."""
    d1 = p1 - p0
    d2 = B - A
    r = p0 - A
    a = float(d1 @ d1)
    e = np.einsum('ij,ij->i', d2, d2)
    f = np.einsum('ij,ij->i', d2, r)
    c = r @ d1
    b = d2 @ d1
    denom = a * e - b * b
    s = np.where(denom > 1e-9, np.clip((b * f - c * e) / np.where(denom > 1e-9, denom, 1), 0, 1), 0.0)
    t = (b * s + f) / e
    lo = t < 0
    hi = t > 1
    s = np.where(lo, np.clip(-c / a, 0, 1), s)
    s = np.where(hi, np.clip((b - c) / a, 0, 1), s)
    t = np.clip(t, 0, 1)
    d = (p0 + s[:, None] * d1) - (A + t[:, None] * d2)
    return np.sqrt(np.einsum('ij,ij->i', d, d))


class Packer:
    GAP = 0.012

    def __init__(self, cap: int = 6000):
        self.A = np.zeros((cap, 3))
        self.B = np.zeros((cap, 3))
        self.C = np.zeros((cap, 3))
        self.H = np.zeros(cap)
        self.R = np.zeros(cap)
        self.n = 0
        self.items = []

    def free(self, a, b, r):
        n = self.n
        if n == 0:
            return True
        c = 0.5 * (a + b)
        h = 0.5 * float(np.linalg.norm(b - a))
        dc = np.linalg.norm(self.C[:n] - c, axis=1)
        idx = np.nonzero(dc < self.H[:n] + h + self.R[:n] + r + self.GAP)[0]
        if len(idx) == 0:
            return True
        d = segdist(a, b, self.A[idx], self.B[idx])
        return bool(np.all(d > self.R[idx] + r + self.GAP))

    def add(self, a, b, r, item):
        i = self.n
        self.A[i], self.B[i] = a, b
        self.C[i] = 0.5 * (a + b)
        self.H[i] = 0.5 * float(np.linalg.norm(b - a))
        self.R[i] = r
        self.n += 1
        self.items.append(item)


CLEAR = 0.05  # gap between a stick and the film
LONG = 0.5 * (dims.STICK_L[0] + dims.STICK_L_SHORT[1])  # whole sticks are longer than this


def _reff(r, bend):
    """Radius of the capsule that holds a stick: its crinkles, kinks and bow."""
    return r * 1.12 + bend * 0.5 + 0.02
CORE_INSET = 1.95  # the hidden core sits this far in from the film


def _unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _first_fit(centres, d, hl, reff, n_pts=7):
    """centres: N x K x 3 candidate centres (K pushes each). Returns, per
    candidate, the first push whose axis points all sit inside the film, or -1."""
    N, K = centres.shape[:2]
    t = np.linspace(-1.0, 1.0, n_pts)
    pts = centres[:, :, None, :] + d[:, None, None, :] * (t[None, :] * hl[:, None])[:, None, :, None]
    margin = np.repeat(np.repeat((reff + CLEAR)[:, None], K, 1)[:, :, None], n_pts, 2)
    ok = pouch.inside(pts.reshape(-1, 3), margin.ravel()).reshape(N, K, n_pts).all(axis=2)
    first = np.argmax(ok, axis=1)
    return np.where(ok[np.arange(N), first], first, -1)


def _pair_closest(A0, A1):
    """Closest points between every pair of 2D segments A0[i]-A1[i] and
    A0[j]-A1[j]. Returns (pi, pj, dist) as N x N (x 2) arrays."""
    p0, q0 = A0[:, None, :], A0[None, :, :]
    d1 = (A1 - A0)[:, None, :]
    d2 = (A1 - A0)[None, :, :]
    r = p0 - q0
    a = np.sum(d1 * d1, -1)
    e = np.sum(d2 * d2, -1)
    f = np.sum(d2 * r, -1)
    c = np.sum(d1 * r, -1)
    b = np.sum(d1 * d2, -1)
    denom = a * e - b * b
    s = np.where(denom > 1e-9, np.clip((b * f - c * e) / np.where(denom > 1e-9, denom, 1), 0, 1), 0.0)
    t = (b * s + f) / e
    s = np.where(t < 0, np.clip(-c / a, 0, 1), s)
    s = np.where(t > 1, np.clip((b - c) / a, 0, 1), s)
    t = np.clip(t, 0, 1)
    pi = p0 + s[..., None] * d1
    pj = q0 + t[..., None] * d2
    return pi, pj, np.linalg.norm(pi - pj, axis=-1)


def relax_layer(rng, P, pool, cover, side, deeper=0.0, iters=700, gap=0.03, align=0.55):
    """A dense single layer of sticks against one panel. The stick axes lie
    on the film set in by about a stick radius; on that surface, unrolled
    (s = arc length across, z = height), sticks are scattered, pushed apart
    and turned until they no longer overlap, then wrapped back onto it.
    Returns candidates (proto index, centres with inward pushes, dir, bend dir)."""
    inset = float(np.mean(P[pool, 1] * 1.1 + P[pool, 2] * 0.5)) + CLEAR + 0.07 + deeper
    xi_g = np.linspace(-0.999, 0.999, 801)

    def lens(z):
        a = float(pouch.a_at(z)) - 1.25 * inset
        b = max(0.02, float(pouch.b_at(z)) - inset)
        x = a * xi_g
        y = b * pouch.g(xi_g)
        acc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
        acc -= acc[-1] / 2
        return a, b, acc

    # Usable half-width of the unrolled layer by height (sticks need depth).
    zt = np.linspace(0.0, dims.Z_TOP, 200)
    half = np.array([lens(z)[2][-1] for z in zt]) - 0.35
    half = np.where(pouch.b_at(zt) - inset > 0.3, half, 0.0)
    z_lo = 0.6
    # As many sticks as cover `cover` of the layer (the rest stays gaps).
    area = float(np.sum(2 * half * (zt < dims.FILL)) * (zt[1] - zt[0]))
    idx = rng.choice(pool, 400)
    reff = _reff(P[idx, 1], P[idx, 2])
    n = int(np.searchsorted(np.cumsum(2 * reff * P[idx, 0]), cover * area))
    idx, reff = idx[:n], reff[:n]
    L = P[idx, 0]
    h = L / 2 - P[idx, 1]
    c = np.stack([np.zeros(n), rng.uniform(z_lo, dims.FILL, n)], 1)
    c[:, 0] = rng.uniform(-1, 1, n) * np.interp(c[:, 1], zt, half)
    field = 1.57 + 1.1 * np.sin(0.5 * c[:, 0] + 0.33 * c[:, 1] + 1.0 + side) + 0.7 * np.sin(0.8 * c[:, 1] - 0.4 * c[:, 0] + 2.3)
    th = np.where(rng.random(n) < align, field + rng.normal(0, 0.35, n), rng.uniform(0, math.pi, n))
    eye = np.eye(n, dtype=bool)
    for it in range(iters):
        dv = np.stack([np.cos(th), np.sin(th)], 1)
        pi, pj, dist = _pair_closest(c - dv * h[:, None], c + dv * h[:, None])
        over = np.where(eye, 0.0, np.maximum(0.0, reff[:, None] + reff[None, :] + gap - dist))
        if over.max() < 1e-3:
            break
        sep = (pi - pj) / np.maximum(dist, 1e-6)[..., None]
        # Crossing sticks have no separation direction: part them across
        # the other stick, away from its centre.
        cross = dist < 1e-4
        if cross.any():
            nj = np.stack([-dv[:, 1], dv[:, 0]], 1)[None, :, :].repeat(n, 0)
            side_ = np.sign(np.sum((c[:, None, :] - c[None, :, :]) * nj, -1) + 1e-9)
            sep = np.where(cross[..., None], nj * side_[..., None], sep)
        push = (sep * over[..., None] * 0.5).sum(1)
        # Torque about each centre turns sticks to slide past each other.
        arm = pi - c[:, None, :]
        tq = (arm[..., 0] * sep[..., 1] - arm[..., 1] * sep[..., 0]) * over
        c += push * 0.9
        th += np.clip(tq.sum(1) / np.maximum(h, 0.3) ** 2 * 0.6, -0.15, 0.15)
        # Keep both ends on the layer and under the heap's top.
        dv = np.stack([np.cos(th), np.sin(th)], 1)
        ext = np.abs(dv) * h[:, None] + reff[:, None] * 0.6
        top = pouch.fill_top(c[:, 0]) - 0.15
        c[:, 1] = np.clip(c[:, 1], z_lo + ext[:, 1], np.maximum(z_lo + ext[:, 1], top - ext[:, 1]))
        lim = np.minimum(np.interp(c[:, 1] - ext[:, 1], zt, half), np.interp(c[:, 1] + ext[:, 1], zt, half))
        c[:, 0] = np.clip(c[:, 0], -lim + ext[:, 0], np.maximum(-lim + ext[:, 0], lim - ext[:, 0]))

    # Least tangled first: the 3D packer keeps the first of any overlapping pair.
    dv = np.stack([np.cos(th), np.sin(th)], 1)
    _, _, dist = _pair_closest(c - dv * h[:, None], c + dv * h[:, None])
    over = np.where(eye, 0.0, np.maximum(0.0, reff[:, None] + reff[None, :] - dist)).sum(1)
    _dbg('  relax', it, n, float(over.max()), int((over > 0.01).sum()))
    order = np.argsort(over)
    idx, c, th, reff, h = idx[order], c[order], th[order], reff[order], h[order]

    # Wrap back: each end of a stick goes to its point on the inset surface.
    dv = np.stack([np.cos(th), np.sin(th)], 1)
    ends = np.concatenate([c - dv * h[:, None], c + dv * h[:, None]])
    pts = np.empty((len(ends), 3))
    xis = np.empty(len(ends))
    for i, (s, z) in enumerate(ends):
        a, b, acc = lens(z)
        xis[i] = np.interp(s, acc, xi_g)
        pts[i] = (a * xis[i], side * b * float(pouch.g(xis[i])), z)
    m = len(c)
    e0, e1 = pts[:m], pts[m:]
    mid = 0.5 * (e0 + e1)
    d = _unit(e1 - e0)
    _, nrm, _, _ = pouch.surface_frames(side, 0.5 * (xis[:m] + xis[m:]), mid[:, 2])
    inward = -nrm
    w = _unit(np.cross(inward, d)) * rng.choice([-1.0, 1.0], (m, 1))
    base = mid + inward * (reff - np.mean(reff))[:, None]
    steps = np.arange(20) * 0.03
    centres = base[:, None, :] + inward[:, None, :] * steps[None, :, None]
    return idx, centres, d, w


def _dbg(*a):
    import os
    if os.environ.get('PACK_DEBUG'):
        print('[pack]', *a)


def pack(protos, seed: int = 11):
    """Returns [(proto index, centre, axis dir, bend dir)] for every stick."""
    rng = np.random.default_rng(seed)
    pk = Packer()
    P = np.array(protos)  # L, r, bend
    long_ = np.nonzero(P[:, 0] >= LONG)[0]
    short = np.nonzero(P[:, 0] < LONG)[0]

    def place(pi, centres, d, w):
        L, r, bend = P[pi, 0], P[pi, 1], P[pi, 2]
        reff = _reff(r, bend)
        hl = L / 2 - 0.4 * r
        k = _first_fit(centres, d, hl, reff)
        t = np.linspace(-1, 1, 7)
        stats = [int((k < 0).sum()), 0, 0]
        K = centres.shape[1]
        for i in np.nonzero(k >= 0)[0]:
            h = max(0.01, L[i] / 2 - r[i])
            # From the first push that fits the film, further in until the
            # stick clears the others: it then lies across them, behind.
            for j in range(k[i], K):
                c = centres[i, j]
                a, b = c - d[i] * h, c + d[i] * h
                axis = c + np.outer(t * L[i] / 2, d[i])
                if pouch.core_hits(axis, reff[i] + 0.01, CORE_INSET, CORE_INSET + 0.05).any():
                    stats[1] += 1
                    break
                if pk.free(a, b, reff[i]):
                    pk.add(a, b, reff[i], (int(pi[i]), c.copy(), d[i].copy(), w[i].copy()))
                    break
            else:
                stats[2] += 1
        _dbg('  no fit / core / taken', stats)

    def wall(side, n, depth_range, pool, pushes=12):
        xi = rng.uniform(-0.96, 0.96, n)
        z = rng.uniform(0.35, dims.FILL + 0.5, n)
        p, nrm, tx, tz = pouch.surface_frames(side, xi, z)
        keep = p[:, 2] < pouch.fill_top(p[:, 0]) - 0.12
        p, nrm, tx, tz = p[keep], nrm[keep], tx[keep], tz[keep]
        m = len(p)
        pi = rng.choice(pool, m)
        # Sticks settle in loose local drifts of similar direction.
        x, zz = p[:, 0], p[:, 2]
        field = 1.57 + 1.1 * np.sin(0.5 * x + 0.33 * zz + 1.0 + side) + 0.7 * np.sin(0.8 * zz - 0.4 * x + 2.3)
        phi = np.where(rng.random(m) < 0.7, field + rng.normal(0, 0.3, m), rng.uniform(0, math.pi, m))[:, None]
        d = _unit(np.cos(phi) * tx + np.sin(phi) * tz + nrm * rng.uniform(-0.1, 0.1, (m, 1)))
        w = _unit(np.cross(nrm, d)) * rng.choice([-1.0, 1.0], (m, 1))
        reff = _reff(P[pi, 1], P[pi, 2])
        base = p - nrm * (reff + CLEAR + 0.01 + rng.uniform(*depth_range, m))[:, None]
        steps = np.arange(pushes) * 0.05
        centres = base[:, None, :] - nrm[:, None, :] * steps[None, :, None]
        place(pi, centres, d, w)

    def top(n, pool):
        z0 = dims.FILL - 0.8
        a = float(pouch.a_at(z0))
        x = rng.uniform(-a + 0.4, a - 0.4, n)
        bm = pouch.b_at(z0) * pouch.g(x / a)
        y = rng.uniform(-1, 1, n) * bm * 0.85
        ang = rng.uniform(0, 2 * math.pi, n)
        d = _unit(np.stack([np.cos(ang), np.sin(ang) * 0.6, rng.uniform(-0.3, 0.3, n)], axis=1))
        w = _unit(np.cross(d, [0.0, 0.0, 1.0]))
        pi = rng.choice(pool, n)
        reff = _reff(P[pi, 1], P[pi, 2])
        base = np.stack([x, y, pouch.fill_top(x) - reff - rng.uniform(0.02, 0.3, n)], axis=1)
        steps = np.arange(14) * 0.05
        centres = base[:, None, :] - np.array([0, 0, 1.0])[None, None, :] * steps[None, :, None]
        place(pi, centres, d, w)

    def middle(n, pool):
        z = rng.uniform(0.5, dims.FILL, n)
        a = pouch.a_at(z)
        x = rng.uniform(-1, 1, n) * a
        bm = pouch.b_at(z) * pouch.g(x / a)
        y = rng.uniform(-1, 1, n) * bm
        d = _unit(rng.normal(size=(n, 3)))
        w = _unit(np.cross(d, rng.normal(size=(n, 3))))
        pi = rng.choice(pool, n)
        place(pi, np.stack([x, y, z], axis=1)[:, None, :], d, w)

    def floor(n, pool):
        # Lying on the gusset at the bottom.
        z0 = 0.5
        a = float(pouch.a_at(z0))
        x = rng.uniform(-1, 1, n) * a
        bm = pouch.b_at(z0) * pouch.g(x / a)
        y = rng.uniform(-1, 1, n) * bm
        ang = rng.uniform(0, 2 * math.pi, n)
        d = _unit(np.stack([np.cos(ang), np.sin(ang), rng.uniform(-0.12, 0.12, n)], axis=1))
        w = _unit(np.cross(d, [0.0, 0.0, 1.0]))
        pi = rng.choice(pool, n)
        reff = _reff(P[pi, 1], P[pi, 2])
        base = np.stack([x, y, 0.2 + reff + CLEAR + rng.uniform(0.0, 0.05, n)], axis=1)
        steps = np.arange(8) * 0.05
        centres = base[:, None, :] + np.array([0, 0, 1.0])[None, None, :] * steps[None, :, None]
        place(pi, centres, d, w)

    # Two dense layers against the film, front and back; the second sits a
    # stick's width further in.
    mix = np.concatenate([long_, long_, long_, short])
    for side in (-1, +1):
        pi, centres, d, w = relax_layer(rng, P, mix, 0.68, side, iters=1500, align=0.7)
        place(pi, centres, d, w)
        _dbg('layer1', len(pi), pk.n)
    top(2500, long_)
    _dbg('top', 0, pk.n)
    floor(1500, np.arange(len(P)))
    _dbg('floor', 0, pk.n)
    for side in (-1, +1):
        pi, centres, d, w = relax_layer(rng, P, mix, 0.62, side, deeper=0.5, iters=1500, align=0.7)
        place(pi, centres, d, w)
        _dbg('layer2', len(pi), pk.n)
    # Whole sticks in the gaps of those layers, lying across them behind;
    # broken pieces in what gaps are left, then the middle.
    wall(-1, 4000, (0.0, 0.5), long_, pushes=16)
    wall(+1, 2500, (0.0, 0.5), long_, pushes=16)
    _dbg('wall long', 0, pk.n)
    wall(-1, 5000, (0.0, 0.03), short)
    wall(+1, 3000, (0.0, 0.03), short)
    _dbg('wall', 0, pk.n)
    top(1500, short)
    middle(2500, np.arange(len(P)))
    _dbg('middle', 0, pk.n)
    return pk.items, pk


def crumbs(rng, pk, n=26):
    """Small broken bits at the bottom, in the gaps against the film."""
    out = []
    for _ in range(n * 25):
        if len(out) >= n:
            break
        z = rng.uniform(0.3, 1.6)
        xi = rng.uniform(-0.85, 0.85)
        side = -1 if rng.random() < 0.7 else 1
        p, nrm, tx, tz = (v[0] for v in pouch.surface_frames(side, np.array([xi]), np.array([z])))
        r = rng.uniform(0.05, 0.13)
        c = p - nrm * (1.6 * r + CLEAR + 0.02)
        if pouch.inside(c[None], 1.6 * r + CLEAR)[0] and pk.free(c - 0.001, c + 0.001, 1.6 * r):
            pk.add(c - 0.001, c + 0.001, 1.6 * r, None)
            out.append((c, r, rng.uniform(0, 2 * math.pi)))
    return out


# ----------------------------------------------------------------- materials


def _n(nt, kind, **inputs):
    node = nt.nodes.new(kind)
    for k, v in inputs.items():
        node.inputs[k].default_value = v
    return node


def fried(m, name: str = 'namkeen', dark: float = 1.0):
    """Fried gram-flour: golden to orange-brown, browner patches, black
    pepper and chilli specks, a crumbly surface with a little oil sheen.
    `dark` < 1 gives the shadowed core."""
    from studio.core import rgba

    mat = m.solid(name, '#d8aa5a', roughness=0.55)
    nt = mat.node_tree
    L = nt.links
    p = nt.nodes['Principled BSDF']
    coord = nt.nodes.new('ShaderNodeTexCoord')
    info = nt.nodes.new('ShaderNodeObjectInfo')
    # Offset the texture per stick so instances differ.
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    for i in range(3):
        L.new(info.outputs['Random'], comb.inputs[i])
    rnd = nt.nodes.new('ShaderNodeVectorMath')
    rnd.operation = 'SCALE'
    L.new(comb.outputs[0], rnd.inputs[0])
    rnd.inputs['Scale'].default_value = 97.0
    vec = nt.nodes.new('ShaderNodeVectorMath')
    vec.operation = 'ADD'
    L.new(coord.outputs['Object'], vec.inputs[0])
    L.new(rnd.outputs[0], vec.inputs[1])
    V = vec.outputs[0]

    # Base colour: golden to orange patches (sampled from the photo, a
    # little richer, since the film's sheen lifts and greys them).
    n1 = _n(nt, 'ShaderNodeTexNoise', Scale=2.2, Detail=4.0, Roughness=0.55)
    L.new(V, n1.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.elements[0].position = 0.3
    cr.elements[0].color = rgba('#d8a452')
    cr.elements[1].position = 0.72
    cr.elements[1].color = rgba('#f8da92')
    mid = cr.elements.new(0.52)
    mid.color = rgba('#ecbd68')
    L.new(n1.outputs['Fac'], ramp.inputs['Fac'])
    col = ramp.outputs['Color']

    # Each stick fried a little differently: from pale gold to deep orange-brown.
    tone_r = nt.nodes.new('ShaderNodeValToRGB')
    tr = tone_r.color_ramp
    tr.elements[0].position = 0.0
    tr.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    tr.elements[1].position = 1.0
    tr.elements[1].color = rgba('#e6bc94')
    pale = tr.elements.new(0.18)
    pale.color = rgba('#fff4dc')
    L.new(info.outputs['Random'], tone_r.inputs['Fac'])
    mixd = nt.nodes.new('ShaderNodeMix')
    mixd.data_type = 'RGBA'
    mixd.blend_type = 'MULTIPLY'
    mixd.inputs['Factor'].default_value = 1.0
    L.new(col, mixd.inputs['A'])
    L.new(tone_r.outputs['Color'], mixd.inputs['B'])
    col = mixd.outputs['Result']

    # Browned patches on the crust.
    n2 = _n(nt, 'ShaderNodeTexNoise', Scale=7.0, Detail=6.0, Roughness=0.6)
    L.new(V, n2.inputs['Vector'])
    r2 = nt.nodes.new('ShaderNodeMapRange')
    r2.inputs['From Min'].default_value = 0.5
    r2.inputs['From Max'].default_value = 0.72
    r2.inputs['To Min'].default_value = 0.0
    r2.inputs['To Max'].default_value = 0.5
    L.new(n2.outputs['Fac'], r2.inputs['Value'])
    mb = nt.nodes.new('ShaderNodeMix')
    mb.data_type = 'RGBA'
    mb.blend_type = 'MULTIPLY'
    L.new(r2.outputs['Result'], mb.inputs['Factor'])
    L.new(col, mb.inputs['A'])
    mb.inputs['B'].default_value = rgba('#b88448')
    col = mb.outputs['Result']

    # Masala: a reddish-brown spice dusting, caught in patches.
    n4 = _n(nt, 'ShaderNodeTexNoise', Scale=4.5, Detail=5.0, Roughness=0.65)
    va = nt.nodes.new('ShaderNodeVectorMath')
    va.operation = 'ADD'
    L.new(V, va.inputs[0])
    va.inputs[1].default_value = (13.0, 7.0, 3.0)
    L.new(va.outputs[0], n4.inputs['Vector'])
    r4 = nt.nodes.new('ShaderNodeMapRange')
    r4.inputs['From Min'].default_value = 0.52
    r4.inputs['From Max'].default_value = 0.7
    r4.inputs['To Min'].default_value = 0.0
    r4.inputs['To Max'].default_value = 0.3
    L.new(n4.outputs['Fac'], r4.inputs['Value'])
    mm = nt.nodes.new('ShaderNodeMix')
    mm.data_type = 'RGBA'
    L.new(r4.outputs['Result'], mm.inputs['Factor'])
    L.new(col, mm.inputs['A'])
    mm.inputs['B'].default_value = rgba('#b46a34')
    col = mm.outputs['Result']

    # Pepper and chilli specks.
    def specks(scale, size, density_scale, colour, seed_off, strength):
        vo = _n(nt, 'ShaderNodeTexVoronoi', Scale=scale)
        add = nt.nodes.new('ShaderNodeVectorMath')
        add.operation = 'ADD'
        L.new(V, add.inputs[0])
        add.inputs[1].default_value = (seed_off, seed_off * 0.7, seed_off * 1.3)
        L.new(add.outputs[0], vo.inputs['Vector'])
        dot = nt.nodes.new('ShaderNodeMapRange')
        dot.inputs['From Min'].default_value = size
        dot.inputs['From Max'].default_value = size * 0.6
        L.new(vo.outputs['Distance'], dot.inputs['Value'])
        mask = _n(nt, 'ShaderNodeTexNoise', Scale=density_scale, Detail=2.0)
        L.new(add.outputs[0], mask.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['From Min'].default_value = 0.45
        mr.inputs['From Max'].default_value = 0.6
        L.new(mask.outputs['Fac'], mr.inputs['Value'])
        mul = nt.nodes.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        L.new(dot.outputs['Result'], mul.inputs[0])
        L.new(mr.outputs['Result'], mul.inputs[1])
        mul2 = nt.nodes.new('ShaderNodeMath')
        mul2.operation = 'MULTIPLY'
        L.new(mul.outputs[0], mul2.inputs[0])
        mul2.inputs[1].default_value = strength
        return mul2.outputs[0]

    # (voronoi scale per cm, speck radius in cells, clustering, colour, seed, opacity)
    for scale, size, dens, colour, off, k in (
        (5.0, 0.11, 2.5, '#35241a', 3.0, 0.95),  # black pepper
        (3.5, 0.1, 1.8, '#9a3419', 9.0, 0.75),  # chilli
        (8.0, 0.14, 3.5, '#7a4a22', 21.0, 0.6),  # darker fried bits
    ):
        mx = nt.nodes.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        L.new(specks(scale, size, dens, colour, off, k), mx.inputs['Factor'])
        L.new(col, mx.inputs['A'])
        mx.inputs['B'].default_value = rgba(colour)
        col = mx.outputs['Result']

    core_bump = None
    if dark != 1.0:
        # The hidden core: seen only through gaps, it is painted as more
        # sticks further in, packed tight with dark cracks between them.
        # Elongated Voronoi cells in two directions, patched by a noise.
        def cells(stretch):
            sc = nt.nodes.new('ShaderNodeVectorMath')
            sc.operation = 'MULTIPLY'
            L.new(coord.outputs['Object'], sc.inputs[0])
            sc.inputs[1].default_value = stretch
            vo = _n(nt, 'ShaderNodeTexVoronoi', Scale=3.4, Randomness=0.9)
            vo.feature = 'DISTANCE_TO_EDGE'
            L.new(sc.outputs[0], vo.inputs['Vector'])
            return vo.outputs['Distance']

        pick = _n(nt, 'ShaderNodeTexNoise', Scale=0.6, Detail=1.0)
        L.new(coord.outputs['Object'], pick.inputs['Vector'])
        sel = nt.nodes.new('ShaderNodeMapRange')
        sel.inputs['From Min'].default_value = 0.47
        sel.inputs['From Max'].default_value = 0.53
        L.new(pick.outputs['Fac'], sel.inputs['Value'])
        both = nt.nodes.new('ShaderNodeMix')
        both.data_type = 'FLOAT'
        L.new(sel.outputs['Result'], both.inputs['Factor'])
        L.new(cells((1.0, 0.3, 0.26)), both.inputs['A'])
        L.new(cells((0.26, 0.3, 1.0)), both.inputs['B'])
        crack = nt.nodes.new('ShaderNodeMapRange')
        crack.inputs['From Min'].default_value = 0.0
        crack.inputs['From Max'].default_value = 0.12
        crack.inputs['To Min'].default_value = 0.15
        crack.inputs['To Max'].default_value = 1.0
        L.new(both.outputs['Result'], crack.inputs['Value'])
        core_bump = crack.outputs['Result']
        md = nt.nodes.new('ShaderNodeMix')
        md.data_type = 'RGBA'
        md.blend_type = 'MULTIPLY'
        md.inputs['Factor'].default_value = 1.0
        L.new(col, md.inputs['A'])
        tone = nt.nodes.new('ShaderNodeMath')
        tone.operation = 'MULTIPLY'
        L.new(crack.outputs['Result'], tone.inputs[0])
        tone.inputs[1].default_value = dark
        comb = nt.nodes.new('ShaderNodeCombineXYZ')
        for i in range(3):
            L.new(tone.outputs[0], comb.inputs[i])
        L.new(comb.outputs[0], md.inputs['B'])
        col = md.outputs['Result']
    L.new(col, p.inputs['Base Color'])

    # Crumbly surface: fine noise plus little pits.
    n3 = _n(nt, 'ShaderNodeTexNoise', Scale=16.0, Detail=10.0, Roughness=0.7)
    L.new(V, n3.inputs['Vector'])
    b1 = _n(nt, 'ShaderNodeBump', Strength=0.8, Distance=0.03)
    L.new(n3.outputs['Fac'], b1.inputs['Height'])
    vo = _n(nt, 'ShaderNodeTexVoronoi', Scale=28.0)
    L.new(V, vo.inputs['Vector'])
    b2 = _n(nt, 'ShaderNodeBump', Strength=0.5, Distance=0.015)
    L.new(vo.outputs['Distance'], b2.inputs['Height'])
    L.new(b1.outputs['Normal'], b2.inputs['Normal'])
    normal = b2.outputs['Normal']
    if core_bump is not None:
        b3 = _n(nt, 'ShaderNodeBump', Strength=1.0, Distance=0.15)
        L.new(core_bump, b3.inputs['Height'])
        L.new(normal, b3.inputs['Normal'])
        normal = b3.outputs['Normal']
    L.new(normal, p.inputs['Normal'])

    # A little oil sheen, varying over the surface; a dusting of spice.
    rr = nt.nodes.new('ShaderNodeMapRange')
    rr.inputs['To Min'].default_value = 0.42
    rr.inputs['To Max'].default_value = 0.68
    L.new(n2.outputs['Fac'], rr.inputs['Value'])
    L.new(rr.outputs['Result'], p.inputs['Roughness'])
    p.inputs['Specular IOR Level'].default_value = 0.45
    p.inputs['Sheen Weight'].default_value = 0.25
    p.inputs['Sheen Roughness'].default_value = 0.6
    p.inputs['Sheen Tint'].default_value = rgba('#f0cf8c')
    if dark == 1.0:
        p.inputs['Subsurface Weight'].default_value = 0.12
        p.inputs['Subsurface Radius'].default_value = (1.0, 0.45, 0.2)
        p.inputs['Subsurface Scale'].default_value = 0.08
    return mat


# ----------------------------------------------------------------- build


def build(m, seed: int = 11):
    """Creates the stick instances, crumbs and core; returns the objects."""
    import bpy
    from mathutils import Matrix, Vector

    rng = np.random.default_rng(seed)
    mat = fried(m)
    protos = []
    meshes = []
    for i in range(36):
        # Whole sticks, and broken short pieces.
        L = float(rng.uniform(*dims.STICK_L)) if i < 26 else float(rng.uniform(*dims.STICK_L_SHORT))
        r = float(rng.uniform(*dims.STICK_R))
        bend = float(rng.uniform(0.0, 0.14)) * (L / 3.0)
        protos.append((L, r, bend))
        me = stick_mesh(f'stick-{i}', L, r, bend, seed=i + 1)
        me.materials.append(mat)
        meshes.append(me)

    col = bpy.data.collections.new('namkeen')
    bpy.context.scene.collection.children.link(col)
    objs = []
    items, pk = pack(protos, seed)
    for k, (pi, c, d, w) in enumerate(items):
        x = Vector(d)
        y = Vector(w)
        y = (y - x * x.dot(y)).normalized()
        z = x.cross(y)
        mw = Matrix((x, y, z)).transposed().to_4x4()
        mw.translation = Vector(c)
        ob = bpy.data.objects.new(f'stick.{k:04d}', meshes[pi])
        ob.matrix_world = mw
        col.objects.link(ob)
        objs.append(ob)

    cm = [crumb_mesh(f'crumb-{i}', 1.0, i) for i in range(6)]
    for me in cm:
        me.materials.append(mat)
    for k, (c, r, ang) in enumerate(crumbs(rng, pk)):
        ob = bpy.data.objects.new(f'crumb.{k:03d}', cm[k % len(cm)])
        ob.location = Vector(c)
        ob.scale = (r, r, r)
        ob.rotation_euler = (rng.uniform(0, 6.28), rng.uniform(0, 6.28), ang)
        col.objects.link(ob)
        objs.append(ob)

    objs = cull_through_film(objs)
    core = pouch.build_core(fried(m, 'namkeen-core', dark=0.72), inset_y=CORE_INSET, inset_x=CORE_INSET + 0.05)
    objs.append(core)
    return objs


def film_clearance(pts):
    """Clearance of points (N x 3) inside the built film (the meshes, with
    their waviness), measured across y: negative means through the film."""
    import bpy

    out = np.full(len(pts), np.inf)
    grids = []
    for name, flip in (('pouch-front', False), ('pouch-back', True)):
        ob = bpy.data.objects.get(name)
        if ob is None:
            return out
        G = pouch.sheet_grid(ob)
        grids.append(G[:, ::-1] if flip else G)
    zs = grids[0][:, 0, 2]
    k = np.clip(np.searchsorted(zs, pts[:, 2]) - 1, 0, len(zs) - 2)
    t = np.clip((pts[:, 2] - zs[k]) / (zs[k + 1] - zs[k]), 0.0, 1.0)
    for row in np.unique(k):
        sel = k == row
        x = pts[sel, 0]
        yf = np.interp(x, grids[0][row, :, 0], grids[0][row, :, 1]) * (1 - t[sel]) + np.interp(x, grids[0][row + 1, :, 0], grids[0][row + 1, :, 1]) * t[sel]
        yb = np.interp(x, grids[1][row, :, 0], grids[1][row, :, 1]) * (1 - t[sel]) + np.interp(x, grids[1][row + 1, :, 0], grids[1][row + 1, :, 1]) * t[sel]
        out[sel] = np.minimum(pts[sel, 1] - yf, yb - pts[sel, 1])
    return out


def cull_through_film(objs, clearance: float = 0.03):
    """Removes the odd stick or crumb that the film's waviness brings within
    `clearance` of the film (the packing works on the smooth shape)."""
    import bpy

    bpy.context.view_layer.update()
    keep = []
    for ob in objs:
        me = ob.data
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get('co', co)
        M = np.array(ob.matrix_world)
        w = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
        if film_clearance(w).min() < clearance:
            bpy.data.objects.remove(ob)
        else:
            keep.append(ob)
    _dbg('culled near the film', len(objs) - len(keep))
    return keep
