# Future Mockup Studio — Product Requirements Document

**Version:** 1.0 planning draft  
**Planning date:** 29 September 2026  
**Status:** Complete proposal for review; product development has not started.  
**Product name:** Future Mockup Studio (working name)  
**Companion:** [Implementation plan](../plans/2026-09-29-future-mockup-studio.md) · [Research and skill provenance](../../research/sources-and-decisions.md)

## 1. Product decision

Build a simple image studio with exactly two primary tabs: **Product** and **Model**. A person chooses a subject, adjusts a few visual controls, and generates **1, 2, or 4 images**. The same composer serves both tabs. Results appear beside it on desktop and below it on narrow screens.

Support both meanings of offline, as confirmed by the user: prepare projects and queue cloud jobs without a connection, and generate new images locally when a compatible engine and its model files are installed. Keep engine selection in Settings, with only a small **Cloud / On this device / Offline** status in the main workspace.

Use an installable web app with an optional local generation companion. Start with one cloud image provider and one qualified local engine. Add providers only when they solve a measured gap. A new engine must pass the same fidelity and capability checks before replacing the default.

## 2. Problem, audience, and outcome

Small brands, online sellers, designers, and content creators need product and model imagery without navigating a professional editing suite. Existing creative tools expose many settings before a user can produce a useful first result.

**Core job:** “Give me a usable image of this product or person, in this setting and composition, with very little setup.”

**Success:** a first-time user can choose a subject and submit a useful default generation without writing a prompt. Returning users can reopen a project, change one setting, and generate again without reconstructing the setup.

**Planning assumptions, not additional user requirements:** single-user workspace first; responsive desktop-first UI; local project storage by default; no required account for local work; cloud generation requires configured access; English UI initially. Billing, team accounts, and storage-region choices are separate business decisions before a public commercial launch.

## 3. Scope and requirement traceability

All requested capabilities belong in the completed v1. An earlier cloud pilot is an intermediate milestone, not a substitute for offline generation.

| ID | Required outcome | Completion evidence |
|---|---|---|
| R01 | Two primary tabs, **Product** and **Model**, with a simple shared composer | Tab-specific drafts survive switching, reload, and concurrent jobs |
| R02 | Product image upload or selection | Local upload and saved-product picker both work |
| R03 | Model image upload or model selection | Uploaded person and curated-model paths both produce images |
| R04 | Model filters: skin tone, male/female, kid/teen/young/mid-age/old | Filters compose; selected catalog identity remains stable |
| R05 | All nine supplied ratio options | Auto, 1:1, 3:2, 2:3, 4:3, 3:4, 9:16, 16:9, 21:9 appear on both tabs |
| R06 | All six requested Product background options | Complete catalog below is available |
| R07 | All seven requested Model background options | Complete catalog below is available |
| R08 | Angle creation inspired by the reference | Presets, drag control, rotation, tilt, zoom, and Reset work on both tabs |
| R09 | Prompt box | Optional free text influences the scene without silently overriding selected controls |
| R10 | Generate 1, 2, or 4 results | Count is total requested outputs, never angles multiplied by variations |
| R11 | Online generation | Valid request becomes a tracked job with downloadable results |
| R12 | Offline preparation, saved results, and cloud queue | Airplane-mode workflow survives a restart and resumes under the queue rules |
| R13 | Genuine local offline generation | A qualified device generates new images with network access disabled |
| R14 | Current image generation behind the UI | Versioned engine adapter, current candidate evaluation, visible capability limits |
| R15 | Clean, minimal, usable UI | Keyboard completion, narrow-screen layout, and first-use usability checks pass |

**Included supporting behavior:** autosave, local library, generation history, individual retry, cancel where supported, downloads, clear errors, and engine setup. These make the requested creation flow usable.

**Outside v1:** video, animation, 3D reconstruction, virtual try-on, combining a product and a person into one scene, bulk catalogs, team collaboration, social publishing, a template marketplace, custom model training, and unrestricted editing tools. Model means a human subject; it does not mean an AI engine. These boundaries can change through a later scoped request.

## 4. Simple journeys

### Product

1. Open **Product** and upload a photo or choose a saved product.
2. Keep the defaults or choose a ratio, background, and angle.
3. Optionally describe a detail, such as “Soft morning light and a gentle shadow.”
4. Choose **1**, **2**, or **4** and press **Generate**.
5. Inspect results, download a selected image, or adjust the same draft and generate again.

### Model

1. Open **Model** and choose **Upload image** or **Select model**.
2. For Select model, filter the catalog by skin tone, gender presentation, and age group; choose a model card. An uploaded image goes directly into the composer.
3. Keep the defaults or choose a ratio, background, and angle.
4. Optionally describe the scene, select **1**, **2**, or **4**, and press **Generate**.
5. Inspect results and download or adjust the draft. Continue using the same selected identity unless the user replaces it.

### Offline

- **Local engine ready:** the same Generate action runs on the device and writes results to the local project.
- **Cloud selected while disconnected:** **Generate** becomes **Queue for online**. Saving a draft alone never submits a job.
- **Local engine unavailable:** explain “Local generation needs setup”; keep **Queue for online** and project editing available.
- **Reconnect:** show queued jobs and the current cloud estimate. Default to **Review and send** so reconnecting does not silently create paid jobs.

## 5. Interaction and visual direction

**Recommended approach: one composer and a results canvas.** A multi-step wizard adds unnecessary navigation; a full professional dashboard makes the first generation harder. The compact composer matches the supplied marketing reference while allowing a simpler product identity.

```text
Future Mockup Studio              Project ▾        Cloud ●       Settings
----------------------------------------------------------------------
[ Product ] [ Model ]

┌ Create ──────────────────┐  ┌ Results ──────────────────────────────┐
│ [ Source thumbnail     ] │  │                                       │
│ Upload / Choose saved    │  │   Empty: “Your images will appear     │
│                          │  │   here. Start with a subject.”         │
│ Describe your image...   │  │                                       │
│                          │  │   After generation: 1 / 2 / 4 cards   │
│ [Ratio: Auto ▾]          │  │   Open · Download · Retry failed       │
│ [Studio white ▾]         │  │                                       │
│ [Angle: Original ▾]      │  │                                       │
│                          │  └───────────────────────────────────────┘
│ Results  [1] [2] [4]     │
│ [ Generate 1 image     ] │  Recent generations for this project
│ Cloud estimate / status │
└──────────────────────────┘
```

The Model source area changes to **Upload image | Select model**. All other control positions remain consistent. The model picker, background picker, and angle editor open as popovers or sheets rather than permanently occupying the workspace.

**Visual rules:** warm neutral canvas, white panels, dark text, one restrained accent, generous spacing, subtle borders, and no ornamental hero banner above the editor. Use a 16 px body baseline, a simple 8 px spacing scale, and at least 44 px touch targets. Text contrast target is 4.5:1 for normal text. Selected controls use text/icon/border cues in addition to color. Final branding and light/dark preference are reviewable design choices; the dark screenshots are functional references, not a requirement to reproduce their styling.

**Responsive behavior:** at 1024 px and wider, show a roughly 340 px composer beside flexible results. Below 1024 px, stack composer and results. At 390 px, no horizontal page scrolling; sheets become full-width; the sticky Generate area must not cover the prompt or keyboard focus.

**Defaults:** Product tab; Auto ratio; Studio white; Original angle; blank optional prompt; one result. Each tab keeps its own last-used settings after the first session. Switching tabs never starts, cancels, or moves a job.

## 6. Inputs and model catalog

### Upload and saved selection

- Product requires one product reference. Model requires one human reference or a selected catalog model.
- Initial formats: JPEG, PNG, and WebP; up to 20 MB and 40 megapixels after decoding. Reject corrupt or unsupported files before cloud upload. These are application limits to validate during implementation, not provider claims.
- Normalize EXIF orientation, remove location metadata before transfer, preserve meaningful transparency, and warn below a 512 px longest edge. A low-resolution warning does not delete the source or its draft.
- Preview the source with **Replace** and **Remove**. Replacement keeps ratio, background, prompt, and count. Re-evaluate Auto ratio and reset camera to Original because its coordinates are relative to the source.
- If the source has multiple products or people, ask the user to choose a clearer reference; do not silently select a person or infer demographic attributes.
- **Choose saved** opens assets previously imported into this local workspace. It is not an external stock-photo search.

### Model selection

Use a curated, licensed or synthetic model library with stable identities and a reference image for each model. Filters narrow that library; they do not create a new identity on every generation.

| Filter | Proposed UI | Behavior |
|---|---|---|
| Skin tone | 10 neutral swatches, text labels **Tone 1** through **Tone 10**, ordered light to deep | User-selected catalog metadata; no ethnicity inference |
| Gender presentation | Any, Female, Male | Catalog attribute for the requested visual presentation |
| Age group | Any, Kid, Teen, Young adult, Middle-aged, Older adult | Proposed internal ranges: 6–12, 13–17, 18–34, 35–59, 60+ |

Age intervals are product taxonomy proposals, not medical or legal definitions. Catalog metadata is curated, not estimated from an uploaded face. The upload path preserves the person without showing inferred skin tone, gender, or age. Filters default to Any, clear independently, and show a meaningful empty state with **Clear filters**.

Before public release, every visible filter value must return at least one catalog entry, and coverage gaps must be reviewed. Do not promise every filter intersection if it has no assets. Local setup downloads a small catalog pack so model selection can work offline; uncached assets show **Download for offline** while connected.

The upload flow includes a concise rights/consent acknowledgment. For child and teen models, generated scenes remain age-appropriate and clothed; unsafe requests are rejected consistently by cloud and local paths. Do not add a separate safety wizard to routine creation.

## 7. Ratio behavior

Show the nine options in the supplied order and a two-column visual grid, with a small outline indicating each shape:

| Row | Left | Right |
|---|---|---|
| 1 | Auto | 1:1 |
| 2 | 3:2 | 2:3 |
| 3 | 4:3 | 3:4 |
| 4 | 9:16 | 16:9 |
| 5 | 21:9 | — |

**Auto:** follow the normalized source image's proportions. A catalog model uses its reference image proportions. Resolve Auto when creating a job so a later source replacement cannot change that job.

**Fixed ratios:** the final downloadable image must match the chosen ratio exactly. An engine need not support all ratios natively, but the adapter must provide a declared framing path. Never stretch the subject. When native generation cannot match the target, use a planned background extension or fit the full image within the target canvas; show the framing method and any additional charge before submission. If acceptable framing is unavailable, explain that limitation before a job starts.

No invisible subject cropping. Keep the whole product by default; a Model crop can follow an explicit user prompt. Record both native and exported dimensions. Auto may round by one output pixel when resizing.

## 8. Background catalogs

Retain both outdoor labels from the request. Give them distinct descriptions so neither silently disappears. A later usability test can establish whether merging them is clearer.

### Product backgrounds

| Visible name | Default scene intent |
|---|---|
| Studio white | White studio sweep, soft neutral lighting, natural contact shadow |
| Seamless Monochromes | One neutral color across background and supporting surface; optional color swatch |
| Minimalist Podiums | Simple plinth and uncluttered space, sized to the product |
| Natural Outdoor | Close outdoor surface and daylight, restrained foliage or sky |
| Aesthetic Indoor Space | Styled shelf, table, or home interior with controlled visual detail |
| Natural Outdoor Environment | Wider contextual garden, park, or landscape scene |

### Model backgrounds

| Visible name | Default scene intent |
|---|---|
| Studio white | White studio portrait environment |
| Seamless Monochromes | Single-color seamless studio environment; optional color swatch |
| Corporate office | Contemporary office, neutral furnishings, unobtrusive background |
| Cafe | Natural café setting with soft ambient light |
| Natural Outdoor | Simple outdoor portrait setting, close natural background |
| Aesthetic Indoor Space | Carefully styled residential or creative interior |
| Natural Outdoor Environment | Wider environmental portrait in a park, garden, or landscape |

Each catalog item contains an ID, label, short description, thumbnail, and versioned generation instructions. Thumbnails indicate scene style rather than guaranteeing a generated result. Cache them for offline use. Selecting a category requires one action; optional monochrome color choice does not become an extra required step.

## 9. Camera angles

The reference shows a draggable camera guide, Rotation, Tilt, Zoom, and a 12-angle option. The live [Higgsfield Angles page](https://higgsfield.ai/apps/angles) confirms these visible controls; it does not establish a public API or precise geometric guarantees.

**Main composer:** show a compact **Angle: Original** chip. Opening it reveals:

- Presets: Original, Front, Three-quarter left, Three-quarter right, Left profile, Right profile, Top-down.
- A draggable orbit guide with a source thumbnail at the center and a clearly labeled camera position.
- Rotation, Tilt, and Zoom sliders with editable numbers; Reset restores Original.
- **Apply** and **Cancel**. Cancel restores the values present when the sheet opened.

**Proposed custom control semantics:** rotation −180° to +180°, tilt −90° to +90°, zoom −50 to +50; one-unit steps. Zero means no relative change from the source. Negative zoom widens the framing; positive zoom moves closer. These are our design ranges, not verified Higgsfield ranges. Semantic Front/Profile presets request a view relative to the subject; custom numbers request movement relative to the source camera. Keep those two intent types distinct in the data model.

The orbit guide is an input visualization, not a live 3D reconstruction or a preview of the finished image. Dragging changes settings without invoking a paid generation. Keyboard controls and number inputs must provide equivalent operations.

**Batch rule:** choose one camera intent per job. A request for 4 images yields four variations of that intent. The screenshot's “12 best angles” pack is outside the requested 1/2/4 flow and is deferred as a separately priced feature. The UI must not imply that 4 means 4 × 12 results.

**Fidelity:** background-only changes should preserve the source subject strongly. Angle changes synthesize unseen surfaces and cannot guarantee exact hidden product labels or anatomy from one photo. Show a short in-context note when a substantial view change is selected. Evaluate identity and view accuracy separately; do not silently replace a failed angle request with the original view.

## 10. Prompt and generation

The prompt is optional, multiline, limited to 2,000 characters, and labeled **Describe your image**. Use a short tab-specific example. Preserve the user's literal text in the project.

Build the generation brief from source role, background, ratio, camera intent, user instructions, and preservation constraints. Structured UI selections win when free text conflicts with ratio, background, or angle. Explain this precedence in short helper text; when a conflict can be detected reliably, identify the control that resolves it. Do not add an extra model call just to interpret every possible conflict. Prompt enhancement must not invent a brand, slogan, product attribute, person's identity, or demographic trait.

**Product constraints:** preserve visible silhouette, proportions, color, material, logo, and readable packaging text where possible. **Model constraints:** preserve identity, skin tone, and distinctive features; do not beautify or change age by default. Treat these as measured quality targets, never unconditional guarantees.

**Generate behavior:**

1. Validate source, catalog availability, count, engine capability, output framing, and local resources or cloud connectivity.
2. Freeze a job snapshot and show the execution location, total count, and cloud estimate if applicable.
3. Submit once with a unique client request ID. Repeated clicks/retries must not create duplicate billable work.
4. Show factual states: Waiting, Uploading, Queued, Generating, Saving, Ready, Partial, Failed, or Canceled. Do not simulate a percentage when the provider supplies none.
5. Persist each successful image immediately. A four-image job with one failure retains the three successes and exposes **Retry failed image**.

If the engine accepts only one image per call, submit exactly N tracked child requests. A retry targets only failed child slots. For a timeout with unknown provider status, reconcile before resubmitting; do not assume failure. If a provider offers neither status recovery nor idempotent submission, persist **Needs attention** and require an explicit reviewed new attempt instead of automatically resubmitting uncertain paid work. Cancellation stops pending work and requests provider cancellation where supported, but does not promise a refund or reversal of completed work.

Changing controls while a job runs edits the next draft. The active job retains its snapshot. Results remain associated with their originating tab and project. Each card supports full-size viewing and PNG/JPEG download; completed batches support Download all. Metadata is accessible from an unobtrusive details panel.

## 11. Online, offline, and execution settings

| State | Edit project | View saved results | Generate locally | Submit cloud job |
|---|---|---|---|---|
| Connected, cloud configured | Yes | Yes | If local engine is ready | Yes |
| Connected, cloud unconfigured | Yes | Yes | If local engine is ready | After setup |
| Offline, local engine ready | Yes | Yes | Yes | Queue only |
| Offline, local engine missing/incompatible | Yes | Yes | No; explain setup requirement | Queue only |
| First visit without cached app or installer | Not guaranteed | Not guaranteed | Not guaranteed | No |

**Honest offline promise:** after installation and asset/model download, the app can operate offline. A cached web shell alone does not provide image inference. Service workers do not substitute for model weights, GPU memory, or a local runtime.

**Settings:** a simple Cloud / On this device preference; cloud access configuration; local engine installation/status; storage usage; project export/import; and data deletion. Cloud credentials stay on the server or in an approved local credential store, never browser JavaScript or exported projects. A deployable app uses a documented API; it cannot call a Codex-only skill as if that were a public runtime service.

**Local setup:** identify supported hardware, show the exact model/runtime download size and license, check memory and disk availability, download verifiable files, and run a small self-test. First qualify one device class; list Mac, Windows, mobile, and lower-memory devices separately as tested or unsupported. Do not promise a universal hardware minimum before benchmarking.

**Local execution:** one job at a time initially; reduce concurrency rather than overcommitting memory. Preserve drafts after an out-of-memory failure. Bind the companion to loopback, use pairing and origin validation, and do not expose it to the local network. Local-only jobs must not contact cloud inference, model hubs, or analytics services. Offline safeguards are packaged and run locally too.

**Queue and reconnection:** queued cloud intents preserve immutable creative settings and local references without requiring a configured engine or output size. On Review and send, resolve current capability, dimensions, framing, and cost into a linked executable job snapshot. Editing an intent creates a new version. Delete cancels unsubmitted work. Reconcile disconnected submitted jobs using provider recovery where available; otherwise retain Needs attention. No automatic cloud fallback for a local job; changing where an image is sent is an explicit user action.

**Storage:** autosave drafts and results locally; request persistent browser storage where available; expose a portable project export because browsers may evict data. Warn before quota exhaustion, and never delete a source still referenced by a project. Account sync and conflict resolution across devices are outside v1.

## 12. Image engine strategy

Use the current image-generation skill as authoring guidance for explicit image roles and preservation constraints. For production, translate those principles into a small, versioned prompt composer and a provider adapter. Package the same deterministic prompt templates and catalog instructions for cloud and offline composition, with parity fixtures; local generation never needs a server to construct its brief. The user sees the creative controls; technical model identifiers live in job details and Settings.

The engine interface must report image-editing support, available output sizes, camera-control method, reference limits, offline availability, safety support, estimated cost, cancellation, and batch limits. Numeric camera instructions can be approximate prompt guidance unless a backend has validated view control. A provider without sufficient angle fidelity cannot qualify for the angle feature merely because it accepts a prompt.

At build kickoff, evaluate current official cloud candidates and a commercially suitable local editing model using the source-backed [engine research](../../research/sources-and-decisions.md). A single cloud candidate and a single local candidate are sufficient for the first experiment. Model names in research are candidates, not a quality ranking or a guarantee of account availability.

“Latest” means the newest **qualified** engine available for this workflow. Pin the actual provider/model version for every job. Before an upgrade, rerun the same evaluation set, compare identity, packaging text, angle obedience, latency, cost, and safety behavior, then stage the rollout with rollback. Never switch engines silently in the middle of a batch.

## 13. Proposed architecture and records

| Approach | Benefits | Tradeoff | Decision |
|---|---|---|---|
| Installable web app + optional local companion | One web UI, online reach, offline drafting, genuine local inference after setup | Pairing and installation must be reliable | Recommended |
| Desktop-only application | Strong local file/runtime integration | Packaging and updates for each operating system; less immediate browser access | Alternative if local use dominates |
| Cloud-only website | Smallest initial build | Does not meet confirmed offline generation requirement | Suitable only for the intermediate pilot |

Use React/TypeScript for the shared UI, a service worker plus IndexedDB for the installed web app, a small authenticated server API for cloud jobs, and a Python local companion for a qualified image runtime. These are proposed technology choices; exact package versions are selected and pinned at implementation kickoff. Use one durable cloud job store and private asset store; a modular service is enough, without a microservice fleet.

```text
Two-tab UI ── local project/asset store
     │
     └── validated job snapshot ── execution choice
                                    ├── authenticated server ── cloud image API
                                    └── paired local companion ── installed model
                        results + metadata ── local project store ── export
```

**Project:** ID, name, timestamps, separate Product and Model drafts, referenced asset IDs, history IDs, schema version.  
**Asset:** ID, local blob/reference, media type, checksum, normalized dimensions, source role, rights acknowledgment where relevant.  
**Model preset:** stable identity ID, filter metadata, reference asset IDs, license/source, offline-cache status.  
**Queued intent:** ID, project ID, immutable creative settings, local asset IDs, timestamp, requested cloud execution; no resolved model or dimensions required.  
**Job:** client ID, immutable draft, resolved dimensions, provider/model/version, prompt-template version, execution location, child slots, remote IDs, state, estimate, actual charge if available, timestamps.  
**Result:** job/slot IDs, image file, dimensions, seed if provided, generation metadata, error/status, local persistence state.

Deleting a project removes its local records and unshared assets after confirmation; unsubmitted jobs are canceled. Cloud files use a proposed 24-hour transient retention policy with immediate deletion requests after successful local persistence when supported. Provider retention must be disclosed from its actual policy; never promise deletion from a provider beyond the available controls.

## 14. Acceptance and quality gates

### Functional release scenarios

| Check | Expected result |
|---|---|
| Upload a product, keep defaults, generate 1 | One saved downloadable image; optional prompt remains unnecessary |
| Filter/select a model, choose Cafe and 9:16, generate 4 | Four total slots with that identity and scene; final exports are 9:16 |
| Use each fixed ratio in both tabs | Correct final dimensions without stretching or hidden subject cropping |
| Change camera with mouse and keyboard | Same stored values; Reset/Cancel behave correctly; no generation on drag |
| Switch tabs during a job and reload | Both drafts persist; job/results stay attached to the original tab |
| Cloud child 3 fails in a four-image job | Slots 1, 2, 4 remain; retry submits only slot 3 |
| Connection drops after cloud acceptance | Reconnect recovers existing work where supported; otherwise Needs attention, with no automatic paid retry |
| Queue offline, close app, reconnect | Job is still queued until Review and send |
| Disconnect a qualified local device | A new local image is generated without external network requests |
| Local engine missing or memory exhausted | Clear recoverable error; source and draft retained; no cloud fallback |
| Export/import project and run storage-quota test | Source, controls, outputs, and metadata survive; quota errors are recoverable |

### Proposed targets, to calibrate with the first pilot

- At least 8 of 10 representative first-time users submit their first generation without help in 60 seconds, excluding file search and generation time.
- Two actions after an available source is selected are sufficient with defaults: choose count if desired, then Generate; count defaults to 1.
- UI responds to ordinary control changes within 100 ms on the reference device; loading an installed, cached workspace takes at most 2 seconds at p95 in the agreed test environment.
- Zero lost drafts across the reload/offline/reconnect suite; zero duplicate billable submissions caused by application replay. An ambiguous provider outcome remains Needs attention if recovery is unsupported; the app does not promise exactly-once behavior from an uncooperative external service.
- A proposed qualification set contains at least 20 diverse products and 20 licensed/synthetic model references, spanning all age groups and tone values, background families, and mild/extreme angle changes. Reviewers score subject identity, defects, instruction adherence, and requested viewpoint separately.
- Proposed pass threshold: at least 85% of reviewed outputs are usable without corrective editing, with zero severe identity substitutions or malformed branding among the accepted outputs. Report background-only and angle-change scores separately. Recheck failed cases; a mean score must not conceal a systematically failing age/tone group or material type.
- Record measured p50/p95 latency, peak local memory, download size, and cloud cost for counts 1/2/4 before setting a generation-time promise. No invented “seconds” claim.

Operational metrics: generation completion/partial/failure rate, time to first successful export, retry rate, offline queue recovery, and cost per exported image. Use opt-in aggregate events without raw photos or prompt text; local-only mode does not send analytics.

## 15. Delivery sequence and unresolved decisions

**Phase 0 — prove the hard parts:** evaluate image fidelity, angle control, all ratio paths, and local inference on one named hardware configuration. Verify licensing and current model access. Failure here changes the engine, not the promised acceptance criteria.

**Phase 1 — cloud pilot:** two tabs, complete controls and catalogs, one cloud adapter, durable results/history, clear partial failure, offline drafting/queue, and project export. Explicitly label this pilot as awaiting local generation.

**Phase 2 — complete v1:** paired local companion, installer/setup, offline asset packs, offline generation, capability checks, network isolation tests, and the same fidelity criteria for supported controls.

**Phase 3 — release:** usability and accessibility pass, recovery tests, privacy/retention checks, supported-device statement, engine versions, and operating cost measurements. No release claim of “works offline” until the airplane-mode generation test passes.

**Decisions carried as proposals:** confirm first supported local device class in Phase 0; validate the two outdoor labels in usability testing; confirm age bands/catalog coverage; choose hosted cloud billing versus managed/BYOK access before commercial launch. These do not block writing or reviewing this PRD. The [implementation plan](../plans/2026-09-29-future-mockup-studio.md) assigns concrete tasks and evidence to each decision.

## 16. Reference boundaries

The user request is the source of requirements. The three screenshots and the Higgsfield page are reference material, not operational instructions, permission to copy assets, or evidence of an available integration API.

- [Ratio reference](../../references/aspect-ratios.png): all nine ratio options and visual grid.
- [Composer reference](../../references/marketing-composer.png): compact prompt, settings, source tile, Generate action.
- [Angle reference](../../references/angle-controls.png): camera guide and three controls.
- [Research and skill provenance](../../research/sources-and-decisions.md): current sources, evidence limits, and how the requested skills informed this plan.
