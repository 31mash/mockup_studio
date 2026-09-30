"""Outlines and artwork layout maths, in cm. Pure Python: usable from artwork
scripts without Blender."""

from __future__ import annotations

import math



def rounded_rect(w: float, d: float, r: float, seg: int = 10) -> list[tuple[float, float]]:
    """Closed CCW outline of a w x d rectangle with corner radius r, starting at
    the left end of the front (-Y) edge."""
    r = max(0.0, min(r, w / 2 - 1e-4, d / 2 - 1e-4))
    hw, hd = w / 2, d / 2
    pts: list[tuple[float, float]] = []
    corners = [  # (centre, start angle) for the arcs after each straight edge
        ((hw - r, -hd + r), -90),  # front-right
        ((hw - r, hd - r), 0),  # back-right
        ((-hw + r, hd - r), 90),  # back-left
        ((-hw + r, -hd + r), 180),  # front-left
    ]
    for (cx, cy), a0 in corners:
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    # Rotate so the outline starts at the front edge's left end: the last
    # point of the front-left arc.
    start = pts[-1]
    pts = [start] + pts[:-1]
    return pts


def circle(r: float, seg: int = 96) -> list[tuple[float, float]]:
    """Closed CCW circle starting at the front (-Y) centre."""
    return [(r * math.cos(math.radians(-90 + 360 * i / seg)), r * math.sin(math.radians(-90 + 360 * i / seg))) for i in range(seg)]


def inset(profile, amount: float):
    """Offsets a convex CCW outline inward along its averaged vertex normals."""
    n = len(profile)
    out = []

    def unit(x, y):
        L = math.hypot(x, y)
        return (x / L, y / L) if L > 1e-12 else (0.0, 0.0)

    for i, (x, y) in enumerate(profile):
        px, py = profile[i - 1]
        nx_, ny_ = profile[(i + 1) % n]
        # Edge normals, pointing outward for a CCW outline.
        n1 = unit(y - py, -(x - px))
        n2 = unit(ny_ - y, -(nx_ - x))
        nv = unit(n1[0] + n2[0], n1[1] + n2[1])
        if nv == (0.0, 0.0):
            nv = n1
        # Keep the offset distance true at corners.
        cosang = max(0.3, nv[0] * n1[0] + nv[1] * n1[1]) if n1 != (0.0, 0.0) else 1.0
        out.append((x - nv[0] * amount / cosang, y - nv[1] * amount / cosang))
    return out


def perimeter(profile) -> list[float]:
    """Cumulative arc length at each vertex, closing back to the start."""
    acc = [0.0]
    for i in range(1, len(profile) + 1):
        a = profile[i - 1]
        b = profile[i % len(profile)]
        acc.append(acc[-1] + math.dist(a, b))
    return acc


def wrap_layout(w: float, d: float, r: float) -> dict:
    """Where each face of a rounded-rect wall lands in its wrap strip, as
    fractions of the strip width: {'front': (u0, u1), 'right': ..., 'back': ..., 'left': ...}.
    Corners fill the gaps between faces. Also returns 'length' in cm."""
    fw, fd = w - 2 * r, d - 2 * r
    arc = math.pi * r / 2
    total = 2 * fw + 2 * fd + 4 * arc
    u = 0.0
    out = {}
    for name, span in (('front', fw), ('right', fd), ('back', fw), ('left', fd)):
        out[name] = (u / total, (u + span) / total)
        u += span + arc
    out['length'] = total
    return out


