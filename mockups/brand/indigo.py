"""IndiGo brand pieces as SVG snippets, shared by every product's artwork.

The dotted plane is measured from the flat logos on the posters in the spread.
The typeface is Comfortaa (bold for the wordmark), the closest open font to
IndiGo's rounded lettering.
"""

import math

INDIGO_BLUE = '#3d4399'
INDIGO_GREEN = '#9fcc3b'
FONT = 'Comfortaa'


# Dot centres of the plane, measured from IndiGo's flat artwork (the posters
# in the spread): grid units of one dot spacing, y pointing down, heading
# up-right. A wing row and a wing column meet at the fuselage, which runs
# diagonally from the two-dot nose to the tail, where a short row and column
# form the tail wings. Twenty dots.
PLANE = [
    (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),  # wing row
    (4, 1), (4, 2), (4, 3), (4, 4),  # wing column
    (4.71, -0.71), (5.41, -1.41),  # nose
    (3.0, 1.0), (2.3, 1.72), (1.58, 2.43), (0.88, 3.13),  # fuselage
    (0.2, 3.85),  # tail junction
    (-0.8, 3.85), (-1.8, 3.85),  # tail row
    (0.2, 4.85), (0.2, 5.85),  # tail column
]


def plane_svg(cx: float, cy: float, size: float, color: str = INDIGO_GREEN, dot: float = 0.3, rotate: float = 0.0) -> str:
    """The plane as SVG circles, centred on (cx, cy); size = overall width."""
    xs = [p[0] for p in PLANE]
    ys = [p[1] for p in PLANE]
    span = max(xs) - min(xs) + 2 * dot
    s = size / span
    ox = (max(xs) + min(xs)) / 2
    oy = (max(ys) + min(ys)) / 2
    a = math.radians(rotate)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y in PLANE:
        dx, dy = (x - ox) * s, (y - oy) * s
        out.append(f'<circle cx="{cx + dx * ca - dy * sa:.2f}" cy="{cy + dx * sa + dy * ca:.2f}" r="{dot * s:.2f}" fill="{color}"/>')
    return ''.join(out)


def veg_mark(x: float, y: float, size: float) -> str:
    """India's vegetarian mark: green square outline and dot on white."""
    b = size * 0.1
    return (
        f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="#ffffff"/>'
        f'<rect x="{x + b * 0.9}" y="{y + b * 0.9}" width="{size - b * 1.8}" height="{size - b * 1.8}" fill="none" stroke="#0d9447" stroke-width="{b}"/>'
        f'<circle cx="{x + size / 2}" cy="{y + size / 2}" r="{size * 0.24}" fill="#0d9447"/>'
    )


def nonveg_mark(x: float, y: float, size: float) -> str:
    """India's non-vegetarian mark: brown square outline and dot on white."""
    b = size * 0.1
    return (
        f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="#ffffff"/>'
        f'<rect x="{x + b * 0.9}" y="{y + b * 0.9}" width="{size - b * 1.8}" height="{size - b * 1.8}" fill="none" stroke="#7b3f1d" stroke-width="{b}"/>'
        f'<circle cx="{x + size / 2}" cy="{y + size / 2}" r="{size * 0.24}" fill="#7b3f1d"/>'
    )


def svg(w: float, h: float, body: str, px: int = 4096) -> str:
    """An artwork file: viewBox in 1/100 cm (w, h in those units)."""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" data-width="{px}">{body}</svg>'
