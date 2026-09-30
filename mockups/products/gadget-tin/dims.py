"""Gadget tin size, in cm, estimated from the spread (source/crops/gadget-tin.png).

A rectangular slip-lid tin: a tall body under a short lid. The round pocket
watch on the lid and the iPod's round control pad on the body fix the photo's
foreshortening; with the width taken as 13 cm that gives a depth of about
8.5 cm, 4.8 cm of body below the lid and a 2 cm lid.
"""

W, D = 13.0, 8.5  # lid outline
CORNER = 1.35  # plan-view corner radius of the lid
BODY_H = 4.8  # body wall below the lid
LID_H = 2.0  # lid, from the body's top edge to the top of the lid
LID_EDGE = 0.55  # rounded top edge of the lid
BODY_EDGE = 0.3  # rounded bottom edge of the body
WALL = 0.08  # lid overhang over the body

BLUE = '#8ac4ea'  # printed sky blue (the photo samples #8cc7ea to #91c9ed under light)
WHITE = '#fdfefe'  # opaque white ink


def body_outline():
    inset = WALL + 0.04
    return W - 2 * inset, D - 2 * inset, max(0.1, CORNER - inset)
