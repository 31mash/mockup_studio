"""Studio: scene, light rig, camera presets and rendering for product mockups.

Matches the look of source/nut-case-reference.jpg: a flat light-grey sweep
(#d1d2d6), very even soft light from above and the front, and a short, soft
contact shadow. Renders are made once with a transparent background (the floor
is a shadow catcher), then composited onto the studio grey, so every shot comes
as both a finished JPG and a PNG cut-out with its shadow.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

BACKGROUND = (209, 210, 214)  # sRGB, sampled from the reference render
FINAL_SIZE = (2000, 1280)  # the reference's size
PREVIEW_SIZE = (800, 512)


def srgb_to_linear(c: float) -> float:
    c = c / 255.0 if c > 1 else c
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgba(hex_or_tuple, alpha: float = 1.0):
    """Linear RGBA from '#rrggbb' or an sRGB 0-255 tuple, for node inputs."""
    if isinstance(hex_or_tuple, str):
        h = hex_or_tuple.lstrip('#')
        t = tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    else:
        t = hex_or_tuple
    return (*(srgb_to_linear(v) for v in t[:3]), alpha)


# ----------------------------------------------------------------- scene


def reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 0.01  # 1 Blender unit = 1 cm: products are modelled in centimetres


def configure_render(preview: bool = False, size: tuple[int, int] | None = None, samples: int | None = None) -> None:
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples or (24 if preview else 160)
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02 if preview else 0.006
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.cycles.max_bounces = 8
    sc.cycles.transparent_max_bounces = 16
    sc.cycles.transmission_bounces = 8
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    w, h = size or (PREVIEW_SIZE if preview else FINAL_SIZE)
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '8'
    # Standard keeps printed brand colours as printed; the light rig is set
    # so a lit face shows its artwork at about its flat colour.
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0


@dataclass
class Rig:
    key: bpy.types.Object
    fill: bpy.types.Object
    top: bpy.types.Object
    floor: bpy.types.Object
    extras: list = field(default_factory=list)


def studio() -> Rig:
    """Floor, world and softboxes. aim_lights() turns the softboxes with the
    camera, so every angle is lit the same way relative to the lens."""
    sc = bpy.context.scene

    world = bpy.data.worlds.new('studio')
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = rgba((238, 239, 242))
    bg.inputs['Strength'].default_value = 0.45

    # Shadow-catching floor: transparent in the render, but it still takes
    # shadows and blocks and bounces light like the grey paper sweep would.
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = 'floor'
    floor.is_shadow_catcher = True
    mat = bpy.data.materials.new('floor')
    mat.use_nodes = True
    p = mat.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = rgba(BACKGROUND)
    p.inputs['Roughness'].default_value = 0.95
    floor.data.materials.append(mat)

    bpy.ops.object.empty_add(location=(0, 0, 0))
    turntable = bpy.context.object
    turntable.name = 'light-turntable'

    def area(name, loc, size, energy, color=(1, 1, 1)):
        bpy.ops.object.light_add(type='AREA', location=loc)
        L = bpy.context.object
        L.name = name
        L.parent = turntable
        L.data.shape = 'RECTANGLE'
        L.data.size, L.data.size_y = size
        L.data.energy = energy
        L.data.color = color
        track = L.constraints.new('TRACK_TO')
        track.target = _origin_empty()
        track.track_axis = 'TRACK_NEGATIVE_Z'
        track.up_axis = 'UP_Y'
        return L

    def at(x, y, z):
        return (x, y, z)

    # Big overhead softbox: short, soft shadows like the reference.
    # Calibrated so a face turned to the lens shows its artwork at about its
    # printed colour, the top a touch darker, and the camera-left side about
    # half as bright, as in the reference.
    top = area('softbox-top', at(10, -18, 120), (140, 110), 62_000)
    # Key from camera right and high.
    key = area('softbox-key', at(70, -120, 90), (120, 90), 118_000)
    # Gentle fill from camera left, so that side never goes flat.
    fill = area('softbox-fill', at(-110, -60, 40), (100, 80), 26_000)
    return Rig(key=key, fill=fill, top=top, floor=floor, extras=[turntable])


def aim_lights(rig: Rig, azimuth: float, target) -> None:
    """Keeps the light rig in the same place relative to the camera."""
    rig.extras[0].rotation_euler = (0, 0, math.radians(-azimuth))
    _origin_empty().location = target
    bpy.context.view_layer.update()


_ORIGIN = None


def _origin_empty():
    global _ORIGIN
    if _ORIGIN is None or _ORIGIN.name not in bpy.data.objects:
        bpy.ops.object.empty_add(location=(0, 0, 8))
        _ORIGIN = bpy.context.object
        _ORIGIN.name = 'light-target'
    return _ORIGIN


# ----------------------------------------------------------------- camera

# Camera positions around a product whose front faces -Y. Azimuth is measured
# from the front, positive towards the product's left side (the camera moves
# to its left and looks back at the front-left corner, like the reference).
PRESETS: dict[str, dict] = {
    'hero': dict(azimuth=31, elevation=38, lens=100, fill=0.56),
    'hero-right': dict(azimuth=-31, elevation=38, lens=100, fill=0.56),
    'front': dict(azimuth=0, elevation=10, lens=85, fill=0.5),
    'side': dict(azimuth=90, elevation=10, lens=85, fill=0.5),
    'back': dict(azimuth=150, elevation=32, lens=85, fill=0.52),
    'top': dict(azimuth=0, elevation=90, lens=85, fill=0.55),
    'low': dict(azimuth=28, elevation=7, lens=85, fill=0.52),
    'high': dict(azimuth=20, elevation=62, lens=85, fill=0.52),
}


def _mesh_points(objs):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        if o.type != 'MESH':
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        step = max(1, len(me.vertices) // 4000)
        verts = me.vertices
        pts.extend(mw @ verts[i].co for i in range(0, len(verts), step))
        ev.to_mesh_clear()
    return pts


def place_camera(objs, azimuth=33, elevation=36, lens=85, fill=0.52, roll=0.0, target=None, shift=(0.0, 0.0)):
    """Aims a camera at the product and sets the distance so its projected
    size fills `fill` of the frame's limiting side."""
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None:
        bpy.ops.object.camera_add()
        cam = bpy.context.object
        sc.camera = cam
    cam.data.lens = lens
    cam.data.sensor_fit = 'HORIZONTAL'
    cam.data.sensor_width = 36
    cam.data.clip_start = 0.5
    cam.data.clip_end = 5000

    pts = _mesh_points(objs)
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = target if target is not None else (lo + hi) / 2

    az = math.radians(azimuth)
    el = math.radians(min(elevation, 89.95))
    direction = Vector((-math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))

    def aim(dist):
        cam.location = center + direction * dist
        look = (center - cam.location).normalized()
        # Keep verticals upright; for top-down, the product's front is at the bottom.
        rot = look.to_track_quat('-Z', 'Y' if elevation < 89 else 'Y')
        cam.rotation_euler = rot.to_euler()
        if elevation >= 89:
            cam.rotation_euler = (0, 0, -az)
        cam.rotation_euler.rotate_axis('Z', math.radians(roll))
        cam.data.shift_x, cam.data.shift_y = shift
        bpy.context.view_layer.update()

    w, h = sc.render.resolution_x, sc.render.resolution_y
    aspect = w / h

    # Fit: the product's larger projected side (in frame units) equals `fill`,
    # with height measured against the frame's own height.
    def size(dist):
        aim(dist)
        xs, ys = [], []
        for p in pts:
            c = world_to_camera_view(sc, cam, p)
            xs.append(c.x)
            ys.append(c.y)
        return max(max(xs) - min(xs), (max(ys) - min(ys)) * 0.78), xs, ys

    lo_d, hi_d = 1.0, 20000.0
    for _ in range(40):
        mid = math.sqrt(lo_d * hi_d)
        s, _, _ = size(mid)
        if s > fill:
            lo_d = mid
        else:
            hi_d = mid
    s, xs, ys = size(hi_d)
    # Centre the product's projection in the frame (a touch above centre, like the reference).
    cx = (max(xs) + min(xs)) / 2 - 0.5
    cy = (max(ys) + min(ys)) / 2 - 0.52
    cam.data.shift_x = shift[0] + cx
    cam.data.shift_y = shift[1] + cy * (h / w)
    return cam


# ----------------------------------------------------------------- output


def render_to(path_png: str) -> None:
    sc = bpy.context.scene
    os.makedirs(os.path.dirname(path_png), exist_ok=True)
    sc.render.filepath = path_png
    bpy.ops.render.render(write_still=True)


def composite(path_png: str, path_jpg: str, background=BACKGROUND, quality: int = 93) -> None:
    """The transparent render (with its shadow) over the flat studio grey."""
    from PIL import Image

    fg = Image.open(path_png).convert('RGBA')
    bg = Image.new('RGBA', fg.size, (*background, 255))
    bg.alpha_composite(fg)
    bg.convert('RGB').save(path_jpg, quality=quality, subsampling=0, optimize=True)
