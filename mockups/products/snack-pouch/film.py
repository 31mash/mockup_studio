"""Clear pouch film as a clean thin sheet.

Why not a glossy + transparent mix: Cycles picks one closure per bounce, so a
film that is 95 % transparent and 5 % glossy sends 5 % of the camera paths
off as reflections, and the alpha (which the denoiser does not touch) turns
into grain. Here every closure a camera ray meets on the film is either
Transparent or Emission, so the film's alpha and colour are exact at any
sample count:

- reflection: the sheet reflects the studio itself, computed in the shader.
  The reflected ray is traced against the three softboxes of the light rig
  (read from the scene, in the rig's own frame, which turns with the camera),
  the floor below the horizon and the grey world above it; the result is
  weighted by a two-sided Schlick Fresnel, so the film stays clear head-on
  and turns into a mirror at grazing angles, as thin PET does.
- seals: the heat seals are a milky veil (the seals.png mask), with the fine
  ribbing the sealing jaws leave.
- ink: white ink from the artwork, an ordinary lit BSDF (clear_film's graph).

Other rays (shadows, bounce light) see the film as clear, so the namkeen
inside is lit as if the film were not there, apart from the ink.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Vector


class _G:
    """Tiny node-graph builder."""

    def __init__(self, nt):
        self.nt = nt
        self.L = nt.links

    def _in(self, sock, v):
        if v is None:
            return
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, (tuple, list, Vector)):
            sock.default_value = tuple(v)
        else:
            self.L.new(v, sock)

    def m(self, op, a, b=None, clamp=False):
        n = self.nt.nodes.new('ShaderNodeMath')
        n.operation = op
        n.use_clamp = clamp
        self._in(n.inputs[0], a)
        self._in(n.inputs[1], b)
        return n.outputs[0]

    def v(self, op, a, b=None, scale=None):
        n = self.nt.nodes.new('ShaderNodeVectorMath')
        n.operation = op
        self._in(n.inputs[0], a)
        self._in(n.inputs[1], b)
        if scale is not None:
            self._in(n.inputs['Scale'], scale)
        return n.outputs['Value'] if op in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else n.outputs['Vector']

    def dot(self, a, b):
        return self.v('DOT_PRODUCT', a, b)

    def smooth(self, x, lo, hi, out_lo=0.0, out_hi=1.0):
        n = self.nt.nodes.new('ShaderNodeMapRange')
        n.interpolation_type = 'SMOOTHSTEP'
        self._in(n.inputs['Value'], x)
        n.inputs['From Min'].default_value = lo
        n.inputs['From Max'].default_value = hi
        n.inputs['To Min'].default_value = out_lo
        n.inputs['To Max'].default_value = out_hi
        return n.outputs['Result']

    def combine(self, x, y, z):
        n = self.nt.nodes.new('ShaderNodeCombineXYZ')
        for i, s in enumerate((x, y, z)):
            self._in(n.inputs[i], s)
        return n.outputs[0]

    def mix_shader(self, fac, a, b):
        n = self.nt.nodes.new('ShaderNodeMixShader')
        self._in(n.inputs['Fac'], fac)
        self.L.new(a, n.inputs[1])
        self.L.new(b, n.inputs[2])
        return n.outputs[0]

    def mix_col(self, fac, a, b):
        n = self.nt.nodes.new('ShaderNodeMix')
        n.data_type = 'RGBA'
        self._in(n.inputs['Factor'], fac)
        self._in(n.inputs['A'], a)
        self._in(n.inputs['B'], b)
        return n.outputs['Result']

    def emission(self, colour, strength=1.0):
        n = self.nt.nodes.new('ShaderNodeEmission')
        self._in(n.inputs['Color'], colour)
        self._in(n.inputs['Strength'], strength)
        return n.outputs[0]


def _softboxes(target):
    """The rig's softboxes in the light turntable's frame: centre, facing
    direction, rectangle axes, half sizes and radiance (Cycles area lights:
    radiance = power / (4 * area))."""
    out = []
    for ob in bpy.data.objects:
        if ob.type != 'LIGHT' or ob.data.type != 'AREA':
            continue
        c = Vector(ob.location)
        n = (target - c).normalized()  # the way it shines
        up = Vector((0, 0, 1))
        v = (up - n * up.dot(n)).normalized()
        u = n.cross(v).normalized()
        sx, sy = ob.data.size, ob.data.size_y
        radiance = ob.data.energy * 0.25 / (sx * sy)
        out.append((c, n, u, v, sx / 2, sy / 2, radiance))
    return out


FLOOR = 0.62  # the lit grey sweep, seen in the film below the horizon (linear)
WORLD = (0.33, 0.335, 0.345)  # the studio around it, above the horizon
F0 = 0.075  # head-on reflectance of the sheet (two faces of PET)
FMAX = 0.9


def reflection(g: _G, target=Vector((0, 0, 8.5))):
    """Returns (fresnel, reflected radiance colour) sockets."""
    geo = g.nt.nodes.new('ShaderNodeNewGeometry')
    N, I, P = geo.outputs['Normal'], geo.outputs['Incoming'], geo.outputs['Position']
    ndi = g.dot(N, I)
    cos = g.m('ABSOLUTE', ndi)
    k = g.m('POWER', g.m('SUBTRACT', 1.0, cos, clamp=True), 5.0)
    fres = g.m('MINIMUM', g.m('ADD', g.m('MULTIPLY', k, 1.0 - F0), F0), FMAX)
    # R = 2 (N.I) N - I, in world space.
    R = g.v('SUBTRACT', g.v('SCALE', N, scale=g.m('MULTIPLY', ndi, 2.0)), I)

    # The rig's frame: x = the camera's right (horizontal), z = up.
    vt = g.nt.nodes.new('ShaderNodeVectorTransform')
    vt.vector_type = 'VECTOR'
    vt.convert_from = 'CAMERA'
    vt.convert_to = 'WORLD'
    vt.inputs['Vector'].default_value = (1.0, 0.0, 0.0)
    X = g.v('NORMALIZE', g.v('MULTIPLY', vt.outputs['Vector'], (1.0, 1.0, 0.0)))
    Z = (0.0, 0.0, 1.0)
    Y = g.v('CROSS_PRODUCT', Z, X)

    def local(vec):
        return g.combine(g.dot(vec, X), g.dot(vec, Y), g.dot(vec, Z))

    Rl = local(R)
    Pl = local(P)
    rz = g.dot(R, Z)

    # Floor below the horizon, the grey world above it.
    up = g.smooth(rz, -0.06, 0.04)
    col = g.mix_col(up, (FLOOR, FLOOR, FLOOR, 1.0), (*WORLD, 1.0))

    for c, n, u, v, hx, hy, rad in _softboxes(target):
        denom = g.dot(Rl, tuple(n))
        facing = g.m('LESS_THAN', denom, -0.02)
        D = g.v('SUBTRACT', tuple(c), Pl)
        t = g.m('DIVIDE', g.dot(D, tuple(n)), g.m('MINIMUM', denom, -0.02))
        h = g.v('SUBTRACT', g.v('SCALE', Rl, scale=t), D)
        a = g.m('DIVIDE', g.m('ABSOLUTE', g.dot(h, tuple(u))), hx)
        b = g.m('DIVIDE', g.m('ABSOLUTE', g.dot(h, tuple(v))), hy)
        # Soft edges (the film's slight roughness and its ripples blur them).
        wa = g.smooth(a, 0.72, 1.12, 1.0, 0.0)
        wb = g.smooth(b, 0.72, 1.12, 1.0, 0.0)
        w = g.m('MULTIPLY', g.m('MULTIPLY', wa, wb), facing)
        # Softboxes are a little brighter in the middle.
        w = g.m('MULTIPLY', w, g.m('SUBTRACT', 1.08, g.m('MULTIPLY', g.m('MAXIMUM', a, b), 0.16)))
        add = g.nt.nodes.new('ShaderNodeMix')
        add.data_type = 'RGBA'
        add.blend_type = 'ADD'
        g._in(add.inputs['Factor'], w)
        g._in(add.inputs['A'], col)
        add.inputs['B'].default_value = (rad, rad, rad, 1.0)
        col = add.outputs['Result']
    return fres, col


def sheet(m, name: str, art: str | None = None, seals: str | None = None, seal_veil: float = 0.34, seal_colour: float = 0.86):
    """The pouch film. `art`: white ink (alpha = ink). `seals`: the heat-seal
    mask (alpha = how milky)."""
    mat = m.clear_film(name, art=art)
    mat.cycles.emission_sampling = 'NONE'  # the veil is not a light
    nt = mat.node_tree
    g = _G(nt)
    p = nt.nodes['Principled BSDF']
    out = nt.nodes['Material Output']

    clear = nt.nodes.new('ShaderNodeBsdfTransparent').outputs[0]
    fres, refl = reflection(g)
    s = clear
    if seals:
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = m.image(seals)
        tex.interpolation = 'Cubic'
        tex.extension = 'EXTEND'
        veil = g.m('MULTIPLY', tex.outputs['Alpha'], seal_veil)
        s = g.mix_shader(veil, s, g.emission((seal_colour, seal_colour, seal_colour * 1.01, 1.0)))
    s = g.mix_shader(fres, s, g.emission(refl))
    lp = nt.nodes.new('ShaderNodeLightPath')
    s = g.mix_shader(lp.outputs['Is Camera Ray'], nt.nodes.new('ShaderNodeBsdfTransparent').outputs[0], s)

    users = [lk.to_socket for lk in nt.links if lk.from_node == p]
    nt.nodes.remove(p)
    if users:
        for sock in users:
            g.L.new(s, sock)
    else:
        g.L.new(s, out.inputs['Surface'])
    return mat
