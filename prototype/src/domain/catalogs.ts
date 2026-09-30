import type { CameraPreset, Ratio, StudioTab } from './studio';

export type RatioOption = { id: Ratio; label: string; w: number; h: number };

/** The nine supplied options, in the supplied order (PRD section 7). */
export const RATIOS: readonly RatioOption[] = [
  { id: 'auto', label: 'Auto', w: 0, h: 0 },
  { id: '1:1', label: '1:1', w: 1, h: 1 },
  { id: '3:2', label: '3:2', w: 3, h: 2 },
  { id: '2:3', label: '2:3', w: 2, h: 3 },
  { id: '4:3', label: '4:3', w: 4, h: 3 },
  { id: '3:4', label: '3:4', w: 3, h: 4 },
  { id: '9:16', label: '9:16', w: 9, h: 16 },
  { id: '16:9', label: '16:9', w: 16, h: 9 },
  { id: '21:9', label: '21:9', w: 21, h: 9 },
];

/**
 * Candidate native canvases from docs/research/sources-and-decisions.md.
 * Each matches its ratio exactly.
 */
export const NATIVE_CANVAS: Record<Exclude<Ratio, 'auto'>, [number, number]> = {
  '1:1': [1024, 1024],
  '3:2': [1536, 1024],
  '2:3': [1024, 1536],
  '4:3': [1536, 1152],
  '3:4': [1152, 1536],
  '9:16': [864, 1536],
  '16:9': [1536, 864],
  '21:9': [1792, 768],
};

export type SceneKind =
  | 'studio-white'
  | 'seamless-monochrome'
  | 'minimalist-podium'
  | 'natural-outdoor'
  | 'aesthetic-indoor'
  | 'natural-outdoor-environment'
  | 'corporate-office'
  | 'cafe';

export type BackgroundOption = { id: SceneKind; label: string; description: string };

/** PRD section 8. Both outdoor labels are kept, with distinct descriptions. */
export const BACKGROUNDS: Record<StudioTab, readonly BackgroundOption[]> = {
  product: [
    { id: 'studio-white', label: 'Studio white', description: 'White studio sweep, soft neutral light, natural contact shadow' },
    { id: 'seamless-monochrome', label: 'Seamless Monochromes', description: 'One color across background and surface' },
    { id: 'minimalist-podium', label: 'Minimalist Podiums', description: 'A simple plinth in uncluttered space, sized to the product' },
    { id: 'natural-outdoor', label: 'Natural Outdoor', description: 'Close outdoor surface in daylight, with a little foliage or sky' },
    { id: 'aesthetic-indoor', label: 'Aesthetic Indoor Space', description: 'A styled table or shelf in a calm home interior' },
    { id: 'natural-outdoor-environment', label: 'Natural Outdoor Environment', description: 'A wider garden, park or landscape scene' },
  ],
  model: [
    { id: 'studio-white', label: 'Studio white', description: 'White studio portrait environment' },
    { id: 'seamless-monochrome', label: 'Seamless Monochromes', description: 'Single-color seamless studio' },
    { id: 'corporate-office', label: 'Corporate office', description: 'Contemporary office with an unobtrusive background' },
    { id: 'cafe', label: 'Cafe', description: 'Natural café setting with soft ambient light' },
    { id: 'natural-outdoor', label: 'Natural Outdoor', description: 'Simple outdoor portrait with a close natural background' },
    { id: 'aesthetic-indoor', label: 'Aesthetic Indoor Space', description: 'A carefully styled home or studio interior' },
    { id: 'natural-outdoor-environment', label: 'Natural Outdoor Environment', description: 'A wider portrait in a park, garden or landscape' },
  ],
};

export function findBackground(tab: StudioTab, id: string): BackgroundOption {
  return BACKGROUNDS[tab].find((b) => b.id === id) ?? BACKGROUNDS[tab][0];
}

export type Swatch = { name: string; hex: string };

/** Optional color for Seamless Monochromes. */
export const MONOCHROME_SWATCHES: readonly Swatch[] = [
  { name: 'Stone', hex: '#C8C2B6' },
  { name: 'Sage', hex: '#A9B5A0' },
  { name: 'Powder blue', hex: '#A7BCCB' },
  { name: 'Blush', hex: '#D9B4A8' },
  { name: 'Butter', hex: '#E3D199' },
  { name: 'Graphite', hex: '#55565A' },
];
export const DEFAULT_MONOCHROME = MONOCHROME_SWATCHES[0].hex;

export type PresetOption = { id: CameraPreset; label: string; rotation: number; tilt: number };

/**
 * Semantic presets (PRD section 9). Rotation and tilt are only where the
 * orbit guide draws the camera; the stored intent stays the preset name.
 */
export const CAMERA_PRESETS: readonly PresetOption[] = [
  { id: 'original', label: 'Original', rotation: 0, tilt: 0 },
  { id: 'front', label: 'Front', rotation: 0, tilt: 0 },
  { id: 'three-quarter-left', label: 'Three-quarter left', rotation: -35, tilt: 0 },
  { id: 'three-quarter-right', label: 'Three-quarter right', rotation: 35, tilt: 0 },
  { id: 'left-profile', label: 'Left profile', rotation: -90, tilt: 0 },
  { id: 'right-profile', label: 'Right profile', rotation: 90, tilt: 0 },
  { id: 'top-down', label: 'Top-down', rotation: 0, tilt: 90 },
];

export const CAMERA_RANGE = {
  rotation: { min: -180, max: 180 },
  tilt: { min: -90, max: 90 },
  zoom: { min: -50, max: 50 },
} as const;

export type AgeGroup = 'kid' | 'teen' | 'young-adult' | 'middle-aged' | 'older-adult';
export type Presentation = 'female' | 'male';
export type Tone = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

/** Proposed internal ranges from PRD section 6; product taxonomy, not legal definitions. */
export const AGE_GROUPS: readonly { id: AgeGroup; label: string; range: string }[] = [
  { id: 'kid', label: 'Kid', range: '6-12' },
  { id: 'teen', label: 'Teen', range: '13-17' },
  { id: 'young-adult', label: 'Young adult', range: '18-34' },
  { id: 'middle-aged', label: 'Middle-aged', range: '35-59' },
  { id: 'older-adult', label: 'Older adult', range: '60+' },
];

export const PRESENTATIONS: readonly { id: Presentation; label: string }[] = [
  { id: 'female', label: 'Female' },
  { id: 'male', label: 'Male' },
];

/**
 * Ten swatches ordered light to deep. Values from the Monk Skin Tone Scale
 * (Dr. Ellis Monk, Google; CC BY 4.0). Labels stay "Tone 1" to "Tone 10".
 */
export const TONES: readonly { id: Tone; label: string; hex: string }[] = [
  { id: 1, label: 'Tone 1', hex: '#F6EDE4' },
  { id: 2, label: 'Tone 2', hex: '#F3E7DB' },
  { id: 3, label: 'Tone 3', hex: '#F7EAD0' },
  { id: 4, label: 'Tone 4', hex: '#EADABA' },
  { id: 5, label: 'Tone 5', hex: '#D7BD96' },
  { id: 6, label: 'Tone 6', hex: '#A07E56' },
  { id: 7, label: 'Tone 7', hex: '#825C43' },
  { id: 8, label: 'Tone 8', hex: '#604134' },
  { id: 9, label: 'Tone 9', hex: '#3A312A' },
  { id: 10, label: 'Tone 10', hex: '#292420' },
];

export function toneHex(tone: Tone): string {
  return TONES[tone - 1].hex;
}

export const PROMPT_LIMIT = 2000;

export const PROMPT_EXAMPLES: Record<StudioTab, string> = {
  product: 'Soft morning light and a gentle shadow.',
  model: 'Relaxed pose, warm late-afternoon light.',
};
