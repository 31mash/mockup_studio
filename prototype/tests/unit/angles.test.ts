import { describe, expect, test } from 'vitest';
import { describePlan, planAngle } from '../../src/domain/angles';
import { createDraft, validateDraft } from '../../src/domain/generation';
import type { CameraIntent, Draft } from '../../src/domain/studio';
import { HF_ANGLES, LOCAL_SKETCH, engineById, engineFor } from '../../src/engine/engines';

const preset = (name: Extract<CameraIntent, { kind: 'preset' }>['name']): CameraIntent => ({ kind: 'preset', name });
const custom = (rotation: number, tilt = 0, zoom = 0): CameraIntent => ({ kind: 'relative', rotation, tilt, zoom });
const product = { refine: true };
const person = { refine: false };

describe('camera intent to model view', () => {
  test('original and front need no generation', () => {
    expect(planAngle(preset('original'), product)).toEqual({ view: null, refine: { rotation: 0, tilt: 0 } });
    expect(planAngle(preset('front'), product).view).toBeNull();
  });

  test('presets map to the trained views, positive rotation to the right', () => {
    expect(planAngle(preset('three-quarter-right'), product)).toEqual({ view: { azimuth: 45, elevation: 0 }, refine: { rotation: -10, tilt: 0 } });
    expect(planAngle(preset('three-quarter-left'), product)).toEqual({ view: { azimuth: 315, elevation: 0 }, refine: { rotation: 10, tilt: 0 } });
    expect(planAngle(preset('right-profile'), product).view).toEqual({ azimuth: 90, elevation: 0 });
    expect(planAngle(preset('left-profile'), product).view).toEqual({ azimuth: 270, elevation: 0 });
  });

  test('top-down uses the highest trained view and refines the rest within limits', () => {
    expect(planAngle(preset('top-down'), product)).toEqual({ view: { azimuth: 0, elevation: 60 }, refine: { rotation: 0, tilt: 15 } });
  });

  test('back views both ways round', () => {
    expect(planAngle(custom(180), product).view).toEqual({ azimuth: 180, elevation: 0 });
    expect(planAngle(custom(-180), product).view).toEqual({ azimuth: 180, elevation: 0 });
    expect(planAngle(custom(-135), product).view).toEqual({ azimuth: 225, elevation: 0 });
  });

  test('small turns stay with the photo; products are refined, people are not', () => {
    expect(planAngle(custom(20, 10), product)).toEqual({ view: null, refine: { rotation: 20, tilt: 10 } });
    expect(planAngle(custom(20, 10), person)).toEqual({ view: null, refine: { rotation: 0, tilt: 0 } });
    expect(planAngle(custom(30), person)).toEqual({ view: { azimuth: 45, elevation: 0 }, refine: { rotation: 0, tilt: 0 } });
    expect(planAngle(custom(23), product)).toEqual({ view: { azimuth: 45, elevation: 0 }, refine: { rotation: -22, tilt: 0 } });
  });

  test('tilt snaps to the nearest trained height', () => {
    expect(planAngle(custom(0, -90), product)).toEqual({ view: { azimuth: 0, elevation: -30 }, refine: { rotation: 0, tilt: -15 } });
    expect(planAngle(custom(90, 40), product)).toEqual({ view: { azimuth: 90, elevation: 30 }, refine: { rotation: 0, tilt: 10 } });
  });

  test('job details describe what was generated and refined', () => {
    expect(describePlan(planAngle(preset('three-quarter-right'), product))).toBe('generated as the front-right quarter view, eye level, then turned 10° left in perspective');
    expect(describePlan(planAngle(preset('right-profile'), person))).toBe('generated as the right side view, eye level');
    expect(describePlan(planAngle(custom(20, -5), product))).toBe('turned 20° right and 5° lower in perspective');
  });
});

describe('generative engine', () => {
  const withSource = (d: Draft): Draft => ({ ...d, source: { kind: 'upload', assetId: 'a1' } });

  test('is chosen by the cloud provider setting and found by provider id', () => {
    expect(engineFor('cloud', 'huggingface')).toBe(HF_ANGLES);
    expect(engineFor('local', 'huggingface')).toBe(LOCAL_SKETCH);
    expect(engineById('huggingface-space')).toBe(HF_ANGLES);
  });

  test('allows profiles, top-down and turning people', () => {
    for (const name of ['left-profile', 'right-profile', 'top-down'] as const) {
      expect(validateDraft({ ...withSource(createDraft('product')), camera: preset(name) }, HF_ANGLES.caps)).toEqual([]);
      expect(validateDraft({ ...withSource(createDraft('model')), camera: preset(name) }, HF_ANGLES.caps)).toEqual([]);
    }
  });

  test('still names its limits: no worm-eye views', () => {
    const issues = validateDraft({ ...withSource(createDraft('product')), camera: custom(0, -60) }, HF_ANGLES.caps);
    expect(issues.map((i) => i.code)).toEqual(['camera-beyond-limits']);
  });
});
