"""The Bunji! bag's vintage pugilist: a one-colour engraving of a bare-chested
boxer in knee breeches, turned three-quarters to the right in the old
guard (lead arm out, rear fist across the body), redrawn as clean SVG from
the photo.

Paths are in the photo's own measuring space: 120 units per cm, origin
6.4 cm right of and 4.0 cm below the frame's outer top-left corner, so the
drawing lands where the figure sits on the printed bag. figure() places it."""

INK = '#4a332d'
PER_CM = 120.0

# ------------------------------------------------------------------ parts
# Drawn back to front. Each part is filled white (bare paper), hatched where
# it turns from the light, then outlined in ink.

REAR_LEG = (
    'M 88,486 C 88,506 90,524 94,544 C 88,560 82,580 84,604 '
    'C 86,626 94,644 98,662 L 130,664 C 128,646 130,628 132,606 '
    'C 134,584 134,562 136,546 C 140,526 146,506 150,488 Z'
)
FRONT_LEG = (
    'M 204,484 C 206,504 208,522 212,542 C 206,560 202,582 206,604 '
    'C 210,626 218,644 222,660 L 254,662 C 252,642 254,624 256,604 '
    'C 258,584 262,564 264,544 C 268,524 270,504 270,484 Z'
)
REAR_SHOE = (
    'M 96,662 L 132,664 C 136,674 142,684 150,694 C 158,703 156,713 146,715 '
    'L 94,717 C 87,715 85,707 87,698 C 89,686 92,674 96,662 Z'
)
FRONT_SHOE = (
    'M 222,660 L 254,662 C 266,672 282,680 300,687 C 316,693 328,699 330,708 '
    'C 330,716 322,719 312,719 L 218,719 C 211,717 209,709 211,700 C 213,688 216,674 222,660 Z'
)
TRUNKS = (
    'M 106,354 C 140,362 196,362 228,352 C 244,390 262,436 276,482 '
    'C 252,492 226,492 200,486 C 194,472 186,460 178,450 '
    'C 170,464 162,478 156,490 C 130,496 106,494 84,488 '
    'C 82,444 92,398 106,354 Z'
)
# The torso runs up into the neck; the head is drawn over its top.
TORSO = (
    'M 70,156 C 84,138 104,128 124,124 C 130,118 132,108 130,96 L 186,98 '
    'C 186,114 190,128 198,138 C 214,142 234,146 248,154 '
    'C 260,164 262,180 256,196 C 250,210 244,222 240,234 '
    'C 246,256 246,282 240,304 C 234,324 228,344 226,362 L 108,362 '
    'C 106,330 106,296 106,266 C 98,232 82,198 70,156 Z'
)
HEAD = (
    'M 124,104 C 110,86 106,60 116,40 C 128,22 158,16 178,22 '
    'C 192,28 198,40 198,54 C 200,62 204,68 209,76 C 209,80 205,83 200,84 '
    'C 202,89 202,93 199,96 C 200,103 198,110 192,114 '
    'C 182,120 166,121 156,115 C 144,111 134,108 124,104 Z'
)
HAIR = (
    'M 116,40 C 128,22 158,16 178,22 C 190,26 197,34 198,46 '
    'C 188,40 176,40 168,44 C 162,50 158,58 157,66 '
    'C 150,62 142,64 139,72 C 135,82 136,94 139,102 '
    'C 128,100 120,94 115,84 C 108,70 108,54 116,40 Z'
)
HAIR_STRANDS = ['M 122,44 C 134,30 156,24 176,28', 'M 120,60 C 128,44 146,36 166,36', 'M 124,76 C 128,62 138,52 152,48']
EAR = 'M 142,64 C 150,60 156,66 155,76 C 155,86 150,92 143,90 C 139,84 138,70 142,64 Z'
MOUSTACHE = 'M 181,88 C 186,83 197,83 204,87 C 205,93 198,96 191,95 C 186,96 181,94 181,88 Z'
REAR_UPPER_ARM = (
    'M 76,146 C 62,154 54,172 54,196 C 54,220 58,240 64,254 '
    'C 70,264 80,268 92,262 L 102,250 C 104,222 102,196 98,174 C 94,158 86,148 76,146 Z'
)
REAR_FOREARM = (
    'M 70,242 C 100,228 150,220 208,216 L 212,247 '
    'C 170,252 122,262 84,272 C 68,272 60,254 70,242 Z'
)
REAR_FIST = (
    'M 204,212 C 218,203 244,205 253,218 C 260,231 256,246 243,252 '
    'C 229,257 212,255 205,249 C 200,238 200,222 204,212 Z'
)
LEAD_ARM = (
    'M 238,156 C 254,150 268,158 274,174 C 292,190 320,198 352,204 '
    'L 356,238 C 330,242 300,248 276,248 C 262,248 250,242 244,232 '
    'C 236,214 234,184 238,156 Z'
)
LEAD_HAND = (
    'M 350,204 C 366,196 390,198 401,210 C 408,222 403,237 389,242 '
    'C 375,247 360,245 352,241 C 347,230 346,214 350,204 Z'
)

# ------------------------------------------------------------------ shading
# (part, (spacing, line width, angle), area): hatched areas, clipped to the
# part and laid in order, so 'white' areas take a highlight back out of the
# tone beneath. Lines run across each form, like an engraver's.

L1 = (5.2, 1.3, 58)  # light tone
M1 = (4.4, 1.8, 58)  # mid tone
D1 = (4.6, 1.5, -32)  # cross-hatch: dark tone
LEGL = (5.0, 1.2, 8)
LEGM = (4.2, 1.8, 8)
LEGD = (4.6, 1.5, -60)
TR_A = (4.0, 2.2, 68)
TR_B = (4.4, 1.7, -25)
ARM_M = (4.4, 1.8, -72)
ARM_D = (4.6, 1.5, 20)
FACE = (4.4, 1.3, 62)

SHADE = [
    # Head: the far cheek and jaw turn away from the light.
    ('head', FACE, 'M 150,70 C 160,84 168,100 176,118 L 150,116 C 140,110 132,104 128,98 Z'),
    ('head', FACE, 'M 186,58 C 192,58 197,60 199,64 C 194,68 188,68 185,64 Z'),
    # Torso: an overall light tone with the lit chest and belly left bare,
    # then the neck's shadow, the back and flank, a dark band under the
    # pecs, the ribs and belly turning away on the right.
    ('torso', L1, TORSO),
    ('torso', 'white', 'M 196,148 C 222,146 244,166 242,192 C 240,212 222,220 204,212 C 186,204 178,184 182,166 C 184,156 188,150 196,148 Z'),
    ('torso', 'white', 'M 132,146 C 152,140 174,150 176,170 C 178,190 164,204 146,202 C 130,200 120,186 122,170 C 122,158 126,150 132,146 Z'),
    ('torso', 'white', 'M 206,258 C 214,262 218,280 218,300 C 218,320 214,336 208,344 C 204,330 202,310 202,290 C 202,274 202,262 206,258 Z'),
    ('torso', M1, 'M 124,96 L 160,98 C 158,112 162,128 170,140 C 150,146 128,140 112,128 Z'),
    ('torso', M1, 'M 70,156 C 82,198 98,232 106,266 C 106,296 106,330 108,362 L 140,362 '
                  'C 134,320 128,280 126,240 C 122,200 114,160 102,130 Z'),
    ('torso', D1, 'M 70,156 C 82,198 98,232 106,266 C 106,296 106,330 108,362 L 124,362 '
                  'C 120,320 118,284 118,252 C 112,214 100,180 86,140 Z'),
    ('torso', L1, 'M 116,196 C 140,214 172,214 204,204 L 240,226 C 236,236 230,244 222,248 '
                  'C 186,248 146,246 112,242 Z'),
    ('torso', L1, 'M 162,140 C 166,166 170,190 172,212 L 182,210 C 180,186 178,162 176,142 Z'),
    ('torso', M1, 'M 220,250 C 232,280 230,322 220,362 L 226,362 C 228,344 234,324 240,304 C 246,282 246,256 240,234 Z'),
    ('torso', L1, 'M 210,252 C 224,282 224,322 214,362 L 226,362 C 230,320 240,280 240,240 Z'),
    ('torso', L1, 'M 126,262 C 156,276 192,278 222,266 L 222,282 C 192,294 156,292 126,280 Z'),
    ('torso', L1, 'M 132,316 C 160,326 194,326 222,316 L 222,332 C 194,342 160,342 132,332 Z'),
    # Breeches: dark cloth, darkest on the shadow side and between the legs.
    ('trunks', TR_A, TRUNKS),
    ('trunks', TR_B, 'M 106,354 C 92,398 82,444 84,488 C 98,492 112,494 126,494 C 120,446 120,400 132,360 Z'),
    ('trunks', TR_B, 'M 156,490 C 162,476 170,462 178,450 C 186,460 194,472 200,486 '
                     'C 196,440 188,400 176,370 C 166,400 158,450 156,490 Z'),
    ('trunks', TR_B, 'M 222,366 C 236,408 250,448 262,486 L 276,482 C 262,436 246,390 228,352 Z'),
    # Legs: the backs of the legs (left) and the calves in shadow, the
    # shins catching the light.
    ('rear-leg', LEGL, REAR_LEG),
    ('rear-leg', 'white', 'M 122,500 C 128,530 126,560 122,600 C 120,630 120,650 122,662 L 130,664 C 128,646 130,628 132,606 C 134,584 134,562 136,546 C 140,526 144,508 146,494 Z'),
    ('rear-leg', LEGM, 'M 88,486 C 88,506 90,524 94,544 C 88,560 82,580 84,604 C 86,626 94,644 98,662 '
                       'L 116,663 C 110,640 106,614 106,592 C 106,566 112,530 118,488 Z'),
    ('rear-leg', LEGD, 'M 88,486 C 88,506 90,524 94,544 C 88,560 82,580 84,604 C 86,626 94,644 98,662 '
                       'L 106,663 C 100,640 96,614 96,592 C 96,566 100,530 104,488 Z'),
    ('front-leg', LEGL, FRONT_LEG),
    ('front-leg', 'white', 'M 236,500 C 244,530 246,560 242,600 C 240,630 240,650 242,662 L 252,662 C 250,640 252,620 254,600 C 256,580 260,560 262,540 C 264,520 266,504 266,490 Z'),
    ('front-leg', LEGM, 'M 204,484 C 206,504 208,522 212,542 C 206,560 202,582 206,604 C 210,626 218,644 222,660 '
                        'L 236,661 C 230,636 226,610 226,588 C 226,560 230,520 232,484 Z'),
    ('front-leg', LEGD, 'M 204,484 C 206,504 208,522 212,542 C 206,560 202,582 206,604 L 216,606 '
                        'C 214,584 218,562 220,542 C 220,522 218,500 216,484 Z'),
    # Arms: the far upper arm in shadow, the undersides of both forearms dark.
    ('rear-upper-arm', ARM_M, REAR_UPPER_ARM),
    ('rear-upper-arm', ARM_D, 'M 76,146 C 62,154 54,172 54,196 C 54,220 58,240 64,254 C 70,264 80,268 92,262 '
                              'L 86,252 C 76,238 70,214 70,194 C 70,172 74,156 76,146 Z'),
    ('rear-forearm', L1, REAR_FOREARM),
    ('rear-forearm', 'white', 'M 70,242 C 100,228 150,220 208,216 L 209,226 C 160,228 110,236 72,250 Z'),
    ('rear-forearm', ARM_M, 'M 84,272 C 122,262 170,252 212,247 L 211,236 C 168,240 120,248 68,260 Z'),
    ('rear-fist', FACE, 'M 205,249 C 212,255 229,257 243,252 C 256,246 260,231 253,218 L 246,236 C 238,244 222,246 204,240 Z'),
    ('lead-arm', L1, LEAD_ARM),
    ('lead-arm', 'white', 'M 238,156 C 254,150 268,158 274,174 C 292,190 320,198 352,204 L 353,214 C 320,210 290,202 270,188 C 262,174 252,166 238,166 Z'),
    ('lead-arm', ARM_M, 'M 356,238 C 330,242 300,248 276,248 C 262,248 250,242 244,232 L 254,224 '
                        'C 262,228 280,232 302,230 C 322,228 340,226 355,224 Z'),
    ('lead-arm', ARM_D, 'M 356,238 C 330,242 300,248 276,248 L 276,240 C 300,240 326,236 355,231 Z'),
    ('lead-hand', FACE, 'M 352,241 C 360,245 375,247 389,242 C 403,237 408,222 401,210 L 394,226 C 386,234 370,236 351,230 Z'),
]

# Ink lines: anatomy, folds, knuckles, face.
LINES = [
    ('M 116,196 C 140,214 172,214 204,204', 2.2),  # under the rear pec
    ('M 204,152 C 216,172 228,196 238,214', 1.6),  # lead pec
    ('M 170,142 C 172,166 174,190 174,210', 1.5),  # sternum
    ('M 160,262 C 164,290 166,320 166,350', 1.3),  # belly line
    ('M 124,128 C 140,138 160,142 196,140', 1.4),  # collarbone
    ('M 130,392 C 132,420 132,450 128,490', 1.8),  # breeches folds
    ('M 214,392 C 228,420 242,450 256,486', 1.8),
    ('M 134,552 C 128,558 126,568 128,578', 1.5),  # knees
    ('M 262,550 C 256,558 254,568 256,578', 1.5),
    ('M 216,224 C 226,226 236,228 246,232', 1.6),  # rear knuckles
    ('M 214,236 C 224,238 234,240 244,244', 1.6),
    ('M 360,212 C 372,212 384,214 394,220', 1.6),  # lead knuckles
    ('M 358,226 C 370,226 382,228 396,232', 1.6),
    ('M 300,204 C 306,212 308,222 306,232', 1.3),  # lead elbow
    ('M 185,56 C 190,54 195,54 199,57', 2.4),  # brow
    ('M 188,63 C 191,62 194,62 196,64', 2.0),  # eye
    ('M 193,106 C 196,108 199,108 201,106', 1.6),  # lip
    ('M 146,72 C 150,74 151,80 147,84', 1.4),  # ear
]
GROUND = [
    ('M 76,722 L 162,722', 1.8), ('M 204,724 L 346,724', 1.8), ('M 96,729 L 142,729', 1.3), ('M 230,731 L 322,731', 1.3),
]
HIGHLIGHTS = [
    ('M 120,40 C 134,30 154,26 172,30', 2.2),  # hair sheen
    ('M 246,686 C 264,692 282,698 300,702', 2.4),  # shoe shine
    ('M 104,684 C 116,690 128,696 140,702', 2.0),
    ('M 146,400 C 150,430 150,456 148,482', 2.6),  # cloth sheen
    ('M 200,400 C 210,430 218,456 226,482', 2.6),
]

# His near (right) side faces us: the guard arm across the body is in front
# of the torso, the extended lead arm and the leading leg are behind it.
PARTS = [
    ('lead-arm', LEAD_ARM),
    ('lead-hand', LEAD_HAND),
    ('front-leg', FRONT_LEG),
    ('rear-leg', REAR_LEG),
    ('trunks', TRUNKS),
    ('torso', TORSO),
    ('head', HEAD),
    ('rear-upper-arm', REAR_UPPER_ARM),
    ('rear-forearm', REAR_FOREARM),
    ('rear-fist', REAR_FIST),
    ('rear-shoe', REAR_SHOE),
    ('front-shoe', FRONT_SHOE),
]


def figure(x: float, y: float, units_per_cm: float, uid: str = 'fig') -> str:
    """The figure as an SVG group, with the drawing space's origin at (x, y)
    in artwork units and `units_per_cm` artwork units to the centimetre."""
    s = units_per_cm / PER_CM
    defs = []
    pats = {}

    def pattern(spec):
        if spec not in pats:
            sp, lw, ang = spec
            pid = f'{uid}-h{len(pats)}'
            pats[spec] = pid
            defs.append(
                f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{sp}" height="{sp}" '
                f'patternTransform="rotate({ang})"><rect x="0" y="0" width="{sp}" height="{lw}" fill="{INK}"/></pattern>'
            )
        return pats[spec]

    body = []
    for i, (name, d) in enumerate(PARTS):
        if name.endswith('shoe'):
            body.append(f'<path d="{d}" fill="{INK}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>')
            continue
        cid = f'{uid}-clip-{i}'
        defs.append(f'<clipPath id="{cid}"><path d="{d}"/></clipPath>')
        body.append(f'<path d="{d}" fill="#ffffff"/>')
        for part, spec, sd in SHADE:
            if part == name:
                fill = '#ffffff' if spec == 'white' else f'url(#{pattern(spec)})'
                body.append(f'<path d="{sd}" fill="{fill}" clip-path="url(#{cid})"/>')
        body.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>')
        if name == 'head':
            body.append(f'<path d="{HAIR}" fill="{INK}"/>')
            for sd in HAIR_STRANDS:
                body.append(f'<path d="{sd}" fill="none" stroke="#ffffff" stroke-width="1.3" stroke-linecap="round"/>')
            body.append(f'<path d="{EAR}" fill="#ffffff" stroke="{INK}" stroke-width="1.8"/>')
            body.append(f'<path d="{MOUSTACHE}" fill="{INK}"/>')
    for d, w in HIGHLIGHTS:
        body.append(f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="{w}" stroke-linecap="round"/>')
    for d, w in LINES + GROUND:
        body.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w}" stroke-linecap="round"/>')
    return f'<defs>{"".join(defs)}</defs><g transform="translate({x:.2f},{y:.2f}) scale({s:.5f})">{"".join(body)}</g>'
