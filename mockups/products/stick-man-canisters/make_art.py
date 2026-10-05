"""Stick Man canister labels, laid out on the label's real size (1 unit = 0.1 mm).
Run: python3 products/stick-man-canisters/make_art.py && node tools/raster.mjs products/stick-man-canisters/art

One wrap strip per can (label-<colour>.svg): u = 0 at the back, where the
label's ends overlap, running counter-clockwise seen from above, so the front
centre is the middle of the strip and the strip reads left to right across the
front (see dims.py). Everything is drawn three times, shifted by one
circumference, so anything crossing the back seam stays continuous.

The label, as in the spread: a parade of stick men built from mustard potato
sticks marches round the top of each can, and gets eaten from can to can
(whole on the brown, losing arms and legs on the pink, a head and a last crumb
on the navy). A title panel carries the dotted IndiGo plane, 'Stick Man' in
Comfortaa, the flavour, the veg mark and the Stick Man rhyme; ingredients run
round the foot, and a nutrition panel is set sideways.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)

from brand.indigo import FONT, plane_svg, svg, veg_mark  # noqa: E402

import dims  # noqa: E402

U = 100  # units per cm
L = dims.CIRC * U
HS = dims.ART_H * U

POEM = [
    # As printed: no commas, every line capitalised but the second.
    'Stick man stick man',
    'marching side by side',
    'Stick man stick man',
    'Got nowhere to hide',
    'Eat his left arm',
    'And the right one too',
    'When he comes to his senses',
    "He won’t know what to do",
    "He’ll run and run",
    "But there’s no place to flee",
    'Gobble up his left leg',
    'And lick your lips with glee',
]

INGREDIENTS = {
    'brown': [
        'Ingredients: Potatoes (86%), Edible Vegetable Oil, Tomato Powder (1.4%), Sugar, Iodised Salt, Spices and Condiments, Acidity Regulator (330)',
        'and Antioxidant (319). CONTAINS ADDED FLAVOURS – NATURAL AND NATURE IDENTICAL FLAVOURING SUBSTANCES. Contains sulphites.',
        'Made in India. Exclusively produced for IndiGo. For complaints and feedback, write to us at goIndiGo.in',
    ],
    'pink': [
        'Ingredients: Potatoes (85%), Edible Vegetable Oil, Masala Seasoning (5%) [Spices and Condiments, Sugar, Onion and Garlic Powder], Edible Common Salt, Acidity Regulator (330)',
        'and Antioxidant (319). CONTAINS ADDED FLAVOURS – NATURAL AND NATURE IDENTICAL FLAVOURING SUBSTANCES. Contains sulphites. Made in India.',
        'Exclusively produced for IndiGo. For complaints and feedback, write to us at goIndiGo.in',
    ],
    'navy': [
        'Ingredients: Potatoes (88%), Edible Vegetable Oil, Iodised Salt and Antioxidant (319).',
        'Contains sulphites. Made in India. Exclusively produced for IndiGo.',
        'For complaints and feedback, write to us at goIndiGo.in',
    ],
}

NUTRITION = {
    # energy kcal, fat g, cholesterol mg, carbohydrate g, of which sugar g, protein g, fibre g
    'brown': ('541', '33.8', '0', '52.6', '2.1', '6.4', '4.2'),
    'pink': ('538', '33.2', '0', '52.9', '1.8', '6.6', '4.5'),
    'navy': ('543', '34.5', '0', '50.2', '0.5', '6.8', '4.4'),
}
NUTRI_ROWS = ('Energy (kcal)', 'Total Fat (g)', 'Cholesterol (mg)', 'Total Carbohydrate (g)', 'of which Sugars (g)', 'Protein (g)', 'Dietary Fibre (g)')


def f(v):
    return f'{v:.1f}'


def stick(cx, cy, length, angle, w=dims.STICK_W * U, colour=dims.STICK_COLOUR):
    """A potato stick: a cut bar with softened corners (not a capsule, as in
    the print) centred on (cx, cy), tilted `angle` degrees from vertical with
    its lower end out to the right for +angle."""
    return (
        f'<rect x="{f(cx - w / 2)}" y="{f(cy - length / 2)}" width="{f(w)}" height="{f(length)}" rx="{f(w * dims.STICK_ROUND)}" '
        f'fill="{colour}" transform="rotate({-angle:.2f} {f(cx)} {f(cy)})"/>'
    )


def figure(th, parts):
    cx, cy = dims.x_of(th) * U, dims.y_of(dims.FIG_D) * U
    out = []
    for name in parts:
        x, y, length, ang = dims.FIGURE[name]
        out.append(stick(cx + x * U, cy + y * U, length * U, ang))
    return ''.join(out)


def crumb(th):
    c = dims.CRUMB * U
    cx, cy = dims.x_of(th) * U, dims.y_of(dims.CRUMB_D) * U
    return f'<rect x="{f(cx - c / 2)}" y="{f(cy - c / 2)}" width="{f(c)}" height="{f(c * 0.92)}" rx="{f(c * 0.4)}" fill="{dims.STICK_COLOUR}" transform="rotate(12 {f(cx)} {f(cy)})"/>'


def text(x, y, size, body, colour, weight=500, anchor='start', spacing=0.0):
    ls = f' letter-spacing="{spacing:.2f}"' if spacing else ''
    return (
        f'<text x="{f(x)}" y="{f(y)}" font-family="{FONT}" font-weight="{weight}" font-size="{f(size)}" '
        f'fill="{colour}" text-anchor="{anchor}"{ls}>{body}</text>'
    )


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def title_panel(can, c):
    x0 = dims.x_of(c['panel']) * U
    tw = (dims.TITLE_EM * dims.TITLE_SIZE + 8 * dims.TITLE_SPACING) * U
    out = [plane_svg(x0 + tw / 2, dims.y_of(dims.PLANE_D) * U, dims.PLANE_W * U, color=c['plane'], dot=0.25)]
    out.append(text(x0, dims.y_of(dims.TITLE_D) * U, dims.TITLE_SIZE * U, 'Stick Man', c['title'], weight=500, spacing=dims.TITLE_SPACING * U))
    sub = f'Potato Sticks {c["flavour"]}'
    out.append(text(x0, dims.y_of(dims.SUB_D) * U, dims.SUB_SIZE * U, sub, c['sub'], weight=500))
    vx = x0 + (dims.SUB_EM[can] * dims.SUB_SIZE + 0.16) * U
    out.append(veg_mark(round(vx, 1), round(dims.y_of(dims.SUB_D - 0.345) * U, 1), round(dims.VEG * U, 1)))
    for i, line in enumerate(POEM):
        out.append(text(x0, dims.y_of(dims.POEM_D + i * dims.POEM_LEAD) * U, dims.POEM_SIZE * U, esc(line), c['poem'], weight=500))
    return ''.join(out)


def ingredients(can, c):
    x0 = dims.x_of(c['ingr'][0]) * U
    return ''.join(
        text(x0, dims.y_of(d) * U, dims.INGR_SIZE * U, esc(line), c['small'], weight=500)
        for d, line in zip(dims.INGR_D, INGREDIENTS[can])
    )


def recycle(cx, cy, r, colour, sw):
    """Three chasing arrows round a circle, the plain recycling mark."""
    out = []
    for k in range(3):
        a0 = math.radians(k * 120 - 90 + 18)
        a1 = math.radians(k * 120 - 90 + 92)
        p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0))
        p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
        out.append(f'<path d="M{f(p0[0])} {f(p0[1])} A{f(r)} {f(r)} 0 0 1 {f(p1[0])} {f(p1[1])}" fill="none" stroke="{colour}" stroke-width="{f(sw)}" stroke-linecap="round"/>')
        # Arrowhead at the arc's end, pointing along it (clockwise).
        t = (-math.sin(a1), math.cos(a1))
        n = (math.cos(a1), math.sin(a1))
        hl, hw = sw * 2.4, sw * 1.9
        tip = (p1[0] + t[0] * hl, p1[1] + t[1] * hl)
        b1 = (p1[0] + n[0] * hw, p1[1] + n[1] * hw)
        b2 = (p1[0] - n[0] * hw, p1[1] - n[1] * hw)
        out.append(f'<path d="M{f(tip[0])} {f(tip[1])} L{f(b1[0])} {f(b1[1])} L{f(b2[0])} {f(b2[1])} Z" fill="{colour}"/>')
    return ''.join(out)


def nutrition(can, c):
    """The sideways panel, drawn in its own reading frame (x along the lines,
    y down across them, in cm), then turned to read from the foot upwards."""
    col = c['small']
    fs = dims.NUTRI_SIZE * U
    p = dims.NUTRI_LEAD * U
    Wb, Hb, split = dims.NUTRI_W * U, dims.NUTRI_H * U, dims.NUTRI_SPLIT * U
    out = []
    out.append(text(0, 0.22 * U, fs, 'NUTRITIONAL FACTS', col, weight=700, spacing=0.4))
    out.append(text(0, 0.22 * U + p, fs, f'Stick Man {c["flavour"]} Potato Sticks', col))
    out.append(text(0, 0.22 * U + 2 * p, fs, 'Values per 100 g (approx.)', col))
    y = 1.10 * U
    for label, val in zip(NUTRI_ROWS, NUTRITION[can]):
        out.append(text(0, y, fs, label, col))
        out.append(text(split - 0.12 * U, y, fs, val, col, anchor='end'))
        y += p
    out.append(f'<line x1="{f(split)}" y1="{f(0.05 * U)}" x2="{f(split)}" y2="{f(Hb - 0.05 * U)}" stroke="{col}" stroke-width="{f(0.014 * U)}"/>')
    x2 = split + 0.18 * U
    lines = [
        (0.22, 'Net weight: 50 g'),
        (0.22 + 0.25, 'MRP: Rs. 50.00'),
        (0.22 + 0.50, '(incl. of all taxes)'),
        (1.10, 'Best before 6 months from'),
        (1.10 + 0.25, 'the date of manufacture.'),
        (1.10 + 0.50, 'Store in a cool, dry place.'),
        (2.35, 'Exclusively produced'),
        (2.60, 'for IndiGo.'),
    ]
    for yy, s in lines:
        out.append(text(x2, yy * U, fs, s, col))
    out.append(recycle(Wb - 0.2 * U, 1.40 * U, 0.13 * U, col, 0.028 * U))
    x0 = dims.x_of(c['nutri']) * U
    y0 = dims.y_of(dims.NUTRI_D) * U
    return f'<g transform="translate({f(x0)} {f(y0)}) rotate(-90)">{"".join(out)}</g>'


def label(can):
    c = dims.CANS[can]
    parts = [figure(th, pp) for th, pp in c['figures']]
    parts += [crumb(th) for th in c['crumbs']]
    parts.append(title_panel(can, c))
    parts.append(ingredients(can, c))
    parts.append(nutrition(can, c))
    body = (
        f'<defs><g id="label">{"".join(parts)}</g></defs>'
        f'<rect width="{f(L)}" height="{f(HS)}" fill="{c["paper"]}"/>'
        f'<use href="#label" x="{f(-L)}"/><use href="#label"/><use href="#label" x="{f(L)}"/>'
    )
    return svg(L, HS, body, px=8192)


def lid(can):
    """The peel-off foil seen from above, front edge at the bottom: bare
    silver foil with the heat-seal ring pressed round its edge, and the
    plane and 'Stick Man' printed in the can's colour."""
    c = dims.CANS[can]
    D = 2 * dims.FOIL_R * U
    cx = cy = D / 2
    ink = c['paper']
    out = [f'<rect width="{f(D)}" height="{f(D)}" fill="{dims.FOIL_SILVER}"/>']
    # Seal ring: fine pressed rings where the foil is sealed onto the flange.
    for i in range(7):
        r = (dims.APERTURE_R + 0.035 + i * 0.034) * U
        out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="none" stroke="#c3c4c8" stroke-width="{f(0.008 * U)}"/>')
    out.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(dims.APERTURE_R * U)}" fill="none" stroke="#c9cacd" stroke-width="{f(0.02 * U)}"/>')
    out.append(plane_svg(cx, cy + dims.LID_PLANE_CY * U, dims.LID_PLANE_W * U, color=ink, dot=0.27))
    out.append(text(cx, cy + dims.LID_TITLE_Y * U, dims.LID_TITLE_SIZE * U, 'Stick Man', ink, weight=600, anchor='middle', spacing=-0.4))
    out.append(text(cx, cy + (dims.LID_TITLE_Y + 0.42) * U, 0.2 * U, f'Potato Sticks {c["flavour"]}', ink, weight=600, anchor='middle'))
    return svg(D, D, ''.join(out), px=4096)


def main():
    out = os.path.join(HERE, 'art')
    os.makedirs(out, exist_ok=True)
    for can in dims.CANS:
        with open(os.path.join(out, f'label-{can}.svg'), 'w', encoding='utf-8') as fh:
            fh.write(label(can))
        with open(os.path.join(out, f'lid-{can}.svg'), 'w', encoding='utf-8') as fh:
            fh.write(lid(can))
    print('art written')


if __name__ == '__main__':
    main()
