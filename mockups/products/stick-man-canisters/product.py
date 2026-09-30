"""IndiGo 'Stick Man' potato-stick canisters: three composite cans (chocolate
brown, magenta pink and deep navy) with gold double-seamed tinplate ends, a
silver peel-off foil under the top seam, and printed paper labels on which a
parade of potato-stick men gets eaten from can to can.

Variants: 'brown', 'pink', 'navy', and 'set' (the three in a row, as in the
spread). A variant may end in '@<azimuth>': the can (or each can of the set)
is turned so the label front measured from the spread faces a camera at that
azimuth, so a hero shot shows the same stretch of label as the photo.
"""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import can  # noqa: E402
import dims  # noqa: E402

TITLE = 'Stick Man potato-stick canisters'
SHOTS = [
    {'name': 'hero', 'preset': 'hero', 'variant': 'brown@31'},
    {'name': 'hero-right', 'preset': 'hero-right', 'variant': 'brown'},
    {'name': 'front', 'preset': 'front', 'variant': 'brown'},
    {'name': 'pink-hero', 'preset': 'hero', 'variant': 'pink@31'},
    {'name': 'navy-hero', 'preset': 'hero', 'variant': 'navy@126'},
    {'name': 'set-hero', 'preset': 'hero', 'variant': 'set@31', 'fill': 0.66},
    {'name': 'set-front', 'preset': 'front', 'variant': 'set', 'fill': 0.74},
    {'name': 'set-top', 'preset': 'top', 'variant': 'set', 'fill': 0.72},
]
VARIANTS = ['brown', 'pink', 'navy', 'set']


@bpy.app.handlers.persistent
def _forget_light_target(*_):
    """studio.core caches its light-target empty in core._ORIGIN, and
    core.reset() frees that object; when render.py rebuilds the scene for the
    next variant, core.studio() would trip over the stale reference. Clearing
    the cache after each reset avoids that without touching the studio."""
    from studio import core

    core._ORIGIN = None


for _h in (bpy.app.handlers.load_factory_startup_post, bpy.app.handlers.load_post):
    if not any(getattr(f, '__name__', '') == '_forget_light_target' for f in _h):
        _h.append(_forget_light_target)


def materials(ctx, colour, cache):
    m = ctx.mat
    if 'gold' not in cache:
        # Gold-lacquered tinplate ends, as in the photo.
        cache['gold'] = m.bare_metal('gold lacquer', color='#cdb67c', roughness=0.24)
        # The pull tab: the membrane's unprinted foil, folded back. Peel-off
        # foils carry a heat-seal lacquer: a soft satin silver, not a mirror
        # (a mirror would blow out under the overhead softbox in a top view).
        cache['foil'] = m.printed_metal('peel foil', color='#d6d7da', roughness=0.36, coat=0.1, metallic=0.55)
    if colour not in cache:
        paper = m.board(f'label {colour}', art=ctx.art(f'label-{colour}.png'), roughness=0.42, coat=0.14, tooth=0.025)
        # The membrane: printed foil. Ink on foil stays metallic, tinted.
        lid = m.printed_metal(f'foil {colour}', art=ctx.art(f'lid-{colour}.png'), roughness=0.36, coat=0.1, metallic=0.55)
        cache[colour] = (paper, lid)
    paper, lid = cache[colour]
    return paper, lid, cache['gold'], cache['foil']


def one_can(ctx, cache, colour, x=0.0, face=0.0):
    """A closed can standing on z = 0 at (x, 0). `face` is the camera azimuth
    the label's front should face (degrees, + towards the product's left)."""
    paper, lid, gold, foil = materials(ctx, colour, cache)
    body = [
        can.paper_tube(f'{colour}-label', paper),
        can.top_ring(f'{colour}-top-ring', gold),
        can.bottom_end(f'{colour}-bottom', gold),
    ]
    bpy.ops.object.empty_add(location=(x, 0.0, 0.0))
    pivot = bpy.context.object
    pivot.name = f'{colour}-can'
    pivot.rotation_euler.z = math.radians(-face)
    for p in body:
        p.parent = pivot
    # The end is seamed on at no particular turn, so its printed foil keeps
    # facing the front (-Y) like the Nut Case lid, whichever way the label turns.
    top = [can.foil(f'{colour}-foil', lid), can.pull_tab(f'{colour}-tab', foil)]
    for p in top:
        p.location.x += x
    return body + top


def build(ctx, variant=None):
    name, _, face = (variant or 'brown').partition('@')
    face = float(face) if face else 0.0
    cache = {}
    if name == 'set':
        objs = []
        for i, colour in enumerate(dims.SET_ORDER):
            objs += one_can(ctx, cache, colour, x=(i - 1) * dims.SET_STEP, face=face)
    elif name in dims.CANS:
        objs = one_can(ctx, cache, name, face=face)
    else:
        raise ValueError(f'unknown variant {variant!r}')
    bpy.context.view_layer.update()
    return objs
