# mockup_studio

Creative mockups: product and lifestyle still shoots.

**Future Mockup Studio** (working name) is a planned image studio for small brands, online sellers, designers and content creators. Pick a product or a person, choose a setting, ratio and camera angle, and get 1, 2 or 4 finished stills, without writing a prompt. It generates in the cloud or, after setup, on your own machine with no connection.

> **Status: working prototype.** The PRD, implementation plan and research log are in [`docs/`](docs/README.md). A working prototype of the studio is in [`prototype/`](prototype/README.md). It generates real images in the browser with a sketch compositor. Run on your computer, it also makes new camera angles with a real image model on Hugging Face, through a small local server that keeps your token off the page. A full cloud provider and an offline local model are still to come.

## What it will do

- **Product tab:** upload or choose a saved product, then place it in a studio, on a podium, in an interior or outdoors.
- **Model tab:** upload a photo of a person, or select a model from a curated catalog filtered by skin tone, gender presentation and age group, then place them in a studio, office, café, interior or outdoors.
- **Nine ratios**, from Auto to 21:9, with no stretching or hidden cropping.
- **Camera angles:** presets like Front, Three-quarter and Top-down, or a custom orbit with rotation, tilt and zoom.
- **Optional prompt** for extra direction.
- **Cloud or on-device generation.** Offline without a local engine, projects still save and cloud jobs wait until you review and send them.

## Try the prototype

```bash
cd prototype
npm install
cp .env.example .env.local   # optional: add HF_TOKEN for generative camera angles
npm run dev                  # http://localhost:5173
```

See [`prototype/README.md`](prototype/README.md) for what is real, what is simulated, how the local server works, and how the design was built.

## Documentation

| Document | What it covers |
|---|---|
| [Docs overview](docs/README.md) | Reading order, product summary, roadmap, open decisions |
| [PRD](docs/superpowers/specs/2026-09-29-future-mockup-studio-design.md) | Requirements R01–R15, UI, catalogs, offline rules, architecture, acceptance gates |
| [Implementation plan](docs/superpowers/plans/2026-09-29-future-mockup-studio.md) | 11 tasks across milestones M0–M3, contracts, API, tests |
| [Research and decisions](docs/research/sources-and-decisions.md) | Engine candidates, sources, decision rationale |
| [Prototype](prototype/README.md) | How to run it, what it covers, requirement status |
