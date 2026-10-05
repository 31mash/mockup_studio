"""Bunji! bag size, in cm, estimated from the spread (the front panel's
corners rectified to a flat rectangle) and a standard SOS bag."""

W, D, H = 12.5, 8.0, 20.0  # front width, gusset depth, height
PAPER = 0.012  # kraft thickness (about 80 gsm)
FOLD_R = 0.07  # radius of the folded corners and the gusset crease

# Open mouth: the pinked (zigzag) top edge, and the gussets folding inward
# towards the top, which pulls the front and back panels together.
PINK_PERIOD = 0.2
PINK_DEPTH = 0.07
GUSSET_START = D / 2  # the gusset lies flat below its bottom creases (the square bottom holds it)
CREASE_Z = 17.3  # a crease where the top was once folded over
GUSSET_IN_CREASE = 1.35  # how far the gusset's centre fold is pushed in at the crease
GUSSET_IN_TOP = 2.85  # ... and at the top edge

# Paper colours: the kraft outside (print multiplies over it) and the
# slightly smoother, lighter inside.
KRAFT = '#c3a372'
KRAFT_INSIDE = '#c9aa7a'

# Front print, in cm from the front panel's top-left corner.
FRAME = (0.65, 6.0, 11.2, 11.75)  # x, y, w, h of the frame's outer edge
BAND = 0.27  # frame band width (the rope rule)
# 'Bunji!': baseline start (from the frame's outer corner), font size, how
# steeply the baseline climbs (a shear, so stems keep their forward lean)
# and a slight widening towards the hand-lettered original's broad letters.
LETTER_AT = (0.95, 4.72)
LETTER_SIZE = 2.02
LETTER_RISE = 20
LETTER_WIDEN = 1.08
LETTER_UNSLANT = 6
# The paragraph: 'No.' baseline (from the frame's corner), size and leading.
COPY_AT = (1.0, 5.95)
COPY_SIZE = 0.245
COPY_LEAD = 0.30
SEAM_X = 3.4  # glue seam on the back, from the back's left edge seen from behind
