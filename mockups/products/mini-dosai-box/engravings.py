"""Engraving-style line art for the Mini Dosai sleeves, as SVG snippets.

Both drawings are traced from the sleeves in source/crops/mini-dosai-boxes.png
(hand-placed outlines on a grid over the enlarged crop) plus generated detail:
contour lines and feather strokes on the hen, veins, hatching and wrapped
contour lines on the leaves and tubers.

hen(x, y, sx, sy): a white hen standing, facing right (the chicken sleeve),
on a 1050 x 980 design box.
potato_plant(x, y, s, sy): a potato plant lifted with its tubers (the veg
sleeve), on an 840 x 1140 design box.
(x, y) places the design box's origin on the artwork; the scales map it on.
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


# ----------------------------------------------------------------- the hen

# Silhouette, traced from the sleeve's engraving on a 1050 x 980 design box
# (y down): a plump hen in three-quarter profile facing right, its tail fan
# raised at the upper left, the back dipping to a short neck, the breast full
# at the right and the body sloping down to the legs at the lower middle.
# Order: beak tip, crown, nape, back, the tail-feather tips, the underside,
# belly, breast, throat.
HEN_OUTLINE = [
    (846, 184), (836, 168), (824, 156), (810, 140), (788, 128), (760, 121), (732, 125), (708, 137),
    (686, 154), (664, 174), (644, 198), (622, 224), (598, 246), (570, 262),
    (534, 268), (494, 264), (452, 255), (410, 243), (372, 229), (336, 213), (304, 195), (276, 173), (252, 150), (232, 126),
    (220, 106), (212, 96), (200, 93), (192, 100), (198, 118),
    (178, 116), (160, 121), (150, 132), (168, 150),
    (138, 150), (120, 160), (113, 175), (140, 192),
    (122, 200), (114, 214), (122, 228), (150, 240),
    (132, 250), (130, 266), (142, 278), (162, 292),
    (148, 300), (146, 316), (156, 332), (172, 348),
    (190, 380), (212, 413), (238, 445), (266, 475), (292, 503), (314, 533), (338, 565), (366, 595), (398, 621), (432, 641), (468, 655), (502, 657),
    (540, 648), (572, 628), (604, 600), (640, 574), (684, 548), (724, 518), (760, 480), (790, 438), (812, 394), (826, 348), (832, 302), (828, 264), (818, 238), (804, 220),
    (814, 206), (828, 196), (840, 190),
]
# Index ranges of HEN_OUTLINE (inclusive) for the shaded stretches.
_UNDER = (47, 60)  # under the tail to the legs
_BREAST = (68, 72)  # the breast's shaded right edge
HEN_COMB = (
    'M708,138 C704,122 712,106 726,108 C722,90 738,78 750,88 C750,70 772,60 782,74 '
    'C790,60 812,64 812,80 C826,78 834,92 826,104 C836,110 834,126 822,130 '
    'C812,146 798,138 790,130 C770,124 748,124 730,132 C722,138 714,142 708,138 Z'
)
HEN_BEAK = 'M824,158 C832,160 842,170 850,184 C842,186 834,190 826,194'
# The face: the red ear lobe and the wattle, both printed solid.
HEN_FACE = (
    'M726,160 C734,152 746,156 750,166 C754,178 750,192 742,196 C732,198 724,188 724,176 C724,170 724,164 726,160 Z '
    'M790,192 C800,186 816,190 818,202 C820,216 810,226 798,224 C786,222 780,212 782,202 C784,198 786,194 790,192 Z'
)


def _densify(pts, closed=False, per=8):
    """Points along the Catmull-Rom curve through pts."""
    n = len(pts)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[i - 1] if (closed or i > 0) else pts[0]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                for j in (0, 1)
            ))
    if not closed:
        out.append(pts[-1])
    return out


def _offset(curve, d, sign=1.0):
    """The polyline moved by d along its left-hand normal (sign flips it)."""
    out = []
    n = len(curve)
    for i, (x, y) in enumerate(curve):
        a, b = curve[max(0, i - 1)], curve[min(n - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        dd = d(i / (n - 1)) if callable(d) else d
        out.append((x - ty / ln * dd * sign, y + tx / ln * dd * sign))
    return out


def _poly(pts) -> str:
    return 'M' + ' L'.join(f'{_f(x)},{_f(y)}' for x, y in pts)


def hen(x: float, y: float, sx: float, sy: float | None = None, ink: str = INK, paper: str = PAPER) -> str:
    """A white hen standing, facing right, in the manner of the sleeve's steel
    engraving: a heavy black underside whose upper edge breaks into feather
    tips, contour lines that turn the body, short feather strokes on the white,
    a solid comb, lobe and wattle, and dark legs. (x, y) places the design
    box's origin; sx, sy scale it."""
    sy = sx if sy is None else sy
    rnd = random.Random(7)
    body = _catmull(HEN_OUTLINE, closed=True)
    out = [f'<g transform="translate({_f(x)},{_f(y)}) scale({sx:.4f},{sy:.4f})">']
    out.append(f'<clipPath id="hen-body"><path d="{body}"/></clipPath>')
    grey = f'stroke="{ink}" fill="none" stroke-linecap="round"'

    # Ground: a few short strokes under the feet.
    out.append(f'<path d="M470,770 L690,770 M500,782 L640,782 M540,794 L600,794" {grey} stroke-width="2.4" opacity="0.7"/>')
    # Legs: the far leg a little lighter, the near one heavy; scaled shanks,
    # three forward toes and a hind toe each.
    for (hx, hy), (kx, ky), (fx, fy), w, op in (
        ((548, 640), (556, 700), (566, 748), 11, 0.75),
        ((506, 646), (512, 700), (528, 752), 15, 1.0),
    ):
        out.append(f'<path d="M{hx},{hy} Q{kx},{ky} {fx},{fy}" {grey} stroke-width="{w}" opacity="{op}"/>')
        toes = (
            f'M{fx},{fy} C{fx + 40},{fy + 4} {fx + 80},{fy + 10} {fx + 118},{fy + 16} '
            f'M{fx},{fy} C{fx + 24},{fy + 12} {fx + 44},{fy + 22} {fx + 64},{fy + 30} '
            f'M{fx},{fy} C{fx - 24},{fy + 4} {fx - 48},{fy + 8} {fx - 70},{fy + 12}'
        )
        out.append(f'<path d="{toes}" {grey} stroke-width="{w * 0.55:.1f}" opacity="{op}"/>')
        scales = ' '.join(f'M{hx + (fx - hx) * t - w * 0.4:.1f},{hy + (fy - hy) * t:.1f} l{w * 0.8:.1f},2' for t in (0.3, 0.45, 0.6, 0.75))
        out.append(f'<path d="{scales}" stroke="{paper}" stroke-width="1.6" fill="none"/>')

    # The white bird.
    out.append(f'<path d="{body}" fill="{paper}"/>')

    dense = _densify(HEN_OUTLINE, closed=True, per=8)
    under = dense[_UNDER[0] * 8 : _UNDER[1] * 8 + 1]
    # The outline runs anticlockwise on the page, so its interior lies to the
    # left of travel: _offset with sign=-1 moves inwards.
    # Contour lines turning the body: offsets of the underside, broken into
    # dashes and thinning upwards into the white.
    lines = []
    for k in range(1, 9):
        d = 34 + k * 17
        crv = _offset(under, lambda t, d=d: d * (0.55 + 0.45 * math.sin(math.pi * min(1.0, t * 1.15))), sign=-1)
        # dashes: longer and denser low down
        i = 0
        while i < len(crv) - 3:
            ln = rnd.randint(5, 12) - k // 2
            gap = rnd.randint(1, 3) + k // 2
            seg = crv[i : i + max(3, ln)]
            if len(seg) > 1:
                lines.append((_poly(seg), max(1.4, 4.2 - k * 0.38)))
            i += max(3, ln) + gap
    for d_, w in lines:
        out.append(f'<path d="{d_}" {grey} stroke-width="{w:.2f}" clip-path="url(#hen-body)"/>')

    # The heavy underside: a solid band whose upper edge breaks into a row of
    # pointed feather tips.
    depth = lambda t: 18 + 30 * math.sin(math.pi * min(1.0, t * 1.08)) ** 0.8  # noqa: E731
    inner = _offset(under, depth, sign=-1)
    jag = []
    for i, (px, py) in enumerate(inner):
        a, b = inner[max(0, i - 1)], inner[min(len(inner) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = ty / ln, -tx / ln  # inwards (the interior is left of travel)
        k = (14 if (i % 6) < 3 else 0) * rnd.uniform(0.6, 1.3)
        jag.append((px + nx * k, py + ny * k))
    band = under + list(reversed(jag))
    out.append(f'<path d="{_poly(band)} Z" fill="{ink}" clip-path="url(#hen-body)"/>')
    # Feather tips standing proud of the band.
    tips = []
    for i in range(3, len(jag) - 3, 6):
        px, py = jag[i]
        qx, qy = under[i]
        dx, dy = px - qx, py - qy
        ln = math.hypot(dx, dy) or 1.0
        dx, dy = dx / ln, dy / ln
        l = rnd.uniform(10, 22)
        tips.append(f'M{_f(px - dy * 6)},{_f(py + dx * 6)} L{_f(px + dx * l)},{_f(py + dy * l)} L{_f(px + dy * 6)},{_f(py - dx * 6)} Z')
    out.append(f'<path d="{" ".join(tips)}" fill="{ink}" clip-path="url(#hen-body)"/>')

    # The breast's shaded edge, heavy at mid height.
    br = dense[_BREAST[0] * 8 : _BREAST[1] * 8 + 1]
    edge = _offset(br, lambda t: 2 + 14 * math.sin(math.pi * t) ** 1.2, sign=-1)
    out.append(f'<path d="{_poly(br + list(reversed(edge)))} Z" fill="{ink}" clip-path="url(#hen-body)"/>')

    # Tail: the feathers' partings and shafts, from each notch into the body.
    tail = (
        'M198,118 C240,156 290,192 340,214 M168,150 C210,182 256,218 306,246 '
        'M140,192 C182,218 228,252 282,288 M150,240 C188,262 226,292 266,326 '
        'M162,292 C190,312 214,338 238,368'
    )
    out.append(f'<path d="{tail}" {grey} stroke-width="2.6" clip-path="url(#hen-body)"/>')
    # Fine lines along each tail feather, towards its tip.
    vanes = []
    for (ax, ay), (bx, by) in (((204, 100), (330, 200)), ((158, 128), (300, 226)), ((120, 170), (270, 262)), ((120, 214), (250, 300)), ((136, 266), (230, 340))):
        for k in (-7, 0, 7):
            ln = math.hypot(bx - ax, by - ay)
            nx, ny = -(by - ay) / ln * k, (bx - ax) / ln * k
            t0 = rnd.uniform(0.05, 0.2)
            vanes.append(f'M{_f(ax + (bx - ax) * t0 + nx)},{_f(ay + (by - ay) * t0 + ny)} L{_f(bx + nx * 0.4)},{_f(by + ny * 0.4)}')
    out.append(f'<path d="{" ".join(vanes)}" {grey} stroke-width="1.2" opacity="0.7" clip-path="url(#hen-body)"/>')

    # Wing: the folded wing's lower edge, the covert rows and primaries.
    wing = (
        'M436,392 C446,430 488,460 540,470 C584,476 624,462 652,436 '
        'M470,412 C500,436 540,448 590,446 M452,370 C470,346 500,334 532,330 '
        'M610,330 C628,340 640,352 648,366'
    )
    out.append(f'<path d="{wing}" {grey} stroke-width="2.6" clip-path="url(#hen-body)"/>')

    # Feather strokes: short curved ticks, sparse on the lit back and breast,
    # denser low and to the rear, all following the flow from neck to tail.
    ticks = []
    for _ in range(950):
        px, py = rnd.uniform(130, 830), rnd.uniform(140, 650)
        # density: more towards the lower left, little on the upper right
        dens = 0.15 + 0.9 * ((py - 200) / 450) + 0.5 * ((600 - px) / 500)
        if 560 < px < 800 and py < 420:
            dens -= 0.45
        if rnd.random() > dens * 0.55:
            continue
        ang = math.radians(rnd.uniform(195, 215) + (px - 500) * 0.04)
        l = rnd.uniform(9, 17)
        ex, ey = px + math.cos(ang) * l, py + math.sin(ang) * l
        cx_, cy_ = (px + ex) / 2 - math.sin(ang) * 4, (py + ey) / 2 + math.cos(ang) * 4
        ticks.append(f'M{_f(px)},{_f(py)} Q{_f(cx_)},{_f(cy_)} {_f(ex)},{_f(ey)}')
    out.append(f'<path d="{" ".join(ticks)}" {grey} stroke-width="1.8" opacity="0.85" clip-path="url(#hen-body)"/>')
    # Neck hackles: fine strands from the crown over the shoulder.
    hack = (
        'M712,150 C690,190 664,226 632,254 M736,150 C720,196 696,236 664,266 M760,160 C750,206 730,246 700,280 '
        'M786,200 C784,238 772,272 748,302 M808,230 C808,262 798,292 780,318'
    )
    out.append(f'<path d="{hack}" {grey} stroke-width="1.5" opacity="0.8" clip-path="url(#hen-body)"/>')

    # Outline: fine over the back, heavier along the breast.
    out.append(f'<path d="{body}" fill="none" stroke="{ink}" stroke-width="3.0" stroke-linejoin="round"/>')
    # Head: comb, beak, lobe and wattle, eye.
    out.append(f'<path d="{HEN_COMB}" fill="{ink}"/>')
    out.append(f'<path d="{HEN_BEAK}" fill="{paper}" stroke="{ink}" stroke-width="3" stroke-linejoin="round"/>')
    out.append(f'<path d="M830,174 L846,182" stroke="{ink}" stroke-width="1.6"/>')
    out.append(f'<path d="{HEN_FACE}" fill="{ink}"/>')
    out.append(f'<circle cx="782" cy="160" r="7.5" fill="{ink}"/><circle cx="784" cy="158" r="2" fill="{paper}"/>')
    out.append(f'<path d="M770,150 Q782,142 796,150" {grey} stroke-width="1.6"/>')
    out.append('</g>')
    return ''.join(out)


# ----------------------------------------------------------------- potato plant


def _leaflet(bx, by, length, width, angle, bend, ink, shade=1, hatch=True, seed=0, lw=1.0) -> str:
    """An ovate, pointed leaf from (bx, by) along `angle` (degrees), its
    midrib bending sideways by `bend`; `width` is its full width. Midrib,
    side veins stopping short of the margin, and fine hatching on the
    `shade` half. lw scales every line."""
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

    prof = [(0.08, 0.26), (0.22, 0.45), (0.4, 0.5), (0.6, 0.44), (0.78, 0.3), (0.92, 0.12)]
    a1 = 1 + rnd.uniform(-0.1, 0.1)
    a2 = 1 + rnd.uniform(-0.1, 0.1)
    outline = [mid(0)] + [P(t, f * a1) for t, f in prof] + [mid(1)] + [P(t, -f * a2) for t, f in reversed(prof)]
    d = _catmull(outline, closed=True, tension=0.55)
    cid = f'lf{next(_ids)}'
    out = [f'<clipPath id="{cid}"><path d="{d}"/></clipPath>']
    out.append(f'<path d="{d}" fill="{PAPER}" stroke="{ink}" stroke-width="{1.5 * lw:.2f}" stroke-linejoin="round"/>')
    rib = [mid(t) for t in (0, 0.25, 0.5, 0.75, 0.94)]
    out.append(f'<path d="{_catmull(rib)}" fill="none" stroke="{ink}" stroke-width="{1.1 * lw:.2f}"/>')
    veins = []
    for t in (0.18, 0.34, 0.5, 0.66, 0.8):
        for sg in (1, -1):
            m0 = mid(t)
            m1 = P(min(0.9, t + 0.12), sg * 0.3)
            veins.append(f'M{_f(m0[0])},{_f(m0[1])} Q{_f((m0[0] + m1[0]) / 2 + ux * 3)},{_f((m0[1] + m1[1]) / 2 + uy * 3)} {_f(m1[0])},{_f(m1[1])}')
    out.append(f'<path d="{" ".join(veins)}" fill="none" stroke="{ink}" stroke-width="{0.7 * lw:.2f}" stroke-linecap="round" clip-path="url(#{cid})"/>')
    if hatch:
        hat = []
        for i in range(2, 21):
            t = i / 22
            m0 = P(t, shade * 0.12)
            m1 = P(t + 0.05, shade * 0.55)
            hat.append(f'M{_f(m0[0])},{_f(m0[1])} L{_f(m1[0])},{_f(m1[1])}')
        out.append(f'<path d="{" ".join(hat)}" fill="none" stroke="{ink}" stroke-width="{0.6 * lw:.2f}" stroke-linecap="round" opacity="0.8" clip-path="url(#{cid})"/>')
    return ''.join(out)


def _tuber(cx, cy, rx, ry, angle, ink, seed, dark=0.5, lw=1.0) -> str:
    """A potato: a lumpy oblong with engraved contour lines wrapping its
    shaded side (more of them for `dark`), stipple, and a few eyes."""
    rnd = random.Random(seed)
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)

    def R(x, y):
        return cx + x * ca - y * sa, cy + x * sa + y * ca

    pts = []
    for i in range(16):
        t = 2 * math.pi * i / 16
        k = 1 + rnd.uniform(-0.06, 0.06)
        pts.append(R(rx * math.cos(t) * k, ry * math.sin(t) * k))
    d = _catmull(pts, closed=True)
    cid = f'tb{next(_ids)}'
    out = [f'<clipPath id="{cid}"><path d="{d}"/></clipPath>']
    out.append(f'<path d="{d}" fill="{PAPER}"/>')
    # Contour lines across the long axis, wrapping the form: sparse and fine
    # on the lit side, closer and heavier into the shaded side.
    arcs = []
    n = int(8 + 12 * dark)
    for i in range(n):
        t = i / (n - 1)
        f = -0.9 + 1.8 * t ** 0.8
        ox = rx * f
        half = ry * math.sqrt(max(0.04, 1 - min(0.98, abs(f)) ** 2)) * 1.1
        bow = rx * 0.22
        p0, p1, p2 = R(ox - bow * 0.3, -half), R(ox + bow, 0), R(ox - bow * 0.3, half)
        w = (0.5 + 0.9 * t) * lw
        arcs.append((f'M{_f(p0[0])},{_f(p0[1])} Q{_f(p1[0])},{_f(p1[1])} {_f(p2[0])},{_f(p2[1])}', w))
    for dd, w in arcs:
        out.append(f'<path d="{dd}" fill="none" stroke="{ink}" stroke-width="{w:.2f}" opacity="0.75" clip-path="url(#{cid})"/>')
    # Shadow side: a crescent of fine hatching along the lower edge.
    hat = []
    for i in range(24):
        t = math.pi * (0.1 + 0.8 * i / 23)
        px, py = R(rx * math.cos(t) * 0.98, ry * math.sin(t) * 0.98)
        qx, qy = R(rx * math.cos(t) * 0.7, ry * math.sin(t) * 0.62)
        hat.append(f'M{_f(px)},{_f(py)} L{_f(qx)},{_f(qy)}')
    out.append(f'<path d="{" ".join(hat)}" fill="none" stroke="{ink}" stroke-width="{0.9 * lw:.2f}" opacity="{0.4 + 0.5 * dark:.2f}" clip-path="url(#{cid})"/>')
    # Eyes: tiny shallow pits, drawn as short dark flecks.
    eyes = []
    for t, rr in ((5.5, 0.6), (3.2, 0.5), (1.0, 0.55), (2.2, 0.75)):
        ex, ey = R(rx * rr * math.cos(t), ry * rr * math.sin(t))
        eyes.append(f'<ellipse cx="{_f(ex)}" cy="{_f(ey)}" rx="{3.2 * lw:.1f}" ry="{1.4 * lw:.1f}" transform="rotate({angle + rnd.uniform(-30, 30):.0f} {_f(ex)} {_f(ey)})"/>')
    out.append(f'<g fill="{ink}" opacity="0.85">{"".join(eyes)}</g>')
    out.append(f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{1.8 * lw:.2f}"/>')
    return ''.join(out)


PLANT_INK = '#37322f'


def potato_plant(x: float, y: float, s: float, sy: float | None = None, ink: str = PLANT_INK) -> str:
    """A potato plant lifted with its tubers, after the sleeve's botanical
    engraving (traced on an 840 x 1140 design box, y down): a slender,
    slightly wavering stem; broad ovate leaves in loose pairs, the largest
    opening in a V at the top, the lowest held out level; roots; and a
    cluster of shaded tubers at the foot, a long one standing at the left and
    one lying out to the right. (x, y) places the box; s (and sy) scale it."""
    lw = 2.8
    sy = s if sy is None else sy
    out = [f'<g transform="translate({_f(x)},{_f(y)}) scale({s:.4f},{sy:.4f})">']
    rnd = random.Random(5)
    # Roots and stolons, behind the tubers.
    roots = [
        [(430, 830), (400, 860), (360, 880)],
        [(432, 830), (470, 870), (500, 920)],
        [(430, 834), (436, 900), (450, 980), (470, 1030)],
        [(428, 834), (412, 900), (404, 960)],
        [(434, 836), (520, 860), (560, 900)],
    ]
    for r in roots:
        out.append(f'<path d="{_catmull(r)}" fill="none" stroke="{ink}" stroke-width="{1.2 * lw}" stroke-linecap="round"/>')
    hairs = []
    for _ in range(30):
        bx, by = 440 + rnd.uniform(-50, 60), 860 + rnd.uniform(0, 150)
        ang = math.radians(rnd.uniform(30, 150))
        ln = rnd.uniform(12, 26)
        hairs.append(f'M{_f(bx)},{_f(by)} l{_f(math.cos(ang) * ln)},{_f(math.sin(ang) * ln)}')
    out.append(f'<path d="{" ".join(hairs)}" fill="none" stroke="{ink}" stroke-width="{0.6 * lw}" stroke-linecap="round" opacity="0.8"/>')
    # Tubers: back ones first.
    out.append(_tuber(388, 930, 30, 36, 10, ink, 23, dark=1.0, lw=lw))
    out.append(_tuber(522, 962, 34, 46, -20, ink, 25, dark=0.9, lw=lw))
    out.append(_tuber(598, 978, 108, 46, 33, ink, 22, dark=0.6, lw=lw))
    out.append(_tuber(266, 898, 36, 60, -8, ink, 21, dark=0.7, lw=lw))
    out.append(_tuber(296, 1030, 50, 74, -14, ink, 24, dark=0.8, lw=lw))
    # Stem: a gently wavering double line.
    stem = [(432, 840), (424, 760), (432, 690), (438, 620), (434, 540), (440, 460), (436, 390), (444, 310), (452, 250)]
    out.append(f'<path d="{_catmull(stem)}" fill="none" stroke="{ink}" stroke-width="{3.4 * lw}" stroke-linecap="round"/>')
    out.append(f'<path d="{_catmull(stem)}" fill="none" stroke="{PAPER}" stroke-width="{1.2 * lw}" stroke-linecap="round"/>')
    # Leaves: base (on the stem), tip, full width, bend, shaded half, hatched.
    leaves = [
        ((420, 734), (290, 726), 54, -6, 1, False),
        ((440, 744), (562, 736), 56, 6, -1, True),
        ((424, 634), (262, 640), 76, -8, 1, True),
        ((444, 654), (606, 656), 82, 8, -1, False),
        ((432, 526), (320, 408), 92, -10, -1, True),
        ((442, 528), (586, 442), 38, 6, 1, True),
        ((440, 430), (536, 366), 58, 6, -1, True),
        ((444, 320), (302, 128), 124, -14, 1, True),
        ((452, 300), (598, 148), 120, 14, -1, True),
        ((452, 262), (478, 200), 40, 4, 1, False),
    ]
    for i, ((bx, by), (tx, ty), wd, bend, shade, hat) in enumerate(leaves):
        ang = math.degrees(math.atan2(ty - by, tx - bx))
        ln = math.hypot(tx - bx, ty - by)
        a = math.radians(ang)
        st = 0.12 * ln  # a short leaf stalk
        sx, sy = bx + math.cos(a) * st, by + math.sin(a) * st
        out.append(f'<path d="M{_f(bx)},{_f(by)} L{_f(sx)},{_f(sy)}" stroke="{ink}" stroke-width="{1.4 * lw}" stroke-linecap="round"/>')
        out.append(_leaflet(sx, sy, ln - st, wd, ang, bend, ink, shade=shade, hatch=hat, seed=40 + i * 5, lw=lw))
    out.append('</g>')
    return ''.join(out)
