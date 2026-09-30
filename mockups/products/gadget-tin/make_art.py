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
    """Upright, 510 tall: rounded scales, keyring shackle, a blade proud of the
    right side, tool tips peeking out on the left."""
    ticks = ''.join(g(R(-14, -4.5, 28, 9, 4.5), -80, y, rot=-16) for y in (-172, -124, -76, -28))
    return (
        ticks
        + C(-14, -250, 20)
        + C(-14, -250, 7.5, BL)
        + R(-70, -255, 140, 510, 70)
        + P('M 78 -168 C 88 -190 97 -212 103 -228 C 110 -150 107 -60 96 6 Q 90 22 81 14 C 83 -50 83 -118 78 -168 Z')
        + KO('M 95 -170 L 98 -118')
    )


def binder_clip():
    """Body with the wire handles folded up: a keyhole-shaped loop."""
    handles = WIRE('M -14 -57 C -30 -78 -62 -100 -62 -124 C -62 -150 -32 -160 0 -160 C 32 -160 62 -150 62 -124 C 62 -100 30 -78 14 -57')
    return (
        handles
        + R(-138, -57, 276, 114, 8)
        + KO('M -14 -57 L -60 46')
        + KO('M 14 -57 L 60 46')
        + R(-138, 66, 276, 15, 6)
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
        C(0, 0, 80)
        + P('M -262 -80 L 0 -80 L 0 -34 L -262 -34 Q -268 -34 -268 -40 L -268 -74 Q -268 -80 -262 -80 Z')
        + R(-70, -84, 34, 18, 2, BL)
    )
    return g(local, rot=-32) + RING(62, -72, 15, 8)


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
        + C(482, 0, 30)
        + C(490, 0, 10, BL)
        + RING(534, 0, 42, 9)
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
        'M -134 0 C -86 -9 -44 -17 -22 -24 C -15 -42 -9 -70 -3 -92 Q 0 -98 3 -92 C 9 -70 15 -42 22 -24 '
        'C 44 -17 86 -9 134 0 C 86 9 44 19 22 26 C 15 44 9 64 3 82 Q 0 88 -3 82 C -9 64 -15 44 -22 26 '
        'C -44 19 -86 9 -134 0 Z'
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


def ipod_shuffle():
    """First-generation iPod shuffle: a long white stick with the round control
    pad near one end. Origin: the pad end, centreline; the stick runs left."""
    pad = -155
    # White symbols on the blue ring: + and - above and below, skip marks
    # (two chevrons) left and right; play/pause in blue on the white centre.
    plus_minus = R(pad - 13, -82, 26, 6, 2) + R(pad - 3, -92, 6, 26, 2) + R(pad - 13, 76, 26, 6, 2)
    prev = P(f'M {pad - 70} -11 L {pad - 88} 0 L {pad - 70} 11 Z') + P(f'M {pad - 86} -11 L {pad - 104} 0 L {pad - 86} 11 Z')
    nxt = P(f'M {pad + 70} -11 L {pad + 88} 0 L {pad + 70} 11 Z') + P(f'M {pad + 86} -11 L {pad + 104} 0 L {pad + 86} 11 Z')
    play = P(f'M {pad - 22} -11 L {pad - 4} 0 L {pad - 22} 11 Z', BL) + R(pad + 4, -10, 5, 20, 1, BL) + R(pad + 13, -10, 5, 20, 1, BL)
    return (
        R(-675, -125, 675, 250, 36)
        + KO('M -612 -125 L -612 125')
        + C(pad, 0, 104, BL)
        + C(pad, 0, 52)
        + plus_minus
        + prev
        + nxt
        + play
    )


def paper_clip():
    return WIRE('M -22 -62 L -22 70 A 22 22 0 0 0 22 70 L 22 -100 A 33.5 33.5 0 0 0 -45 -100 L -45 94 A 45 45 0 0 0 45 94 L 45 -78')


def battery():
    """AA cell lying down, positive end on the left. Origin: the terminal tip."""
    return (
        R(0, -31, 24, 62, 6)
        + R(18, -87, 608, 174, 18)
        + KO('M 112 -87 L 112 87')
        + KO('M 50 0 L 80 0')
        + KO('M 65 -15 L 65 15')
    )


def dice():
    pips = ''.join(C(x, y, 11.5, BL) for x, y in ((0, 0), (-34, -34), (34, -34), (-34, 34), (34, 34)))
    return R(-64, -64, 128, 128, 22) + pips


def safety_pin():
    """Coil on the left, clasp head on the right. Origin: coil centre."""
    return (
        WIRE('M 14 -16 L 362 -28', w=9)
        + WIRE('M 14 16 L 356 24', w=9)
        + RING(0, 0, 19, 9)
        + P('M 346 -46 L 390 -46 C 414 -46 428 -30 428 -6 C 428 18 414 36 390 38 L 346 38 C 338 16 338 -24 346 -46 Z')
        + KO('M 372 -12 C 380 -26 404 -24 406 -6 C 408 10 390 18 380 8')
    )


def bobby_pin():
    """Hair grip: straight lower leg, wavy upper leg, ball tips. Origin: the bend."""
    wave = 'M 500 -14 L 470 -14 Q 452 -24 434 -14 Q 416 -4 398 -14 Q 380 -24 362 -14 Q 344 -4 326 -14 Q 308 -24 290 -14 L 16 -14 A 14 14 0 0 0 16 14 L 500 14'
    return WIRE(wave, w=9) + C(502, -14, 9.5) + C(502, 14, 9.5)


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


def eraser():
    return R(-120, -48, 240, 96, 16) + KO('M -36 -48 L -36 48') + KO('M -24 -48 L -24 48', w=3)


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
    text = ''.join(TXT(628, 112 + i * 35, s, 26.5, fill=WH, weight=600, anchor='start', spacing=0.2) for i, s in enumerate(lines))
    icons = (
        g(swiss_knife(), 150, 334)
        + g(binder_clip(), 454, 226)
        + g(usb_stick(), 460, 390)
        + g(whistle(), 540, 572)
        + g(nail_clipper(), 72, 706)
        + g(pocket_watch(), 800, 486)
        + g(sharpener(), 1086, 318)
        + g(spinning_top(), 1060, 540)
        + g(nail(), 1214, 450)
        + g(key(), 790, 690)
    )
    return f'<rect width="{W}" height="{D}" fill="{BL}"/>' + icons + text


# ----------------------------------------------------------------- body wrap

bw, bd, br = dims.body_outline()
LAY = wrap_layout(bw, bd, br)
L = LAY['length'] * U
H = (dims.BODY_H - dims.BODY_EDGE) * U
FRONT_C = (LAY['front'][0] + LAY['front'][1]) / 2 * LAY['length']  # cm along the strip


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
    fc = FRONT_C
    rc, bc, lc = face_c('right'), face_c('back'), face_c('left')
    # Front, from the photo: two rows. The iPod runs round the front-left
    # corner onto the left side; the battery and the pin reach the right corner.
    front = (
        place(ipod_shuffle(), fc - 2.25, 3.0)
        + place(paper_clip(), fc - 1.5, 2.75)
        + place(battery(), fc - 0.63, 3.17)
        + place(dice(), fc + 0.15, 1.12)
        + place(safety_pin(), fc + 1.45, 1.12)
        + place(bobby_pin(), fc - 6.05, 0.93)
    )
    right = (
        place(sd_card(), rc - 1.85, 3.2)
        + place(sewing_button(), rc + 0.05, 3.25)
        + place(push_pin(), rc + 1.9, 3.2)
        + place(tape_measure(), rc - 1.9, 1.08)
        + place(eraser(), rc + 1.3, 1.08)
    )
    back = (
        place(camera(), bc - 3.3, 3.2)
        + place(mobile_phone(), bc - 0.35, 3.2)
        + place(calculator(), bc + 1.85, 3.2)
        + place(spool(), bc + 4.05, 3.2)
        + place(ballpoint(), bc - 4.6, 1.1)
        + place(needle(), bc + 2.65, 1.1)
    )
    left = (
        place(pocket_compass(), lc - 0.95, 2.95)
        + place(pencil(), lc - 2.75, 0.98)
    )
    content = front + right + back + left
    # The strip is a loop: draw it again one length either side so icons that
    # cross the seam (the iPod, the hair grip) continue at the other end.
    return f'<rect width="{L}" height="{H}" fill="{BL}"/>' + g(content) + g(content, L) + g(content, -L)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    open(os.path.join(HERE, 'art', 'lid-top.svg'), 'w').write(svg(W, D, lid_top()))
    open(os.path.join(HERE, 'art', 'body-side.svg'), 'w').write(svg(L, H, body_side(), px=12288))
    print(f'art written: lid {W:.0f}x{D:.0f}, body strip {L:.0f}x{H:.0f} units')
