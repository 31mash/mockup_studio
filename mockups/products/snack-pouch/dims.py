"""IndiGo namkeen pouch: a clear stand-up zip pouch (doypack) with a bottom
gusset, filled with namkeen sticks. Sizes in cm, estimated from the spread
(the pouch is about 0.70 as wide as it is tall) and the common 125 x 180 mm
doypack size."""

# Flat film panel (front and back are the same size).
W = 12.5  # flat width
H = 18.0  # flat height of a panel
SEAL = 0.7  # side seal width
TOP_SEAL = 1.0  # heat seal along the top edge
ZIP = 2.7  # zip centre, measured down from the top edge
ZIP_GAP = 0.42  # distance between the two zip tracks
NOTCH = 1.75  # tear notches, measured down from the top edge
BOTTOM_SEAL = 0.5  # the band where the panel is sealed to the gusset
GUSSET_CURVE = 3.2  # height of the gusset's curved corner seal at the side

# Standing, filled shape.
Z_TOP = 17.55  # standing height (the bulge takes up a little of H)
BOTTOM_R = 0.75  # rounded edge where the panels turn under into the gusset
FILL = 13.1  # mean height of the namkeen inside
FILM = 0.004  # half the film gap at the seals (two layers sealed together)

# Half-depth of the pouch at the middle of its width, by height (z, half-depth).
# Plump at the gusset, easing off towards the fill line, nearly flat at the zip.
DEPTH = [
    (0.0, 2.05),
    (1.4, 2.15),
    (4.0, 2.1),
    (7.0, 1.95),
    (10.0, 1.72),
    (12.0, 1.42),
    (13.3, 1.0),
    (14.3, 0.55),
    (15.0, 0.28),
    (15.8, 0.1),
    (16.4, 0.02),
    (16.55, FILM),
    (Z_TOP, FILM),
]

# Namkeen sticks: thick, crinkly fried gram-flour sticks.
STICK_R = (0.17, 0.235)  # radius range
STICK_L = (1.3, 4.2)  # length range
