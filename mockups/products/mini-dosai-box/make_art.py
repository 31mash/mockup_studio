"""Mini Dosai sleeve artwork, laid out on the sleeve's real dimensions
(1 unit = 0.1 mm), one wrap strip per variant (see dims.sleeve_layout).
Run: python3 products/mini-dosai-box/make_art.py && node tools/raster.mjs products/mini-dosai-box/art"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..'))

from brand.indigo import FONT, nonveg_mark, plane_svg, svg, veg_mark  # noqa: E402

import dims  # noqa: E402
from engravings import hen, potato_plant  # noqa: E402

U = 100  # units per cm
W, L = dims.W * U, dims.L * U
LAY = dims.sleeve_layout()
STRIP = LAY['length'] * U

CREAM = '#f4f1e3'
SLAB = 'Bevan'
TAMIL = 'Noto Serif Tamil'
BADGE = '#d3c43b'
BADGE_INK = '#3a2e1c'
INK = '#221d1a'

VARIANTS = {
    'chicken': dict(
        ink='#961d24',
        badge=(618, 484),
        badge_text=['Chicken', 'kurma and', 'coconut', 'chutney'],
        name='Chicken',
        mark=nonveg_mark,
        blurb='Crisp mini dosai, folded around a spiced chicken kurma.',
    ),
    'veg': dict(
        ink='#2a6236',
        badge=(228, 505),
        badge_text=['Aloo', 'podimas and', 'coconut', 'chutney'],
        name='Vegetarian',
        mark=veg_mark,
        blurb='Crisp mini dosai, folded around a potato podimas.',
    ),
}


def ticket_frame(x0, y0, x1, y1, rn, step, color, width):
    """A rectangle with concave (ticket) corners and a small step into each notch."""
    ra = math.hypot(rn, step)
    d = (
        f'M{x0 + rn},{y0 - 0} L{x1 - rn},{y0} L{x1 - rn},{y0 + step} '
        f'A{ra:.2f},{ra:.2f} 0 0 0 {x1 - step},{y0 + rn} L{x1},{y0 + rn} '
        f'L{x1},{y1 - rn} L{x1 - step},{y1 - rn} '
        f'A{ra:.2f},{ra:.2f} 0 0 0 {x1 - rn},{y1 - step} L{x1 - rn},{y1} '
        f'L{x0 + rn},{y1} L{x0 + rn},{y1 - step} '
        f'A{ra:.2f},{ra:.2f} 0 0 0 {x0 + step},{y1 - rn} L{x0},{y1 - rn} '
        f'L{x0},{y0 + rn} L{x0 + step},{y0 + rn} '
        f'A{ra:.2f},{ra:.2f} 0 0 0 {x0 + rn},{y0 + step} Z'
    )
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="miter"/>'


def outlined_word(text, cx, baseline, size, sx, ink, gap, ring, family=SLAB, spacing=0):
    """Slab lettering with a hairline outline following the letters at a gap,
    like the sleeve's DOSAI: ink ring, cream gap, ink letters."""
    t = (
        f'font-family="{family}" font-size="{size}" text-anchor="middle" letter-spacing="{spacing}" '
        f'x="0" y="0"'
    )
    g = f'<g transform="translate({cx},{baseline}) scale({sx},1)">'
    g += f'<text {t} fill="{ink}" stroke="{ink}" stroke-width="{2 * (gap + ring)}" stroke-linejoin="round">{text}</text>'
    g += f'<text {t} fill="{CREAM}" stroke="{CREAM}" stroke-width="{2 * gap}" stroke-linejoin="round">{text}</text>'
    g += f'<text {t} fill="{ink}">{text}</text>'
    return g + '</g>'


def seal(cx, cy, r, color, teeth=64, depth=2.2):
    pts = []
    for i in range(teeth * 2):
        a = math.pi * i / teeth
        rr = r if i % 2 == 0 else r - depth
        pts.append(f'{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}')
    return f'<polygon points="{" ".join(pts)}" fill="{color}"/>'


def front(v):
    """The printed face (top of the sleeve), W x L, back end at the top."""
    ink = v['ink']
    cx = W / 2
    out = [ticket_frame(54, 64, W - 54, L - 54, 50, 6, ink, 5)]
    out.append(f'<text x="{cx}" y="152" font-family="{SLAB}" font-size="82" text-anchor="middle" fill="{ink}">MINI</text>')
    out.append(outlined_word('DOSAI', cx, 322, 150, 1.1, ink, gap=9, ring=4.5))
    # Oval vignette: heavy outer rule, hairline inside.
    ox, oy = cx, 716
    out.append(f'<ellipse cx="{ox}" cy="{oy}" rx="235" ry="311" fill="none" stroke="{ink}" stroke-width="10"/>')
    out.append(f'<ellipse cx="{ox}" cy="{oy}" rx="217" ry="293" fill="none" stroke="{ink}" stroke-width="3.5"/>')
    if v is VARIANTS['chicken']:
        out.append(hen(272, 568, 0.985))
    else:
        out.append(potato_plant(318, 452, 1.0))
    # Tamil name.
    out.append(
        f'<text transform="translate({cx},1158) scale(0.86,1)" x="0" y="0" font-family="{TAMIL}" font-weight="800" '
        f'font-size="126" text-anchor="middle" fill="{ink}">தோசை</text>'
    )
    # Yellow seal with the filling, overlapping the oval.
    bx, by = v['badge']
    out.append(seal(bx, by, 84, BADGE))
    lines = v['badge_text']
    lh = 19
    y0 = by - (len(lines) - 1) * lh / 2 + 5
    for i, s in enumerate(lines):
        out.append(
            f'<text x="{bx}" y="{y0 + i * lh:.1f}" font-family="Libre Baskerville" font-style="italic" font-size="17" '
            f'text-anchor="middle" fill="{BADGE_INK}">{s}</text>'
        )
    return ''.join(out)


def side_left(v, w, h):
    """Left side panel, drawn upright as seen from outside: w along the
    sleeve (front end at the right), h across (the panel's height)."""
    ink = v['ink']
    out = [ticket_frame(34, 34, w - 34, h - 34, 26, 4, ink, 4)]
    out.append(f'<text x="{w * 0.5}" y="{h * 0.5 + 34}" font-family="{SLAB}" font-size="100" text-anchor="middle" fill="{ink}" letter-spacing="4">MINI DOSAI</text>')
    out.append(f'<text x="{w * 0.5}" y="{h * 0.5 + 92}" font-family="Libre Baskerville" font-style="italic" font-size="30" text-anchor="middle" fill="{ink}">{v["name"]}</text>')
    out.append(v['mark'](w - 150, h / 2 - 32, 64))
    out.append(plane_svg(150, h / 2, 110, color=ink, dot=0.32))
    return ''.join(out)


def side_right(v, w, h):
    """Right side panel, upright seen from outside (front end at the left)."""
    ink = v['ink']
    out = [ticket_frame(34, 34, w - 34, h - 34, 26, 4, ink, 4)]
    out.append(f'<text x="{w * 0.5}" y="{h * 0.5 + 12}" font-family="{TAMIL}" font-weight="800" font-size="92" text-anchor="middle" fill="{ink}">மினி தோசை</text>')
    out.append(f'<text x="{w * 0.5}" y="{h * 0.5 + 76}" font-family="Libre Baskerville" font-size="25" text-anchor="middle" fill="{ink}" letter-spacing="3">SERVED FRESH ON BOARD</text>')
    out.append(f'<text x="150" y="{h * 0.5 + 22}" font-family="{FONT}" font-weight="700" font-size="58" text-anchor="middle" fill="{ink}">IndiGo</text>')
    out.append(f'<text x="{w - 150}" y="{h * 0.5 - 6}" font-family="Libre Baskerville" font-size="24" text-anchor="middle" fill="{ink}">Net wt.</text>')
    out.append(f'<text x="{w - 150}" y="{h * 0.5 + 30}" font-family="Libre Baskerville" font-weight="700" font-size="30" text-anchor="middle" fill="{ink}">120 g</text>')
    return ''.join(out)


def bottom(v, w, h):
    """Bottom panel, upright seen from below with the back end at the top."""
    ink = v['ink']
    cx = w / 2
    out = [ticket_frame(54, 64, w - 54, h - 54, 50, 6, ink, 5)]
    out.append(f'<text x="{cx}" y="190" font-family="{SLAB}" font-size="62" text-anchor="middle" fill="{ink}">MINI DOSAI</text>')
    out.append(f'<text x="{cx}" y="250" font-family="Libre Baskerville" font-style="italic" font-size="28" text-anchor="middle" fill="{ink}">{v["blurb"]}</text>')
    rows = [
        ('Ingredients', 'Rice, black gram, filling, curry leaves, oil, salt, spices.'),
        ('Storage', 'Keep chilled. Heat on board and serve warm.'),
        ('Allergens', 'Contains mustard. Made in a kitchen that handles nuts.'),
    ]
    y = 360
    for k, t in rows:
        out.append(f'<text x="120" y="{y}" font-family="Libre Baskerville" font-weight="700" font-size="24" fill="{ink}">{k}</text>')
        out.append(f'<text x="120" y="{y + 36}" font-family="Libre Baskerville" font-size="22" fill="{INK}">{t}</text>')
        y += 110
    # Nutrition box.
    out.append(f'<rect x="120" y="{y}" width="{w - 240}" height="300" fill="none" stroke="{ink}" stroke-width="3"/>')
    out.append(f'<text x="140" y="{y + 44}" font-family="Libre Baskerville" font-weight="700" font-size="24" fill="{ink}">Nutrition, per 100 g</text>')
    facts = [('Energy', '212 kcal'), ('Protein', '6.1 g'), ('Carbohydrate', '28.4 g'), ('Fat', '8.2 g'), ('Sodium', '390 mg')]
    for i, (k, t) in enumerate(facts):
        yy = y + 96 + i * 42
        out.append(f'<text x="140" y="{yy}" font-family="Libre Baskerville" font-size="22" fill="{INK}">{k}</text>')
        out.append(f'<text x="{w - 140}" y="{yy}" font-family="Libre Baskerville" font-size="22" text-anchor="end" fill="{INK}">{t}</text>')
    out.append(v['mark'](cx - 40, L - 330, 80))
    out.append(plane_svg(cx, L - 170, 120, color=ink, dot=0.32))
    return ''.join(out)


def strip(v):
    """The whole sleeve print as one wrap strip (see dims.sleeve_layout)."""
    fb = LAY['bottom_a'][1] * U
    lh = (LAY['left'][1] - LAY['left'][0]) * U
    out = [f'<rect width="{STRIP:.0f}" height="{L:.0f}" fill="{CREAM}"/>']
    # Top: centred on the top panel, full sleeve width.
    tc = (LAY['top'][0] + LAY['top'][1]) / 2 * U
    out.append(f'<g transform="translate({tc - W / 2:.1f},0)">{front(v)}</g>')
    # Left side: panel spans u (bottom -> top), v along the sleeve. Drawn
    # upright (L wide, h high) then turned so reading runs towards the front.
    pl0 = LAY['left'][0] * U - dims.R * U * 0.3
    hh = dims.H * U
    out.append(
        f'<g transform="translate({pl0 + (lh + dims.R * U * 0.6) / 2:.1f},{L / 2:.1f}) rotate(90) translate({-L / 2:.1f},{-hh / 2:.1f})">'
        f'{side_left(v, L, hh)}</g>'
    )
    pr0 = LAY['right'][0] * U - dims.R * U * 0.3
    out.append(
        f'<g transform="translate({pr0 + (lh + dims.R * U * 0.6) / 2:.1f},{L / 2:.1f}) rotate(-90) translate({-L / 2:.1f},{-hh / 2:.1f})">'
        f'{side_right(v, L, hh)}</g>'
    )
    # Bottom: centred on the strip's start (and again at its end).
    for c in (0.0, STRIP):
        out.append(f'<g transform="translate({c - W / 2:.1f},0)">{bottom(v, W, L)}</g>')
    return ''.join(out)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    for name, v in VARIANTS.items():
        open(os.path.join(HERE, 'art', f'sleeve-{name}.svg'), 'w').write(svg(STRIP, L, strip(v), px=6144))
        # A flat proof of the printed face alone, for checking the artwork.
        open(os.path.join(HERE, 'art', f'_proof-{name}.svg'), 'w').write(
            svg(W, L, f'<rect width="{W}" height="{L}" fill="{CREAM}"/>' + front(v), px=1700)
        )
    print('art written')
