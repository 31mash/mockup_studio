# Future Mockup Studio: working prototype

A clickable, working prototype of the two-tab image studio in the [PRD](../docs/superpowers/specs/2026-09-29-future-mockup-studio-design.md). Pick a product or a person, choose a ratio, background and camera angle, and generate 1, 2 or 4 images. Results are real, downloadable images made in your browser.

It uses the stack the [implementation plan](../docs/superpowers/plans/2026-09-29-future-mockup-studio.md) proposes (React, TypeScript, Vite, IndexedDB), and its domain code follows the plan's shared contracts, so it can seed the real build.

## Run it

```bash
cd prototype
npm install
npm run dev            # http://localhost:5173
```

| Command | What it does |
|---|---|
| `npm run build` | Typechecks, then builds one self-contained `dist/index.html` (fonts and code inlined, works offline from disk) |
| `npm test` | Domain unit tests (Vitest) |
| `npm run test:e2e` | Browser journeys (Playwright). Builds must exist: run `npm run build` first |
| `npm run build:artifact` | Also writes `artifact/future-mockup-studio.html`, the fragment published as a claude.ai artifact |

## What is real and what is simulated

| Area | In this prototype |
|---|---|
| Two tabs, composer, drafts | Real. Each tab keeps its own draft in IndexedDB and survives reloads |
| Uploads | Real. JPEG, PNG and WebP up to 20 MB and 40 MP; EXIF orientation applied; files re-encoded so location metadata never leaves the device; warning under 512 px |
| Model catalog and filters | Real filtering over 12 stable identities covering every tone, presentation and age group. **Faceless stand-in figures** replace photos until licensed or synthetic references exist |
| Ratios, backgrounds, angle controls | Real. All 9 ratios, 6 product and 7 model backgrounds, 7 presets, drag, keyboard and number inputs |
| Cutout | Real, on device. Transparent images are used as they are. Photos on a studio backdrop are separated by growing the backdrop inward from the border; the photo's own soft shadows go with it, so no grey slab or halo stays on the product. Edges are trimmed by a pixel and their colour cleaned. Limits: a white object on a backdrop of exactly the same white can lose parts, and enclosed holes (a mug handle) keep the backdrop colour |
| Camera angle | Real, on device, for products. The product is re-projected in WebGL: the photo stays a crisp front face, a side is extruded along its traced outline and lit by the scene light, and a long-lens camera turns up to 35° and tilts from -15° to 40°. Three-quarter presets use 35°. **Profile and top-down views are disabled**: the photo has no pixels for those sides, so they need a generative model. People keep their photographed angle (turning a person this way looks like a cardboard cutout); zoom still works |
| Shadows | Real, derived from the product's silhouette in the final view: a crisp contact line along its actual bottom outline, a soft occlusion pool, and a long soft shadow cast away from the key light. All are kept on the floor or podium top, never on the wall |
| Scenes | Painted procedurally (studio sweeps, podium, interiors, outdoors). Horizon, parallax and light follow the camera |
| On this device | Real. The sketch engine runs locally and offline, and never uploads anything |
| Cloud | **Simulated.** Same renderer plus upload, queue and network delays, so queueing, cancel and reconnection can be tested. No provider, no cost |
| Offline queue | Real behavior against the simulated cloud: queue while offline, persist across reloads, send only after **Review and send** |
| Partial failure and retry | Real. Settings has a switch that fails one image per batch, so retry-only-the-failed-slot can be tried |
| Generation brief | Real. A versioned, deterministic prompt composer (`brief-2026-09-29.1`) builds the text a real model would receive; see any job's Details |
| Downloads and export | Real. JPEG or PNG per image, a zip per batch, and a project export (zip with `project.json` and images). Inside the claude.ai viewer, saves go through the viewer's download prompt |

Not in the prototype: a real cloud provider, the local model companion, service-worker install, project import, and cross-device sync.

## Requirement coverage (PRD R01 to R15)

| ID | Status |
|---|---|
| R01 Two tabs, shared composer | Done |
| R02 Product upload or saved selection | Done |
| R03 Model upload or catalog selection | Done, with stand-in figures and a rights and consent check for uploads |
| R04 Tone, gender presentation, age filters | Done |
| R05 Nine ratios | Done, exact export sizes from the research table; Auto follows the source |
| R06, R07 Background catalogs | Done, both outdoor labels kept |
| R08 Angle controls | Done for products up to 35° turn and -15° to 40° tilt (true perspective re-projection). Profiles, top-down and turning people need a generative engine and are disabled with the reason shown |
| R09 Prompt box | Done, with 2,000-character limit and conflict notes that name the deciding control |
| R10 1, 2 or 4 results | Done. Count is the total; one camera intent per batch |
| R11 Online generation | Simulated cloud |
| R12 Offline preparation and queue | Done against the simulated cloud |
| R13 Local offline generation | The sketch engine runs offline; a qualified image model does not exist yet |
| R14 Current engine behind an adapter | Engine interface with capabilities and pinned versions; real engines come from plan Task 1 |
| R15 Clean, minimal, usable UI | Keyboard, focus, 390 px layout, light and dark themes, reduced motion |

## Design

Three skills shaped the interface.

- **clean-ui-report** gave the visual system: bone paper, violet-cast ink, one signal red, Anton display type with Archivo for everything else, hairline rules, square corners, no shadows, and caption rows under every image. Its signature ghost-and-ink wayfinding became the two big tabs. Dark mode uses its "lifted" inverse, not a literal swap.
- **ui-ux-pro-max** supplied the UX rules: 44 px targets, visible focus, labels above fields, errors next to the cause, empty and loading states, and the pre-delivery checklist. Its automatic style recommendation (claymorphism, purple, Fredoka) was rejected because it contradicts the chosen system.
- **design-taste-frontend** set the brief reading (a single-screen creative tool, print-calm editorial language) and the dials (variance 4, motion 3, density 5), and its bans: no em dashes, no emoji, one accent, one corner style, one icon family (Phosphor), no div-built fake screenshots. It is written for landing pages, so only those parts applied.

One deliberate deviation: clean-ui-report's muted grey `#757570` measures 4.0:1 on its paper color, below WCAG AA for small text. The light theme uses `#666661` (5.0:1), a darker step in the same hue.

## Engine lab

`npm run dev`, then open `/lab.html`. It renders cutouts (on dark and coloured grounds, with the alpha mask) and a matrix of scenes and camera angles from the test fixtures, with timings. Use it to review output quality side by side after engine changes. `tests/fixtures/shadow-box.jpg` and `shadow-bottle.jpg` are studio-style photos with soft cast shadows, for checking shadow removal.

## Structure

```text
src/
  domain/     contracts, catalogs, validation, framing, slots, camera, prompt composer
  engine/     canvas helpers, subject keying, WebGL re-projection (view3d), scene painters, renderer, stand-ins, engines
  lab/        dev-only engine lab (lab.html)
  storage/    IndexedDB, upload normalization, downloads
  state/      store, asset URLs, actions (jobs, queue, export)
  components/ top bar, tabs, composer, pickers, angle sheet, results, panels
tests/
  unit/       domain tests, including the plan's representative tests
  e2e/        browser journeys from the plan and PRD
  fixtures/   test images, drawn by make-fixtures.mjs
```
