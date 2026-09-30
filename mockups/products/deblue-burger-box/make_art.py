"""DaBlue Burger artwork, laid out on the clamshell's real panels (1 unit = 0.1 mm).
Run: python3 products/deblue-burger-box/make_art.py && node tools/raster.mjs products/deblue-burger-box/art

Panels (each drawn upright as seen from outside):
  top.svg                 the flat top: mint medallion, tile border
  wall-{front,left,right,back}.svg
                          the lid walls, trapezoids W wide at the bottom edge, TOP wide at the fold
  base-side.svg           the base tray's four walls (inverted trapezoids)

The layout follows the photo, rectified panel by panel: Kutch folk patterns
on slate grey. Each lid wall is a grey field under a zigzag of blunt teeth
with dashed stitching; the pale-blue ground between the teeth carries
sky-blue V's. The front is symmetric: a sky-blue onion-dome lake with a
stitched shoreline, a peacock either side facing it, two star flowers, the
IndiGo wordmark and dotted plane in white, and 'Dabeli' repeated in Gujarati.
The left wall has the story, with coral-like white tufts along its foot. The
top is a mint medallion of dotted rings inside a border of diamond tiles,
with white scallops and dark sprigs along its edge and a grey dome in each
corner. The right and back walls are not in the photo: their copy is ours,
in the same style. Gujarati is set in Noto Sans Gujarati (OFL, art/src/),
loaded with @font-face.
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
ART = os.path.join(HERE, 'art')

# Print colours: sampled from the photo, then cleaned up (flat ink, no lighting).
SLATE = '#6e7b83'
PALE = '#bde2f1'
SKY = '#8acbe6'
LAKE = '#62b6d3'
MINT = '#b2dbc8'
MINT_DEEP = '#96cbb3'
YELLOW = '#ebe69a'
TILE = '#a6b3ba'
SPRIG = '#48605c'
OUTLINE = '#56676c'
TEAL = '#2f9bc6'
WHITE = '#f7fafa'
PEA_BODY = '#2a93c0'
PEA_NECK = '#2f7fb8'
PEA_TAIL = '#97d4ab'
PEA_EYE = '#2b5ca5'
PEA_RING = '#86d0e6'
STAR = '#2d3538'
FAN = '#b9c4c9'
BASE_BG = '#c6d0d6'
OVAL = '#8ccbe2'
GUJ = '#d9f0f8'

GUJ_FONT = 'Noto Sans Gujarati'
FONT_FACE = (
    "<style>@font-face{font-family:'Noto Sans Gujarati';"
    "src:url('src/noto-sans-gujarati-500.woff2') format('woff2');font-weight:500}</style>"
)


# ----------------------------------------------------------------- svg helpers (cm in, units out)


def f(v):
    return f'{v * U:.1f}'


def pts(ps):
    return ' '.join(f'{f(x)},{f(y)}' for x, y in ps)


def polygon(ps, fill, extra=''):
    return f'<polygon points="{pts(ps)}" fill="{fill}" {extra}/>'


def polyline(ps, stroke, w, extra=''):
    return f'<polyline points="{pts(ps)}" fill="none" stroke="{stroke}" stroke-width="{f(w)}" stroke-linejoin="round" stroke-linecap="round" {extra}/>'


def circle(x, y, r, fill, extra=''):
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{fill}" {extra}/>'


def group(body, x=0.0, y=0.0, s=1.0, rot=0.0, flip=False, extra=''):
    """A group drawn in local cm, placed at (x, y) cm, scaled by s."""
    sx = -s if flip else s
    return f'<g transform="translate({f(x)} {f(y)}) rotate({rot}) scale({sx * U:.3f} {s * U:.3f})" {extra}>{body}</g>'


def text(x, y, s, size, fill=WHITE, family=FONT, weight=500, anchor='start', extra=''):
    return (
        f'<text x="{f(x)}" y="{f(y)}" font-family="{family}" font-weight="{weight}" font-size="{f(size)}" '
        f'fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>'
    )


def offset_polyline(ps, d):
    """Miter offset of an open polyline by d towards its right-hand side in
    screen coordinates (y down), i.e. the inside of a clockwise outline."""

    def nrm(a, b):
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty)
        return (-ty / L, tx / L)

    out = []
    for i, p in enumerate(ps):
        if i == 0:
            n = nrm(ps[0], ps[1])
            out.append((p[0] + n[0] * d, p[1] + n[1] * d))
        elif i == len(ps) - 1:
            n = nrm(ps[-2], ps[-1])
            out.append((p[0] + n[0] * d, p[1] + n[1] * d))
        else:
            n1, n2 = nrm(ps[i - 1], p), nrm(p, ps[i + 1])
            mx, my = n1[0] + n2[0], n1[1] + n2[1]
            L = math.hypot(mx, my)
            mx, my = mx / L, my / L
            k = d / max(0.2, mx * n1[0] + my * n1[1])
            out.append((p[0] + mx * k, p[1] + my * k))
    return out


# ----------------------------------------------------------------- motifs (local cm)


def star_flower(r=0.26):
    """Dark eight-petal flower with a white heart and hairline."""
    petals = ''.join(
        f'<ellipse cx="0" cy="{-r * 0.52:.3f}" rx="{r * 0.26:.3f}" ry="{r * 0.5:.3f}" transform="rotate({a})" fill="{STAR}" stroke="{WHITE}" stroke-width="0.014"/>'
        for a in range(0, 360, 45)
    )
    return petals + f'<circle r="{r * 0.2:.3f}" fill="{WHITE}"/>'


def fan(length=0.28, spread=50, blades=5, color=FAN, w=0.034):
    """Hanging tassel: blades radiating downward from the origin, tips curling out."""
    out = []
    for i in range(blades):
        t = i / (blades - 1) * 2 - 1
        a = math.radians(90 + spread * t)
        L = length * (1.0 - 0.12 * abs(t))
        cx, cy = math.cos(math.radians(90 + spread * t * 0.5)) * L * 0.55, math.sin(math.radians(90 + spread * t * 0.5)) * L * 0.55
        ex, ey = L * math.cos(a), L * math.sin(a)
        out.append(f'<path d="M0,0 Q{cx:.3f},{cy:.3f} {ex:.3f},{ey:.3f}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>')
    return ''.join(out)


def coral(height=0.72, color=WHITE, w=0.07, foot=True):
    """Standing tuft as in the photo: six fingers rising from one foot, each
    bending outwards, the outer ones low and wide (like a sea anemone)."""
    H = height
    out = []
    # (lean of the finger's end in x, height of its end, how far its base sits off-centre)
    fingers = [(-0.56, 0.6, -0.05), (-0.36, 0.88, -0.03), (-0.1, 1.0, -0.01), (0.14, 0.98, 0.01), (0.38, 0.84, 0.03), (0.58, 0.56, 0.05)]
    for ex, ey, bx in fingers:
        x0, y0 = bx * H, 0.0
        x1, y1 = ex * H, -ey * H
        # the finger rises straight first and bends out near its tip
        cx, cy = x0 + (x1 - x0) * 0.1, y1 * 0.72
        out.append(f'<path d="M{x0:.3f},{y0:.3f} Q{cx:.3f},{cy:.3f} {x1:.3f},{y1:.3f}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>')
    if foot:
        out.append(f'<ellipse cx="0" cy="{-w * 0.2:.3f}" rx="{H * 0.1:.3f}" ry="{w * 0.7:.3f}" fill="{color}"/>')
    return ''.join(out)


def feather(root, angle, length, width, bend=0.0):
    """One tail feather: a long leaf from the root, ending in an eye. bend
    curves it sideways (cm at the tip)."""
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])
    rx, ry = root

    def P(s, o):
        o += bend * (s / length) ** 2
        return (rx + d[0] * s + n[0] * o, ry + d[1] * s + n[1] * o)

    E = P(length, 0)
    m = 0.62 * length
    c1, c2, c3, c4 = P(m * 0.5, width * 0.5), P(m * 1.15, width * 0.62), P(m * 1.15, -width * 0.62), P(m * 0.5, -width * 0.5)
    tipL, tipR = P(length * 0.93, width * 0.36), P(length * 0.93, -width * 0.36)
    body = (
        f'<path d="M{rx:.3f},{ry:.3f} C{c1[0]:.3f},{c1[1]:.3f} {c2[0]:.3f},{c2[1]:.3f} {tipL[0]:.3f},{tipL[1]:.3f} '
        f'Q{E[0]:.3f},{E[1]:.3f} {tipR[0]:.3f},{tipR[1]:.3f} C{c3[0]:.3f},{c3[1]:.3f} {c4[0]:.3f},{c4[1]:.3f} {rx:.3f},{ry:.3f}Z" '
        f'fill="{PEA_TAIL}" stroke="{WHITE}" stroke-width="0.026" stroke-linejoin="round"/>'
    )
    ex, ey = P(length * 0.8, 0)
    ang = angle + math.degrees(math.atan2(2 * bend * 0.8, length))
    eye = (
        f'<g transform="translate({ex:.3f} {ey:.3f}) rotate({ang:.1f})">'
        f'<ellipse rx="{width * 0.5:.3f}" ry="{width * 0.37:.3f}" fill="{PEA_RING}" stroke="{WHITE}" stroke-width="0.022"/>'
        f'<ellipse cx="{width * 0.06:.3f}" rx="{width * 0.3:.3f}" ry="{width * 0.21:.3f}" fill="{PEA_EYE}"/></g>'
    )
    s0, s1, s2 = P(length * 0.12, 0), P(length * 0.38, 0), P(length * 0.6, 0)
    rachis = (
        f'<path d="M{s0[0]:.3f},{s0[1]:.3f} Q{s1[0]:.3f},{s1[1]:.3f} {s2[0]:.3f},{s2[1]:.3f}" fill="none" '
        f'stroke="{WHITE}" stroke-width="0.016" stroke-linecap="round" opacity="0.75"/>'
    )
    return body + rachis + eye


def peacock(tail_angle=122, tail_len=2.5, feathers=5):
    """Folk peacock in local cm: head at (0, 0), facing +x. An S-curved neck
    runs down to a round breast; the body leans back into a long train of
    eyed feathers that sweeps down and back (towards -x)."""
    root = (-0.44, 1.38)
    spread = [(-16 + 32 * i / (feathers - 1)) for i in range(feathers)]
    lens = [0.84 + 0.16 * math.cos(math.radians(s * 5.5)) for s in spread]
    tail = ''.join(
        feather(root, tail_angle + s, tail_len * L, 0.44, bend=-0.06 * s / 16)
        for s, L in sorted(zip(spread, lens), key=lambda t: -abs(t[0]))
    )
    # Neck and body as one outline: throat, breast, belly, the rump running
    # into the train, the back and the nape.
    body = (
        f'<path d="M0.09,0.12 C0.12,0.34 0.04,0.52 0.10,0.74 C0.16,0.94 0.27,1.06 0.25,1.28 '
        f'C0.23,1.50 0.04,1.64 -0.20,1.64 C-0.42,1.64 -0.60,1.54 -0.68,1.40 '
        f'C-0.56,1.28 -0.42,1.12 -0.31,0.94 C-0.20,0.76 -0.15,0.56 -0.13,0.36 C-0.12,0.24 -0.11,0.14 -0.10,0.08Z" '
        f'fill="{PEA_BODY}" stroke="{WHITE}" stroke-width="0.032" stroke-linejoin="round"/>'
    )
    wing = (
        f'<path d="M-0.08,1.02 C0.04,1.18 0.03,1.38 -0.11,1.48 C-0.30,1.60 -0.52,1.52 -0.62,1.42 '
        f'C-0.44,1.38 -0.25,1.24 -0.08,1.02Z" fill="{PEA_NECK}" stroke="{WHITE}" stroke-width="0.022" stroke-linejoin="round"/>'
        f'<path d="M-0.12,1.20 C-0.20,1.34 -0.34,1.44 -0.52,1.48" fill="none" stroke="{WHITE}" stroke-width="0.016" stroke-linecap="round" opacity="0.8"/>'
        # dotted collar where the neck meets the breast
        + ''.join(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="0.022" fill="{WHITE}"/>' for x, y in ((0.14, 0.76), (0.04, 0.8), (-0.07, 0.8), (-0.17, 0.76)))
    )
    legs = ''.join(
        f'<path d="M{x0:.2f},1.6 L{x0 + 0.03:.2f},1.98 M{x0 + 0.03:.2f},1.98 l0.12,0.02 M{x0 + 0.03:.2f},1.98 l-0.08,0.05" '
        f'fill="none" stroke="{WHITE}" stroke-width="0.026" stroke-linecap="round" stroke-linejoin="round"/>'
        for x0 in (-0.16, 0.0)
    )
    crest = ''
    for ex, ey in ((-0.26, -0.42), (-0.12, -0.5), (0.03, -0.5), (0.17, -0.44)):
        crest += f'<line x1="-0.02" y1="-0.1" x2="{ex}" y2="{ey}" stroke="{WHITE}" stroke-width="0.02" stroke-linecap="round"/>'
        crest += f'<circle cx="{ex}" cy="{ey}" r="0.048" fill="{WHITE}"/>'
    head = (
        f'<path d="M0.11,-0.03 L0.33,0.04 L0.11,0.10Z" fill="{PALE}" stroke="{WHITE}" stroke-width="0.02" stroke-linejoin="round"/>'
        f'<circle cx="0" cy="0.02" r="0.15" fill="{PEA_BODY}" stroke="{WHITE}" stroke-width="0.032"/>'
        f'<circle cx="0.045" cy="-0.005" r="0.038" fill="{WHITE}"/>'
    )
    return tail + legs + body + wing + crest + head


# ----------------------------------------------------------------- lid walls


def wall_frame():
    """Geometry of a lid wall panel (cm, y down from the top fold): the grey
    field's zigzag outline (clockwise), where its teeth are, and the sky V's
    that fill the pale ground between the teeth. Nine blunt teeth run along
    the top, with a tooth at the centre; smaller teeth run down each side."""
    w, h, e = dims.W, dims.LID_SLANT, dims.A0 - dims.A1
    p_top, q_top, n_top, flat = 0.15, 0.62, 9, 0.16  # top zigzag: peak and valley depth, teeth, blunt tip
    p_side, q_side, pitch = 0.1, 0.52, 0.86
    L = math.hypot(e, h)
    sides = {
        'L': ((e, 0.0), (-e / L, h / L), (h / L, e / L)),
        'R': ((w - e, 0.0), (e / L, h / L), (-h / L, e / L)),
    }

    def at(side, s, o):
        (tx, ty), d, n = sides[side]
        return (tx + d[0] * s + n[0] * o, ty + d[1] * s + n[1] * o)

    # Each top corner is a valley shared by the top and side zigzags: where
    # the top valley line meets the side valley line.
    s_c = (q_top - (e / L) * q_side) / (h / L)
    VL, VR = at('L', s_c, q_side), at('R', s_c, q_side)
    # Side teeth from the corner down, ending on a half tooth at the bottom.
    m = max(1, round((L - s_c) / pitch - 0.5))
    step = (L - s_c) / (m + 0.5)
    side_pts = {k: [] for k in 'LR'}
    side_peaks = {k: [] for k in 'LR'}
    vees = []
    for k in 'LR':
        for i in range(m + 1):
            s_pk = s_c + (i + 0.5) * step
            side_pts[k].append(at(k, s_pk, p_side))
            if i < m:
                side_peaks[k].append(at(k, s_pk, p_side + 0.22))
                side_pts[k].append(at(k, s_c + (i + 1) * step, q_side))
                vees.append([at(k, s_pk, 0), at(k, s_pk + step, 0), at(k, s_c + (i + 1) * step, q_side)])
    top, top_peaks, top_valleys = [], [], []
    span = VR[0] - VL[0]
    half = span / (2 * n_top)
    for i in range(1, 2 * n_top):
        x = VL[0] + half * i
        if i % 2:
            top += [(x - flat / 2, p_top), (x + flat / 2, p_top)]
            top_peaks.append((x, p_top))
        else:
            top.append((x, q_top))
            top_valleys.append((x, q_top))
    for x, y in top_valleys:
        vees.append([(x - half, 0), (x + half, 0), (x, y)])
    # The corner V's: from the first top peak round the wall's corner to the
    # first side peak.
    s1 = s_c + 0.5 * step
    vees.append([(top_peaks[0][0], 0), (e, 0), at('L', s1, 0), VL])
    vees.append([(top_peaks[-1][0], 0), (w - e, 0), at('R', s1, 0), VR])
    outline = list(reversed(side_pts['L'])) + [VL] + top + [VR] + side_pts['R']
    field = outline + [(w + 0.3, h + 0.3), (-0.3, h + 0.3)]
    return dict(
        w=w, h=h, e=e, outline=outline, field=field, top_peaks=top_peaks, top_valleys=top_valleys,
        side_peaks=side_peaks['L'] + side_peaks['R'], vees=vees,
    )


def wall(name, scene, texts='', tooth='dot', defs=''):
    """A lid wall: pale ground with sky V's, the grey field with its stitched
    zigzag border (a white dot in each tooth, or a white dash on the story
    panel, and a grey tassel under each valley), then the panel's own scene
    (local cm) and texts (units)."""
    fr = wall_frame()
    w, h = fr['w'], fr['h']
    stitch = offset_polyline(fr['outline'], 0.08)
    deco = ''
    for x, y in fr['top_peaks']:
        if tooth == 'dot':
            deco += circle(x, y + 0.24, 0.05, WHITE)
        else:
            deco += f'<line x1="{f(x)}" y1="{f(y + 0.22)}" x2="{f(x)}" y2="{f(y + 0.5)}" stroke="{WHITE}" stroke-width="{f(0.06)}" stroke-linecap="round"/>'
    for x, y in fr['side_peaks']:
        deco += circle(x, y, 0.045, WHITE)
    if tooth == 'dot':
        for x, y in fr['top_valleys']:
            deco += group(fan(), x, y + 0.1)
    body = (
        FONT_FACE
        + f'<defs><clipPath id="field"><polygon points="{pts(fr["field"])}"/></clipPath>{defs}</defs>'
        + f'<rect x="-10" y="-10" width="{w * U + 20:.0f}" height="{h * U + 20:.0f}" fill="{PALE}"/>'
        + ''.join(polygon(v, SKY) for v in fr['vees'])
        + polygon(fr['field'], SLATE)
        + polyline(stitch, WHITE, 0.03, f'stroke-dasharray="{f(0.065)} {f(0.06)}"')
        + deco
        + f'<g clip-path="url(#field)">{scene}</g>'
        + texts
    )
    open(os.path.join(ART, f'{name}.svg'), 'w').write(svg(w * U, h * U, body, px=4096))


def lake_path():
    """The front panel's lake, centred: an onion-dome arch with a pointed
    finial just under the middle tooth, a round bulb, then a skirt that
    flares out to the panel's lower corners (cm)."""
    c = dims.A0
    b = dims.LID_SLANT + 0.4
    # right half, from the finial down: (control, control, end) in (dx, y)
    right = [
        ((0.06, 1.06), (0.25, 1.38), (0.72, 1.62)),
        ((1.18, 1.87), (1.5, 2.13), (1.62, 2.6)),
        ((1.74, 3.04), (1.95, 3.38), (2.62, 3.6)),
        ((3.46, 3.87), (4.2, 4.17), (4.58, 4.72)),
        ((4.74, 4.94), (4.8, 5.19), (4.8, b)),
    ]
    top = 0.76
    d = f'M{c:.3f},{top}'
    for (a, bb, e) in right:
        d += f' C{c + a[0]:.3f},{a[1]} {c + bb[0]:.3f},{bb[1]} {c + e[0]:.3f},{e[1]}'
    # across the bottom (below the panel's edge), then back up the left half, mirrored
    d += f' L{c - right[-1][2][0]:.3f},{b}'
    ends = [(0.0, top)] + [seg[2] for seg in right]
    for k in range(len(right) - 1, -1, -1):
        a, bb, _ = right[k]
        e = ends[k]
        d += f' C{c - bb[0]:.3f},{bb[1]} {c - a[0]:.3f},{a[1]} {c - e[0]:.3f},{e[1]}'
    return d + 'Z'


# 'Dabeli' in Gujarati, n times, joined by a middle dot between thin spaces.
def dabeli(n, x, y, size=0.44):
    return text(x, y, ' · '.join(['દાબેલી'] * n), size, GUJ, GUJ_FONT, 500, 'middle')


def front():
    c = dims.A0
    lp = lake_path()
    lake = (
        f'<path d="{lp}" fill="{LAKE}"/>'
        # stitched ticks just inside the shoreline, then the white shoreline
        f'<g clip-path="url(#lakein)"><path d="{lp}" fill="none" stroke="{WHITE}" stroke-width="0.32" stroke-dasharray="0.03 0.075"/>'
        f'<path d="{lp}" fill="none" stroke="{LAKE}" stroke-width="0.16"/></g>'
        f'<path d="{lp}" fill="none" stroke="{WHITE}" stroke-width="0.05" stroke-linejoin="round"/>'
    )
    # A symmetric panel: the lake in the middle, a peacock either side
    # facing it, a star flower either side of the finial.
    scene = (
        group(lake)
        + group(star_flower(0.2), c - 1.04, 1.14)
        + group(star_flower(0.2), c + 1.04, 1.14)
        + group(peacock(tail_angle=129, tail_len=2.2), c - 2.4, 1.42, s=0.86)
        + group(peacock(tail_angle=129, tail_len=2.2), c + 2.4, 1.42, s=0.86, flip=True)
        + plane_svg(c * U, 2.4 * U, 0.64 * U, color=WHITE, dot=0.26, rotate=0)
    )
    rows = dabeli(4, c, 4.52, 0.41) + dabeli(5, c, 4.99, 0.41)
    texts = (
        text(c, 3.92, 'IndiGo', 0.8, WHITE, FONT, 700, 'middle', f'letter-spacing="{f(-0.025)}"')
        + f'<g clip-path="url(#lakeU)">{rows}</g>'
    )
    defs = (
        f'<clipPath id="lakein"><path d="{lp}"/></clipPath>'
        f'<clipPath id="lakeU"><path d="{lp}" transform="scale({U})"/></clipPath>'
    )
    wall('wall-front', scene, texts, defs=defs)


def row_of(motif, xs, y, s=1.0):
    return ''.join(group(motif, x, y, s) for x in xs)


# Where the tufts stand along the lid walls' feet; the base's pools sit under them.
TUFT_XS = [dims.A0 + 1.42 * k for k in (-3, -2, -1, 0, 1, 2, 3)]


def left():
    h = dims.LID_SLANT
    lines = [
        'Sweet and spicy potato mixture filled into a',
        'burger bun and topped with pomegranate,',
        'peanuts, fresh garlic chutney and sev. Loved',
        'around Gujarat as Dabeli. Add 35000 ft',
        'and Dabeli becomes a delicious DaBlue.',
    ]
    texts = ''.join(text(1.95, 1.74 + 0.46 * i, s, 0.3, WHITE, FONT, 600) for i, s in enumerate(lines))
    scene = row_of(coral(0.72), TUFT_XS, h - 0.1)
    wall('wall-left', scene, texts, tooth='dash')


def right():
    h = dims.LID_SLANT
    lines = [
        'Burger bun, spiced potato filling (potato,',
        'dabeli masala, tamarind and date chutney),',
        'pomegranate, roasted peanuts, garlic chutney,',
        'sev and fresh coriander.',
    ]
    texts = text(2.55, 1.86, 'Ingredients', 0.34, WHITE, FONT, 700)
    texts += ''.join(text(1.95, 2.38 + 0.41 * i, s, 0.26, WHITE, FONT, 600) for i, s in enumerate(lines))
    texts += text(1.95, 4.08, 'Contains wheat (gluten) and peanuts. Best enjoyed fresh.', 0.21, WHITE, FONT, 600)
    scene = row_of(coral(0.6), TUFT_XS, h - 0.1)
    scene += veg_mark(1.95 * U, 1.54 * U, 0.42 * U)
    wall('wall-right', scene, texts)


def back():
    h = dims.LID_SLANT
    c = dims.A0
    scene = row_of(coral(0.6), TUFT_XS, h - 0.1)
    scene += group(star_flower(0.24), c - 1.9, 1.95) + group(star_flower(0.24), c + 1.9, 1.95)
    scene += plane_svg(c * U, 1.9 * U, 1.15 * U, color=WHITE, dot=0.28)
    texts = text(c, 3.22, 'goIndiGo.in', 0.48, WHITE, FONT, 700, 'middle')
    texts += text(c, 3.76, 'Please dispose of this box responsibly.', 0.23, WHITE, FONT, 600, 'middle')
    wall('wall-back', scene, texts)


# ----------------------------------------------------------------- top panel


def top():
    # Drawn in a 9.3 cm frame, measured from the rectified photo, then scaled
    # to the real panel.
    S = 9.3
    B = 1.06  # tile border width
    c = S / 2
    row = 0.52  # tile row centre, from the outer edge
    n = 8
    pitch = (S - 2 * row) / n
    a = pitch * 0.47  # half-diagonal of a diamond tile
    edge = ''
    # One edge's border, drawn along the front (bottom) edge, then rotated:
    # a row of diamond tiles, sky triangles between them on the outside,
    # yellow ones on the inside.
    for k in range(n):
        x0 = row + k * pitch
        x1 = x0 + pitch
        xm = (x0 + x1) / 2
        edge += polygon([(x0, S), (x1, S), (xm, S - row)], SKY)
        edge += polygon([(x0, S - B), (x1, S - B), (xm, S - row)], YELLOW)

    def tile_at(x, y):
        dia = [(x, y - a), (x + a, y), (x, y + a), (x - a, y)]
        inner = [(x, y - a + 0.12), (x + a - 0.12, y), (x, y + a - 0.12), (x - a + 0.12, y)]
        return (
            polygon(dia, WHITE, f'stroke="{OUTLINE}" stroke-width="{f(0.022)}" stroke-linejoin="round"')
            + polygon(inner, TILE)
            + circle(x, y, 0.06, WHITE)
        )

    for k in range(1, n):
        edge += tile_at(row + k * pitch, S - row)
    # Each edge's band is a trapezoid mitred at the corners; the corner tiles
    # sit on the mitres.
    band = pts([(0, S), (S, S), (S - B, S - B), (B, S - B)])
    border = ''.join(f'<g transform="rotate({ang} {f(c)} {f(c)})"><g clip-path="url(#band)">{edge}</g></g>' for ang in (0, 90, 180, 270))
    border += ''.join(tile_at(x, y) for x in (row, S - row) for y in (row, S - row))

    # Mint medallion: concentric rings of short white dashes, as in the print.
    m0, m1 = B, S - B
    rings = ''
    r = 2.36
    i = 0
    while r < 6.6:
        rings += f'<circle cx="{f(c)}" cy="{f(c)}" r="{f(r)}" stroke-dashoffset="{f(0.037 * i)}"/>'
        r += 0.105
        i += 1
    rings = (
        f'<g clip-path="url(#mint)" fill="none" stroke="{WHITE}" stroke-width="{f(0.03)}" '
        f'stroke-dasharray="{f(0.045)} {f(0.07)}" stroke-linecap="round" opacity="0.8">{rings}</g>'
    )

    # Scalloped inner edge: white half-ellipse arches outlined in grey with
    # dark sprigs between them; a grey dome in each corner.
    arch_rx, arch_ry, gate = 0.3, 0.24, 0.8
    span = (m1 - m0) - 2 * gate
    na = 6
    ap = span / na
    scal = ''
    for k in range(na):
        x = m0 + gate + ap * (k + 0.5)
        scal += f'<path d="M{f(x - arch_rx)},{f(m1)} A{f(arch_rx)},{f(arch_ry)} 0 0 1 {f(x + arch_rx)},{f(m1)}Z" fill="{WHITE}" stroke="{OUTLINE}" stroke-width="{f(0.04)}"/>'
    for k in range(1, na):
        x = m0 + gate + ap * k
        scal += group(coral(0.4, SPRIG, 0.036, foot=False), x, m1 - 0.01)
    scal_all = ''.join(f'<g transform="rotate({ang} {f(c)} {f(c)})">{scal}</g>' for ang in (0, 90, 180, 270))
    # The dome, drawn for the corner at the origin with its axis along the
    # diagonal: a grey arch whose foot fills the corner, ringed by a white
    # halo of short rays.
    rd = 0.3
    Ld = 1.0  # from the corner to the dome's crown, along the diagonal
    hw = 0.18
    rays = ''
    for j in range(13):
        t = math.radians(-90 + 180 * j / 12)
        x0, y0 = Ld - rd + (rd + 0.04) * math.cos(t), (rd + 0.04) * math.sin(t)
        x1, y1 = Ld - rd + (rd + hw - 0.05) * math.cos(t), (rd + hw - 0.05) * math.sin(t)
        rays += f'<line x1="{x0:.3f}" y1="{y0:.3f}" x2="{x1:.3f}" y2="{y1:.3f}"/>'
    for yy in (-1, 1):
        for xx in (0.1, 0.3, 0.5):
            rays += f'<line x1="{xx:.3f}" y1="{yy * (rd + 0.04):.3f}" x2="{xx:.3f}" y2="{yy * (rd + hw - 0.05):.3f}"/>'
    dome_local = (
        f'<path d="M-0.4,{-rd - hw:.3f} L{Ld - rd:.3f},{-rd - hw:.3f} A{rd + hw:.3f},{rd + hw:.3f} 0 0 1 {Ld - rd:.3f},{rd + hw:.3f} L-0.4,{rd + hw:.3f}Z" '
        f'fill="{WHITE}" stroke="{OUTLINE}" stroke-width="0.03"/>'
        f'<g stroke="{TILE}" stroke-width="0.026" stroke-linecap="round">{rays}</g>'
        f'<path d="M-0.4,{-rd:.3f} L{Ld - rd:.3f},{-rd:.3f} A{rd:.3f},{rd:.3f} 0 0 1 {Ld - rd:.3f},{rd:.3f} L-0.4,{rd:.3f}Z" '
        f'fill="{TILE}" stroke="{OUTLINE}" stroke-width="0.03"/>'
    )
    dome = '<g clip-path="url(#mint)">' + group(dome_local, m0, m0, rot=45) + '</g>'
    domes = ''.join(f'<g transform="rotate({ang} {f(c)} {f(c)})">{dome}</g>' for ang in (0, 90, 180, 270))

    # The label: two lines ranged left, the block centred in the circle.
    lx = c - 1.22
    label = (
        circle(c, c, 2.22, MINT_DEEP)
        + circle(c, c, 1.9, '#f4f8f9')
        + text(lx, c - 0.1, 'DaBlue', 0.7, TEAL, FONT, 600, 'start', f'letter-spacing="{f(-0.01)}"')
        + text(lx + 0.04, c + 0.66, 'Burger', 0.7, TEAL, FONT, 600, 'start', f'letter-spacing="{f(-0.01)}"')
    )
    body = (
        f'<defs><clipPath id="mint"><rect x="{f(m0)}" y="{f(m0)}" width="{f(m1 - m0)}" height="{f(m1 - m0)}"/></clipPath>'
        f'<clipPath id="band"><polygon points="{band}"/></clipPath></defs>'
        + f'<rect width="{f(S)}" height="{f(S)}" fill="{PALE}"/>'
        + border
        + f'<rect x="{f(m0)}" y="{f(m0)}" width="{f(m1 - m0)}" height="{f(m1 - m0)}" fill="{MINT}"/>'
        + rings
        + scal_all
        + domes
        + label
    )
    k = dims.TOP / S
    open(os.path.join(ART, 'top.svg'), 'w').write(svg(dims.TOP * U, dims.TOP * U, f'<g transform="scale({k:.5f})">{body}</g>', px=4096))


# ----------------------------------------------------------------- base tray


def base_side():
    """The base walls: the flange (hidden inside the lid) at the top of the
    image, then the visible sloping wall down to the bottom fold. A blue pool
    sits under each of the lid's tufts, tucked just under the lid's edge."""
    w, h = 2 * dims.CK, dims.BASE_SLANT
    cy = dims.BASE_FLANGE + dims.BASE_LOWER * 0.36
    ovals = ''
    for x in TUFT_XS:
        xx = x - dims.A0 + dims.CK
        ovals += f'<ellipse cx="{f(xx)}" cy="{f(cy)}" rx="{f(0.44)}" ry="{f(0.3)}" fill="{OVAL}" stroke="{WHITE}" stroke-width="{f(0.045)}"/>'
        ovals += f'<ellipse cx="{f(xx)}" cy="{f(cy + 0.02)}" rx="{f(0.24)}" ry="{f(0.13)}" fill="none" stroke="{WHITE}" stroke-width="{f(0.025)}" opacity="0.8"/>'
    body = f'<rect width="{f(w)}" height="{f(h)}" fill="{BASE_BG}"/>' + ovals
    open(os.path.join(ART, 'base-side.svg'), 'w').write(svg(w * U, h * U, body, px=4096))


if __name__ == '__main__':
    os.makedirs(ART, exist_ok=True)
    top()
    front()
    left()
    right()
    back()
    base_side()
    print('art written')
