"""IndiGo namkeen pouch: a clear stand-up zip pouch with a bottom gusset,
printed in white ink with the story of the namkeen maker, filled with thick
crinkly namkeen sticks."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402,F401
import food  # noqa: E402
import pouch  # noqa: E402

TITLE = 'Namkeen pouch'
SHOTS = ['hero', 'hero-right', 'front', 'side', 'back', 'low']

F0 = 0.02  # the film's head-on reflectance (kept low: see film())


def film(m, name, art=None):
    """Clear film as a thin sheet. studio.materials.clear_film gives the ink
    (artwork alpha = opaque ink over clear film); its clear part is swapped
    for a thin-sheet shader: straight-through transparency plus a Fresnel
    gloss that is the same from both sides. A refractive clear part would
    stop light reaching the namkeen inside (Cycles runs without caustics).

    The clear part is untinted: over the shadow-catcher floor a tint reads
    as a shadow, and that shadow speckles (alpha is not denoised). The gloss
    stays low head-on and rises at grazing angles; the seals are a faint
    white ink in the artwork, close to the studio grey, so they stay clean."""
    mat = m.clear_film(name, art=art)
    nt = mat.node_tree
    L = nt.links
    p = nt.nodes['Principled BSDF']
    out = nt.nodes['Material Output']

    clear = nt.nodes.new('ShaderNodeBsdfTransparent')
    gloss = nt.nodes.new('ShaderNodeBsdfGlossy')
    gloss.distribution = 'GGX'
    gloss.inputs['Roughness'].default_value = 0.08
    # Schlick Fresnel on |N.I|, so both faces of the sheet reflect alike.
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    dot = nt.nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    L.new(geo.outputs['Normal'], dot.inputs[0])
    L.new(geo.outputs['Incoming'], dot.inputs[1])

    def op(kind, a, b=None):
        n = nt.nodes.new('ShaderNodeMath')
        n.operation = kind
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    cos = op('ABSOLUTE', dot.outputs['Value'])
    k = op('POWER', op('SUBTRACT', 1.0, cos), 5.0)
    fres = op('ADD', op('MULTIPLY', k, 0.85 - F0), F0)
    sheet = nt.nodes.new('ShaderNodeMixShader')
    L.new(fres, sheet.inputs['Fac'])
    L.new(clear.outputs[0], sheet.inputs[1])
    L.new(gloss.outputs[0], sheet.inputs[2])

    users = [lk for lk in nt.links if lk.from_node == p]
    for lk in users:
        L.new(sheet.outputs[0], lk.to_socket)
    nt.nodes.remove(p)
    if not users:
        L.new(sheet.outputs[0], out.inputs['Surface'])
    return mat


def zip_plastic(m):
    """The zip profiles: milky, half-clear polyethylene. Transmission rather
    than transparency, so these thin lines render clean (opaque alpha)."""
    mat = m.solid('zip', '#f2f4f4', roughness=0.3)
    p = mat.node_tree.nodes['Principled BSDF']
    p.inputs['Transmission Weight'].default_value = 0.55
    p.inputs['IOR'].default_value = 1.5
    return mat


def build(ctx, variant=None):
    m = ctx.mat
    front_m = film(m, 'film-front', ctx.art('front.png'))
    back_m = film(m, 'film-back', ctx.art('back.png'))
    base_m = film(m, 'film-base')
    front, back, base = pouch.build_film(front_m, back_m, base_m)
    edge_m = zip_plastic(m)
    zips = pouch.build_zip(edge_m, front, back)
    edges = pouch.build_edges(front, edge_m)
    food.build(m)
    return [front, back, base] + zips + [edges]
