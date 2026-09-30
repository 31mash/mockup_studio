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
    """Upright, 550 tall: rounded scales, keyring shackle on top, a folded
    blade's back along the right side (split off by a knock-out, with its nail
    nick), four tool tips peeking out of the left side."""
    tabs = ''.join(g(R(-24, -5.5, 36, 11, 5.5), -76, y, rot=-22) for y in (-196, -150, -104, -58))
    return (
        tabs
        + RING(0, -286, 17, 9)
        + R(-70, -275, 140, 550, 70)
        + P('M 75 -214 L 97 -246 Q 101 -250 101 -244 L 101 170 Q 101 196 83 200 L 75 200 Z')
        + KO('M 90 -176 L 90 -140', w=5)
    )


def binder_clip():
    """Body with the wire handles folded up: a keyhole-shaped loop."""
    handles = WIRE('M -13 -62 C -28 -86 -56 -116 -56 -142 C -56 -168 -30 -178 0 -178 C 30 -178 56 -168 56 -142 C 56 -116 28 -86 13 -62')
    return (
        handles
        + R(-134, -62, 268, 124, 8)
        + KO('M -13 -62 L -60 52')
        + KO('M 13 -62 L 60 52')
        + R(-134, 72, 268, 14, 6)
    )


def usb_stick():
    return (
        P('M -137 -60 L 125 -60 Q 133 -60 133 -52 L 133 52 Q 133 60 125 60 L -137 60 A 60 60 0 0 1 -137 -60 Z')
        + R(128, -38, 70, 76, 4)
        + KO('M 131 -44 L 131 44')
        + R(154, -24, 18, 15, 2, BL)
        + R(154, 9, 18, 15, 2, BL)
    )


def whistle():
    """Round chamber with the mouthpiece along its top, tipped down to the left,
    and a small ring for a lanyard."""
    local = (
        C(0, 0, 84)
        + P('M -214 -84 L 0 -84 L 0 -26 L -214 -26 Q -222 -26 -222 -34 L -222 -76 Q -222 -84 -214 -84 Z')
        + R(-78, -88, 36, 22, 3, BL)
    )
    return g(local, rot=-30) + RING(64, -76, 16, 8)


def nail_clipper():
    """Lying flat, lever raised, keyring at the tail. Origin: jaw end, centreline."""
    lever = g(P('M 0 -8 L 368 -10 Q 384 -10 384 0 Q 384 10 368 10 L 0 8 Z'), 50, -36, rot=-31.7)
    return (
        lever
        + P('M 20 -31 C 4 -31 -2 -18 -2 0 C -2 18 4 31 20 31 Z')
        + P('M 16 -32 L 440 -24 Q 468 -22 478 -10 L 478 10 Q 468 22 440 24 L 16 32 Z')
        + KO('M 66 -6 L 262 -4')
        + KO('M 66 6 L 262 4')
        + R(36, -50, 26, 98, 6)
        + C(480, 0, 28)
        + C(488, 0, 12, BL)
        + RING(530, 0, 40, 8 + 2 * K, BL)  # a blue edge where the ring crosses the tail
        + RING(530, 0, 40, 8)
    )


def pocket_watch():
    return (
        RING(0, -184, 29, 11)
        + R(-22, -154, 44, 20, 7)
        + R(-13, -140, 26, 26, 3)
        + C(0, 0, 120)
        + RING(0, 0, 100, K, BL)
        + RING(0, 0, 91, 2.6, BL)
        + KO('M 0 0 L -48 -28')
        + KO('M 0 0 L 64 -37')
        + C(0, 0, 7, BL)
    )


def sharpener():
    return (
        P('M -114 -82 Q -134 -82 -134 -62 L -134 62 Q -134 82 -114 82 C -60 68 60 68 114 82 Q 134 82 134 62 L 134 -62 Q 134 -82 114 -82 C 60 -68 -60 -68 -114 -82 Z')
        + KO('M -116 -22 L 116 -22 L 116 52 L -116 52 Z')
        + KO('M -116 -22 L 116 -22', w=8)
        + C(0, 14, 8, BL)
    )


def spinning_top():
    return P(
        'M -136 0 C -88 -10 -46 -18 -24 -26 C -13 -42 -8 -78 -5 -106 Q 0 -114 5 -106 C 8 -78 13 -42 24 -26 '
        'C 46 -18 88 -10 136 0 C 88 10 46 20 24 28 C 16 42 10 58 4 74 Q 0 81 -4 74 C -10 58 -16 42 -24 28 '
        'C -46 20 -88 10 -136 0 Z'
    )


def nail():
    """Upright, flat head at the top. Origin: top centre."""
    return R(-17, 0, 34, 10, 3) + P('M -5.5 8 L 5.5 8 L 5.5 234 L 0 266 L -5.5 234 Z')


def key():
    """Old-style key: round bow with a hole, shaft, stepped bit. Origin: bow centre."""
    bit = 'M 226 18 L 226 62 L 250 62 L 250 92 L 280 92 L 280 70 L 302 70 L 302 92 L 334 92 L 334 60 L 350 60 L 350 84 L 372 84 L 372 18 Z'
    return (
        C(-62, 0, 48)
        + C(8, 0, 76)
        + P('M 50 -62 C 82 -34 102 -23 132 -22 L 132 22 C 102 23 82 34 50 62 Z')
        + R(120, -22, 252, 44, 4)
        + P(bit)
        + C(-66, 0, 18, BL)
        + KO('M 150 -22 L 150 22')
    )


# ----------------------------------------------------------------- body icons

IPOD_W = 386  # 0.61 cm round the front-left corner to 3.25 cm along the front


def ipod_shuffle():
    """First-generation iPod shuffle, lying down with its round control pad
    near the right end. As printed, the white body is cut square at both ends
    and starts on the front-left corner of the tin. Origin: the right end,
    centreline."""
    pad = -150
    # White symbols on the blue ring: + and - above and below, skip marks
    # (two chevrons) left and right; play/pause in blue on the white centre.
    plus_minus = R(pad - 13, -82, 26, 6, 2) + R(pad - 3, -92, 6, 26, 2) + R(pad - 13, 76, 26, 6, 2)
    prev = P(f'M {pad - 70} -11 L {pad - 88} 0 L {pad - 70} 11 Z') + P(f'M {pad - 86} -11 L {pad - 104} 0 L {pad - 86} 11 Z')
    nxt = P(f'M {pad + 70} -11 L {pad + 88} 0 L {pad + 70} 11 Z') + P(f'M {pad + 86} -11 L {pad + 104} 0 L {pad + 86} 11 Z')
    play = P(f'M {pad - 22} -11 L {pad - 4} 0 L {pad - 22} 11 Z', BL) + R(pad + 4, -10, 5, 20, 1, BL) + R(pad + 13, -10, 5, 20, 1, BL)
    return R(-IPOD_W, -132, IPOD_W, 264, 5) + C(pad, 0, 104, BL) + C(pad, 0, 52) + plus_minus + prev + nxt + play


def paper_clip():
    """Standing up: pointed outer loop on top, round loop at the bottom, the
    inner leg ending in a short diagonal tail. Origin: centre."""
    return WIRE(
        'M 34 104 L 34 -92 Q 34 -104 27 -112 L 6 -136 Q 0 -142 -6 -136 L -27 -112 Q -34 -104 -34 -92 '
        'L -34 110 A 28 28 0 0 0 22 110 L 22 -58 A 19 19 0 0 0 -16 -58 L -16 84 Q -16 96 -6 90 L 18 66'
    )


def battery():
    """AA cell lying down, positive end on the left. Origin: the terminal tip."""
    return R(0, -28, 24, 56, 6) + R(18, -80, 582, 160, 16)


def dice():
    pips = ''.join(C(x, y, 11.5, BL) for x, y in ((0, 0), (-34, -34), (34, -34), (-34, 34), (34, 34)))
    return R(-64, -64, 128, 128, 22) + pips


def safety_pin():
    """Coil on the left, clasp head on the right. Origin: coil centre."""
    return (
        WIRE('M 22 -18 L 316 -28', w=9)
        + WIRE('M 22 18 L 310 24', w=9)
        + RING(0, 0, 26, 9)
        + P('M 300 -46 L 344 -46 C 368 -46 382 -30 382 -6 C 382 18 368 36 344 38 L 300 38 C 292 16 292 -24 300 -46 Z')
        + KO('M 326 -12 C 334 -26 358 -24 360 -6 C 362 10 344 18 334 8')
    )


def bobby_pin():
    """Hair grip: straight lower leg, wavy upper leg, ball tips. Origin: the bend."""
    wave = 'M 470 -14 L 440 -14 Q 422 -24 404 -14 Q 386 -4 368 -14 Q 350 -24 332 -14 Q 314 -4 296 -14 Q 278 -24 260 -14 L 16 -14 A 14 14 0 0 0 16 14 L 470 14'
    return WIRE(wave, w=9) + C(472, -14, 9.5) + C(472, 14, 9.5)


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
    """Layout from the photo: knife and clipper down the left, clip / USB /
    whistle in the middle, watch, key, sharpener, top and nail on the right,
    the text top right."""
    lines = [
        'This is not just a biscuit tin but something',
        'you can keep lots of small things in. Enjoy',
        'IndiGo’s 2nd reusable tin for the 2nd time',
        'in aviation history.',
    ]
    text = ''.join(TXT(630, 72 + i * 36.5, s, 26.5, fill=WH, weight=700, anchor='start', spacing=0) for i, s in enumerate(lines))
    icons = (
        g(swiss_knife(), 162, 326)
        + g(binder_clip(), 462, 206)
        + g(usb_stick(), 462, 378)
        + g(whistle(), 540, 566)
        + g(nail_clipper(), 72, 706)
        + g(pocket_watch(), 800, 458)
        + g(sharpener(), 1074, 306)
        + g(spinning_top(), 1056, 530)
        + g(nail(), 1200, 440)
        + g(key(), 776, 688)
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
        place(ipod_shuffle(), 3.25, 3.04)
        + place(paper_clip(), 3.98, 2.80)
        + place(battery(), 4.75, 3.34)
        + place(bobby_pin(), -0.44, 0.89)
        + place(dice(), 5.5, 1.11)
        + place(safety_pin(), 6.75, 1.11)
    )
    right = (
        place(sd_card(), rc - 2.05, 3.36)
        + place(sewing_button(), rc - 0.1, 3.41)
        + place(push_pin(), rc + 1.8, 3.36)
        + place(tape_measure(), rc - 1.95, 1.13)
        + place(torch(), rc + 1.05, 1.16)
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
        place(pocket_compass(), lc - 1.75, 3.15)
        + place(scissors(), lc + 0.8, 3.31)
        + place(pencil(), lc - 2.75, 1.03)
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
