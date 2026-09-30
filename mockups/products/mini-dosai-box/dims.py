"""Mini Dosai box sizes, in cm, measured from source/crops/mini-dosai-boxes.png
(sleeve 280 x 435 px, drawer out 135 px) at a typical snack-box width.

A matchbox-style pack: a printed cream sleeve (a paperboard tube open at both
ends) lying flat, printed face up, and a white card drawer pulled out towards
the front (-Y). The drawer holds an aluminium foil tray with a folded dosa.

Pure Python: make_art.py uses it without Blender.
"""

import math

# ---------------------------------------------------------------- sleeve
W = 8.5  # across (x)
L = 13.2  # long axis (y); the front end (-Y) is where the drawer comes out
H = 3.0  # thickness (z)
T = 0.05  # board caliper
R = 0.11  # outer radius of the four long folds
FOLD_SEG = 8

# ---------------------------------------------------------------- drawer
CLEAR = 0.035  # play between drawer and sleeve, each side
DW = W - 2 * T - 2 * CLEAR  # drawer outside width
DH = H - 2 * T - 2 * CLEAR  # drawer outside height
DL = L - 0.1  # drawer length
DWALL = 0.09  # drawer walls are folded board, double thickness
OUT = 4.0  # how far the drawer is pulled out beyond the sleeve's front end

# ---------------------------------------------------------------- foil tray
TRAY_GAP = 0.08  # between tray rim and drawer wall
FLANGE = 0.34  # flat rim, outward from the top of the wall
BEAD = 0.07  # rolled edge radius
TRAY_W = DW - 2 * DWALL - 2 * TRAY_GAP  # rim outline, outside of the bead
TRAY_L = DL - 2 * DWALL - 2 * TRAY_GAP
TRAY_H = 2.45  # floor to rim
TRAY_DRAFT = 0.42  # wall slope: the floor is this much smaller on each side
TRAY_R = 1.0  # plan corner radius at the rim (outside of the flange)

# ---------------------------------------------------------------- dosa parcels
DOSA_W = 6.4
DOSA_L = 3.3
DOSA_H = 1.55
DOSA_COUNT = 3


def sleeve_layout(w=W, h=H, r=R):
    """Where each panel of the sleeve's print lands along its wrap strip.

    The strip runs once around the sleeve's cross-section, starting at the
    centre of the bottom panel and heading towards -X: bottom (left half),
    left side (going up), top (left to right), right side (going down),
    bottom (right half). v runs along the sleeve, the image's top being the
    back end (+Y). Returns spans in cm, and 'length' (the strip width)."""
    arc = math.pi * r / 2
    fb, fs, ft = w / 2 - r, h - 2 * r, w - 2 * r
    out = {}
    u = 0.0
    out['bottom_a'] = (u, u + fb)
    u += fb + arc
    out['left'] = (u, u + fs)
    u += fs + arc
    out['top'] = (u, u + ft)
    u += ft + arc
    out['right'] = (u, u + fs)
    u += fs + arc
    out['bottom_b'] = (u, u + fb)
    u += fb
    out['length'] = u
    return out
