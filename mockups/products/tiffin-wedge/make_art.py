"""Tiffin sandwich wedge artwork, laid out on the carton's real surfaces (1 unit = 0.1 mm).
Run: python3 products/tiffin-wedge/make_art.py && node tools/raster.mjs products/tiffin-wedge/art

Files (one set per colourway, 'love-story' and 'big-don'):
- tube-<variant>.svg: one wrap strip around the base, back and front panels.
  u (left to right) runs along the cross-section from the seam in the middle
  of the base, up the back, down the front; v (bottom to top) runs along X
  (bottom edge = the -X end). Each panel is drawn upright in its own group and
  turned into the strip.
- end-<variant>-l.svg / -r.svg: the triangle ends, seen from outside, upright,
  over the whole L x L square (right angle at bottom-left on the -X end and at
  bottom-right on the +X end).
- sandwich.png: the cut face of the sandwich behind the window, written
  directly (no SVG): the window of the original pack in
  source/crops/tiffin-wedge-front.png, rectified to the window's real size
  and lightly colour-corrected. Reproducible from the crop.
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)

from brand.indigo import FONT, svg, veg_mark  # noqa: E402

import dims  # noqa: E402

U = 100  # units per cm
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
ART = os.path.join(HERE, 'art')
os.makedirs(ART, exist_ok=True)

# Print colours: sampled from the spread, then cleaned up (the photo is dull
# and warm; the inks are flat and a little brighter).
BLUE = '#264d98'  # IndiGo band (a cobalt blue, not the tins' violet indigo)
LIME = '#95bd43'  # Soul-itude end and the window's green strip
AMBER = '#eea437'  # the window's right-hand strip
ORANGE = '#e9692e'  # Tiffin band, Love Story back, Aero-bics end
LEAF = '#5bab5a'  # Big Don back
INK = '#fffcf3'  # white ink on the coloured board

# Each pack carries both exercise panels, one per end, and the end next to
# the back contrasts with it: the spread shows Love Story's -X end green
# (Soul-itude, its slope edge showing the green strip) and, in the front shot,
# an orange sliver of its +X end widening towards the base; Big Don's -X end
# is the orange Aero-bics.
VARIANTS = {
    'love-story': dict(back=ORANGE, band=ORANGE, left=LIME, right=AMBER, base=ORANGE, ends={'l': 'soulitude', 'r': 'aerobics'}, story='love'),
    'big-don': dict(back=LEAF, band=LEAF, left=ORANGE, right=AMBER, base=LEAF, ends={'l': 'aerobics', 'r': 'soulitude'}, story='don'),
}
END_COLOUR = {'soulitude': LIME, 'aerobics': ORANGE}

# Comfortaa advance widths in em (weight 400), measured in Chromium.
ADV = {'ro-bics': 3.63, 'Soul-itud': 4.77}
STEM = 0.076  # Comfortaa 400 stem, em


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def text(x, y, s, size, fill=INK, weight=400, anchor='start', extra=''):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-weight="{weight}" font-size="{size:.1f}" '
        f'fill="{fill}" text-anchor="{anchor}" {extra}>{esc(s)}</text>'
    )


# ----------------------------------------------------------------- IndiGo glyphs
# IndiGo's lettering has an arch-shaped A and an e with a diagonal bar;
# Comfortaa has neither, so the titles draw those two as monoline strokes.


def glyph_A(x, base, F, fill):
    sw = STEM * F
    l = x + 0.08 * F + sw / 2
    r = x + 0.62 * F - sw / 2
    top = base - 0.782 * F + sw / 2
    rad = 0.25 * F
    bar = base - 0.36 * F
    d = (
        f'M{l:.1f},{base:.1f} L{l:.1f},{top + rad:.1f} A{rad:.1f},{rad:.1f} 0 0 1 {l + rad:.1f},{top:.1f} '
        f'L{r - rad:.1f},{top:.1f} A{rad:.1f},{rad:.1f} 0 0 1 {r:.1f},{top + rad:.1f} L{r:.1f},{base:.1f} '
        f'M{l:.1f},{bar:.1f} L{r:.1f},{bar:.1f}'
    )
    return f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round"/>', 0.70 * F


def glyph_e(x, base, F, fill):
    sw = STEM * F
    cx, cy = x + 0.3125 * F, base - 0.2815 * F
    rx, ry = 0.2265 * F, 0.2415 * F
    a1, a2 = math.radians(22), math.radians(-42)  # arc start (upper right) and end (lower right)

    def pt(a):
        return cx + rx * math.cos(a), cy - ry * math.sin(a)

    s, e = pt(a1), pt(a2)
    b = pt(a1 + math.pi)
    d = (
        f'M{s[0]:.1f},{s[1]:.1f} A{rx:.1f},{ry:.1f} 0 1 0 {e[0]:.1f},{e[1]:.1f} '
        f'M{b[0]:.1f},{b[1]:.1f} L{s[0]:.1f},{s[1]:.1f}'
    )
    return f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round"/>', 0.61 * F


def title(parts, x, base, F, fill=INK, anchor='start'):
    """A title line from Comfortaa runs and IndiGo glyphs ('A', 'e')."""
    width = sum(0.70 * F if p == 'A' else 0.61 * F if p == 'e' else ADV[p] * F for p in parts)
    cx = x - width if anchor == 'end' else x
    out = []
    for p in parts:
        if p == 'A':
            g, adv = glyph_A(cx, base, F, fill)
        elif p == 'e':
            g, adv = glyph_e(cx, base, F, fill)
        else:
            g, adv = text(cx, base, p, F, fill), ADV[p] * F
        out.append(g)
        cx += adv
    return ''.join(out), width


# ----------------------------------------------------------------- front panel

FW = dims.W * U
FL = dims.FRONT_LEN * U


def front_panel(v):
    blue = dims.BLUE_BAND * U
    low = FL - dims.ORANGE_BAND * U
    out = [
        f'<rect x="-40" y="-40" width="{FW / 2 + 40}" height="{FL + 80}" fill="{v["left"]}"/>',
        f'<rect x="{FW / 2}" y="-40" width="{FW / 2 + 40}" height="{FL + 80}" fill="{v["right"]}"/>',
        f'<rect x="-40" y="-40" width="{FW + 80}" height="{blue + 40}" fill="{BLUE}"/>',
        f'<rect x="-40" y="{low}" width="{FW + 80}" height="{FL - low + 40}" fill="{v["band"]}"/>',
    ]
    # IndiGo wordmark, measured on the rectified front photo: upright, about
    # 5.6 cm wide with a 1.38 cm cap height (IndiGo's lettering runs a little
    # narrower than Comfortaa, so the run is fitted to its measured width),
    # its baseline 2.75 cm below the apex fold; a small (R) by the o's shoulder.
    F, wm = 176, 560
    base = 275
    out.append(
        f'<text x="{FW / 2 - 8:.1f}" y="{base}" font-family="{FONT}" font-weight="600" font-size="{F}" fill="{INK}" '
        f'text-anchor="middle" textLength="{wm}" lengthAdjust="spacingAndGlyphs">IndiGo</text>'
    )
    out.append(text(FW / 2 - 8 + wm / 2 + 6, base - 0.53 * F + 6, '\u00ae', 24, INK, 400))
    # Tiffin: upright, bold and only slightly narrow (4.4 cm wide, 1.5 cm
    # cap height), sitting low in the bottom band.
    F, wt = 195, 452
    base = low + 0.745 * dims.ORANGE_BAND * U
    out.append(
        f'<text x="{FW / 2:.1f}" y="{base:.1f}" font-family="{FONT}" font-weight="700" font-size="{F}" fill="{INK}" '
        f'text-anchor="middle" textLength="{wt}" lengthAdjust="spacingAndGlyphs">Tiffin</text>'
    )
    return ''.join(out)


# ----------------------------------------------------------------- back panel

BL = dims.BACK_LEN * U

STORIES = {
    'love': (
        'The Ultimate Love Story',
        [
            'Meet Romeo, the bad-boy rebel and Sally, the poor, rich girl. They meet on a huge ship and '
            'instantly fall in love. Their love blossoms as they exchange secret love letters through '
            'pigeons and dance and sing around trees. But fate has a different plan. A war breaks out and '
            'separates them.',
            'The next time they meet, Sally is betrothed to an oil tycoon and bumps into Romeo, who is a '
            'dance instructor in Casablanca. They try to be friends but tempers flare between the two of '
            'them. So, they part again.',
            'One year later, Romeo is on the top of the Empire State Building when he sees a glass slipper '
            'on the floor. As he picks it up, he sees Sally standing in front of him and notices that she is '
            'missing a shoe and without a fiancé. They both realize that they still love each other. '
            'Reunited, the lovers ride off into the sunset.',
        ],
        40.5,
        25.5,
    ),
    'don': (
        'Big Don',
        [
            'Anthony Baba is the Big Don in Mumbai. His kids are Sunny, Chinky, Mintu, Honey and Tushar, '
            'a surrogate son. Mintu rejects the family business to become an honest IPS officer.',
            'Things get messy after a deal with Robert, a gun dealer, goes bad. Baba is shot, a gang-war '
            "erupts, Baba’s life is threatened again and Mintu murders Robert and Inspector Ramesh, a "
            'corrupt police officer.',
            'Mintu hides in a village, falls in love and marries a local girl, who gets bumped off by '
            "Baba’s enemies.",
            "Meanwhile, Sunny’s life is cut short and Baba makes peace with the other rival gangs. Then "
            'Baba dies in his sleep. Mintu comes back, remarries, takes care of some unfinished business '
            'and becomes the new Big Don. Khallas!',
        ],
        43.5,
        26.5,
    ),
}


def back_panel(v):
    """Positions measured on the two back photos (cm from the apex fold):
    'Easy to digest' on 1.4, 'stories' on 2.2, rules at 2.5 and 3.48 around
    the story's title, the story from 4.05 down to about 11.6."""
    name, paras, lead, size = STORIES[v['story']]
    m = 28
    out = [f'<rect x="-40" y="-40" width="{FW + 80}" height="{BL + 80}" fill="{v["back"]}"/>']
    out.append(text(FW / 2, 140, 'Easy to digest', 88, INK, 400, 'middle', 'letter-spacing="-0.5"'))
    out.append(text(FW / 2, 220, 'stories', 62, INK, 400, 'middle'))
    rule = lambda y: f'<rect x="{m}" y="{y - 3}" width="{FW - 2 * m}" height="6" fill="{INK}"/>'  # noqa: E731
    out.append(rule(250))
    out.append(text(FW / 2, 314, name, 46, INK, 400, 'middle'))
    out.append(rule(348))
    body = ''.join(f'<p style="margin:0 0 {lead * 0.22:.1f}px 0">{esc(p)}</p>' for p in paras)
    top = 405 - lead * 0.5 - size * 0.36  # first baseline on 4.05 cm
    out.append(
        f'<foreignObject x="{m + 3}" y="{top:.1f}" width="{FW - 2 * m - 3}" height="{BL - top}">'
        f'<div xmlns="http://www.w3.org/1999/xhtml" style="font-family:{FONT};font-weight:400;font-size:{size}px;'
        f'line-height:{lead}px;color:{INK};letter-spacing:-0.1px">{body}</div></foreignObject>'
    )
    return ''.join(out)


# ----------------------------------------------------------------- base panel

BASE = dims.BASE_LEN * U


def base_panel(v):
    """Underneath: pack information (never in shot, but printed like a real one)."""
    out = [f'<rect x="-40" y="-40" width="{FW + 80}" height="{BASE + 80}" fill="{v["base"]}"/>']
    y0 = 180
    out.append(text(60, y0, 'Tiffin', 70, INK, 700))
    out.append(veg_mark(FW - 60 - 70, y0 - 62, 70))
    lines = [
        'Sweet corn and spinach sandwich on white and',
        'whole wheat bread, with a mint chutney spread.',
        '',
        'Ingredients: bread (wheat flour, whole wheat flour,',
        'yeast, salt, sugar), sweet corn, spinach, cheese,',
        'mint, coriander, green chilli, butter, spices.',
        '',
        'Keep refrigerated. Best consumed on the day of',
        'your flight.',
    ]
    for i, s in enumerate(lines):
        out.append(text(60, y0 + 90 + i * 40, s, 25, INK))
    return ''.join(out)


# ----------------------------------------------------------------- the wrap strip


def tube(vname):
    v = VARIANTS[vname]
    Lp = dims.PERIMETER * U
    H = FW
    ua, ub, uf = dims.U_APEX * U, dims.U_BACK * U, dims.U_FRONT_BOTTOM * U
    parts = []
    # Base: the seam is in its middle; draw it whole on both sides of the strip.
    base_top = uf  # front-bottom fold midline; the base continues to Lp, then from 0
    parts.append(f'<g transform="matrix(0,1,-1,0,{base_top + BASE:.2f},0)">{base_panel(v)}</g>')
    parts.append(f'<g transform="matrix(0,1,-1,0,{base_top + BASE - Lp:.2f},0)">{base_panel(v)}</g>')
    # Back: drawn upright (top = apex), seen from behind; its left is +X.
    parts.append(f'<g transform="matrix(0,1,-1,0,{ua:.2f},0)"><svg x="0" y="0" width="{FW}" height="{BL}" overflow="hidden">{back_panel(v)}</svg></g>')
    # Front: top = apex, left = -X.
    parts.append(f'<g transform="matrix(0,-1,1,0,{ua:.2f},{H})"><svg x="0" y="0" width="{FW}" height="{FL}" overflow="hidden">{front_panel(v)}</svg></g>')
    body = ''.join(parts)
    open(os.path.join(ART, f'tube-{vname}.svg'), 'w').write(svg(Lp, H, body, px=12288))


# ----------------------------------------------------------------- triangle ends

E = dims.L * U  # the end artwork covers the L x L square


def out_stroke(d, bg, w=9.0, inner=3.6, extra=''):
    """IndiGo's pictogram style: limbs drawn as double lines (an ink stroke
    with the board colour down its middle)."""
    return (
        f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'
        f'<path d="{d}" fill="none" stroke="{bg}" stroke-width="{inner}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'
    )


def line(d, w=3.2):
    return f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'


def arrowhead(x, y, ang, s=9):
    a = math.radians(ang)
    p1 = (x + s * math.cos(a + 2.6), y + s * math.sin(a + 2.6))
    p2 = (x + s * math.cos(a - 2.6), y + s * math.sin(a - 2.6))
    return f'<path d="M{p1[0]:.1f},{p1[1]:.1f} L{x:.1f},{y:.1f} L{p2[0]:.1f},{p2[1]:.1f}" fill="none" stroke="{INK}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>'


def meditating(bg):
    """Seated in padmasana, drawn as on the pack: a solid head, a narrow
    torso with the arms flaring from the shoulders down to the hands resting
    on the knees, and two crossed shins drawn as outlined bars.
    Box 0..164 x 0..216 (units)."""
    o = [f'<circle cx="80" cy="22" r="19" fill="{INK}"/>']
    # Shoulders, torso sides and the arms' outer and inner edges.
    o.append(line('M26,58 L126,58 M52,58 L52,146 M108,58 L108,146', 3.4))
    o.append(line('M26,58 L9,158 M52,146 L20,166 M126,58 L151,158 M108,146 L140,166', 3.4))
    # Hands on the knees.
    for cx in (12, 148):
        o.append(f'<circle cx="{cx}" cy="163" r="7" fill="{bg}" stroke="{INK}" stroke-width="3.2"/>')
    # Crossed shins: the right one passes over the left.
    o.append(out_stroke('M20,176 L128,204', bg, 16, 9.2))
    o.append(out_stroke('M140,176 L32,204', bg, 16, 9.2))
    return ''.join(o)


def fig_shoulders(bg):
    """Seated on a chair, rolling the shoulders. Box 0..72 x 0..118."""
    o = [out_stroke('M6,14 L6,116 M6,76 L66,76 L66,116', bg, 7, 2.8)]  # chair
    o.append(f'<circle cx="36" cy="14" r="10" fill="none" stroke="{INK}" stroke-width="3.2"/>')
    o.append(out_stroke('M36,26 L36,72 M22,34 L50,34 M22,34 L20,66 M50,34 L52,66 M36,72 L62,72 L62,112', bg, 7, 2.8))
    o.append(line('M12,36 A10,10 0 0 1 20,24'))
    o.append(arrowhead(20, 24, -40, 6))
    o.append(line('M60,36 A10,10 0 0 0 52,24'))
    o.append(arrowhead(52, 24, 220, 6))
    return ''.join(o)


def fig_arm(bg):
    """Standing, the right arm stretched over the head. Box 0..72 x 0..118."""
    o = [f'<circle cx="34" cy="30" r="10" fill="none" stroke="{INK}" stroke-width="3.2"/>']
    o.append(out_stroke('M34,42 L34,82 L22,116 M34,82 L46,116 M34,50 L22,74', bg, 7, 2.8))
    o.append(out_stroke('M34,50 L50,34 C54,24 46,14 34,12', bg, 7, 2.8))
    o.append(line('M14,16 C22,2 50,2 60,14'))
    o.append(arrowhead(14, 16, 125, 7))
    o.append(arrowhead(60, 14, 50, 7))
    return ''.join(o)


def fig_neck(bg):
    """Standing, hands on hips, turning the head. Box 0..72 x 0..118."""
    o = [f'<circle cx="36" cy="26" r="10" fill="none" stroke="{INK}" stroke-width="3.2"/>']
    o.append(out_stroke('M36,38 L36,82 L24,116 M36,82 L48,116 M36,46 L20,62 L34,76 M36,46 L52,62 L38,76', bg, 7, 2.8))
    o.append(line('M14,20 C14,4 58,4 58,20'))
    o.append(arrowhead(14, 20, 100, 7))
    o.append(arrowhead(58, 20, 80, 7))
    return ''.join(o)


def fig_ankle(bg):
    """Seated, circling the ankle. Box 0..90 x 0..118."""
    o = [out_stroke('M6,20 L6,116 M6,72 L50,72 L50,116', bg, 7, 2.8)]  # chair
    o.append(f'<circle cx="28" cy="16" r="10" fill="none" stroke="{INK}" stroke-width="3.2"/>')
    o.append(out_stroke('M28,28 L28,68 M28,36 L40,58 M28,68 L54,68 L64,100 L74,100', bg, 7, 2.8))
    o.append(f'<ellipse cx="76" cy="98" rx="11" ry="9" fill="none" stroke="{INK}" stroke-width="3"/>')
    o.append(arrowhead(87, 96, 95, 6))
    return ''.join(o)


# The breathing text as set on the pack (line for line, from the photo of the
# Soul-itude end): five lines above the figure, seven beside it, one below.
BREATHE = [
    'Breathe in. Breathe out. Breathe',
    'in. Breathe out. Breathe in. Breathe',
    'out. Breathe in. Breathe out. Breathe',
    'in. Breathe out. Breathe in. Breathe out.',
    'Breathe in. Breathe out. Breathe in. Breathe',
    'out. Breathe in. Breathe out.',
    'Breathe in. Breathe out. Breathe',
    'in. Breathe out. Breathe in. Breathe',
    'out. Breathe in. Breathe out. Breathe',
    'in. Breathe out. Breathe in. Breathe out.',
    'Breathe in. Breathe out. Breathe in. Breathe',
    'out. Breathe in. Breathe out. Breathe in. Breathe',
    'out. Breathe in. Breathe out. Breathe in. Breathe out.',
]


def end_panel(vname, side):
    """side 'l' = the -X end (right angle bottom-left), 'r' = the +X end (mirrored layout).
    Positions are measured on the photos of the two ends (units on the L x L
    square, x from the vertical edge, y down from the apex)."""
    v = VARIANTS[vname]
    exercise = v['ends'][side]
    bg = END_COLOUR[exercise]
    mir = side == 'r'

    def X(x):
        return E - x if mir else x

    anchor = 'end' if mir else 'start'
    o = [f'<rect width="{E}" height="{E}" fill="{bg}"/>']

    def icon(g, x, y, w, sc=1.0):
        # On the +X end the icon keeps its drawing (a raised right arm stays
        # the right arm); only its place is mirrored.
        return f'<g transform="translate({(E - x - w * sc) if mir else x:.1f},{y:.1f}) scale({sc})">{g}</g>'

    def big_title(parts, x, base, F, sx=1.0):
        t, _ = title(parts, X(x), base, F, anchor=anchor)
        ax = X(x)
        return f'<g transform="translate({ax:.1f},{base}) scale({sx},1) translate({-ax:.1f},{-base})">{t}</g>'

    if exercise == 'soulitude':
        for i, s in enumerate(['Here are some', 'breathing exercises', 'to attain peace', 'of mind:']):
            o.append(text(X(62), 352 + i * 36.5, s, 23, anchor=anchor))
        o.append(f'<rect x="{min(X(60), X(390)):.1f}" y="501" width="330" height="3" fill="{INK}"/>')
        for i, s in enumerate(BREATHE):
            x0 = 250 if 5 <= i <= 11 else 62
            o.append(text(X(x0), 561 + 36.9 * i, s, 21.5, anchor=anchor))
        o.append(icon(meditating(bg), 57, 754, 164, 0.97))
        # IndiGo's lettering is a little narrower than Comfortaa's.
        o.append(big_title(['Soul-itud', 'e'], 58, 1184, 158, 0.93))
    else:
        for i, s in enumerate(['Follow', 'these simple', 'stretching exercises to', 'enjoy a relaxed flight:']):
            o.append(text(X(104), 345 + i * 35, s, 22, anchor=anchor))
        o.append(f'<rect x="{min(X(104), X(430)):.1f}" y="489" width="326" height="3" fill="{INK}"/>')
        rows = [
            (fig_shoulders, 92, 515, 195, ['Rotate your', 'shoulders backward', 'and forward.']),
            (fig_arm, 94, 682, 195, ['Raise your right arm over your', 'head and stretch. Repeat with', 'your left arm.']),
            (fig_neck, 92, 852, 195, ['Rotate your neck', 'clockwise and', 'anticlockwise.']),
            (fig_ankle, 432, 852, 540, ['Rotate your left', 'ankle ten times. Repeat', 'with your right ankle.']),
        ]
        for fig, ix, iy, tx, tl in rows:
            o.append(icon(fig(bg), ix, iy, 90 if fig is fig_ankle else 72))
            for i, s in enumerate(tl):
                o.append(text(X(tx), iy + 30 + i * 36, s, 24, anchor=anchor))
        o.append(big_title(['A', 'e', 'ro-bics'], 88, 1178, 176))
    open(os.path.join(ART, f'end-{vname}-{side}.svg'), 'w').write(svg(E, E, ''.join(o), px=4096))


# ----------------------------------------------------------------- sandwich

# The window of the original pack in the front crop (pixels): its four
# corners, found as the edges of the printed strips around it.
CROP = os.path.join(ROOT, 'source', 'crops', 'tiffin-wedge-front.png')
WINDOW_QUAD = [(130.3, 127.0), (336.0, 127.0), (321.0, 458.0), (82.0, 458.0)]  # TL TR BR BL


def _homography(src, dst):
    """Coefficients (a..h) mapping src points to dst points."""
    A, B = [], []
    for (x, y), (u, w) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        B.append(u)
        A.append([0, 0, 0, x, y, 1, -w * x, -w * y])
        B.append(w)
    return np.linalg.solve(np.array(A, float), np.array(B, float))


def _apply(c, x, y):
    w = c[6] * x + c[7] * y + 1
    return (c[0] * x + c[1] * y + c[2]) / w, (c[3] * x + c[4] * y + c[5]) / w


def sandwich():
    """The window's contents, rectified to the window's real size (100 px per
    cm, the top of the image towards the apex), with a small inset so the
    die-cut edge and the printed strips stay out. The crop is a dull print:
    stretch its levels a little and give back some colour."""
    (x0, x1), (p0, p1) = dims.WIN_X, dims.WIN_P
    wp, hp = round((x1 - x0) * 100), round((p1 - p0) * 100)
    unit = _homography([(0, 0), (1, 0), (1, 1), (0, 1)], WINDOW_QUAD)
    iu, iv = 0.015, 0.012
    corners = [_apply(unit, u, w) for u, w in ((iu, iv), (1 - iu, iv), (1 - iu, 1 - iv), (iu, 1 - iv))]
    c = _homography([(0, 0), (wp, 0), (wp, hp), (0, hp)], corners)
    im = Image.open(CROP).convert('RGB').transform((wp, hp), Image.PERSPECTIVE, tuple(c), Image.BICUBIC)
    a = np.asarray(im).astype(float) / 255
    a = np.clip((a - 0.045) / (0.95 - 0.045), 0, 1)
    im = Image.fromarray((a * 255 + 0.5).astype(np.uint8))
    im = ImageEnhance.Color(im).enhance(1.06)
    im = im.filter(ImageFilter.UnsharpMask(radius=2.5, percent=40, threshold=2))
    im.save(os.path.join(ART, 'sandwich.png'))


for vn in VARIANTS:
    tube(vn)
    end_panel(vn, 'l')
    end_panel(vn, 'r')
sandwich()
print('art written')
