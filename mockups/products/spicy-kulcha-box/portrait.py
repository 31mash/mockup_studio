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


def _face():
    """Head and neck in face-local coordinates: nose tip near (0, 0), the face
    about 290 wide; y down."""
    p = []
    # hair behind the head, falling to the shoulders
    p.append(
        f'<path d="M-182,-140 C-196,-248 -86,-292 0,-290 C92,-292 198,-244 186,-136 '
        f'C180,-58 196,40 186,128 C180,178 160,212 126,226 L-126,226 C-166,206 -184,140 -188,52 '
        f'C-192,-30 -176,-92 -182,-140 Z" fill="{HAIR}"/>'
    )
    # neck, with the shadow under the jaw
    p.append(f'<path d="M-64,120 C-62,190 -70,260 -78,320 L78,320 C70,260 62,190 64,120 Z" fill="{SKIN}"/>')
    p.append(f'<path d="M-64,130 C-40,196 40,196 64,130 L66,206 C34,236 -34,236 -66,206 Z" fill="{SKIN_SH}"/>')
    # face
    face = (
        'M-140,-150 C-150,-100 -151,-36 -139,22 C-126,92 -82,152 -36,180 '
        'C-16,192 16,192 36,180 C82,152 126,92 139,22 C151,-36 150,-100 140,-150 Z'
    )
    p.append(f'<path d="{face}" fill="{SKIN}"/>')
    # modelling on the shadow side (the viewer's right)
    p.append(f'<path d="M140,-150 C152,-60 146,40 118,108 C96,150 66,172 36,182 C84,140 112,70 116,-10 C119,-70 112,-120 108,-150 Z" fill="{SKIN_SH}"/>')
    # ears, mostly under the hair, and jhumka earrings
    for sx in (-1, 1):
        p.append(f'<ellipse cx="{sx * 146}" cy="-18" rx="16" ry="34" fill="{SKIN_SH if sx > 0 else SKIN}"/>')
    # front hair: centre parting, swept over the temples
    p.append(
        f'<path d="M-168,-96 C-170,-206 -78,-262 0,-262 C78,-262 170,-206 168,-96 '
        f'C160,-96 154,-84 150,-60 C138,-150 76,-196 6,-194 L0,-184 L-6,-194 '
        f'C-76,-196 -138,-150 -150,-60 C-154,-84 -160,-96 -168,-96 Z" fill="{HAIR}"/>'
    )
    # sheen on the hair
    for d in (
        'M-26,-250 C-80,-246 -128,-214 -148,-160',
        'M-40,-232 C-86,-222 -120,-194 -134,-150',
        'M26,-250 C80,-246 128,-214 148,-160',
        'M44,-230 C92,-220 124,-190 136,-146',
    ):
        p.append(f'<path d="{d}" fill="none" stroke="{HAIR_HI}" stroke-width="7" stroke-linecap="round"/>')
    # parting with sindoor, and the maang tikka
    p.append(f'<path d="M0,-262 L0,-190" stroke="{RED}" stroke-width="5" stroke-linecap="round"/>')
    p.append(f'<path d="M0,-200 L0,-172" stroke="{GOLD_DK}" stroke-width="3"/>')
    p.append(f'<circle cx="0" cy="-164" r="11" fill="{GOLD}" stroke="{GOLD_DK}" stroke-width="3"/><circle cx="0" cy="-164" r="4.5" fill="{RED}"/>')
    p.append(f'<path d="M-6,-152 L0,-140 L6,-152 Z" fill="{GOLD}"/>')
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


def portrait(rx, ry, bg, uid):
    """The whole oval picture: background, shoulders, shawl, braid and head."""
    s = []
    s.append(f'<rect x="{-rx}" y="{-ry}" width="{2 * rx}" height="{2 * ry}" fill="{bg}"/>')
    # soft halo behind the head, in a lighter tint of the background
    s.append(f'<ellipse cx="-10" cy="-70" rx="{rx * 0.78}" ry="{ry * 0.62}" fill="#ffffff" fill-opacity="0.12"/>')
    s.append(
        f'<defs><pattern id="hatch-{uid}" patternUnits="userSpaceOnUse" width="11" height="11" patternTransform="rotate(38)">'
        f'<rect width="11" height="11" fill="{SHAWL}"/><rect width="4.4" height="11" fill="{SHAWL_HI}"/></pattern></defs>'
    )
    # blouse
    s.append(f'<path d="M-320,{ry} L-320,250 C-250,186 -150,168 -60,168 L130,168 C210,172 280,196 330,250 L330,{ry} Z" fill="{RED}"/>')
    # head and neck, tilted, pivoting on the base of the neck
    nx, ny = 34, 186
    face = f'<g transform="translate({nx},{ny}) rotate(-9) scale(0.78) translate(0,-300)">{_face()}</g>'
    s.append(face)
    # neckline: skin V into the blouse, with a gold choker
    s.append(f'<path d="M-30,168 L108,168 L46,262 Z" fill="{SKIN}"/>')
    s.append(f'<path d="M-24,172 C10,200 70,200 102,168" fill="none" stroke="{GOLD}" stroke-width="10" stroke-linecap="round"/>')
    for k in range(7):
        t = k / 6
        x = -16 + 110 * t
        y = 176 + 22 * math.sin(math.pi * t)
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{RED if k % 2 else GOLD}" stroke="{GOLD_DK}" stroke-width="1.5"/>')
    # blouse trim along the neckline
    s.append(f'<path d="M-30,168 L46,262 L108,168" fill="none" stroke="{GOLD}" stroke-width="6" stroke-linejoin="round"/>')
    # shawl over her right shoulder (the viewer's left), with a dotted gold border
    shawl = f'M-330,96 C-250,110 -170,150 -118,190 C-60,236 -18,282 12,{ry + 10} L-330,{ry + 10} Z'
    s.append(f'<path d="{shawl}" fill="url(#hatch-{uid})"/>')
    s.append(f'<path d="M-330,96 C-250,110 -170,150 -118,190 C-60,236 -18,282 12,{ry + 10}" fill="none" stroke="{GOLD}" stroke-width="8"/>')
    s.append(f'<path d="M-330,114 C-256,128 -180,166 -130,206 C-76,250 -36,294 -8,{ry + 10}" fill="none" stroke="{GOLD}" stroke-width="3" stroke-dasharray="3 9" stroke-linecap="round"/>')
    # plait over her left shoulder (the viewer's right)
    s.append(_braid(150, 70, 214, 300, n=6))
    return ''.join(s)
