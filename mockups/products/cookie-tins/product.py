"""IndiGo reusable cookie tins: round slip-lid tins in pale cyan (Chocolate chip)
and pink (Oatmeal + Honey). The lid carries the white dotted plane and the
flavour; one white sentence runs round the body. Gold curl at the lid's edge
and a gold double seam at the foot, as in the spread."""

import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402
import tin  # noqa: E402

TITLE = 'IndiGo cookie tins'
# Single-tin variants are 'flavour/preset': the body is turned for that
# camera so the sentence starts near the tin's left edge, as on the spread's
# first tin (see dims.PHOTO_TURN).
SHOTS = [
    {'name': 'hero', 'variant': 'chocolate-chip/hero'},
    {'name': 'hero-right', 'variant': 'chocolate-chip/hero-right'},
    {'name': 'front', 'variant': 'chocolate-chip/front'},
    {'name': 'top', 'variant': 'chocolate-chip/top'},
    {'name': 'oatmeal-hero', 'preset': 'hero', 'variant': 'oatmeal-honey/hero'},
    {'name': 'set-hero', 'preset': 'hero', 'variant': 'set', 'fill': 0.66},
    {'name': 'set-front', 'preset': 'front', 'variant': 'set', 'fill': 0.72},
    {'name': 'open', 'preset': 'hero', 'elevation': 42, 'variant': 'open', 'fill': 0.6},
]
VARIANTS = [None] + [f'{f}/{v}' for f in ('chocolate-chip', 'oatmeal-honey') for v in ('hero', 'hero-right', 'front', 'top')] + ['set', 'open']


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


def materials(ctx, flavour, cache):
    """The tin's materials, made once per build (core.reset() frees them)."""
    m = ctx.mat
    if 'gold' not in cache:
        # Gold-lacquered tinplate: the lid curl, bottom seam and inside.
        cache['gold'] = m.bare_metal('gold lacquer', color='#d3bf8a', roughness=0.26)
    if flavour not in cache:
        lid = m.printed_metal(f'lid {flavour}', art=ctx.art(f'lid-{flavour}.png'), roughness=0.3, coat=0.25)
        body = m.printed_metal(f'body {flavour}', art=ctx.art(f'body-{flavour}.png'), roughness=0.3, coat=0.25)
        # The wrap strip meets itself at the front centre: sample across it.
        for node in body.node_tree.nodes:
            if node.type == 'TEX_IMAGE':
                node.extension = 'REPEAT'
        cache[flavour] = (lid, body)
    lid, body = cache[flavour]
    return lid, body, cache['gold']


def one_tin(ctx, cache, flavour, name, x=0.0, y=0.0, turn=0.0):
    """A closed tin standing on z = 0 at (x, y). `turn` rotates the body (in
    degrees, counter-clockwise from above) to bring another stretch of the
    sentence to the front; the lid always keeps its artwork upright."""
    lid_m, body_m, gold = materials(ctx, flavour, cache)
    b = tin.body(f'{name}-body', [body_m, gold])
    li = tin.lid(f'{name}-lid', [lid_m, gold])
    b.rotation_euler.z = math.radians(turn)
    for o in (b, li):
        o.location.x, o.location.y = x, y
    return [b, li]


def open_tin(ctx, cache):
    """The Chocolate chip tin opened: the lid stands on its edge, leaning on
    the tin's rim, and the top of a stack of cookies shows inside."""
    import cookies

    from studio import core

    b, li = one_tin(ctx, cache, 'chocolate-chip', 'tin', turn=presented(core.PRESETS['hero']['azimuth']))
    tin.lean_lid(li, bearing=dims.OPEN_LID_BEARING, alpha=dims.OPEN_LID_LEAN, tilt_art=dims.OPEN_LID_TURN)
    dough = cookies.dough_material(ctx.mat)
    choc = cookies.chocolate_material(ctx.mat)
    objs = [b, li]
    # A stack of cookies fills the tin from its floor; the top two or three
    # show. Each is dropped onto the one below (a little off-centre, tipped).
    import random

    rng = random.Random(4)
    seeds = [21, 22, 23, 7, 3, 5]
    for k, seed in enumerate(seeds):
        top = k >= len(seeds) - 3
        parts = cookies.cookie(f'cookie{seed}', seed, (dough, choc), chips=15 if top else 6)
        loc = (rng.uniform(-0.45, 0.45), rng.uniform(-0.45, 0.45), 0.3 + 1.4 * k)
        cookies.place(parts[0], loc, (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)), rng.uniform(0, 6.28))
        cookies.settle(parts[0])
        objs += parts
    return objs


def presented(azimuth):
    """Body turn that shows a camera at `azimuth` the sentence's start."""
    return dims.PHOTO_TURN - azimuth


def build(ctx, variant=None):
    from studio import core

    cache = {}
    if variant is None:
        variant = 'chocolate-chip/hero'
    if variant in ('chocolate-chip', 'oatmeal-honey'):
        variant += '/front'
    if '/' in variant:
        flavour, view = variant.split('/')
        return one_tin(ctx, cache, flavour, 'tin', turn=presented(core.PRESETS[view]['azimuth']))
    if variant == 'open':
        return open_tin(ctx, cache)
    if variant == 'set':
        # Cyan, pink, cyan in a row, as in the spread; each body turned so the
        # sentence reads on across the three fronts.
        step = 2 * dims.RL + dims.SET_GAP
        objs = []
        t1, t2, t3 = dims.SET_TURNS
        objs += one_tin(ctx, cache, 'chocolate-chip', 'left', x=-step, turn=t1)
        objs += one_tin(ctx, cache, 'oatmeal-honey', 'middle', x=0.0, turn=t2)
        objs += one_tin(ctx, cache, 'chocolate-chip', 'right', x=step, turn=t3)
        return objs
    raise ValueError(f'unknown variant {variant!r}')
