// Rasterizes flat artwork (SVG or HTML) to PNG textures for the Blender scenes.
//
//   node tools/raster.mjs products/nut-case/art/lid-top.svg [more files...]
//   node tools/raster.mjs products/nut-case/art            (every .svg/.html in it)
//
// Each file becomes a PNG beside it, with the same name. The output width comes
// from --width, else the root element's data-width attribute, else 4096 px; the
// height follows the artwork's aspect ratio. Transparent areas stay transparent.
//
// Every @fontsource family installed in mockups/node_modules is available by
// its family name (for example "Comfortaa", "Noto Sans Devanagari",
// "Noto Serif Tamil", "Alfa Slab One"), in every installed weight. Relative
// <image href> and CSS url() paths resolve from the artwork's own folder.

import { chromium } from '@playwright/test';
import { existsSync, readdirSync, readFileSync, statSync, writeFileSync, unlinkSync } from 'node:fs';
import { basename, dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const FONT_DIR = join(ROOT, 'node_modules', '@fontsource');

function fontCss() {
  if (!existsSync(FONT_DIR)) throw new Error('Run npm install in mockups/ first.');
  const rules = [];
  for (const pkg of readdirSync(FONT_DIR).sort()) {
    for (const f of readdirSync(join(FONT_DIR, pkg))) {
      // "400.css", "700-italic.css": every subset (latin, devanagari, tamil...) of that weight.
      if (/^\d{3}(-italic)?\.css$/.test(f)) rules.push(`@import url("${pathToFileURL(join(FONT_DIR, pkg, f)).href}");`);
    }
  }
  return rules.join('\n');
}

function expand(args) {
  const files = [];
  for (const a of args) {
    const p = resolve(a);
    if (statSync(p).isDirectory()) {
      for (const f of readdirSync(p).sort()) if (/\.(svg|html)$/i.test(f) && !f.startsWith('_')) files.push(join(p, f));
    } else files.push(p);
  }
  return files;
}

function sizeOf(markup, isSvg, forced) {
  const vb = markup.match(/viewBox\s*=\s*"([\d.\s,-]+)"/i);
  const dw = markup.match(/data-width\s*=\s*"(\d+)"/i);
  const dh = markup.match(/data-height\s*=\s*"(\d+)"/i);
  let w = 1000;
  let h = 1000;
  if (isSvg && vb) {
    const [, , vw, vh] = vb[1].trim().split(/[\s,]+/).map(Number);
    w = vw;
    h = vh;
  } else {
    const cw = markup.match(/<[^>]+id="art"[^>]*style="[^"]*width:\s*(\d+)px/i);
    const ch = markup.match(/<[^>]+id="art"[^>]*style="[^"]*height:\s*(\d+)px/i);
    if (cw && ch) {
      w = Number(cw[1]);
      h = Number(ch[1]);
    }
    if (dh && dw && !(cw && ch)) {
      w = Number(dw[1]);
      h = Number(dh[1]);
    }
  }
  const px = forced ?? (dw ? Number(dw[1]) : 4096);
  return { cssW: w, cssH: h, scale: px / w };
}

const argv = process.argv.slice(2);
const wi = argv.indexOf('--width');
const forced = wi >= 0 ? Number(argv.splice(wi, 2)[1]) : undefined;
const files = expand(argv);
if (!files.length) {
  console.error('Usage: node tools/raster.mjs <file.svg|file.html|folder> [...] [--width px]');
  process.exit(1);
}

const css = fontCss();
const browser = await chromium.launch();
try {
  for (const file of files) {
    const markup = readFileSync(file, 'utf8');
    const isSvg = extname(file).toLowerCase() === '.svg';
    const { cssW, cssH, scale } = sizeOf(markup, isSvg, forced);
    // Cap the device scale so a page never exceeds Chromium's texture limits.
    const s = Math.min(scale, 16384 / Math.max(cssW, cssH));
    const page = await browser.newPage({ viewport: { width: Math.ceil(cssW), height: Math.ceil(cssH) }, deviceScaleFactor: s });
    const body = isSvg
      ? markup.replace(/<svg\b/i, `<svg id="art" width="${cssW}" height="${cssH}"`).replace(/<\?xml[^>]*>/, '')
      : markup;
    const html = isSvg
      ? `<!doctype html><html><head><meta charset="utf-8"><style>${css}\nhtml,body{margin:0;padding:0;background:transparent}svg{display:block}</style></head><body>${body}</body></html>`
      : body.replace(/<head>/i, `<head><style>${css}\nhtml,body{margin:0;padding:0}</style>`);
    // Written beside the artwork so relative image paths resolve.
    const tmp = join(dirname(file), `_raster_${basename(file)}.html`);
    writeFileSync(tmp, html);
    try {
      await page.goto(pathToFileURL(tmp).href, { waitUntil: 'load' });
      await page.evaluate(async () => {
        await document.fonts.ready;
        await Promise.all([...document.images].map((i) => (i.complete ? null : new Promise((r) => (i.onload = i.onerror = r)))));
      });
      await page.waitForTimeout(150);
      const missing = await page.evaluate(() => [...document.fonts].filter((f) => f.status === 'error').map((f) => f.family));
      if (missing.length) console.warn(`  fonts failed: ${[...new Set(missing)].join(', ')}`);
      const target = (await page.$('#art')) ?? page;
      const out = file.replace(/\.(svg|html)$/i, '.png');
      await target.screenshot({ path: out, omitBackground: true });
      console.log(`${out.replace(ROOT + '/', '')}  ${Math.round(cssW * s)}x${Math.round(cssH * s)}`);
    } finally {
      unlinkSync(tmp);
      await page.close();
    }
  }
} finally {
  await browser.close();
}
