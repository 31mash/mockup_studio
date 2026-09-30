"""Bunji!: IndiGo's kraft paper bag for its buns. An open SOS bag (square
bottom, side gussets) with a pinked top edge, printed on the front in two
inks: a red rule frame, 'Bunji!' in heavy brush italic with a red offset
shadow, a vintage engraved pugilist and a short paragraph."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402
import sos_bag  # noqa: E402

TITLE = 'Bunji! paper bag'
SHOTS = ['hero', 'hero-right', 'front', 'side', 'high', 'top', 'low']


def build(ctx):
    m, s = ctx.mat, ctx.shapes
    front = m.kraft('bunji front', art=ctx.art('front.png'), color=dims.KRAFT)
    back = m.kraft('bunji back', art=ctx.art('back.png'), color=dims.KRAFT)
    plain = m.kraft('bunji kraft', color=dims.KRAFT)
    inside = m.kraft('bunji inside', color=dims.KRAFT_INSIDE)
    walls = sos_bag.build_walls('bunji-bag', {'front': front, 'plain': plain, 'back': back, 'inside': inside, 'edge': plain})

    # The square bottom: two plies of kraft lying flat inside the walls.
    inner = dims.PAPER + 0.003
    base = s.walled_shell(
        'bunji-bag-bottom',
        s.rounded_rect(dims.W - 2 * inner, dims.D - 2 * inner, dims.FOLD_R, seg=4),
        0.0,
        2 * dims.PAPER,
        mats=(inside, inside, plain, None),
    )
    return [walls, base]
