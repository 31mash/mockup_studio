// Turns the single-file build (dist/index.html) into the page fragment the
// claude.ai artifact viewer expects: title, styles, root and script, with no
// <html>/<head>/<body> wrapper of its own. Output: artifact/future-mockup-studio.html
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const html = readFileSync(new URL('../dist/index.html', import.meta.url), 'utf8');
const title = html.match(/<title>([\s\S]*?)<\/title>/)?.[1] ?? 'Future Mockup Studio';
const styles = [...html.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map((m) => m[1]);
const scripts = [...html.matchAll(/<script type="module"[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
if (!styles.length || !scripts.length) throw new Error('Expected inlined <style> and <script> in dist/index.html');

const out = [
  `<title>${title}</title>`,
  ...styles.map((s) => `<style>${s}</style>`),
  '<div id="root"></div>',
  ...scripts.map((s) => `<script type="module">${s}</script>`),
].join('\n');

mkdirSync(new URL('../artifact/', import.meta.url), { recursive: true });
writeFileSync(new URL('../artifact/future-mockup-studio.html', import.meta.url), out);
console.log(`artifact/future-mockup-studio.html  ${(out.length / 1024).toFixed(0)} KB`);
