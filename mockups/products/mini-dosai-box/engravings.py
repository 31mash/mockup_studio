"""Engraving-style line art for the Mini Dosai sleeves, as SVG snippets.

Both drawings are built from a few hand-placed outlines plus generated
hatching (parallel strokes clipped to a shadow shape) and feather/leaf
detail, so the line weight stays even like a steel engraving.

hen(x, y, s): a white hen standing, facing right (the chicken sleeve).
potato_plant(x, y, s): a potato plant with its tubers (the veg sleeve).
(x, y) is the drawing's top-left; s scales its 300-unit design box.
"""

from __future__ import annotations

import math
import random

INK = '#221d1a'


def _f(v: float) -> str:
    return f'{v:.1f}'


def _pts(points) -> str:
    return ' '.join(f'{_f(x)},{_f(y)}' for x, y in points)


def _catmull(points, closed: bool = False, tension: float = 0.5) -> str:
    """A smooth SVG path through the points (Catmull-Rom as cubic Beziers)."""
    p = list(points)
    n = len(p)
    if closed:
        ext = [p[-1]] + p + [p[0], p[1]]
    else:
        ext = [p[0]] + p + [p[-1]]
    d = f'M{_f(p[0][0])},{_f(p[0][1])}'
    segs = n if closed else n - 1
    k = tension / 3 * 2
    for i in range(segs):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        d += f' C{_f(c1[0])},{_f(c1[1])} {_f(c2[0])},{_f(c2[1])} {_f(p2[0])},{_f(p2[1])}'
    if closed:
        d += ' Z'
    return d


def _hatch(clip_id: str, angle: float, spacing: float, box, width: float, color: str = INK, wobble: float = 0.0, seed: int = 1) -> str:
    """Parallel strokes across `box` (x0, y0, x1, y1), clipped to clip_id."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = math.hypot(x1 - x0, y1 - y0) / 2 + spacing
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    out = []
    k = -r
    while k <= r:
        ox, oy = cx + nx * k, cy + ny * k
        if wobble:
            mid = (ox + nx * rnd.uniform(-wobble, wobble), oy + ny * rnd.uniform(-wobble, wobble))
            out.append(f'M{_f(ox - dx * r)},{_f(oy - dy * r)} Q{_f(mid[0])},{_f(mid[1])} {_f(ox + dx * r)},{_f(oy + dy * r)}')
        else:
            out.append(f'M{_f(ox - dx * r)},{_f(oy - dy * r)} L{_f(ox + dx * r)},{_f(oy + dy * r)}')
        k += spacing
    return f'<path d="{" ".join(out)}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" clip-path="url(#{clip_id})"/>'


# ----------------------------------------------------------------- the hen

# Silhouette in a 300 x 300 design box: nape, back, the raised tail fan,
# the belly, the full breast and the small head (comb, beak and wattle are
# drawn over it).
HEN_BODY = (
    'M214,60 C208,78 204,96 192,108 C178,120 156,124 134,118 C114,112 98,96 86,78 '
    'C76,62 64,48 50,44 C40,42 33,49 36,58 C29,62 25,72 28,82 C21,90 21,102 26,110 '
    'C21,120 25,132 34,138 C40,158 56,180 78,198 C104,220 136,236 170,238 '
    'C204,240 234,222 250,196 C264,172 268,138 260,116 C256,104 250,96 246,90 '
    'C250,82 252,74 250,68 C250,56 240,46 228,46 C218,46 212,52 214,60 Z'
)
HEN_COMB = (
    'M216,51 C213,43 217,38 222,40 C221,32 228,29 232,35 C233,27 241,26 242,34 '
    'C246,29 253,33 249,41 C253,44 251,50 247,53 C238,49 226,49 216,51 Z'
)
HEN_BEAK = 'M249,59 C256,59 262,62 268,66 C262,68 256,70 250,72'
HEN_WATTLE = 'M247,73 C253,75 257,83 255,91 C253,99 246,99 244,93 C242,87 243,79 247,73 Z'
HEN_WING = 'M210,132 C196,122 152,120 122,132 C108,138 106,152 118,158 C148,174 194,178 214,162 C224,152 222,138 210,132 Z'
# Underside shadow: follows the belly and under-tail, feathered upper edge.
HEN_SHADOW = (
    'M26,110 C22,122 26,132 34,138 C40,158 56,180 78,198 C104,220 136,236 170,238 '
    'C204,240 234,222 250,196 L244,196 C236,206 228,210 222,206 C214,214 206,212 202,208 '
    'C194,216 184,214 180,210 C170,216 160,214 156,208 C146,212 136,208 134,202 '
    'C124,204 116,198 114,192 C104,192 98,186 98,180 C88,178 82,170 84,164 '
    'C74,160 70,152 72,146 C62,142 58,134 62,128 C52,124 48,118 52,112 '
    'C44,110 38,104 40,98 C34,100 28,104 26,110 Z'
)
HEN_CORE = (
    'M34,138 C40,158 56,180 78,198 C104,220 136,236 170,238 C196,239 218,230 234,216 '
    'C214,224 194,226 172,224 C140,220 112,206 92,188 C72,170 54,154 42,132 Z'
)


def _scallops(points, w, depth, ink, width=1.0, clip=None):
    """A row of small U-shaped feather marks centred on the given points."""
    d = ' '.join(f'M{_f(x - w / 2)},{_f(y)} Q{_f(x)},{_f(y + depth)} {_f(x + w / 2)},{_f(y)}' for x, y in points)
    c = f' clip-path="url(#{clip})"' if clip else ''
    return f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{width}" stroke-linecap="round"{c}/>'


def hen(x: float, y: float, s: float, ink: str = INK, paper: str = '#fbfaf4') -> str:
    out = [f'<g transform="translate({_f(x)},{_f(y)}) scale({s:.4f})">']
    out.append(
        '<defs>'
        f'<clipPath id="hen-body"><path d="{HEN_BODY}"/></clipPath>'
        f'<clipPath id="hen-shadow"><path d="{HEN_SHADOW}"/></clipPath>'
        f'<clipPath id="hen-wing"><path d="{HEN_WING}"/></clipPath>'
        '</defs>'
    )
    # Ground: a few short engraved strokes under the feet.
    out.append(f'<path d="M132,286 L226,286 M146,291 L210,291 M160,296 L192,296" stroke="{ink}" stroke-width="1.0" stroke-linecap="round"/>')
    # Legs and feet (behind the body).
    legs = 'M161,232 L158,272 M184,232 L186,270'
    out.append(f'<path d="{legs}" fill="none" stroke="{ink}" stroke-width="5" stroke-linecap="round"/>')
    toes = (
        'M158,272 L180,277 M158,272 L171,282 M158,272 L146,277 '
        'M186,270 L208,274 M186,270 L199,280 M186,270 L175,274'
    )
    out.append(f'<path d="{toes}" fill="none" stroke="{ink}" stroke-width="2.8" stroke-linecap="round"/>')
    scales = 'M156,248 l6,1 M156,256 l6,1 M156,264 l6,1 M183,246 l6,1 M183,254 l6,1 M184,262 l6,1'
    out.append(f'<path d="{scales}" stroke="{paper}" stroke-width="0.9"/>')
    # The white bird.
    out.append(f'<path d="{HEN_BODY}" fill="{paper}"/>')
    # Underside: hatching fading up into the feathered edge, solid core at the bottom.
    out.append(_hatch('hen-shadow', 62, 2.6, (20, 96, 256, 242), 1.2, ink, wobble=0.6, seed=3))
    out.append(f'<path d="{HEN_CORE}" fill="{ink}"/>')
    # Contour lines across the lower body, broken like engraved feather texture.
    contours = [
        'M44,118 C54,150 76,176 104,194 C132,210 170,218 206,212 C224,208 238,198 248,186',
        'M56,104 C66,134 86,160 112,176 C140,192 176,198 210,192 C230,188 246,176 254,164',
        'M70,96 C82,120 100,142 124,156 C150,170 184,176 216,170 C236,166 252,154 258,142',
    ]
    for i, c in enumerate(contours):
        out.append(f'<path d="{c}" fill="none" stroke="{ink}" stroke-width="{1.0 - i * 0.12:.2f}" stroke-dasharray="{5 - i},{3 + i * 2}" clip-path="url(#hen-body)"/>')
    # Tail: feather partings from the rump to the notches, and fine shafts.
    tail = (
        'M112,110 C92,92 66,70 36,58 M110,116 C88,104 58,88 28,82 '
        'M108,122 C86,116 56,112 26,110 M106,128 C86,128 60,132 34,138'
    )
    out.append(f'<path d="{tail}" fill="none" stroke="{ink}" stroke-width="1.35" stroke-linecap="round"/>')
    shafts = (
        'M100,98 C80,80 62,62 44,52 M98,108 C76,96 54,82 32,70 '
        'M96,116 C74,110 52,102 27,96 M96,124 C74,124 52,126 30,124'
    )
    out.append(f'<path d="{shafts}" fill="none" stroke="{ink}" stroke-width="0.7" stroke-dasharray="7,4" stroke-linecap="round"/>')
    # Neck hackles: pointed feather tips over the shoulder, and long strands.
    hackle = 'M196,108 L201,118 L205,109 L210,120 L214,110 L219,121 L224,111 L229,121 L234,111 L239,120 L244,110'
    out.append(f'<path d="{hackle}" fill="none" stroke="{ink}" stroke-width="1.1" stroke-linejoin="round" clip-path="url(#hen-body)"/>')
    strands = 'M216,66 C212,82 206,96 200,106 M224,70 C220,86 214,100 210,112 M232,74 C230,88 226,102 222,112 M240,84 C240,94 238,104 236,112'
    out.append(f'<path d="{strands}" fill="none" stroke="{ink}" stroke-width="0.8" stroke-linecap="round"/>')
    # Breast feathers.
    rows = [
        [(250, 128), (240, 132), (254, 142), (244, 146), (232, 140)],
        [(256, 156), (246, 160), (236, 156), (250, 172), (240, 176), (228, 170)],
        [(90, 150), (80, 136), (100, 166), (68, 124)],
    ]
    for r in rows:
        out.append(_scallops(r, 8, 5, ink, 1.0, clip='hen-body'))
    # Wing: outline, two rows of coverts, long primaries to the tip.
    out.append(f'<path d="{HEN_WING}" fill="{paper}" stroke="{ink}" stroke-width="1.6"/>')
    cov1 = [(204 - i * 11, 140 + i * 0.4) for i in range(6)]
    cov2 = [(208 - i * 11, 152 + i * 0.2) for i in range(5)]
    out.append(_scallops(cov1, 11, 6, ink, 1.0, clip='hen-wing'))
    out.append(_scallops(cov2, 11, 6, ink, 1.0, clip='hen-wing'))
    prim = 'M150,160 C136,158 124,154 116,150 M158,166 C142,164 128,160 118,156 M150,150 C138,146 126,142 116,142'
    out.append(f'<path d="{prim}" fill="none" stroke="{ink}" stroke-width="1.0" stroke-linecap="round"/>')
    out.append(_hatch('hen-wing', 14, 3.0, (104, 160, 222, 182), 0.8, ink, seed=7))
    # Outline, heavier along the bottom.
    out.append(f'<path d="{HEN_BODY}" fill="none" stroke="{ink}" stroke-width="2.2" stroke-linejoin="round"/>')
    # Head: comb, face, beak, eye, lobe, wattle.
    out.append(f'<path d="{HEN_COMB}" fill="{ink}"/>')
    out.append(f'<path d="{HEN_BEAK}" fill="{paper}" stroke="{ink}" stroke-width="1.6" stroke-linejoin="round"/>')
    out.append(f'<path d="M250,65.5 L262,65.8" stroke="{ink}" stroke-width="0.9"/>')
    out.append(f'<path d="{HEN_WATTLE}" fill="{ink}"/>')
    out.append(f'<path d="M228,64 C232,62 236,64 236,70 C236,76 230,78 228,74 C226,70 226,66 228,64 Z" fill="{ink}"/>')
    out.append(f'<circle cx="239" cy="57" r="2.5" fill="{ink}"/>')
    out.append(f'<path d="M234,53 Q239,50 244,54" fill="none" stroke="{ink}" stroke-width="0.9"/>')
    out.append('</g>')
    return ''.join(out)


# ----------------------------------------------------------------- potato plant


def _leaf(cx, cy, length, width, angle, ink, shade_side=1, seed=0):
    """An ovate leaflet with a midrib, a few side veins and hatching on one
    half, attached at (cx, cy) and pointing along `angle` (degrees)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux

    def P(t, w):
        return (cx + ux * t + nx * w, cy + uy * t + ny * w)

    # Outline: base, widest at 40 %, pointed tip; slight asymmetry.
    left = [P(length * t, width * f) for t, f in ((0.0, 0.0), (0.12, 0.34), (0.3, 0.5), (0.5, 0.47), (0.72, 0.32), (0.9, 0.12))]
    tip = P(length, 0)
    right = [P(length * t, -width * f) for t, f in ((0.9, 0.1), (0.72, 0.3), (0.5, 0.46), (0.3, 0.5), (0.12, 0.32))]
    outline = left + [tip] + right
    d = _catmull(outline, closed=True, tension=0.55)
    rid = f'leaf{seed}'
    parts = [f'<clipPath id="{rid}"><path d="{d}"/></clipPath>']
    parts.append(f'<path d="{d}" fill="#fbfaf4" stroke="{ink}" stroke-width="1.35" stroke-linejoin="round"/>')
    # Midrib.
    parts.append(f'<path d="M{_f(cx)},{_f(cy)} Q{_f(P(length * 0.5, width * 0.04)[0])},{_f(P(length * 0.5, width * 0.04)[1])} {_f(P(length * 0.93, 0)[0])},{_f(P(length * 0.93, 0)[1])}" fill="none" stroke="{ink}" stroke-width="1.0"/>')
    veins = []
    for t in (0.22, 0.4, 0.58, 0.74):
        for sgn in (1, -1):
            a0 = P(length * t, 0)
            a1 = P(length * (t + 0.16), sgn * width * 0.36)
            veins.append(f'M{_f(a0[0])},{_f(a0[1])} L{_f(a1[0])},{_f(a1[1])}')
    parts.append(f'<path d="{" ".join(veins)}" fill="none" stroke="{ink}" stroke-width="0.7" stroke-linecap="round"/>')
    # Hatching on the shaded half.
    hat = []
    for i in range(1, 12):
        t = i / 12
        a0 = P(length * t, 0)
        a1 = P(length * (t + 0.05), shade_side * width * 0.55)
        hat.append(f'M{_f(a0[0])},{_f(a0[1])} L{_f(a1[0])},{_f(a1[1])}')
    parts.append(f'<path d="{" ".join(hat)}" fill="none" stroke="{ink}" stroke-width="0.55" stroke-linecap="round" clip-path="url(#{rid})"/>')
    return ''.join(parts)


def _tuber(cx, cy, rx, ry, angle, ink, seed):
    """A potato: a lumpy ellipse, hatched on its lower side, with eyes."""
    rnd = random.Random(seed)
    pts = []
    a = math.radians(angle)
    n = 14
    for i in range(n):
        t = 2 * math.pi * i / n
        k = 1 + rnd.uniform(-0.06, 0.06)
        x, y = rx * math.cos(t) * k, ry * math.sin(t) * k
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    d = _catmull(pts, closed=True)
    rid = f'tuber{seed}'
    out = [f'<clipPath id="{rid}"><path d="{d}"/></clipPath>']
    out.append(f'<path d="{d}" fill="#fbfaf4" stroke="{ink}" stroke-width="1.5"/>')
    # Contour hatching: arcs following the tuber's form, denser at the bottom.
    arcs = []
    for i in range(1, 9):
        f = i / 9
        oy = -ry + 2 * ry * f
        w = rx * math.sqrt(max(0.0, 1 - (oy / ry) ** 2)) * 1.05
        if f < 0.45:
            continue
        p0 = (-w, oy)
        p1 = (0, oy + ry * 0.18)
        p2 = (w, oy)
        R = [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in (p0, p1, p2)]
        arcs.append(f'M{_f(R[0][0])},{_f(R[0][1])} Q{_f(R[1][0])},{_f(R[1][1])} {_f(R[2][0])},{_f(R[2][1])}')
    out.append(f'<path d="{" ".join(arcs)}" fill="none" stroke="{ink}" stroke-width="0.75" clip-path="url(#{rid})"/>')
    out.append(_hatch(rid, angle + 60, 2.6, (cx - rx - 4, cy, cx + rx + 4, cy + ry + 4), 0.6, ink, seed=seed))
    # Eyes.
    for _ in range(3):
        t = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.35, 0.7)
        x, y = rx * rr * math.cos(t), ry * rr * math.sin(t)
        ex, ey = cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)
        out.append(f'<path d="M{_f(ex - 2.4)},{_f(ey)} Q{_f(ex)},{_f(ey + 1.8)} {_f(ex + 2.4)},{_f(ey)}" fill="none" stroke="{ink}" stroke-width="0.9"/>')
    return ''.join(out)


def potato_plant(x: float, y: float, s: float, ink: str = INK) -> str:
    """Design box 250 x 490: stem from the tubers at the bottom to a terminal
    leaflet at the top, with pairs of leaflets along it."""
    out = [f'<g transform="translate({_f(x)},{_f(y)}) scale({s:.4f})">']
    stem = [(118, 360), (122, 300), (120, 240), (124, 180), (122, 120), (126, 60), (128, 22)]
    # Roots and stolons under the stem.
    roots = [
        [(118, 360), (104, 382), (92, 396)],
        [(120, 360), (134, 384), (156, 398)],
        [(119, 362), (116, 392), (110, 420), (112, 446)],
        [(121, 364), (140, 396), (150, 430)],
        [(117, 364), (96, 402), (84, 430)],
    ]
    for r in roots:
        out.append(f'<path d="{_catmull(r)}" fill="none" stroke="{ink}" stroke-width="1.05" stroke-linecap="round"/>')
    fine = []
    rnd = random.Random(5)
    for _ in range(14):
        bx, by = 118 + rnd.uniform(-14, 22), 372 + rnd.uniform(0, 60)
        ang = rnd.uniform(40, 140)
        ln = rnd.uniform(8, 18)
        fine.append(f'M{_f(bx)},{_f(by)} l{_f(math.cos(math.radians(ang)) * ln)},{_f(math.sin(math.radians(ang)) * ln)}')
    out.append(f'<path d="{" ".join(fine)}" fill="none" stroke="{ink}" stroke-width="0.6" stroke-linecap="round"/>')
    # Tubers: two large, two small.
    out.append(_tuber(78, 432, 34, 24, -58, ink, 21))
    out.append(_tuber(166, 436, 38, 22, 34, ink, 22))
    out.append(_tuber(104, 404, 15, 11, 20, ink, 23))
    out.append(_tuber(140, 410, 13, 10, -25, ink, 24))
    # Stem, drawn as a double line.
    out.append(f'<path d="{_catmull(stem)}" fill="none" stroke="{ink}" stroke-width="3.2" stroke-linecap="round"/>')
    out.append(f'<path d="{_catmull(stem)}" fill="none" stroke="#fbfaf4" stroke-width="1.2" stroke-linecap="round"/>')
    # Leaflets: (attach t along stem as y, side, length, width, angle).
    leaves = [
        (330, -1, 44, 26, 200), (322, 1, 40, 24, -16),
        (272, -1, 56, 32, 196), (262, 1, 54, 30, -20),
        (206, -1, 58, 34, 206), (196, 1, 60, 34, -28),
        (142, -1, 54, 30, 222), (132, 1, 56, 32, -40),
        (84, -1, 50, 28, 238), (76, 1, 52, 28, -56),
        (24, 0, 56, 30, -84),
    ]
    k = 0
    for ly, side, ln, wd, ang in leaves:
        # Stem x at that height.
        sx = 122 + (4 if ly < 200 else 0)
        # A short petiole to the leaflet.
        a = math.radians(ang)
        px, py = sx + math.cos(a) * 8, ly + math.sin(a) * 8
        out.append(f'<path d="M{_f(sx)},{_f(ly)} L{_f(px)},{_f(py)}" stroke="{ink}" stroke-width="1.4" stroke-linecap="round"/>')
        out.append(_leaf(px, py, ln, wd, ang, ink, shade_side=-1 if side >= 0 else 1, seed=100 + k))
        k += 1
    out.append('</g>')
    return ''.join(out)
