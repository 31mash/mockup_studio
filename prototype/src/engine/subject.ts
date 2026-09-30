import { ctx2d, makeCanvas } from './canvas';
import { rgbToHex } from './color';

export type Cutout = 'alpha' | 'keyed' | 'none';
export type PreparedSubject = { canvas: HTMLCanvasElement; cutout: Cutout };

const WORK_EDGE = 1400;

/**
 * Separates the subject from its backdrop so it can sit in a new scene.
 *
 * Transparent images are used as they are. Photos on a studio backdrop are
 * segmented by growing the backdrop inward from the border through pixels
 * that continue it smoothly: the backdrop itself, its gradients, and the
 * photo's own soft shadows (same hue, darker). Product edges are steps, so
 * growth stops there. Near-white pixels must be very smooth to join, which
 * keeps white caps and labels. Anything that is not a studio backdrop is
 * placed whole; the job details say which path was taken.
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

  const N = W * H;
  // Lightly smoothed channels, so sensor and JPEG noise don't read as edges.
  const R = new Float32Array(N);
  const G = new Float32Array(N);
  const B = new Float32Array(N);
  for (let p = 0; p < N; p++) {
    R[p] = d[p * 4];
    G[p] = d[p * 4 + 1];
    B[p] = d[p * 4 + 2];
  }
  for (const ch of [R, G, B]) ch.set(boxBlur(ch, W, H, 1));
  const lum = (p: number) => 0.2126 * R[p] + 0.7152 * G[p] + 0.0722 * B[p];
  const chroma = (p: number): [number, number] => {
    const t = R[p] + G[p] + B[p] + 1;
    return [R[p] / t, G[p] / t];
  };

  // Backdrop model from the top and the upper three quarters of each side.
  // The bottom is left out: products and people often run off the bottom.
  const border: number[] = [];
  const stride = Math.max(1, Math.floor(Math.min(W, H) / 250));
  for (let px = 0; px < W; px += stride) border.push(px);
  for (let py = 0; py < H * 0.75; py += stride) border.push(py * W, py * W + W - 1);
  const median = (vals: number[]) => vals.sort((a, b) => a - b)[Math.floor(vals.length / 2)];
  const bl = median(border.map(lum));
  const bc: [number, number] = [median(border.map((p) => chroma(p)[0])), median(border.map((p) => chroma(p)[1]))];
  const cdist = (p: number) => {
    const [a, b] = chroma(p);
    return Math.hypot(a - bc[0], b - bc[1]);
  };
  const spread = median(border.map(cdist));
  const onModel = border.filter((p) => cdist(p) < 0.03 + spread * 2 && lum(p) > bl * 0.6).length / border.length;
  if (onModel < 0.8 || bl < 60) return { canvas: c, cutout: 'none' };

  const cTol = 0.02 + spread * 2.5;
  const brightFloor = bl * 0.9;
  // Each backdrop pixel carries a slowly updated reference color along its
  // growth path. Gradients and soft shadows move the reference with them; a
  // product edge (even a faint white-on-white one) pulls away from it within
  // a few pixels and stops the growth. Shadows may change faster than the
  // near-white backdrop, so they get a quicker reference and a wider margin.
  const refR = new Float32Array(N);
  const refG = new Float32Array(N);
  const refB = new Float32Array(N);
  const joins = (q: number, p: number) => {
    const L = lum(q);
    if (L > bl * 1.16 + 8 || L < bl * 0.3) return false;
    if (cdist(q) > cTol) return false;
    const dR = R[q] - refR[p];
    const dG = G[q] - refG[p];
    const dB = B[q] - refB[p];
    const up = Math.max(dR, dG, dB);
    const down = -Math.min(dR, dG, dB);
    const bright = L >= brightFloor;
    // The backdrop may darken into a shadow but almost never brightens into a
    // highlight, so white caps, labels and lettering stay with the product.
    if (up > 3.5) return false;
    if (down > (bright ? 5.5 : 22)) return false;
    const k = bright ? 0.12 : 0.35;
    refR[q] = refR[p] + k * (R[q] - refR[p]);
    refG[q] = refG[p] + k * (G[q] - refG[p]);
    refB[q] = refB[p] + k * (B[q] - refB[p]);
    return true;
  };

  const bg = new Uint8Array(N);
  const queue = new Int32Array(N);
  let head = 0;
  let tail = 0;
  const seedOk = (p: number) => cdist(p) <= cTol && lum(p) > bl * 0.8 && lum(p) < bl * 1.16 + 8;
  const addSeed = (p: number) => {
    if (!bg[p] && seedOk(p)) {
      bg[p] = 1;
      refR[p] = R[p];
      refG[p] = G[p];
      refB[p] = B[p];
      queue[tail++] = p;
    }
  };
  for (let px = 0; px < W; px++) {
    addSeed(px);
    addSeed((H - 1) * W + px);
  }
  for (let py = 0; py < H; py++) {
    addSeed(py * W);
    addSeed(py * W + W - 1);
  }
  while (head < tail) {
    const p = queue[head++];
    const px = p % W;
    const visit = (q: number) => {
      if (!bg[q] && joins(q, p)) {
        bg[q] = 1;
        queue[tail++] = q;
      }
    };
    if (px > 0) visit(p - 1);
    if (px < W - 1) visit(p + 1);
    if (p >= W) visit(p - W);
    if (p < N - W) visit(p + W);
  }

  // Keep the product: drop foreground specks far smaller than the main part.
  const fg = new Uint8Array(N);
  for (let p = 0; p < N; p++) fg[p] = bg[p] ? 0 : 1;
  keepMainParts(fg, W, H);

  let count = 0;
  for (let p = 0; p < N; p++) count += fg[p];
  const fraction = 1 - count / N;
  if (fraction < 0.03 || fraction > 0.97) return { canvas: c, cutout: 'none' };

  // Edge: choke by one pixel so no backdrop-tinted rim survives, then soften.
  const choked = erode(fg, W, H);
  let alpha = new Float32Array(N) as Float32Array;
  for (let p = 0; p < N; p++) alpha[p] = choked[p];
  alpha = boxBlur(boxBlur(alpha, W, H, 1), W, H, 1);

  // Replace rim colors with nearby interior colors (no light fringe on dark scenes).
  decontaminate(d, choked, alpha, W, H);
  for (let p = 0; p < N; p++) d[p * 4 + 3] = Math.round(Math.min(1, alpha[p] * 1.15) * 255);
  x.putImageData(img, 0, 0);
  return { canvas: trim(c, x), cutout: 'keyed' };
}

/** Keeps connected parts at least 3% the size of the largest; clears the rest. */
function keepMainParts(fg: Uint8Array, W: number, H: number): void {
  const N = W * H;
  const label = new Int32Array(N).fill(-1);
  const sizes: number[] = [];
  const stack = new Int32Array(N);
  for (let s = 0; s < N; s++) {
    if (!fg[s] || label[s] >= 0) continue;
    const id = sizes.length;
    let top = 0;
    let size = 0;
    stack[top++] = s;
    label[s] = id;
    while (top) {
      const p = stack[--top];
      size++;
      const px = p % W;
      const nb = [px > 0 ? p - 1 : -1, px < W - 1 ? p + 1 : -1, p >= W ? p - W : -1, p < N - W ? p + W : -1];
      for (const q of nb) {
        if (q >= 0 && fg[q] && label[q] < 0) {
          label[q] = id;
          stack[top++] = q;
        }
      }
    }
    sizes.push(size);
  }
  if (!sizes.length) return;
  const keep = Math.max(...sizes) * 0.03;
  for (let p = 0; p < N; p++) if (fg[p] && sizes[label[p]] < keep) fg[p] = 0;
}

function erode(m: Uint8Array, W: number, H: number): Uint8Array {
  const out = new Uint8Array(m.length);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const p = y * W + x;
      out[p] = m[p] && (x === 0 || m[p - 1]) && (x === W - 1 || m[p + 1]) && (y === 0 || m[p - W]) && (y === H - 1 || m[p + W]) ? 1 : 0;
    }
  }
  return out;
}

/** Rim pixels take the average color of interior neighbors, grown outward. */
function decontaminate(d: Uint8ClampedArray, inner: Uint8Array, alpha: Float32Array, W: number, H: number): void {
  const N = W * H;
  const solid = new Uint8Array(N);
  // Interior = at least two pixels inside the choked mask.
  const e1 = erode(inner, W, H);
  const e2 = erode(e1, W, H);
  solid.set(e2);
  for (let pass = 0; pass < 4; pass++) {
    const next = solid.slice();
    for (let y = 1; y < H - 1; y++) {
      for (let x = 1; x < W - 1; x++) {
        const p = y * W + x;
        if (solid[p] || alpha[p] <= 0) continue;
        let r = 0;
        let g = 0;
        let b = 0;
        let n = 0;
        for (const q of [p - 1, p + 1, p - W, p + W, p - W - 1, p - W + 1, p + W - 1, p + W + 1]) {
          if (solid[q]) {
            r += d[q * 4];
            g += d[q * 4 + 1];
            b += d[q * 4 + 2];
            n++;
          }
        }
        if (n) {
          d[p * 4] = r / n;
          d[p * 4 + 1] = g / n;
          d[p * 4 + 2] = b / n;
          next[p] = 1;
        }
      }
    }
    solid.set(next);
  }
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
