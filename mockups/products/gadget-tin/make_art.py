"""Gadget tin artwork, laid out on the tin's real dimensions (1 unit = 0.1 mm).
Run: python3 products/gadget-tin/make_art.py && node tools/raster.mjs products/gadget-tin/art

Style (from the photo): flat sky blue, everyday gadgets as white silhouettes,
their details cut back to the blue as fine lines ("knock-outs"). Wires (paper
clip, pins, clip handles) are one white stroke weight; knock-outs one blue
stroke weight. Every icon is drawn about its own centre and placed with
g(x, y, rotate)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

from brand.indigo import FONT, svg  # noqa: E402
from studio.layout import wrap_layout  # noqa: E402

import dims  # noqa: E402

U = 100  # units per cm
BL, WH = dims.BLUE, dims.WHITE
K = 4.5  # knock-out line width (0.45 mm)
WS = 11  # white wire width (1.1 mm)


# ----------------------------------------------------------------- primitives


def g(body, x=0.0, y=0.0, rot=0.0, s=1.0):
    t = f'translate({x:.1f} {y:.1f})'
    if rot:
        t += f' rotate({rot:.2f})'
    if s != 1:
        t += f' scale({s:.4f})'
    return f'<g transform="{t}">{body}</g>'


def P(d, fill=WH):
    return f'<path d="{d}" fill="{fill}"/>'


def R(x, y, w, h, rx=0.0, fill=WH):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}"/>'


def C(cx, cy, r, fill=WH):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"/>'


def ELL(cx, cy, rx, ry, fill=WH):
    return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}"/>'


def RING(cx, cy, r, w, color=WH):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{color}" stroke-width="{w:.1f}"/>'


def KO(d, w=K):
    """Blue knock-out line inside a white shape."""
    return f'<path d="{d}" fill="none" stroke="{BL}" stroke-width="{w:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'


def WIRE(d, w=WS):
    return f'<path d="{d}" fill="none" stroke="{WH}" stroke-width="{w:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'


def TXT(x, y, s, size, fill=BL, weight=700, anchor='middle', spacing=0):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="{FONT}" font-weight="{weight}" '
        f'font-size="{size:.1f}" letter-spacing="{spacing}" fill="{fill}">{s}</text>'
    )


# ----------------------------------------------------------------- lid icons


def swiss_knife():
    """Upright pocket knife, 645 tall: a pill-shaped body with a small keyring
    lug on top, the folded main blade's back along the right side (split off by
    a blue gap, with its nail nick) and four tool tips peeking out on the left.
    Origin: the body's centre."""
    tips = ''.join(WIRE(f'M -70 {y} C -84 {y} -90 {y - 4} -91 {y - 13}', w=11) for y in (-195, -140, -85, -30))
    return (
        tips
        + C(-3, -318, 17)
        + C(-3, -322, 6, BL)
        + R(-77, -322.5, 154, 645, 77)
        + P('M 81 -236 C 97 -214 107 -186 107 -150 L 107 258 C 107 280 98 291 84 293 L 81 293 Z')
        + KO('M 94 -170 L 94 -114', w=6)
    )


def binder_clip():
    """Body with the wire handles folded up into a keyhole loop; inside the
    body the legs show as white wires edged in blue. Origin: the body's centre."""
    handles = WIRE(
        'M -37 -71 L -31 -108 C -47 -122 -63 -140 -63 -162 C -63 -192 -34 -208 0 -208 '
        'C 34 -208 63 -192 63 -162 C 63 -140 47 -122 31 -108 L 37 -71'
    )
    legs = ''.join(
        f'<path d="M {sx * 37} -71 L {sx * 62} 78" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>'
        for sx in (-1, 1)
        for c, w in ((BL, 17), (WH, 7))
    )
    return handles + R(-143.5, -71.5, 287, 143, 6) + legs + R(-143.5, 80.5, 287, 23, 9)


def usb_stick():
    """Capped-off USB stick: rounded body, square connector with its two
    holes. Origin: the body's centre."""
    return (
        P('M -89 -71 L 156 -71 Q 160 -71 160 -67 L 160 67 Q 160 71 156 71 L -89 71 A 71 71 0 0 1 -89 -71 Z')
        + R(156, -50, 76, 100, 4)
        + R(169, -24, 13, 13, 3, BL)
        + R(169, 11, 13, 13, 3, BL)
    )


def whistle():
    """Round chamber with the mouthpiece along its top, tipped down to the
    left, a lug at the top right with a small ring and a hanging cord.
    Origin: the chamber's centre."""
    local = (
        C(0, 0, 85)
        + P('M -214 -85 L 0 -85 L 0 -30 L -214 -30 Q -222 -30 -222 -38 L -222 -77 Q -222 -85 -214 -85 Z')
        + R(-44, -90, 32, 24, 3, BL)
    )
    return (
        g(local, rot=-34)
        + g(R(-14, -16, 28, 32, 10), 62, -62, rot=45)
        + RING(88, -38, 12, 6)
        + WIRE('M 90 -26 L 90 56', w=6)
    )


def nail_clipper():
    """Lying flat, lever raised, keyring at the tail. Origin: jaw end, centreline."""
    lever = g(P('M 0 -7 L 360 -8 Q 376 -8 376 0 Q 376 8 360 8 L 0 7 Z'), 46, -46, rot=-36)
    return (
        lever
        + WIRE('M 52 -44 C 8 -44 -2 -22 -2 0 C -2 22 8 44 52 44', w=8)
        + P('M 40 -31 L 438 -24 Q 458 -22 466 -12 L 466 12 Q 458 22 438 24 L 40 31 Z')
        + KO('M 90 -7 L 300 -5')
        + KO('M 90 6 L 300 4')
        + R(34, -51, 24, 100, 6)
        + C(462, 0, 27)
        + C(470, 0, 10, BL)
        + RING(492, 0, 44, 8 + 2 * K, BL)  # a blue edge where the ring crosses the tail
        + RING(492, 0, 44, 8)
    )


def pocket_watch():
    """Disc with a bezel ring and dial ring, hands at 10:10; the crown sits
    inside the bow. Origin: the dial's centre."""
    return (
        RING(0, -204, 35, 12)
        + R(-20, -210, 40, 40, 13)
        + P('M -12 -174 L 12 -174 L 12 -148 C 12 -133 26 -124 45 -113 L -45 -113 C -26 -124 -12 -133 -12 -148 Z')
        + C(0, 0, 122)
        + RING(0, 0, 95, K, BL)
        + RING(0, 0, 87, 2.6, BL)
        + KO('M 0 0 L -50 -43')
        + KO('M 0 0 L 69 -43')
        + C(0, 0, 7, BL)
    )


def sharpener():
    """Box sharpener with concave top and bottom, its blade window outlined.
    Origin: centre."""
    return (
        P('M -122 -99 Q -138 -99 -138 -83 L -138 83 Q -138 99 -122 99 C -60 78 60 78 122 99 '
          'Q 138 99 138 83 L 138 -83 Q 138 -99 122 -99 C 60 -78 -60 -78 -122 -99 Z')
        + KO('M -123 -21 L 122 -21 L 122 40 L -123 40 Z')
        + KO('M -123 -21 L 122 -21', w=9)
        + KO('M -123 40 L 122 40', w=7)
        + C(0, 8, 7, BL)
    )


def spinning_top():
    """Lens-shaped disc on a thin spindle, with a short point below.
    Origin: the disc's centre."""
    return (
        P('M -131 0 C -88 -33 88 -33 132 0 C 88 33 -88 33 -131 0 Z')
        + P('M -5 -127 Q 0 -133 5 -127 L 7 -64 C 9 -40 20 -28 46 -18 L -46 -18 C -20 -28 -9 -40 -7 -64 Z')
        + P('M -38 18 C -16 24 -8 42 -4 78 Q 0 86 4 78 C 8 42 16 24 38 18 Z')
    )


def nail():
    """Upright, flat head at the top. Origin: top centre."""
    return R(-12.5, 0, 25, 11, 3) + P('M -5 9 L 5 9 L 5 262 L 0 293 L -5 262 Z')


def key():
    """Old-style key: a two-lobed bow with a hole, a flared collar, a straight
    shaft and a stepped bit. Origin: the bow's big lobe."""
    bit = (
        'M 195 26 L 195 44 L 205 44 L 205 56 L 215 56 L 215 68 L 225 68 L 225 84 L 255 84 L 255 62 '
        'L 265 62 L 265 84 L 283 84 L 283 62 L 293 62 L 293 84 L 313 84 L 313 26 Z'
    )
    return (
        C(-60, 0, 50)
        + C(0, 0, 88)
        + P('M 38 -79 C 68 -60 80 -31 112 -28.5 L 112 28.5 C 80 31 68 60 38 79 Z')
        + R(100, -28.5, 232, 57, 6)
        + P(bit)
        + C(-63, 0, 19, BL)
    )


# ----------------------------------------------------------------- body icons

IPOD_W = 398  # 0.78 cm round the front-left corner to 3.2 cm along the front


def ipod_shuffle():
    """First-generation iPod shuffle, lying down with its round control pad
    near the right end. As printed, the white body is cut square at both ends
    and starts on the front-left corner of the tin. Origin: the right end,
    centreline."""
    pad = -152
    # White symbols on the blue ring: + and - above and below, skip marks
    # (two chevrons) left and right; play/pause in blue on the white centre.
    plus_minus = R(pad - 13, -82, 26, 6, 2) + R(pad - 3, -92, 6, 26, 2) + R(pad - 13, 76, 26, 6, 2)
    prev = P(f'M {pad - 70} -11 L {pad - 88} 0 L {pad - 70} 11 Z') + P(f'M {pad - 86} -11 L {pad - 104} 0 L {pad - 86} 11 Z')
    nxt = P(f'M {pad + 70} -11 L {pad + 88} 0 L {pad + 70} 11 Z') + P(f'M {pad + 86} -11 L {pad + 104} 0 L {pad + 86} 11 Z')
    play = P(f'M {pad - 22} -11 L {pad - 4} 0 L {pad - 22} 11 Z', BL) + R(pad + 4, -10, 5, 20, 1, BL) + R(pad + 13, -10, 5, 20, 1, BL)
    return R(-IPOD_W, -134, IPOD_W, 268, 5) + C(pad, 0, 104, BL) + C(pad, 0, 58) + plus_minus + prev + nxt + play


def paper_clip():
    """Standing up: pointed outer loop on top, round loop at the bottom, the
    inner leg ending in a short diagonal tail. Origin: centre."""
    return WIRE(
        'M 34 104 L 34 -92 Q 34 -104 27 -112 L 6 -136 Q 0 -142 -6 -136 L -27 -112 Q -34 -104 -34 -92 '
        'L -34 110 A 28 28 0 0 0 22 110 L 22 -58 A 19 19 0 0 0 -16 -58 L -16 84 Q -16 96 -6 90 L 18 66'
    )


def battery():
    """AA cell lying down, positive end on the left. Origin: the terminal tip."""
    return R(0, -28, 24, 56, 6) + R(18, -83, 582, 166, 16)


def dice():
    pips = ''.join(C(x, y, 11, BL) for x, y in ((0, 0), (-32, -32), (32, -32), (-32, 32), (32, 32)))
    return R(-68, -68, 136, 136, 22) + pips


def safety_pin():
    """Coil on the left, D-shaped clasp head on the right, the two legs
    opening slightly towards it. Origin: coil centre."""
    return (
        WIRE('M 22 -22 L 292 -40', w=9)
        + WIRE('M 22 24 L 292 42', w=9)
        + RING(0, 0, 28, 10)
        + P('M 282 -58 L 328 -58 C 362 -58 386 -32 386 3 C 386 38 362 64 328 64 L 282 64 C 274 30 274 -24 282 -58 Z')
        + KO('M 314 -12 C 322 -32 354 -30 356 -4 C 358 16 338 26 326 14')
    )


def bobby_pin():
    """Hair grip: straight lower leg, gently wavy upper leg, ball tips.
    Origin: the bend."""
    xs = [482 - 32 * i for i in range(15)]  # wave nodes, 482 back to 34
    d = 'M 482 -17 '
    for i in range(len(xs) - 1):
        amp = -4 if i % 2 == 0 else 4
        d += f'Q {(xs[i] + xs[i + 1]) / 2} {-17 + amp} {xs[i + 1]} -17 '
    d += 'L 17 -17 A 17 17 0 0 0 17 17 L 482 17'
    return WIRE(d, w=9) + C(484, -17, 10) + C(484, 17, 10)


def pocket_compass():
    ticks = ''.join(KO(f'M {x1} {y1} L {x2} {y2}') for x1, y1, x2, y2 in ((0, -66, 0, -74), (66, 0, 74, 0), (0, 66, 0, 74), (-66, 0, -74, 0)))
    return (
        RING(0, -126, 20, 10)
        + R(-13, -106, 26, 22, 4)
        + C(0, 0, 90)
        + RING(0, 0, 78, K, BL)
        + ticks
        + P('M 0 -58 L 15 0 L -15 0 Z', BL)
        + KO('M -15 0 L 0 58 L 15 0', w=3.5)
        + C(0, 0, 5)
    )


def scissors():
    """Closed scissors lying down, points to the right. Origin: the pivot."""
    return (
        ELL(-98, -34, 40, 27)
        + ELL(-98, -34, 26, 14, BL)
        + ELL(-98, 34, 40, 27)
        + ELL(-98, 34, 26, 14, BL)
        + P('M -74 -52 C -52 -36 -30 -20 0 -17 L 0 17 C -30 20 -52 36 -74 52 L -62 14 L -62 -14 Z')
        + P('M -8 -22 L 184 -5 Q 193 0 184 5 L -8 22 Z')
        + KO('M 12 0 L 176 0', w=3.5)
        + C(0, 0, 8, BL)
    )


def torch():
    """Pocket torch lying down, lamp to the right. Origin: centre."""
    return (
        R(-132, -30, 196, 60, 12)
        + P('M 58 -30 L 96 -46 L 126 -46 Q 134 -46 134 -38 L 134 38 Q 134 46 126 46 L 96 46 L 58 30 Z')
        + KO('M 104 -46 L 104 46')
        + R(-46, -42, 36, 14, 5)
        + ''.join(KO(f'M {x} -30 L {x} 30', w=3.5) for x in (-112, -100, -88))
    )


def cassette():
    """Compact cassette: label panel outlined, two reel hubs either side of the
    window, the head opening along the bottom edge. Origin: centre."""
    hubs = ''.join(C(x, -18, 25, BL) + C(x, -18, 12) + C(x, -18, 4.5, BL) for x in (-64, 64))
    return (
        R(-140, -88, 280, 176, 14)
        + KO('M -118 -70 L 118 -70 L 118 34 L -118 34 Z')
        + hubs
        + R(-30, -31, 60, 26, 5, BL)
        + KO('M -86 88 L -68 54 L 68 54 L 86 88')
        + C(-36, 72, 6, BL)
        + C(36, 72, 6, BL)
    )


def pencil():
    """Lying down, point to the right. Origin: the eraser end."""
    return (
        R(0, -28, 60, 56, 14)
        + R(52, -31, 52, 62, 4)
        + KO('M 66 -31 L 66 31', w=3.5)
        + KO('M 78 -31 L 78 31', w=3.5)
        + KO('M 90 -31 L 90 31', w=3.5)
        + R(100, -28, 344, 56, 2)
        + KO('M 110 -9 L 434 -9', w=3.5)
        + KO('M 110 9 L 434 9', w=3.5)
        + P('M 440 -28 L 548 -3 Q 553 0 548 3 L 440 28 Z')
        + KO('M 446 -27 Q 474 0 446 27', w=3.5)
        + KO('M 524 -8 L 524 8', w=3.5)
    )


def sd_card():
    return (
        P('M -75 -88 Q -75 -100 -63 -100 L 43 -100 L 75 -68 L 75 88 Q 75 100 63 100 L -63 100 Q -75 100 -75 88 Z')
        + KO('M -54 -32 L 54 -32 L 54 80 L -54 80 Z')
        + R(-75, -40, 10, 30, 2, BL)
        + ''.join(R(-52 + i * 15, -86, 9, 24, 2, BL) for i in range(7))
        + TXT(0, 42, 'SD', 44)
    )


def sewing_button():
    return C(0, 0, 70) + RING(0, 0, 56, K, BL) + ''.join(C(x, y, 10, BL) for x, y in ((-17, -17), (17, -17), (-17, 17), (17, 17)))


def push_pin():
    head = (
        'M -38 -104 Q -38 -112 -30 -112 L 30 -112 Q 38 -112 38 -104 L 38 -90 Q 38 -82 30 -82 L 18 -82 '
        'L 20 -24 L 44 -14 Q 50 -12 50 -6 L 50 0 Q 50 6 44 6 L -44 6 Q -50 6 -50 0 L -50 -6 Q -50 -12 -44 -14 '
        'L -20 -24 L -18 -82 L -30 -82 Q -38 -82 -38 -90 Z'
    )
    return P(head) + P('M -4.5 6 L 4.5 6 L 4.5 82 L 0 104 L -4.5 82 Z')


def tape_measure():
    return (
        R(-60, -60, 120, 120, 30)
        + RING(0, 0, 28, K, BL)
        + C(0, 0, 9, BL)
        + R(44, 34, 64, 22, 3)
        + R(104, 24, 10, 40, 3)
        + R(-22, -60, 44, 12, 4, BL)
    )


def camera():
    """Compact digital camera, seen from the front."""
    return (
        R(-122, -118, 58, 24, 6)
        + R(-170, -100, 340, 200, 26)
        + RING(38, 6, 70, K, BL)
        + RING(38, 6, 50, K, BL)
        + C(38, 6, 22, BL)
        + R(-146, -78, 58, 28, 6, BL)
        + C(130, -70, 9, BL)
    )


def mobile_phone():
    keys = ''.join(R(-40 + c * 30, 30 + r * 22, 20, 12, 5, BL) for r in range(4) for c in range(3))
    return (
        R(-60, -126, 120, 252, 28)
        + R(-44, -100, 88, 78, 6, BL)
        + KO('M -14 -113 L 14 -113')
        + RING(0, 6, 12, K, BL)
        + R(-44, 0, 22, 12, 5, BL)
        + R(22, 0, 22, 12, 5, BL)
        + keys
    )


def calculator():
    keys = ''.join(R(-72 + c * 38, -18 + r * 30, 30, 20, 5, BL) for r in range(4) for c in range(4))
    return R(-92, -118, 184, 236, 18) + R(-72, -98, 144, 58, 6, BL) + keys


def spool():
    lines = ''.join(KO(f'M -58 {y} L 58 {y}', w=3) for y in range(-60, 70, 15))
    return R(-78, -100, 156, 26, 8) + R(-62, -76, 124, 152) + lines + R(-78, 74, 156, 26, 8)


def ballpoint():
    """Clicky ballpoint lying down, tip to the right. Origin: the button end."""
    return (
        R(0, -14, 40, 28, 8)
        + R(34, -27, 540, 54, 24)
        + R(62, -46, 250, 12, 6)
        + R(62, -40, 18, 16, 3)
        + C(300, -40, 10)
        + KO('M 470 -27 L 470 27')
        + KO('M 492 -27 L 492 27', w=3)
        + KO('M 506 -27 L 506 27', w=3)
        + KO('M 520 -27 L 520 27', w=3)
        + P('M 566 -22 L 680 -6 L 680 6 L 566 22 Z')
        + C(686, 0, 6)
    )


def needle():
    """Lying down, eye on the left. Origin: the eye end."""
    return P('M 0 -6 Q 0 -9 6 -9 L 190 -4 L 226 0 L 190 4 L 6 9 Q 0 9 0 6 Z') + KO('M 14 0 L 38 0', w=3.5)


# ----------------------------------------------------------------- lid top

W, D = dims.W * U, dims.D * U


def lid_top():
    """Layout measured on the photo, rectified to the flat lid (13 x 9.5 cm):
    knife and clipper down the left, clip / USB / whistle in the middle, the
    watch, key, sharpener, top and nail on the right, the text top right."""
    lines = [
        'This is not just a biscuit tin but something',
        'you can keep lots of small things in. Enjoy',
        'IndiGo’s 2nd reusable tin for the 2nd time',
        'in aviation history.',
    ]
    text = ''.join(TXT(630, 142 + i * 46.7, s, 27.6, fill=WH, weight=700, anchor='start') for i, s in enumerate(lines))
    icons = (
        g(swiss_knife(), 155, 432.5)
        + g(binder_clip(), 453.5, 286.5)
        + g(usb_stick(), 430, 489)
        + g(whistle(), 540, 695)
        + g(nail_clipper(), 110, 849)
        + g(pocket_watch(), 803, 570)
        + g(sharpener(), 1088, 411)
        + g(spinning_top(), 1043, 673)
        + g(nail(), 1203, 567)
        + g(key(), 805, 828)
    )
    return f'<rect width="{W}" height="{D}" fill="{BL}"/>' + icons + text


# ----------------------------------------------------------------- body wrap

bw, bd, br = dims.body_outline()
LAY = wrap_layout(bw, bd, br)
L = LAY['length'] * U
H = (dims.BODY_H - dims.BODY_EDGE) * U


def face_c(face):
    u0, u1 = LAY[face]
    return (u0 + u1) / 2 * LAY['length']


def at(u, z):
    """Strip position of a point u cm along the wrap and z cm above the floor."""
    return u * U, (dims.BODY_H - z) * U


def place(icon, u, z, rot=0.0, s=1.0):
    x, y = at(u, z)
    return g(icon, x, y, rot, s)


def body_side():
    """Positions in cm: u along the strip from the front face's left end
    (negative = back round the front-left corner), z above the floor."""
    rc, bc, lc = face_c('right'), face_c('back'), face_c('left')
    # Front, measured from the photo: two rows. The iPod panel starts on the
    # front-left corner, the hair grip's bend just round it; the battery and
    # the pin's head reach the front-right corner.
    front = (
        place(ipod_shuffle(), 3.2, 3.065)
        + place(paper_clip(), 3.92, 2.97)
        + place(battery(), 4.68, 3.47)
        + place(bobby_pin(), -0.7, 0.97)
        + place(dice(), 5.47, 1.31)
        + place(safety_pin(), 6.86, 1.37)
    )
    # The other faces are not in the photo: the same style and density, two
    # rows, with the larger shapes on top.
    right = (
        place(sd_card(), rc - 2.55, 3.4)
        + place(sewing_button(), rc - 0.85, 3.45)
        + place(tape_measure(), rc + 0.77, 3.45)
        + place(push_pin(), rc + 2.65, 3.45)
        + place(pencil(), rc - 2.74, 1.15)
    )
    back = (
        place(camera(), bc - 3.3, 3.36)
        + place(mobile_phone(), bc - 0.35, 3.36)
        + place(calculator(), bc + 1.85, 3.36)
        + place(spool(), bc + 4.05, 3.36)
        + place(ballpoint(), bc - 4.6, 1.16)
        + place(needle(), bc + 2.65, 1.16)
    )
    left = (
        place(pocket_compass(), lc - 2.2, 3.05)
        + place(cassette(), lc + 1.1, 3.3)
        + place(scissors(), lc - 1.6, 1.22)
        + place(torch(), lc + 1.75, 1.2)
    )
    content = front + right + back + left
    # The strip is a loop: draw it again one length either side so icons that
    # cross the seam (the iPod, the hair grip) continue at the other end.
    # The background overshoots the viewBox (which svg() rounds to whole units).
    return f'<rect x="-10" y="-10" width="{L + 20}" height="{H + 20}" fill="{BL}"/>' + g(content) + g(content, L) + g(content, -L)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    open(os.path.join(HERE, 'art', 'lid-top.svg'), 'w').write(svg(W, D, lid_top()))
    # Exactly 3 px per unit, so the strip's edge columns are whole pixels.
    open(os.path.join(HERE, 'art', 'body-side.svg'), 'w').write(svg(L, H, body_side(), px=3 * round(L)))
    print(f'art written: lid {W:.0f}x{D:.0f}, body strip {L:.0f}x{H:.0f} units')
