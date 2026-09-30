import { CAMERA_PRESETS, RATIOS, type SceneKind } from '../domain/catalogs';
import type { Capabilities, Execution } from '../domain/studio';
import { renderImage, type RenderInput } from './render';
import { canReproject, TURN_LIMITS } from './view3d';

export type Engine = {
  id: 'local-sketch' | 'cloud-sim' | 'hf-angles';
  label: string;
  execution: Execution;
  provider: string;
  model: string;
  version: string;
  caps: Capabilities;
  /** Plain-language line shown under Generate. */
  runsOn: string;
};

/** Views the photo can supply. Profiles and top-down need new surfaces. */
const TURNABLE = ['original', 'front', 'three-quarter-left', 'three-quarter-right', 'relative'];

const turnOk = typeof document !== 'undefined' && canReproject();

const baseCaps: Omit<Capabilities, 'maxParallel' | 'offline'> = {
  referenceEdit: true,
  cancel: true,
  camera: 'reprojection',
  supportedCameraIntents: turnOk ? TURNABLE : ['original', 'front'],
  supportedRatios: RATIOS.map((r) => r.id),
  dimensionStep: 1,
  cameraLimits: turnOk ? { ...TURN_LIMITS } : { rotation: 0, tiltMin: 0, tiltMax: 0 },
  turnsPeople: false,
};

/**
 * Prototype engines. Both use the in-browser compositor: it separates the
 * real product, turns it in true perspective within the photo's limits, and
 * places it in a painted scene with studio shadows. It does not invent
 * views the photo does not contain; a qualified image model would.
 */
export const LOCAL_SKETCH: Engine = {
  id: 'local-sketch',
  label: 'On this device',
  execution: 'local',
  provider: 'prototype',
  model: 'sketch-compositor',
  version: '0.2.0',
  caps: { ...baseCaps, offline: true, maxParallel: 1 },
  runsOn: 'Runs on this device. Nothing is uploaded.',
};

export const CLOUD_SIM: Engine = {
  id: 'cloud-sim',
  label: 'Cloud (simulated)',
  execution: 'cloud',
  provider: 'simulated-cloud',
  model: 'sketch-compositor',
  version: '0.2.0',
  caps: { ...baseCaps, offline: false, maxParallel: 4 },
  runsOn: 'Runs in the simulated cloud. No cost in this prototype.',
};

/**
 * A real image model: Qwen-Image-Edit-2511 with fal's Multiple-Angles LoRA,
 * on a Hugging Face Space. The studio's local server calls it with your token
 * (server/angles.ts). It draws the views a photo does not contain, profiles,
 * backs and high angles included, for products and people. The browser then
 * cuts the new view out and places it in the scene with the usual shadows.
 */
export const HF_ANGLES: Engine = {
  id: 'hf-angles',
  label: 'Generative angles',
  execution: 'cloud',
  provider: 'huggingface-space',
  model: 'qwen-image-edit-2511-multiple-angles',
  version: 'lightning-4step',
  caps: {
    referenceEdit: true,
    offline: false,
    cancel: true,
    maxParallel: 1,
    camera: 'validated-view-control',
    supportedCameraIntents: [...CAMERA_PRESETS.map((p) => p.id), 'relative'],
    supportedRatios: RATIOS.map((r) => r.id),
    dimensionStep: 1,
    // All the way round; heights from low angle to top-down.
    cameraLimits: { rotation: 180, tiltMin: -45, tiltMax: 90 },
    turnsPeople: true,
  },
  runsOn: 'Each image is one generation on Hugging Face, sent by the local server with your token. It uses your account\'s GPU time.',
};

export type CloudProvider = 'simulated' | 'huggingface';

export function engineFor(execution: Execution, cloud: CloudProvider = 'simulated'): Engine {
  if (execution === 'local') return LOCAL_SKETCH;
  return cloud === 'huggingface' ? HF_ANGLES : CLOUD_SIM;
}

export function engineById(provider: string): Engine {
  return [CLOUD_SIM, HF_ANGLES].find((e) => e.provider === provider) ?? LOCAL_SKETCH;
}

export type SlotRender = Omit<RenderInput, 'scene'> & { scene: SceneKind };

export function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(new DOMException('Canceled', 'AbortError'));
    const t = setTimeout(resolve, ms);
    signal?.addEventListener(
      'abort',
      () => {
        clearTimeout(t);
        reject(new DOMException('Canceled', 'AbortError'));
      },
      { once: true },
    );
  });
}

/** Let the browser paint state changes before heavy canvas work. */
export function nextFrame(): Promise<void> {
  return new Promise((r) => requestAnimationFrame(() => setTimeout(r, 0)));
}

export function renderSlot(input: SlotRender): HTMLCanvasElement {
  return renderImage(input);
}
