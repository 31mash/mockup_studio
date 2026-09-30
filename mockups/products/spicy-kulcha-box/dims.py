"""Spicy Kulcha matchbox pack, in cm, estimated from the spread.

A box is modelled with its long axis along x. The printed sleeve is a
paperboard tube (label on top, striker panels on the long sides); the white
card tray slides out towards +x, the end where 'KULCHA' sits on the label. The
label is a portrait layout whose top ('SPICY') points to -x. product.py then
turns each box a quarter turn, so in the scene the tray comes out towards the
camera (-Y) and the label reads upright from the front.
"""

# Sleeve (outer)
L = 13.4  # length, x
W = 8.0  # width, y
H = 3.8  # height, z
T = 0.045  # board thickness
FOLD_R = 0.12  # outer radius of the four long creases
MARGIN = 0.3  # plain card around the printed label on the sleeve top

# Label (portrait, on the sleeve top): top = -x
LABEL_W = W - 2 * MARGIN  # 7.4, across y
LABEL_H = L - 2 * MARGIN  # 12.8, along x

# Striker panels on the long sides
STRIKER_X = 0.4  # plain card left at each end
STRIKER_Z = 0.36  # plain card above and below

# Tray (outer), a close sliding fit inside the sleeve
TL = L - 0.12
TW = W - 2 * T - 0.07
TH = H - 2 * T - 0.06
TT = 0.055  # tray wall (card) thickness
TB = 0.045  # tray floor thickness

# How far the tray is slid out, per box
PULL = {'red': 5.0, 'green': 5.2, 'red-back': 4.2}

# The pair, as in the spread: box centres in the scene (x, y). The red box sits
# to the right of the green one and a little further back.
PAIR = {'green': (-5.0, -1.6), 'red': (5.0, 1.6)}

# Kulcha: one flatbread folded in half across the tray, the fold at the tray's
# far end (inside the sleeve), the rounded edges towards its open end
KULCHA_T = 1.2  # one layer of dough
KULCHA_GAP = 0.14  # inner radius of the fold (a little filling between the layers)
KULCHA_BACK = 0.1  # fold to the tray's far wall
KULCHA_FRONT = 1.2  # the lower layer's edge to the tray's open end
