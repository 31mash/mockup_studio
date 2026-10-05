"""IndiGo Tiffin sandwich wedge, in cm. Pure Python (no Blender), shared by the
artwork script and the model.

A classic sandwich wedge: a right-triangle prism lying along X. It stands on
its rectangular base; the back panel is vertical; the front (window) panel is
the slanted hypotenuse, facing front and up. The triangle ends face -X / +X.

Sizes from the spread: the back panel is 0.56 as wide as it is tall, the
triangle ends are isosceles, and a wedge is made for a ~12 cm bread slice.
"""

import math

W = 7.0  # width along X (the back panel's width)
L = 12.5  # both legs of the triangle: base depth (Y) and back height (Z)
HYP = L * math.sqrt(2)  # sharp front panel length, 17.68
T = 0.045  # paperboard thickness
R = 0.14  # outer radius of the three long folds (base / back / front)
R_END = 0.1  # outer radius of the folds onto the triangle ends
CREASE_SEG = 8
END_SEG = 5

# Corner geometry of the rounded triangle: exterior turn angle, tangent
# length (from the sharp vertex to where the fold starts) and arc length.
TURN = {'back_bottom': math.pi / 2, 'apex': 3 * math.pi / 4, 'front_bottom': 3 * math.pi / 4}
TAN = {k: R * math.tan(a / 2) for k, a in TURN.items()}
ARC = {k: R * a for k, a in TURN.items()}

# Panel lengths along the printed surface, between fold midlines. The artwork
# for each panel is drawn at exactly this length.
FRONT_LEN = HYP - TAN['apex'] - TAN['front_bottom'] + (ARC['apex'] + ARC['front_bottom']) / 2
BACK_LEN = L - TAN['back_bottom'] - TAN['apex'] + (ARC['back_bottom'] + ARC['apex']) / 2
BASE_LEN = L - TAN['front_bottom'] - TAN['back_bottom'] + (ARC['front_bottom'] + ARC['back_bottom']) / 2
PERIMETER = FRONT_LEN + BACK_LEN + BASE_LEN

# Front panel design, in art coordinates: p along the panel (0 at the apex
# fold, FRONT_LEN at the front-bottom fold), x across it (0 = left, the -X end).
# Measured on the original: the slope edge of the Soul-itude end (seen flat
# on) shows the blue band over the top 27 % of the panel and the bottom band
# over the last 27 %; the front photo, rectified, puts the window 1.0 cm in
# from either side, cutting about 0.9 cm into the blue band and 0.5 cm into
# the bottom band.
BLUE_BAND = 4.7  # IndiGo band from the apex fold
ORANGE_BAND = 4.75  # Tiffin band at the bottom
WIN_X = (1.0, 6.0)  # window aperture across the panel
WIN_P = (BLUE_BAND - 0.88, FRONT_LEN - ORANGE_BAND + 0.48)  # it cuts into both bands
WIN_R = 0.16  # die-cut corner radius of the window
WIN_FRAME = 0.3  # margin of the mesh cell that holds the window
CELL_P = (WIN_P[0] - WIN_FRAME, WIN_P[1] + WIN_FRAME)
CELL_X = (WIN_X[0] - WIN_FRAME, WIN_X[1] + WIN_FRAME)

# Where each panel starts in the wrap strip (arc length from the seam, which
# sits in the middle of the base). The strip runs: half base -> back (upwards)
# -> front (downwards, apex to bottom) -> other half of the base.
U_BACK = L / 2 - TAN['back_bottom'] + ARC['back_bottom'] / 2  # back panel: bottom fold midline
U_APEX = U_BACK + BACK_LEN
U_FRONT_BOTTOM = U_APEX + FRONT_LEN


def _arc(v, d_in, d_out, key, seg):
    """Points of the rounded fold at sharp vertex v (travel d_in then d_out)."""
    t, a = TAN[key], TURN[key]
    p1 = (v[0] - d_in[0] * t, v[1] - d_in[1] * t)
    n = (-d_in[1], d_in[0])  # CCW outline: the centre is on the left
    c = (p1[0] + n[0] * R, p1[1] + n[1] * R)
    a0 = math.atan2(p1[1] - c[1], p1[0] - c[0])
    return [(c[0] + R * math.cos(a0 + a * i / seg), c[1] + R * math.sin(a0 + a * i / seg)) for i in range(seg + 1)]


def profile():
    """The cross-section (y, z) as [(y, z, u)], CCW seen from +X, where u is
    the arc length from the seam at the middle of the base. The front panel
    has extra vertices where the window's mesh cell starts and ends."""
    s2 = 1 / math.sqrt(2)
    F, B, A = (-L / 2, 0.0), (L / 2, 0.0), (L / 2, L)
    east, north, down = (1.0, 0.0), (0.0, 1.0), (-s2, -s2)
    # Straight run to the back-bottom fold, the fold, the back, the apex fold.
    pts = []
    pts += _arc(B, east, north, 'back_bottom', CREASE_SEG)
    pts += _arc(A, north, down, 'apex', CREASE_SEG)
    apex_end = pts[-1]
    # Window cell edges on the flat front, measured from the apex fold midline.
    for p_art in CELL_P:
        d = p_art - ARC['apex'] / 2  # distance from the apex tangent point
        pts.append((apex_end[0] + down[0] * d, apex_end[1] + down[1] * d))
    pts += _arc(F, down, east, 'front_bottom', CREASE_SEG)
    u = 0.0
    prev = (0.0, 0.0)
    out = [(0.0, 0.0, 0.0)]
    for p in pts:
        u += math.dist(prev, p)
        out.append((p[0], p[1], u))
        prev = p
    return out


def front_point(p, depth=0.0):
    """(y, z) of art coordinate p on the front panel's flat part, `depth` cm
    in from the outer surface."""
    s2 = 1 / math.sqrt(2)
    A = (L / 2, L)
    # Apex tangent point on the front side, then down the slope.
    ty = A[0] - s2 * TAN['apex']
    tz = A[1] - s2 * TAN['apex']
    d = p - ARC['apex'] / 2
    return (ty - s2 * d + s2 * depth, tz - s2 * d - s2 * depth)


FRONT_NORMAL = (0.0, -1 / math.sqrt(2), 1 / math.sqrt(2))  # outward, (x, y, z)
