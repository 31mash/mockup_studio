"""DaBlue Burger clamshell size, in cm, measured off the spread photo and
scaled to a single-burger clamshell 11 cm across.

Rectifying the photo's walls and top (a homography on each panel's corners)
and matching a render from the photo's own viewpoint gives: the flat top
spans about 77% of the lid's width at its bottom edge, the lid walls rise
about 0.6 times the top's width, and only a narrow band of the base shows
below the lid.

The closed box has a hexagonal side profile: a flat square top, lid walls
that flare out down to the parting line (the widest point), and a short base
tray whose walls slope back in to a smaller footprint. Above the parting
line the base's walls turn up into a flange that sits just inside the lid.
The lid's two front corners are notched at the bottom, as in the photo.
"""

import math

W = 11.0  # lid outline at its bottom edge (the widest point)
TOP = 8.5  # flat top panel
H = 6.1  # overall height
Z_PART = 1.1  # height of the parting line (the lid's bottom edge)
BASE = 8.9  # base footprint
FLANGE = 0.8  # base flange reaching up inside the lid
BOARD = 0.045  # paperboard thickness (about 450 micron)
FOLD_R = 0.06  # radius of the creased folds
CLEAR = 0.025  # clearance between the base flange and the lid's inside
NOTCH_W, NOTCH_H = 0.5, 0.75  # V-notch at the lid's front corners (its top stays below the flange top)

# Lid walls.
A0, A1 = W / 2, TOP / 2
LID_RISE = H - Z_PART
LID_SLANT = math.hypot(A0 - A1, LID_RISE)
LID_TAPER = (A0 - A1) / LID_RISE  # inset per cm of height
LID_T_H = BOARD / math.cos(math.atan(LID_TAPER))  # board thickness, measured level

# Base walls: sloped up to the parting line, then a flange parallel to the lid.
C0 = BASE / 2
CK = A0 - LID_T_H - CLEAR  # at the parting line
Z_BASE_TOP = Z_PART + FLANGE
C1 = CK - LID_TAPER * FLANGE  # flange top
BASE_SLOPE = (CK - C0) / Z_PART
BASE_LOWER = Z_PART * math.hypot(1, BASE_SLOPE)  # slant of the visible wall
BASE_FLANGE = FLANGE * math.hypot(1, LID_TAPER)
BASE_SLANT = BASE_LOWER + BASE_FLANGE  # artwork height, flange at the top
