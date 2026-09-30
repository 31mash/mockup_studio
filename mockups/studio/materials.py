"""Materials for printed packaging. Artwork images are sRGB PNGs made by
tools/raster.mjs; colours passed as '#rrggbb' are the printed sRGB colours."""

from __future__ import annotations

import os

import bpy

from .core import rgba


def image(path: str, alpha: bool = True, colorspace: str = 'sRGB') -> bpy.types.Image:
    path = os.path.abspath(path)
    img = bpy.data.images.load(path, check_existing=True)
    img.colorspace_settings.name = colorspace
    img.alpha_mode = 'STRAIGHT' if alpha else 'NONE'
    return img


def _principled(name: str):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    return m, nt, p


def _tex(nt, img, interpolation: str = 'Cubic', extension: str = 'EXTEND'):
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = img
    t.interpolation = interpolation
    t.extension = extension
    return t


def _bump(nt, p, strength: float, scale: float, detail: float = 6.0, kind: str = 'noise'):
    """Fine surface texture (paper tooth, foil crinkle) through the normal input."""
    coord = nt.nodes.new('ShaderNodeTexCoord')
    if kind == 'voronoi':
        n = nt.nodes.new('ShaderNodeTexVoronoi')
        n.inputs['Scale'].default_value = scale
        out = n.outputs['Distance']
    else:
        n = nt.nodes.new('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = 0.6
        out = n.outputs['Fac']
    nt.links.new(coord.outputs['Object'], n.inputs['Vector'])
    b = nt.nodes.new('ShaderNodeBump')
    b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = 0.02
    nt.links.new(out, b.inputs['Height'])
    nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    return b


def printed_metal(name: str, art: str | None = None, color: str | None = None, roughness: float = 0.34, coat: float = 0.18, metallic: float = 0.0):
    """Lithographed tinplate: opaque ink under a satin lacquer. Pass the
    artwork image, or a flat printed colour."""
    m, nt, p = _principled(name)
    if art:
        t = _tex(nt, image(art))
        nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    else:
        p.inputs['Base Color'].default_value = rgba(color or '#ffffff')
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Coat Weight'].default_value = coat
    p.inputs['Coat Roughness'].default_value = 0.2
    p.inputs['Specular IOR Level'].default_value = 0.3
    return m


def bare_metal(name: str = 'tinplate', color: str = '#d9dadd', roughness: float = 0.22):
    """Unprinted tinplate or aluminium: seams, beads, rims."""
    m, nt, p = _principled(name)
    p.inputs['Base Color'].default_value = rgba(color)
    p.inputs['Metallic'].default_value = 1.0
    p.inputs['Roughness'].default_value = roughness
    return m


def board(name: str, art: str | None = None, color: str | None = None, roughness: float = 0.55, coat: float = 0.12, tooth: float = 0.05):
    """Printed paperboard with a light varnish; `tooth` adds paper grain."""
    m, nt, p = _principled(name)
    if art:
        t = _tex(nt, image(art))
        nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    else:
        p.inputs['Base Color'].default_value = rgba(color or '#ffffff')
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Coat Weight'].default_value = coat
    p.inputs['Coat Roughness'].default_value = 0.35
    p.inputs['Specular IOR Level'].default_value = 0.35
    if tooth:
        _bump(nt, p, tooth, 60.0)
    return m


def kraft(name: str, art: str | None = None, color: str = '#b58a5a', roughness: float = 0.88):
    """Brown kraft paper: matte, fibrous. Artwork is multiplied over the kraft
    colour, like ink on unbleached paper (draw it on white)."""
    m, nt, p = _principled(name)
    base = nt.nodes.new('ShaderNodeRGB')
    base.outputs[0].default_value = rgba(color)
    fib = nt.nodes.new('ShaderNodeTexNoise')
    fib.inputs['Scale'].default_value = 180.0
    fib.inputs['Detail'].default_value = 8.0
    coord = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(coord.outputs['Object'], fib.inputs['Vector'])
    mixf = nt.nodes.new('ShaderNodeMix')
    mixf.data_type = 'RGBA'
    mixf.blend_type = 'MULTIPLY'
    mixf.inputs['Factor'].default_value = 0.12
    nt.links.new(base.outputs[0], mixf.inputs['A'])
    nt.links.new(fib.outputs['Color'], mixf.inputs['B'])
    col = mixf.outputs['Result']
    if art:
        t = _tex(nt, image(art))
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        nt.links.new(col, mix.inputs['A'])
        nt.links.new(t.outputs['Color'], mix.inputs['B'])
        col = mix.outputs['Result']
    nt.links.new(col, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Specular IOR Level'].default_value = 0.25
    _bump(nt, p, 0.12, 90.0)
    return m


def foil(name: str = 'foil', roughness: float = 0.28, crinkle: float = 0.25):
    """Aluminium foil tray."""
    m, nt, p = _principled(name)
    p.inputs['Base Color'].default_value = rgba('#d6d7da')
    p.inputs['Metallic'].default_value = 1.0
    p.inputs['Roughness'].default_value = roughness
    _bump(nt, p, crinkle, 6.0, detail=10.0, kind='voronoi')
    return m


def clear_film(name: str = 'film', art: str | None = None, roughness: float = 0.06):
    """Clear plastic film (a window or pouch). Artwork alpha marks printed ink,
    which is opaque; the rest stays clear."""
    m, nt, p = _principled(name)
    p.inputs['Base Color'].default_value = (1, 1, 1, 1)
    p.inputs['Transmission Weight'].default_value = 1.0
    p.inputs['Roughness'].default_value = roughness
    p.inputs['IOR'].default_value = 1.45
    if art:
        t = _tex(nt, image(art))
        ink = nt.nodes.new('ShaderNodeBsdfPrincipled')
        ink.inputs['Roughness'].default_value = 0.45
        nt.links.new(t.outputs['Color'], ink.inputs['Base Color'])
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(t.outputs['Alpha'], mix.inputs['Fac'])
        out = nt.nodes['Material Output']
        nt.links.new(p.outputs['BSDF'], mix.inputs[1])
        nt.links.new(ink.outputs['BSDF'], mix.inputs[2])
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return m


def tissue(name: str, art: str | None = None, color: str = '#f7f6f1'):
    """Soft paper napkin: matte, slightly translucent, embossed."""
    m, nt, p = _principled(name)
    if art:
        t = _tex(nt, image(art))
        nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    else:
        p.inputs['Base Color'].default_value = rgba(color)
    p.inputs['Roughness'].default_value = 0.95
    p.inputs['Subsurface Weight'].default_value = 0.15
    p.inputs['Subsurface Radius'].default_value = (0.3, 0.3, 0.3)
    _bump(nt, p, 0.18, 35.0, detail=4.0)
    return m


def solid(name: str, color: str, roughness: float = 0.5, metallic: float = 0.0, coat: float = 0.0):
    m, nt, p = _principled(name)
    p.inputs['Base Color'].default_value = rgba(color)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Coat Weight'].default_value = coat
    return m


def textured(name: str, art: str, roughness: float = 0.6, bump: float = 0.0, bump_scale: float = 40.0):
    """Anything with a photographic or painted colour map (food, for example)."""
    m, nt, p = _principled(name)
    t = _tex(nt, image(art), extension='REPEAT')
    nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = roughness
    if bump:
        _bump(nt, p, bump, bump_scale)
    return m
