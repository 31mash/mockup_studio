"""IndiGo namkeen pouch: a clear stand-up zip pouch with a bottom gusset,
printed in white ink with the story of the namkeen maker, filled with thick
crinkly namkeen sticks."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402,F401
import film  # noqa: E402
import food  # noqa: E402
import pouch  # noqa: E402

TITLE = 'Namkeen pouch'
SHOTS = ['hero', 'hero-right', 'front', 'side', 'low']


def build(ctx, variant=None):
    m = ctx.mat
    seals = ctx.art('seals.png')
    front_m = film.sheet(m, 'film-front', ctx.art('front.png'), seals)
    back_m = film.sheet(m, 'film-back', ctx.art('back.png'), seals)
    base_m = film.sheet(m, 'film-base')
    front, back, base = pouch.build_film(front_m, back_m, base_m)
    zip_m = film.milky(m, 'zip', veil=0.42)
    edge_m = film.milky(m, 'film-edge', veil=0.55, rim=0.35)
    zips = pouch.build_zip(zip_m, front, back)
    edges = pouch.build_edges(front, edge_m)
    food.build(m)
    return [front, back, base] + zips + [edges]
