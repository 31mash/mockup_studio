"""Smoked Almonds tin size, in cm, estimated from the spread.

The photo shows the tin from the front, about 33 degrees up (the lid top is an
ellipse 0.54 as deep as it is wide). Heights below are measured down the front
of the tin against the lid's width, taken as 10 cm, a common size for a 100 g
round slip-lid tin, and corrected for the view angle: from the lid's top edge
to the floor, the lid wall takes 40 %, the shadow and bead under it 9 %, the
body 38 % and the bottom seam 13 %.
"""

R = 5.0  # lid outer radius
HEIGHT = 2.5  # overall, lid on
BODY_H = 1.34  # floor to the silver bead at the lid line
LID_GAP = 0.12  # bead centre to the lid's open edge (lid wall about 1.0 cm)
LID_EDGE = 0.2  # rounded top edge of the lid
WALL = 0.08  # lid overhang over the body
BODY_R = R - WALL - 0.04  # body wall radius
BEAD_TUBE = 0.075  # rolled bead just under the lid
SEAM_H = 0.3  # rolled bottom seam
SEAM_PROUD = 0.035  # how far the seam stands out from the body wall

# Printed lid top (radii from the tin's centre).
RING_R = R - 0.33  # thin bronze ring near the edge
ART_R = R - 0.44  # the almond illustration stays inside this
