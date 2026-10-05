"""Builds the mockup gallery page: site/index.html plus thumbnails.

    python3 tools/gallery.py

The page shows every product's final shots (renders/<id>/*.jpg), its
original from the spread (source/crops/), and opens any shot full size.
Full-size images are not copied: publish them from renders/ under full/.
"""

import glob
import html
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(HERE, 'site')

# Gallery order and copy: tins, canisters, cartons, bags, paper, print.
PRODUCTS = [
    ('nut-case', 'Nut Case', 'Slip-lid nut tin in IndiGo blue and green. The studio was calibrated on it: its hero matches the reference render.', ['nut-case-tin']),
    ('cookie-tins', 'Cookie tins', 'Reusable round tins, Chocolate chip and Oatmeal + Honey, with gold seams. Shown alone, as a set of three, and open.', ['cookie-tins']),
    ('smoked-almonds-tin', 'Smoked Almonds', 'Shallow matte-black tin with metallic bronze almond engraving.', ['smoked-almonds-tin']),
    ('gadget-tin', 'Gadget tin', 'Reusable sky-blue tin printed all round with white silhouettes of small gadgets.', ['gadget-tin']),
    ('stick-man-canisters', 'Stick Man', 'Potato-stick canisters in brown, pink and navy with gold rims; the stick men lose their limbs from can to can.', ['stick-man-canisters']),
    ('tiffin-wedge', 'Tiffin', 'Sandwich wedges in two colourways, with story panels and exercise ends. The sandwich in the window is the pack\'s own photograph.', ['tiffin-wedge-front', 'tiffin-wedge-love-story-back', 'tiffin-wedge-soulitude-end']),
    ('deblue-burger-box', 'DaBlue Burger', 'Folk-printed clamshell for the Dabeli burger, with peacocks and Gujarati lettering.', ['deblue-burger-box']),
    ('spicy-kulcha-box', 'Spicy Kulcha', 'Matchbox-style sleeve and tray with a retro film-poster label.', ['spicy-kulcha-matchboxes']),
    ('mini-dosai-box', 'Mini Dosai', 'Cream sleeve over a foil tray, chicken in red and veg in green, with engraved illustrations and Tamil lettering.', ['mini-dosai-boxes']),
    ('chandni-chowk-bag', 'Chandni Chowk to the Sky', 'Newsprint samosa bag with a blue rubber stamp over a Hindi newspaper page.', ['chandni-chowk-bag', 'samosa']),
    ('bunji-bag', 'Bunji!', 'Kraft paper bag with red lettering and a line-drawn figure.', ['bunji-bag']),
    ('snack-pouch', 'Namkeen pouch', 'Clear stand-up zip pouch filled with bhujia sticks, printed in white ink.', ['snack-pouch']),
    ('napkin', 'Napkin', 'Quarter-folded paper napkin with an embossed border and a line of Hindi.', ['napkin']),
    ('posters', 'Posters', '"Thought for food" and "Say no to airline food", standing and laid flat.', ['poster-thought-for-food', 'poster-say-no']),
]

SHOT_LABELS = {
    'hero': 'Hero',
    'hero-right': 'Hero, right',
    'front': 'Front',
    'side': 'Side',
    'back': 'Back',
    'top': 'Top-down',
    'low': 'Low angle',
    'high': 'High angle',
    'open': 'Open',
    'stack': 'Stack',
    'flatlay': 'Flat lay',
    'flatlay-high': 'Flat lay, high',
    'set-hero': 'Set',
    'set-front': 'Set, front',
    'pair-hero': 'Pair',
    'pair-top': 'Pair, top-down',
    'stack-hero': 'Stack',
    'stack-top': 'Stack, top-down',
    'three-quarter': 'Three-quarter',
    'spread-angle': 'As in the spread',
    'samosa-hero': 'With samosa',
    'oatmeal-hero': 'Oatmeal + Honey',
    'pink-hero': 'Pink can',
    'navy-hero': 'Navy can',
    'big-don-hero': 'Big Don colourway',
    'front-say-no': 'Front, Say no',
}


def shot_order(pid: str) -> list[str]:
    import sys

    sys.path.insert(0, os.path.join(HERE, 'tools'))
    import render_all

    return render_all.shot_names(pid)


def thumb(src: str, dst: str, width: int) -> tuple[int, int]:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src).convert('RGB')
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, quality=84, optimize=True, progressive=True)
    return im.size


def main():
    products = []
    for pid, name, blurb, crops in PRODUCTS:
        order = shot_order(pid)
        shots = []
        for s in order:
            full = os.path.join(HERE, 'renders', pid, f'{s}.jpg')
            if not os.path.exists(full):
                continue
            w, h = thumb(full, os.path.join(SITE, 'thumbs', pid, f'{s}.jpg'), 960)
            shots.append({'id': s, 'label': SHOT_LABELS.get(s, s.replace('-', ' ').capitalize()), 'thumb': f'thumbs/{pid}/{s}.jpg', 'full': f'full/{pid}/{s}.jpg'})
        originals = []
        for c in crops:
            src = os.path.join(HERE, 'source', 'crops', f'{c}.png')
            thumb(src, os.path.join(SITE, 'originals', f'{c}.jpg'), 520)
            originals.append(f'originals/{c}.jpg')
        if shots:
            products.append({'id': pid, 'name': name, 'blurb': blurb, 'shots': shots, 'originals': originals})

    total = sum(len(p['shots']) for p in products)
    e = html.escape
    sections = []
    for p in products:
        figs = []
        for i, s in enumerate(p['shots']):
            figs.append(
                f'<figure><button type="button" data-full="{s["full"]}" data-product="{e(p["name"])}" data-label="{e(s["label"])}" aria-label="{e(p["name"])}, {e(s["label"])}, open full size">'
                f'<img src="{s["thumb"]}" alt="{e(p["name"])}, {e(s["label"])}" width="960" height="614" loading="{"eager" if i == 0 and p is products[0] else "lazy"}" decoding="async"></button>'
                f'<figcaption><span>{e(s["label"])}</span></figcaption></figure>'
            )
        origins = ''.join(f'<img src="{o}" alt="Original in the spread" loading="lazy">' for o in p['originals'])
        sections.append(
            f'<section class="product" id="{p["id"]}"><div class="head"><div><h2>{e(p["name"])}</h2><p>{e(p["blurb"])}</p></div>'
            f'<div class="origin"><span>In the spread</span><div>{origins}</div></div></div>'
            f'<div class="shots">{"".join(figs)}</div></section>'
        )
    sys.path.insert(0, os.path.join(HERE, 'tools'))
    from brand_plane import plane_dots_svg

    page = (
        TEMPLATE.replace('{{SECTIONS}}', '\n'.join(sections))
        .replace('{{COUNT}}', str(total))
        .replace('{{PRODUCTS}}', str(len(products)))
        .replace('{{PLANE}}', plane_dots_svg())
        .replace('{{INDEX}}', ''.join(f'<li><a href="#{p["id"]}">{e(p["name"])}</a></li>' for p in products))
    )
    os.makedirs(SITE, exist_ok=True)
    with open(os.path.join(SITE, 'index.html'), 'w') as f:
        f.write(page)
    files = {}
    for p in products:
        for s in p['shots']:
            files[s['thumb']] = os.path.relpath(os.path.join(SITE, s['thumb']), os.path.dirname(HERE))
            files[s['full']] = os.path.relpath(os.path.join(HERE, 'renders', p['id'], f"{s['id']}.jpg"), os.path.dirname(HERE))
        for o in p['originals']:
            files[o] = os.path.relpath(os.path.join(SITE, o), os.path.dirname(HERE))
    with open(os.path.join(SITE, 'files.json'), 'w') as f:
        json.dump(files, f, indent=1)
    print(f'site/index.html: {len(products)} products, {total} shots, {len(files)} files')


TEMPLATE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery_template.html')).read() if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery_template.html')) else ''

if __name__ == '__main__':
    main()
