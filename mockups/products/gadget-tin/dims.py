"""Gadget tin size, in cm, fitted to the spread (source/crops/gadget-tin.png).

A rectangular slip-lid tin: a tall body under a short lid, 13 x 9.5 cm as the
brief gives it. The photo is a perspective shot from about 47 degrees above
the horizon at roughly 45 cm: the round pocket watch on the lid reads as 45
degrees, the iPod's round pad lower down on the body as 51. A camera fitted to
those, to the tin's outline and to the silver line of the lid's rolled edge
gives a depth of 9.5 cm, the rolled edge 5.1 cm above the floor and an overall
height of about 6.65 cm; the watch, the pad and the dice then rectify to true
circles and squares. The lid's rolled edge stands proud of the body by about
0.25 cm each side.
"""

W, D = 13.0, 9.5  # lid outline
CORNER = 1.35  # plan-view corner radius of the lid
BODY_H = 4.95  # body wall below the lid
LID_H = 1.7  # lid, from the body's top edge to the top of the lid
LID_GAP = 0.17  # the lid's rim sits this far above the top of the body's printed wall
LID_EDGE = 0.55  # rounded top edge of the lid
BODY_EDGE = 0.3  # rounded bottom edge of the body
OVERHANG = 0.26  # lid outline to body wall, each side
LIP_R = 0.09  # the lid's rolled bottom edge (bare tinplate)

BLUE = '#8cc6ec'  # printed sky blue (the photo samples #8fc9ed under bright light)
WHITE = '#fdfefe'  # opaque white ink


def body_outline():
    """Body wall: width, depth and plan corner radius."""
    return W - 2 * OVERHANG, D - 2 * OVERHANG, max(0.1, CORNER - OVERHANG)
