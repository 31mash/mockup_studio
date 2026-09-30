"""Render a product's shots.

    python3 render.py nut-case                       # every shot, final quality
    python3 render.py nut-case --preview             # quick 800x512 previews
    python3 render.py nut-case --shots hero,top      # some shots only

Finals go to renders/<id>/<shot>.png (transparent, with shadow) and .jpg (on
the studio grey). Previews go to products/<id>/preview/.

A product lives in products/<id>/product.py and defines:

    TITLE = 'Nut Case tin'
    SHOTS = ['hero', 'front', ...]            # preset names or dicts, see below
    VARIANTS = [None]                          # optional: build variants
    def build(ctx, variant=None) -> list[bpy.types.Object]

A shot dict may set: name, preset, azimuth, elevation, lens, fill, roll,
variant. Unset values come from the preset (studio.core.PRESETS).
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

from studio import core, materials, shapes  # noqa: E402


def load_product(pid: str):
    path = os.path.join(HERE, 'products', pid, 'product.py')
    spec = importlib.util.spec_from_file_location(f'product_{pid.replace("-", "_")}', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def context_for(pid: str):
    base = os.path.join(HERE, 'products', pid)
    return types.SimpleNamespace(
        id=pid,
        dir=base,
        art=lambda name: os.path.join(base, 'art', name),
        core=core,
        mat=materials,
        shapes=shapes,
    )


def normalize(shot):
    if isinstance(shot, str):
        shot = {'name': shot}
    preset = core.PRESETS[shot.get('preset', shot['name'] if shot['name'] in core.PRESETS else 'hero')]
    out = {**preset, **{k: v for k, v in shot.items() if k not in ('preset',)}}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('product')
    ap.add_argument('--shots', default='')
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--size', default='')
    ap.add_argument('--samples', type=int, default=0)
    ap.add_argument('--out', default='')
    a = ap.parse_args(argv)

    mod = load_product(a.product)
    shots = [normalize(s) for s in getattr(mod, 'SHOTS', ['hero'])]
    if a.shots:
        wanted = a.shots.split(',')
        shots = [s for s in shots if s['name'] in wanted] or [normalize(n) for n in wanted]
    size = tuple(int(v) for v in a.size.split('x')) if a.size else None
    out_dir = a.out or os.path.join(HERE, 'products', a.product, 'preview') if a.preview else a.out or os.path.join(HERE, 'renders', a.product)

    built_variant = object()
    objs = rig = None
    for shot in shots:
        variant = shot.get('variant')
        if variant != built_variant:
            core.reset()
            core.configure_render(preview=a.preview, size=size, samples=a.samples or None)
            rig = core.studio()
            objs = mod.build(context_for(a.product), variant) if 'variant' in mod.build.__code__.co_varnames else mod.build(context_for(a.product))
            built_variant = variant
        cam = core.place_camera(objs, azimuth=shot['azimuth'], elevation=shot['elevation'], lens=shot['lens'], fill=shot['fill'], roll=shot.get('roll', 0.0))
        pts = core._mesh_points(objs)
        from mathutils import Vector

        center = sum(pts, Vector()) / len(pts)
        core.aim_lights(rig, shot['azimuth'], center)
        png = os.path.join(out_dir, f"{shot['name']}.png")
        t = time.time()
        core.render_to(png)
        core.composite(png, png[:-4] + '.jpg')
        print(f"[render] {a.product}/{shot['name']}  {time.time() - t:.1f}s  -> {os.path.relpath(png[:-4] + '.jpg', HERE)}", flush=True)


if __name__ == '__main__':
    main()
