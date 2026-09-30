"""Gadget tin size, in cm, estimated from the spread (source/crops/gadget-tin.png).

A rectangular slip-lid tin: a tall body with a short lid. Proportions come from
the photo (the round pocket watch on the lid and the iPod's round control pad
on the body fix the foreshortening): about 13 x 8.6 cm in plan, 4.4 cm of body
below a 1.85 cm lid.
"""

W, D = 13.0, 8.6  # lid outline
CORNER = 1.35  # plan-view corner radius of the lid
BODY_H = 4.4  # body wall below the lid
LID_H = 1.85  # lid, from the body's top edge to the top of the lid
LID_EDGE = 0.55  # rounded top edge of the lid
BODY_EDGE = 0.3  # rounded bottom edge of the body
WALL = 0.08  # lid overhang over the body

BLUE = '#8ac4ea'  # printed sky blue (photo samples #8cc7ea to #91c9ed under light)
WHITE = '#fdfefe'  # opaque white ink


def body_outline():
    inset = WALL + 0.04
    return W - 2 * inset, D - 2 * inset, max(0.1, CORNER - inset)
