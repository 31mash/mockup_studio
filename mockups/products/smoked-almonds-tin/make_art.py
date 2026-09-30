"""Smoked Almonds artwork, laid out on the tin's real dimensions (1 unit = 0.1 mm).
Run: python3 products/smoked-almonds-tin/make_art.py && node tools/raster.mjs products/smoked-almonds-tin/art

lid-top.svg  the lid seen from above, front edge at the bottom: a pile of
             almonds engraved in bronze line art on print black (grooves cut
             heavier on each nut's shadow side), a thin bronze ring near the
             edge, "Smoked Almonds" knocked out across the pile on the
             diagonal, and the veg mark turned to match.
lid-ink.svg  the same drawing as a mask, white where the metallic bronze ink
             is printed. product.py uses it to make only that ink metallic.
"""

import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

from brand.indigo import FONT, svg, veg_mark  # noqa: E402

import dims  # noqa: E402

U = 100  # units per cm
S = 2 * dims.R * U  # the lid-top image spans the lid's full width
C = S / 2

BLACK = '#0e1015'  # print black: a deep, slightly cool rich black
BRONZE = '#b99569'  # metallic bronze ink (its colour when it reflects white)

# Title in IndiGo's rounded lettering (Comfortaa Bold, with IndiGo's arched
# capital A drawn in), two left-aligned lines running up to the right.
# Positions matched on the photo by overlaying a render from its angle.
TITLE_ANGLE = 49  # degrees, anticlockwise
TITLE_CENTRE = (-0.25, -0.2)  # cm from the lid centre; x right, y to the front
F = 1.28 * U  # font size
TRACK = 0.075 * F  # letter spacing
CAP = 0.655 * F  # Comfortaa cap height
STEM = 0.115 * F  # Comfortaa Bold stem weight
HALO = 0.018 * U  # black keyline that keeps the almond lines off the letters

VEG = (-1.95, 3.75)  # veg mark centre, cm from the lid centre (front-left)
VEG_SIZE = 0.6 * U
PILE = (0.45, -0.35, 5.0)  # centre (cm) and reach of the almond pile


def fmt(pts):
    return 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)


# ----------------------------------------------------------------- almonds


LIGHT = (-0.6, -0.8)  # engraver's light, from the back-left (SVG y points to the front)


def wobble(rng, cycles, amp):
    """A smooth random wiggle along a line (s in 0..1), zero at both ends."""
    waves = [(rng.uniform(cycles * 0.6, cycles * 1.4), rng.uniform(0, 2 * math.pi), rng.uniform(0.5, 1.0)) for _ in range(3)]
    norm = sum(w for _, _, w in waves)
    return lambda s: amp * math.sin(math.pi * s) * sum(w * math.sin(2 * math.pi * f * s + p) for f, p, w in waves) / norm


def almond(rng, L, W):
    """One almond in local cm, long axis along +x (round base at -x, pointed
    tip at +x). Returns its outline and its skin grooves, drawn like an
    engraving: lines that run the length of the nut like meridians, each
    with its own slight crinkle and now and then a break, ends staggered so
    they never clot at the tip. Each groove is (points, side) where side is -1..1
    across the nut, so the caller can weight lines for shading."""
    bend = rng.uniform(-0.035, 0.035)
    asym = rng.uniform(-0.04, 0.04)
    p_base = rng.uniform(0.50, 0.58)
    p_tip = rng.uniform(0.74, 0.86)

    def prof(s):
        return s**p_base * (1 - s) ** p_tip

    smax = p_base / (p_base + p_tip)
    fmax = prof(smax)

    def hw(s, side):
        return W / 2 * prof(s) / fmax * (1 + side * asym)

    def point(s, off):
        cx, cy = (s - 0.45) * L, bend * L * math.sin(math.pi * s)
        dx, dy = L, bend * L * math.pi * math.cos(math.pi * s)
        n = math.hypot(dx, dy)
        return cx - dy / n * off, cy + dx / n * off

    N = 80
    ss = [(1 - math.cos(math.pi * i / N)) / 2 for i in range(N + 1)]
    outline = [point(s, hw(s, 1)) for s in ss] + [point(s, -hw(s, -1)) for s in reversed(ss[1:-1])]

    n = max(16, round(W / 0.058))
    theta = math.radians(78)
    shared = wobble(rng, 2.5, 0.010)  # the skin's broad wrinkles, shared by neighbours
    lines = []
    M = 48
    for k in range(n):
        t = math.sin(-theta + 2 * theta * (k + 0.5) / n)
        side = 1 if t > 0 else -1
        own = wobble(rng, rng.uniform(5.0, 8.0), 0.0065 * (1 - 0.8 * t * t))
        stag = (k % 2) * rng.uniform(0.04, 0.09)
        s0 = 0.04 + 0.05 * abs(t) + 0.5 * stag + rng.uniform(0, 0.03)
        s1 = 0.955 - 0.06 * abs(t) - stag - rng.uniform(0, 0.03)
        # Now and then a short break along the groove, as a burin skips.
        cuts = sorted(rng.uniform(s0 + 0.2, s1 - 0.2) for _ in range(rng.choice((0, 0, 1))))
        spans, a = [], s0
        for c in cuts:
            g = rng.uniform(0.02, 0.045)
            if c - g / 2 - a > 0.08:
                spans.append((a, c - g / 2))
                a = c + g / 2
        spans.append((a, s1))
        for a, b in spans:
            m = max(6, round(M * (b - a)))
            pts = []
            for i in range(m + 1):
                s = a + (b - a) * i / m
                off = t * hw(s, side) + shared(s) * (1 - t * t) + own(s)
                pts.append(point(s, off))
            lines.append((pts, t))
    return outline, lines


def poisson(rng, radius, r_min, tries=40):
    """Bridson's Poisson-disc sampling inside a circle (cm)."""
    pts = [(rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5))]
    active = [0]
    while active:
        i = rng.choice(active)
        px, py = pts[i]
        for _ in range(tries):
            a = rng.uniform(0, 2 * math.pi)
            d = rng.uniform(r_min, 2 * r_min)
            q = (px + d * math.cos(a), py + d * math.sin(a))
            if math.hypot(*q) > radius:
                continue
            if all(math.dist(q, p) >= r_min for p in pts):
                pts.append(q)
                active.append(len(pts) - 1)
                break
        else:
            active.remove(i)
    return pts


def inside(poly, x, y):
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def covered(pile, x, y, core=0.72):
    """Whether (x, y) lies well inside an almond, where its ridges are dense
    (not out at the tip or the rim, where the lines thin out)."""
    for cx, cy, rot, outline, _ in pile:
        dx, dy = x - cx, y - cy
        if dx * dx + dy * dy > 1.6:
            continue
        a = math.radians(-rot)
        lx, ly = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
        if inside(outline, lx / core, ly / core):
            return True
    return False


def title_frame(x, y):
    """A point in the title's frame (cm, origin at its centre) on the lid (cm from centre)."""
    a = math.radians(-TITLE_ANGLE)
    return TITLE_CENTRE[0] + x * math.cos(a) - y * math.sin(a), TITLE_CENTRE[1] + x * math.sin(a) + y * math.cos(a)


def build_pile(seed=5):
    rng = random.Random(seed)

    def nut(cx, cy):
        L = rng.uniform(1.95, 2.45)
        W = L * rng.uniform(0.54, 0.60)
        outline, lines = almond(rng, L, W)
        return (cx, cy, rng.uniform(0, 360), outline, lines)

    pile = []
    for cx, cy in poisson(rng, dims.ART_R + 0.3, 1.07):
        # Keep a quiet black field around the veg mark, as on the tin.
        if math.dist((cx, cy), VEG) < 1.25:
            continue
        # The pile sits a little up and to the right, so the black shows
        # through at the lid's left and front-left edge, as on the tin.
        if rng.random() > (PILE[2] - math.dist((cx, cy), PILE[:2])) / 0.9:
            continue
        pile.append(nut(cx, cy))
    rng.shuffle(pile)
    # The title is black knocked out of the ink, so it only reads where there
    # are almonds behind it: fill any gap under the lettering.
    samples = [title_frame(x * 0.2, y * 0.2) for x in range(-15, 16) for y in range(-6, 7)]
    rng.shuffle(samples)
    for x, y in samples:
        if not covered(pile, x, y):
            pile.insert(rng.randrange(len(pile) + 1), nut(x + rng.uniform(-0.3, 0.3), y + rng.uniform(-0.3, 0.3)))
    return pile


def pile_svg(pile, ink, bg):
    defs, body = [], []
    for i, (cx, cy, rot, outline, lines) in enumerate(pile):
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)

        def world(pts):
            return [(C + (cx + x * ca - y * sa) * U, C + (cy + x * sa + y * ca) * U) for x, y in pts]

        o = fmt(world(outline)) + 'Z'
        # Engraver's shading: grooves on the side turned from the light are
        # cut heavier, those facing it finer, so each nut reads as round.
        facing = -sa * LIGHT[0] + ca * LIGHT[1]
        defs.append(f'<clipPath id="al{i}"><path d="{o}"/></clipPath>')
        body.append(
            f'<path d="{o}" fill="{bg}"/>'
            f'<g clip-path="url(#al{i})" fill="none" stroke="{ink}" stroke-linecap="round" stroke-linejoin="round">'
            + ''.join(f'<path d="{fmt(world(p))}" stroke-width="{2.3 - 0.9 * facing * t:.2f}"/>' for p, t in lines)
            + '</g>'
            f'<path d="{o}" fill="none" stroke="{ink}" stroke-width="4.4" stroke-linejoin="round"/>'
        )
    return defs, body


# ----------------------------------------------------------------- title


def title_svg(color, halo):
    """'Smoked / Almonds' in the rotated title frame, origin at its centre."""
    x0 = -2.56 * U
    y1 = -0.2 * U  # baseline of Smoked
    y2 = y1 + 1.2 * U  # baseline of Almonds
    style = f'font-family="{FONT}" font-weight="700" font-size="{F:.1f}" letter-spacing="{TRACK:.1f}" fill="{color}"'
    stroke = f'stroke="{color}" stroke-width="{2 * halo:.1f}" stroke-linejoin="round" paint-order="stroke"'
    # IndiGo's capital A is an arch with a crossbar, narrower than Comfortaa's.
    ax = x0 - 0.02 * U
    aw = 0.54 * F
    sw = STEM
    r = (aw - sw) / 2
    xl, xr = ax + sw / 2, ax + aw - sw / 2
    yc = y2 - CAP + sw / 2 + r
    bar = y2 - 0.36 * CAP
    a_path = f'M{xl:.1f},{y2 - sw / 2:.1f} L{xl:.1f},{yc:.1f} A{r:.1f},{r:.1f} 0 0 1 {xr:.1f},{yc:.1f} L{xr:.1f},{y2 - sw / 2:.1f} M{xl:.1f},{bar:.1f} L{xr:.1f},{bar:.1f}'
    rest_x = ax + aw + 0.075 * F + TRACK
    return (
        f'<text x="{x0:.1f}" y="{y1:.1f}" {style} {stroke}>Smoked</text>'
        f'<path d="{a_path}" fill="none" stroke="{color}" stroke-width="{sw + 2 * halo:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<text x="{rest_x:.1f}" y="{y2:.1f}" {style} {stroke}>lmonds</text>'
    )


# ----------------------------------------------------------------- lid top


def lid_top(pile, mask=False):
    ink = '#ffffff' if mask else BRONZE
    bg = '#000000' if mask else BLACK
    defs, body = pile_svg(pile, ink, bg)
    tx, ty = C + TITLE_CENTRE[0] * U, C + TITLE_CENTRE[1] * U
    vx, vy = C + VEG[0] * U, C + VEG[1] * U
    veg = (
        f'<g transform="rotate({-TITLE_ANGLE} {vx:.1f} {vy:.1f})">'
        f'<rect x="{vx - VEG_SIZE / 2 - HALO * 2:.1f}" y="{vy - VEG_SIZE / 2 - HALO * 2:.1f}" width="{VEG_SIZE + HALO * 4:.1f}" height="{VEG_SIZE + HALO * 4:.1f}" fill="{bg}"/>'
        + ('' if mask else veg_mark(vx - VEG_SIZE / 2, vy - VEG_SIZE / 2, VEG_SIZE))
        + '</g>'
    )
    return svg(
        S,
        S,
        f'<defs><clipPath id="field"><circle cx="{C}" cy="{C}" r="{dims.ART_R * U:.1f}"/></clipPath>{"".join(defs)}</defs>'
        f'<rect width="{S}" height="{S}" fill="{bg}"/>'
        f'<g clip-path="url(#field)">{"".join(body)}</g>'
        f'<circle cx="{C}" cy="{C}" r="{dims.RING_R * U:.1f}" fill="none" stroke="{ink}" stroke-width="3"/>'
        f'<g transform="translate({tx:.1f},{ty:.1f}) rotate({-TITLE_ANGLE})">{title_svg(bg, HALO)}</g>'
        + veg,
        px=4096,
    )


if __name__ == '__main__':
    out = os.path.join(HERE, 'art')
    os.makedirs(out, exist_ok=True)
    pile = build_pile()
    open(os.path.join(out, 'lid-top.svg'), 'w').write(lid_top(pile))
    open(os.path.join(out, 'lid-ink.svg'), 'w').write(lid_top(pile, mask=True))
    print(f'art written: {len(pile)} almonds')
