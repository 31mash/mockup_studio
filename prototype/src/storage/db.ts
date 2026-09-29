import { createStore, del, get, keys, set, clear, type UseStore } from 'idb-keyval';

/**
 * Local project storage. IndexedDB when the browser allows it; otherwise an
 * in-memory map so the studio still works for the session, and the UI says
 * that nothing is being saved.
 */
type Backend = {
  get<T>(key: string): Promise<T | undefined>;
  set(key: string, value: unknown): Promise<void>;
  del(key: string): Promise<void>;
  keys(): Promise<string[]>;
  clear(): Promise<void>;
};

let backend: Backend | null = null;
let persistent = false;

function memoryBackend(): Backend {
  const m = new Map<string, unknown>();
  return {
    get: async <T,>(k: string) => m.get(k) as T | undefined,
    set: async (k, v) => void m.set(k, v),
    del: async (k) => void m.delete(k),
    keys: async () => [...m.keys()],
    clear: async () => m.clear(),
  };
}

export async function openStorage(): Promise<'ok' | 'unavailable'> {
  try {
    const store: UseStore = createStore('future-mockup-studio', 'kv');
    await set('__probe', 1, store);
    await del('__probe', store);
    backend = {
      get: <T,>(k: string) => get<T>(k, store),
      set: (k, v) => set(k, v, store),
      del: (k) => del(k, store),
      keys: async () => (await keys(store)).map(String),
      clear: () => clear(store),
    };
    persistent = true;
    return 'ok';
  } catch {
    backend = memoryBackend();
    persistent = false;
    return 'unavailable';
  }
}

function db(): Backend {
  if (!backend) backend = memoryBackend();
  return backend;
}

export const isPersistent = () => persistent;

let asked = false;
/** Ask the browser not to evict project data. Called after real work exists. */
export async function requestPersistence(): Promise<void> {
  if (asked || !persistent) return;
  asked = true;
  try {
    if (!(await navigator.storage?.persisted?.())) await navigator.storage?.persist?.();
  } catch {
    /* best effort */
  }
}
export const loadJSON = <T,>(key: string) => db().get<T>(key);
export const saveJSON = (key: string, value: unknown) => db().set(key, value);

export async function putBlob(id: string, blob: Blob): Promise<void> {
  await db().set(`blob:${id}`, blob);
}

export async function getBlob(id: string): Promise<Blob | undefined> {
  return db().get<Blob>(`blob:${id}`);
}

export async function deleteBlob(id: string): Promise<void> {
  await db().del(`blob:${id}`);
}

export async function clearAll(): Promise<void> {
  await db().clear();
}

export async function storageEstimate(): Promise<{ usage: number; quota: number } | null> {
  try {
    const e = await navigator.storage?.estimate?.();
    if (!e || e.usage === undefined || e.quota === undefined) return null;
    return { usage: e.usage, quota: e.quota };
  } catch {
    return null;
  }
}
