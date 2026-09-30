"""Gadget tin size, in cm, estimated from the spread (source/crops/gadget-tin.png).

A rectangular slip-lid tin: a tall body under a short lid. The photo is taken
from about 52 degrees above the horizon (the round pocket watch on the lid and
the iPod's round control pad on the body both give that), nearly straight on.
With the width taken as 13 cm that gives a depth of about 8.5 cm, the lid's
rolled edge about 5.2 cm above the floor and a lid whose flat side is about
0.9 cm below a 0.55 cm rounded top edge. The lid's rolled edge stands clearly
proud of the body: about 0.25 cm each side.
"""

W, D = 13.0, 8.5  # lid outline
CORNER = 1.35  # plan-view corner radius of the lid
BODY_H = 5.05  # body wall below the lid
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
