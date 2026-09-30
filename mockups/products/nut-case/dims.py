"""Nut Case tin size, in cm, estimated from the reference render."""

W, D = 12.0, 9.4  # lid outline
CORNER = 1.15  # plan-view corner radius
BODY_H = 2.1  # body wall below the lid
LID_H = 1.55  # lid height
LID_EDGE = 0.3  # rounded top edge of the lid
BODY_EDGE = 0.25
WALL = 0.08  # lid overhang over the body
RIM = 1.05  # green rim on the lid top, including the rounded edge
PANEL_R = 0.95


def body_outline():
    inset = WALL + 0.04
    return W - 2 * inset, D - 2 * inset, max(0.1, CORNER - inset)
