"""Namkeen pouch artwork: white ink on clear film, laid out on the flat film
panel (1 unit = 0.1 mm). Transparent pixels stay clear film; the alpha channel
is ink opacity, so the heat seals are a faint white haze and the copy is solid
white ink. Run:

    python3 products/snack-pouch/make_art.py && node tools/raster.mjs products/snack-pouch/art
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

from brand.indigo import FONT, plane_svg, veg_mark  # noqa: E402

import dims  # noqa: E402

U = 100  # units per cm
W, H = dims.W * U, dims.H * U
ART = os.path.join(HERE, 'art')
os.makedirs(ART, exist_ok=True)

# The copy on the front, as printed on the pouch (the photo's words, with the
# few unreadable ones filled in). Set as one justified paragraph.
STORY = (
    'Omprakash Vaishnav has been dedicated to Namkeen for 30 years. '
    'And it doesn\u2019t stop there. His father started making it in 1962 and it\u2019s been running ever since. '
    'Omprakash doesn\u2019t want to make anything else. He doesn\u2019t want to expand into other snack varieties. '
    'Omprakash wants to focus and continue to focus on the very Namkeen you are holding. '
    'And the recipe is quite simple for him. Use the best ingredients, no colours or artificial preservatives. '
    'Just pure natural ingredients and pure oil. '
    'Made in a small village in Jodhpur, this is quite possibly the best Namkeen ever in the sky.'
)


def seals_svg() -> str:
    """Heat seals: a faint frosted haze with the fine crimp lines the sealing
    jaws leave, on the side seals, the top seal, the zip band and the curved
    gusset seal at the bottom corners."""
    s = dims.SEAL * U
    top = dims.TOP_SEAL * U
    bot = dims.BOTTOM_SEAL * U
    zc = dims.ZIP * U
    zg = dims.ZIP_GAP * U
    gc = dims.GUSSET_CURVE * U
    gx = 3.3 * U  # where the gusset curve meets the bottom seal
    haze = 'rgba(255,255,255,0.17)'
    crimp = 'rgba(255,255,255,0.13)'
    pitch = 9
    parts = [
        '<defs>'
        f'<pattern id="crimp" width="{pitch}" height="{pitch}" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<rect width="{pitch * 0.45}" height="{pitch}" fill="{crimp}"/></pattern>'
        '</defs>'
    ]
    shapes = [
        f'<rect x="0" y="0" width="{s}" height="{H}"/>',
        f'<rect x="{W - s}" y="0" width="{s}" height="{H}"/>',
        f'<rect x="{s}" y="0" width="{W - 2 * s}" height="{top}"/>',
        f'<rect x="{s}" y="{H - bot}" width="{W - 2 * s}" height="{bot}"/>',
        # Gusset corner seals: the classic curve from the side seal down to the bottom.
        f'<path d="M{s},{H - gc} C{s + 0.2 * U},{H - gc * 0.38} {gx * 0.55},{H - bot * 1.05} {gx},{H - bot} L{s},{H - bot} Z"/>',
        f'<path d="M{W - s},{H - gc} C{W - s - 0.2 * U},{H - gc * 0.38} {W - gx * 0.55},{H - bot * 1.05} {W - gx},{H - bot} L{W - s},{H - bot} Z"/>',
    ]
    body = ''.join(shapes)
    parts.append(f'<g fill="{haze}">{body}</g><g fill="url(#crimp)">{body}</g>')
    # Zip: a faint milky band between the two tracks (the tracks are modelled).
    parts.append(f'<rect x="{s}" y="{zc - zg / 2}" width="{W - 2 * s}" height="{zg}" fill="rgba(255,255,255,0.07)"/>')
    return ''.join(parts)


def page(inner_svg: str, html_body: str = '') -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
#art {{ position: relative; overflow: hidden; background: transparent; }}
#art svg {{ position: absolute; left: 0; top: 0; }}
.story {{ position: absolute; font-family: '{FONT}'; font-weight: 700; color: rgba(255,255,255,0.97);
         font-size: 40px; line-height: 56.5px; text-align: justify; hyphens: none; text-wrap: pretty; }}
.small {{ position: absolute; font-family: '{FONT}'; font-weight: 700; color: rgba(255,255,255,0.97);
         text-align: center; width: 100%; left: 0; }}
</style></head>
<body><div id="art" data-width="4096" style="width:{W:.0f}px;height:{H:.0f}px">
<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">{inner_svg}</svg>
{html_body}
</div></body></html>
"""


# Front: the story, set justified in IndiGo's rounded type, white ink.
left, width, top = 2.1 * U, 8.3 * U, 3.62 * U
story = f'<div class="story" style="left:{left:.0f}px;top:{top:.0f}px;width:{width:.0f}px">{STORY}</div>'
open(os.path.join(ART, 'front.html'), 'w').write(page(seals_svg(), story))

# Back (drawn as seen from behind): the plane mark, veg mark and a few small
# lines low on the panel, where the namkeen hides them from the front.
cx = W / 2
back_svg = seals_svg() + plane_svg(cx, 9.3 * U, 1.7 * U, color='#ffffff') + veg_mark(cx - 0.3 * U, 12.35 * U, 0.6 * U)
back_text = (
    f'<div class="small" style="top:{10.45 * U:.0f}px;font-size:{0.62 * U:.0f}px;letter-spacing:-1px">Namkeen</div>'
    f'<div class="small" style="top:{11.3 * U:.0f}px;font-size:{0.25 * U:.0f}px;line-height:{0.38 * U:.0f}px;font-weight:600">'
    'Handmade in Jodhpur for IndiGo<br>Gram flour, vegetable oil, salt and spices</div>'
    f'<div class="small" style="top:{13.25 * U:.0f}px;font-size:{0.22 * U:.0f}px;font-weight:600">Net wt. 60 g</div>'
)
open(os.path.join(ART, 'back.html'), 'w').write(page(back_svg, back_text))
print('art written')
