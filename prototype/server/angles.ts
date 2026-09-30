// Generative camera angles for the local server.
//
// Runs in Node, next to the studio's dev or preview server, never in the
// browser. It holds the Hugging Face token, calls the camera-angle model and
// hands the browser only the finished image, so the token never reaches page
// JavaScript, exported projects or the network tab.

import { Client, handle_file } from '@gradio/client';

/** Qwen-Image-Edit-2511 with fal's Multiple-Angles LoRA, 4-step Lightning. */
export const DEFAULT_SPACE = 'multimodalart/qwen-image-multiple-angles-3d-camera';
export const ENDPOINT = '/infer_camera_edit';

// The views the model was trained on. It snaps any value to the nearest one.
export const AZIMUTHS = [0, 45, 90, 135, 180, 225, 270, 315] as const;
export const ELEVATIONS = [-30, 0, 30, 60] as const;
export const DISTANCES = [0.6, 1.0, 1.8] as const;

const AZIMUTH_NAMES: Record<number, string> = {
  0: 'front view',
  45: 'front-right quarter view',
  90: 'right side view',
  135: 'back-right quarter view',
  180: 'back view',
  225: 'back-left quarter view',
  270: 'left side view',
  315: 'front-left quarter view',
};
const ELEVATION_NAMES: Record<number, string> = { [-30]: 'low-angle shot', 0: 'eye-level shot', 30: 'elevated shot', 60: 'high-angle shot' };
const DISTANCE_NAMES: Record<number, string> = { 0.6: 'close-up', 1: 'medium shot', 1.8: 'wide shot' };

const nearest = (v: number, options: readonly number[]) => options.reduce((a, b) => (Math.abs(b - v) < Math.abs(a - v) ? b : a));

/** The prompt the Space builds, for logs and job details. */
export function cameraPrompt(azimuth: number, elevation: number, distance: number): string {
  return `<sks> ${AZIMUTH_NAMES[nearest(azimuth, AZIMUTHS)]} ${ELEVATION_NAMES[nearest(elevation, ELEVATIONS)]} ${DISTANCE_NAMES[nearest(distance, DISTANCES)]}`;
}

export type AngleParams = { azimuth: number; elevation: number; distance: number; seed: number; width: number; height: number };
export type AngleResult = { bytes: Uint8Array; mime: string; seed: number; prompt: string };

export type ProviderStatus = {
  ready: boolean;
  provider: 'huggingface-space' | 'mock';
  /** Space id or URL the server calls. */
  space: string;
  /** Hugging Face account the token belongs to, once checked. */
  account?: string;
  reason?: string;
};

export type AngleErrorCode =
  | 'bad-request'
  | 'no-token'
  | 'token-rejected'
  | 'unreachable'
  | 'space-unavailable'
  | 'quota'
  | 'timeout'
  | 'canceled'
  | 'failed';

export class AngleError extends Error {
  constructor(
    readonly code: AngleErrorCode,
    message: string,
    readonly status = 502,
  ) {
    super(message);
  }
}

export interface AngleProvider {
  status(): Promise<ProviderStatus>;
  generate(image: Blob, params: AngleParams, signal: AbortSignal): Promise<AngleResult>;
}

// ------------------------------------------------------------------ requests

function num(q: URLSearchParams, key: string, min: number, max: number, fallback?: number): number {
  const raw = q.get(key);
  const v = raw === null || raw === '' ? fallback : Number(raw);
  if (v === undefined || !Number.isFinite(v) || v < min || v > max) {
    throw new AngleError('bad-request', `${key} must be a number from ${min} to ${max}.`, 400);
  }
  return v;
}

/** Reads and range-checks the query of a POST /api/local/angles request. */
export function parseParams(q: URLSearchParams): AngleParams {
  const size = (key: string) => {
    const v = Math.round(num(q, key, 256, 2048, 1024));
    return v - (v % 16);
  };
  return {
    azimuth: num(q, 'azimuth', 0, 359.99),
    elevation: num(q, 'elevation', -30, 60),
    distance: num(q, 'distance', 0.6, 1.8, 1),
    seed: Math.round(num(q, 'seed', 0, 2 ** 31 - 1, 0)),
    width: size('width'),
    height: size('height'),
  };
}

/** PNG, JPEG or WebP by signature; anything else is refused. */
export function sniffImage(bytes: Uint8Array): string | null {
  const at = (i: number, ...b: number[]) => b.every((v, k) => bytes[i + k] === v);
  if (at(0, 0x89, 0x50, 0x4e, 0x47)) return 'image/png';
  if (at(0, 0xff, 0xd8, 0xff)) return 'image/jpeg';
  if (at(0, 0x52, 0x49, 0x46, 0x46) && at(8, 0x57, 0x45, 0x42, 0x50)) return 'image/webp';
  return null;
}

// ------------------------------------------------------------------ providers

export type ProviderEnv = {
  HF_TOKEN?: string;
  /** Space id (owner/name) or the URL of any Gradio app with the same endpoint. */
  HF_ANGLE_SPACE?: string;
  /** `mock` returns the input unchanged, for tests without a network. */
  MOCKUP_ANGLES?: string;
};

export function createProvider(env: ProviderEnv): AngleProvider {
  if (env.MOCKUP_ANGLES === 'mock') return new MockProvider();
  return new SpaceProvider(env.HF_ANGLE_SPACE?.trim() || DEFAULT_SPACE, env.HF_TOKEN?.trim() || undefined);
}

class MockProvider implements AngleProvider {
  async status(): Promise<ProviderStatus> {
    return { ready: true, provider: 'mock', space: 'mock', account: 'mock' };
  }

  async generate(image: Blob, p: AngleParams, signal: AbortSignal): Promise<AngleResult> {
    await new Promise<void>((resolve, reject) => {
      const t = setTimeout(resolve, 400);
      signal.addEventListener('abort', () => (clearTimeout(t), reject(new AngleError('canceled', 'Canceled.', 499))), { once: true });
    });
    return { bytes: new Uint8Array(await image.arrayBuffer()), mime: image.type || 'image/png', seed: p.seed, prompt: cameraPrompt(p.azimuth, p.elevation, p.distance) };
  }
}

const TIMEOUT_MS = 240_000;
const isUrl = (s: string) => /^https?:\/\//i.test(s);

class SpaceProvider implements AngleProvider {
  private client: Promise<Client> | null = null;
  private checked: { at: number; status: ProviderStatus } | null = null;

  constructor(
    private readonly space: string,
    private readonly token: string | undefined,
  ) {}

  async status(): Promise<ProviderStatus> {
    const base = { provider: 'huggingface-space' as const, space: this.space };
    // Your own Gradio app (a duplicated Space, or one on your GPU) may not need a token.
    if (isUrl(this.space)) return { ...base, ready: true };
    if (!this.token) {
      return { ...base, ready: false, reason: 'No Hugging Face token. Add HF_TOKEN to prototype/.env.local, then restart the studio.' };
    }
    // Successful checks hold for ten minutes, failures for thirty seconds.
    const ttl = this.checked?.status.ready ? 600_000 : 30_000;
    if (this.checked && Date.now() - this.checked.at < ttl) return this.checked.status;
    const status = await this.whoami().then(
      (account) => ({ ...base, ready: true, account }),
      (e: AngleError) => ({ ...base, ready: false, reason: e.message }),
    );
    this.checked = { at: Date.now(), status };
    return status;
  }

  private async whoami(): Promise<string> {
    let res: Response;
    try {
      res = await fetch('https://huggingface.co/api/whoami-v2', { headers: { authorization: `Bearer ${this.token}` }, signal: AbortSignal.timeout(10_000) });
    } catch {
      throw new AngleError('unreachable', "Can't reach huggingface.co from this computer. Check the connection or proxy.");
    }
    if (res.status === 401) throw new AngleError('token-rejected', 'Hugging Face rejected the token in HF_TOKEN. Create a new read token and restart.', 401);
    if (!res.ok) throw new AngleError('unreachable', `Hugging Face answered ${res.status} when checking the token.`);
    const who = (await res.json()) as { name?: string };
    return who.name ?? 'your account';
  }

  private connect(): Promise<Client> {
    if (!this.client) {
      // Status events carry queue errors such as an exhausted GPU quota.
      const options = { events: ['data', 'status'] as ('data' | 'status')[], ...(this.token ? { token: this.token as `hf_${string}` } : {}) };
      // A sleeping Space wakes on connect; give up after two minutes.
      const wait = new Promise<never>((_, reject) => setTimeout(() => reject(new Error('The Space did not wake up within two minutes.')), 120_000).unref());
      this.client = Promise.race([Client.connect(this.space, options), wait]).catch((e: unknown) => {
        this.client = null;
        throw classify(e, 'connect');
      });
    }
    return this.client;
  }

  async generate(image: Blob, p: AngleParams, signal: AbortSignal): Promise<AngleResult> {
    if (!isUrl(this.space) && !this.token) throw new AngleError('no-token', 'No Hugging Face token on the local server.', 503);
    const client = await this.connect();
    const job = client.submit(ENDPOINT, {
      image: handle_file(image),
      azimuth: p.azimuth,
      elevation: p.elevation,
      distance: p.distance,
      seed: p.seed,
      randomize_seed: false,
      guidance_scale: 1,
      num_inference_steps: 4,
      height: p.height,
      width: p.width,
    });

    const timeout = AbortSignal.timeout(TIMEOUT_MS);
    const stop = AbortSignal.any([signal, timeout]);
    const onStop = () => void job.cancel().catch(() => undefined);
    stop.addEventListener('abort', onStop, { once: true });
    // Don't rely on the stream ending after a cancel: stop waiting at once.
    const stopped = new Promise<never>((_, reject) => stop.addEventListener('abort', () => reject(new Error('stopped')), { once: true }));
    stopped.catch(() => undefined);

    try {
      let output: unknown[] | null = null;
      const events = job[Symbol.asyncIterator]();
      for (;;) {
        const next = await Promise.race([events.next(), stopped]);
        if (next.done) break;
        const msg = next.value;
        if (msg.type === 'status' && msg.stage === 'error') {
          throw classify(new Error(typeof msg.message === 'string' ? msg.message : 'The model reported an error.'), 'run');
        }
        if (msg.type === 'data') {
          output = msg.data as unknown[];
          void events.return?.();
          break;
        }
      }
      if (timeout.aborted) throw new AngleError('timeout', 'The model took longer than four minutes. Try again when the Space is less busy.', 504);
      if (signal.aborted) throw new AngleError('canceled', 'Canceled.', 499);
      if (!output) throw new AngleError('failed', 'The model returned no image.');

      const [file, seed, prompt] = output as [{ url?: string; path?: string } | string | null, number, string];
      const url = typeof file === 'string' ? file : file?.url;
      if (!url) throw new AngleError('failed', 'The model returned no image.');
      const sameHost = /(^|\.)(hf\.space|huggingface\.co)$/i.test(new URL(url).hostname);
      const res = await fetch(url, { headers: this.token && sameHost ? { authorization: `Bearer ${this.token}` } : {}, signal: stop });
      if (!res.ok) throw new AngleError('failed', `Downloading the result failed (${res.status}).`);
      const bytes = new Uint8Array(await res.arrayBuffer());
      return { bytes, mime: sniffImage(bytes) ?? 'image/png', seed: Number(seed) || p.seed, prompt: String(prompt ?? cameraPrompt(p.azimuth, p.elevation, p.distance)) };
    } catch (e) {
      if (signal.aborted) throw new AngleError('canceled', 'Canceled.', 499);
      if (timeout.aborted) throw new AngleError('timeout', 'The model took longer than four minutes. Try again when the Space is less busy.', 504);
      throw e instanceof AngleError ? e : classify(e, 'run');
    } finally {
      stop.removeEventListener('abort', onStop);
    }
  }
}

/** Turns Gradio and network failures into codes the studio can explain. */
function classify(e: unknown, phase: 'connect' | 'run'): AngleError {
  const text = e instanceof Error ? e.message : String(e ?? '');
  if (/quota|exceeded your gpu/i.test(text)) {
    return new AngleError('quota', 'Your Hugging Face GPU time for today is used up. It refills daily, or upgrade the account for more.', 429);
  }
  if (/401|unauthori[sz]ed|invalid.*token/i.test(text)) return new AngleError('token-rejected', 'Hugging Face rejected the token in HF_TOKEN.', 401);
  if (/fetch failed|ENOTFOUND|ECONNREFUSED|ECONNRESET|ETIMEDOUT|EAI_AGAIN|network/i.test(text)) {
    return new AngleError('unreachable', "Can't reach Hugging Face from this computer. Check the connection or proxy.");
  }
  if (phase === 'connect' || /sleeping|paused|building|runtime error|could not resolve app config|space.*(not|isn)/i.test(text)) {
    return new AngleError('space-unavailable', `The camera-angle Space is not available right now${text ? ` (${text.slice(0, 160)})` : ''}.`, 503);
  }
  return new AngleError('failed', text ? `The model failed: ${text.slice(0, 200)}` : 'The model failed.');
}
