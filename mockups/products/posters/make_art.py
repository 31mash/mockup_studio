"""IndiGo food posters: artwork laid out on the 40 x 59.4 cm sheet (1 unit = 0.1 mm).

Every position is measured from the two posters in the spread (ink edges and
baselines, as fractions of the sheet converted to cm). The lettering is
Comfortaa set as IndiGo's display face (see typeset.py): its y, e and l are
redrawn in IndiGo's shapes, and each line is fitted to the original's ink
width with tight display tracking and a gentle 0.95 condense (Comfortaa's
n, u and h run wider than IndiGo's; its o is already the right size, so a
stronger condense would make the o's oval).

Run: python3 products/posters/make_art.py && node tools/raster.mjs products/posters/art
(make_art.py measures the text with measure.mjs: Node and Playwright, as for raster.mjs.)
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)

from brand.indigo import plane_svg, svg  # noqa: E402

import dims  # noqa: E402
from typeset import Typesetter  # noqa: E402

U = 100  # units per cm
W, H = dims.W * U, dims.H * U
BLUE = dims.POSTER_BLUE
WHITE = dims.PAPER_WHITE
SX = 0.95  # display condense

T = Typesetter(WHITE)

# ------------------------------------------------------------------ copy
TFF_PARA = [
    'Enjoy the largest variety of delicious food',
    'in the sky – recommended and selected by',
    'the best food critics around.',
]
TFF_HEAD = ['Thought', 'for food']
SN_HEAD = ['Say no', 'to airline', 'food']
SN_PARA = [
    [('Don’t settle for preheated', 500)],
    [('and reheated ‘meals’. Limited', 500)],
    [('choices. Compromised eating.', 500)],
    [('Fly ', 500), ('IndiGo', 700), (' and choose from', 500)],
    [('the largest variety of fresh', 500)],
    [('and delicious food in the sky.', 500)],
]
WEB = 'goIndiGo.in'
CALL = 'Call 0 99 10 38 38 38 / 1800 180 38 38 (toll free)'
STATS = [('170', 'daily flights'), ('25', 'new aircraft'), ('22', 'destinations')]

for t in TFF_PARA:
    T.plan([(t, 700)])
for t in TFF_HEAD + SN_HEAD:
    T.plan([(t, 700)])
for segs in SN_PARA:
    T.plan(segs)
T.plan([(WEB, 700)])
T.plan([(CALL, 600)])
for num, label in STATS:
    T.plan([(num, 700)])
    T.plan([(label, 500)])
T.measure()


def headline(lines, size, targets):
    """Display lines, each fitted to the original's ink extent.
    targets: [(ink left, ink right, baseline)] in cm."""
    out = []
    for text, (l, r, base) in zip(lines, targets):
        segs = [(text, 700)]
        # Never tighter than -0.1 em, where Comfortaa's letters start to touch.
        ls = max(T.fit_ls(segs, size, (r - l) * U / SX), -0.1 * size)
        print(f'  {text!r}: tracking {ls / size:+.3f} em')
        out.append(T.line(segs, l * U, base * U, size, ls=ls, sx=SX))
    return ''.join(out)


def block(lines, x, base0, lead, size, width_of=None, ls=None):
    """A left-aligned paragraph: every line starts at the same origin, the
    first line's ink at x; tracking fitted so line `width_of` = (i, width)."""
    if ls is None:
        i, width = width_of
        ls = T.fit_ls(lines[i], size, width * U)
    _, left, _ = T.layout(lines[0], size, ls)
    ox = x * U - left
    return ''.join(T.line(segs, ox, (base0 + k * lead) * U, size, ls=ls, ink_left=False) for k, segs in enumerate(lines))


def footer():
    """Web address and call-centre line, bottom left (shared by both posters)."""
    web = T.line([(WEB, 700)], 2.5 * U, 54.87 * U, 2.2 * U, ls=T.fit_ls([(WEB, 700)], 2.2 * U, 11.6 * U))
    call = T.line([(CALL, 600)], 2.5 * U, 56.83 * U, 0.9 * U, ls=T.fit_ls([(CALL, 600)], 0.9 * U, 22.0 * U))
    return web + call


# ------------------------------------------------------------- Thought for food
print('thought-for-food')
body = f'<rect width="{W}" height="{H}" fill="{BLUE}"/>'
body += block([[(t, 700)] for t in TFF_PARA], 2.59, 3.93, 2.3, 1.6 * U, width_of=(0, 33.78))
body += headline(TFF_HEAD, 7.7 * U, [(2.59, 30.15, 17.98), (2.59, 28.89, 25.76)])
body += plane_svg(10.18 * U, 40.66 * U, 11.8 * U, color=WHITE)
body += footer()

# Stats panel: one outlined box of three rows, bottom right.
bx0, bx1, by0, by1 = 29.22, 37.23, 50.77, 56.71
rh = (by1 - by0) / 3
lw = 0.06
body += (
    f'<rect x="{bx0 * U:.1f}" y="{by0 * U:.1f}" width="{(bx1 - bx0) * U:.1f}" height="{(by1 - by0) * U:.1f}" '
    f'fill="none" stroke="{WHITE}" stroke-width="{lw * U}"/>'
)
for k in (1, 2):
    y = (by0 + k * rh) * U
    body += f'<line x1="{bx0 * U:.1f}" y1="{y:.1f}" x2="{bx1 * U:.1f}" y2="{y:.1f}" stroke="{WHITE}" stroke-width="{lw * U}"/>'
for k, (num, label) in enumerate(STATS):
    base = by0 + k * rh + 1.52
    n_size = 1.3 * U
    _, _, n_right = T.layout([(num, 700)], n_size, -0.03 * n_size)
    body += T.line([(num, 700)], 29.6 * U, base * U, n_size, ls=-0.03 * n_size, ink_left=False)
    body += T.line([(label, 500)], 29.6 * U + n_right + 0.28 * U, base * U, 0.8 * U, ls=0.0)
open(os.path.join(HERE, 'art', 'thought-for-food.svg'), 'w').write(svg(W, H, body))


# ------------------------------------------------------------- Say no to airline food
print('say-no')
body = f'<rect width="{W}" height="{H}" fill="{BLUE}"/>'
body += headline(SN_HEAD, 8.8 * U, [(2.69, 29.03, 11.18), (2.99, 36.81, 20.68), (2.99, 21.49, 30.18)])
# The copy sits beside "food": its last baseline on the baseline of "food",
# its right edge in line with the end of "airline".
body += block(SN_PARA, 22.6, 30.18 - 5 * 1.506, 1.506, 0.92 * U, width_of=(2, 14.16))
body += plane_svg(27.2 * U, 42.54 * U, 11.78 * U, color=WHITE)
body += footer()


def spark(cx, cy, r):
    """The fine starburst over the InterGlobe name: long rays up and to the
    right, short ones elsewhere, and a bright centre."""
    out = [f'<circle cx="{cx * U:.1f}" cy="{cy * U:.1f}" r="{0.07 * U:.1f}" fill="{WHITE}"/>']
    for k in range(12):
        a = math.radians(k * 30 + 15)
        up_right = math.cos(a - math.radians(-70))  # rays towards the upper right are longest
        ln = r * (0.3 + 0.7 * max(0.0, up_right)) * (1.0 if k % 2 == 0 else 0.6)
        x0, y0 = cx + math.cos(a) * r * 0.14, cy + math.sin(a) * r * 0.14
        x1, y1 = cx + math.cos(a) * ln, cy + math.sin(a) * ln
        out.append(
            f'<line x1="{x0 * U:.1f}" y1="{y0 * U:.1f}" x2="{x1 * U:.1f}" y2="{y1 * U:.1f}" '
            f'stroke="{WHITE}" stroke-width="{0.035 * U:.1f}" stroke-linecap="round"/>'
        )
    return ''.join(out)


# Parent-company line, bottom right: "an INTERGLOBE enterprise" mark.
body += (
    f'<text x="{29.75 * U:.1f}" y="{57.15 * U:.1f}" font-family="Comfortaa" font-weight="500" '
    f'font-size="{0.55 * U:.1f}" fill="{WHITE}" letter-spacing="{0.06 * U:.1f}">an</text>'
)
body += spark(31.45, 55.95, 0.68)
body += (
    f'<text x="{31.85 * U:.1f}" y="{57.15 * U:.1f}" font-family="Archivo" font-weight="800" '
    f'font-size="{0.76 * U:.1f}" fill="{WHITE}" textLength="{5.0 * U:.1f}" lengthAdjust="spacing">INTERGLOBE</text>'
)
open(os.path.join(HERE, 'art', 'say-no.svg'), 'w').write(svg(W, H, body))
print('art written')
