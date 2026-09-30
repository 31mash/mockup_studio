"""The label's portrait: a 1950s film heroine in flat screen-print colours,
drawn as SVG paths. Coordinates: the oval's centre is the origin, units are
0.1 mm like the rest of the artwork; the caller clips to the oval."""

import math

HAIR = '#1e1a25'
HAIR_HI = '#4b4f74'
SKIN = '#f8e5c3'
SKIN_SH = '#e9b98a'
LINE = '#5a2418'  # warm dark brown for the drawing
DARK = '#221a1c'
RED = '#c3262d'
GOLD = '#e7b12c'
GOLD_DK = '#8a5a14'
SHAWL = '#5a3421'
SHAWL_HI = '#8f5d37'
WHITE = '#fffaf0'


def _braid(x0, y0, x1, y1, n=7):
    """A plait from (x0, y0) to (x1, y1): alternating lobes with sheen strokes."""
    out = []
    dx, dy = (x1 - x0) / n, (y1 - y0) / n
    ang = math.degrees(math.atan2(dy, dx)) - 90
    for i in range(n):
        cx, cy = x0 + dx * (i + 0.5), y0 + dy * (i + 0.5)
        s = 1.0 - 0.06 * i
        tilt = 28 if i % 2 else -28
        out.append(
            f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({ang + tilt:.1f}) scale({s:.2f})">'
            f'<ellipse cx="0" cy="0" rx="34" ry="24" fill="{HAIR}"/>'
            f'<path d="M-22,-6 C-10,-16 10,-16 22,-6" fill="none" stroke="{HAIR_HI}" stroke-width="4" stroke-linecap="round"/>'
            '</g>'
        )
    # a red and gold tassel (paranda) at the end
    ex, ey = x1 + dx * 0.2, y1 + dy * 0.2
    out.append(
        f'<g transform="translate({ex:.1f},{ey:.1f}) rotate({ang:.1f})">'
        f'<rect x="-12" y="-4" width="24" height="10" rx="3" fill="{GOLD}"/>'
        f'<path d="M-12,6 L-16,52 L-6,48 L0,56 L6,48 L16,52 L12,6 Z" fill="{RED}"/>'
        '</g>'
    )
    return ''.join(out)


def _head_back():
    """Hair behind the head and the neck, in face-local coordinates (nose tip
    near (0, 0), the face about 290 wide, y down)."""
    return (
        f'<path d="M-182,-140 C-196,-248 -86,-292 0,-290 C92,-292 198,-244 186,-136 '
        f'C180,-58 196,40 190,150 C186,240 176,300 150,380 L-150,380 C-176,300 -186,220 -190,100 '
        f'C-192,-10 -176,-92 -182,-140 Z" fill="{HAIR}"/>'
        # neck, widening into the chest
        f'<path d="M-64,110 C-62,190 -72,250 -96,330 C-120,390 -150,440 -170,470 L190,470 C170,430 130,380 106,330 C76,250 64,190 64,110 Z" fill="{SKIN}"/>'
        f'<path d="M-64,130 C-40,196 40,196 64,130 L66,206 C34,236 -34,236 -66,206 Z" fill="{SKIN_SH}"/>'
        f'<path d="M64,150 C66,230 86,300 118,360 L150,360 C110,300 88,230 86,150 Z" fill="{SKIN_SH}"/>'
    )


def _head_front():
    """Face, hair framing it, features and jewellery (face-local)."""
    p = []
    face = (
        'M-140,-150 C-150,-100 -151,-36 -139,22 C-126,92 -82,152 -36,180 '
        'C-16,192 16,192 36,180 C82,152 126,92 139,22 C151,-36 150,-100 140,-150 '
        'C128,-206 64,-222 0,-222 C-64,-222 -128,-206 -140,-150 Z'
    )
    p.append(f'<path d="{face}" fill="{SKIN}"/>')
    # modelling on the shadow side (the viewer's right): a slim crescent
    p.append(
        f'<path d="M136,-160 C150,-96 151,-34 139,22 C126,92 82,152 36,180 '
        f'C74,146 106,90 116,26 C126,-32 124,-96 112,-160 Z" fill="{SKIN_SH}"/>'
    )
    # ears, mostly under the hair
    for sx in (-1, 1):
        p.append(f'<ellipse cx="{sx * 146}" cy="-18" rx="16" ry="34" fill="{SKIN_SH if sx > 0 else SKIN}"/>')
    # front hair: centre parting, rounded waves over the temples and the ear tops
    p.append(
        f'<path d="M-172,-90 C-176,-212 -80,-266 0,-266 C80,-266 176,-212 172,-90 '
        f'C170,-60 164,-40 158,-22 C154,-60 148,-100 140,-128 C124,-178 70,-206 8,-206 L0,-196 L-8,-206 '
        f'C-70,-206 -124,-178 -140,-128 C-148,-100 -154,-60 -158,-22 C-164,-40 -170,-60 -172,-90 Z" fill="{HAIR}"/>'
    )
    # sheen on the hair
    for d in (
        'M-24,-252 C-84,-246 -134,-208 -154,-140',
        'M-44,-230 C-94,-218 -128,-186 -142,-138',
        'M24,-252 C84,-246 134,-208 154,-140',
        'M46,-228 C96,-216 128,-184 140,-136',
    ):
        p.append(f'<path d="{d}" fill="none" stroke="{HAIR_HI}" stroke-width="7" stroke-linecap="round"/>')
    # parting with sindoor, and the maang tikka
    p.append(f'<path d="M0,-264 L0,-204" stroke="{RED}" stroke-width="5" stroke-linecap="round"/>')
    p.append(f'<path d="M0,-204 L0,-178" stroke="{GOLD_DK}" stroke-width="3"/>')
    p.append(f'<circle cx="0" cy="-170" r="11" fill="{GOLD}" stroke="{GOLD_DK}" stroke-width="3"/><circle cx="0" cy="-170" r="4.5" fill="{RED}"/>')
    p.append(f'<path d="M-6,-158 L0,-146 L6,-158 Z" fill="{GOLD}"/>')
    # brows: thick, arched, tapering to the tail
    for sx in (-1, 1):
        p.append(
            f'<path d="M{sx * 24},-100 C{sx * 58},-124 {sx * 104},-122 {sx * 128},-94 '
            f'C{sx * 100},-112 {sx * 62},-112 {sx * 26},-94 Z" fill="{DARK}"/>'
        )
    # eyes: almond whites, dark irises, winged kajal
    for sx in (-1, 1):
        eye = f'M{sx * 110},-54 C{sx * 94},-78 {sx * 50},-82 {sx * 28},-60 C{sx * 50},-46 {sx * 90},-42 {sx * 110},-54 Z'
        cid = 'eyeL' if sx < 0 else 'eyeR'
        p.append(f'<clipPath id="{cid}"><path d="{eye}"/></clipPath>')
        p.append(f'<path d="{eye}" fill="{WHITE}"/>')
        ix = sx * 64 + 8  # both glance slightly to the viewer's right
        p.append(f'<g clip-path="url(#{cid})"><circle cx="{ix}" cy="-60" r="18" fill="#3a2016"/><circle cx="{ix}" cy="-60" r="9" fill="{DARK}"/></g>')
        p.append(f'<circle cx="{ix + 5}" cy="-66" r="4" fill="{WHITE}"/>')
        # upper lash line with a wing
        p.append(
            f'<path d="M{sx * 132},-72 C{sx * 124},-64 {sx * 116},-58 {sx * 110},-54 '
            f'C{sx * 94},-80 {sx * 50},-86 {sx * 26},-60 C{sx * 50},-76 {sx * 92},-74 {sx * 112},-62 '
            f'C{sx * 118},-64 {sx * 126},-68 {sx * 132},-72 Z" fill="{DARK}"/>'
        )
        p.append(f'<path d="M{sx * 104},-50 C{sx * 86},-42 {sx * 52},-44 {sx * 34},-56" fill="none" stroke="{LINE}" stroke-width="2.5" stroke-linecap="round"/>')
        # lid crease
        p.append(f'<path d="M{sx * 104},-74 C{sx * 88},-92 {sx * 52},-94 {sx * 34},-76" fill="none" stroke="{SKIN_SH}" stroke-width="4" stroke-linecap="round"/>')
    # nose: bridge shadow on one side, nostrils, the shadow beneath
    p.append(f'<path d="M16,-50 C18,-22 22,0 26,16" fill="none" stroke="{SKIN_SH}" stroke-width="7" stroke-linecap="round"/>')
    p.append(f'<path d="M-24,18 C-22,30 -10,34 -3,28 M3,28 C10,34 22,30 24,18" fill="none" stroke="{LINE}" stroke-width="4" stroke-linecap="round"/>')
    p.append(f'<ellipse cx="4" cy="40" rx="16" ry="4" fill="{SKIN_SH}"/>')
    # smile: red lips around a line of teeth
    p.append(f'<path d="M-54,78 C-30,68 -12,66 0,72 C12,66 30,68 54,78 C30,84 -30,84 -54,78 Z" fill="{RED}"/>')
    p.append(f'<path d="M-46,80 C-20,86 20,86 46,80 C28,96 -28,96 -46,80 Z" fill="{WHITE}"/>')
    p.append(f'<path d="M-44,82 C-26,114 26,114 44,82 C24,96 -24,96 -44,82 Z" fill="{RED}"/>')
    p.append(f'<path d="M-58,74 C-55,78 -52,80 -48,80 M58,74 C55,78 52,80 48,80" fill="none" stroke="{LINE}" stroke-width="3" stroke-linecap="round"/>')
    p.append(f'<path d="M-66,40 C-70,54 -68,66 -62,76" fill="none" stroke="{SKIN_SH}" stroke-width="4" stroke-linecap="round"/>')
    # bindi
    p.append(f'<circle cx="0" cy="-112" r="9" fill="{RED}"/>')
    # jhumkas
    for sx in (-1, 1):
        x = sx * 150
        p.append(
            f'<circle cx="{x}" cy="18" r="8" fill="{GOLD}" stroke="{GOLD_DK}" stroke-width="2.5"/>'
            f'<path d="M{x - 20},56 C{x - 18},34 {x + 18},34 {x + 20},56 Z" fill="{GOLD}" stroke="{GOLD_DK}" stroke-width="2.5"/>'
            f'<line x1="{x}" y1="26" x2="{x}" y2="36" stroke="{GOLD_DK}" stroke-width="3"/>'
        )
        for k in range(5):
            bx = x - 16 + k * 8
            p.append(f'<circle cx="{bx}" cy="62" r="3.6" fill="{RED if k % 2 else GOLD}"/>')
    return ''.join(p)


def _hand():
    """Her right hand raised to her hair, back of the hand to us, the four
    fingers resting on the hair (the thumb hidden in front of her temple);
    hand-local: wrist at the origin, fingers pointing up (-y)."""
    out = []
    # fingers: little, ring, middle, index (x at the knuckle, length, splay, width)
    for x, length, ang, w in ((-26, 60, -8, 17), (-9, 76, -3, 18.5), (9.5, 82, 1.5, 18.5), (27, 72, 6, 17.5)):
        out.append(
            f'<g transform="translate({x},-92) rotate({ang})">'
            f'<rect x="{-w / 2}" y="{-length}" width="{w}" height="{length + 14}" rx="{w / 2}" fill="{SKIN}" stroke="{SKIN_SH}" stroke-width="3"/>'
            # the nail, seen from the back of the hand, just short of the tip
            f'<path d="M{-w * 0.28},{-length + 17} C{-w * 0.28},{-length + 5} {w * 0.28},{-length + 5} {w * 0.28},{-length + 17} Z" fill="{RED}"/>'
            '</g>'
        )
    # the back of the hand over the finger roots, then its shadow side
    out.append(
        f'<path d="M-36,0 C-41,-40 -42,-76 -37,-100 C-24,-110 26,-110 39,-100 C44,-76 42,-40 38,0 Z" fill="{SKIN}"/>'
        f'<path d="M39,-100 C44,-76 42,-40 38,0 L24,0 C29,-40 31,-72 29,-104 C33,-103 36,-102 39,-100 Z" fill="{SKIN_SH}"/>'
    )
    # glass and gold bangles
    out.append(
        f'<rect x="-44" y="-6" width="90" height="11" rx="5" fill="{GOLD}" stroke="{GOLD_DK}" stroke-width="2"/>'
        f'<rect x="-46" y="6" width="94" height="10" rx="5" fill="{RED}" stroke="{GOLD_DK}" stroke-width="2"/>'
        f'<rect x="-48" y="17" width="98" height="11" rx="5" fill="{GOLD}" stroke="{GOLD_DK}" stroke-width="2"/>'
    )
    return ''.join(out)


def portrait(rx, ry, bg, uid):
    """The whole oval picture: background, shoulders, shawl, plait, raised
    hand and head."""
    s = []
    s.append(f'<rect x="{-rx}" y="{-ry}" width="{2 * rx}" height="{2 * ry}" fill="{bg}"/>')
    # soft halo behind the head, in a lighter tint of the background
    s.append(f'<ellipse cx="-10" cy="-70" rx="{rx * 0.78}" ry="{ry * 0.62}" fill="#ffffff" fill-opacity="0.12"/>')
    s.append(
        f'<defs><pattern id="hatch-{uid}" patternUnits="userSpaceOnUse" width="9" height="9" patternTransform="rotate(38)">'
        f'<rect width="9" height="9" fill="{SHAWL}"/><rect width="3" height="9" fill="{SHAWL_HI}"/></pattern></defs>'
    )
    head = 'translate(34,186) rotate(-9) scale(0.78) translate(0,-300)'
    s.append(f'<g transform="{head}">{_head_back()}</g>')
    # blouse, with a V neckline and gold trim
    s.append(
        f'<path d="M-330,{ry + 10} L-330,250 C-250,186 -150,170 -60,170 L-34,170 L46,264 L120,170 '
        f'C210,172 280,196 330,250 L330,{ry + 10} Z" fill="{RED}"/>'
    )
    s.append(f'<path d="M-34,170 L46,264 L120,170" fill="none" stroke="{GOLD}" stroke-width="7" stroke-linejoin="round"/>')
    # gold choker
    s.append(f'<path d="M-22,150 C12,186 74,184 106,146" fill="none" stroke="{GOLD}" stroke-width="10" stroke-linecap="round"/>')
    for k in range(7):
        t = k / 6
        x = -14 + 114 * t
        y = 160 + 24 * math.sin(math.pi * t) - 6 * t
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{RED if k % 2 else GOLD}" stroke="{GOLD_DK}" stroke-width="1.5"/>')
    # shawl over her right shoulder (the viewer's left), with a dotted gold border
    edge = f'M-330,96 C-250,110 -170,150 -118,190 C-60,236 -18,282 12,{ry + 10}'
    s.append(f'<path d="{edge} L-330,{ry + 10} Z" fill="url(#hatch-{uid})"/>')
    s.append(f'<path d="{edge}" fill="none" stroke="{GOLD}" stroke-width="8"/>')
    s.append(
        f'<path d="M-330,114 C-256,128 -180,166 -130,206 C-76,250 -36,294 -8,{ry + 10}" fill="none" '
        f'stroke="{GOLD}" stroke-width="3" stroke-dasharray="3 9" stroke-linecap="round"/>'
    )
    # plait over her left shoulder (the viewer's right)
    s.append(_braid(150, 70, 214, 300, n=6))
    # head
    s.append(f'<g transform="{head}">{_head_front()}</g>')
    # raised hand at her temple; the forearm wrapped in the shawl
    hand = 'translate(-206,-8) rotate(18) scale(0.86)'
    s.append(
        f'<g transform="{hand}">'
        f'<path d="M-50,22 L52,22 C60,140 70,260 60,420 L-120,420 C-96,260 -70,140 -50,22 Z" fill="url(#hatch-{uid})"/>'
        f'<path d="M-50,22 L52,22" stroke="{GOLD}" stroke-width="9"/>'
        f'{_hand()}</g>'
    )
    return ''.join(s)
