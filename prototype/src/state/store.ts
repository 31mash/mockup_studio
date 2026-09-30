import { useSyncExternalStore } from 'react';
import { createDraft } from '../domain/generation';
import type { AssetMeta, Draft, JobRecord, Project, QueuedIntent, Settings, StudioTab } from '../domain/studio';
import { saveJSON } from '../storage/db';
import type { SaveMode } from '../storage/download';
import { engineFor, type Engine } from '../engine/engines';
import type { LocalStatus } from '../engine/generative';

export type Toast = { id: number; text: string; tone: 'info' | 'error' };

export type AppState = {
  ready: boolean;
  project: Project;
  tab: StudioTab;
  drafts: Record<StudioTab, Draft>;
  assets: Record<string, AssetMeta>;
  jobs: JobRecord[];
  queue: QueuedIntent[];
  settings: Settings;
  storage: 'ok' | 'unavailable' | 'error';
  browserOnline: boolean;
  /** Transient per-job phase the slots can't express (cloud upload). */
  uploading: Record<string, boolean>;
  toasts: Toast[];
  saveMode: SaveMode;
  /** The studio's local server, which runs the generative engine. */
  local: LocalStatus;
};

export type Persisted = Pick<AppState, 'project' | 'tab' | 'drafts' | 'assets' | 'jobs' | 'queue' | 'settings'>;
export const STATE_KEY = 'state:v1';

export function newProject(): Project {
  const now = new Date().toISOString();
  return { id: `project_${Date.now().toString(36)}`, name: 'Untitled project', createdAt: now, updatedAt: now, schemaVersion: 1 };
}

export const DEFAULT_SETTINGS: Settings = { execution: 'local', cloudProvider: 'simulated', simulateOffline: false, failOneSlot: false, theme: 'system' };

/** The engine new jobs use, from Settings. */
export function currentEngine(s: AppState): Engine {
  return engineFor(s.settings.execution, s.settings.cloudProvider);
}

let state: AppState = {
  ready: false,
  project: newProject(),
  tab: 'product',
  drafts: { product: createDraft('product'), model: createDraft('model') },
  assets: {},
  jobs: [],
  queue: [],
  settings: DEFAULT_SETTINGS,
  storage: 'ok',
  browserOnline: typeof navigator === 'undefined' ? true : navigator.onLine,
  uploading: {},
  toasts: [],
  saveMode: typeof window !== 'undefined' && 'claude' in window ? 'none' : 'browser',
  local: { state: 'checking' },
};

const listeners = new Set<() => void>();

export function getState(): AppState {
  return state;
}

export function setState(update: Partial<AppState> | ((s: AppState) => Partial<AppState>)): void {
  const patch = typeof update === 'function' ? update(state) : update;
  state = { ...state, ...patch };
  listeners.forEach((l) => l());
  if (state.ready && touchesPersisted(patch)) schedulePersist();
}

export function subscribe(l: () => void): () => void {
  listeners.add(l);
  return () => listeners.delete(l);
}

export function useApp<T>(selector: (s: AppState) => T): T {
  return useSyncExternalStore(subscribe, () => selector(state), () => selector(state));
}

export function isOnline(s: AppState): boolean {
  return s.browserOnline && !s.settings.simulateOffline;
}

const PERSISTED_KEYS: (keyof Persisted)[] = ['project', 'tab', 'drafts', 'assets', 'jobs', 'queue', 'settings'];

function touchesPersisted(patch: Partial<AppState>): boolean {
  return PERSISTED_KEYS.some((k) => k in patch);
}

let timer: ReturnType<typeof setTimeout> | null = null;
let failedOnce = false;

export function persistedSlice(s: AppState): Persisted {
  return { project: s.project, tab: s.tab, drafts: s.drafts, assets: s.assets, jobs: s.jobs, queue: s.queue, settings: s.settings };
}

function schedulePersist(): void {
  if (timer) clearTimeout(timer);
  timer = setTimeout(async () => {
    timer = null;
    try {
      await saveJSON(STATE_KEY, persistedSlice(state));
      if (state.storage === 'error') setState({ storage: 'ok' });
    } catch {
      if (!failedOnce) toast('Changes could not be saved on this device. Export the project to keep a copy.', 'error');
      failedOnce = true;
      setState({ storage: 'error' });
    }
  }, 250);
}

/** Save now, before an action that must not lose the draft (like a submit). */
export async function flushPersist(): Promise<void> {
  if (timer) {
    clearTimeout(timer);
    timer = null;
  }
  try {
    await saveJSON(STATE_KEY, persistedSlice(state));
  } catch {
    setState({ storage: 'error' });
  }
}

let toastId = 0;
export function toast(text: string, tone: Toast['tone'] = 'info'): void {
  const id = ++toastId;
  setState((s) => ({ toasts: [...s.toasts.slice(-2), { id, text, tone }] }));
  setTimeout(() => setState((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })), tone === 'error' ? 8000 : 5000);
}

export function dismissToast(id: number): void {
  setState((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
}

export function updateDraft(tab: StudioTab, patch: Partial<Draft>): void {
  setState((s) => ({ drafts: { ...s.drafts, [tab]: { ...s.drafts[tab], ...patch } } }));
}

export function updateJob(id: string, fn: (j: JobRecord) => JobRecord): void {
  setState((s) => ({ jobs: s.jobs.map((j) => (j.snapshot.id === id ? fn(j) : j)) }));
}

export function updateSettings(patch: Partial<Settings>): void {
  setState((s) => ({ settings: { ...s.settings, ...patch } }));
}
