# Future Mockup Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the two-tab image studio specified in the PRD, including cloud generation, offline preparation/queuing, and qualified local offline generation.

**Architecture:** One shared web composer creates immutable job requests. Local project storage supports offline work; an authenticated server runs cloud jobs, while a paired companion runs installed models locally. Both execution paths return the same result records and never change execution location without user action.

**Tech Stack:** Proposed React, TypeScript, Vite, IndexedDB, a service worker, Node/TypeScript cloud API with durable SQL job records and private object storage, and a Python local companion with a qualified image runtime. Vitest and Playwright cover behavior; pytest covers the companion. Pin actual dependency versions at kickoff rather than treating this plan as a package lockfile.

**Spec:** [Future Mockup Studio PRD](../specs/2026-09-29-future-mockup-studio-design.md). Read the PRD and this plan together.

## Global constraints

- Build a simple image studio with exactly two primary tabs: **Product** and **Model**.
- Count is total requested outputs, never angles multiplied by variations.
- Auto, 1:1, 3:2, 2:3, 4:3, 3:4, 9:16, 16:9, 21:9 appear on both tabs.
- All requested capabilities belong in the completed v1. An earlier cloud pilot is an intermediate milestone, not a substitute for offline generation.
- No automatic cloud fallback for a local job; changing where an image is sent is an explicit user action.
- The prompt is optional, multiline, limited to 2,000 characters, and labeled **Describe your image**.
- Never stretch the subject.
- No invisible subject cropping.
- No release claim of “works offline” until the airplane-mode generation test passes.

This is a proposed implementation sequence, not evidence that code or tests already exist. All application paths below are files to create in this currently empty workspace. The snippets define shared contracts and representative acceptance tests; complete feature implementation follows the PRD. Do not scaffold or deploy from the mere existence of this document.

## Milestones, ownership, and dependencies

| Milestone | Tasks | Evidence | Indicative effort |
|---|---|---|---|
| M0: feasibility | 1 | Engine and hardware report; view/ratio feasibility; selected browser-to-companion transport | 3–5 working days |
| M1: cloud pilot | 2–8 | Complete two-tab experience, real cloud results, offline drafts and queue | 10–15 working days |
| M2: offline v1 | 9–10 | Installed engine generates offline; same job semantics | 7–12 working days |
| M3: release | 11 | Recovery, usability, accessibility, quality, and operations evidence | 3–5 working days |

Planning allowance: roughly 5–8 calendar weeks with two experienced full-stack engineers and part-time image/ML, design, and QA support. This is an estimate, not a delivery commitment; M0 replaces it with measured work, provider access, and device constraints. One engineer or additional operating systems extends the schedule.

**Dependency order:** 1 → 2 → 3; then 4 and 5 can proceed independently. Task 6 depends on 2 and the M0 engine choice. Task 7 joins 3–6. Task 8 adds durable offline handling to 7. Task 9 may run alongside 4–8 after M0; 10 joins 8 and 9; 11 verifies the complete product. Cloud API owner and companion owner share one contract fixture rather than independently defining requests.

## Proposed file responsibilities

| Path | Responsibility |
|---|---|
| `src/domain/studio.ts` | Draft, source, camera, count, ratio, and immutable job contracts |
| `src/domain/catalogs.ts` | Backgrounds, ratio ordering, age/tone filter definitions |
| `src/domain/generation.ts` | Validation, snapshotting, slot planning, state transitions |
| `src/features/studio/StudioPage.tsx` | Shared composer and results layout; tab selection |
| `src/features/studio/SourcePicker.tsx` | Upload, saved products, model source mode |
| `src/features/studio/ModelPicker.tsx` | Catalog filtering and stable model selection |
| `src/features/studio/CompositionControls.tsx` | Ratio, background, prompt, count |
| `src/features/studio/AngleSheet.tsx` | Camera presets, orbit guide, numeric inputs |
| `src/features/results/ResultGrid.tsx` | Per-slot status, preview, retry, and export actions |
| `src/features/settings/EngineSettings.tsx` | Cloud/local configuration, setup status, storage |
| `src/storage/project-store.ts` | Transactional IndexedDB persistence and migrations |
| `src/storage/project-archive.ts` | Portable export/import with asset checksums |
| `src/engines/contracts.ts` | Shared capability, job status, and output types |
| `src/engines/cloud-client.ts` | Authenticated cloud API access and reconnect reconciliation |
| `src/engines/local-client.ts` | Paired loopback companion transport |
| `src/offline/queue.ts` | Immutable waiting jobs, review-before-send, queue edits |
| `src/offline/service-worker.ts` | App shell and catalog caching, safe app updates |
| `server/jobs.ts` | Durable cloud job creation, idempotency, lookup, cancellation |
| `server/cloud-provider.ts` | One qualified provider's request/status/result mapping |
| `server/prompt-composer.ts` | Versioned generation brief and preservation constraints |
| `shared/prompt-templates.json` | Versioned deterministic instructions available to cloud and local execution |
| `shared/prompt-fixtures.json` | Golden briefs proving cloud/local composition parity |
| `server/assets.ts` | Authorized private upload/download and retention cleanup |
| `server/auth.ts` | Workspace sessions, ownership checks, limits |
| `server/schema.sql` | Jobs, child attempts, asset ownership, retention records |
| `shared/job.schema.json` | JSON wire schema consumed by server and companion |
| `companion/app.py` | Loopback API, pairing, request validation, job status |
| `companion/runtime.py` | Installed-model inference and resource checks |
| `companion/prompt_composer.py` | Offline brief construction using the same packaged templates |
| `companion/storage.py` | Durable local jobs and output files across restarts |
| `companion/safety.py` | Local input/output checks, including under-18 handling |
| `companion/install.py` | Download manifest, checksums, license and setup self-test |
| `evals/` | Reference set, benchmark runner, scored outputs, and reports |
| `tests/` | Domain, API contract, browser journey, and fault-injection tests |

Use these boundaries, not an elaborate plugin framework. A cloud adapter and a local adapter are justified by two explicitly required execution modes. Keep one server deployment and one companion process initially.

## Shared design contracts

Task 2 establishes the following names so later tasks cannot drift. A string ID always refers to a workspace-owned record, not an arbitrary URL or filesystem path. `Readonly` alone is insufficient: freeze by cloning and persisting a snapshot.

```ts
export type StudioTab = 'product' | 'model';
export type OutputCount = 1 | 2 | 4;
export type Ratio = 'auto' | '1:1' | '3:2' | '2:3' | '4:3'
  | '3:4' | '9:16' | '16:9' | '21:9';
export type CameraPreset = 'original' | 'front' | 'three-quarter-left'
  | 'three-quarter-right' | 'left-profile' | 'right-profile' | 'top-down';
export type CameraIntent =
  | { kind: 'preset'; name: CameraPreset }
  | { kind: 'relative'; rotation: number; tilt: number; zoom: number };
export type Source =
  | { kind: 'upload'; assetId: string }
  | { kind: 'catalog'; modelId: string; assetId: string };
export type Draft = {
  tab: StudioTab; source: Source | null; ratio: Ratio;
  backgroundId: string; monochromeColor?: string;
  camera: CameraIntent; prompt: string; count: OutputCount;
};
export type JobSnapshot = {
  schemaVersion: 1; id: string; projectId: string; createdAt: string;
  queuedIntentId?: string;
  draft: Draft & { source: Source };
  execution: 'cloud' | 'local';
  engine: { provider: string; model: string; version: string };
  promptVersion: string;
  target: { width: number; height: number; framing: 'native' | 'extend' | 'fit' };
};
export type QueuedIntent = {
  schemaVersion: 1; id: string; projectId: string; createdAt: string;
  draft: Draft & { source: Source }; requestedExecution: 'cloud';
};
export type SlotState = 'queued' | 'running' | 'saving' | 'succeeded'
  | 'failed' | 'canceled' | 'unknown';
export type Slot = {
  index: number; attempt: number; state: SlotState;
  remoteId?: string; assetId?: string; errorCode?: string;
};
export type JobRecord = {
  snapshot: JobSnapshot; slots: Slot[];
  state: 'awaiting-review' | 'queued' | 'running' | 'saving'
    | 'succeeded' | 'partial' | 'failed' | 'canceled' | 'unknown';
};
export type Issue = { field: string; code: string; message: string };
export type Dimensions = { width: number; height: number };
export type Capabilities = {
  referenceEdit: boolean; offline: boolean; cancel: boolean;
  maxParallel: number; camera: 'validated-view-control' | 'qualified-prompt';
  supportedCameraIntents: string[]; supportedRatios: Ratio[];
};
```

**Domain interfaces:**

```ts
createDraft(tab: StudioTab): Draft
validateDraft(draft: Draft, caps: Capabilities): Issue[]
resolveTarget(ratio: Ratio, source: Dimensions, caps: Capabilities):
  { width: number; height: number; framing: 'native' | 'extend' | 'fit' }
planSlots(count: OutputCount): Slot[]
retryableSlots(slots: Slot[]): number[]
summarizeSlots(slots: Slot[]): JobRecord['state']
```

`resolveTarget` also consults the selected adapter's versioned dimension/framing rules; `supportedRatios` describes the final export capability, not just native generation. A supported capability is confirmed by tests and qualification, not inferred from a model name.

**HTTP contract, cloud and local:**

- `GET /v1/capabilities` → engine identity, Capabilities, readiness reason, resource/cost metadata.
- `POST /v1/assets` → accepts a validated file under the session; returns scoped `assetId` and normalized dimensions.
- `POST /v1/jobs` → `{ snapshot, attemptSlots: number[] }`; requires `Idempotency-Key`; returns `202 { jobId }` or an existing job response for an identical replay.
- `GET /v1/jobs/:id` → `JobRecord` with result asset references; enforce project ownership.
- `POST /v1/jobs/:id/retry` → `{ slotIndexes: number[] }`; reject successful/running/unknown slots and create numbered attempts only for failed slots.
- `POST /v1/jobs/:id/cancel` → latest job record; best-effort cancellation status is explicit.
- `GET /v1/assets/:id` → authenticated image bytes or a short-lived private download URL.

For cloud, map local asset IDs to uploaded remote IDs in the adapter transport; preserve original IDs in the saved snapshot. For local, stream bytes to the paired companion rather than asking it to open user-supplied filesystem paths. Use JSON Schema to validate both implementations. Model safety, limits, and unsupported capabilities yield stable error codes before submission where possible.

## Task 1 — Qualify the engines and offline transport

**Requirement coverage:** R08, R11, R13, R14.  
**Owner:** image/ML engineer with client engineer.  
**Create:** `evals/cases.json`, `evals/run.py`, `evals/report.md`, `docs/decisions/engine-and-device.md`, `docs/decisions/local-transport.md`.  
**Consumes:** PRD quality rubric and research sources.  
**Produces:** qualified engine/version manifest, supported device statement, measured limits, and a selected companion transport.

- [ ] Define at least 20 product and 20 model references with explicit usage rights and the PRD's coverage. Separate original-view background changes from new-view cases. Include packaging text, reflective/transparent products, all model age groups, and skin-tone coverage.
- [ ] Validate current cloud access, pricing, and exact image API parameters. Start with Sunburst; compare another candidate only if a concrete cost, speed, or quality gap requires it. Do not treat the Codex imagegen tool as an app API.
- [ ] Run the same meaningful subset on the candidate local editing checkpoint; record model checksum, runtime versions, hardware/OS, peak memory, install size, latency, and output scores. Benchmark a named device before setting a minimum requirement.
- [ ] Verify all eight fixed ratios and Auto framing; measure viewpoint accuracy independently of visual attractiveness. Reject a candidate that silently ignores a requested viewpoint.
- [ ] Prove the hosted HTTPS app can pair with the loopback companion on the intended browsers, including local-network permissions, origin checks, CORS, and mixed-content constraints. Test offline reopen of the installed shell. If that transport is blocked, choose and document a small desktop wrapper using the same UI before committing to the public-browser route; do not weaken local authentication.
- [ ] Deliver a pass/fail report with representative outputs, known limits, and a recommended first device class. If an engine fails, rerun the failing cases on a replacement before moving its feature to done.

**Evidence schema example:**

```json
{
  "caseId": "product-label-three-quarter",
  "referenceId": "licensed-product-01",
  "tab": "product",
  "camera": { "kind": "preset", "name": "three-quarter-left" },
  "ratio": "3:4",
  "checks": ["same-product", "legible-label", "requested-view", "no-defects"]
}
```

**Verification:** run `python evals/run.py --manifest evals/cases.json --report evals/report.md` after the runner is implemented. Every reported score links to an actual case/output; quality thresholds and hardware results come from observed evidence. Commercial cloud runs need configured account access and an explicit experiment spend ceiling before execution.

## Task 2 — Establish contracts, catalogs, and domain validation

**Requirement coverage:** R01, R04–R10, R14.  
**Owner:** client engineer.  
**Create:** `package.json`, `tsconfig.json`, `vite.config.ts`, `vitest.config.ts`, `src/domain/studio.ts`, `src/domain/catalogs.ts`, `src/domain/generation.ts`, `src/engines/contracts.ts`, `shared/job.schema.json`, `tests/domain/generation.test.ts`.  
**Consumes:** M0 capability manifest.  
**Produces:** the shared contracts and six domain interfaces listed above; JSON fixtures valid in TypeScript and Python.

- [ ] Pin dependencies and establish `npm run typecheck`, `npm run test`, `npm run test:e2e`, and `npm run build`. Add JSON schema validation with strict numeric count values; reject 3 and 12.
- [ ] Add all nine ratios, both exact background catalogs, the documented age groups, 10 tone choices, and stable catalog IDs. Store descriptions separately from labels.
- [ ] Write failing tests for unsupported source/tab combinations, missing source, prompt length, angle boundaries, and total output counts.
- [ ] Implement deterministic defaults, validation, native/export size resolution, and per-slot planning. Do not let a queued job read mutable draft objects.
- [ ] Run the domain suite and typecheck; review the small diff and commit the coherent contract/catalog change after repository setup is authorized.

**Representative test:**

```ts
import { expect, test } from 'vitest';
import { planSlots, retryableSlots } from '../../src/domain/generation';

test('four outputs produce four slots and retry only the failed slot', () => {
  const slots = planSlots(4);
  expect(slots.map(s => s.index)).toEqual([0, 1, 2, 3]);
  slots.forEach(s => { s.state = 'succeeded'; });
  slots[2].state = 'failed';
  expect(retryableSlots(slots)).toEqual([2]);
  slots[2].state = 'unknown';
  expect(retryableSlots(slots)).toEqual([]);
});
```

**Run:** `npm run test -- tests/domain/generation.test.ts` → failing behavior before implementation, then pass. The tests must fail for an actual behavioral gap, not only a missing import.

## Task 3 — Build the shared composer with durable drafts

**Requirement coverage:** R01, R02, R03, R15.  
**Owner:** client engineer with designer.  
**Create:** `src/main.tsx`, `src/features/studio/StudioPage.tsx`, `src/features/studio/SourcePicker.tsx`, `src/storage/project-store.ts`, `src/styles.css`, `tests/e2e/drafts.spec.ts`, `tests/storage/project-store.test.ts`.  
**Consumes:** `Draft`, `StudioTab`, `createDraft`.  
**Produces:** `ProjectStore.load(id): Promise<Project>` and `ProjectStore.save(project): Promise<void>`; `Project` contains ID, name, schema version, timestamps, `drafts: Record<StudioTab, Draft>`, asset IDs, and job IDs.

- [ ] Implement the PRD wireframe with two tabs, one composer, a results area, and simple project/settings controls. No extra creative-mode tabs.
- [ ] Save separate drafts transactionally after edits and before submission. Show unsaved/error status if storage fails rather than pretending autosave succeeded.
- [ ] Validate and normalize uploads; enforce decoded dimensions and file-size limits. Save local bytes before creating an Asset record. Add the saved-product picker, replace/remove actions, metadata stripping, and reference counting for safe deletion.
- [ ] Verify source replacement preserves settings but resets relative camera intent and resolves Auto for the new source. Switching tabs preserves both drafts without canceling running work.
- [ ] Exercise reload, denied storage, corrupt upload, large decoded image, transparent PNG, and narrow-screen layout. Use manual visual review for spacing rather than snapshot tests of CSS implementation.

**Browser test excerpt:**

```ts
await page.getByRole('tab', { name: 'Product', exact: true }).click();
await page.getByLabel('Describe your image').fill('Soft morning light');
await page.getByRole('tab', { name: 'Model', exact: true }).click();
await page.getByLabel('Describe your image').fill('Warm cafe portrait');
await page.reload();
await expect(page.getByLabel('Describe your image')).toHaveValue('Warm cafe portrait');
await page.getByRole('tab', { name: 'Product', exact: true }).click();
await expect(page.getByLabel('Describe your image')).toHaveValue('Soft morning light');
```

**Run:** `npm run test:e2e -- tests/e2e/drafts.spec.ts`. Pass requires real IndexedDB persistence after reload, not component memory.

## Task 4 — Complete model selection and composition controls

**Requirement coverage:** R03–R07, R09, R10.  
**Owner:** client engineer with catalog/content owner.  
**Create:** `src/features/studio/ModelPicker.tsx`, `src/features/studio/CompositionControls.tsx`, `src/catalog/models.json`, `src/catalog/backgrounds.json`, `tests/e2e/composition.spec.ts`, `tests/domain/catalogs.test.ts`.  
**Consumes:** domain catalogs and `Draft`.  
**Produces:** selected `Source`, background ID/color, `Ratio`, prompt, and `OutputCount` updates; no generation side effects.

- [ ] Populate a licensed/synthetic catalog with stable IDs, reference assets, licenses, offline availability, skin-tone metadata, gender presentation, and age group. Verify every individual filter option has results; document empty intersections.
- [ ] Implement Upload image / Select model, combined filters, selected-card state, Clear filters, and uncached-offline states. Do not apply inferred demographic filters to uploaded photos.
- [ ] Implement the exact ratio grid and tab-specific background pickers. Retain both outdoor categories with their distinct descriptions. Add optional monochrome color within that picker.
- [ ] Implement optional 2,000-character prompt and 1/2/4 segmented control; Generate label reflects the selected count. Empty prompt is valid; missing source is not.
- [ ] Verify filter combinations, no results, keyboard selection, and preservation of a model identity across later drafts. Verify the exact option sets so a requested background cannot disappear during copy changes.

**Catalog contract excerpt:**

```ts
export type AgeGroup = 'kid' | 'teen' | 'young-adult' | 'middle-aged' | 'older-adult';
export type ModelPreset = {
  id: string; label: string; assetId: string;
  tone: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;
  presentation: 'female' | 'male'; ageGroup: AgeGroup;
  rights: { source: string; license: string }; cached: boolean;
};
```

**Acceptance test excerpt:**

```ts
await page.getByRole('tab', { name: 'Model', exact: true }).click();
await page.getByRole('button', { name: 'Select model', exact: true }).click();
await page.getByLabel('Age group').selectOption('teen');
await page.getByLabel('Gender presentation').selectOption('female');
await expect(page.getByRole('dialog', { name: 'Select model' })).toBeVisible();
// The rights-cleared test catalog has one matching card with this accessible name.
await page.getByRole('button', { name: 'Select model Maya' }).click();
await page.getByRole('radio', { name: '4 results', exact: true }).check();
await expect(page.getByRole('button', { name: 'Generate 4 images' })).toBeEnabled();
```

**Run:** `npm run test:e2e -- tests/e2e/composition.spec.ts` and `npm run test -- tests/domain/catalogs.test.ts`. Test-catalog fixtures are synthetic records, clearly labeled as such; production assets require actual rights metadata.

## Task 5 — Build camera intent controls

**Requirement coverage:** R08, R10, R15.  
**Owner:** client engineer with designer.  
**Create:** `src/features/studio/AngleSheet.tsx`, `src/domain/camera.ts`, `tests/domain/camera.test.ts`, `tests/e2e/angles.spec.ts`.  
**Consumes:** `CameraIntent`, qualified engine capability list.  
**Produces:** `normalizeCamera(intent: CameraIntent): CameraIntent` plus draft camera updates only when Apply is selected.

- [ ] Add the seven semantic presets and source-relative drag/numeric control. Keep semantic presets distinct from numeric offsets so Front does not incorrectly mean zero source-relative rotation.
- [ ] Implement the PRD ranges and clamping, arrow-key/number-input equivalents, Reset, Apply, Cancel, focus management, and escape-to-close.
- [ ] Render the guide from camera settings without sending a generation request. Label it as a guide; do not depict a reconstructed product as if it were available geometry.
- [ ] Show selected intent on the composer. Include the short fidelity note for substantial view changes and an availability reason for unsupported engine controls.
- [ ] Verify drag, keyboard, cancel/reopen, reset, and unchanged result count. Review at 390 px and with reduced motion enabled.

**Representative test:**

```ts
expect(normalizeCamera({
  kind: 'relative', rotation: 240, tilt: -120, zoom: 80
})).toEqual({ kind: 'relative', rotation: 180, tilt: -90, zoom: 50 });
expect(normalizeCamera({ kind: 'preset', name: 'front' }))
  .toEqual({ kind: 'preset', name: 'front' });
```

**Run:** `npm run test -- tests/domain/camera.test.ts` and `npm run test:e2e -- tests/e2e/angles.spec.ts`. Browser network assertions must show zero job submissions while dragging/applying camera settings.

## Task 6 — Implement one authenticated cloud generation adapter

**Requirement coverage:** R08–R11, R14.  
**Owner:** server engineer.  
**Create:** `server/jobs.ts`, `server/cloud-provider.ts`, `server/prompt-composer.ts`, `shared/prompt-templates.json`, `shared/prompt-fixtures.json`, `server/assets.ts`, `server/auth.ts`, `server/schema.sql`, `src/engines/cloud-client.ts`, `tests/api/jobs.test.ts`, `tests/api/prompt.test.ts`, `tests/api/ownership.test.ts`.  
**Consumes:** `JobSnapshot`, JSON Schema, M0 model/version and capability manifest.  
**Produces:** the HTTP contract above and durable per-slot attempt/result records.

- [ ] Create a minimal durable SQL store with unique constraints on workspace/request key and job/slot/attempt. Store the snapshot before requesting inference. Reject reuse of one key with different content using HTTP 409.
- [ ] Implement workspace authentication, project ownership checks, upload validation, rate/spend limits, and private result storage. Keep provider secrets server-side; redact photos, raw prompts, and credentials from routine logs.
- [ ] Compose a versioned brief from image roles, tab-specific preservation rules, background, ratio, camera, and user text using packaged `shared/prompt-templates.json`. Selected controls prevail; return conflict details so the UI can explain conflicting free text. Store golden input/output fixtures for the offline composer; neither path needs an extra LLM call to construct the brief.
- [ ] Implement capability preflight, total estimate, provider submission, polling/callback normalization, cancellation semantics, and retry eligibility. Use one child request per slot if necessary; a provider-native batch must still map to N stable slots.
- [ ] Add timeout reconciliation: accepted remote work retains its remote ID. For providers without idempotency or status recovery, mark an ambiguous submission unknown and require reconciliation/manual resolution; never automatically resubmit an uncertain paid request.
- [ ] Run fixture-based tests first, then a small real benchmark within the configured experiment budget. Compare actual exports with requested ratios and record exact model version.

**Idempotency test excerpt:**

```ts
const request = { snapshot, attemptSlots: [0, 1, 2, 3] };
const headers = { 'Idempotency-Key': snapshot.id, Authorization: sessionToken };
const first = await api.post('/v1/jobs', request, headers);
const replay = await api.post('/v1/jobs', request, headers);
expect(first.status).toBe(202);
expect(replay.body.jobId).toBe(first.body.jobId);
expect(provider.submittedSlots).toEqual([0, 1, 2, 3]);
```

`api` is the in-process HTTP test client, `provider` is the deterministic recording test adapter, and `snapshot`/`sessionToken` are a valid owned request/session fixture created in `tests/api/jobs.test.ts`. Add a cross-workspace access fixture and expect 403/404, not another user's job or assets.

**Run:** `npm run test -- tests/api`. Pass requires both replay safety and ownership isolation. A successful HTTP response alone does not prove image quality; M0/release evaluation covers that separately.

## Task 7 — Connect generation, partial results, history, and exports

**Requirement coverage:** R01, R05, R10, R11, R15.  
**Owner:** client engineer.  
**Create:** `src/features/results/ResultGrid.tsx`, `src/features/results/ResultDetails.tsx`, `src/features/studio/use-generation.ts`, `src/storage/project-archive.ts`, `tests/e2e/generation.spec.ts`, `tests/storage/project-archive.test.ts`.  
**Consumes:** cloud job API, `ProjectStore`, `JobRecord`, `summarizeSlots`, `retryableSlots`.  
**Produces:** saved output assets, history, accessible result actions, project export/import.

- [ ] Preflight and freeze a snapshot before submission; display count, execution location, estimate, and framing method. Disable duplicate submissions for the pending request, without locking next-draft editing.
- [ ] Render factual provider states; distinguish provider success from saving the result locally. Saving failures retry download/persistence, not inference.
- [ ] Preserve successes in a partial batch, expose retry for failed slots only, and show best-effort cancel. Keep jobs tied to project and tab when the user changes views.
- [ ] Add full-size preview, individual PNG/JPEG download, batch Download all, and job details. Record native/exported dimensions and model/prompt versions; never stretch or silently crop.
- [ ] Implement portable archive export/import with checksums, version, sources, drafts, history, and outputs; exclude tokens and remote credentials. Reject malformed archives and path traversal. Confirm before deleting a project and remove only unshared assets.
- [ ] Verify partial failure, expired result URL, storage quota, interrupted saving, cross-tab navigation, export dimensions, and archive round-trip.

**Browser test excerpt:**

```ts
// Deterministic server fixture: slots 0, 1, 3 succeed; slot 2 fails.
await page.getByRole('button', { name: 'Generate 4 images' }).click();
await expect(page.getByRole('button', { name: 'Download image', exact: true }))
  .toHaveCount(3);
await page.getByRole('button', { name: 'Retry failed image', exact: true }).click();
await expect(page.getByRole('button', { name: 'Download image', exact: true }))
  .toHaveCount(4);
// Assert recorded retry request has slotIndexes: [2]; no second batch submission.
```

**Run:** `npm run test:e2e -- tests/e2e/generation.spec.ts` and `npm run test -- tests/storage/project-archive.test.ts`. Open exported files and verify dimensions, successful decoding, and archive round-trip metadata.

## Task 8 — Add installed offline workspace and cloud queue

**Requirement coverage:** R01, R12, R15.  
**Owner:** client engineer.  
**Create:** `src/offline/service-worker.ts`, `src/offline/queue.ts`, `public/manifest.webmanifest`, `tests/e2e/offline-queue.spec.ts`, `tests/offline/queue.test.ts`.  
**Consumes:** `QueuedIntent`, local assets, cloud reconciliation API, archive persistence.  
**Produces:** `enqueue(intent: QueuedIntent): Promise<void>`, `listPending(): Promise<QueuedIntent[]>`, `removePending(id: string): Promise<void>`, and explicit review-before-send UI.

- [ ] Cache the versioned app shell, default background thumbnails, and installed model-catalog assets. Apply service-worker updates only at a safe point after drafts are persisted; migrate local schemas transactionally.
- [ ] Separate browser connectivity from actual API availability. On offline/cloud-unreachable submission, offer Queue for online and persist a `QueuedIntent` plus source references. No cloud configuration, model version, or resolved output size is required to save the intent.
- [ ] On reconnect, fetch capabilities and estimate, resolve dimensions/framing, and build a new executable `JobSnapshot` linked by `queuedIntentId`. Show Review and send with any unavailable controls or changed cost. Preserve the original queued intent; do not silently change its creative choices. Editing a queued request creates a new intent/version; delete affects unsubmitted work only.
- [ ] On restart, restore queue state; reconcile submitted jobs before any retry. Browser background scheduling is best effort, so queued work resumes when the app is opened and the user sends it.
- [ ] Exercise airplane-mode editing/upload, reload, queue persistence, reconnect, and storage eviction recovery via project export. Preserve available local results even if the cloud is unavailable.

**Browser test excerpt:**

```ts
await context.setOffline(true);
await page.getByRole('button', { name: 'Queue for online' }).click();
await page.reload();
await expect(page.getByText('1 job waiting for connection')).toBeVisible();
await context.setOffline(false);
await expect(page.getByRole('button', { name: 'Review and send' })).toBeVisible();
expect(recordedCloudSubmissions).toHaveLength(0);
```

`recordedCloudSubmissions` is an array populated by Playwright request interception in this test. After clicking Review and send and accepting the displayed total, assert exactly one matching request. Changing the estimate requires presenting the revised total before submission.

**Run:** `npm run test:e2e -- tests/e2e/offline-queue.spec.ts`. This proves offline preparation; it does not satisfy the local image-generation milestone.

## Task 9 — Build and package the local generation companion

**Requirement coverage:** R08, R13, R14.  
**Owner:** image/ML engineer with server engineer.  
**Create:** `companion/pyproject.toml`, `companion/app.py`, `companion/runtime.py`, `companion/prompt_composer.py`, `companion/storage.py`, `companion/safety.py`, `companion/install.py`, `companion/model-manifest.json`, `companion/tests/test_contract.py`, `companion/tests/test_offline.py`, `companion/tests/test_prompt_parity.py`.  
**Consumes:** M0 engine/transport decisions, JSON Schema, shared prompt templates/fixtures, licensed offline catalog.  
**Produces:** paired loopback service implementing the same job API, persistent local results, verified installer, readiness/capability report.

- [ ] Package the exact qualified checkpoint, runtime dependencies, local safety components, and prompt/catalog assets. Record all licenses and checksums. Show measured download size, required free disk, and the hardware configuration actually supported.
- [ ] Implement authenticated pairing and origin restrictions under the M0 transport decision. Bind only to loopback; reject unpaired callers, unapproved origins, arbitrary file paths, and oversized requests. Do not disable security to bypass browser transport restrictions.
- [ ] Parse the shared schema in Python and build prompts from the packaged templates. Compare output with the same golden fixtures used by the server. The local composer must not call an online LLM or configuration service.
- [ ] Add one-at-a-time inference with readiness checks, resource preflight, cancellation checkpoints, durable per-slot progress, and local file storage. On memory exhaustion, fail that slot with a recoverable error; keep successful results and the source.
- [ ] Use cached-only model loading, Hub offline mode, and a network-denied test. Disable analytics and automatic update checks while local-only jobs run. Package the input/output safeguards needed for the supported catalog, including child/teen cases.
- [ ] Create the installer/setup self-test, progress/cancel behavior, and cleanup of incomplete downloads. Reuse a verified installation on restart; never redownload weights when the device is offline.

**Offline test contract:**

```python
def test_generate_with_network_denied(offline_worker, local_snapshot):
    # Fixture denies external socket connections and contains cached model files.
    job = offline_worker.submit(local_snapshot)
    result = offline_worker.wait(job.id)
    assert result.slots[0].state == "succeeded"
    assert result.slots[0].output_path.is_file()
    assert offline_worker.external_connection_attempts == []
```

**Run:** `python -m pytest companion/tests/test_contract.py companion/tests/test_prompt_parity.py` for fast contract checks, then `python -m pytest companion/tests/test_offline.py` on the named qualified device. The second test must run real inference with installed weights; a stub cannot pass the offline-generation gate.

## Task 10 — Integrate engine setup and complete offline journeys

**Requirement coverage:** R03, R11–R15.  
**Owner:** client engineer with companion owner.  
**Create:** `src/engines/local-client.ts`, `src/features/settings/EngineSettings.tsx`, `src/features/settings/StorageSettings.tsx`, `tests/e2e/local-generation.spec.ts`, `tests/e2e/engine-routing.spec.ts`, `docs/local-setup.md`.  
**Consumes:** both engine API contracts, queue, local asset store, companion readiness.  
**Produces:** reliable Cloud / On this device choice, offline asset installation, device setup and recovery.

- [ ] Add Settings for cloud configuration, local pairing/setup, model/catalog packs, storage, and export/import. Keep the main workspace to a concise execution-status indicator.
- [ ] Show the exact execution location and capability failures before submission. Changing preference affects only new jobs; existing jobs keep their immutable engine/version. An unavailable local engine never triggers cloud upload.
- [ ] Stream local reference bytes to the paired companion, preserve original local IDs in the project, and persist returned assets. If a pairing expires, pause transport and allow re-pairing without losing inputs.
- [ ] Cache selected model assets and background previews. Show uncached catalog entries clearly when offline; retain access to uploaded subjects.
- [ ] Verify the entire Product and Model journeys in airplane mode, including app restart, local generation, partial failures, full-size viewing, and download. Also verify queued cloud work remains waiting until reviewed after reconnecting.
- [ ] Document supported devices, first-install connectivity, storage needs, realistic measured speed, and how to remove the local engine. The app's setup screen must use the same support facts as the documentation.

**Routing test excerpt:**

```ts
await page.getByRole('radio', { name: 'On this device', exact: true }).check();
await page.getByRole('button', { name: 'Generate 1 image', exact: true }).click();
await expect(page.getByRole('button', { name: 'Download image', exact: true }))
  .toBeVisible();
expect(recordedCloudRequests).toEqual([]);
expect(recordedLocalSubmissions).toHaveLength(1);
```

The arrays are captured by the test transport recording fixtures. Repeat with local memory failure and assert no cloud fallback, a retained draft, and a clear recovery action. In the full offline run, block external network access below browser level so server-side companion traffic is also covered.

**Run:** `npm run test:e2e -- tests/e2e/engine-routing.spec.ts` for deterministic failure cases; `npm run test:e2e -- tests/e2e/local-generation.spec.ts` against the real qualified companion for release evidence.

## Task 11 — Validate the complete product and prepare release

**Requirement coverage:** R01–R15.  
**Owner:** QA with design, client, server, and image/ML owners.  
**Create:** `tests/e2e/release-journeys.spec.ts`, `docs/quality/release-checklist.md`, `docs/quality/benchmark-report.md`, `docs/operations/runbook.md`, `docs/operations/data-retention.md`.  
**Consumes:** complete installed app, qualified engines, PRD acceptance matrix.  
**Produces:** measured go/no-go evidence, supported-device statement, operating instructions, and a reviewable release candidate.

- [ ] Walk every PRD release scenario. Include both tabs, all ratios/backgrounds, count 1/2/4, original/custom camera, saved and uploaded subjects, unknown provider outcome, and partial batches.
- [ ] Run 10 first-use sessions against the PRD target; record task time and points of confusion. Test the two outdoor labels, model picker, angle discovery, and total-count understanding. Revise copy or layout when evidence warrants it.
- [ ] Complete keyboard, screen-reader label, contrast, reduced-motion, 390 px, and desktop reviews. Verify sheets trap/restore focus and the sticky action never hides focused content.
- [ ] Re-run the representative image benchmark on pinned cloud and local engines. Report preservation/viewpoint scores separately, coverage gaps, p50/p95 latency, memory, failures, and real cost. A visual gallery alone is not a benchmark report.
- [ ] Fault-inject reloads, dropped connections, missing weights, corrupted downloads, quota exhaustion, local out-of-memory, expired credentials, and provider 429/5xx. Verify application replay does not create duplicate paid requests; unresolved provider outcomes remain Needs attention.
- [ ] Verify private asset ownership, credential storage, local pairing, network isolation, transient-file cleanup, project deletion, archive recovery, and log redaction. Document actual provider retention separately from application cleanup.
- [ ] Produce an engine rollback procedure, service-worker/schema migration recovery, cloud budget/rate-limit controls, and incident diagnostics that omit raw user imagery.
- [ ] Present the release candidate and collected evidence. Publishing or distributing the application belongs to a later authorized execution step; this planning deliverable performs neither.

**Release evidence check example:**

```json
{
  "requirement": "R13",
  "scenario": "Generate a new Model image with all external network access denied",
  "evidenceRequired": ["device-manifest", "job-record", "output-image", "network-log"],
  "passCondition": "real local result saved, zero external requests, metadata complete"
}
```

**Run after implementation:** `npm run typecheck`, `npm run test`, `npm run test:e2e`, `npm run build`, and `python -m pytest companion/tests`. Run the GPU tests on the qualified hardware; report unsupported environments explicitly. Do not mark skipped real-inference checks as passes.

## Requirement-to-task coverage

| Requirement | Tasks |
|---|---|
| R01 — tabs and independent drafts | 2, 3, 7, 8, 11 |
| R02 — Product upload/select | 3, 11 |
| R03 — Model upload/select | 3, 4, 10, 11 |
| R04 — model filters | 2, 4, 11 |
| R05 — ratios | 1, 2, 4, 6, 7, 11 |
| R06/R07 — backgrounds | 2, 4, 6, 9, 11 |
| R08 — angles | 1, 2, 5, 6, 9, 11 |
| R09 — prompt | 2, 4, 6, 9, 11 |
| R10 — total output count | 2, 4, 5, 6, 7, 11 |
| R11 — online generation | 1, 6, 7, 10, 11 |
| R12 — offline work and queue | 3, 8, 10, 11 |
| R13 — offline generation | 1, 9, 10, 11 |
| R14 — current qualified engines | 1, 2, 6, 9, 10, 11 |
| R15 — minimal usable interface | 3, 4, 5, 7, 8, 10, 11 |

## Handoff and definition of done

The next step is a design review of the PRD and M0 candidate/device choices. When implementation is requested, use either a task-by-task subagent workflow with review between deliverables or a single-session execution workflow with the same verification gates. Do not interpret the draft's technology recommendations as irreversible decisions.

For each task: create a failing behavioral test where useful, implement the smallest complete slice, run the named checks, inspect results, and commit the coherent change in the implementation repository. Visual styling changes use visual review rather than redundant tests. Finish a milestone only when its evidence exists; screenshots of a simulated Generate action are not evidence of real inference.

The completed v1 must meet all R01–R15 requirements on its declared supported environments. If model fidelity or local hardware prevents a requirement from passing, record that as an unresolved release condition and adjust the engine or supported-device statement. Do not relabel queued cloud work as offline image generation.
