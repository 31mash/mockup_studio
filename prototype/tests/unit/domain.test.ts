import { describe, expect, test } from 'vitest';
import { BACKGROUNDS, RATIOS, TONES, AGE_GROUPS, PRESENTATIONS } from '../../src/domain/catalogs';
import { normalizeCamera, isSubstantialChange } from '../../src/domain/camera';
import {
  createDraft,
  planSlots,
  resolveTarget,
  retryableSlots,
  summarizeSlots,
  validateDraft,
} from '../../src/domain/generation';
import { filterModels, MODEL_CATALOG, NO_FILTERS } from '../../src/domain/models';
import { composeBrief, detectConflicts } from '../../src/domain/prompt';
import type { Capabilities, Draft, OutputCount } from '../../src/domain/studio';

const caps: Capabilities = {
  referenceEdit: true,
  offline: true,
  cancel: true,
  maxParallel: 1,
  camera: 'scene-only',
  supportedCameraIntents: ['original', 'front', 'three-quarter-left', 'three-quarter-right', 'left-profile', 'right-profile', 'top-down', 'relative'],
  supportedRatios: RATIOS.map((r) => r.id),
  dimensionStep: 1,
};

const withSource = (d: Draft): Draft => ({ ...d, source: { kind: 'upload', assetId: 'a1' } });

describe('slots (plan task 2 representative test)', () => {
  test('four outputs produce four slots and retry only the failed slot', () => {
    const slots = planSlots(4);
    expect(slots.map((s) => s.index)).toEqual([0, 1, 2, 3]);
    slots.forEach((s) => {
      s.state = 'succeeded';
    });
    slots[2].state = 'failed';
    expect(retryableSlots(slots)).toEqual([2]);
    slots[2].state = 'unknown';
    expect(retryableSlots(slots)).toEqual([]);
  });

  test('summaries follow slot states', () => {
    const s = planSlots(4);
    expect(summarizeSlots(s)).toBe('queued');
    s[0].state = 'running';
    expect(summarizeSlots(s)).toBe('running');
    s.forEach((x) => (x.state = 'succeeded'));
    expect(summarizeSlots(s)).toBe('succeeded');
    s[3].state = 'failed';
    expect(summarizeSlots(s)).toBe('partial');
    s.forEach((x) => (x.state = 'failed'));
    expect(summarizeSlots(s)).toBe('failed');
    s.forEach((x) => (x.state = 'canceled'));
    expect(summarizeSlots(s)).toBe('canceled');
    s[1].state = 'unknown';
    expect(summarizeSlots(s)).toBe('unknown');
  });
});

describe('camera (plan task 5 representative test)', () => {
  test('clamps custom values and keeps presets', () => {
    expect(normalizeCamera({ kind: 'relative', rotation: 240, tilt: -120, zoom: 80 })).toEqual({
      kind: 'relative',
      rotation: 180,
      tilt: -90,
      zoom: 50,
    });
    expect(normalizeCamera({ kind: 'preset', name: 'front' })).toEqual({ kind: 'preset', name: 'front' });
  });

  test('front is a semantic preset, not a substantial change', () => {
    expect(isSubstantialChange({ kind: 'preset', name: 'front' })).toBe(false);
    expect(isSubstantialChange({ kind: 'preset', name: 'left-profile' })).toBe(true);
    expect(isSubstantialChange({ kind: 'relative', rotation: 10, tilt: 5, zoom: 40 })).toBe(false);
  });
});

describe('validation', () => {
  test('missing source blocks generation, empty prompt does not', () => {
    const d = createDraft('product');
    expect(validateDraft(d, caps).map((i) => i.code)).toEqual(['missing-source']);
    expect(validateDraft(withSource(d), caps)).toEqual([]);
  });

  test('rejects counts other than 1, 2 and 4', () => {
    for (const n of [3, 12]) {
      const d = { ...withSource(createDraft('product')), count: n as OutputCount };
      expect(validateDraft(d, caps).map((i) => i.code)).toContain('invalid-count');
    }
  });

  test('prompt limit is 2,000 characters', () => {
    const d = { ...withSource(createDraft('model')), prompt: 'x'.repeat(2001) };
    expect(validateDraft(d, caps).map((i) => i.code)).toContain('prompt-too-long');
  });

  test('uploaded person needs a rights acknowledgment', () => {
    const d = withSource(createDraft('model'));
    const asset = { id: 'a1', role: 'person' as const, name: 'p.jpg', mime: 'image/jpeg', width: 800, height: 1000, createdAt: '', origin: 'upload' as const };
    expect(validateDraft(d, caps, { sourceAsset: asset }).map((i) => i.code)).toEqual(['rights-required']);
    expect(validateDraft(d, caps, { sourceAsset: { ...asset, rightsAcknowledged: true } })).toEqual([]);
  });

  test('engine capability gates camera intents', () => {
    const noCamera = { ...caps, supportedCameraIntents: ['original'] };
    const d = { ...withSource(createDraft('product')), camera: { kind: 'preset' as const, name: 'top-down' as const } };
    expect(validateDraft(d, noCamera).map((i) => i.code)).toEqual(['camera-unsupported']);
  });
});

describe('ratios and framing', () => {
  test('all nine ratios, in the supplied order', () => {
    expect(RATIOS.map((r) => r.id)).toEqual(['auto', '1:1', '3:2', '2:3', '4:3', '3:4', '9:16', '16:9', '21:9']);
  });

  test('fixed ratios export exactly', () => {
    for (const r of RATIOS.filter((x) => x.id !== 'auto')) {
      const t = resolveTarget(r.id, { width: 1000, height: 1000 }, caps);
      expect(t.width * r.h).toBe(t.height * r.w);
      expect(t.framing).toBe('native');
    }
  });

  test('auto follows the source within one pixel', () => {
    const t = resolveTarget('auto', { width: 3000, height: 2000 }, caps);
    expect([t.width, t.height]).toEqual([1536, 1024]);
    const odd = resolveTarget('auto', { width: 1234, height: 987 }, caps);
    expect(Math.abs(odd.height - (odd.width * 987) / 1234)).toBeLessThanOrEqual(1);
  });

  test('extreme sources fit inside 9:21 and say so', () => {
    const t = resolveTarget('auto', { width: 1000, height: 4000 }, caps);
    expect(t.height).toBe(1536);
    expect(t.framing).toBe('fit');
  });

  test('a 16 px engine step records an extended native canvas', () => {
    const t = resolveTarget('auto', { width: 1234, height: 987 }, { ...caps, dimensionStep: 16 });
    expect(t.native.width % 16).toBe(0);
    expect(t.native.height % 16).toBe(0);
    expect(t.framing).toBe('extend');
  });
});

describe('catalogs', () => {
  test('six product and seven model backgrounds, both outdoor labels kept', () => {
    expect(BACKGROUNDS.product.map((b) => b.label)).toEqual([
      'Studio white',
      'Seamless Monochromes',
      'Minimalist Podiums',
      'Natural Outdoor',
      'Aesthetic Indoor Space',
      'Natural Outdoor Environment',
    ]);
    expect(BACKGROUNDS.model.map((b) => b.label)).toEqual([
      'Studio white',
      'Seamless Monochromes',
      'Corporate office',
      'Cafe',
      'Natural Outdoor',
      'Aesthetic Indoor Space',
      'Natural Outdoor Environment',
    ]);
  });

  test('every single filter value returns at least one model', () => {
    for (const t of TONES) expect(filterModels({ ...NO_FILTERS, tone: t.id }).length).toBeGreaterThan(0);
    for (const a of AGE_GROUPS) expect(filterModels({ ...NO_FILTERS, ageGroup: a.id }).length).toBeGreaterThan(0);
    for (const p of PRESENTATIONS) expect(filterModels({ ...NO_FILTERS, presentation: p.id }).length).toBeGreaterThan(0);
    expect(filterModels({ tone: null, presentation: 'female', ageGroup: 'teen' }).map((m) => m.label)).toEqual(['Maya']);
    expect(new Set(MODEL_CATALOG.map((m) => m.id)).size).toBe(MODEL_CATALOG.length);
  });
});

describe('prompt composer', () => {
  test('brief carries settings, preservation rules and user text', () => {
    const d = { ...withSource(createDraft('product')), prompt: 'Soft morning light', ratio: '3:4' as const };
    const brief = composeBrief(d, { width: 1152, height: 1536 }, 'bottle.png');
    expect(brief).toContain('Scene: Studio white.');
    expect(brief).toContain('1152 x 1536 px');
    expect(brief).toContain('readable packaging text');
    expect(brief).toContain('"Soft morning light"');
    expect(brief).toContain('follow the settings above');
  });

  test('minor catalog models get the age-appropriate line', () => {
    const d: Draft = { ...createDraft('model'), source: { kind: 'catalog', modelId: 'maya', assetId: 'catalog:maya' } };
    expect(composeBrief(d, { width: 864, height: 1536 }, '')).toContain('fully clothed');
  });

  test('conflicts name the control that decides', () => {
    const d = { ...withSource(createDraft('product')), ratio: '3:4' as const, prompt: 'A square shot on a beach, top-down' };
    const c = detectConflicts(d);
    expect(c.map((x) => x.control)).toEqual(['ratio', 'background', 'angle']);
    const agree = { ...d, ratio: '1:1' as const, backgroundId: 'natural-outdoor-environment', camera: { kind: 'preset' as const, name: 'top-down' as const } };
    expect(detectConflicts(agree)).toEqual([]);
  });
});
