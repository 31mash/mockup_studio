"""Contact sheet of every final render: renders/contact-sheet.jpg.

    python3 tools/contact_sheet.py            # finals in renders/
    python3 tools/contact_sheet.py --preview  # previews in products/*/preview/
"""

import argparse
import glob
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = (209, 210, 214)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--cols', type=int, default=4)
    ap.add_argument('--tile', type=int, default=480)
    a = ap.parse_args()

    if a.preview:
        groups = {os.path.basename(os.path.dirname(os.path.dirname(p))): sorted(glob.glob(os.path.join(p, '*.jpg'))) for p in sorted(glob.glob(os.path.join(HERE, 'products', '*', 'preview/')))}
        out = os.path.join(HERE, 'renders', 'preview-sheet.jpg')
    else:
        groups = {os.path.basename(p.rstrip('/')): sorted(glob.glob(os.path.join(p, '*.jpg'))) for p in sorted(glob.glob(os.path.join(HERE, 'renders', '*/')))}
        out = os.path.join(HERE, 'renders', 'contact-sheet.jpg')
    groups = {k: v for k, v in groups.items() if v}

    tw, th = a.tile, int(a.tile * 0.64)
    label_h = 44
    rows = []
    for name, files in groups.items():
        for i in range(0, len(files), a.cols):
            rows.append((name if i == 0 else None, files[i : i + a.cols]))
    W = a.cols * tw
    H = sum(th + (label_h if n else 0) for n, _ in rows)
    sheet = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
        small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
    except OSError:
        font = small = ImageFont.load_default()
    y = 0
    for name, files in rows:
        if name:
            d.rectangle((0, y, W, y + label_h), fill=(37, 36, 42))
            d.text((14, y + 10), name, fill=(240, 240, 230), font=font)
            y += label_h
        for i, f in enumerate(files):
            im = Image.open(f).convert('RGB')
            im.thumbnail((tw, th))
            sheet.paste(im, (i * tw + (tw - im.width) // 2, y + (th - im.height) // 2))
            d.text((i * tw + 10, y + th - 24), os.path.basename(f)[:-4], fill=(60, 60, 66), font=small)
        y += th
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out, quality=88)
    print(out, sheet.size)


if __name__ == '__main__':
    main()
