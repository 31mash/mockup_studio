"""IndiGo reusable cookie tins: round slip-lid tins in pale cyan (Chocolate chip)
and pink (Oatmeal + Honey). The lid carries the white dotted plane and the
flavour; one white sentence runs round the body. Gold curl at the lid's edge
and a gold double seam at the foot, as in the spread."""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402
import tin  # noqa: E402

TITLE = 'IndiGo cookie tins'
# Single-tin variants are 'flavour/preset': the body is turned for that
# camera so its front reads 'history of aviation, IndiGo presents', and the
# lid so its artwork faces the lens squarely (see dims.SINGLE_TURN). A round
# tin set square to the lens looks the same from either side, so hero-right
# shows the other flavour rather than a mirror of hero.
SHOTS = [
    {'name': 'hero', 'variant': 'chocolate-chip/hero'},
    {'name': 'hero-right', 'variant': 'oatmeal-honey/hero-right'},
    {'name': 'front', 'variant': 'chocolate-chip/front'},
    {'name': 'top', 'variant': 'chocolate-chip/top'},
    {'name': 'set-hero', 'preset': 'hero', 'variant': 'set/hero', 'fill': 0.66},
    {'name': 'set-front', 'preset': 'front', 'variant': 'set/front', 'fill': 0.72},
    {'name': 'open', 'preset': 'hero', 'elevation': 42, 'variant': 'open', 'fill': 0.6},
]
VARIANTS = (
    [None]
    + [f'{f}/{v}' for f in ('chocolate-chip', 'oatmeal-honey') for v in ('hero', 'hero-right', 'front', 'top')]
    + ['set/hero', 'set/front', 'open']
)


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


def one_tin(ctx, cache, flavour, name, x=0.0, y=0.0, turn=0.0, lid_turn=0.0):
    """A closed tin standing on z = 0 at (x, y). `turn` rotates the body (in
    degrees, counter-clockwise from above) to bring another stretch of the
    sentence to the front; `lid_turn` rotates the lid, to square its artwork
    to a camera that is not straight in front."""
    lid_m, body_m, gold = materials(ctx, flavour, cache)
    b = tin.body(f'{name}-body', [body_m, gold])
    li = tin.lid(f'{name}-lid', [lid_m, gold])
    b.rotation_euler.z = math.radians(turn)
    li.rotation_euler.z = math.radians(lid_turn)
    for o in (b, li):
        o.location.x, o.location.y = x, y
    return [b, li]


def open_tin(ctx, cache):
    """The Chocolate chip tin opened: the lid stands on its edge, leaning on
    the tin's rim, and the top of a stack of cookies shows inside."""
    import cookies

    from studio import core

    b, li = one_tin(ctx, cache, 'chocolate-chip', 'tin', turn=dims.OPEN_TURN - core.PRESETS['hero']['azimuth'])
    tin.lean_lid(li, bearing=dims.OPEN_LID_BEARING, alpha=dims.OPEN_LID_LEAN, tilt_art=dims.OPEN_LID_TURN)
    dough = cookies.dough_material(ctx.mat)
    choc = cookies.chocolate_material(ctx.mat)
    objs = [b, li]
    # A stack of cookies fills the tin from its floor; the top two or three
    # show. Each is dropped onto the one below (a little off-centre, tipped).
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


def build(ctx, variant=None):
    from studio import core

    cache = {}
    if variant is None:
        variant = 'chocolate-chip/hero'
    if variant in ('chocolate-chip', 'oatmeal-honey', 'set'):
        variant += '/front'
    if variant == 'open':
        return open_tin(ctx, cache)
    what, view = variant.split('/')
    # A camera at azimuth a sees the tin as the front camera would once the
    # body and lid turn by -a.
    az = core.PRESETS[view]['azimuth']
    if what == 'set':
        # Cyan, pink, cyan in a row, as in the spread; each body turned so the
        # sentence reads on across the three fronts.
        step = 2 * dims.RL + dims.SET_GAP
        tins = (('chocolate-chip', 'left', -step), ('oatmeal-honey', 'middle', 0.0), ('chocolate-chip', 'right', step))
        objs = []
        for (flavour, name, x), t, nudge in zip(tins, dims.SET_TURNS, dims.SET_NUDGE):
            objs += one_tin(ctx, cache, flavour, name, x=x, turn=t + nudge - az, lid_turn=-az)
        return objs
    if what in ('chocolate-chip', 'oatmeal-honey'):
        return one_tin(ctx, cache, what, 'tin', turn=dims.SINGLE_TURN - az, lid_turn=-az)
    raise ValueError(f'unknown variant {variant!r}')
