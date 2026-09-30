"""IndiGo food posters, in cm.

Both posters measure 0.673 wide per unit of height in the spread, a touch
narrower than A-series paper (0.707): 40 x 59.4 cm matches that exactly
(an A2 height on a 40 cm web). Printed on heavy matte card.
"""

W, H = 40.0, 59.4  # trimmed sheet
T = 0.05  # 0.5 mm card

# Standing: the sheet stands on its bottom edge, bowed very slightly along its
# width (as a heavy card does when it has been rolled), and leans back a hair.
BOW = 1.1  # sagitta of the bow across the width
LEAN = 1.5  # degrees, top away from the viewer

# Print colours (sampled flat from the spread, which reproduces the Nut Case
# tin's blue within a few levels, so it is close to true).
POSTER_BLUE = '#1f419b'
PAPER_WHITE = '#fbfbf8'  # unprinted card: the white type is the paper
CARD_BACK = '#f1f0eb'
CARD_EDGE = '#e9e7e0'
