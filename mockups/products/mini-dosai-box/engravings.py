"""Engraving-style line art for the Mini Dosai sleeves, as SVG snippets.

Both drawings are hand-placed outlines plus generated detail (hatching
clipped to a shadow shape, rows of feather marks, leaf veins), so the line
weight stays even like a steel engraving.

hen(x, y, s): a white hen standing, facing right (the chicken sleeve), in a
300 x 300 design box.
potato_plant(x, y, s): a potato plant with its tubers (the veg sleeve), in a
250 x 490 design box.
(x, y) is the drawing's top-left; s scales the design box.
"""

from __future__ import annotations

import itertools
import math
import random

INK = '#221d1a'
PAPER = '#fbfaf4'
_ids = itertools.count(1)


def _f(v: float) -> str:
    return f'{v:.1f}'


def _catmull(points, closed: bool = False, tension: float = 0.5) -> str:
    """A smooth SVG path through the points (Catmull-Rom as cubic Beziers)."""
    p = list(points)
    n = len(p)
    ext = ([p[-1]] + p + [p[0], p[1]]) if closed else ([p[0]] + p + [p[-1]])
    d = f'M{_f(p[0][0])},{_f(p[0][1])}'
    k = tension / 3
    for i in range(n if closed else n - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        d += f' C{_f(c1[0])},{_f(c1[1])} {_f(c2[0])},{_f(c2[1])} {_f(p2[0])},{_f(p2[1])}'
    return d + (' Z' if closed else '')


def _bezier(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def _hatch(clip_id: str, angle: float, spacing: float, box, width: float, color: str = INK, wobble: float = 0.0, seed: int = 1) -> str:
    """Parallel strokes filling `box` (x0, y0, x1, y1), clipped to the box and
    to clip_id."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = math.hypot(x1 - x0, y1 - y0) / 2 + spacing
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    lines = []
    k = -r
    while k <= r:
        ox, oy = cx + nx * k, cy + ny * k
        w = rnd.uniform(-wobble, wobble) if wobble else 0.0
        lines.append(
            f'M{_f(ox - dx * r)},{_f(oy - dy * r)} Q{_f(ox + nx * w)},{_f(oy + ny * w)} {_f(ox + dx * r)},{_f(oy + dy * r)}'
        )
        k += spacing
    bid = f'hb{next(_ids)}'
    return (
        f'<clipPath id="{bid}"><rect x="{_f(x0)}" y="{_f(y0)}" width="{_f(x1 - x0)}" height="{_f(y1 - y0)}"/></clipPath>'
        f'<g clip-path="url(#{bid})"><path d="{" ".join(lines)}" fill="none" stroke="{color}" stroke-width="{width}" '
        f'stroke-linecap="round" clip-path="url(#{clip_id})"/></g>'
    )


def _scallops(points, w, depth, ink, width=1.0, clip=None) -> str:
    """Small U-shaped feather marks centred on the given points."""
    d = ' '.join(f'M{_f(x - w / 2)},{_f(y)} Q{_f(x)},{_f(y + depth)} {_f(x + w / 2)},{_f(y)}' for x, y in points)
    c = f' clip-path="url(#{clip})"' if clip else ''
    return f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{width}" stroke-linecap="round"{c}/>'


# ----------------------------------------------------------------- the hen

# Silhouette, traced from the sleeve's engraving (design box about 285 x 280,
# y down): nape, the back dipping to the tail base, the raised fan of tail
# feathers (tips and notches), the under-tail and the round belly, the full
# breast, throat, beak base and crown. Drawn as one smooth closed curve.
HEN_OUTLINE = [
    (228, 34), (216, 52), (200, 67), (178, 77), (153, 81), (129, 77), (109, 67),
    (92, 55), (76, 41), (60, 28), (45, 18),
    (34, 12), (30, 13), (24, 21), (18, 20), (14, 25), (15, 32), (8, 36), (6, 44), (11, 49), (5, 56), (5, 64), (12, 68), (8, 76), (12, 84), (18, 88),
    (18, 100), (25, 120), (39, 141), (57, 163), (81, 187), (109, 206), (139, 220), (169, 227),
    (198, 224), (226, 214), (250, 196), (266, 174), (276, 150), (279, 124), (274, 100),
    (267, 82), (262, 68), (264, 58), (268, 50), (266, 38), (258, 30), (244, 26), (232, 28),
]
HEN_COMB = (
    'M231,31 C227,21 232,13 239,17 C238,7 249,4 252,13 C255,5 265,7 264,16 '
    'C271,14 275,23 268,29 C259,26 244,26 231,31 Z'
)
HEN_BEAK = 'M266,39 C272,40 278,42 284,46 C278,48 272,50 266,52'
HEN_WATTLE = 'M261,55 C267,57 270,64 269,71 C267,78 259,77 258,71 C256,65 257,58 261,55 Z'


def _outline_points(pts, per=6):
    """Dense points along the closed Catmull-Rom curve through pts."""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                for j in (0, 1)
            ))
    return out


def _band(curve, depth, jag, seed):
    """A filled band inside a stretch of the outline: its outer edge is the
    curve, its inner edge a feathered, jagged line `depth(t)` inside (the
    curve runs clockwise, so inside is to the right)."""
    rnd = random.Random(seed)
    inner = []
    n = len(curve)
    for i, (x, y) in enumerate(curve):
        a = curve[max(0, i - 1)]
        b = curve[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1
        nx, ny = ty / ln, -tx / ln  # inside: the outline runs anticlockwise on the page (y down)
        d = depth(i / (n - 1))
        if d <= 0:
            inner.append((x, y))
            continue
        k = d * (1.0 if i % 2 == 0 else 1 - jag) * rnd.uniform(0.85, 1.15)
        inner.append((x + nx * k, y + ny * k))
    pts = curve + list(reversed(inner))
    return 'M' + ' L'.join(f'{_f(x)},{_f(y)}' for x, y in pts) + ' Z'


def hen(x: float, y: float, s: float, ink: str = INK, paper: str = PAPER) -> str:
    """A white hen standing, facing right, in the manner of a steel
    engraving: clean outline, a solid black underside feathering up into
    hatching, light feather marks on the white body."""
    body = _catmull(HEN_OUTLINE, closed=True)
    dense = _outline_points(HEN_OUTLINE, 6)
    out = [f'<g transform="translate({_f(x)},{_f(y)}) scale({s:.4f})">']
    out.append(f'<clipPath id="hen-body"><path d="{body}"/></clipPath>')
    # Ground: a few short strokes under the feet.
    out.append(f'<path d="M126,276 L214,276 M142,281 L200,281 M158,286 L184,286" stroke="{ink}" stroke-width="1.0" stroke-linecap="round"/>')
    # Legs (behind the body): tapered shanks, scale marks, toes and spur.
    out.append(f'<path d="M160,218 C159,236 156,252 152,268 M186,220 C187,238 188,252 190,266" fill="none" stroke="{ink}" stroke-width="5.2" stroke-linecap="round"/>')
    toes = (
        'M152,268 C160,269 168,271 176,274 M152,268 C156,272 160,276 164,279 M152,268 C146,270 141,272 136,274 '
        'M190,266 C198,267 206,269 214,272 M190,266 C194,270 198,274 201,277 M190,266 C184,268 179,270 174,272'
    )
    out.append(f'<path d="{toes}" fill="none" stroke="{ink}" stroke-width="2.6" stroke-linecap="round"/>')
    out.append(
        f'<path d="M154,240 l5,1.2 M153,248 l5,1.2 M152,256 l5,1.2 M185,238 l5,0.6 M186,246 l5,0.6 M186,254 l5,0.6" '
        f'stroke="{paper}" stroke-width="0.9"/>'
    )
    # The white bird.
    out.append(f'<path d="{body}" fill="{paper}"/>')
    # Underside: from under the tail round the belly, a solid black band with
    # a feathered upper edge, deepest at the rear of the belly, and hatching
    # above it fading into the white.
    i0 = min(range(len(dense)), key=lambda i: math.dist(dense[i], (16, 84)))
    i1 = min(range(len(dense)), key=lambda i: math.dist(dense[i], (206, 222)))
    under = dense[i0 : i1 + 1]
    depth = lambda t: 15 * math.sin(math.pi * min(1.0, t * 1.1)) ** 0.7 + 2  # noqa: E731
    shade = f'<clipPath id="hen-shade"><path d="{_band(under, lambda t: depth(t) * 1.9 + 6, 0.35, 5)}"/></clipPath>'
    out.append(shade)
    out.append(_hatch('hen-shade', -58, 2.4, (0, 70, 240, 232), 0.8, ink, wobble=0.8, seed=3))
    out.append(f'<path d="{_band(under, depth, 0.45, 9)}" fill="{ink}" clip-path="url(#hen-body)"/>')
    # Breast: a thin shaded edge on the right.
    j0 = min(range(len(dense)), key=lambda i: math.dist(dense[i], (262, 186)))
    j1 = min(range(len(dense)), key=lambda i: math.dist(dense[i], (270, 88)))
    breast = dense[j0 : j1 + 1]
    out.append(f'<path d="{_band(breast, lambda t: 7 * math.sin(math.pi * t) + 1, 0.6, 12)}" fill="{ink}" clip-path="url(#hen-body)"/>')
    # Tail: short curved partings running in from each notch, and loose
    # feather marks over the fan.
    tail = (
        'M30,13 C42,24 54,34 66,42 M18,20 C32,32 46,44 58,52 M15,32 C30,42 44,52 56,60 '
        'M11,49 C26,56 40,62 54,68 M12,68 C26,72 40,76 52,80 M12,84 C24,88 38,92 50,96'
    )
    out.append(f'<path d="{tail}" fill="none" stroke="{ink}" stroke-width="0.9" stroke-linecap="round" clip-path="url(#hen-body)"/>')
    rnd = random.Random(11)
    tmarks = [(46 + rnd.uniform(-4, 4) + 10 * (i % 3), 40 + 14 * (i // 3) + rnd.uniform(-3, 3)) for i in range(12)]
    out.append(_scallops(tmarks, 8, 4, ink, 0.8, clip='hen-body'))
    # Neck hackles: fine strands from the nape over the shoulder.
    hack = (
        'M232,40 C228,56 222,70 214,82 M240,44 C238,60 232,74 224,88 M248,52 C248,66 244,80 236,92 '
        'M256,62 C258,74 256,86 250,98 M224,46 C218,58 210,68 200,76'
    )
    out.append(f'<path d="{hack}" fill="none" stroke="{ink}" stroke-width="0.8" stroke-linecap="round"/>')
    out.append(_scallops([(206, 86), (216, 92), (227, 97), (238, 101), (249, 104)], 9, 4.5, ink, 0.85, clip='hen-body'))
    # Wing: only suggested, by loose rows of coverts and three primaries.
    cov = [(204 - i * 12 + rnd.uniform(-2, 2), 118 + i * 1.5 + rnd.uniform(-2, 2)) for i in range(6)]
    cov += [(198 - i * 12 + rnd.uniform(-2, 2), 133 + i * 1.8 + rnd.uniform(-2, 2)) for i in range(5)]
    out.append(_scallops(cov, 10, 5, ink, 0.85, clip='hen-body'))
    prim = 'M196,152 C176,158 154,156 134,148 M188,162 C168,166 148,163 128,155'
    out.append(f'<path d="{prim}" fill="none" stroke="{ink}" stroke-width="0.8" stroke-linecap="round"/>')
    # Stipple: an engraver's dots, thickening towards the shaded underside.
    dots = []
    for _ in range(420):
        px, py = rnd.uniform(20, 276), rnd.uniform(40, 226)
        # keep dots mostly low and at the rear, where the form turns away
        w = (py - 60) / 170 + (0.6 if px < 90 else 0.0) - (0.35 if 120 < px < 230 and py < 150 else 0.0)
        if rnd.random() < w * 0.7:
            dots.append(f'<circle cx="{_f(px)}" cy="{_f(py)}" r="{rnd.uniform(0.45, 0.9):.2f}"/>')
    out.append(f'<g fill="{ink}" clip-path="url(#hen-body)">{"".join(dots)}</g>')
    # Breast and flank feathers: sparse marks, denser towards the shade.
    marks = []
    for cx0, cy0, n_, dx, dy in ((236, 128, 4, -6, 14), (250, 124, 5, -4, 14), (224, 176, 5, -12, 6), (96, 132, 5, 12, 10), (68, 104, 4, 12, 12)):
        for i in range(n_):
            marks.append((cx0 + dx * i + rnd.uniform(-2, 2), cy0 + dy * i + rnd.uniform(-2, 2)))
    out.append(_scallops(marks, 8, 4, ink, 0.8, clip='hen-body'))
    # Outline.
    out.append(f'<path d="{body}" fill="none" stroke="{ink}" stroke-width="1.7" stroke-linejoin="round"/>')
    # Head: comb, beak, wattle, eye, ear lobe.
    out.append(f'<path d="{HEN_COMB}" fill="{ink}"/>')
    out.append(f'<path d="{HEN_BEAK}" fill="{paper}" stroke="{ink}" stroke-width="1.5" stroke-linejoin="round"/>')
    out.append(f'<path d="M267,45.5 L278,46" stroke="{ink}" stroke-width="0.8"/>')
    out.append(f'<path d="{HEN_WATTLE}" fill="{ink}"/>')
    out.append(f'<path d="M243,46 C247,44 251,47 250,52 C249,57 243,57 242,53 C241,50 241,48 243,46 Z" fill="{ink}"/>')
    out.append(f'<circle cx="254" cy="38" r="2.4" fill="{ink}"/>')
    out.append(f'<path d="M249,34.5 Q254,32 259,35" fill="none" stroke="{ink}" stroke-width="0.8"/>')
    out.append('</g>')
    return ''.join(out)


# ----------------------------------------------------------------- potato plant


def _leaflet(bx, by, length, width, angle, bend, ink, shade=1, hatch=True, seed=0) -> str:
    """An ovate, pointed leaflet from (bx, by) along `angle` (degrees), its
    midrib bending sideways by `bend`. Midrib, side veins stopping short of
    the margin, and fine hatching on the `shade` half."""
    rnd = random.Random(seed)
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux

    def mid(t):  # point on the (quadratic) midrib
        off = bend * 4 * t * (1 - t)
        return bx + ux * length * t + nx * off, by + uy * length * t + ny * off

    def P(t, f):
        mx, my = mid(t)
        return mx + nx * width * f, my + ny * width * f

    prof = [(0.1, 0.3), (0.26, 0.48), (0.45, 0.5), (0.65, 0.4), (0.82, 0.22), (0.93, 0.08)]
    a1 = 1 + rnd.uniform(-0.08, 0.08)
    a2 = 1 + rnd.uniform(-0.08, 0.08)
    outline = [mid(0)] + [P(t, f * a1) for t, f in prof] + [mid(1)] + [P(t, -f * a2) for t, f in reversed(prof)]
    d = _catmull(outline, closed=True, tension=0.55)
    cid = f'lf{next(_ids)}'
    out = [f'<clipPath id="{cid}"><path d="{d}"/></clipPath>']
    out.append(f'<path d="{d}" fill="{PAPER}" stroke="{ink}" stroke-width="1.3" stroke-linejoin="round"/>')
    rib = [mid(t) for t in (0, 0.25, 0.5, 0.75, 0.94)]
    out.append(f'<path d="{_catmull(rib)}" fill="none" stroke="{ink}" stroke-width="0.95"/>')
    veins = []
    for t in (0.2, 0.36, 0.52, 0.68):
        for sg in (1, -1):
            m0 = mid(t)
            m1 = P(t + 0.14, sg * 0.3)
            veins.append(f'M{_f(m0[0])},{_f(m0[1])} L{_f(m1[0])},{_f(m1[1])}')
    out.append(f'<path d="{" ".join(veins)}" fill="none" stroke="{ink}" stroke-width="0.6" stroke-linecap="round"/>')
    if hatch:
        hat = []
        for i in range(2, 17):
            t = i / 18
            m0 = P(t, shade * 0.18)
            m1 = P(t + 0.04, shade * 0.6)
            hat.append(f'M{_f(m0[0])},{_f(m0[1])} L{_f(m1[0])},{_f(m1[1])}')
        out.append(f'<path d="{" ".join(hat)}" fill="none" stroke="{ink}" stroke-width="0.5" stroke-linecap="round" clip-path="url(#{cid})"/>')
    return ''.join(out)


def _tuber(cx, cy, rx, ry, angle, ink, seed, dark=0.5) -> str:
    """A potato: a lumpy oblong with engraved contour lines wrapping its
    shaded side (more of them for `dark`), stipple, and a few eyes."""
    rnd = random.Random(seed)
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)

    def R(x, y):
        return cx + x * ca - y * sa, cy + x * sa + y * ca

    pts = []
    for i in range(14):
        t = 2 * math.pi * i / 14
        k = 1 + rnd.uniform(-0.07, 0.07)
        pts.append(R(rx * math.cos(t) * k, ry * math.sin(t) * k))
    d = _catmull(pts, closed=True)
    cid = f'tb{next(_ids)}'
    out = [f'<clipPath id="{cid}"><path d="{d}"/></clipPath>']
    out.append(f'<path d="{d}" fill="{PAPER}"/>')
    # Contour lines wrapping the form: fine and far apart on the lit top,
    # heavier and closer into the shaded underside.
    for group, (f0, f1, n, w) in enumerate(((-0.55, 0.1, 4, 0.35), (0.12, 1.0, int(6 + 10 * dark), 0.6))):
        arcs = []
        for i in range(n):
            t = i / max(1, n - 1)
            f = f0 + (f1 - f0) * (t ** 0.75 if group else t)
            oy = ry * f
            half = rx * math.sqrt(max(0.05, 1 - min(0.97, abs(f)) ** 2)) * 1.1
            bow = ry * 0.24 * (1 - 0.4 * abs(f))
            p0, p1, p2 = R(-half, oy - bow), R(0, oy + bow), R(half, oy - bow)
            arcs.append(f'M{_f(p0[0])},{_f(p0[1])} Q{_f(p1[0])},{_f(p1[1])} {_f(p2[0])},{_f(p2[1])}')
        out.append(f'<path d="{" ".join(arcs)}" fill="none" stroke="{ink}" stroke-width="{w}" clip-path="url(#{cid})"/>')
    dots = []
    for _ in range(int(70 * dark * rx * ry / 900)):
        u, v = rnd.uniform(-1, 1), rnd.uniform(0.0, 1)
        if u * u + v * v < 0.9:
            px, py = R(rx * u, ry * v)
            dots.append(f'<circle cx="{_f(px)}" cy="{_f(py)}" r="{rnd.uniform(0.4, 0.8):.2f}"/>')
    out.append(f'<g fill="{ink}" clip-path="url(#{cid})">{"".join(dots)}</g>')
    # Eyes: tiny shallow pits, drawn as short dark flecks.
    eyes = []
    for t, rr in ((5.5, 0.72), (3.0, 0.45), (1.2, 0.7)):
        ex, ey = R(rx * rr * math.cos(t), ry * rr * math.sin(t))
        eyes.append(f'<ellipse cx="{_f(ex)}" cy="{_f(ey)}" rx="1.6" ry="0.8" transform="rotate({angle + rnd.uniform(-30, 30):.0f} {_f(ex)} {_f(ey)})"/>')
    out.append(f'<g fill="{ink}">{"".join(eyes)}</g>')
    out.append(f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="1.3"/>')
    return ''.join(out)


def potato_plant(x: float, y: float, s: float, ink: str = INK) -> str:
    """A potato plant lifted with its tubers, in the manner of the sleeve's
    botanical engraving: a slender stem, a few large simple leaves (the
    biggest pair opening in a V at the top), roots, and a cluster of shaded
    tubers at the base. Design box about 250 x 490."""
    out = [f'<g transform="translate({_f(x)},{_f(y)}) scale({s:.4f})">']
    # Roots and stolons.
    roots = [
        [(121, 368), (106, 386), (86, 398)],
        [(123, 368), (140, 384), (160, 398)],
        [(122, 370), (120, 392), (126, 414)],
        [(124, 372), (132, 396), (146, 404)],
    ]
    for r in roots:
        out.append(f'<path d="{_catmull(r)}" fill="none" stroke="{ink}" stroke-width="1.0" stroke-linecap="round"/>')
    rnd = random.Random(5)
    hairs = []
    for _ in range(22):
        bx, by = 122 + rnd.uniform(-22, 22), 378 + rnd.uniform(0, 44)
        ang = math.radians(rnd.uniform(40, 140))
        ln = rnd.uniform(6, 14)
        hairs.append(f'M{_f(bx)},{_f(by)} l{_f(math.cos(ang) * ln)},{_f(math.sin(ang) * ln)}')
    out.append(f'<path d="{" ".join(hairs)}" fill="none" stroke="{ink}" stroke-width="0.5" stroke-linecap="round"/>')
    # Tubers: a big one standing at the left, a long one lying to the right,
    # two small dark ones tucked between.
    out.append(_tuber(170, 426, 52, 27, 22, ink, 22, dark=0.6))
    out.append(_tuber(84, 432, 31, 52, -18, ink, 21, dark=0.85))
    out.append(_tuber(114, 398, 16, 13, 20, ink, 23, dark=1.0))
    out.append(_tuber(142, 402, 14, 11, -30, ink, 24, dark=1.0))
    # Stem: a gently curving double line.
    stem = [(121, 374), (118, 330), (121, 280), (125, 230), (124, 180), (127, 130), (130, 86), (132, 56)]
    out.append(f'<path d="{_catmull(stem)}" fill="none" stroke="{ink}" stroke-width="3.2" stroke-linecap="round"/>')
    out.append(f'<path d="{_catmull(stem)}" fill="none" stroke="{PAPER}" stroke-width="1.1" stroke-linecap="round"/>')
    # Leaves: (base x, base y, angle, length, width, bend, shade, hatch).
    leaves = [
        (120, 330, 196, 44, 24, -3, 1, False),
        (121, 300, -18, 50, 26, 3, -1, True),
        (124, 256, 202, 62, 32, -4, 1, True),
        (125, 222, -26, 62, 32, 4, -1, False),
        (124, 178, 212, 66, 34, -4, -1, True),
        (127, 146, -34, 64, 32, 4, 1, True),
        (130, 92, 236, 92, 44, -6, 1, True),
        (131, 100, -56, 88, 42, 6, -1, True),
    ]
    for i, (bx, by, ang, ln, wd, bend, shade, hat) in enumerate(leaves):
        a = math.radians(ang)
        # a short leaf stalk
        sx, sy = bx + math.cos(a) * 8, by + math.sin(a) * 8
        out.append(f'<path d="M{_f(bx)},{_f(by)} L{_f(sx)},{_f(sy)}" stroke="{ink}" stroke-width="1.2" stroke-linecap="round"/>')
        out.append(_leaflet(sx, sy, ln, wd, ang, bend, ink, shade=shade, hatch=hat, seed=40 + i * 5))
    # Crown: a small folded leaf at the tip.
    out.append(_leaflet(132, 58, 34, 16, -84, 2, ink, shade=1, hatch=True, seed=81))
    out.append('</g>')
    return ''.join(out)
