"""The newspaper bag (lifafa) lying on its back: shape maths in numpy, meshes in bmesh.

Paper coordinates: s across the bag (0 = left edge seen from the front, W =
right), t up the bag (0 = the bottom fold, L = the top fold). The front panel
is a height field over them, draped over the samosa inside: a tent of
straight-ruled facets running from the samosa down to the folded edges,
meeting in soft creases (towards the corners especially), with a gentle rumple
and two faint old creases from handling. Paper does not
stretch, so every row and column is laid out by arc length: where the panel
rises, its edges pull in, and the bag's sides and ends bow inward slightly, as
on a real filled paper bag. The artwork's (u, v) is (s / W, t / L), so the
print is never stretched.

The back panel shares the folded edges, which ride a little off the floor,
and flattens onto the floor under the belly. The top is folded over once
towards the front: the flap is its own sheet (with real paper thickness) that
wraps round the top edge on a small radius and lies on the front panel,
springing up a touch towards its free edge.
"""

from __future__ import annotations

import math

import numpy as np

import dims

W, L, F = dims.W, dims.L, dims.F


def _smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _waves(seed, n, amp, scale):
    """Smooth 2D noise: a sum of plane waves in random directions (cm)."""
    rnd = np.random.default_rng(seed)
    ang = rnd.uniform(0, 2 * np.pi, n)
    k = 2 * np.pi / (scale * rnd.uniform(0.6, 1.4, n))
    ph = rnd.uniform(0, 2 * np.pi, n)
    a = amp * rnd.uniform(0.5, 1.0, n) / math.sqrt(n / 2)

    def f(x, y):
        out = np.zeros_like(x)
        for i in range(n):
            out += a[i] * np.sin(k[i] * (np.cos(ang[i]) * x + np.sin(ang[i]) * y) + ph[i])
        return out

    return f


def _value_noise(seed, cell, amp, octaves=3):
    """Smooth lattice noise (cm): random heights on a square lattice of
    `cell` cm, blended with smoothstep weights, over a few octaves. Unlike a
    sum of waves it has no regular interference pattern."""
    rnd = np.random.default_rng(seed)
    grids = [rnd.uniform(-1, 1, (64, 64)) for _ in range(octaves)]

    def f(x, y):
        out = np.zeros_like(np.asarray(x, float))
        for o, g in enumerate(grids):
            c = cell / 2 ** o
            gx, gy = np.asarray(x) / c + 7.3 * o, np.asarray(y) / c + 3.1 * o
            ix, iy = np.floor(gx).astype(int), np.floor(gy).astype(int)
            fx, fy = gx - ix, gy - iy
            fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
            ix, iy = ix % 63, iy % 63
            v = (g[iy, ix] * (1 - fx) * (1 - fy) + g[iy, ix + 1] * fx * (1 - fy)
                 + g[iy + 1, ix] * (1 - fx) * fy + g[iy + 1, ix + 1] * fx * fy)
            out = out + v * amp / 2 ** (o * 1.2)
        return out

    return f


_rumple = _value_noise(3, 3.4, 0.055)
_edge_wave = _waves(21, 6, 0.06, 5.0)


def edge_z(S, T):
    """Height of the folded edges off the floor (varies gently)."""
    return dims.EDGE_Z * (1.0 + _edge_wave(S, T) / 0.06 * 0.25)


# The samosa inside, as the paper feels it: lying on a face, its top is a
# rounded ridge (the upturned edge) with the tip lower down to one side.
# (s, t, height) in cm of paper; the ridge is sampled densely.
SUPPORT = [((4.3, 4.6), (8.4, 7.4), 1.0, 0.93), ((8.4, 7.4), (6.6, 10.4), 0.93, 0.62)]


def _support():
    pts = []
    for (a, b, ha, hb) in SUPPORT:
        for k in np.linspace(0.0, 1.0, 24):
            pts.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, ha + (hb - ha) * k))
    return np.array(pts)


def _tent(S, T):
    """Paper draped over the support and pulled flat to the bag's edges: the
    upper envelope of cones from each support point down to the edges. Every
    cone is ruled (straight from the samosa to the edge), so the panel is made
    of developable pieces meeting in soft creases, as paper does."""
    z = np.zeros_like(S)
    for qs, qt, h in _support():
        ds, dt = S - qs, T - qt
        with np.errstate(divide='ignore', invalid='ignore'):
            ts = np.where(ds > 0, (W - qs) / ds, np.where(ds < 0, -qs / ds, np.inf))
            tt = np.where(dt > 0, (L - qt) / dt, np.where(dt < 0, -qt / dt, np.inf))
        tau = np.minimum(ts, tt)  # the ray from q through p leaves the bag at q + tau (p - q)
        lam = np.where(np.isfinite(tau), 1.0 / np.maximum(tau, 1e-9), 0.0)
        z = np.maximum(z, h * np.clip(1.0 - lam, 0.0, 1.0))
    return z


def _blur(Z, s, t, sigma):
    """Gaussian blur on the paper grid, odd-reflected at the edges so the
    folded edges stay at zero."""
    out = Z
    for axis, coords in ((1, s), (0, t)):
        step = float(np.mean(np.diff(coords)))
        r = max(1, int(3 * sigma / step))
        k = np.exp(-0.5 * (np.arange(-r, r + 1) * step / sigma) ** 2)
        k /= k.sum()
        pad = [(0, 0), (0, 0)]
        pad[axis] = (r, r)
        P = np.pad(out, pad, mode='reflect', reflect_type='odd')
        out = np.apply_along_axis(lambda v: np.convolve(v, k, mode='valid'), axis, P)
    return out


def front_height(S, T, s=None, t=None):
    """Front panel height z over paper coordinates (2D grids, cm)."""
    tent = dims.PUFF * _tent(S, T)
    if s is not None:
        tent = _blur(tent, s, t, 0.32)
    z = tent.copy()
    mask = _smooth(0.0, 0.9, np.minimum(S, W - S)) * _smooth(0.0, 0.8, T) * _smooth(0.0, 0.5, L - T)
    # Two old creases from handling: shallow, sharp-sided ridges.
    for (s0, t0, ang, amp) in ((2.0, 13.8, -21.0, 0.018), (11.2, 2.6, 61.0, -0.014)):
        a = math.radians(ang)
        dist = -(S - s0) * math.sin(a) + (T - t0) * math.cos(a)
        z += amp * np.exp(-np.abs(dist) / 0.09) * mask
    # Loose rumples in the paper, fading out at the folded edges.
    z += _rumple(S, T) * mask
    z = np.maximum(z, 0.8 * tent)
    # Edge height: the panel meets the back panel along the folds.
    return edge_z(S, T) + z


def back_height(S, T):
    """Back panel: rises from the floor under the belly to the folded edges."""
    b = dims.BELLY * W / 2
    c = _smooth(0.0, b, np.minimum(S, W - S)) * _smooth(0.0, b, T) * _smooth(0.0, b * 1.4, L - T)
    return edge_z(S, T) * (1 - c)


def samples():
    """Paper-coordinate samples; the flap's free edge is one of the rows."""
    s = np.linspace(0.0, W, 136)
    t = np.unique(np.round(np.concatenate([
        np.linspace(0.0, L - F, 170),
        np.linspace(L - F, L, 16),
        np.linspace(0.0, 0.5, 8),  # finer at the bottom fold
    ]), 6))
    return s, t


def layout(Z, s, t):
    """Positions (x, y) for a height field sampled on the paper grid, laid
    out by arc length along rows and columns, centred on the origin."""
    ds = np.diff(s)[None, :]
    dz = np.diff(Z, axis=1)
    dx = np.sqrt(np.maximum(ds * ds - dz * dz, (0.3 * ds) ** 2))
    X = np.concatenate([np.zeros((Z.shape[0], 1)), np.cumsum(dx, axis=1)], axis=1)
    X -= X[:, -1:] / 2
    dt = np.diff(t)[:, None]
    dzt = np.diff(Z, axis=0)
    dy = np.sqrt(np.maximum(dt * dt - dzt * dzt, (0.3 * dt) ** 2))
    Y = np.concatenate([np.zeros((1, Z.shape[1])), np.cumsum(dy, axis=0)], axis=0)
    Y -= Y[-1:, :] / 2
    return X, Y


def shape():
    s, t = samples()
    S, T = np.meshgrid(s, t)
    Zf = front_height(S, T, s, t)
    Zb = back_height(S, T)
    X, Y = layout(Zf, s, t)
    return dict(s=s, t=t, X=X, Y=Y, Zf=Zf, Zb=Zb)


# ----------------------------------------------------------------- meshes


def body(sh, front_mat, back_mat):
    """Front and back panels as one closed shell joined along the folds."""
    import bmesh
    import bpy

    s, t, X, Y, Zf, Zb = sh['s'], sh['t'], sh['X'], sh['Y'], sh['Zf'], sh['Zb']
    nt, ns = X.shape
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    top = [[bm.verts.new((X[i, j], Y[i, j], Zf[i, j])) for j in range(ns)] for i in range(nt)]
    bot = [[None] * ns for _ in range(nt)]
    for i in range(nt):
        for j in range(ns):
            if i in (0, nt - 1) or j in (0, ns - 1):
                bot[i][j] = top[i][j]
            else:
                bot[i][j] = bm.verts.new((X[i, j], Y[i, j], Zb[i, j]))
    for i in range(nt - 1):
        for j in range(ns - 1):
            q = [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]
            f = bm.faces.new([top[a][b] for a, b in q])
            f.material_index = 0
            f.smooth = True
            for loop, (a, b) in zip(f.loops, q):
                loop[uv].uv = (s[b] / W, t[a] / L)
            q2 = q[::-1]
            f = bm.faces.new([bot[a][b] for a, b in q2])
            f.material_index = 1
            f.smooth = True
            for loop, (a, b) in zip(f.loops, q2):
                loop[uv].uv = (1 - s[b] / W, t[a] / L)
    # The folded edges are crisp creases.
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.link_faces[0].material_index != e.link_faces[1].material_index:
            e.smooth = False
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('bag-body')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('bag-body', me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(front_mat)
    me.materials.append(back_mat)
    return ob


def flap(sh, mat):
    """The folded-over top: wraps round the top edge on radius FOLD_R and lies
    on the front panel down to its free edge, lifting a little towards it."""
    import bmesh
    import bpy

    s, t, X, Y, Zf = sh['s'], sh['t'], sh['X'], sh['Y'], sh['Zf']
    ns = len(s)
    rows = np.nonzero(t >= L - F - 1e-6)[0][::-1]  # from the fold down to the free edge
    R = dims.FOLD_R
    gap0 = 0.03
    total = F + dims.FOLD_ARC
    lift = _waves(33, 5, 1.0, 4.0)

    pts, vs = [], []
    # The fold: from under the top edge, round the outside, up onto the flap.
    arc = dims.FOLD_ARC / R
    iT = rows[0]
    for k in range(10, -1, -1):
        a = math.pi / 2 - arc * k / 10
        row = []
        for j in range(ns):
            cy, cz = Y[iT, j], Zf[iT, j] + gap0 - R
            row.append((X[iT, j], cy + R * math.cos(a), cz + R * math.sin(a)))
        pts.append(row)
        vs.append((F + R * arc * k / 10) / total)
    # The flat part, following the panel.
    for n, i in enumerate(rows):
        f = L - t[i]
        spring = 0.12 * (f / F) ** 2.2
        row = []
        for j in range(ns):
            w = max(0.3, 1.0 + 0.35 * float(lift(np.array(s[j]), np.array(0.0))))
            row.append((X[i, j], Y[i, j], Zf[i, j] + gap0 + spring * float(w)))
        if n == 0:
            continue  # same as the arc's last row
        pts.append(row)
        vs.append((F - f) / total)
    pts = np.array(pts)

    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    grid = [[bm.verts.new(tuple(p)) for p in row] for row in pts]
    for r in range(len(grid) - 1):
        for j in range(ns - 1):
            q = [(r, j), (r + 1, j), (r + 1, j + 1), (r, j + 1)]
            fc = bm.faces.new([grid[a][b] for a, b in q])
            fc.smooth = True
            for loop, (a, b) in zip(fc.loops, q):
                loop[uv].uv = (s[b] / W, vs[a])
    me = bpy.data.meshes.new('bag-flap')
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('bag-flap', me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(mat)
    # Make sure the flat part faces up.
    me.update()
    up = sum(p.normal.z for p in me.polygons)
    if up < 0:
        me.flip_normals()
    sol = ob.modifiers.new('paper', 'SOLIDIFY')
    sol.thickness = dims.PAPER * 1.6
    sol.offset = -1.0
    sol.use_even_offset = True
    return ob
