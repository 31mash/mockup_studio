import { newId } from '../domain/generation';
import type { AssetMeta, AssetRole } from '../domain/studio';
import { canvasToBlob, ctx2d, makeCanvas } from '../engine/canvas';
import { samplePalette } from '../engine/subject';

export const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp'];
export const MAX_BYTES = 20 * 1024 * 1024;
export const MAX_PIXELS = 40_000_000;
export const LOW_RES_EDGE = 512;
const STORE_EDGE = 3072;

export class UploadError extends Error {}

/**
 * Validates and normalizes an upload: checks type, size and decoded pixels,
 * applies EXIF orientation, and re-encodes so location and camera metadata
 * never leave the device. Transparency is kept as PNG.
 */
export async function normalizeUpload(file: File, role: AssetRole): Promise<{ meta: AssetMeta; blob: Blob }> {
  if (!ACCEPTED.includes(file.type)) throw new UploadError('Use a JPEG, PNG or WebP image.');
  if (file.size > MAX_BYTES) throw new UploadError('This file is over 20 MB. Export a smaller version and try again.');

  let bmp: ImageBitmap;
  try {
    bmp = await createImageBitmap(file, { imageOrientation: 'from-image' });
  } catch {
    throw new UploadError("This image couldn't be read. The file may be damaged.");
  }
  if (bmp.width * bmp.height > MAX_PIXELS) {
    bmp.close();
    throw new UploadError('This image is over 40 megapixels. Resize it and try again.');
  }

  const scale = Math.min(1, STORE_EDGE / Math.max(bmp.width, bmp.height));
  const c = makeCanvas(bmp.width * scale, bmp.height * scale);
  const x = ctx2d(c, { willReadFrequently: true });
  x.drawImage(bmp, 0, 0, c.width, c.height);
  const longest = Math.max(bmp.width, bmp.height);
  bmp.close();

  let hasAlpha = false;
  if (file.type !== 'image/jpeg') {
    const d = x.getImageData(0, 0, c.width, c.height).data;
    for (let i = 3; i < d.length; i += 40) {
      if (d[i] < 250) {
        hasAlpha = true;
        break;
      }
    }
  }
  const blob = hasAlpha ? await canvasToBlob(c, 'image/png') : await canvasToBlob(c, 'image/jpeg', 0.94);
  const meta: AssetMeta = {
    id: newId('asset'),
    role,
    name: file.name || 'Untitled image',
    mime: blob.type,
    width: c.width,
    height: c.height,
    createdAt: new Date().toISOString(),
    origin: 'upload',
    hasAlpha,
    lowResolution: longest < LOW_RES_EDGE,
    palette: samplePalette(c),
    saved: role === 'product',
  };
  return { meta, blob };
}

export async function canvasAsset(
  c: HTMLCanvasElement,
  init: Omit<AssetMeta, 'width' | 'height' | 'mime' | 'createdAt' | 'palette'>,
  type: 'image/png' | 'image/jpeg' = 'image/png',
): Promise<{ meta: AssetMeta; blob: Blob }> {
  const blob = await canvasToBlob(c, type, type === 'image/jpeg' ? 0.94 : undefined);
  return {
    blob,
    meta: {
      ...init,
      width: c.width,
      height: c.height,
      mime: blob.type,
      createdAt: new Date().toISOString(),
      palette: samplePalette(c),
    },
  };
}

export async function toPng(blob: Blob): Promise<Blob> {
  if (blob.type === 'image/png') return blob;
  const bmp = await createImageBitmap(blob);
  const c = makeCanvas(bmp.width, bmp.height);
  ctx2d(c).drawImage(bmp, 0, 0);
  bmp.close();
  return canvasToBlob(c, 'image/png');
}
