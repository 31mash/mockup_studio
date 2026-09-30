import type { SceneKind } from '../domain/catalogs';
import type { StudioTab } from '../domain/studio';
import { blurredLayer, composite, ctx2d, makeCanvas, type Ctx } from './canvas';
import { rgba, rng } from './color';
import { paintScene, SCENE_AMBIENT, SCENE_HORIZON, type Ground, type SceneParams } from './scenes';
import type { Cutout } from './subject';
import { reproject } from './view3d';

export type RenderInput = {
  tab: StudioTab;
  scene: SceneKind;
  width: number;
  height: number;
  subject: HTMLCanvasElement;
  cutout: Cutout;
  camera: { rotation: number; tilt: number; zoom: number };
  /**
   * How far to turn the subject itself, when it differs from the camera: a
   * generated view already shows most of the turn, and only the rest is
   * turned in perspective. Defaults to the camera's rotation and tilt.
   */
  turn?: { rotation: number; tilt: number };
  color: string;
  seed: number;
};

/** Product fit as a share of the frame, per scene. */
const PRODUCT_FIT: Partial<Record<SceneKind, number>> = {
  'minimalist-podium': 0.5,
  'natural-outdoor-environment': 0.42,
};

const MARGIN = 0.04;
const SHADOW = '#1c1a15';

export function renderImage(input: RenderInput): HTMLCanvasElement {
  const { width: W, height: H, camera, tab } = input;
  const rand = rng(input.seed);
  const out = makeCanvas(W, H);
  const x = ctx2d(out);

  // Variations stay small: a premium set changes framing, not the product.
  const jitter = { dx: (rand() - 0.5) * 0.04, scale: 1 + (rand() - 0.5) * 0.05, light: (rand() - 0.5) * 0.35 };
  const horizon = H * (SCENE_HORIZON[input.scene] - (camera.tilt / 90) * 0.55);
  const parallax = -(camera.rotation / 180) * W * 0.45;
  const light = -2.5 + (camera.rotation / 180) * Math.PI * 0.6 + jitter.light;
  const zoom = 1 + (camera.zoom / 50) * 0.55;

  // Turn the product for real when the camera moves around it.
  let subject = input.subject;
  const turn = input.turn ?? camera;
  if (input.cutout !== 'none' && (Math.abs(turn.rotation) >= 1 || Math.abs(turn.tilt) >= 1)) {
    subject = reproject(subject, turn.rotation, turn.tilt, light) ?? subject;
  }

  // Size the subject without ever cropping or stretching it.
  const aspect = subject.width / subject.height;
  const isPerson = tab === 'model' && input.cutout !== 'none';
  let h: number;
  let w: number;
  if (isPerson) {
    h = H * 0.8 * zoom * jitter.scale;
    w = h * aspect;
  } else {
    const fit = (PRODUCT_FIT[input.scene] ?? 0.58) * zoom * jitter.scale;
    w = Math.min(W * fit, H * fit * aspect);
    h = w / aspect;
  }
  const shrink = Math.min(1, (W * (1 - MARGIN * 2)) / w, (H * (isPerson ? 1 - MARGIN : 1 - MARGIN * 2)) / h);
  w *= shrink;
  h *= shrink;

  let sx = W / 2 - w / 2 + W * jitter.dx * (isPerson ? 0.5 : 1);
  sx = Math.min(W - W * MARGIN - w, Math.max(W * MARGIN, sx));
  let bottom: number;
  if (isPerson) bottom = H;
  else {
    const floorDepth = input.scene === 'minimalist-podium' ? 0.3 : input.scene === 'natural-outdoor-environment' ? 0.5 : 0.42;
    bottom = horizon + (H - horizon) * floorDepth;
    bottom = Math.min(H * (1 - MARGIN), Math.max(H * MARGIN + h, bottom));
  }
  const sy = bottom - h;

  const params: SceneParams = {
    W,
    H,
    horizon,
    parallax,
    light,
    color: input.color,
    rand,
    subject: { x: sx, y: bottom, w, h },
    tilt: camera.tilt,
  };
  const ground = paintScene(x, input.scene, params);

  if (input.cutout === 'none') {
    // Could not separate the subject: place the photo whole, like a print.
    const drop = blurredLayer(W, H, W * 0.012, (b) => {
      b.fillStyle = 'rgba(20,18,16,0.3)';
      b.fillRect(sx + W * 0.006, sy + W * 0.01, w, h);
    });
    composite(x, drop, W, H);
    x.drawImage(subject, sx, sy, w, h);
  } else {
    const sil = silhouette(subject);
    if (isPerson) {
      if (input.scene === 'studio-white' || input.scene === 'seamless-monochrome') backdropShadow(x, sil, sx, sy, w, h, light, W, H);
    } else {
      groundShadows(x, sil, { sx, bottom, w, h }, light, camera.tilt, ground, W, H);
    }
    drawLitSubject(x, subject, sx, sy, w, h, light, SCENE_AMBIENT[input.scene], W, H);
  }

  addGrain(x, W, H, input.seed);
  return out;
}

/** The subject's shape in shadow color, at a size that keeps edges smooth. */
function silhouette(subject: HTMLCanvasElement): HTMLCanvasElement {
  const scale = Math.min(1, 900 / Math.max(subject.width, subject.height));
  const c = makeCanvas(subject.width * scale, subject.height * scale);
  const s = ctx2d(c, { willReadFrequently: true });
  s.drawImage(subject, 0, 0, c.width, c.height);
  s.globalCompositeOperation = 'source-in';
  s.fillStyle = SHADOW;
  s.fillRect(0, 0, c.width, c.height);
  return c;
}

/**
 * The lower outline of a silhouette as a thin band: for each column, a strip
 * around its lowest point, kept only where that point is near the ground.
 * `band` is how far above the lowest point (share of height) still counts as
 * touching; `up` and `down` set the strip's reach above and below the edge.
 */
function footprint(sil: HTMLCanvasElement, band: number, up: number, down: number): HTMLCanvasElement {
  const W = sil.width;
  const H = sil.height;
  const d = ctx2d(sil, { willReadFrequently: true }).getImageData(0, 0, W, H).data;
  const low = new Int32Array(W).fill(-1);
  let maxY = 0;
  for (let x = 0; x < W; x++) {
    for (let y = H - 1; y >= 0; y--) {
      if (d[(y * W + x) * 4 + 3] > 128) {
        low[x] = y;
        break;
      }
    }
    if (low[x] > maxY) maxY = low[x];
  }
  const out = makeCanvas(W, H);
  const o = ctx2d(out);
  o.fillStyle = SHADOW;
  const u = Math.max(1, H * up);
  const dn = Math.max(1, H * down);
  for (let x = 0; x < W; x++) {
    if (low[x] < 0 || low[x] < maxY - H * band) continue;
    o.fillRect(x, low[x] - u, 1, u + dn);
  }
  return out;
}

let filterOk: boolean | null = null;
function canFilter(): boolean {
  if (filterOk === null) {
    const t = document.createElement('canvas').getContext('2d');
    if (t) t.filter = 'blur(2px)';
    filterOk = Boolean(t && t.filter === 'blur(2px)');
  }
  return filterOk;
}

/**
 * Gaussian-looking blur of a layer. Canvas filters where the browser has
 * them; otherwise three box passes on the alpha channel, which converge on
 * a Gaussian and never look blocky.
 */
function blur(src: HTMLCanvasElement, radius: number): HTMLCanvasElement {
  const out = makeCanvas(src.width, src.height);
  const o = ctx2d(out, { willReadFrequently: !canFilter() });
  if (radius < 0.5) {
    o.drawImage(src, 0, 0);
    return out;
  }
  if (canFilter()) {
    o.filter = `blur(${radius.toFixed(2)}px)`;
    o.drawImage(src, 0, 0);
    return out;
  }
  o.drawImage(src, 0, 0);
  const img = o.getImageData(0, 0, out.width, out.height);
  const W = out.width;
  const H = out.height;
  let a: Float32Array = new Float32Array(W * H);
  for (let i = 0; i < a.length; i++) a[i] = img.data[i * 4 + 3];
  const r = Math.max(1, Math.round(radius * 0.58));
  for (let pass = 0; pass < 3; pass++) a = boxPass(a, W, H, r);
  for (let i = 0; i < a.length; i++) img.data[i * 4 + 3] = a[i];
  o.putImageData(img, 0, 0);
  return out;
}

function boxPass(src: Float32Array, W: number, H: number, r: number): Float32Array {
  const tmp = new Float32Array(W * H);
  const out = new Float32Array(W * H);
  const n = 2 * r + 1;
  for (let y = 0; y < H; y++) {
    let s = 0;
    for (let k = -r; k <= r; k++) s += src[y * W + Math.min(W - 1, Math.max(0, k))];
    for (let x = 0; x < W; x++) {
      tmp[y * W + x] = s / n;
      s += src[y * W + Math.min(W - 1, x + r + 1)] - src[y * W + Math.max(0, x - r)];
    }
  }
  for (let x = 0; x < W; x++) {
    let s = 0;
    for (let k = -r; k <= r; k++) s += tmp[Math.min(H - 1, Math.max(0, k)) * W + x];
    for (let y = 0; y < H; y++) {
      out[y * W + x] = s / n;
      s += tmp[Math.min(H - 1, y + r + 1) * W + x] - tmp[Math.max(0, y - r) * W + x];
    }
  }
  return out;
}

/** Keeps a shadow layer on the surface the subject stands on. */
function clipToGround(layer: HTMLCanvasElement, ground: Ground, k: number, H: number): void {
  const g = ctx2d(layer);
  g.save();
  g.globalCompositeOperation = 'destination-in';
  if (ground.kind === 'plane') {
    const top = Math.max(0, (ground.y - H * 0.015) * k);
    const full = Math.max(top + 1, (ground.y + H * 0.035) * k);
    const m = g.createLinearGradient(0, top, 0, full);
    m.addColorStop(0, 'rgba(0,0,0,0)');
    m.addColorStop(1, 'rgba(0,0,0,1)');
    g.fillStyle = m;
    g.fillRect(0, 0, layer.width, layer.height);
  } else {
    g.fillStyle = '#000';
    g.beginPath();
    g.ellipse(ground.cx * k, ground.cy * k, ground.rx * k * 0.985, ground.ry * k * 0.97, 0, 0, Math.PI * 2);
    g.fill();
  }
  g.restore();
}

/**
 * Studio product shadows, all derived from the real silhouette and kept on
 * the ground: a crisp contact line under the footprint, a soft occlusion
 * pool, and a long soft shadow projected away from the key light.
 */
function groundShadows(
  x: Ctx,
  sil: HTMLCanvasElement,
  s: { sx: number; bottom: number; w: number; h: number },
  light: number,
  tilt: number,
  ground: Ground,
  W: number,
  H: number,
): void {
  const k = 0.5; // shadow layers at half resolution; blur hides the difference
  const lw = Math.ceil(W * k);
  const lh = Math.ceil(H * k);
  const { sx, bottom, w, h } = s;
  const view = Math.max(0, Math.min(1, (tilt + 15) / 55)); // higher camera sees more of the ground

  // 1. Cast shadow: the silhouette laid on the ground, falling away from the light.
  const flat = 0.1 + 0.28 * view;
  const skew = Math.cos(light) * 0.55;
  const cast = makeCanvas(lw, lh);
  const c = ctx2d(cast);
  c.scale(k, k);
  c.translate(sx, bottom);
  c.transform(1, 0, skew * flat, flat, 0, 0);
  c.drawImage(sil, 0, -h, w, h);
  // Fade with distance from the contact point, as real soft shadows do.
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.globalCompositeOperation = 'destination-in';
  const fade = c.createLinearGradient(0, bottom * k, 0, (bottom - h * flat) * k);
  fade.addColorStop(0, 'rgba(0,0,0,1)');
  fade.addColorStop(1, 'rgba(0,0,0,0.15)');
  c.fillStyle = fade;
  c.fillRect(0, 0, lw, lh);
  const castSoft = blur(cast, Math.max(2, h * 0.045 * k));
  clipToGround(castSoft, ground, k, H);

  // 2 and 3. Occlusion pool and contact line follow the product's real
  // bottom outline, so a turned product sits on its base edges.
  const view2 = Math.max(0, Math.min(1, (tilt + 15) / 55));
  const pool = makeCanvas(lw, lh);
  const p = ctx2d(pool);
  p.scale(k, k);
  p.drawImage(footprint(sil, 0.06 + 0.12 * view2, 0.05, 0.018), sx, bottom - h, w, h);
  const poolSoft = blur(pool, Math.max(1.5, h * 0.02 * k));
  clipToGround(poolSoft, ground, k, H);

  const line = makeCanvas(lw, lh);
  const l = ctx2d(line);
  l.scale(k, k);
  l.drawImage(footprint(sil, 0.06 + 0.12 * view2, 0.012, 0.004), sx, bottom - h, w, h);
  const lineSoft = blur(line, Math.max(0.8, h * 0.004 * k));

  x.save();
  x.imageSmoothingQuality = 'high';
  x.globalAlpha = 0.24;
  x.drawImage(castSoft, 0, 0, W, H);
  x.globalAlpha = 0.42;
  x.drawImage(poolSoft, 0, 0, W, H);
  x.globalAlpha = 0.55;
  x.drawImage(lineSoft, 0, 0, W, H);
  x.restore();
}

/** A very soft shadow on a studio backdrop behind a portrait. */
function backdropShadow(x: Ctx, sil: HTMLCanvasElement, sx: number, sy: number, w: number, h: number, light: number, W: number, H: number): void {
  const k = 0.5;
  const layer = makeCanvas(Math.ceil(W * k), Math.ceil(H * k));
  const g = ctx2d(layer);
  g.scale(k, k);
  g.drawImage(sil, sx - Math.cos(light) * w * 0.05, sy + h * 0.015, w, h);
  const soft = blur(layer, w * 0.06 * k);
  x.save();
  x.globalAlpha = 0.14;
  x.drawImage(soft, 0, 0, W, H);
  x.restore();
}

/** Tints the subject toward the scene light so it sits in the image. */
function drawLitSubject(
  x: Ctx,
  subject: HTMLCanvasElement,
  sx: number,
  sy: number,
  w: number,
  h: number,
  light: number,
  ambient: string | null,
  W: number,
  H: number,
): void {
  const layer = makeCanvas(W, H);
  const l = ctx2d(layer);
  l.drawImage(subject, sx, sy, w, h);
  l.globalCompositeOperation = 'source-atop';
  if (ambient) {
    l.fillStyle = rgba(ambient, 0.07);
    l.fillRect(sx, sy, w, h);
  }
  const lx = Math.cos(light);
  const g = l.createLinearGradient(sx + w / 2 + lx * w * 0.6, sy, sx + w / 2 - lx * w * 0.6, sy + h * 0.4);
  g.addColorStop(0, 'rgba(255,252,244,0.07)');
  g.addColorStop(1, 'rgba(18,16,12,0.09)');
  l.fillStyle = g;
  l.fillRect(sx, sy, w, h);
  x.drawImage(layer, 0, 0);
}

function addGrain(x: Ctx, W: number, H: number, seed: number): void {
  const img = x.getImageData(0, 0, W, H);
  const d = img.data;
  let s = seed >>> 0 || 1;
  for (let i = 0; i < d.length; i += 4) {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
    const n = ((s >>> 24) - 128) / 64;
    d[i] += n;
    d[i + 1] += n;
    d[i + 2] += n;
  }
  x.putImageData(img, 0, 0);
}
