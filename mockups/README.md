# IndiGo food packaging: 3D product mockups

Clean studio product shots of the IndiGo in-flight food packaging in `source/indigo-food-spread.webp`, from several angles, in the style of `source/nut-case-reference.jpg`: a flat light-grey sweep (#d1d2d6), soft even light, a short soft contact shadow, and the artwork reproduced at its printed colour.

Every product is a real 3D model rendered with Blender's Cycles path tracer, so light, shadow and reflections are physically consistent between shots. Every shot comes as:

- `renders/<product>/<shot>.jpg`: on the studio grey, 2000 × 1280 px (the reference's size);
- `renders/<product>/<shot>.png`: the same shot with a transparent background and its shadow, to place on any colour.

## How it's built

```text
source/            the spread, the Nut Case reference render, and crops/ of every product
studio/            the shared studio: core.py (scene, lights, camera presets, render and
                   composite), shapes.py (tins, walls, beads, cartons), layout.py (outlines
                   and artwork positions, no Blender needed), materials.py
brand/indigo.py    IndiGo pieces for artwork: the dotted plane, colours, font, veg marks
tools/raster.mjs   artwork SVG/HTML to PNG, with 35 bundled font families
products/<id>/     one folder per product: dims.py, make_art.py, art/, product.py, preview/
render.py          renders a product's shots
renders/           final shots
```

The artwork is recreated as clean vector files from the spread. The spread is a low-resolution photograph, so recreated artwork is what keeps the mockups sharp. To use the original print files instead, replace the PNGs in `products/<id>/art/` (same names and proportions) and render again.

## Requirements

- Python 3.11 with Blender as a module: `pip install bpy` (5.0), and Pillow.
- Node 18+ for artwork: `npm install` in this folder (fonts and Playwright's Chromium).

## Render

```bash
cd mockups
python3 products/nut-case/make_art.py && node tools/raster.mjs products/nut-case/art   # artwork
python3 render.py nut-case --preview          # 800 x 512 previews in products/nut-case/preview/
python3 render.py nut-case                    # finals in renders/nut-case/
python3 render.py nut-case --shots hero,top   # some shots only
```

A preview takes about 13 s on 4 CPU cores; a final about a minute.

## The studio

- **Units**: centimetres. Model products at their real size; the camera frames them automatically.
- **Orientation**: the product's front faces -Y (towards the default camera), up is +Z, and it stands on the floor at z = 0.
- **Light**: three large softboxes (overhead, key from camera right, fill from camera left) plus a soft grey world. The rig turns with the camera, so every angle is lit the same way relative to the lens. Calibrated so a face turned to the camera shows its artwork at about its printed colour: the Nut Case blue and green render within a few levels of the reference.
- **Colour**: the Standard view transform, so brand colours are not tone-mapped. Artwork PNGs are sRGB.
- **Floor**: a shadow catcher, so the PNGs carry only the product and its shadow.

### Camera presets (`studio/core.py`)

Azimuth is measured from the front, positive towards the product's left (the camera moves left and sees the front-left corner, as in the reference). Elevation is above the horizon.

| Preset | Azimuth | Elevation | Notes |
|---|---|---|---|
| `hero` | 31° | 38° | The reference's angle, 100 mm lens |
| `hero-right` | -31° | 38° | Mirror of hero |
| `front` | 0° | 10° | |
| `side` | 90° | 10° | The product's left side |
| `back` | 150° | 32° | Three-quarter from behind |
| `top` | 0° | 90° | Flat lay, front at the bottom |
| `low` | 28° | 7° | Nearly eye level, heroic |
| `high` | 20° | 62° | |

A product's `SHOTS` list mixes preset names and dicts that override them: `{'name': 'set-hero', 'preset': 'hero', 'fill': 0.62, 'variant': 'set'}`. `fill` is how much of the frame the product fills (0.56 for hero).

## Adding a product

`products/<id>/product.py`:

```python
TITLE = 'Nut Case tin'
SHOTS = ['hero', 'hero-right', 'front', 'side', 'back', 'top']
VARIANTS = [None]           # optional; a shot's 'variant' is passed to build()

def build(ctx, variant=None):
    m, s = ctx.mat, ctx.shapes      # studio.materials, studio.shapes
    art = ctx.art('lid-top.png')    # products/<id>/art/lid-top.png
    ...
    return [objects that make up the product]   # used for framing
```

`products/nut-case/` is the worked example: `dims.py` holds the sizes, `make_art.py` writes the SVG artwork laid out on those sizes (with `studio.layout.wrap_layout` for wrap-around walls), and `product.py` builds the model.

### Artwork

- Write artwork as SVG (or HTML for long flowing text) in `art/`, one file per surface, then `node tools/raster.mjs products/<id>/art`. Each file becomes a PNG beside it; files starting with `_` are skipped.
- Size the artwork on the real surface: `brand/indigo.svg()` uses 100 units per cm. `data-width` sets the PNG width (default 4096; use up to 12288 for long wrap strips).
- Fonts by family name: Comfortaa (IndiGo's rounded lettering), Quicksand, Varela Round, Nunito, Noto Sans/Serif Devanagari, Tiro Devanagari Hindi, Mukta, Noto Sans/Serif Tamil, Alfa Slab One, Roboto Slab, Zilla Slab, Bevan, Rye, Abril Fatface, Playfair Display, Oswald, Bebas Neue, Archivo Black, Archivo, Anton, Pacifico, Lobster, Kalam, Special Elite, Inter, Libre Baskerville, Old Standard TT, Courier Prime, Fredoka, Baloo 2, Yatra One, Permanent Marker, Caveat Brush.
- Brand pieces: `brand.indigo.plane_svg()` (the dotted plane, measured from the posters), `veg_mark()`, `nonveg_mark()`, `INDIGO_BLUE`, `INDIGO_GREEN`, `FONT`.

UV conventions (`studio/shapes.py`):

- **Caps** (lid tops, bottoms): planar; the image is the surface seen from above, with the product's front edge at the bottom of the image.
- **Walls** (`walled_shell`, `slip_lid_tin`): one wrap strip; u runs counter-clockwise seen from above, starting at the left end of the front face (round shapes: at the front centre, going right); v runs up. `wrap_layout(w, d, r)` says where each face lands in the strip.
- **Cartons** (`carton`): one image per face, upright as seen from outside.

### Materials (`studio/materials.py`)

`printed_metal` (lithographed tin under satin lacquer), `bare_metal` (seams, beads, rims), `board` (printed paperboard), `kraft` (brown paper; artwork multiplies over it), `foil` (trays), `clear_film` (windows and pouches; artwork alpha marks opaque ink), `tissue` (napkins), `solid`, `textured` (colour maps such as food).
