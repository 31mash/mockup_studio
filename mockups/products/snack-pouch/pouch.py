"""The stand-up pouch: shape maths (pure numpy, also used to pack the namkeen)
and the Blender meshes for the film, the zip tracks, the gusset base and a
hidden core that keeps gaps between the sticks from showing daylight.

Shape model. Seen from above, every horizontal slice of the filled pouch is a
lens: the front and back film bulge out as y = +-b * g(x / a) between the two
side seals, which carry on as flat fins. The film does not stretch, so for a
slice of half-depth b the lens half-width a is solved so that the curve's arc
length equals the flat panel width between the seals. The artwork's u then
follows arc length across the film and v follows arc length down each
column, so the print is never stretched: the seals pull in where the pouch
bulges, as on a real filled pouch.
"""

from __future__ import annotations

import math

import numpy as np

import dims

LENS_P = 0.72  # lens profile exponent: g(t) = (1 - t^2)^p
L_HALF = dims.W / 2 - dims.SEAL  # half the film width between the seals


def g(t):
    t = np.clip(np.abs(t), 0.0, 1.0)
    return (1.0 - t * t) ** LENS_P


def _pchip(xs, ys):
    """Monotone cubic interpolation (Fritsch-Carlson) through (xs, ys)."""
    xs = np.asarray(xs, float)
    ys = np.asarray(ys, float)
    h = np.diff(xs)
    d = np.diff(ys) / h
    m = np.zeros_like(ys)
    m[0], m[-1] = d[0], d[-1]
    for k in range(1, len(xs) - 1):
        if d[k - 1] * d[k] > 0:
            w1 = 2 * h[k] + h[k - 1]
            w2 = h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])

    def f(x):
        x = np.clip(np.asarray(x, float), xs[0], xs[-1])
        k = np.clip(np.searchsorted(xs, x) - 1, 0, len(xs) - 2)
        t = (x - xs[k]) / h[k]
        h00 = (1 + 2 * t) * (1 - t) ** 2
        h10 = t * (1 - t) ** 2
        h01 = t * t * (3 - 2 * t)
        h11 = t * t * (t - 1)
        return h00 * ys[k] + h10 * h[k] * m[k] + h01 * ys[k + 1] + h11 * h[k] * m[k + 1]

    return f


_depth = _pchip([p[0] for p in dims.DEPTH], [p[1] for p in dims.DEPTH])


def depth(z):
    """Half-depth b of the lens at height z, with the rounded bottom edge where
    the panels turn under into the gusset."""
    z = np.asarray(z, float)
    b = _depth(z)
    R = dims.BOTTOM_R
    zz = np.clip(z, 0.0, R)
    turn = R - np.sqrt(np.maximum(0.0, R * R - (R - zz) ** 2))
    return np.maximum(dims.FILM, b - turn)


_T = np.linspace(0.0, 1.0, 600)


def _half_arc(a, b):
    x = a * _T
    y = b * g(_T)
    return float(np.sum(np.hypot(np.diff(x), np.diff(y))))


def half_width(b: float) -> float:
    """Lens half-width a for half-depth b, keeping the film's length."""
    lo, hi = 0.3 * L_HALF, L_HALF
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if _half_arc(mid, b) > L_HALF:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


# Tables over height for fast lookups.
ZT = np.linspace(0.0, dims.Z_TOP, 900)
BT = depth(ZT)
AT = np.array([half_width(b) for b in BT])


def a_at(z):
    return np.interp(z, ZT, AT)


def b_at(z):
    return np.interp(z, ZT, BT)


def fill_top(x):
    """Height of the namkeen's top surface across the width: a little higher
    on the left, as in the photo, and gently lumpy."""
    x = np.asarray(x, float)
    return dims.FILL + 0.28 * np.sin(1.25 * x + 0.6) + 0.18 * np.sin(2.7 * x + 2.1) - 0.09 * x


def inside(p, margin):
    """True where points p (N x 3) sit inside the film by at least `margin`
    (per point or scalar) and below the fill surface."""
    p = np.atleast_2d(p)
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    a = a_at(z)
    b = b_at(z)
    ax = np.abs(x) + margin * 1.15
    ok = ax < a
    lim = b * g(ax / a) - margin
    ok &= np.abs(y) < lim
    ok &= z - margin > 0.22
    ok &= z + margin * 0.6 < fill_top(x)
    return ok


def surface(side: int, xi, z):
    """Film point on the lens at parameter xi in [-1, 1] (x = a * xi), height z.
    side = -1 front, +1 back."""
    a = a_at(z)
    b = b_at(z)
    return np.stack([a * xi, side * b * g(xi), np.broadcast_to(z, np.shape(xi))], axis=-1)


def surface_frame(side: int, xi: float, z: float):
    """Point, outward normal and the two tangents (across, up) on the film."""
    e = 1e-3
    p = surface(side, xi, z)
    tx = surface(side, min(xi + e, 0.999), z) - surface(side, max(xi - e, -0.999), z)
    tz = surface(side, xi, z + e) - surface(side, xi, max(z - e, 0.0))
    tx /= np.linalg.norm(tx)
    tz /= np.linalg.norm(tz)
    n = np.cross(tx, tz)
    n /= np.linalg.norm(n)
    if n[1] * side < 0:
        n = -n
    return p, n, tx, tz


# ----------------------------------------------------------------- the film


def _rows():
    R = dims.BOTTOM_R
    zs = [R * (1 - math.cos(math.radians(90 * i / 7))) for i in range(7)]
    z = R
    while z < dims.Z_TOP - 1e-6:
        zs.append(z)
        z += 0.13
    zs.append(dims.Z_TOP)
    return np.array(zs)


def _columns():
    # Denser near the lens tips, where the film turns sharply into the fins.
    n_fin, n_lens = 5, 96
    fin = np.linspace(0.0, dims.SEAL, n_fin + 1)
    t = np.linspace(-1.0, 1.0, n_lens + 1)
    lens = dims.SEAL + L_HALF * (1 + np.sin(t * math.pi / 2) * 0.35 + t * 0.65)
    return np.concatenate([fin[:-1], lens, dims.W - fin[::-1][1:]])


def _row_points(side: int, z: float, us):
    """3D points of one horizontal row of a panel at film coordinates us (cm
    from the panel's left edge as seen from outside)."""
    a = float(a_at(z))
    b = float(b_at(z))
    t = np.linspace(-1.0, 1.0, 801)
    x = a * t
    y = side * b * g(t)
    acc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
    acc *= (2 * L_HALF) / acc[-1]
    # Front: u runs left to right (-x to +x). Back, seen from behind: +x to -x.
    xs = np.empty_like(us)
    ys = np.empty_like(us)
    for k, u in enumerate(us):
        if u <= dims.SEAL:
            xs[k], ys[k] = -(a + dims.SEAL - u), side * dims.FILM
        elif u >= dims.W - dims.SEAL:
            xs[k], ys[k] = a + (u - (dims.W - dims.SEAL)), side * dims.FILM
        else:
            s = u - dims.SEAL
            xs[k] = np.interp(s, acc, x)
            ys[k] = np.interp(s, acc, y) + side * dims.FILM
    if side > 0:
        xs = -xs
    return np.stack([xs, ys, np.full_like(xs, z)], axis=-1)


def panel_grid(side: int, seed: float = 0.0):
    """Vertex grid (rows x cols x 3) and UVs (rows x cols x 2) of one panel,
    with gentle waviness: sealed parts move together, open film bows out."""
    from mathutils import Vector, noise

    zs = _rows()
    us = _columns()
    P = np.stack([_row_points(side, z, us) for z in zs])
    rows, cols = P.shape[:2]

    # Film waviness. Common: both layers move together (the seals, the flat
    # top). Outward: open film bows out a little, never into the contents.
    Q = P.copy()
    for r in range(rows):
        z = zs[r]
        upper = np.clip((z - (dims.FILL - 0.4)) / 1.2, 0.0, 1.0)
        low = np.clip((z - 0.25) / 0.6, 0.0, 1.0)
        for c in range(cols):
            u = us[c]
            in_fin = u <= dims.SEAL or u >= dims.W - dims.SEAL
            edge = min(u, dims.W - u)
            tip = np.clip((edge - dims.SEAL) / 0.8, 0.0, 1.0)  # 0 at the seal, 1 inside
            n1 = noise.noise(Vector((u * 0.55, z * 0.42, 3.1)))
            n2 = noise.noise(Vector((u * 1.7, z * 1.3, 7.7)))
            common = (0.07 * n1 + 0.02 * n2) * (1.0 if in_fin else max(upper, 1 - tip)) * low
            n3 = noise.noise(Vector((u * 0.8, z * 0.6, 11.3 + seed)))
            n4 = noise.noise(Vector((u * 2.3, z * 2.0, 17.9 + seed)))
            open_amp = (0.022 + 0.035 * upper) * tip * (0 if in_fin else 1)
            out = open_amp * (0.55 + 0.45 * n3 + 0.25 * n4)
            out = max(out, 0.0)
            # Keep the open top from pinching through the other layer.
            if z > dims.Z_TOP - dims.TOP_SEAL:
                out = 0.0
            Q[r, c, 1] += common + side * out * low
    P = Q

    # UVs: u across the flat film, v by arc length down each column.
    U = np.broadcast_to(us / dims.W, (rows, cols))
    seg = np.linalg.norm(np.diff(P, axis=0), axis=-1)  # (rows-1) x cols
    from_top = np.concatenate([np.cumsum(seg[::-1], axis=0)[::-1], np.zeros((1, cols))])
    V = 1.0 - from_top / dims.H
    return P, np.stack([U, V], axis=-1)


def grid_object(name, P, UV, mats, faces_mat=None, flip=False, smooth=True):
    import bpy

    rows, cols = P.shape[:2]
    verts = P.reshape(-1, 3)
    idx = np.arange(rows * cols).reshape(rows, cols)
    a = idx[:-1, :-1].ravel()
    b = idx[:-1, 1:].ravel()
    c = idx[1:, 1:].ravel()
    d = idx[1:, :-1].ravel()
    quads = np.stack([a, b, c, d], axis=1)
    if flip:
        quads = quads[:, ::-1]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], quads.tolist())
    uv = me.uv_layers.new(name='UVMap')
    uvf = UV.reshape(-1, 2)
    loop_uv = uvf[quads.ravel()]
    uv.data.foreach_set('uv', loop_uv.ravel())
    if faces_mat is not None:
        me.polygons.foreach_set('material_index', faces_mat)
    me.polygons.foreach_set('use_smooth', [smooth] * len(me.polygons))
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in mats:
        me.materials.append(m)
    return ob


def build_film(front_mat, back_mat, base_mat):
    Pf, UVf = panel_grid(-1, seed=0.0)
    Pb, UVb = panel_grid(+1, seed=5.0)
    front = grid_object('pouch-front', Pf, UVf, [front_mat])
    back = grid_object('pouch-back', Pb, UVb, [back_mat], flip=True)

    # Gusset base: joins the two bottom rows, its middle fold pushed up a
    # little so the pouch stands on the rim of the oval.
    f0 = Pf[0]
    b0 = Pb[0][::-1]
    mid = 0.5 * (f0 + b0)
    xi = np.clip(np.abs(mid[:, 0]) / (np.abs(mid[:, 0]).max() + 1e-6), 0, 1)
    mid[:, 2] = 0.28 * (1 - xi ** 2)
    q1 = 0.5 * (f0 + mid)
    q1[:, 2] = 0.12 * (1 - xi ** 2)
    q2 = 0.5 * (b0 + mid)
    q2[:, 2] = 0.12 * (1 - xi ** 2)
    G = np.stack([f0, q1, mid, q2, b0])
    UVg = np.zeros(G.shape[:2] + (2,))
    base = grid_object('pouch-base', G, UVg, [base_mat], flip=True)
    return front, back, base


def build_zip(mat):
    """Two zip tracks on the inside of each panel: thin milky ridges."""
    import bpy

    from mathutils import Vector  # noqa: F401

    objs = []
    zc = dims.Z_TOP - dims.ZIP
    us = np.linspace(0.12, dims.W - 0.12, 140)
    for side in (-1, 1):
        for dz in (-dims.ZIP_GAP / 2, dims.ZIP_GAP / 2):
            z = zc + dz
            path = _row_points(side, z, us)
            # Inside the film, towards the middle.
            path[:, 1] -= side * 0.035
            ring = 8
            ry, rz = 0.028, 0.075
            verts = []
            for k, p in enumerate(path):
                edge = min(us[k], dims.W - us[k])
                squash = np.clip((edge - 0.1) / 0.6, 0.25, 1.0)  # crushed flat in the seals
                for j in range(ring):
                    t = 2 * math.pi * j / ring
                    verts.append((p[0], p[1] - side * (ry * squash * (1 + math.cos(t))), p[2] + rz * math.sin(t)))
            faces = []
            n = len(path)
            for k in range(n - 1):
                for j in range(ring):
                    j2 = (j + 1) % ring
                    faces.append((k * ring + j, k * ring + j2, (k + 1) * ring + j2, (k + 1) * ring + j))
            faces.append(tuple(range(ring))[::-1])
            faces.append(tuple((n - 1) * ring + j for j in range(ring)))
            me = bpy.data.meshes.new('zip')
            me.from_pydata(verts, [], faces)
            me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
            me.update()
            ob = bpy.data.objects.new(f'zip-{side}-{dz:+.2f}', me)
            bpy.context.collection.objects.link(ob)
            me.materials.append(mat)
            objs.append(ob)
    return objs


def build_core(mat, inset_y=0.62, inset_x=0.75):
    """A closed lens-shaped body inside the sticks, following the pouch but
    smaller, with a bumpy top under the fill surface. Seen only through the
    gaps between sticks, where it reads as more namkeen further in."""
    import bpy

    from mathutils import Vector, noise

    zs = np.linspace(0.45, dims.FILL - 0.25, 44)
    t = np.linspace(-1, 1, 49)[1:-1]
    rings = []
    for z in zs:
        a = float(a_at(z)) - inset_x
        b = max(0.12, float(b_at(z)) - inset_y)
        front = [(a * s, -b * float(g(s)) ** 0.9) for s in t]
        back = [(a * s, b * float(g(s)) ** 0.9) for s in t[::-1]]
        pts = [(-a, 0.0)] + front + [(a, 0.0)] + back
        ring = []
        for x, y in pts:
            top = float(fill_top(x)) - 0.55
            zz = min(z, top + 0.15 * noise.noise(Vector((x * 1.3, y * 1.3, 2.0))))
            ring.append((x, y, zz))
        rings.append(ring)
    n = len(rings[0])
    verts = [v for r in rings for v in r]
    faces = []
    for k in range(len(rings) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((k * n + j, k * n + j2, (k + 1) * n + j2, (k + 1) * n + j))
    faces.append(tuple(range(n))[::-1])
    faces.append(tuple((len(rings) - 1) * n + j for j in range(n)))
    me = bpy.data.meshes.new('core')
    me.from_pydata(verts, [], faces)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.update()
    ob = bpy.data.objects.new('namkeen-core', me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(mat)
    return ob
