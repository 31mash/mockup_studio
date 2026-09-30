"""A printed sheet of card as a closed solid: printed front, plain back and a
thin white cut edge, built from a front-surface function so the same code
makes a bowed, standing poster and a poster lying on the floor.

UVs: the front is the artwork seen from the front, upright (u to the right,
v up the sheet); the back is mirrored so it reads correctly from behind; the
edges map along their length.
"""

from __future__ import annotations

import math

from mathutils import Matrix, Vector


def standing_surface(w: float, h: float, bow: float = 0.0, lean_deg: float = 0.0):
    """Front surface of a sheet standing on its bottom edge, facing -Y.

    The bottom edge is a circular arc of length w whose middle bulges towards
    the viewer by `bow` (so the card keeps its true width), and the sheet rises
    along a line tipped back by `lean_deg`: a developable cylinder, like real
    card. Returns f(u, v) -> Vector for u, v in [0, 1]."""
    g = Vector((0.0, math.sin(math.radians(lean_deg)), math.cos(math.radians(lean_deg))))
    if bow > 1e-6:
        # Radius from arc length w and sagitta bow: R (1 - cos(w / 2R)) = bow.
        lo, hi = w / (2 * math.pi) + 1e-6, 1e6
        for _ in range(100):
            mid = math.sqrt(lo * hi)
            if mid * (1 - math.cos(w / (2 * mid))) > bow:
                lo = mid
            else:
                hi = mid
        R = hi
        half = w / (2 * R)

        def base(u):
            a = (u - 0.5) * 2 * half
            return Vector((R * math.sin(a), R * (1 - math.cos(a)) - bow, 0.0))
    else:

        def base(u):
            return Vector(((u - 0.5) * w, 0.0, 0.0))

    def f(u, v):
        return base(u) + g * (v * h)

    return f


def lying_surface(w: float, h: float, cx: float, cy: float, rot_deg: float, height=None):
    """Underside of a sheet lying face up on the floor, its top edge towards
    +Y before rotating by rot_deg about Z around (cx, cy).
    height(u, v, x, y) -> z lifts it (a residual curl, or where it rests on
    another sheet)."""
    a = math.radians(rot_deg)
    ca, sa = math.cos(a), math.sin(a)

    def f(u, v):
        lx, ly = (u - 0.5) * w, (v - 0.5) * h
        x, y = cx + lx * ca - ly * sa, cy + lx * sa + ly * ca
        return Vector((x, y, height(u, v, x, y) if height else 0.0))

    return f


def to_local(x: float, y: float, cx: float, cy: float, rot_deg: float, w: float, h: float):
    """(u, v) of a floor point on a lying sheet (outside 0..1 when off it)."""
    a = math.radians(-rot_deg)
    dx, dy = x - cx, y - cy
    lx, ly = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
    return lx / w + 0.5, ly / h + 0.5


def build(ctx, name: str, surface, thickness: float, mats, nu: int = 64, nv: int = 24, lying: bool = False):
    """The sheet as one mesh. mats = (front, back, edge). For a lying sheet
    the surface is its underside on the floor and the print is on top."""
    from studio.shapes import MeshBuilder

    front_m, back_m, edge_m = mats
    mb = MeshBuilder(name)
    bm, uvl = mb.bm, mb.uv

    us = [i / nu for i in range(nu + 1)]
    vs = [j / nv for j in range(nv + 1)]

    def normal(u, v):
        e = 1e-4
        du = surface(min(1, u + e), v) - surface(max(0, u - e), v)
        dv = surface(u, min(1, v + e)) - surface(u, max(0, v - e))
        n = du.cross(dv)
        return n.normalized()

    # The print side is the surface itself; the back is offset through the
    # card. A lying sheet rests on its back, so its print side is lifted.
    P = [[surface(u, v) for v in vs] for u in us]
    N = [[normal(u, v) for v in vs] for u in us]
    if lying:
        F = [[P[i][j] + N[i][j] * thickness for j in range(nv + 1)] for i in range(nu + 1)]
        B = P
    else:
        F = P
        B = [[P[i][j] - N[i][j] * thickness for j in range(nv + 1)] for i in range(nu + 1)]

    fv = [[bm.verts.new(F[i][j]) for j in range(nv + 1)] for i in range(nu + 1)]
    bv = [[bm.verts.new(B[i][j]) for j in range(nv + 1)] for i in range(nu + 1)]

    def quad(verts, uvs, mat):
        f = bm.faces.new(verts)
        f.material_index = mat
        f.smooth = True
        for loop, uv in zip(f.loops, uvs):
            loop[uvl].uv = uv
        return f

    for i in range(nu):
        for j in range(nv):
            u0, u1, v0, v1 = us[i], us[i + 1], vs[j], vs[j + 1]
            quad([fv[i][j], fv[i + 1][j], fv[i + 1][j + 1], fv[i][j + 1]], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], 0)
            quad([bv[i][j], bv[i][j + 1], bv[i + 1][j + 1], bv[i + 1][j]], [(1 - u0, v0), (1 - u0, v1), (1 - u1, v1), (1 - u1, v0)], 1)

    # Cut edges: bottom, top (along u) and the two sides (along v).
    for i in range(nu):
        u0, u1 = us[i], us[i + 1]
        quad([fv[i][0], bv[i][0], bv[i + 1][0], fv[i + 1][0]], [(u0, 0), (u0, 1), (u1, 1), (u1, 0)], 2)
        quad([fv[i][nv], fv[i + 1][nv], bv[i + 1][nv], bv[i][nv]], [(u0, 0), (u1, 0), (u1, 1), (u0, 1)], 2)
    for j in range(nv):
        v0, v1 = vs[j], vs[j + 1]
        quad([fv[0][j], fv[0][j + 1], bv[0][j + 1], bv[0][j]], [(v0, 0), (v1, 0), (v1, 1), (v0, 1)], 2)
        quad([fv[nu][j], bv[nu][j], bv[nu][j + 1], fv[nu][j + 1]], [(v0, 0), (v0, 1), (v1, 1), (v1, 0)], 2)

    ob = mb.finish([front_m, back_m, edge_m], auto_smooth=30)
    # Rest exactly on the floor.
    zmin = min(v.co.z for v in ob.data.vertices)
    ob.data.transform(Matrix.Translation((0.0, 0.0, -zmin)))
    return ob
