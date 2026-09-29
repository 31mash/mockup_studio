// Shared contracts from the implementation plan ("Shared design contracts").
// Names match the plan so the prototype can seed the real build.

export type StudioTab = 'product' | 'model';
export type OutputCount = 1 | 2 | 4;
export const OUTPUT_COUNTS: readonly OutputCount[] = [1, 2, 4];

export type Ratio = 'auto' | '1:1' | '3:2' | '2:3' | '4:3' | '3:4' | '9:16' | '16:9' | '21:9';

export type CameraPreset =
  | 'original'
  | 'front'
  | 'three-quarter-left'
  | 'three-quarter-right'
  | 'left-profile'
  | 'right-profile'
  | 'top-down';

export type CameraIntent =
  | { kind: 'preset'; name: CameraPreset }
  | { kind: 'relative'; rotation: number; tilt: number; zoom: number };

export type Source =
  | { kind: 'upload'; assetId: string }
  | { kind: 'catalog'; modelId: string; assetId: string };

export type Draft = {
  tab: StudioTab;
  source: Source | null;
  ratio: Ratio;
  backgroundId: string;
  monochromeColor?: string;
  camera: CameraIntent;
  prompt: string;
  count: OutputCount;
};

export type Execution = 'cloud' | 'local';
export type Framing = 'native' | 'extend' | 'fit';

export type JobSnapshot = {
  schemaVersion: 1;
  id: string;
  projectId: string;
  createdAt: string;
  queuedIntentId?: string;
  draft: Draft & { source: Source };
  execution: Execution;
  engine: { provider: string; model: string; version: string };
  promptVersion: string;
  brief: string;
  target: { width: number; height: number; framing: Framing };
};

export type QueuedIntent = {
  schemaVersion: 1;
  id: string;
  projectId: string;
  createdAt: string;
  draft: Draft & { source: Source };
  requestedExecution: 'cloud';
};

export type SlotState = 'queued' | 'running' | 'saving' | 'succeeded' | 'failed' | 'canceled' | 'unknown';

export type Slot = {
  index: number;
  attempt: number;
  state: SlotState;
  remoteId?: string;
  assetId?: string;
  errorCode?: string;
  seed?: number;
};

export type JobState =
  | 'awaiting-review'
  | 'queued'
  | 'running'
  | 'saving'
  | 'succeeded'
  | 'partial'
  | 'failed'
  | 'canceled'
  | 'unknown';

export type JobRecord = {
  snapshot: JobSnapshot;
  slots: Slot[];
  state: JobState;
  /** Marks jobs the app created to show the tool working on first open. */
  example?: boolean;
};

export type Issue = { field: string; code: string; message: string };
export type Dimensions = { width: number; height: number };

/**
 * `scene-only` is a prototype addition to the plan's enum: the sketch engine
 * moves the scene and framing for a camera change but cannot redraw the subject.
 */
export type CameraSupport = 'validated-view-control' | 'qualified-prompt' | 'scene-only';

export type Capabilities = {
  referenceEdit: boolean;
  offline: boolean;
  cancel: boolean;
  maxParallel: number;
  camera: CameraSupport;
  supportedCameraIntents: string[];
  supportedRatios: Ratio[];
  /** Output dimensions must be a multiple of this (1 = any size). */
  dimensionStep: number;
};

export type AssetRole = 'product' | 'person' | 'result';

export type AssetMeta = {
  id: string;
  role: AssetRole;
  name: string;
  mime: string;
  width: number;
  height: number;
  createdAt: string;
  origin: 'upload' | 'sample' | 'catalog' | 'generated';
  hasAlpha?: boolean;
  lowResolution?: boolean;
  rightsAcknowledged?: boolean;
  /** Up to four tones sampled from the image, used for placeholder mattes. */
  palette?: string[];
  /** Saved products appear in "Choose saved". */
  saved?: boolean;
};

export type Settings = {
  execution: Execution;
  simulateOffline: boolean;
  failOneSlot: boolean;
  theme: 'system' | 'light' | 'dark';
};

export type Project = {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  schemaVersion: 1;
};
