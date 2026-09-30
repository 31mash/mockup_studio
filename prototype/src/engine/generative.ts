import type { ModelView } from '../domain/angles';
import { canvasToBlob, ctx2d, makeCanvas } from './canvas';
import type { PreparedSubject } from './subject';

// Browser side of the local server (server/plugin.ts). The page never sees
// the Hugging Face token: it sends an image and a view, and gets an image back.

export type LocalStatus =
  | { state: 'checking' }
  /** No local server: the artifact, a file on disk, or a static host. */
  | { state: 'absent'; reason: string }
  | { state: 'not-ready'; reason: string; space?: string }
  | { state: 'ready'; provider: string; space: string; account?: string };

export const RUN_LOCALLY = 'Generative angles need the studio running on your computer: npm run dev, with a Hugging Face token in prototype/.env.local.';

export async function probeLocalServer(): Promise<LocalStatus> {
  const absent: LocalStatus = { state: 'absent', reason: RUN_LOCALLY };
  if (import.meta.env.MODE === 'artifact' || location.protocol === 'file:') return absent;
  try {
    const res = await fetch('/api/local/status', { cache: 'no-store', signal: AbortSignal.timeout(15_000) });
    if (!res.ok || !(res.headers.get('content-type') ?? '').includes('json')) return absent;
    const body = (await res.json()) as { service?: string; angles?: { ready: boolean; provider: string; space: string; account?: string; reason?: string } };
    const a = body.angles;
    if (body.service !== 'mockup-studio-local' || !a) return absent;
    return a.ready ? { state: 'ready', provider: a.provider, space: a.space, account: a.account } : { state: 'not-ready', reason: a.reason ?? 'The local server is not ready.', space: a.space };
  } catch {
    return absent;
  }
}

/** Error codes match the server's, plus `local-server` when it can't be reached. */
export class LocalServerError extends Error {
  constructor(
    readonly code: string,
    message: string,
  ) {
    super(message);
  }
}

export type AngleResponse = { blob: Blob; seed: number; prompt: string };

export async function requestAngle(image: Blob, view: ModelView, size: { width: number; height: number }, seed: number, signal: AbortSignal): Promise<AngleResponse> {
  const q = new URLSearchParams({
    azimuth: String(view.azimuth),
    elevation: String(view.elevation),
    // Framing is the studio's job, so the model keeps a medium shot.
    distance: '1',
    seed: String(seed % 2147483647),
    width: String(size.width),
    height: String(size.height),
  });
  let res: Response;
  try {
    res = await fetch(`/api/local/angles?${q}`, { method: 'POST', body: image, headers: { 'content-type': image.type, 'x-mockup-studio': '1' }, signal });
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw e;
    throw new LocalServerError('local-server', "The studio's local server isn't running.");
  }
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { error?: string; message?: string } | null;
    throw new LocalServerError(body?.error ?? 'local-server', body?.message ?? `The local server answered ${res.status}.`);
  }
  return { blob: await res.blob(), seed: Number(res.headers.get('x-angle-seed')) || seed, prompt: res.headers.get('x-angle-prompt') ?? '' };
}

/** A light neutral the keyer separates cleanly from white and dark products alike. */
const BACKDROP = '#e4e4e0';
const MODEL_EDGE = 1024;
const step16 = (v: number) => Math.max(256, Math.round(v / 16) * 16);

/**
 * What the model sees: the cut-out subject on a plain studio backdrop, with
 * room to turn. A product stands a little above the bottom edge; a person is
 * framed like a portrait, running off the bottom. A subject that could not be
 * cut out goes as its whole photo.
 */
export async function angleInput(subject: PreparedSubject, person: boolean): Promise<{ blob: Blob; width: number; height: number }> {
  const s = subject.canvas;
  const cut = subject.cutout !== 'none';
  const W0 = cut ? Math.max(s.width * (person ? 1.35 : 1.5), s.height * (person ? 0.8 : 0.9)) : s.width;
  const H0 = cut ? s.height * (person ? 1.12 : 1.3) : s.height;
  const scale = MODEL_EDGE / Math.max(W0, H0);
  const width = step16(W0 * scale);
  const height = step16(H0 * scale);
  const c = makeCanvas(width, height);
  const x = ctx2d(c);
  x.fillStyle = BACKDROP;
  x.fillRect(0, 0, width, height);
  x.imageSmoothingQuality = 'high';
  if (cut) {
    const w = s.width * scale;
    const h = s.height * scale;
    const bottom = person ? height : height * 0.88;
    x.drawImage(s, (width - w) / 2, bottom - h, w, h);
  } else {
    x.drawImage(s, 0, 0, width, height);
  }
  return { blob: await canvasToBlob(c, 'image/png'), width, height };
}
