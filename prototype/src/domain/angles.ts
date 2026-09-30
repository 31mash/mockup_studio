import { cameraPosition } from './camera';
import type { CameraIntent } from './studio';

// The camera-angle model is trained on 8 directions and 4 heights. A camera
// intent maps to the nearest one; for products, whatever is left over is
// turned in perspective in the browser, so any angle in between still works.

export const MODEL_AZIMUTHS = [0, 45, 90, 135, 180, 225, 270, 315] as const;
export const MODEL_ELEVATIONS = [-30, 0, 30, 60] as const;
/** The most the browser refines a generated view, in degrees. */
export const REFINE_LIMITS = { rotation: 22.5, tilt: 15 } as const;

const AZIMUTH_LABELS: Record<number, string> = {
  0: 'front',
  45: 'front-right quarter',
  90: 'right side',
  135: 'back-right quarter',
  180: 'back',
  225: 'back-left quarter',
  270: 'left side',
  315: 'front-left quarter',
};
const ELEVATION_LABELS: Record<number, string> = { [-30]: 'low angle', 0: 'eye level', 30: 'elevated', 60: 'high angle' };

export type ModelView = { azimuth: number; elevation: number };

export type AnglePlan = {
  /** The view to generate, or null when the photo already shows it (front, eye level). */
  view: ModelView | null;
  /** What the browser still turns in perspective afterwards. */
  refine: { rotation: number; tilt: number };
};

const nearest = (v: number, options: readonly number[]) => options.reduce((a, b) => (Math.abs(b - v) < Math.abs(a - v) ? b : a));
const clamp = (v: number, lim: number) => Math.max(-lim, Math.min(lim, v));
const tidy = (v: number) => Math.round(v) || 0;

/**
 * Splits a camera intent into a model view and a small perspective refinement.
 * Positive rotation moves the camera to the subject's right (three-quarter
 * right is +35, so it becomes the front-right quarter view); positive tilt
 * raises the camera. People are not refined: turning a photographed person in
 * perspective reads as a cardboard cutout, so they snap to the nearest view.
 */
export function planAngle(intent: CameraIntent, opts: { refine: boolean }): AnglePlan {
  const { rotation, tilt } = cameraPosition(intent);
  const step = Math.round(rotation / 45) * 45;
  const azimuth = ((step % 360) + 360) % 360;
  const elevation = nearest(tilt, MODEL_ELEVATIONS);
  const view = azimuth === 0 && elevation === 0 ? null : { azimuth, elevation };
  const refine = opts.refine
    ? { rotation: tidy(clamp(rotation - step, REFINE_LIMITS.rotation)), tilt: tidy(clamp(tilt - elevation, REFINE_LIMITS.tilt)) }
    : { rotation: 0, tilt: 0 };
  return { view, refine };
}

export function describeView(view: ModelView): string {
  return `${AZIMUTH_LABELS[view.azimuth] ?? `${view.azimuth}°`} view, ${ELEVATION_LABELS[view.elevation] ?? `${view.elevation}°`}`;
}

/** One line for job details: what was generated and what was refined. */
export function describePlan(plan: AnglePlan): string {
  const parts: string[] = [];
  if (plan.view) parts.push(`generated as the ${describeView(plan.view)}`);
  const { rotation, tilt } = plan.refine;
  if (rotation || tilt) {
    const bits = [rotation ? `${Math.abs(rotation)}° ${rotation > 0 ? 'right' : 'left'}` : '', tilt ? `${Math.abs(tilt)}° ${tilt > 0 ? 'higher' : 'lower'}` : ''].filter(Boolean);
    parts.push(`${plan.view ? 'then ' : ''}turned ${bits.join(' and ')} in perspective`);
  }
  return parts.join(', ');
}
