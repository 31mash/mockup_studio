"""Spicy Kulcha: IndiGo's big matchbox pack. A printed paperboard sleeve (vintage
matchbox label on top, brown striker panels on the long sides) with a white
card tray slid half out, holding a folded kulcha.

Each box is modelled lying along x with the tray sliding out towards +x (see
dims.py), then turned so it lies front to back: the tray comes out towards the
camera (-Y) and the label reads upright from the front, as in the spread, where
the hero angle looks down the box from its open end. Variants: 'single' (the
red colourway) and 'pair' (green in front, red behind and to the right, as in
the spread)."""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dims  # noqa: E402

TITLE = 'Spicy Kulcha matchbox'
VARIANTS = ['single', 'pair']
SHOTS = [
    {'name': 'hero', 'variant': 'single'},
    {'name': 'hero-right', 'variant': 'single'},
    # straight down the box from its open end, a little above the tray
    {'name': 'front', 'elevation': 24, 'variant': 'single'},
    # the long striker side, the label just in view
    {'name': 'side', 'elevation': 16, 'fill': 0.6, 'variant': 'single'},
    {'name': 'top', 'fill': 0.62, 'variant': 'single'},  # the box is upright in the frame: a little larger
    {'name': 'high', 'variant': 'single'},
    {'name': 'pair-hero', 'preset': 'hero', 'variant': 'pair', 'fill': 0.6},
    {'name': 'pair-top', 'preset': 'top', 'variant': 'pair', 'fill': 0.6},
]

CARD = '#f4f2eb'


# ----------------------------------------------------------------- geometry


def _mesh(name, bm, mats, smooth_angle=40.0):
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in mats:
        me.materials.append(m)
    # Smooth shading with crisp creases (the mesh API: the auto-smooth operator
    # needs a selection context that a background render does not have).
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    return ob


def sleeve(name, layout, mats, x0=0.0, y0=0.0):
    """The printed sleeve: a paperboard tube along x with rounded creases,
    open at both ends. mats: top, front, back, bottom, inside, edge.

    UVs: top = the label image (portrait, image top at -x, image left at -y);
    front/back = the side image as seen from outside; others unmapped."""
    L, W, H, T = dims.L, dims.W, dims.H, dims.T
    order = ['top', 'front', 'back', 'bottom', 'inside', 'edge']
    mi = {k: i for i, k in enumerate(order)}
    prof = layout.rounded_rect(W, H, dims.FOLD_R, seg=6)  # (y, z - H/2), CCW from the bottom's left end
    inner = layout.inset(prof, T)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    xs = (x0 - L / 2, x0 + L / 2)
    out = [[bm.verts.new((x, y0 + a, b + H / 2)) for a, b in prof] for x in xs]
    inn = [[bm.verts.new((x, y0 + a, b + H / 2)) for a, b in inner] for x in xs]
    n = len(prof)

    def uv_for(face, co):
        x, y, z = co.x - x0, co.y - y0, co.z
        if face == 'top':
            return ((y + W / 2) / W, (L / 2 - x) / L)
        if face == 'front':
            return ((x + L / 2) / L, z / H)
        if face == 'back':
            return ((L / 2 - x) / L, z / H)
        return (0.5, 0.5)

    def quad(vs, face):
        f = bm.faces.new(vs)
        f.material_index = mi[face]
        for loop in f.loops:
            loop[uvl].uv = uv_for(face, loop.vert.co)

    for i in range(n):
        j = (i + 1) % n
        (a0, b0), (a1, b1) = prof[i], prof[j]
        # outward normal of this segment decides which printed face it belongs to
        ny, nz = (b1 - b0), -(a1 - a0)
        if abs(nz) >= abs(ny):
            face = 'top' if nz > 0 else 'bottom'
        else:
            face = 'back' if ny > 0 else 'front'
        quad([out[0][i], out[0][j], out[1][j], out[1][i]], face)
        quad([inn[0][j], inn[0][i], inn[1][i], inn[1][j]], 'inside')
        quad([out[0][j], out[0][i], inn[0][i], inn[0][j]], 'edge')
        quad([out[1][i], out[1][j], inn[1][j], inn[1][i]], 'edge')
    ob = _mesh(name, bm, [mats[k] for k in order], smooth_angle=35)
    b = ob.modifiers.new('cut-edge', 'BEVEL')
    b.width = 0.012
    b.segments = 2
    b.limit_method = 'ANGLE'
    b.angle_limit = math.radians(50)
    return ob


def tray(name, layout, mat, x0=0.0, y0=0.0):
    """The white card tray: an open box with a thin wall and floor, resting on
    the sleeve's inner floor."""
    TL, TW, TH, TT, TB = dims.TL, dims.TW, dims.TH, dims.TT, dims.TB
    z0 = dims.T
    outer = [(x0 + a, y0 + b) for a, b in layout.rounded_rect(TL, TW, 0.07, seg=4)]
    inner = layout.inset(outer, TT)
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    r0 = [bm.verts.new((x, y, z0)) for x, y in outer]
    r1 = [bm.verts.new((x, y, z0 + TH)) for x, y in outer]
    r2 = [bm.verts.new((x, y, z0 + TH)) for x, y in inner]
    r3 = [bm.verts.new((x, y, z0 + TB)) for x, y in inner]
    n = len(outer)
    for i in range(n):
        j = (i + 1) % n
        for a, b in ((r0, r1), (r1, r2), (r2, r3)):
            bm.faces.new([a[i], a[j], b[j], b[i]])
    bm.faces.new(list(reversed(r0)))
    bm.faces.new(r3)
    ob = _mesh(name, bm, [mat], smooth_angle=30)
    b = ob.modifiers.new('folded-rim', 'BEVEL')
    b.width = 0.022
    b.segments = 3
    b.limit_method = 'ANGLE'
    b.angle_limit = math.radians(40)
    return ob


def _smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def kulcha(name, mat, x0, x1, y_back, y_front, z_floor, seed=1.0, turn=None):
    """A kulcha folded in half: the fold runs along x at y_back, the two
    layers' rounded edges come towards y_front, the top one ending short.
    `turn` (x, y) -> (x', y') then moves it into place. Built as one dough
    sheet (a grid over the unfolded disc) bent round the fold, with a thinner
    rim, a slight droop and puff to the top layer, and irregular bubbles.

    UV = the position on the unfolded sheet in cm (for the procedural texture)."""
    t = dims.KULCHA_T
    r_i = dims.KULCHA_GAP
    r_mid = r_i + t / 2
    arc = math.pi * r_mid
    a = (x1 - x0) / 2
    cx = (x0 + x1) / 2
    y_fold = y_back - (r_i + t)
    b = y_fold - y_front  # reach of the bottom layer from the fold
    b_top = b - 1.1  # the top layer ends short, so both rounded edges show
    p = 3.6  # superellipse: a round pressed square by the tray walls
    nu, n1, n2, n3 = 48, 36, 12, 36

    def prof(xn, k):
        base = max(0.0, 1 - abs(xn) ** p) ** (1 / p)
        wob = 1 + 0.035 * noise.noise(Vector((xn * 2.2, k * 3.1, seed)))
        return base * wob

    def bubbles(u, s):
        """Soft undulation plus raised tandoor blisters."""
        v = Vector((u * 0.7, s * 0.7, seed * 1.7))
        blist = max(0.0, noise.noise(Vector((u * 1.9, s * 1.9, seed * 3.1))) - 0.08)
        return 0.07 * noise.noise(v) + 0.03 * noise.noise(v * 2.7) + 0.16 * blist

    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    rim_l = bm.verts.layers.float.new('rim')
    grids = {}
    for side, d_sign in (('in', 1), ('out', -1)):
        rows = []
        for i in range(nu + 1):
            # denser towards the ends, where the outline turns fast
            xn = 0.998 * math.sin(math.pi * (i / nu - 0.5))
            x = cx + a * xn
            f_lo = prof(xn, 0.0)
            f_hi = prof(xn, 1.0)
            s_lo = -b * f_lo
            s_hi = arc + b_top * f_hi
            ss = [s_lo + (0 - s_lo) * k / n1 for k in range(n1)]
            ss += [arc * k / n2 for k in range(n2)]
            ss += [arc + (s_hi - arc) * k / n3 for k in range(n3 + 1)]
            row = []
            for s in ss:
                # distance to the nearest rim of the sheet, in cm: the dough thins there
                rim = min(s - s_lo, s_hi - s, a * (0.998 - abs(xn)) + 0.05)
                tl = t * (0.38 + 0.62 * _smooth(0.0, 1.5, rim))
                d = d_sign * tl / 2
                if s <= 0:
                    yy, zz = y_fold + s, t / 2 + d
                    zz += 0.18 * (1 - _smooth(0.0, 1.4, rim))  # rim curls up a touch
                elif s < arc:
                    th = s / r_mid
                    cy_, cz_ = y_fold, t / 2 + r_mid
                    my, mz = cy_ + r_mid * math.sin(th), cz_ - r_mid * math.cos(th)
                    yy, zz = my - d * math.sin(th), mz + d * math.cos(th)
                else:
                    s2 = s - arc
                    yy, zz = y_fold - s2, t / 2 + 2 * r_mid - d
                    reach = max(0.01, s_hi - arc)
                    q = s2 / reach
                    zz -= 2 * r_i * 0.6 * _smooth(0.0, 1.0, q)  # droops towards the lower layer
                    zz += 0.65 * math.sin(math.pi * min(1.0, q) ** 1.3) * (1 - xn ** 4)  # puffed middle
                    zz -= 0.12 * (1 - _smooth(0.0, 1.2, rim))
                zz += bubbles(x, s)
                v = bm.verts.new((x, yy, z_floor + zz))
                v[rim_l] = 1.0 - _smooth(0.0, 0.9, rim)  # 1 at the baked rim, for the shader
                row.append((v, (x - cx + 7.3 * seed, s + 3.1 * seed + (0 if d_sign > 0 else 40.0))))
            rows.append(row)
        grids[side] = rows

    def face(vs_uv):
        try:
            f = bm.faces.new([v for v, _ in vs_uv])
        except ValueError:
            return
        f.smooth = True
        for loop, (_, uv) in zip(f.loops, vs_uv):
            loop[uvl].uv = uv

    gi, go = grids['in'], grids['out']
    nv = len(gi[0])
    for i in range(nu):
        for k in range(nv - 1):
            face([gi[i][k], gi[i + 1][k], gi[i + 1][k + 1], gi[i][k + 1]])
            face([go[i][k + 1], go[i + 1][k + 1], go[i + 1][k], go[i][k]])
    # rims: the two long edges and the two ends
    for i in range(nu):
        face([gi[i][0], go[i][0], go[i + 1][0], gi[i + 1][0]])
        face([gi[i + 1][-1], go[i + 1][-1], go[i][-1], gi[i][-1]])
    for k in range(nv - 1):
        face([gi[0][k + 1], go[0][k + 1], go[0][k], gi[0][k]])
        face([gi[-1][k], go[-1][k], go[-1][k + 1], gi[-1][k + 1]])
    if turn is not None:
        for v in bm.verts:
            v.co.x, v.co.y = turn(v.co.x, v.co.y)
    ob = _mesh(name, bm, [mat], smooth_angle=180)
    sub = ob.modifiers.new('soft', 'SUBSURF')
    sub.levels = 1
    sub.render_levels = 2
    # rest it on the tray floor after smoothing
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    zmin = min((ev.matrix_world @ v.co).z for v in ev.data.vertices)
    ob.location.z += z_floor + 0.005 - zmin
    return ob


# ----------------------------------------------------------------- materials


def kulcha_material(name='kulcha'):
    """Soft leavened flatbread: pale dough, tandoor-golden blisters with a few
    charred hearts, a golden baked rim, chopped coriander, chilli flakes and
    nigella seeds; subsurface softness. Procedural over the unfolded sheet's UVs
    (in cm), so the pattern follows the dough round the fold."""
    from studio.core import rgba

    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    p = N['Principled BSDF']

    tc = N.new('ShaderNodeTexCoord')
    pos = tc.outputs['UV']

    def noise_tex(scale, detail=4.0, rough=0.55, distort=0.0, w=0.0, vec=None):
        t = N.new('ShaderNodeTexNoise')
        t.noise_dimensions = '4D'
        t.inputs['Scale'].default_value = scale
        t.inputs['Detail'].default_value = detail
        t.inputs['Roughness'].default_value = rough
        t.inputs['Distortion'].default_value = distort
        t.inputs['W'].default_value = w
        Lk.new(vec or pos, t.inputs['Vector'])
        return t

    def ramp(src, stops):
        r = N.new('ShaderNodeValToRGB')
        cr = r.color_ramp
        cr.elements[0].position, cr.elements[0].color = stops[0][0], stops[0][1]
        cr.elements[1].position, cr.elements[1].color = stops[-1][0], stops[-1][1]
        for pos_, col in stops[1:-1]:
            e = cr.elements.new(pos_)
            e.color = col
        Lk.new(src, r.inputs['Fac'])
        return r.outputs['Color']

    def mask(src, e0, e1):
        return ramp(src, [(e0, (0, 0, 0, 1)), (e1, (1, 1, 1, 1))])

    def mix(a, b, fac):
        mx = N.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        Lk.new(fac, mx.inputs['Factor'])
        Lk.new(a, mx.inputs['A'])
        Lk.new(b, mx.inputs['B'])
        return mx.outputs['Result']

    def op(kind, a, b=None, v=None):
        n = N.new('ShaderNodeMath')
        n.operation = kind
        for k, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, float):
                n.inputs[k].default_value = x
            else:
                Lk.new(x, n.inputs[k])
        return n.outputs[0]

    # dough: pale cream, gently uneven
    dough = ramp(noise_tex(0.5, 3, 0.5, 0.0, 1.0).outputs['Fac'], [(0.3, rgba('#f1e5bf')), (0.72, rgba('#e5d19e'))])
    # golden blisters: warped noise patches, deeper colour at their hearts
    bl = noise_tex(1.5, 5, 0.6, 0.5, 3.0).outputs['Fac']
    gold = mask(bl, 0.55, 0.69)
    heart = mask(bl, 0.71, 0.8)
    col = mix(dough, _rgb(N, Lk, '#dab478'), gold)
    col = mix(col, _rgb(N, Lk, '#b27d43'), heart)
    # a few small charred blisters: irregular, soft-edged, darker at the heart
    cb = noise_tex(2.2, 3, 0.5, 1.2, 21.0).outputs['Fac']
    char_ring = mask(cb, 0.69, 0.75)
    col = mix(col, _rgb(N, Lk, '#c28c48'), char_ring)
    col = mix(col, _rgb(N, Lk, '#6e4828'), mask(cb, 0.755, 0.8))
    # fine freckles from the tawa
    fre = mask(noise_tex(6.0, 2, 0.5, 0.0, 7.0).outputs['Fac'], 0.65, 0.73)
    col = mix(col, _rgb(N, Lk, '#c08a4a'), fre)
    # baked rim: golden towards the edges
    att = N.new('ShaderNodeAttribute')
    att.attribute_name = 'rim'
    rimf = op('MULTIPLY', att.outputs['Fac'], 0.45)
    col = mix(col, _rgb(N, Lk, '#d8ae6c'), rimf)

    # herbs, chilli and nigella: a few cells of a warped Voronoi field
    def flecks(scale, w, frac, size, colour, warp_amt=0.3):
        warp = noise_tex(scale * 2.5, 2, 0.5, 0.0, w + 11.0)
        add = N.new('ShaderNodeVectorMath')
        add.operation = 'MULTIPLY_ADD'
        Lk.new(warp.outputs['Color'], add.inputs[0])
        add.inputs[1].default_value = (warp_amt / scale, warp_amt / scale, 0.0)
        Lk.new(pos, add.inputs[2])
        v = N.new('ShaderNodeTexVoronoi')
        v.voronoi_dimensions = '4D'
        v.inputs['Scale'].default_value = scale
        v.inputs['W'].default_value = w
        Lk.new(add.outputs[0], v.inputs['Vector'])
        sep = N.new('ShaderNodeSeparateColor')
        Lk.new(v.outputs['Color'], sep.inputs[0])
        f = op('MULTIPLY', op('LESS_THAN', sep.outputs[0], frac), op('LESS_THAN', v.outputs['Distance'], size))
        return f, _rgb(N, Lk, colour)

    herb_mask = None
    for sc, w, frac, size, c in ((2.0, 5.0, 0.42, 0.22, '#46681f'), (3.4, 9.0, 0.34, 0.17, '#2c4a15')):
        f, fc = flecks(sc, w, frac, size, c, warp_amt=0.55)
        col = mix(col, fc, f)
        herb_mask = f if herb_mask is None else op('MAXIMUM', herb_mask, f)
    f, fc = flecks(1.7, 13.0, 0.08, 0.12, '#b3371c')
    col = mix(col, fc, f)
    f, fc = flecks(2.6, 17.0, 0.16, 0.1, '#1d1a17', warp_amt=0.12)
    col = mix(col, fc, f)
    Lk.new(col, p.inputs['Base Color'])

    p.inputs['Roughness'].default_value = 0.5
    p.inputs['Specular IOR Level'].default_value = 0.4
    p.inputs['Subsurface Weight'].default_value = 0.12
    p.inputs['Subsurface Radius'].default_value = (0.35, 0.22, 0.12)
    p.inputs['Subsurface Scale'].default_value = 0.4

    # relief: blisters stand up, a fine flour texture, herbs sit proud
    fine = noise_tex(18.0, 3, 0.6, 0.0, 17.0).outputs['Fac']
    h = op('MULTIPLY_ADD', ramp(bl, [(0.4, (0, 0, 0, 1)), (0.75, (1, 1, 1, 1))]), 0.8)
    Lk.new(fine, h.node.inputs[2])
    h = op('ADD', h, op('MULTIPLY', herb_mask, 0.35))
    # small open pits of a leavened crumb
    pit = N.new('ShaderNodeTexVoronoi')
    pit.inputs['Scale'].default_value = 6.0
    Lk.new(pos, pit.inputs['Vector'])
    h = op('ADD', h, op('MULTIPLY', mask(pit.outputs['Distance'], 0.0, 0.22), 0.3))
    # soft undulation of the crumb and the raised blisters
    h = op('ADD', h, op('MULTIPLY', noise_tex(2.5, 3, 0.5, 0.0, 29.0).outputs['Fac'], 1.2))
    h = op('ADD', h, op('MULTIPLY', char_ring, 0.4))
    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.55
    bump.inputs['Distance'].default_value = 0.03
    Lk.new(h, bump.inputs['Height'])
    Lk.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


def _rgb(N, Lk, hexcol):
    from studio.core import rgba

    n = N.new('ShaderNodeRGB')
    n.outputs[0].default_value = rgba(hexcol)
    return n.outputs[0]


# ----------------------------------------------------------------- build


def matchbox(ctx, colourway, pull, x0=0.0, y0=0.0, seed=1.0, kmat=None):
    m = ctx.mat
    lay = ctx.shapes
    mats = {
        'top': m.board(f'label {colourway}', art=ctx.art(f'top-{colourway}.png'), roughness=0.5, coat=0.14, tooth=0.04),
        'front': m.board(f'striker {colourway} front', art=ctx.art('side.png'), roughness=0.72, coat=0.04, tooth=0.1),
        'back': None,
        'bottom': m.board(f'sleeve bottom {colourway}', color=CARD, roughness=0.55, coat=0.1, tooth=0.04),
        'inside': m.board(f'sleeve inside {colourway}', color='#e9e6dd', roughness=0.8, coat=0.0, tooth=0.05),
        'edge': m.solid(f'board edge {colourway}', '#dcd6c8', roughness=0.9),
    }
    mats['back'] = mats['front']
    sl = sleeve(f'sleeve-{colourway}', lay, mats, x0, y0)
    white = m.board(f'tray {colourway}', color='#f6f5f1', roughness=0.6, coat=0.06, tooth=0.04)
    tr = tray(f'tray-{colourway}', lay, white, x0 + pull, y0)
    tx = x0 + pull
    # The kulcha lies folded across the tray: the fold at the far end, inside
    # the sleeve, the rounded edges coming out towards the tray's open end.
    fold_x = tx - dims.TL / 2 + dims.TT + dims.KULCHA_BACK
    edge_x = tx + dims.TL / 2 - dims.TT - dims.KULCHA_FRONT
    half = dims.TW / 2 - dims.TT - 0.1
    kb = kulcha(
        f'kulcha-{colourway}',
        kmat or kulcha_material(),
        y0 - half,
        y0 + half,
        0.0,
        -(edge_x - fold_x),
        dims.T + dims.TB,
        seed=seed,
        turn=lambda x, y: (fold_x - y, x),  # a quarter turn: the fold across the tray
    )
    return [sl, tr, kb]


def _guard_studio_reset(core):
    """Workaround for a shared bug: studio.core keeps a module-level reference to
    the lights' target empty, which goes stale when core.reset() (a factory
    reset) runs between variants, so core.studio() raises ReferenceError. Clear
    the reference on every factory reset."""
    handlers = bpy.app.handlers.load_factory_startup_post
    if any(getattr(h, '__name__', '') == '_clear_light_target' for h in handlers):
        return

    @bpy.app.handlers.persistent
    def _clear_light_target(*_):
        core._ORIGIN = None

    handlers.append(_clear_light_target)


def _place(objs, x, y):
    """Turn a box built along x (tray towards +x) so the tray comes out towards
    -Y, and move it to (x, y) on the floor."""
    rot = Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(-math.pi / 2, 4, 'Z')
    for ob in objs:
        ob.matrix_world = rot @ ob.matrix_world
    bpy.context.view_layer.update()
    return objs


def build(ctx, variant=None):
    _guard_studio_reset(ctx.core)
    if variant == 'pair':
        km = kulcha_material()
        front = _place(matchbox(ctx, 'green', dims.PULL['green'], seed=1.0, kmat=km), *dims.PAIR['green'])
        back = _place(matchbox(ctx, 'red', dims.PULL['red-back'], seed=4.0, kmat=km), *dims.PAIR['red'])
        return front + back
    return _place(matchbox(ctx, 'red', dims.PULL['red']), 0.0, 0.0)
