"""IndiGo food posters: 'Thought for food' and 'Say no to airline food',
printed on heavy matte card (40 x 59.4 cm, 0.5 mm).

Variants: each poster alone, standing on its bottom edge, bowed very slightly
across its width and leaning back a hair ('thought-for-food', 'say-no');
'set' stands both side by side; 'flatlay' lays them on the floor with the
residual curl of rolled card, 'say-no' resting over the other's margin."""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402
import sheet  # noqa: E402

TITLE = 'IndiGo food posters'
SHOTS = [
    {'name': 'hero', 'preset': 'hero', 'variant': 'thought-for-food', 'fill': 0.52},
    {'name': 'front', 'preset': 'front', 'variant': 'thought-for-food'},
    {'name': 'hero-right', 'preset': 'hero-right', 'variant': 'say-no', 'fill': 0.52},
    {'name': 'front-say-no', 'preset': 'front', 'variant': 'say-no'},
    {'name': 'set-hero', 'preset': 'hero', 'variant': 'set'},
    {'name': 'flatlay', 'preset': 'top', 'variant': 'flatlay', 'fill': 0.6},
    {'name': 'flatlay-high', 'preset': 'high', 'variant': 'flatlay', 'fill': 0.6},
]
VARIANTS = ['thought-for-food', 'say-no', 'set', 'flatlay']
POSTERS = ('thought-for-food', 'say-no')

# Flat lay: (centre x, centre y, rotation) of each sheet. 'thought-for-food'
# lies underneath on the left; 'say-no' lies over its bottom-right margin,
# so both stay fully legible.
FLAT = {
    'thought-for-food': (-19.5, 3.0, 3.0),
    'say-no': (21.0, -3.0, -2.5),
}
UNDER, OVER = 'thought-for-food', 'say-no'
CURL = 0.6  # lift of the long edges of a sheet lying on the floor


def _survive_variant_switch(core):
    """render.py resets the scene when the variant changes, but studio.core
    keeps a module-level handle on the old light-target empty, and reading a
    freed object raises ReferenceError in the next studio() call. Forget that
    handle after every reset (runtime only; the shared file is untouched)."""
    if getattr(core.reset, 'forgets_origin', False):
        return
    reset = core.reset

    def reset_and_forget():
        reset()
        core._ORIGIN = None

    reset_and_forget.forgets_origin = True
    core.reset = reset_and_forget


def materials(ctx):
    m = ctx.mat
    back = m.board('card back', color=dims.CARD_BACK, roughness=0.8, coat=0.0, tooth=0.06)
    edge = m.solid('card edge', dims.CARD_EDGE, roughness=0.9)
    fronts = {}
    for p in POSTERS:
        # Uncoated matte card: a broad, low sheen, so the blue stays deep.
        mat = m.board(f'{p} print', art=ctx.art(f'{p}.png'), roughness=0.7, coat=0.0, tooth=0.04)
        mat.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.2
        fronts[p] = mat
    return fronts, back, edge


def standing(ctx, name, mats, x=0.0, y=0.0, yaw=0.0, bow=dims.BOW):
    fronts, back, edge = mats
    surf = sheet.standing_surface(dims.W, dims.H, bow=bow, lean_deg=dims.LEAN)
    ob = sheet.build(ctx, name, surf, dims.T, (fronts[name], back, edge), nu=72, nv=4)
    ob.location.x, ob.location.y = x, y
    ob.rotation_euler.z = math.radians(yaw)
    return ob


def curl(u):
    """Residual curl of card that has been rolled: flat in the middle, the
    two long edges lifting a little."""
    t = max(0.0, abs(2 * u - 1) - 0.25) / 0.75
    return CURL * t * t


def flatlay(ctx, mats):
    fronts, back, edge = mats
    W, H, T = dims.W, dims.H, dims.T
    cx, cy, rot = FLAT[UNDER]
    under = sheet.lying_surface(W, H, cx, cy, rot, height=lambda u, v, x, y: curl(u))
    objs = [sheet.build(ctx, UNDER, under, T, (fronts[UNDER], back, edge), nu=64, nv=4, lying=True)]

    def support(x, y):
        """Top of the lower sheet under (x, y): stiff card overhangs the
        step a little, then eases down to the floor over a couple of cm."""
        u, v = sheet.to_local(x, y, cx, cy, rot, W, H)
        uc, vc = min(1.0, max(0.0, u)), min(1.0, max(0.0, v))
        d = math.hypot((u - uc) * W, (v - vc) * H)
        t = min(1.0, max(0.0, d - 0.5) / 2.0)
        return (curl(uc) + T + 0.008) * (1 - t * t * (3 - 2 * t))

    tx, ty, trot = FLAT[OVER]
    over = sheet.lying_surface(W, H, tx, ty, trot, height=lambda u, v, x, y: max(curl(u), support(x, y)))
    objs.append(sheet.build(ctx, OVER, over, T, (fronts[OVER], back, edge), nu=140, nv=150, lying=True))
    return objs


def build(ctx, variant=None):
    _survive_variant_switch(ctx.core)
    mats = materials(ctx)
    variant = variant or 'thought-for-food'
    if variant in POSTERS:
        return [standing(ctx, variant, mats)]
    if variant == 'set':
        # Side by side with a clear gap between them, each turned a few
        # degrees towards the middle; card never bows exactly alike.
        gap = 8.0
        off = dims.W / 2 + gap / 2
        return [
            standing(ctx, 'thought-for-food', mats, x=-off, yaw=4.0, bow=dims.BOW),
            standing(ctx, 'say-no', mats, x=off, yaw=-3.0, bow=dims.BOW * 0.8),
        ]
    if variant == 'flatlay':
        return flatlay(ctx, mats)
    raise ValueError(f'unknown variant {variant!r}')
