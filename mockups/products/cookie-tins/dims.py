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
TEXT_SIZE = 0.60  # font size, cm: the sentence (44.7 em) runs 26.8 cm of the 28.2 cm round

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
# of the sentence, at TEXT_SIZE on the CIRC round.
SET_TURNS = (105.6, -16.5, -116.6)
# A single tin is shown the way the spread shows its first one: the sentence
# starts near the left edge ('For the first time in the history of'). For a
# camera at azimuth a the body turns by PHOTO_TURN - a, so every angle sees
# that same stretch of the sentence.
PHOTO_TURN = SET_TURNS[0]
# Body shoulder under the lid curl: the wall rounds inwards to the neck with
# this radius, leaving the dark crease under the curl seen in the photo.
SHOULDER_R = 0.07

# Open tin: the lid stands on its edge in front and to the right of the tin,
# top outwards, leaning back on the tin's rim.
OPEN_LID_BEARING = 9.0  # degrees from the front, towards +X
OPEN_LID_LEAN = 24.0  # degrees back from vertical
OPEN_LID_TURN = 14.0  # lid turned in its own plane so the flavour reads level to the hero camera
