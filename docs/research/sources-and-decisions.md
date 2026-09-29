# Research and planning decisions

This is a planning evidence log. Sources were reviewed during the session beginning 29 September 2026. Public documentation establishes capabilities to investigate; it does not establish account access, product quality, or compatibility with this computer.

## User requirements and references

The user requested a PRD and plan using andrej-karpathy-skills and Superpowers, with Product and Model tabs, supplied options, a simple UI, and online/offline use. The user subsequently confirmed **both** offline project preparation/queuing and offline image generation.

The screenshots are retained as reference assets in [docs/references](../references). They are not instructions to execute, copy a brand, start a generation, or publish a product.

The [Higgsfield Angles page](https://higgsfield.ai/apps/angles) describes new viewpoints from a photo and exposes a draggable camera control, Rotation, Tilt, Zoom, and a 12-angle option. The fetched page also reported a media-loading error; text controls were readable. We did not test its generation, inspect private implementation, or verify an integration API. The raw scrape is saved locally in `.firecrawl/higgsfield-angles.json` and is excluded from source control.

**Design inference:** use comparable camera input concepts, but keep one camera intent and a total result count of 1/2/4. The 12-angle pack is excluded from v1 to preserve the user's explicit output-count choices. No existing Higgsfield subscription or API access is assumed.

## Requested skills actually used

### Karpathy Guidelines

The named repository now resolves to [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills). The [skill at commit 2c606141936f1eeef17fa3043a72095b4765b9c2](https://github.com/multica-ai/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/skills/karpathy-guidelines/SKILL.md) was retrieved and read. It is a community interpretation of Karpathy's observations, not a claim that Karpathy authored this PRD or skill.

Applied principles: state assumptions, compare meaningful alternatives, keep scope small, change only requested material, and attach verification to each goal. No plugin was installed.

### Superpowers

Read the installed **brainstorming** and **writing-plans** skills from the Claude skill cache. Their local source paths are recorded below for reproducibility; upstream [Superpowers](https://github.com/obra/superpowers) was verified at commit `8ca22dba9a94f28898bbce59f2537ff4d87c747d`. The local cache's revision was not established, so it is not represented as identical to that upstream commit.

- [Local brainstorming SKILL.md](</Users/manishminglani/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/011d5361-1718-40c2-bcd8-1baf9adfccf3/efcb4615-ea87-4f1e-b145-2060dfe92195/skills/brainstorming/SKILL.md>)
- [Local writing-plans SKILL.md](</Users/manishminglani/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/011d5361-1718-40c2-bcd8-1baf9adfccf3/efcb4615-ea87-4f1e-b145-2060dfe92195/skills/writing-plans/SKILL.md>)

Applied the new-project design path: context inspection, a targeted clarification, alternative approaches, explicit system boundaries, written requirements, verifiable delivery tasks, and consistency review. The user explicitly requested both the PRD and plan, so both are supplied together as proposals. This session does not implement the application. The empty workspace was not a Git repository; no repository or commit was created merely to store the documents.

## Image-generation skill versus application backend

Read the installed [imagegen skill](/Users/manishminglani/.codex/skills/.system/imagegen/SKILL.md). It provides authoring guidance for reference roles, prompt structure, and identity preservation. Its preferred built-in tool runs inside Codex; its documented CLI fallback currently names `gpt-image-2`. That skill is not a standalone offline inference engine or a public API dependency for the proposed app.

No raster assets or sample generations were requested for this planning deliverable, so no paid image generation was submitted. The implementation uses the prompting principles through a versioned application module and independently selects an API/runtime from current documentation.

## Current cloud candidates

The [official OpenAI image-generation guide](https://developers.openai.com/api/docs/guides/image-generation) currently recommends `gpt-image-2.5-sunburst` for precise edits and `gpt-image-2.5-flare` for everyday speed. It documents reference-image editing, multiple outputs, custom sizing, and limits to consistency and composition. Initial design choice: benchmark Sunburst for product/person preservation, with Flare as a speed comparison if needed. This is a candidate selection, not a tested winner.

The [Sunburst model documentation](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst) lists the dated snapshot `gpt-image-2.5-sunburst-2026-09-08` and token-based pricing. Record the exact available snapshot; verify account eligibility, limits, and live pricing before build-time experiments. No fixed per-image price is assumed in this plan.

The following canvas examples are calculated to satisfy the guide's current custom-size constraints (16-pixel multiples, allowed pixel area, maximum edge, and aspect-ratio limits). They have not been quality-tested. The adapter must validate them against the actual selected engine at runtime.

| Ratio | Candidate native canvas |
|---|---|
| 1:1 | 1024 × 1024 |
| 3:2 | 1536 × 1024 |
| 2:3 | 1024 × 1536 |
| 4:3 | 1536 × 1152 |
| 3:4 | 1152 × 1536 |
| 9:16 | 864 × 1536 |
| 16:9 | 1536 × 864 |
| 21:9 | 1792 × 768 |

Auto depends on source proportions and may require an explicit framing path. Do not force all sources into the nearest preset without informing the user.

## Current local candidate

The [official Black Forest Labs FLUX.2 repository](https://github.com/black-forest-labs/flux2/blob/main/README.md) documents FLUX.2 Klein 4B generation and reference editing, and identifies the 4B variant as Apache-2.0. Other variants have different license restrictions. Its approximate 8 GB VRAM statement is a vendor claim for supported GPUs, not a validated requirement or a promise of performance on a Mac.

**Design choice:** evaluate Klein 4B as the first local candidate; verify the exact checkpoint license and all companion components. Do not substitute a non-commercial checkpoint unnoticed. If its fidelity or view control fails, qualify another local engine before claiming offline feature completion.

[Hugging Face Diffusers installation documentation](https://huggingface.co/docs/diffusers/installation) describes local caching of required files and `HF_HUB_OFFLINE=1` to prevent Hub requests. This supports the feasibility of preinstalled offline inference. It does not prove the entire application has no network traffic; that requires a network-denied end-to-end test, including local safety components and catalog assets.

## Decisions and evidence limits

| Decision | Basis | What must be validated |
|---|---|---|
| Shared two-tab composer | User request and compact screenshot | First-use success and control discovery |
| Preserve both outdoor labels | User explicitly listed both | Whether descriptions are distinguishable |
| Curated model catalog | Simple, repeatable identity selection | Rights, age/tone coverage, offline asset pack |
| One angle per 1/2/4 batch | Avoid ambiguous output multiplication | Usability of count and camera summary |
| Web app + local companion | Covers both confirmed offline needs | Browser pairing, caching, installation, hardware |
| Newest qualified engine | Current models evolve | Fidelity, access, pricing, latency, regression checks |
| No cloud fallback for local jobs | Keeps execution location meaningful | Network isolation and failure recovery |

No live image benchmarks, provider purchases, hardware benchmarks, app deployment, or product implementation occurred in this session. All timings and quality thresholds in the PRD are proposed acceptance targets.
