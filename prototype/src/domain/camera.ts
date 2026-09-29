import { CAMERA_PRESETS, CAMERA_RANGE } from './catalogs';
import type { CameraIntent } from './studio';

export const ORIGINAL: CameraIntent = { kind: 'preset', name: 'original' };

function clamp(n: number, min: number, max: number): number {
  if (!Number.isFinite(n)) return 0;
  return Math.min(max, Math.max(min, Math.round(n)));
}

/** Clamp a custom intent to the PRD ranges; presets pass through unchanged. */
export function normalizeCamera(intent: CameraIntent): CameraIntent {
  if (intent.kind === 'preset') return { kind: 'preset', name: intent.name };
  return {
    kind: 'relative',
    rotation: clamp(intent.rotation, CAMERA_RANGE.rotation.min, CAMERA_RANGE.rotation.max),
    tilt: clamp(intent.tilt, CAMERA_RANGE.tilt.min, CAMERA_RANGE.tilt.max),
    zoom: clamp(intent.zoom, CAMERA_RANGE.zoom.min, CAMERA_RANGE.zoom.max),
  };
}

export function isOriginal(intent: CameraIntent): boolean {
  if (intent.kind === 'preset') return intent.name === 'original';
  return intent.rotation === 0 && intent.tilt === 0 && intent.zoom === 0;
}

/** Position the orbit guide and the sketch scene use for any intent. */
export function cameraPosition(intent: CameraIntent): { rotation: number; tilt: number; zoom: number } {
  if (intent.kind === 'relative') return { rotation: intent.rotation, tilt: intent.tilt, zoom: intent.zoom };
  const p = CAMERA_PRESETS.find((c) => c.id === intent.name) ?? CAMERA_PRESETS[0];
  return { rotation: p.rotation, tilt: p.tilt, zoom: 0 };
}

/** A new view has to invent unseen surfaces; show the fidelity note. */
export function isSubstantialChange(intent: CameraIntent): boolean {
  if (intent.kind === 'preset') return intent.name !== 'original' && intent.name !== 'front';
  return Math.abs(intent.rotation) >= 30 || Math.abs(intent.tilt) >= 20;
}

function signed(n: number): string {
  return n > 0 ? `+${n}` : `${n}`;
}

export function describeCamera(intent: CameraIntent): string {
  if (intent.kind === 'preset') return CAMERA_PRESETS.find((p) => p.id === intent.name)?.label ?? 'Original';
  if (isOriginal(intent)) return 'Original';
  return `Rotate ${signed(intent.rotation)}°, tilt ${signed(intent.tilt)}°, zoom ${signed(intent.zoom)}`;
}

export function shortCamera(intent: CameraIntent): string {
  if (intent.kind === 'preset') return describeCamera(intent);
  if (isOriginal(intent)) return 'Original';
  return 'Custom';
}
