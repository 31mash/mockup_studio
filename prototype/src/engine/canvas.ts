export type Ctx = CanvasRenderingContext2D;

export function makeCanvas(width: number, height: number): HTMLCanvasElement {
  const c = document.createElement('canvas');
  c.width = Math.max(1, Math.round(width));
  c.height = Math.max(1, Math.round(height));
  return c;
}

export function ctx2d(c: HTMLCanvasElement, opts?: CanvasRenderingContext2DSettings): Ctx {
  const x = c.getContext('2d', opts);
  if (!x) throw new Error('Canvas 2D is unavailable in this browser.');
  x.imageSmoothingEnabled = true;
  x.imageSmoothingQuality = 'high';
  return x;
}

let filterSupport: boolean | null = null;
function supportsFilter(): boolean {
  if (filterSupport === null) {
    const x = document.createElement('canvas').getContext('2d');
    if (!x) return (filterSupport = false);
    x.filter = 'blur(2px)';
    filterSupport = x.filter === 'blur(2px)';
  }
  return filterSupport;
}

/**
 * Draws into a reduced-size layer and blurs it, for out-of-focus scenery.
 * Draw code uses full-size coordinates; the caller composites the result
 * with drawImage(layer, 0, 0, W, H).
 */
export function blurredLayer(W: number, H: number, radius: number, draw: (x: Ctx) => void): HTMLCanvasElement {
  const k = Math.max(1, Math.min(8, radius / 4));
  const w = Math.ceil(W / k);
  const h = Math.ceil(H / k);
  const c = makeCanvas(w, h);
  const x = ctx2d(c);
  x.scale(1 / k, 1 / k);
  draw(x);
  const r = radius / k;
  if (r < 0.75) return c;
  if (supportsFilter()) {
    const out = makeCanvas(w, h);
    const y = ctx2d(out);
    y.filter = `blur(${r.toFixed(2)}px)`;
    y.drawImage(c, 0, 0);
    return out;
  }
  // Fallback: a second downscale pass softens enough without canvas filters.
  const tiny = makeCanvas(Math.max(1, w / 3), Math.max(1, h / 3));
  ctx2d(tiny).drawImage(c, 0, 0, tiny.width, tiny.height);
  const out = makeCanvas(w, h);
  ctx2d(out).drawImage(tiny, 0, 0, w, h);
  return out;
}

export function composite(dst: Ctx, layer: HTMLCanvasElement, W: number, H: number, alpha = 1): void {
  dst.save();
  dst.globalAlpha = alpha;
  dst.drawImage(layer, 0, 0, W, H);
  dst.restore();
}

export function canvasToBlob(c: HTMLCanvasElement, type = 'image/png', quality?: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    c.toBlob((b) => (b ? resolve(b) : reject(new Error('Could not encode the image.'))), type, quality);
  });
}

export async function blobToCanvas(blob: Blob, maxEdge = Infinity): Promise<HTMLCanvasElement> {
  const bmp = await createImageBitmap(blob);
  const scale = Math.min(1, maxEdge / Math.max(bmp.width, bmp.height));
  const c = makeCanvas(bmp.width * scale, bmp.height * scale);
  ctx2d(c).drawImage(bmp, 0, 0, c.width, c.height);
  bmp.close?.();
  return c;
}

/** Vertical gradient with stops clamped into [0, 1] and kept in order. */
export function vGradient(x: Ctx, y0: number, y1: number, stops: [number, string][]): CanvasGradient {
  const g = x.createLinearGradient(0, y0, 0, y1);
  let last = 0;
  for (const [p, color] of stops) {
    const t = Math.min(1, Math.max(last, p));
    g.addColorStop(t, color);
    last = t;
  }
  return g;
}
