"""IndiGo cookie tin sizes, in cm, measured from the spread (source/crops/cookie-tins.png).

A round three-piece tea-caddy style tin: a printed body with a gold double seam
at the foot and a short neck at the top, and a slip lid, flush with the body,
with a rounded shoulder and a gold curl at its open edge. In the photo the
height is 0.93 of the lid diameter and the lid is 0.18 of the height; a 9 cm
tin holds about 200 g of cookies.
"""

import math

# Lid
RL = 4.50  # lid outer radius (9 cm across)
H = 8.40  # overall height, floor to lid top
LID_H = 1.60  # lid top to the centre of its curl
LID_SHOULDER = 0.30  # rounded top edge of the lid
CURL_R = 0.065  # tube radius of the curled open edge (it stands 1 mm proud)
T = 0.025  # tinplate thickness (0.25 mm)

# Body
RB = 4.485  # body radius: all but flush with the lid
RN = 4.43  # neck radius, hidden inside the lid
SEAM_H = 0.30  # bottom double seam height
SEAM_OUT = 0.10  # how far the seam stands proud of the body
BOTTOM_Z = 0.14  # recessed bottom panel, underside
INNER_BOTTOM_Z = 0.20  # inside floor of the tin

ZC = H - LID_H  # curl centre
Z_SHOULDER = ZC - CURL_R - 0.004  # body steps in to its neck just under the curl
Z_NECK = H - 0.30  # top of the neck (under the lid top)

# Artwork strip on the body: v = 0 at the seam top, v = 1 at the neck top.
ART_Z0 = SEAM_H
ART_Z1 = Z_NECK
CIRC = 2 * math.pi * RB  # wrap strip length

# Body sentence: centred at this height (the photo: a little below the middle
# of the visible wall).
TEXT_Z = ART_Z0 + 0.45 * (Z_SHOULDER - ART_Z0)
# Font size, cm. The photo measures about 0.60, but at that size the sentence
# (44.7 em) runs 26.8 cm of the 28.2 cm round, and its gap at the back (18
# degrees) is narrower than the stretch a camera sees beyond the edges of a
# tin: the set's end tins showed 'Enjoy.' or 'For' creeping round their
# edges. At 0.58 (3 % smaller, within the photo's measuring error) it runs
# 25.9 cm and leaves a 31 degree gap.
TEXT_SIZE = 0.58

# Lid top layout, as fractions of the lid diameter from the top-left of the
# lid seen from above (front edge at the bottom).
PLANE_W = 0.38
PLANE_CY = 0.398
LID_TEXT_SIZE = 0.074  # of the diameter: 0.67 cm, Comfortaa Bold ('Chocolate chip' spans 0.57 of it, 'cookies' 0.29)
LID_BASE1 = 0.765
LID_BASE2 = 0.848

# Set: three tins in a row, as in the spread.
SET_GAP = 1.0
# Body turns (degrees, counter-clockwise from above) that bring the spread's
# three stretches of the sentence to the fronts: 'For the first time in the
# history of' | 'of aviation, IndiGo presents reus' | 'reusable cookie tins.
# Enjoy'. Measured in Comfortaa: -13.78, +2.16 and +15.21 em from the middle
# of the sentence, at TEXT_SIZE on the body's round.
SET_EM = (-13.78, 2.16, 15.21)
SET_TURNS = tuple(-math.degrees(e * TEXT_SIZE / RB) for e in SET_EM)
# Every shot turns the bodies by (turn - camera azimuth), and the lids by
# -azimuth, so each camera sees the same stretch of the sentence and the lid
# artwork squared to the lens, as a photographer would set a round tin.

# A single tin: the sentence wraps 329 of the round's 360 degrees, so a tin
# turned to show its start ('For', as on the spread's first tin) either
# squeezes it against the left edge or shows the end ('Enjoy.') beside it. A
# single tin is turned like the spread's middle one instead, so its front
# reads 'history of aviation, IndiGo presents', centred between 'aviation,'
# and 'IndiGo' and running on round both edges. Measured in the rasterized
# strip: 'aviation,' spans -36 to -4 degrees from the sentence's middle and
# 'IndiGo' -1 to +23.
SINGLE_TURN = -6.0
# The open tin: its lid hides the right half of the front, so the body turns
# to end 'of aviation, IndiGo' just short of the lid's edge.
OPEN_TURN = -24.0
# The set keeps the spread's stretches, the first tin nudged so its 'For' is
# not squeezed against its edge (its 'Enjoy.' stays round the back) and the
# middle one less, so the sentence still reads on across the fronts.
SET_NUDGE = (10.0, 4.0, 0.0)
# Body shoulder under the lid curl: the wall rounds inwards to the neck with
# this radius, leaving the dark crease under the curl seen in the photo.
SHOULDER_R = 0.07

# Open tin: the lid stands on its edge in front and to the right of the tin,
# top outwards, leaning back on the tin's rim.
OPEN_LID_BEARING = 9.0  # degrees from the front, towards +X
OPEN_LID_LEAN = 24.0  # degrees back from vertical
OPEN_LID_TURN = 25.0  # lid turned in its own plane so the flavour reads about level to the open shot's camera
