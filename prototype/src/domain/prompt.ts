import { findBackground, RATIOS } from './catalogs';
import { describeCamera, isOriginal } from './camera';
import { findModel, isMinor } from './models';
import type { Draft, Ratio, StudioTab } from './studio';

/** Versioned so every job records which template built its brief. */
export const PROMPT_VERSION = 'brief-2026-09-29.1';

const PRESERVE: Record<StudioTab, string> = {
  product:
    'Preserve the visible silhouette, proportions, color, material, logo and readable packaging text. Do not add brands, slogans or text that are not in the reference.',
  model:
    'Preserve identity, skin tone and distinctive features. Do not beautify the person or change their apparent age. Do not infer or change demographic traits.',
};

function ratioLine(ratio: Ratio, width: number, height: number): string {
  const orient = width === height ? 'square' : width > height ? 'landscape' : 'portrait';
  const label = ratio === 'auto' ? 'Auto (follows the reference)' : ratio;
  return `Framing: ${label}, ${orient}, ${width} x ${height} px. Keep the whole subject in frame. Never stretch or crop it.`;
}

/**
 * Builds the generation brief from structured settings plus the user's text.
 * Deterministic, so the cloud server and the local companion can share it.
 */
export function composeBrief(draft: Draft, target: { width: number; height: number }, sourceName: string): string {
  const bg = findBackground(draft.tab, draft.backgroundId);
  const lines: string[] = [];

  if (draft.source?.kind === 'catalog') {
    const model = findModel(draft.source.modelId);
    lines.push(`Subject: image 1 is the catalog reference for model "${model?.label ?? draft.source.modelId}". Keep this exact person.`);
    if (model && isMinor(model)) lines.push('Keep the scene age-appropriate. The person stays fully clothed.');
  } else {
    const role = draft.tab === 'product' ? 'product' : 'person';
    lines.push(`Subject: image 1 ("${sourceName}") is the ${role} reference. Keep this exact ${role}.`);
  }

  const color = draft.backgroundId === 'seamless-monochrome' && draft.monochromeColor ? ` Color ${draft.monochromeColor}.` : '';
  lines.push(`Scene: ${bg.label}. ${bg.description}.${color}`);
  lines.push(ratioLine(draft.ratio, target.width, target.height));
  lines.push(
    isOriginal(draft.camera)
      ? 'Camera: keep the original view of the reference.'
      : `Camera: ${describeCamera(draft.camera)}${draft.camera.kind === 'relative' ? ', relative to the reference camera' : ', relative to the subject'}.`,
  );
  lines.push(`Preserve: ${PRESERVE[draft.tab]}`);

  const text = draft.prompt.trim();
  if (text) {
    lines.push(`Direction from the user: "${text}"`);
    lines.push('If the direction conflicts with the scene, framing or camera above, follow the settings above.');
  }
  return lines.join('\n');
}

export type Conflict = { control: 'ratio' | 'background' | 'angle'; term: string; message: string };

type Rule = { re: RegExp; value: string };

const RATIO_RULES: Rule[] = [
  { re: /\b(square|1:1)\b/i, value: '1:1' },
  { re: /\b(16:9|widescreen)\b/i, value: '16:9' },
  { re: /\b9:16\b/i, value: '9:16' },
  { re: /\b21:9|panoram\w*\b/i, value: '21:9' },
  { re: /\b4:3\b/i, value: '4:3' },
  { re: /\b3:4\b/i, value: '3:4' },
  { re: /\b3:2\b/i, value: '3:2' },
  { re: /\b2:3\b/i, value: '2:3' },
];

const BG_RULES: Rule[] = [
  { re: /\b(white background|white studio|plain white)\b/i, value: 'studio-white' },
  { re: /\b(podium|plinth|pedestal)\b/i, value: 'minimalist-podium' },
  { re: /\b(office|workplace|boardroom)\b/i, value: 'corporate-office' },
  { re: /\b(caf[eé]|coffee shop)\b/i, value: 'cafe' },
  { re: /\b(beach|forest|mountains?|meadow|landscape|park|garden)\b/i, value: 'outdoor' },
  { re: /\b(kitchen|living room|bedroom|bathroom|shelf|interior)\b/i, value: 'aesthetic-indoor' },
];

const ANGLE_RULES: Rule[] = [
  { re: /\b(top[- ]down|overhead|bird'?s[- ]eye|flat[- ]lay)\b/i, value: 'top-down' },
  { re: /\b(side view|profile view|in profile)\b/i, value: 'profile' },
  { re: /\b(three[- ]quarter|3\/4 view)\b/i, value: 'three-quarter' },
  { re: /\b(front view|head[- ]on|straight on)\b/i, value: 'front' },
];

function family(bgId: string): string {
  return bgId === 'natural-outdoor' || bgId === 'natural-outdoor-environment' ? 'outdoor' : bgId;
}

function cameraFamily(draft: Draft): string {
  const cam = draft.camera;
  if (cam.kind === 'relative') return 'custom';
  if (cam.name.endsWith('profile')) return 'profile';
  if (cam.name.startsWith('three-quarter')) return 'three-quarter';
  return cam.name;
}

/**
 * Flags free text that disagrees with a structured control, only where the
 * match is reliable. Controls always win; this tells the user where to look.
 */
export function detectConflicts(draft: Draft): Conflict[] {
  const text = draft.prompt;
  if (!text.trim()) return [];
  const out: Conflict[] = [];

  for (const r of RATIO_RULES) {
    const m = text.match(r.re);
    if (m && draft.ratio !== r.value) {
      const current = RATIOS.find((x) => x.id === draft.ratio)?.label ?? draft.ratio;
      out.push({ control: 'ratio', term: m[0], message: `Your text says "${m[0]}". Ratio is set to ${current}, and the Ratio setting decides the shape.` });
      break;
    }
  }

  for (const r of BG_RULES) {
    const m = text.match(r.re);
    if (m && family(draft.backgroundId) !== r.value) {
      const current = findBackground(draft.tab, draft.backgroundId).label;
      out.push({ control: 'background', term: m[0], message: `Your text mentions "${m[0]}". Background is set to ${current}, and the Background setting decides the scene.` });
      break;
    }
  }

  for (const r of ANGLE_RULES) {
    const m = text.match(r.re);
    if (m && cameraFamily(draft) !== r.value) {
      out.push({ control: 'angle', term: m[0], message: `Your text asks for "${m[0]}". The Angle setting decides the view, so set it there.` });
      break;
    }
  }
  return out;
}
