import type { SceneKind } from '../domain/catalogs';
import type { StudioTab } from '../domain/studio';
import { blurredLayer, composite, ctx2d, makeCanvas, type Ctx } from './canvas';
import { rgba, rng } from './color';
import { paintScene, SCENE_AMBIENT, SCENE_HORIZON, type SceneParams } from './scenes';
import type { Cutout } from './subject';

export type RenderInput = {
  tab: StudioTab;
  scene: SceneKind;
  width: number;
  height: number;
  subject: HTMLCanvasElement;
  cutout: Cutout;
  camera: { rotation: number; tilt: number; zoom: number };
  color: string;
  seed: number;
};

/** Product fit as a share of the frame, per scene. */
const PRODUCT_FIT: Partial<Record<SceneKind, number>> = {
  'minimalist-podium': 0.5,
  'natural-outdoor-environment': 0.42,
};

const MARGIN = 0.04;

export function renderImage(input: RenderInput): HTMLCanvasElement {
  const { width: W, height: H, subject, camera, tab } = input;
  const rand = rng(input.seed);
  const out = makeCanvas(W, H);
  const x = ctx2d(out);

  const jitter = { dx: (rand() - 0.5) * 0.06, scale: 1 + (rand() - 0.5) * 0.08, light: (rand() - 0.5) * 0.5 };
  const topDown = camera.tilt >= 60;
  const horizon = H * (SCENE_HORIZON[input.scene] - (camera.tilt / 90) * 0.55);
  const parallax = -(camera.rotation / 180) * W * 0.45;
  const light = -2.5 + (camera.rotation / 180) * Math.PI * 0.6 + jitter.light;
  const zoom = 1 + (camera.zoom / 50) * 0.55;

  // Size the subject without ever cropping or stretching it.
  const aspect = subject.width / subject.height;
  const isPerson = tab === 'model' && input.cutout !== 'none';
  let h: number;
  let w: number;
  if (isPerson) {
    h = H * 0.8 * zoom * jitter.scale;
    w = h * aspect;
  } else {
    const fit = (PRODUCT_FIT[input.scene] ?? 0.6) * zoom * jitter.scale;
    const boxW = W * fit;
    const boxH = H * fit;
    w = Math.min(boxW, boxH * aspect);
    h = w / aspect;
  }
  const maxW = W * (1 - MARGIN * 2);
  const maxH = H * (isPerson ? 1 - MARGIN : 1 - MARGIN * 2);
  const shrink = Math.min(1, maxW / w, maxH / h);
  w *= shrink;
  h *= shrink;

  let sx = W / 2 - w / 2 + W * jitter.dx * (isPerson ? 0.5 : 1);
  sx = Math.min(W - W * MARGIN - w, Math.max(W * MARGIN, sx));
  let bottom: number;
  if (isPerson) bottom = H;
  else if (topDown) bottom = H / 2 + h / 2;
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
  paintScene(x, input.scene, params);

  if (input.cutout === 'none') {
    // Could not separate the subject: place the photo whole, like a print.
    const drop = blurredLayer(W, H, W * 0.012, (b) => {
      b.fillStyle = 'rgba(20,18,16,0.35)';
      b.fillRect(sx + W * 0.006, sy + W * 0.01, w, h);
    });
    composite(x, drop, W, H);
    x.drawImage(subject, sx, sy, w, h);
  } else {
    if (isPerson) wallShadow(x, subject, sx, sy, w, h, light, W, H);
    else if (topDown) dropShadow(x, subject, sx, sy, w, h, light, W, H);
    else contactShadow(x, subject, sx, bottom, w, h, light, W, H, camera.tilt);
    drawLitSubject(x, subject, sx, sy, w, h, light, SCENE_AMBIENT[input.scene], W, H);
  }

  addGrain(x, W, H, input.seed);
  return out;
}

function silhouette(subject: HTMLCanvasElement, scale: number): HTMLCanvasElement {
  const c = makeCanvas(subject.width * scale, subject.height * scale);
  const s = ctx2d(c);
  s.drawImage(subject, 0, 0, c.width, c.height);
  s.globalCompositeOperation = 'source-in';
  s.fillStyle = '#16140f';
  s.fillRect(0, 0, c.width, c.height);
  return c;
}

function contactShadow(
  x: Ctx,
  subject: HTMLCanvasElement,
  sx: number,
  bottom: number,
  w: number,
  h: number,
  light: number,
  W: number,
  H: number,
  tilt: number,
): void {
  const sil = silhouette(subject, Math.min(1, 320 / subject.height));
  const flatten = 0.16 + Math.max(0, tilt) / 90 * 0.3;
  const skew = -Math.cos(light) * 0.9;
  const cast = blurredLayer(W, H, Math.max(4, h * 0.035), (b) => {
    b.save();
    b.translate(sx, bottom);
    b.transform(1, 0, skew * flatten, -flatten, 0, 0);
    b.globalAlpha = 0.34;
    b.drawImage(sil, 0, 0, w, h);
    b.restore();
  });
  composite(x, cast, W, H);
  // Tight contact darkening right where the subject meets the surface.
  const ao = blurredLayer(W, H, Math.max(3, h * 0.012), (b) => {
    const g = b.createRadialGradient(sx + w / 2, bottom, 0, sx + w / 2, bottom, w * 0.55);
    g.addColorStop(0, 'rgba(22,20,15,0.42)');
    g.addColorStop(1, 'rgba(22,20,15,0)');
    b.fillStyle = g;
    b.save();
    b.translate(sx + w / 2, bottom);
    b.scale(1, 0.08);
    b.translate(-(sx + w / 2), -bottom);
    b.fillRect(sx - w, bottom - w, w * 3, w * 2);
    b.restore();
  });
  composite(x, ao, W, H);
}

function dropShadow(x: Ctx, subject: HTMLCanvasElement, sx: number, sy: number, w: number, h: number, light: number, W: number, H: number): void {
  const sil = silhouette(subject, Math.min(1, 320 / subject.height));
  const off = Math.min(w, h) * 0.05;
  const layer = blurredLayer(W, H, Math.max(4, Math.min(w, h) * 0.04), (b) => {
    b.globalAlpha = 0.38;
    b.drawImage(sil, sx - Math.cos(light) * off, sy - Math.sin(light) * off, w, h);
  });
  composite(x, layer, W, H);
}

function wallShadow(x: Ctx, subject: HTMLCanvasElement, sx: number, sy: number, w: number, h: number, light: number, W: number, H: number): void {
  const sil = silhouette(subject, Math.min(1, 320 / subject.height));
  const off = w * 0.06;
  const layer = blurredLayer(W, H, Math.max(8, w * 0.07), (b) => {
    b.globalAlpha = 0.22;
    b.drawImage(sil, sx - Math.cos(light) * off, sy + off * 0.3, w, h);
  });
  composite(x, layer, W, H);
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
    l.fillStyle = rgba(ambient, 0.1);
    l.fillRect(sx, sy, w, h);
  }
  const lx = Math.cos(light);
  const g = l.createLinearGradient(sx + w / 2 + lx * w * 0.6, sy, sx + w / 2 - lx * w * 0.6, sy + h * 0.4);
  g.addColorStop(0, 'rgba(255,252,244,0.12)');
  g.addColorStop(1, 'rgba(18,16,12,0.14)');
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
    const n = ((s >>> 24) - 128) / 42;
    d[i] += n;
    d[i + 1] += n;
    d[i + 2] += n;
  }
  x.putImageData(img, 0, 0);
}
