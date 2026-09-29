import { AGE_GROUPS, PRESENTATIONS, type AgeGroup, type Presentation, type Tone } from './catalogs';

export type ModelPreset = {
  id: string;
  label: string;
  assetId: string;
  tone: Tone;
  presentation: Presentation;
  ageGroup: AgeGroup;
  rights: { source: string; license: string };
  cached: boolean;
  /** Clothing color for the stand-in figure, so identities stay distinct. */
  wardrobe: string;
};

const STAND_IN = { source: 'Prototype stand-in figure', license: 'No photo yet. Replace with licensed or synthetic references.' };

function preset(
  id: string,
  label: string,
  tone: Tone,
  presentation: Presentation,
  ageGroup: AgeGroup,
  wardrobe: string,
): ModelPreset {
  return { id, label, assetId: `catalog:${id}`, tone, presentation, ageGroup, rights: STAND_IN, cached: true, wardrobe };
}

/**
 * Curated catalog with stable identities. Every tone, presentation and age
 * group returns at least one entry (PRD section 6 release rule).
 */
export const MODEL_CATALOG: readonly ModelPreset[] = [
  preset('maya', 'Maya', 4, 'female', 'teen', '#6F7F9A'),
  preset('tomas', 'Tomás', 6, 'male', 'teen', '#8A6B4E'),
  preset('aiko', 'Aiko', 2, 'female', 'kid', '#C98A7A'),
  preset('kwame', 'Kwame', 9, 'male', 'kid', '#D6B25E'),
  preset('leilani', 'Leilani', 7, 'female', 'young-adult', '#E4DED3'),
  preset('hana', 'Hana', 3, 'female', 'young-adult', '#3F4A44'),
  preset('arjun', 'Arjun', 5, 'male', 'young-adult', '#2F3A4F'),
  preset('ingrid', 'Ingrid', 1, 'female', 'middle-aged', '#7A3E3A'),
  preset('dario', 'Dario', 3, 'male', 'middle-aged', '#9AA39B'),
  preset('mateus', 'Mateus', 7, 'male', 'middle-aged', '#B8A99A'),
  preset('folake', 'Folake', 10, 'female', 'older-adult', '#C4663F'),
  preset('samir', 'Samir', 8, 'male', 'older-adult', '#4E5A5C'),
];

export type ModelFilters = { tone: Tone | null; presentation: Presentation | null; ageGroup: AgeGroup | null };
export const NO_FILTERS: ModelFilters = { tone: null, presentation: null, ageGroup: null };

export function filterModels(filters: ModelFilters, catalog: readonly ModelPreset[] = MODEL_CATALOG): ModelPreset[] {
  return catalog.filter(
    (m) =>
      (filters.tone === null || m.tone === filters.tone) &&
      (filters.presentation === null || m.presentation === filters.presentation) &&
      (filters.ageGroup === null || m.ageGroup === filters.ageGroup),
  );
}

export function findModel(id: string): ModelPreset | undefined {
  return MODEL_CATALOG.find((m) => m.id === id);
}

export function describeModel(m: ModelPreset): string {
  const age = AGE_GROUPS.find((a) => a.id === m.ageGroup)?.label ?? '';
  const pres = PRESENTATIONS.find((p) => p.id === m.presentation)?.label.toLowerCase() ?? '';
  return `${age}, ${pres}, Tone ${m.tone}`;
}

export function isMinor(m: ModelPreset): boolean {
  return m.ageGroup === 'kid' || m.ageGroup === 'teen';
}
