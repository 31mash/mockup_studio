"""Chandni Chowk samosa bag and samosa: sizes in cm, estimated from the
spread (the bag's printed columns, the stamp and the samosa beside it) and a
typical street-food newspaper bag (lifafa).

The bag lies flat on its back, printed face up, its bottom edge towards the
camera (-Y) and the top folded over once towards the front (+Y end).
"""

import math

# ---------------------------------------------------------------- the bag
W = 13.5  # flat width of the bag
L = 18.8  # bottom edge to the top fold
F = 1.3  # depth of the folded-over flap, measured from the fold
PAPER = 0.012  # newsprint: two layers at the edges, but thin
FOLD_R = 0.07  # outer radius of the top fold (four layers of paper)
FOLD_ARC = math.pi * FOLD_R * 0.75  # paper used by the fold's visible arc

PUFF = 2.1  # how far the samosa inside lifts the front panel, at its peak (see bag.SUPPORT)
EDGE_Z = 0.26  # the folded edges ride this far off the floor
BELLY = 0.22  # fraction of the half-width over which the back panel reaches the floor

# ---------------------------------------------------------------- the samosa
SAMOSA_R = 5.0  # base: distance from the centre to a corner (sides about 8.7 cm)
SAMOSA_H = 6.3  # to the tip
SAMOSA_AT = (-13.4, -4.0, 10.0)  # x, y, rotation (deg): in the hero the front-left fold is just left of the lens,
#   so one broad face turns to the key light and the other falls into shade; the seam is at the back
