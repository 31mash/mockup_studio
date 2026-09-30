// Text metrics for make_art.py, measured in the same Chromium and with the
// same @fontsource fonts that tools/raster.mjs uses, so artwork built from
// them lines up exactly with the rasterized text.
//
//   echo '{"runs": [...], "glyphs": [...]}' | node products/posters/measure.mjs
//
// runs:   [{text, family, weight, size, ls}]  (size and ls in SVG user units)
//         -> starts: x of every character's origin as laid out in an SVG
//            <text> at x = 0 (kerning and letter-spacing included), and end.
// glyphs: [{ch, family, weight}]
//         -> ink box at font-size 1000: adv, l, r (x from the origin),
//            asc, desc (above / below the baseline), and rows: the ink runs
//            [x0, x1] at 30, 50 and 70 % of the glyph's height (its stems).

import { chromium } from '@playwright/test';
import { existsSync, readdirSync, readFileSync, unlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const FONT_DIR = join(ROOT, 'node_modules', '@fontsource');

function fontCss() {
  if (!existsSync(FONT_DIR)) throw new Error('Run npm install in mockups/ first.');
  const rules = [];
  for (const pkg of readdirSync(FONT_DIR).sort()) {
    for (const f of readdirSync(join(FONT_DIR, pkg))) {
      if (/^\d{3}(-italic)?\.css$/.test(f)) rules.push(`@import url("${pathToFileURL(join(FONT_DIR, pkg, f)).href}");`);
    }
  }
  return rules.join('\n');
}

const req = JSON.parse(readFileSync(0, 'utf8'));
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  // Loaded from a file (not setContent) so the file:// font CSS may load.
  const tmp = join(tmpdir(), `posters-measure-${process.pid}.html`);
  writeFileSync(tmp, `<!doctype html><html><head><meta charset="utf-8"><style>${fontCss()}</style></head><body></body></html>`);
  try {
    await page.goto(pathToFileURL(tmp).href, { waitUntil: 'load' });
  } finally {
    unlinkSync(tmp);
  }
  const out = await page.evaluate(async (req) => {
    const faces = new Set([...req.runs, ...req.glyphs].map((r) => `${r.weight} 100px "${r.family}"`));
    for (const f of faces) {
      const got = await document.fonts.load(f, 'Aay');
      if (!got.length) throw new Error(`font not available: ${f}`);
    }
    await document.fonts.ready;

    const NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', '4000');
    svg.setAttribute('height', '1000');
    document.body.appendChild(svg);
    const runs = req.runs.map((r) => {
      const t = document.createElementNS(NS, 'text');
      t.setAttribute('x', '0');
      t.setAttribute('y', '500');
      t.setAttribute('font-family', r.family);
      t.setAttribute('font-weight', String(r.weight));
      t.setAttribute('font-size', String(r.size));
      t.setAttribute('letter-spacing', String(r.ls || 0));
      t.setAttribute('style', 'white-space:pre');
      t.textContent = r.text;
      svg.appendChild(t);
      const n = t.getNumberOfChars();
      const starts = [];
      for (let i = 0; i < n; i++) starts.push(t.getStartPositionOfChar(i).x);
      const end = n ? t.getEndPositionOfChar(n - 1).x : 0;
      t.remove();
      return { starts, end };
    });

    // Ink by scanning pixels (measureText's ink boxes are coarse): the glyph
    // is drawn at 1000 px with its origin at (OX, OY).
    const S = 2400, OX = 700, OY = 1500;
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = S;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    const glyphs = req.glyphs.map((g) => {
      ctx.clearRect(0, 0, S, S);
      ctx.font = `${g.weight} 1000px "${g.family}"`;
      ctx.fillStyle = '#000';
      ctx.fillText(g.ch, OX, OY);
      const px = ctx.getImageData(0, 0, S, S).data;
      const ink = (x, y) => px[(y * S + x) * 4 + 3] > 127;
      let x0 = S, x1 = -1, y0 = S, y1 = -1;
      for (let y = 0; y < S; y++)
        for (let x = 0; x < S; x++)
          if (ink(x, y)) {
            if (x < x0) x0 = x;
            if (x > x1) x1 = x;
            if (y < y0) y0 = y;
            if (y > y1) y1 = y;
          }
      // Horizontal ink runs at a few heights above the baseline (stems).
      const runsAt = (h) => {
        const y = Math.round(OY - h);
        const out = [];
        let s = -1;
        for (let x = 0; x <= S; x++) {
          const on = x < S && ink(x, y);
          if (on && s < 0) s = x;
          if (!on && s >= 0) {
            out.push([s - OX, x - OX]);
            s = -1;
          }
        }
        return out;
      };
      const asc = OY - y0;
      return {
        adv: ctx.measureText(g.ch).width,
        l: x0 - OX,
        r: x1 + 1 - OX,
        asc,
        desc: y1 + 1 - OY,
        rows: { q1: runsAt(asc * 0.3), mid: runsAt(asc * 0.5), q3: runsAt(asc * 0.7) },
      };
    });
    return { runs, glyphs };
  }, req);
  process.stdout.write(JSON.stringify(out));
} finally {
  await browser.close();
}
