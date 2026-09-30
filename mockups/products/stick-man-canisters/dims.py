"""Stick Man potato-stick canister sizes, in cm, measured from the spread
(source/crops/stick-man-canisters.png, about 43 px per cm at the cans' fronts).

A composite can: a paperboard tube wrapped in a printed paper label, closed by
two gold-lacquered tinplate ends double-seamed onto it. The top end is a
peel-off end: a gold ring (seam, countersink wall and flange) with a silver
foil membrane sealed onto the flange and a folded pull tab.

In the photo the paper shows 13.0 cm between the seams for a 7.3 cm tube
(559 x 314 px); each seam band is about 0.3 cm tall.

Positions on the label are given as an angle `th` in degrees from the front
centre, positive to the viewer's right (counter-clockwise seen from above),
and a depth `d` in cm down from the visible top edge of the paper (the lower
edge of the top seam).
"""

import math

# Can
R = 3.65  # paper tube outer radius (7.3 cm across)
H = 13.6  # overall height, floor to the top of the seam
SEAM_H = 0.30  # height of each double seam band
SEAM_R = 3.735  # seam outer radius: stands 0.85 mm proud of the paper
SEAM_LIP = 3.615  # the seam's curl tucks in under the paper's surface here
CHUCK_R = 3.47  # inside wall of the top seam (the countersink wall)
FLANGE_Z = 13.235  # top of the ring's flange, where the foil is sealed
APERTURE_R = 3.08  # the ring's open centre, under the foil
FOIL_R = 3.36  # sealed foil membrane radius
FOIL_DOME = 0.018  # the membrane bulges a touch over the aperture
TAB = (1.15, 0.85)  # folded pull tab, width x depth
TAB_AT = 135.0  # tab direction, degrees from the front, positive to the right (back right)
TAB_LIFT = 3.0  # the folded tab springs up from its fold, degrees
FOIL_SILVER = '#d8d9dc'  # unprinted foil
LID_PLANE_W = 1.55  # print on the foil: the dotted plane over 'Stick Man'
LID_PLANE_CY = -0.6  # plane centre, cm behind the lid centre
LID_TITLE_SIZE = 0.62
LID_TITLE_Y = 0.9  # baseline, cm in front of the lid centre
BOTTOM_PANEL_Z = 0.36  # recessed bottom panel, underside

# Paper tube: its ends hide inside the seams.
TUBE_Z0 = 0.24
TUBE_Z1 = H - 0.24
VIS_TOP = H - SEAM_H  # visible paper top (d = 0)
VIS_BOTTOM = SEAM_H  # visible paper bottom (d = 13.0)
LABEL_T = 0.012  # label thickness: its outer end overlaps the start at the back
LABEL_OVERLAP = 0.28  # overlap width, cm

# Artwork strip: covers the whole tube; u = 0 at the back (the label seam),
# running counter-clockwise seen from above, so the front centre is u = 0.5
# and the strip reads left to right across the front. v = 0 at TUBE_Z0.
CIRC = 2 * math.pi * R
ART_H = TUBE_Z1 - TUBE_Z0
ART_TOP_D = -(TUBE_Z1 - VIS_TOP)  # d at the top edge of the strip


def x_of(th):
    """Strip x in cm for an angle from the front (degrees, + to the right)."""
    return CIRC * (0.5 + th / 360.0)


def y_of(d):
    """Strip y in cm (down from the strip's top edge) for a depth d."""
    return d - ART_TOP_D


def arc(deg):
    return CIRC * deg / 360.0


# --- Label layout, measured from the photo (all three cans share it) -------

# The stick man, in cm around his torso centre (x right, y down). Six potato
# sticks with rounded ends: head, torso, two arms and two legs splayed 31
# degrees from vertical, like the Chinese character for person, twice.
STICK_W = 0.185
STICK_COLOUR = '#f0a646'  # mustard orange
FIG_D = 3.0  # torso centre depth
FIGURE = {
    #        centre x, centre y, length, degrees from vertical (+ = foot out to the right)
    'head': (0.0, -1.18, 0.63, 0.0),
    'torso': (0.0, 0.0, 1.45, 0.0),
    'armL': (-0.70, -0.08, 1.39, -31.0),
    'armR': (0.70, -0.08, 1.39, 31.0),
    'legL': (-0.60, 1.42, 1.41, -31.0),
    'legR': (0.60, 1.42, 1.41, 31.0),
}
FULL = ('head', 'torso', 'armL', 'armR', 'legL', 'legR')
CRUMB_D = 4.88  # a last crumb lies at foot level on the navy can
CRUMB = 0.22

# Title panel, left-aligned at the panel's angle.
TITLE_SIZE = 0.9  # 'Stick Man': 0.7 cm capitals, 4.46 cm long (a touch tighter than Comfortaa)
TITLE_SPACING = -0.0225  # letter spacing, cm
TITLE_EM = 5.16  # its width in Comfortaa, em (measured in Chromium)
TITLE_D = 4.63  # baseline
PLANE_D = 3.06  # dotted plane, centred over the title
PLANE_W = 1.45
SUB_SIZE = 0.41  # 'Potato Sticks Tomato': as long as the title
SUB_D = 5.19
SUB_EM = {'brown': 10.98, 'pink': 10.91, 'navy': 10.44}  # measured in Comfortaa
VEG = 0.34
POEM_SIZE = 0.315  # 'When he comes to his senses' runs 4.8 cm
POEM_D = 5.86  # first baseline
POEM_LEAD = 0.465  # twelve lines to d = 10.97
INGR_SIZE = 0.2
INGR_D = (11.55, 11.88, 12.21)

# Nutrition panel: set sideways, reading bottom to top.
NUTRI_W = 5.2  # along its lines (up the can)
NUTRI_H = 2.9  # across its lines (round the can)
NUTRI_D = 10.94  # bottom edge (the start of its lines)
NUTRI_SPLIT = 2.65  # rule between the table and the pack details
NUTRI_SIZE = 0.15
NUTRI_LEAD = 0.25

# Per can: label colours and where things sit round it (degrees from front).
CANS = {
    'brown': dict(
        paper='#5a3f2e', title='#a6d6ef', sub='#d4e7ee', poem='#a4c841', small='#eadccf', plane='#d9e9f0',
        flavour='Tomato', panel=-70.7, ingr=(-70.7, 0), nutri=156.0,
        figures=[(34.4 + 42.0 * k, FULL) for k in range(6)],
        crumbs=[],
    ),
    'pink': dict(
        paper='#e2416e', title='#ffffff', sub='#ffffff', poem='#ffd68a', small='#fde7ee', plane='#ffffff',
        flavour='Masala', panel=172.0, ingr=(172.0, 0), nutri=112.0,
        figures=[
            (-83.5, FULL),
            (-47.2, ('head', 'torso', 'armL', 'legL', 'legR')),
            (-11.2, ('head', 'torso', 'armL', 'legR')),
            (25.5, ('head', 'torso', 'legR')),
            (61.8, ('head', 'torso')),
            (98.1, ('head',)),
        ],
        crumbs=[],
    ),
    'navy': dict(
        paper='#3c3b5c', title='#a2c940', sub='#a2c940', poem='#95cbe8', small='#dedde8', plane='#dfe9ef',
        flavour='Salted', panel=72.0, ingr=(72.0, 0), nutri=-16.3,
        figures=[
            (-141.2, ('head', 'torso', 'legR')),
            (-104.5, ('head', 'torso')),
            (-67.8, ('head', 'torso')),
            (-30.4, ('head',)),
        ],
        crumbs=[4.2],
    ),
}

# Set: three cans in a row, as in the spread (centres 8.5 cm apart).
SET_STEP = 8.5
SET_ORDER = ('brown', 'pink', 'navy')
