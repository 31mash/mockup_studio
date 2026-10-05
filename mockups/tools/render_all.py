"""Render every product's final shots, one product at a time.

    python3 tools/render_all.py                    # all products
    python3 tools/render_all.py cookie-tins posters
    python3 tools/render_all.py --missing          # only shots without a final yet

For each product it regenerates the artwork (make_art.py, then raster.mjs),
then runs render.py. Progress goes to stdout; a failed product is reported
and the run moves on.
"""

import argparse
import glob
import importlib.util
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def shot_names(pid: str) -> list[str]:
    import bpy  # noqa: F401  (product modules use mathutils, which needs Blender loaded)

    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    path = os.path.join(HERE, 'products', pid, 'product.py')
    # Each product has its own dims.py and helpers under the same module
    # names: forget the previous product's before loading this one.
    pdir = os.path.join(HERE, 'products')
    for name, m in list(sys.modules.items()):
        if (getattr(m, '__file__', None) or '').startswith(pdir):
            del sys.modules[name]
    sys.path.insert(0, os.path.dirname(path))
    try:
        spec = importlib.util.spec_from_file_location(f'shots_{pid.replace("-", "_")}', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return [s if isinstance(s, str) else s['name'] for s in getattr(mod, 'SHOTS', ['hero'])]
    finally:
        sys.path.pop(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('products', nargs='*')
    ap.add_argument('--missing', action='store_true')
    ap.add_argument('--skip-art', action='store_true')
    a = ap.parse_args()

    pids = a.products or sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(HERE, 'products', '*', 'product.py')))
    failed = []
    t0 = time.time()
    for pid in pids:
        shots = shot_names(pid)
        if a.missing:
            shots = [s for s in shots if not os.path.exists(os.path.join(HERE, 'renders', pid, f'{s}.jpg'))]
            if not shots:
                print(f'[all] {pid}: up to date', flush=True)
                continue
        print(f'[all] {pid}: {len(shots)} shots', flush=True)
        try:
            if not a.skip_art:
                subprocess.run([sys.executable, os.path.join('products', pid, 'make_art.py')], cwd=HERE, check=True, stdout=subprocess.DEVNULL)
                subprocess.run(['node', 'tools/raster.mjs', os.path.join('products', pid, 'art')], cwd=HERE, check=True, stdout=subprocess.DEVNULL)
            subprocess.run([sys.executable, 'render.py', pid, '--shots', ','.join(shots)], cwd=HERE, check=True)
        except subprocess.CalledProcessError as e:
            print(f'[all] {pid}: FAILED ({e})', flush=True)
            failed.append(pid)
    print(f'[all] done in {(time.time() - t0) / 60:.0f} min; failed: {", ".join(failed) or "none"}', flush=True)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
