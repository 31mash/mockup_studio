"""The sandwich seen through the Tiffin window: the cut faces of two sandwich
halves standing on their crusts, pressed against the film. Left: white bread,
corn and green chutney, white bread. Right: brown bread, cheese spread, corn
and chutney, brown bread.

Only the cut face is ever visible, so the model is that face: a sheet behind
the window carrying a photographic colour map, art/sandwich.png, which
make_art.py rectifies from the window of the original pack
(source/crops/tiffin-wedge-front.png) to the window's real size. The map
covers the window aperture exactly; beyond it, under the board, its edges are
extended. The sheet is relieved where the two halves meet (a shallow groove,
following the photo's seam), and the photo's own light and shade gives the
crumb and the kernels a fine bump.

Coordinates: art space of the front panel (x across from the -X end, p down
the slope from the apex fold, depth in from the outer surface), mapped to the
world by `to_world`.
"""

from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector

# Where the halves meet, measured on art/sandwich.png: x (cm from the -X end)
# at the top and the bottom of the window. The right half leans a little.
SEAM = (3.72, 3.50)
GROOVE_DEPTH = 0.07
GROOVE_WIDTH = 0.06


def material(img_path, name='sandwich'):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    img = bpy.data.images.load(img_path, check_existing=True)
    img.colorspace_settings.name = 'sRGB'
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Cubic'
    tex.extension = 'EXTEND'
    nt.links.new(tex.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.8
    p.inputs['Specular IOR Level'].default_value = 0.3
    # Bread and corn are a little translucent.
    p.inputs['Subsurface Weight'].default_value = 0.06
    p.inputs['Subsurface Radius'].default_value = (0.05, 0.04, 0.025)
    p.inputs['Subsurface Scale'].default_value = 1.0
    bw = nt.nodes.new('ShaderNodeRGBToBW')
    nt.links.new(tex.outputs['Color'], bw.inputs['Color'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.25
    bump.inputs['Distance'].default_value = 0.015
    nt.links.new(bw.outputs['Val'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


def build(name, to_world, win_x, win_p, depth, mat, margin=0.6):
    """The cut-face sheet, `depth` cm in from the outer surface, covering the
    window (win_x, win_p) with `margin` to spare on every side."""
    (x0, x1), (p0, p1) = win_x, win_p
    xa, xb, pa, pb = x0 - margin, x1 + margin, p0 - margin, p1 + margin
    nx = int((xb - xa) / 0.025)
    npp = int((pb - pa) / 0.1)

    def seam(p):
        t = min(1.0, max(0.0, (p - p0) / (p1 - p0)))
        return SEAM[0] + (SEAM[1] - SEAM[0]) * t

    def dep(x, p):
        d = (x - seam(p)) / GROOVE_WIDTH
        return depth + GROOVE_DEPTH * math.exp(-d * d)

    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    grid = []
    for i in range(npp + 1):
        p = pa + (pb - pa) * i / npp
        row = []
        for j in range(nx + 1):
            x = xa + (xb - xa) * j / nx
            row.append((bm.verts.new(to_world(x, p, dep(x, p))), ((x - x0) / (x1 - x0), 1.0 - (p - p0) / (p1 - p0))))
        grid.append(row)
    for i in range(npp):
        for j in range(nx):
            cells = (grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j])
            f = bm.faces.new([c[0] for c in cells])
            f.smooth = True
            for loop, c in zip(f.loops, cells):
                loop[uv].uv = c[1]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # The face must look out through the window.
    out_dir = Vector(to_world(x0, p0, 0.0)) - Vector(to_world(x0, p0, 1.0))
    if sum((f.normal for f in bm.faces), Vector()).dot(out_dir) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(mat)
    return ob
