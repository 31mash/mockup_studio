import { findBackground, RATIOS, type SceneKind } from '../domain/catalogs';
import { describeCamera, isOriginal } from '../domain/camera';
import type { JobRecord, Slot } from '../domain/studio';
import { drawSceneThumb } from '../engine/standins';

export function ratioLabel(id: string): string {
  return RATIOS.find((r) => r.id === id)?.label ?? id;
}

export function jobTitle(job: JobRecord): string {
  const d = job.snapshot.draft;
  return `${findBackground(d.tab, d.backgroundId).label}, ${ratioLabel(d.ratio)}`;
}

export function angleSummary(camera: JobRecord['snapshot']['draft']['camera']): string {
  if (isOriginal(camera)) return 'original angle';
  if (camera.kind === 'relative') return 'custom angle';
  return `${describeCamera(camera).toLowerCase()} view`;
}

export function jobMeta(job: JobRecord): string {
  const d = job.snapshot.draft;
  const n = d.count === 1 ? '1 image' : `${d.count} images`;
  const where = whereLabel(job);
  return `${n}, ${angleSummary(d.camera)}, ${where}`;
}

export function whereLabel(job: JobRecord): string {
  if (job.snapshot.engine.provider === 'huggingface-space') return 'Hugging Face';
  return job.snapshot.execution === 'cloud' ? 'simulated cloud' : 'on this device';
}

export function jobStateLabel(job: JobRecord, uploading: boolean): { text: string; alert: boolean } {
  const n = job.slots.length;
  const ok = job.slots.filter((s) => s.state === 'succeeded').length;
  if (uploading) return { text: 'Uploading', alert: false };
  switch (job.state) {
    case 'queued':
      return { text: job.snapshot.execution === 'cloud' ? 'Queued' : 'Waiting', alert: false };
    case 'running':
      return { text: ok ? `Generating, ${ok} of ${n} ready` : 'Generating', alert: false };
    case 'saving':
      return { text: 'Saving', alert: false };
    case 'succeeded':
      return { text: 'Ready', alert: false };
    case 'partial':
      return { text: `Partial, ${ok} of ${n} ready`, alert: true };
    case 'failed':
      return { text: 'Failed', alert: true };
    case 'canceled':
      return { text: 'Canceled', alert: false };
    case 'unknown':
      return { text: 'Needs attention', alert: true };
    default:
      return { text: '', alert: false };
  }
}

export function slotStateLabel(slot: Slot, cloud: boolean): string {
  switch (slot.state) {
    case 'queued':
      return cloud ? 'Queued' : 'Waiting';
    case 'running':
      return 'Generating';
    case 'saving':
      return 'Saving';
    case 'failed':
      return 'Failed';
    case 'canceled':
      return 'Canceled';
    case 'unknown':
      return 'Outcome unknown';
    default:
      return 'Ready';
  }
}

export const ERROR_TEXT: Record<string, string> = {
  'test-failure': 'Test failure, turned on in Settings.',
  interrupted: 'The app closed before this image finished.',
  'not-found': 'The provider has no record of this image.',
  'render-failed': 'The image could not be rendered.',
  'source-missing': 'The source image is no longer stored on this device.',
  quota: 'Your Hugging Face GPU time for today is used up. It refills daily.',
  'no-token': 'The local server has no Hugging Face token. Add HF_TOKEN to prototype/.env.local, then restart it.',
  'token-rejected': 'Hugging Face rejected the token. Create a new read token, then restart the local server.',
  unreachable: "The local server can't reach Hugging Face. Check the connection.",
  'space-unavailable': 'The camera-angle model is not available right now. Try again later.',
  timeout: 'The model took too long. Try again when it is less busy.',
  'local-server': "The studio's local server isn't running. Start it with npm run dev.",
  'bad-request': 'The local server refused the request.',
  failed: 'The model could not make this view. Try again.',
};

const thumbCache = new Map<string, string>();

/** Scene-only previews for background options, drawn once and cached. */
export function sceneThumb(kind: SceneKind, color: string): string {
  const key = `${kind}:${color}`;
  let url = thumbCache.get(key);
  if (!url) {
    url = drawSceneThumb(kind, color, 144).toDataURL('image/jpeg', 0.85);
    thumbCache.set(key, url);
  }
  return url;
}

export function formatBytes(n: number): string {
  if (n < 1024 * 1024) return `${Math.max(1, Math.round(n / 1024))} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  } catch {
    return iso;
  }
}
