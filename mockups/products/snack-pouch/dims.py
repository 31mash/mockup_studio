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
# Round and full over the opened gusset, easing off towards the fill line,
# pinched shut at the zip (its two profiles locked together, about 1.5 mm
# thick) and flat across the sealed header above it.
DEPTH = [
    (0.0, 2.7),
    (1.2, 2.9),
    (2.8, 2.65),
    (4.5, 2.2),
    (7.0, 2.0),
    (10.0, 1.75),
    (12.0, 1.42),
    (13.3, 1.0),
    (14.1, 0.45),
    (14.6, 0.16),
    (Z_TOP - ZIP, 0.075),
    (15.4, 0.05),
    (16.4, 0.02),
    (16.55, FILM),
    (Z_TOP, FILM),
]
# Below GUSSET_Z the depth comes from the gusset film, not from the front
# panel, so the side seals do not pull in further there (the print is blank).
GUSSET_Z = (2.6, 4.3)

# Namkeen sticks: crinkly fried gram-flour sticks, 4 to 5 mm thick and up to
# 5 cm long in the photo (the longest lie across a third of the pouch).
STICK_R = (0.19, 0.245)  # radius range
STICK_L = (2.6, 5.0)  # length range, whole sticks
STICK_L_SHORT = (1.2, 2.3)  # broken pieces
