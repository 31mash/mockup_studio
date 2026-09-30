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
SHOTS = ['hero', 'hero-right', 'front', 'side', 'back', 'low']


def zip_plastic(m):
    """The zip profiles and the film's cut edge: milky, half-clear
    polyethylene. Transmission rather than transparency, so these thin lines
    render clean (opaque alpha)."""
    mat = m.solid('zip', '#f2f4f4', roughness=0.3)
    p = mat.node_tree.nodes['Principled BSDF']
    p.inputs['Transmission Weight'].default_value = 0.55
    p.inputs['IOR'].default_value = 1.5
    return mat


def build(ctx, variant=None):
    m = ctx.mat
    seals = ctx.art('seals.png')
    front_m = film.sheet(m, 'film-front', ctx.art('front.png'), seals)
    back_m = film.sheet(m, 'film-back', ctx.art('back.png'), seals)
    base_m = film.sheet(m, 'film-base')
    front, back, base = pouch.build_film(front_m, back_m, base_m)
    edge_m = zip_plastic(m)
    zips = pouch.build_zip(edge_m, front, back)
    edges = pouch.build_edges(front, edge_m)
    food.build(m)
    return [front, back, base] + zips + [edges]
