import { zipSync, strToU8 } from 'fflate';
import { cameraPosition, ORIGINAL } from '../domain/camera';
import { DEFAULT_MONOCHROME, findBackground, type SceneKind } from '../domain/catalogs';
import { createDraft, isActive, newId, planSlots, resolveTarget, retryableSlots, summarizeSlots, validateDraft } from '../domain/generation';
import { findModel } from '../domain/models';
import { composeBrief, PROMPT_VERSION } from '../domain/prompt';
import type { AssetMeta, Draft, Issue, JobRecord, JobSnapshot, QueuedIntent, Slot, Source, StudioTab } from '../domain/studio';
import { canvasToBlob } from '../engine/canvas';
import { hashString } from '../engine/color';
import { ERROR_TEXT } from '../components/labels';
import { planAngle } from '../domain/angles';
import { CLOUD_SIM, engineById, engineFor, HF_ANGLES, nextFrame, renderSlot, sleep, type Engine } from '../engine/engines';
import { LocalServerError, probeLocalServer } from '../engine/generative';
import { drawSampleProduct } from '../engine/standins';
import { clearAll, loadJSON, openStorage, requestPersistence } from '../storage/db';
import { safeName, saveFile, saveMode } from '../storage/download';
import { canvasAsset, normalizeUpload, toPng, UploadError } from '../storage/images';
import { addAsset, assetBlob, forgetAll, generatedSubject, subjectFor } from './assets';
import {
  currentEngine,
  DEFAULT_SETTINGS,
  flushPersist,
  getState,
  isOnline,
  newProject,
  setState,
  STATE_KEY,
  toast,
  updateDraft,
  updateJob,
  type Persisted,
} from './store';

const controllers = new Map<string, AbortController>();

export const SAMPLE_ID = 'sample-dropper-bottle';

// ---------------------------------------------------------------- startup

export async function init(): Promise<void> {
  const storage = await openStorage();
  void saveMode().then((m) => setState({ saveMode: m }));
  const saved = storage === 'ok' ? await loadJSON<Persisted>(STATE_KEY).catch(() => undefined) : undefined;

  if (saved && saved.project?.schemaVersion === 1) {
    setState({
      ...saved,
      settings: { ...DEFAULT_SETTINGS, ...saved.settings },
      jobs: saved.jobs.map(recoverInterrupted),
      storage,
      ready: true,
    });
  } else {
    setState({ storage });
    await seed();
    setState({ ready: true });
    await flushPersist();
  }
  void refreshLocal();
  window.addEventListener('online', () => setState({ browserOnline: true }));
  window.addEventListener('offline', () => setState({ browserOnline: false }));
}

/** Ask the local server whether the generative engine is ready. */
export async function refreshLocal(): Promise<void> {
  setState({ local: await probeLocalServer() });
}

/** A job interrupted by a reload: local work failed; cloud outcome is unknown. */
function recoverInterrupted(job: JobRecord): JobRecord {
  if (!isActive(job.state)) return job;
  const cloud = job.snapshot.execution === 'cloud';
  const slots = job.slots.map((s) =>
    s.state === 'queued' || s.state === 'running' || s.state === 'saving'
      ? { ...s, state: cloud ? ('unknown' as const) : ('failed' as const), errorCode: 'interrupted' }
      : s,
  );
  return { ...job, slots, state: summarizeSlots(slots) };
}

/** First open: a sample product and one example batch, so the tool shows its work. */
async function seed(): Promise<void> {
  await document.fonts?.load?.("96px 'Anton'").catch(() => undefined);
  const sample = await canvasAsset(drawSampleProduct(), {
    id: SAMPLE_ID,
    role: 'product',
    name: 'Sample dropper bottle',
    origin: 'sample',
    hasAlpha: true,
    saved: true,
  });
  await addAsset(sample.meta, sample.blob);
  const source: Source = { kind: 'upload', assetId: SAMPLE_ID };
  setState((s) => ({ drafts: { ...s.drafts, product: { ...createDraft('product'), source } } }));

  const exampleDraft: Draft & { source: Source } = {
    ...createDraft('product'),
    source,
    ratio: '3:4',
    backgroundId: 'minimalist-podium',
    prompt: 'Soft morning light and a gentle shadow.',
    count: 2,
  };
  const pair = buildJob(exampleDraft, engineFor('local'), sample.meta);
  // A second example shows the camera turning the product for real.
  const turnedDraft: Draft & { source: Source } = {
    ...createDraft('product'),
    source,
    ratio: '1:1',
    backgroundId: 'studio-white',
    camera: { kind: 'preset', name: 'three-quarter-right' },
    count: 1,
  };
  const turned = buildJob(turnedDraft, engineFor('local'), sample.meta);
  const examples = engineFor('local').caps.supportedCameraIntents.includes('three-quarter-right') ? [turned, pair] : [pair];
  examples.forEach((j) => (j.example = true));
  setState((s) => ({ jobs: [...examples, ...s.jobs] }));
  // Render in the background so the studio is usable straight away.
  for (const j of examples) void runJob(j.snapshot.id, j.slots.map((x) => x.index), { quiet: true });
}

// ---------------------------------------------------------------- sources

export async function uploadSource(tab: StudioTab, file: File): Promise<void> {
  try {
    const { meta, blob } = await normalizeUpload(file, tab === 'product' ? 'product' : 'person');
    await addAsset(meta, blob);
    setSource(tab, { kind: 'upload', assetId: meta.id });
    if (meta.lowResolution) toast('This image is under 512 px on its longest edge. Results may look soft.');
  } catch (e) {
    toast(e instanceof UploadError ? e.message : "This image couldn't be added. Try another file.", 'error');
  }
}

/** Replacing a source keeps ratio, background, prompt and count; the camera resets. */
export function setSource(tab: StudioTab, source: Source | null): void {
  updateDraft(tab, { source, camera: ORIGINAL });
}

export function acknowledgeRights(assetId: string, value: boolean): void {
  setState((s) => ({ assets: { ...s.assets, [assetId]: { ...s.assets[assetId], rightsAcknowledged: value } } }));
}

// ---------------------------------------------------------------- jobs

function sourceMeta(source: Source): AssetMeta | undefined {
  if (source.kind === 'catalog') {
    const m = findModel(source.modelId);
    return m ? { id: source.assetId, role: 'person', name: m.label, mime: 'image/png', width: 900, height: 1150, createdAt: '', origin: 'catalog' } : undefined;
  }
  return getState().assets[source.assetId];
}

export function issuesFor(tab: StudioTab): Issue[] {
  const s = getState();
  const draft = s.drafts[tab];
  const engine = currentEngine(s);
  const issues = validateDraft(draft, engine.caps, { sourceAsset: draft.source ? sourceMeta(draft.source) : undefined });
  // Offline, the job queues; readiness is checked again when it is sent.
  if (engine === HF_ANGLES && isOnline(s) && s.local.state !== 'ready') {
    issues.push({ field: 'engine', code: 'engine-unavailable', message: s.local.state === 'checking' ? 'Checking the local server.' : s.local.reason });
  }
  return issues;
}

function buildJob(draft: Draft & { source: Source }, engine: Engine, meta: AssetMeta | undefined, queuedIntentId?: string): JobRecord {
  const id = newId('job');
  const dims = meta ? { width: meta.width, height: meta.height } : { width: 1024, height: 1024 };
  const target = resolveTarget(draft.ratio, dims, engine.caps);
  const frozen: Draft & { source: Source } = JSON.parse(JSON.stringify(draft));
  const snapshot: JobSnapshot = {
    schemaVersion: 1,
    id,
    projectId: getState().project.id,
    createdAt: new Date().toISOString(),
    queuedIntentId,
    draft: frozen,
    execution: engine.execution,
    engine: { provider: engine.provider, model: engine.model, version: engine.version },
    promptVersion: PROMPT_VERSION,
    brief: composeBrief(frozen, target, meta?.name ?? ''),
    target: { width: target.width, height: target.height, framing: target.framing },
  };
  const base = hashString(id);
  const slots: Slot[] = planSlots(draft.count).map((s) => ({ ...s, seed: (base + s.index * 7919) >>> 0 }));
  return { snapshot, slots, state: 'queued' };
}

export async function generate(tab: StudioTab): Promise<void> {
  const s = getState();
  const draft = s.drafts[tab];
  if (issuesFor(tab).length || !draft.source) return;
  const engine = currentEngine(s);

  if (engine.execution === 'cloud' && !isOnline(s)) {
    queueForOnline(tab);
    return;
  }
  const job = buildJob(draft as Draft & { source: Source }, engine, sourceMeta(draft.source));
  setState((st) => ({ jobs: [job, ...st.jobs] }));
  await flushPersist();
  void runJob(job.snapshot.id, job.slots.map((x) => x.index));
}

function setSlot(jobId: string, index: number, patch: Partial<Slot>): void {
  updateJob(jobId, (j) => {
    const slots = j.slots.map((s) => (s.index === index ? { ...s, ...patch } : s));
    return { ...j, slots, state: summarizeSlots(slots) };
  });
}

function findJob(id: string): JobRecord | undefined {
  return getState().jobs.find((j) => j.snapshot.id === id);
}

/** Failures that will repeat for every remaining image in the batch. */
const FATAL = new Set(['quota', 'no-token', 'token-rejected', 'local-server', 'unreachable', 'space-unavailable']);

async function runJob(jobId: string, indexes: number[], opts: { quiet?: boolean } = {}): Promise<void> {
  const job = findJob(jobId);
  if (!job) return;
  const engine = engineById(job.snapshot.engine.provider);
  const controller = new AbortController();
  controllers.set(jobId, controller);
  const { signal } = controller;
  const simulated = engine === CLOUD_SIM;
  const generative = engine === HF_ANGLES;
  const failIndex = getState().settings.failOneSlot ? Math.min(2, job.slots.length - 1) : -1;
  let fatal: string | null = null;

  try {
    const sourceId = job.snapshot.draft.source.assetId;
    const subject = await subjectFor(sourceId);
    if (simulated) {
      setState((s) => ({ uploading: { ...s.uploading, [jobId]: true } }));
      await sleep(700, signal);
      setState((s) => ({ uploading: { ...s.uploading, [jobId]: false } }));
    }

    const queue = [...indexes];
    const worker = async () => {
      while (queue.length && !signal.aborted) {
        const index = queue.shift()!;
        const slot = findJob(jobId)?.slots.find((x) => x.index === index);
        if (!slot) continue;
        if (fatal) {
          setSlot(jobId, index, { state: 'failed', errorCode: fatal });
          continue;
        }
        try {
          if (simulated) await sleep(400 + Math.random() * 700, signal);
          setSlot(jobId, index, { state: 'running', errorCode: undefined, remoteId: simulated ? newId('remote') : undefined });
          await nextFrame();
          if (simulated) await sleep(1200 + Math.random() * 1400, signal);
          else if (!generative) await sleep(350, signal);
          if (index === failIndex && slot.attempt === 1) throw new Error('test-failure');

          const snap = findJob(jobId)!.snapshot;
          const pos = cameraPosition(snap.draft.camera);
          let placed = subject;
          let turn: { rotation: number; tilt: number } | undefined;
          if (generative) {
            // The model draws the nearest trained view; products are refined
            // the rest of the way in perspective, people snap to the view.
            const person = snap.draft.tab === 'model';
            const plan = planAngle(snap.draft.camera, { refine: !person });
            if (plan.view) placed = await generatedSubject(sourceId, subject, plan.view, slot.seed ?? index, person, signal);
            turn = plan.refine;
          }
          const canvas = renderSlot({
            tab: snap.draft.tab,
            scene: snap.draft.backgroundId as SceneKind,
            width: snap.target.width,
            height: snap.target.height,
            subject: placed.canvas,
            cutout: placed.cutout,
            camera: pos,
            turn,
            color: snap.draft.monochromeColor ?? DEFAULT_MONOCHROME,
            seed: slot.seed ?? index,
          });
          if (signal.aborted) throw new DOMException('Canceled', 'AbortError');
          setSlot(jobId, index, { state: 'saving' });
          await nextFrame();
          const blob = await canvasToBlob(canvas, 'image/jpeg', 0.92);
          const assetId = newId('result');
          await addAsset(
            {
              id: assetId,
              role: 'result',
              name: `${findBackground(snap.draft.tab, snap.draft.backgroundId).label} ${index + 1}`,
              mime: blob.type,
              width: canvas.width,
              height: canvas.height,
              createdAt: new Date().toISOString(),
              origin: 'generated',
            },
            blob,
          );
          setSlot(jobId, index, { state: 'succeeded', assetId });
        } catch (e) {
          if ((e as Error).name === 'AbortError') setSlot(jobId, index, { state: 'canceled' });
          else {
            const code = e instanceof LocalServerError ? e.code : (e as Error).message === 'test-failure' ? 'test-failure' : 'render-failed';
            if (e instanceof LocalServerError) console.warn('[generative]', e.code, e.message);
            if (FATAL.has(code)) fatal = code;
            setSlot(jobId, index, { state: 'failed', errorCode: code });
          }
        }
      }
    };
    await Promise.all(Array.from({ length: Math.min(engine.caps.maxParallel, indexes.length) }, worker));
    if (signal.aborted) cancelRemaining(jobId);
  } catch (e) {
    const code = (e as Error).message === 'source-missing' ? 'source-missing' : 'render-failed';
    if ((e as Error).name === 'AbortError') cancelRemaining(jobId);
    else
      updateJob(jobId, (j) => {
        const slots = j.slots.map((s) => (indexes.includes(s.index) && s.state !== 'succeeded' ? { ...s, state: 'failed' as const, errorCode: code } : s));
        return { ...j, slots, state: summarizeSlots(slots) };
      });
  } finally {
    controllers.delete(jobId);
    setState((s) => ({ uploading: { ...s.uploading, [jobId]: false } }));
  }
  if (fatal) void refreshLocal();

  const done = findJob(jobId);
  if (!done || opts.quiet) return;
  const ok = done.slots.filter((s) => s.state === 'succeeded').length;
  if (ok) void requestPersistence();
  if (done.state === 'succeeded') toast(ok === 1 ? 'Your image is ready.' : `${ok} images are ready.`);
  else if (done.state === 'partial') toast(`${ok} of ${done.slots.length} images are ready. One or more failed; you can retry them.`, 'error');
  else if (done.state === 'failed') toast(fatal ? ERROR_TEXT[fatal] ?? 'The images could not be generated.' : 'The images could not be generated. Retry, or check the job details.', 'error');
}

function cancelRemaining(jobId: string): void {
  updateJob(jobId, (j) => {
    const slots = j.slots.map((s) => (s.state === 'queued' || s.state === 'running' || s.state === 'saving' ? { ...s, state: 'canceled' as const } : s));
    return { ...j, slots, state: summarizeSlots(slots) };
  });
}

export function cancelJob(jobId: string): void {
  controllers.get(jobId)?.abort();
}

export function retryFailed(jobId: string, only?: number): void {
  const job = findJob(jobId);
  if (!job) return;
  const indexes = retryableSlots(job.slots).filter((i) => only === undefined || i === only);
  if (!indexes.length) return;
  updateJob(jobId, (j) => {
    const slots = j.slots.map((s) => (indexes.includes(s.index) ? { ...s, state: 'queued' as const, attempt: s.attempt + 1, errorCode: undefined } : s));
    return { ...j, slots, state: summarizeSlots(slots) };
  });
  void runJob(jobId, indexes);
}

/** Reconcile unknown cloud outcomes. The simulated provider keeps no records. */
export async function checkStatus(jobId: string): Promise<void> {
  await sleep(600);
  updateJob(jobId, (j) => {
    const slots = j.slots.map((s) => (s.state === 'unknown' ? { ...s, state: 'failed' as const, errorCode: 'not-found' } : s));
    return { ...j, slots, state: summarizeSlots(slots) };
  });
  toast('The provider has no record of those images. You can retry them now.');
}

export function removeJob(jobId: string): void {
  setState((s) => ({ jobs: s.jobs.filter((j) => j.snapshot.id !== jobId) }));
}

// ---------------------------------------------------------------- offline queue

export function queueForOnline(tab: StudioTab): void {
  const s = getState();
  const draft = s.drafts[tab];
  if (!draft.source) return;
  const intent: QueuedIntent = {
    schemaVersion: 1,
    id: newId('intent'),
    projectId: s.project.id,
    createdAt: new Date().toISOString(),
    draft: JSON.parse(JSON.stringify(draft)),
    requestedExecution: 'cloud',
  };
  setState((st) => ({ queue: [...st.queue, intent] }));
  toast('Queued. It waits until you are online and choose Review and send.');
}

export function sendQueued(intentId: string): void {
  const s = getState();
  const intent = s.queue.find((q) => q.id === intentId);
  if (!intent || !isOnline(s)) return;
  const engine = engineFor('cloud', s.settings.cloudProvider);
  if (engine === HF_ANGLES && s.local.state !== 'ready') {
    void refreshLocal();
    toast(s.local.state === 'checking' ? 'Checking the local server. Try again in a moment.' : s.local.reason, 'error');
    return;
  }
  const job = buildJob(intent.draft, engine, sourceMeta(intent.draft.source), intent.id);
  setState((st) => ({ queue: st.queue.filter((q) => q.id !== intentId), jobs: [job, ...st.jobs], tab: intent.draft.tab }));
  void runJob(job.snapshot.id, job.slots.map((x) => x.index));
}

export function deleteQueued(intentId: string): void {
  setState((s) => ({ queue: s.queue.filter((q) => q.id !== intentId) }));
}

// ---------------------------------------------------------------- files

function resultFilename(job: JobRecord, index: number, ext: string): string {
  const bg = findBackground(job.snapshot.draft.tab, job.snapshot.draft.backgroundId).label;
  return `${safeName(`${job.snapshot.draft.tab} ${bg} ${job.snapshot.draft.ratio.replace(':', 'x')}`)}-${index + 1}.${ext}`;
}

export async function downloadResult(job: JobRecord, index: number, format: 'jpg' | 'png' = 'jpg'): Promise<void> {
  const slot = job.slots.find((s) => s.index === index);
  if (!slot?.assetId) return;
  const blob = await assetBlob(slot.assetId);
  if (!blob) return toast('That image is no longer stored on this device.', 'error');
  const data = format === 'png' ? await toPng(blob) : blob;
  report(await saveFile(resultFilename(job, index, format), data));
}

export async function downloadAll(job: JobRecord): Promise<void> {
  const files: Record<string, Uint8Array> = {};
  for (const s of job.slots) {
    if (!s.assetId) continue;
    const b = await assetBlob(s.assetId);
    if (b) files[resultFilename(job, s.index, 'jpg')] = new Uint8Array(await b.arrayBuffer());
  }
  const zip = zipSync(files, { level: 0 });
  const name = `${safeName(getState().project.name)}-${job.snapshot.draft.tab}-batch.zip`;
  report(await saveFile(name, new Blob([zip as BlobPart], { type: 'application/zip' })));
}

export async function exportProject(): Promise<void> {
  const s = getState();
  const files: Record<string, Uint8Array> = {};
  const used = new Set<string>();
  for (const id of Object.keys(s.assets)) {
    const b = await assetBlob(id);
    if (!b) continue;
    const ext = b.type === 'image/png' ? 'png' : 'jpg';
    const path = `assets/${id}.${ext}`;
    files[path] = new Uint8Array(await b.arrayBuffer());
    used.add(id);
  }
  const manifest = {
    format: 'future-mockup-studio-project',
    schemaVersion: 1,
    exportedAt: new Date().toISOString(),
    project: s.project,
    drafts: s.drafts,
    assets: Object.values(s.assets).filter((a) => used.has(a.id)),
    jobs: s.jobs,
    queue: s.queue,
  };
  files['project.json'] = strToU8(JSON.stringify(manifest, null, 2));
  const zip = zipSync(files, { level: 0 });
  report(await saveFile(`${safeName(s.project.name)}.zip`, new Blob([zip as BlobPart], { type: 'application/zip' })));
}

function report(r: Awaited<ReturnType<typeof saveFile>>): void {
  if (r === 'unavailable') toast("Saving files isn't available in this view.", 'error');
  else if (r === 'failed') toast('The file could not be saved. Try again.', 'error');
}

export async function resetProject(): Promise<void> {
  controllers.forEach((c) => c.abort());
  await clearAll();
  forgetAll();
  setState({
    project: newProject(),
    tab: 'product',
    drafts: { product: createDraft('product'), model: createDraft('model') },
    assets: {},
    jobs: [],
    queue: [],
    settings: getState().settings,
    ready: false,
  });
  await seed();
  setState({ ready: true });
  await flushPersist();
  toast('Project data deleted. A fresh project is ready.');
}

export function setMonochrome(tab: StudioTab, hex: string): void {
  updateDraft(tab, { monochromeColor: hex });
}
