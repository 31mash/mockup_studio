"""IndiGo paper napkin, in cm, estimated from the spread (source/crops/napkin.png).

The photo shows an offset-folded napkin lying flat: a top flap that stops
about 1.5 cm short of the layer beneath it, whose front edge is a torn
perforation (deckled). Construction, as a folding machine would do it:

    sheet SHEET_W x SHEET_H, printed side up
    fold 1: the right half over the left, along u = W   -> right edge of the pack
    fold 2: the back part (v > D) down over the front, along v = D -> back edge

So the pack is W x D with four layers: two in the base (their torn front edge
shows at the front) and two in the flap, which is DT deep. The Hindi line sits
on the flap, near its free (front) edge.
"""

W = 15.4  # folded width, left edge (free edges) to right edge (fold 1)
D = 10.5  # base depth: back edge (fold 2) to the torn front edge
DT = 8.9  # flap depth: back edge to the flap's free edge
SHEET_W = 2 * W  # the unfolded sheet
SHEET_H = D + DT

LAYER = 0.036  # spacing between stacked layers (2-ply embossed tissue, lofted)
PLY = 0.014  # modelled paper thickness (Solidify)
SKEW = 0.008  # fold 1 is a touch out of square, as on a real napkin

DECKLE = 0.26  # depth of the torn perforation along the base's front edge (wave + jaggies + bites)

# The printed line, measured on the photo relative to the flap.
TEXT_LEFT = 1.45  # from the flap's left edge
TEXT_BASELINE = 1.55  # above the flap's free edge
TEXT_WIDTH = 9.5  # the whole line

# Embossed pattern: overlapping rings of dots all over the sheet.
RING_R = 2.35
RING_PITCH = 4.5
DOT_PITCH = 0.3
