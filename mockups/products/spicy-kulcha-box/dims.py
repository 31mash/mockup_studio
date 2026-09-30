"""Spicy Kulcha matchbox pack, in cm, estimated from the spread.

The pack lies with its long axis along x. The printed sleeve is a paperboard
tube (label on top, striker panels on the long sides); the white card tray
slides out towards +x, the end where 'KULCHA' sits on the label. The label is
a portrait layout whose top ('SPICY') points to -x.
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
PULL = {'red': 5.0, 'green': 5.6, 'red-back': 3.7}

# Kulcha: one flatbread folded in half along x, fold at the back of the tray
KULCHA_T = 0.95  # one layer of dough
KULCHA_GAP = 0.12  # inner radius of the fold (a little filling between the layers)
