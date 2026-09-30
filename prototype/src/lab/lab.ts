// Dev-only engine lab: renders cutouts and a matrix of scenes and cameras so
// output quality can be reviewed side by side. Open /lab.html on the dev
// server, or drive it from a script through window.lab.
import type { SceneKind } from '../domain/catalogs';
import type { StudioTab } from '../domain/studio';
import { blobToCanvas, ctx2d, makeCanvas } from '../engine/canvas';
import { renderImage } from '../engine/render';
import { drawSampleProduct } from '../engine/standins';
import { prepareSubject, type PreparedSubject } from '../engine/subject';

type Input = { name: string; url: string };
type Case = { scene: SceneKind; tab?: StudioTab; rotation?: number; tilt?: number; zoom?: number; width?: number; height?: number; color?: string };

const out = document.getElementById('out')!;

async function load(url: string): Promise<HTMLCanvasElement> {
  const blob = await (await fetch(url)).blob();
  return blobToCanvas(blob, 2000);
}

function on(bg: string, c: HTMLCanvasElement): HTMLCanvasElement {
  const o = makeCanvas(c.width, c.height);
  const x = ctx2d(o);
  x.fillStyle = bg;
  x.fillRect(0, 0, o.width, o.height);
  x.drawImage(c, 0, 0);
  return o;
}

function alphaOf(c: HTMLCanvasElement): HTMLCanvasElement {
  const o = makeCanvas(c.width, c.height);
  const x = ctx2d(o, { willReadFrequently: true });
  x.drawImage(c, 0, 0);
  const d = x.getImageData(0, 0, o.width, o.height);
  for (let i = 0; i < d.data.length; i += 4) d.data[i] = d.data[i + 1] = d.data[i + 2] = d.data[i + 3], (d.data[i + 3] = 255);
  x.putImageData(d, 0, 0);
  return o;
}

function row(title: string, items: [string, HTMLCanvasElement][], cols: number) {
  const h = document.createElement('h2');
  h.textContent = title;
  out.appendChild(h);
  const r = document.createElement('div');
  r.className = 'row';
  r.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
  for (const [cap, c] of items) {
    const f = document.createElement('figure');
    f.appendChild(c);
    const fc = document.createElement('figcaption');
    fc.textContent = cap;
    f.appendChild(fc);
    r.appendChild(f);
  }
  out.appendChild(r);
}

const prepared = new Map<string, PreparedSubject>();

async function subject(input: Input): Promise<PreparedSubject> {
  let p = prepared.get(input.name);
  if (!p) {
    const src = input.url === 'sample' ? drawSampleProduct() : await load(input.url);
    const t0 = performance.now();
    p = prepareSubject(src);
    console.log(`prepare ${input.name}: ${p.cutout} ${(performance.now() - t0).toFixed(0)} ms`);
    prepared.set(input.name, p);
  }
  return p;
}

async function cutouts(inputs: Input[]) {
  for (const input of inputs) {
    const src = input.url === 'sample' ? drawSampleProduct() : await load(input.url);
    const p = await subject(input);
    row(`${input.name}: ${p.cutout}`, [
      ['source', on('#ffffff', src)],
      ['on dark', on('#1e1e20', p.canvas)],
      ['on green', on('#3f7a4c', p.canvas)],
      ['alpha', alphaOf(p.canvas)],
    ], 4);
  }
}

async function renders(input: Input, cases: Case[], cols = 4) {
  const p = await subject(input);
  const items: [string, HTMLCanvasElement][] = [];
  for (const c of cases) {
    const t0 = performance.now();
    const img = renderImage({
      tab: c.tab ?? 'product',
      scene: c.scene,
      width: c.width ?? 1152,
      height: c.height ?? 1536,
      subject: p.canvas,
      cutout: p.cutout,
      camera: { rotation: c.rotation ?? 0, tilt: c.tilt ?? 0, zoom: c.zoom ?? 0 },
      color: c.color ?? '#C8C2B6',
      seed: 12345,
    });
    items.push([`${c.scene} r${c.rotation ?? 0} t${c.tilt ?? 0} z${c.zoom ?? 0} (${(performance.now() - t0).toFixed(0)} ms)`, img]);
  }
  row(input.name, items, cols);
}

declare global {
  interface Window {
    lab: { cutouts: typeof cutouts; renders: typeof renders; clear: () => void };
  }
}
window.lab = { cutouts, renders, clear: () => (out.innerHTML = '') };
