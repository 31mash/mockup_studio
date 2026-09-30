import { RATIOS, type SceneKind } from '../domain/catalogs';
import type { Capabilities, Execution } from '../domain/studio';
import { renderImage, type RenderInput } from './render';
import { canReproject, TURN_LIMITS } from './view3d';

export type Engine = {
  id: 'local-sketch' | 'cloud-sim';
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

export function engineFor(execution: Execution): Engine {
  return execution === 'cloud' ? CLOUD_SIM : LOCAL_SKETCH;
}

export function engineById(provider: string): Engine {
  return provider === CLOUD_SIM.provider ? CLOUD_SIM : LOCAL_SKETCH;
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
