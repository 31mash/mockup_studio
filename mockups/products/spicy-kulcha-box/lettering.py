"""Block capitals for the label: the squared, chamfered display letters of an
Indian matchbox label ('SPICY', 'KULCHA'). Each glyph is drawn on a 100-unit
cap height (y down), with heavy stems, slightly lighter bars and small
chamfers on the outer corners, so the words read as one hand-lettered set.
"""

V = 27  # stem width
B = 22  # bar height
C = 12  # outer chamfer


def _poly(pts):
    return 'M' + ' L'.join(f'{x:g},{y:g}' for x, y in pts) + ' Z'


def _S(w=78):
    m0, m1 = 39, 61  # the middle bar
    return w, _poly([
        (C, 0), (w - C, 0), (w, C), (w, 32), (w - V, 32), (w - V, B), (V, B), (V, m0),
        (w - C, m0), (w, m0 + C), (w, 100 - C), (w - C, 100), (C, 100), (0, 100 - C),
        (0, 68), (V, 68), (V, 100 - B), (w - V, 100 - B), (w - V, m1), (C, m1), (0, m1 - C), (0, C),
    ])


def _P(w=76):
    bb = 60  # bottom of the bowl
    outer = _poly([(0, 0), (w - C, 0), (w, C), (w, bb - C), (w - C, bb), (V, bb), (V, 100), (0, 100)])
    inner = _poly([(V, B), (V, bb - B), (w - V, bb - B), (w - V, B)])
    return w, outer + ' ' + inner


def _I(w=V + 1):
    return w, _poly([(0, 0), (w, 0), (w, 100), (0, 100)])


def _C(w=74):
    return w, _poly([
        (C, 0), (w - C, 0), (w, C), (w, 32), (w - V, 32), (w - V, B), (V, B), (V, 100 - B),
        (w - V, 100 - B), (w - V, 68), (w, 68), (w, 100 - C), (w - C, 100), (C, 100), (0, 100 - C), (0, C),
    ])


def _Y(w=82):
    j = 62  # where the arms meet the stem
    return w, _poly([
        (0, 0), (V, 0), (V, j - B), (w - V, j - B), (w - V, 0), (w, 0), (w, j - C), (w - C, j),
        ((w + V) / 2, j), ((w + V) / 2, 100), ((w - V) / 2, 100), ((w - V) / 2, j), (C, j), (0, j - C),
    ])


def _K(w=80):
    return w, _poly([
        (0, 0), (V, 0), (V, 44), (w - V, 0), (w, 0), (w - 32, 50), (w, 100), (w - V, 100),
        (V, 56), (V, 100), (0, 100),
    ])


def _U(w=78):
    return w, _poly([
        (0, 0), (V, 0), (V, 100 - B), (w - V, 100 - B), (w - V, 0), (w, 0), (w, 100 - C),
        (w - C, 100), (C, 100), (0, 100 - C),
    ])


def _L(w=64):
    return w, _poly([(0, 0), (V, 0), (V, 100 - B), (w, 100 - B), (w, 100), (0, 100)])


def _H(w=80):
    return w, _poly([
        (0, 0), (V, 0), (V, 39), (w - V, 39), (w - V, 0), (w, 0), (w, 100), (w - V, 100),
        (w - V, 61), (V, 61), (V, 100), (0, 100),
    ])


def _A(w=80):
    cb = 70  # bottom of the crossbar
    outer = _poly([
        (0, 100), (0, C + 4), (C + 4, 0), (w - C - 4, 0), (w, C + 4), (w, 100), (w - V, 100),
        (w - V, cb), (V, cb), (V, 100),
    ])
    inner = _poly([(V, B), (V, cb - B), (w - V, cb - B), (w - V, B)])
    return w, outer + ' ' + inner


GLYPHS = {'S': _S, 'P': _P, 'I': _I, 'C': _C, 'Y': _Y, 'K': _K, 'U': _U, 'L': _L, 'H': _H, 'A': _A}
TRACK = 9  # letter spacing, in glyph units


def word(text, x, y, width, height, fill, keyline=None, keyline_w=0.0):
    """`text` set in block capitals to fill a width x height box whose top-left
    corner is (x, y). Returns an SVG group. A keyline, if given, is drawn
    outside the letters (painted under the fill), keyline_w wide in artwork
    units whatever the letters' scale, like a printed outline."""
    parts, cx = [], 0.0
    for ch in text:
        gw, d = GLYPHS[ch]()
        parts.append((cx, d))
        cx += gw + TRACK
    total = cx - TRACK
    sx, sy = width / total, height / 100.0
    stroke = ''
    if keyline:
        stroke = (
            f' stroke="{keyline}" stroke-width="{2 * keyline_w:g}" stroke-linejoin="round"'
            ' paint-order="stroke" vector-effect="non-scaling-stroke"'
        )
    paths = ''.join(
        f'<path transform="translate({x + ox * sx:g},{y:g}) scale({sx:g},{sy:g})" d="{d}"{stroke}/>' for ox, d in parts
    )
    return f'<g fill="{fill}" fill-rule="evenodd">{paths}</g>'
