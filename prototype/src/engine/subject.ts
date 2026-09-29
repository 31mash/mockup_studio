import { ctx2d, makeCanvas } from './canvas';
import { rgbToHex } from './color';

export type Cutout = 'alpha' | 'keyed' | 'none';
export type PreparedSubject = { canvas: HTMLCanvasElement; cutout: Cutout };

const WORK_EDGE = 1400;

/**
 * Separates the subject from a plain backdrop so it can sit in a new scene.
 * Transparent images are used as they are. Photos on a fairly even backdrop
 * are keyed by flood-filling from the border. Anything else stays whole and
 * is placed as shot; the job details say which path was taken.
 */
export function prepareSubject(src: CanvasImageSource & { width: number; height: number }): PreparedSubject {
  const scale = Math.min(1, WORK_EDGE / Math.max(src.width, src.height));
  const W = Math.max(1, Math.round(src.width * scale));
  const H = Math.max(1, Math.round(src.height * scale));
  const c = makeCanvas(W, H);
  const x = ctx2d(c, { willReadFrequently: true });
  x.drawImage(src, 0, 0, W, H);
  const img = x.getImageData(0, 0, W, H);
  const d = img.data;

  let transparent = 0;
  for (let i = 3; i < d.length; i += 16) if (d[i] < 250) transparent++;
  if (transparent / (d.length / 16) > 0.01) return { canvas: trim(c, x), cutout: 'alpha' };

  // Backdrop statistics from the top and side edges. The bottom edge is left
  // out: portraits and tabletop shots often run the subject off the bottom.
  const border: number[] = [];
  const push = (px: number, py: number) => border.push((py * W + px) * 4);
  const stride = Math.max(1, Math.floor(Math.min(W, H) / 200));
  for (let px = 0; px < W; px += stride) push(px, 0);
  for (let py = 0; py < H * 0.75; py += stride) {
    push(0, py);
    push(W - 1, py);
  }
  const mean = [0, 0, 0];
  for (const i of border) for (let k = 0; k < 3; k++) mean[k] += d[i + k];
  for (let k = 0; k < 3; k++) mean[k] /= border.length;
  let variance = 0;
  for (const i of border) for (let k = 0; k < 3; k++) variance += (d[i + k] - mean[k]) ** 2;
  const std = Math.sqrt(variance / (border.length * 3));
  if (std > 26) return { canvas: c, cutout: 'none' };

  const tol = Math.max(26, std * 2.6 + 14);
  const tol2 = tol * tol;
  const dist2 = (i: number) => (d[i] - mean[0]) ** 2 + (d[i + 1] - mean[1]) ** 2 + (d[i + 2] - mean[2]) ** 2;

  const bg = new Uint8Array(W * H);
  const queue = new Int32Array(W * H);
  let head = 0;
  let tail = 0;
  const seed = (p: number) => {
    if (!bg[p] && dist2(p * 4) < tol2) {
      bg[p] = 1;
      queue[tail++] = p;
    }
  };
  for (let px = 0; px < W; px++) {
    seed(px);
    seed((H - 1) * W + px);
  }
  for (let py = 0; py < H; py++) {
    seed(py * W);
    seed(py * W + W - 1);
  }
  while (head < tail) {
    const p = queue[head++];
    const px = p % W;
    if (px > 0) seed(p - 1);
    if (px < W - 1) seed(p + 1);
    if (p >= W) seed(p - W);
    if (p < W * (H - 1)) seed(p + W);
  }

  // Enclosed holes (a mug handle, the gap under an arm) that match the
  // backdrop almost exactly are backdrop too. Strict, so white labels stay.
  const hole2 = 10 * 10;
  const seen = new Uint8Array(W * H);
  const minHole = Math.max(40, Math.round(W * H * 0.0008));
  for (let start = 0; start < W * H; start++) {
    if (bg[start] || seen[start] || dist2(start * 4) >= hole2) continue;
    const comp: number[] = [start];
    seen[start] = 1;
    for (let k = 0; k < comp.length; k++) {
      const p = comp[k];
      const px = p % W;
      const next = [px > 0 ? p - 1 : -1, px < W - 1 ? p + 1 : -1, p >= W ? p - W : -1, p < W * (H - 1) ? p + W : -1];
      for (const q of next) {
        if (q >= 0 && !bg[q] && !seen[q] && dist2(q * 4) < hole2) {
          seen[q] = 1;
          comp.push(q);
        }
      }
    }
    if (comp.length >= minHole) {
      for (const p of comp) bg[p] = 1;
      tail += comp.length;
    }
  }

  const fraction = tail / (W * H);
  if (fraction < 0.03 || fraction > 0.97) return { canvas: c, cutout: 'none' };

  // Soft edge: alpha from the mask, then a small box blur for anti-aliasing.
  let alpha: Float32Array = new Float32Array(W * H);
  for (let p = 0; p < W * H; p++) alpha[p] = bg[p] ? 0 : 1;
  alpha = boxBlur(alpha, W, H, 1);
  alpha = boxBlur(alpha, W, H, 1);
  for (let p = 0; p < W * H; p++) {
    // Keep the interior fully opaque; only soften the rim.
    const a = bg[p] ? alpha[p] * 0.5 : Math.max(alpha[p], 0.85);
    d[p * 4 + 3] = Math.round(Math.min(1, a) * 255);
  }
  x.putImageData(img, 0, 0);
  return { canvas: trim(c, x), cutout: 'keyed' };
}

function boxBlur(src: Float32Array, W: number, H: number, r: number): Float32Array {
  const tmp = new Float32Array(W * H);
  const out = new Float32Array(W * H);
  const n = 2 * r + 1;
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      let s = 0;
      for (let k = -r; k <= r; k++) s += src[y * W + Math.min(W - 1, Math.max(0, x + k))];
      tmp[y * W + x] = s / n;
    }
  }
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      let s = 0;
      for (let k = -r; k <= r; k++) s += tmp[Math.min(H - 1, Math.max(0, y + k)) * W + x];
      out[y * W + x] = s / n;
    }
  }
  return out;
}

/** Crop transparent margins so placement uses the subject's real bounds. */
function trim(c: HTMLCanvasElement, x: CanvasRenderingContext2D): HTMLCanvasElement {
  const { width: W, height: H } = c;
  const d = x.getImageData(0, 0, W, H).data;
  let minX = W;
  let minY = H;
  let maxX = -1;
  let maxY = -1;
  for (let y = 0; y < H; y++) {
    for (let px = 0; px < W; px++) {
      if (d[(y * W + px) * 4 + 3] > 16) {
        if (px < minX) minX = px;
        if (px > maxX) maxX = px;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }
  if (maxX < 0) return c;
  const pad = 2;
  minX = Math.max(0, minX - pad);
  minY = Math.max(0, minY - pad);
  maxX = Math.min(W - 1, maxX + pad);
  maxY = Math.min(H - 1, maxY + pad);
  const out = makeCanvas(maxX - minX + 1, maxY - minY + 1);
  ctx2d(out).drawImage(c, minX, minY, out.width, out.height, 0, 0, out.width, out.height);
  return out;
}

/**
 * Samples up to four tones from the subject: a median, a warm tone, a light
 * tone and the darkest 5 percent. These become the "borrowed" accents that
 * tint loading placeholders for this subject.
 */
export function samplePalette(src: CanvasImageSource & { width: number; height: number }): string[] {
  const c = makeCanvas(64, Math.max(1, Math.round((64 * src.height) / src.width)));
  const x = ctx2d(c, { willReadFrequently: true });
  x.drawImage(src, 0, 0, c.width, c.height);
  const d = x.getImageData(0, 0, c.width, c.height).data;
  const px: [number, number, number, number][] = [];
  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] < 200) continue;
    const lum = 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2];
    px.push([d[i], d[i + 1], d[i + 2], lum]);
  }
  if (px.length < 8) return [];
  px.sort((a, b) => a[3] - b[3]);
  const at = (t: number) => px[Math.min(px.length - 1, Math.floor(t * px.length))];
  const darkest = px.slice(0, Math.max(1, Math.floor(px.length * 0.05)));
  const avg = (arr: typeof px) => rgbToHex([0, 1, 2].map((k) => arr.reduce((s, p) => s + p[k], 0) / arr.length) as [number, number, number]);
  const warm = [...px].sort((a, b) => b[0] - b[2] - (a[0] - a[2])).slice(0, Math.max(1, Math.floor(px.length * 0.15)));
  const median = at(0.5);
  const light = at(0.85);
  return [
    rgbToHex([median[0], median[1], median[2]]),
    avg(warm),
    rgbToHex([light[0], light[1], light[2]]),
    avg(darkest),
  ];
}
