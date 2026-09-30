import { BACKGROUNDS, NATIVE_CANVAS, PROMPT_LIMIT } from './catalogs';
import { cameraPosition, ORIGINAL, normalizeCamera } from './camera';
import type {
  AssetMeta,
  Capabilities,
  Dimensions,
  Draft,
  Framing,
  Issue,
  JobRecord,
  OutputCount,
  Ratio,
  Slot,
  StudioTab,
} from './studio';
import { OUTPUT_COUNTS } from './studio';

/** PRD defaults: Auto ratio, Studio white, Original angle, blank prompt, one result. */
export function createDraft(tab: StudioTab): Draft {
  return {
    tab,
    source: null,
    ratio: 'auto',
    backgroundId: 'studio-white',
    camera: ORIGINAL,
    prompt: '',
    count: 1,
  };
}

export type ValidationContext = { sourceAsset?: AssetMeta };

export function validateDraft(draft: Draft, caps: Capabilities, ctx: ValidationContext = {}): Issue[] {
  const issues: Issue[] = [];

  if (!draft.source) {
    issues.push({
      field: 'source',
      code: 'missing-source',
      message: draft.tab === 'product' ? 'Add a product photo to generate.' : 'Upload a photo or select a model to generate.',
    });
  } else if (draft.source.kind === 'catalog' && draft.tab !== 'model') {
    issues.push({ field: 'source', code: 'unsupported-source', message: 'Catalog models belong to the Model tab.' });
  }

  const asset = ctx.sourceAsset;
  if (draft.source?.kind === 'upload' && asset && asset.role === 'person' && asset.origin === 'upload' && !asset.rightsAcknowledged) {
    issues.push({ field: 'rights', code: 'rights-required', message: 'Confirm you have the rights and consent to use this photo.' });
  }

  if (draft.prompt.length > PROMPT_LIMIT) {
    issues.push({ field: 'prompt', code: 'prompt-too-long', message: 'Shorten the description to 2,000 characters or fewer.' });
  }

  if (!(OUTPUT_COUNTS as readonly number[]).includes(draft.count)) {
    issues.push({ field: 'count', code: 'invalid-count', message: 'Choose 1, 2 or 4 results.' });
  }

  if (!BACKGROUNDS[draft.tab].some((b) => b.id === draft.backgroundId)) {
    issues.push({ field: 'background', code: 'background-unknown', message: 'Choose a background from the list.' });
  }

  if (!caps.supportedRatios.includes(draft.ratio)) {
    issues.push({ field: 'ratio', code: 'ratio-unsupported', message: `This engine can't export ${draft.ratio}.` });
  }

  const cam = draft.camera;
  if (JSON.stringify(normalizeCamera(cam)) !== JSON.stringify(cam)) {
    issues.push({ field: 'camera', code: 'camera-out-of-range', message: 'Camera values are outside the allowed range.' });
  }
  const camKey = cam.kind === 'preset' ? cam.name : 'relative';
  const pos = cameraPosition(cam);
  const turns = pos.rotation !== 0 || pos.tilt !== 0;
  if (!caps.supportedCameraIntents.includes(camKey)) {
    issues.push({
      field: 'camera',
      code: 'camera-unsupported',
      message: caps.cameraLimits
        ? 'Profile and top-down views need a generative engine. Choose a three-quarter view or a custom turn.'
        : "This engine can't change the camera angle.",
    });
  } else if (turns && draft.tab === 'model' && caps.turnsPeople === false) {
    issues.push({ field: 'camera', code: 'camera-people', message: 'Turning a person needs a generative engine. Keep the original angle, or adjust zoom only.' });
  } else if (caps.cameraLimits && cam.kind === 'relative') {
    const l = caps.cameraLimits;
    if (Math.abs(cam.rotation) > l.rotation || cam.tilt < l.tiltMin || cam.tilt > l.tiltMax) {
      issues.push({
        field: 'camera',
        code: 'camera-beyond-limits',
        message: `This engine turns up to ${l.rotation}° and tilts from ${l.tiltMin}° to ${l.tiltMax}°.`,
      });
    }
  }

  return issues;
}

export type Target = { width: number; height: number; framing: Framing; native: Dimensions };

const AUTO_LONG_EDGE = 1536;
const MAX_ASPECT = 21 / 9;
const MIN_ASPECT = 9 / 21;

/**
 * Final export size for a ratio. Fixed ratios match exactly. Auto follows the
 * source proportions (rounded to the nearest pixel) and, for sources beyond
 * 21:9, fits the whole image inside the widest supported frame.
 */
export function resolveTarget(ratio: Ratio, source: Dimensions, caps: Capabilities): Target {
  const step = Math.max(1, caps.dimensionStep);
  const snap = (n: number) => Math.max(step, Math.round(n / step) * step);

  if (ratio !== 'auto') {
    const [width, height] = NATIVE_CANVAS[ratio];
    const native = { width: snap(width), height: snap(height) };
    const framing: Framing = native.width === width && native.height === height ? 'native' : 'extend';
    return { width, height, framing, native };
  }

  const aspect = source.width / Math.max(1, source.height);
  const clamped = Math.min(MAX_ASPECT, Math.max(MIN_ASPECT, aspect));
  const width = clamped >= 1 ? AUTO_LONG_EDGE : Math.round(AUTO_LONG_EDGE * clamped);
  const height = clamped >= 1 ? Math.round(AUTO_LONG_EDGE / clamped) : AUTO_LONG_EDGE;
  const native = { width: snap(width), height: snap(height) };

  let framing: Framing = 'native';
  if (clamped !== aspect) framing = 'fit';
  else if (native.width !== width || native.height !== height) framing = 'extend';
  return { width, height, framing, native };
}

/** Count is the total number of outputs: one slot per requested image. */
export function planSlots(count: OutputCount): Slot[] {
  return Array.from({ length: count }, (_, index) => ({ index, attempt: 1, state: 'queued' as const }));
}

/** Only failed slots can be retried; unknown outcomes need reconciling first. */
export function retryableSlots(slots: Slot[]): number[] {
  return slots.filter((s) => s.state === 'failed').map((s) => s.index);
}

export function summarizeSlots(slots: Slot[]): JobRecord['state'] {
  if (slots.some((s) => s.state === 'running')) return 'running';
  if (slots.some((s) => s.state === 'saving')) return 'saving';
  if (slots.some((s) => s.state === 'queued')) return 'queued';
  if (slots.some((s) => s.state === 'unknown')) return 'unknown';
  const ok = slots.filter((s) => s.state === 'succeeded').length;
  if (ok === slots.length) return 'succeeded';
  if (ok > 0) return 'partial';
  if (slots.every((s) => s.state === 'canceled')) return 'canceled';
  return 'failed';
}

export function isActive(state: JobRecord['state']): boolean {
  return state === 'running' || state === 'saving' || state === 'queued';
}

export function generateLabel(count: OutputCount): string {
  return count === 1 ? 'Generate 1 image' : `Generate ${count} images`;
}

export function newId(prefix: string): string {
  const rand =
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID().replace(/-/g, '').slice(0, 12)
      : Math.random().toString(36).slice(2, 14);
  return `${prefix}_${rand}`;
}
