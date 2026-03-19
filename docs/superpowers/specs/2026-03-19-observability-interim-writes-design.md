# Observability & Interim Writes — Design Spec

**Date:** 2026-03-19
**Status:** Draft
**Scope:** Template-level changes to the deep research engine factory

## Problem Statement

Generated research engines have three architectural gaps:

1. **Silent write failure.** Phase 2 agents accumulate all findings in their context window and attempt a single large file write at the end. When the output exceeds the model's output token limit, the write silently fails — nothing is written to disk, no error is surfaced, and the orchestrator proceeds as if the agent succeeded. All research from that agent is lost.

   **Note (2026-03-19):** Claude Opus 4.6 default output limits increased to 64k tokens (128k upper bound). While this reduces the frequency of silent write failures for typical research budgets (18k per agent), the incremental write protocol remains necessary for: (a) crash recovery — partial findings are preserved on disk, (b) observability — status updates and claims tracking depend on per-question writes, (c) context management — releasing findings from working memory keeps the agent sharp for subsequent questions, (d) future-proofing — token budgets are user-configurable and could exceed even 128k for specialized domains.

2. **Zero observability.** Backgrounded agents are a black box. The only way to check progress is to `ls` the output directory for new files or interrupt Claude to ask for a status update. There is no way to distinguish a stuck agent from one that is mid-research.

3. **Rabbit-holing via sub-agent spawning.** While search iteration depth is capped (`maxIterations`, `explorationDepth`, WebFetch cap), nothing prevents a Phase 2 agent from spawning its own sub-agents via the Agent tool. This opens an uncontrolled recursion path that bypasses all depth limiting.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Write granularity | Per research question | Natural unit of work; maps to existing file structure; keeps context lean |
| Observability mechanism | File-based status JSON + live web dashboard | Agents already write files; dashboard reads status files via SSE for instant updates |
| Dashboard server runtime | Node.js (built-in modules only) | `fs.watch` enables push-based SSE; zero `npm install` dependency |
| Dashboard scope | Read-only monitor (v1) | Controls and file preview add complexity; layer on later |
| Anti-rabbit-holing | Explicit no-spawn constraint in agent template | Simple prompt-level fix; closes the gap without architectural changes |
| Stuck detection | Post-Phase-2 output verification in orchestrator | Catches missing/empty output before Phase 3 synthesis reads non-existent files |
| Quick tier dashboard | Skip dashboard launch | Quick tier is too fast for a dashboard to be useful; adds unnecessary latency |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Orchestrator (orchestrator-skill.md.tmpl)                  │
│                                                             │
│  Phase 0: Create _status/, write _pipeline.json,            │
│           launch dashboard server (Standard+ tiers only)    │
│  Phase 1: Planning (updates _pipeline.json)                 │
│  Phase 2: Deploy agents → monitor → verify output           │
│  Phase 2.5+: Continue pipeline (each phase updates          │
│              _pipeline.json)                                │
└────────┬───────────────────────────────────────┬────────────┘
         │                                       │
    ┌────▼─────┐  ┌──────────┐  ┌──────────┐    │
    │ Agent A  │  │ Agent B  │  │ Agent C  │    │
    │          │  │          │  │          │    │
    │ Research │  │ Research │  │ Research │    │
    │ Q1→write │  │ Q1→write │  │ Q1→write │    │
    │ Q2→write │  │ Q2→write │  │ Q2→write │    │
    │ Q3→write │  │ Q3→write │  │ Q3→write │    │
    │ status✓  │  │ status✓  │  │ status✓  │    │
    └────┬─────┘  └────┬─────┘  └────┬─────┘    │
         │             │             │           │
    ┌────▼─────────────▼─────────────▼────┐      │
    │  BASE_DIR/_status/                  │      │
    │  ├── _pipeline.json                 │      │
    │  ├── agent-a.json                   │      │
    │  ├── agent-b.json                   │      │
    │  ├── agent-c.json                   │      │
    │  ├── server.js                      │      │
    │  └── dashboard.html                 │      │
    └────────────┬────────────────────────┘      │
                 │ fs.watch + SSE                │
    ┌────────────▼────────────────────────┐      │
    │  Dashboard (browser)                │      │
    │  http://localhost:3847              │      │
    │  Real-time pipeline + agent view    │      │
    └─────────────────────────────────────┘      │
```

**Concurrent sessions are safe.** Each research session creates a unique timestamped `BASE_DIR`, so concurrent sessions get separate `_status/` directories. The dashboard server's port-increment behavior handles port conflicts automatically.

## Section 1: Incremental Write Protocol

### Change target: `research-protocol.md.tmpl`

New section inserted after "Iterative Search-Assess-Refine Protocol":

```markdown
## Incremental Write Protocol

Write findings to disk after completing EACH research question — never accumulate
all findings for a single large write at the end.

After completing all Search-Assess-Refine passes for one research question:

1. APPEND new claims to `BASE_DIR/[TOPIC_SLUG]_Claims_[AgentID].md`
2. APPEND new sources to `BASE_DIR/[TOPIC_SLUG]_[AgentID]_Bibliography.md`
3. APPEND the iteration log entry to `BASE_DIR/[TOPIC_SLUG]_Methodology_Log_[AgentID].md`
4. APPEND discovered sources to `BASE_DIR/[TOPIC_SLUG]_Sources_[AgentID].md`
5. OVERWRITE status JSON to `BASE_DIR/_status/[AgentID].json` (see Agent Status Protocol)

### File Creation Convention

- First write creates the file with a markdown header (e.g., `# Claims — [AgentID]`)
- Subsequent writes append a section separator (`---`) followed by the new content
- Files are always valid markdown at every intermediate point

### Context Release

After writing to disk, release detailed findings from working memory. Retain only:
- Claim IDs and confidence levels (e.g., "C-01 HIGH, C-02 MEDIUM")
- Source count and top source IDs
- Brief gap summary (one line)

This keeps the context window lean for subsequent research questions.
```

### Change target: `agent-template.md.tmpl`

New section appended after existing content:

```markdown
## Agent Constraints

- Do NOT spawn sub-agents or use the Agent tool
- Do NOT create background tasks via TaskCreate
- All research must happen within this single agent session
- Write findings to disk after EACH research question — never accumulate
  all findings for a single large write at the end (see Incremental Write Protocol
  in research-protocol.md)
```

**Note on TaskCreate constraint:** This prevents Phase 2 research agents from spawning their own sub-tasks. The orchestrator itself uses the Task tool to deploy Phase 2 agents — that is expected and correct. The constraint applies only to agents' own behavior within their session.

## Section 2: Agent Status Protocol

### Prerequisite

The `BASE_DIR/_status/` directory is created by the orchestrator in Phase 0 (see Section 3, Orchestrator Integration). Agents write to this directory during Phase 2.

### Change target: `research-protocol.md.tmpl`

New section inserted after "Incremental Write Protocol":

```markdown
## Agent Status Protocol

Maintain a status file at `BASE_DIR/_status/[AgentID].json`. This file is OVERWRITTEN
(not appended) after each research question — it represents current state only.

The `_status/` directory is created by the orchestrator before agents are deployed.

### Status JSON Schema

{
  "agentId": "[AgentID]",
  "engineId": "${ENGINE_ID}",
  "phase": 2,
  "status": "researching | writing | assessing | refining | complete | error",
  "currentQuestion": "The research question currently being worked on",
  "questionsCompleted": 2,
  "questionsTotal": 5,
  "activity": "searching | assessing | refining | writing | idle",
  "webFetchesUsed": 4,
  "webFetchCap": 10,
  "claimsFound": 7,
  "sourcesCollected": 4,
  "iterationPass": 2,
  "maxIterations": 3,
  "lastUpdated": "ISO-8601 timestamp"
}

### When to Write Status

- On agent start: status "researching", questionsCompleted 0, activity "searching"
- After each Search pass: update activity to "searching"
- After each Assess pass: update activity to "assessing"
- After each Refine pass: update activity to "refining"
- After writing files for a completed question: increment questionsCompleted,
  update claimsFound and sourcesCollected totals, activity "writing"
- On completion of all questions: status "complete", activity "idle"
- On error or abort: status "error", add "message" field with explanation
```

**Note on `activity` values:** The schema intentionally uses coarse-grained activity states (searching, assessing, refining, writing, idle) rather than fine-grained ones (fetching, reading). Fine-grained states would require status writes before every WebFetch call, adding significant overhead for minimal observability benefit. The coarse states map directly to the Search-Assess-Refine protocol passes.

### Change target: `orchestrator-skill.md.tmpl`

#### Phase 0 additions

After deriving configuration (TOPIC_SLUG, RUN_TS, BASE_DIR), add:

```markdown
Create the status directory and initialize pipeline state:
1. Create `BASE_DIR/_status/` directory
2. Write `BASE_DIR/_status/_pipeline.json` with initial state (substitute all
   runtime variables — ENGINE_ID, TOPIC_SLUG, detected tier, agent IDs):

{
  "engineId": "${ENGINE_ID}",
  "topic": "${TOPIC_SLUG}",
  "tier": "${DETECTED_TIER}",
  "currentPhase": 0,
  "phaseLabel": "Tier Detection",
  "phases": [ ... ],
  "agents": [ ... ],
  "dashboardUrl": null,
  "startedAt": "ISO-8601 timestamp",
  "lastUpdated": "ISO-8601 timestamp"
}
```

**`phases` array construction rules** — build at Phase 0 based on detected tier and VVC config:

| Phase | Label | Include When |
|-------|-------|-------------|
| 0 | "Tier Detection" | Always |
| 1 | "Research Planning" | Always |
| 2 | "Parallel Research" | Always |
| 2.5 | "Batch Source Hashing" | Always |
| 3 | "Research Synthesis" | Always |
| 3.5 | "Comprehensive Follow-Up" | Comprehensive tier only |
| 4 | Use Phase 4 label from engine config: "Draft Reporting" when VVC active, "Professional Reporting" when VVC disabled or `--no-vvc` | Always |
| 4.5 | "Provenance Audit" | Standard, Deep, Comprehensive tiers |
| 5 | "VVC-Verify" | VVC enabled AND `--no-vvc` not set |
| 6 | "VVC-Correct" | VVC enabled AND `--no-vvc` not set |

All phases start with status `"pending"` except Phase 0 which starts as `"complete"`.

**`agents` array:** List only Phase 2 research agent IDs for the detected tier (from `agentPipeline.tiers[detectedTier].agents`). Do not include pipeline agents (research-planning-specialist, synthesis-specialist, research-reporting-specialist, vvc-specialist).

#### Phase transition updates

Before each phase begins, update `_pipeline.json`:
- Set `currentPhase` and `phaseLabel`
- Set the phase's status to `"in_progress"`
- Update `lastUpdated`

After each phase completes:
- Set the phase's status to `"complete"`
- Update `lastUpdated`

## Section 3: Live Dashboard

### New template files

Two new files added to `/plugin/skills/engine-creator/templates/`:

#### `dashboard-server.js.tmpl`

A Node.js server script (~150 lines) using only built-in modules (`http`, `fs`, `path`). Single template placeholder: `{{dashboardPort}}` (default: `3847`).

**Responsibilities:**
- Serve `dashboard.html` at `GET /`
- Serve `GET /api/status` — reads `_pipeline.json` for the `pipeline` key, then reads all other `.json` files (those without underscore prefix) as agent status files for the `agents` map. Returns combined payload:
  ```json
  {
    "pipeline": { /* _pipeline.json contents */ },
    "agents": {
      "agent-id-1": { /* agent status JSON */ },
      "agent-id-2": { /* agent status JSON */ }
    }
  }
  ```
- Serve `GET /api/events` — SSE endpoint. Uses `fs.watch` on the `_status/` directory. On any `.json` file change, reads all status files and pushes a `data:` event
- Port selection: starts at `{{dashboardPort}}`, increments if port is busy, prints URL to stdout
- Auto-shutdown: when `_pipeline.json` shows all phases `"complete"`, remains alive for 5 minutes then exits

#### `dashboard.html.tmpl`

A single self-contained HTML file with embedded CSS and JavaScript. No placeholders — all dynamic data comes from the `/api/status` and `/api/events` endpoints at runtime.

**Important:** The HTML must be served via the dashboard server (not opened directly as a `file://` URL) for SSE and API fetch to work.

**Dashboard UI elements:**

1. **Header bar** — engine name, topic, tier badge, elapsed time (live counter)

2. **Pipeline visualization** — horizontal phase nodes connected by lines. Dynamically renders whatever phases appear in `_pipeline.json` — handles 6-phase (no VVC), 8-phase (VVC), and 9-phase (Comprehensive + VVC) pipelines.
   - `○` pending (gray)
   - `●` in progress (pulsing animation)
   - `✓` complete (green)
   - `✗` error (red)
   - Phase labels below each node

3. **Agent cards** — one card per Phase 2 agent, showing:
   - Agent ID as card title
   - Progress bar (questionsCompleted / questionsTotal)
   - Activity badge with color coding:
     - `searching` → cyan
     - `assessing` → amber
     - `refining` → violet
     - `writing` → emerald
     - `idle` → muted green
     - `error` → rose
   - WebFetch budget meter (segmented blocks, not text)
   - Claims found count
   - Sources collected count
   - Current research question text (truncated with ellipsis if long)

4. **Completion banner** — when all phases are complete, header transitions to completion state showing total duration

**Quick tier behavior:** Dashboard is NOT launched for Quick tier (single agent, too fast to be useful). The orchestrator skips the dashboard launch step when Quick tier is detected. Status files and `_pipeline.json` are still written for post-hoc inspection.

**Behavior:**
- Connects to SSE endpoint on load for instant updates
- Falls back to polling `/api/status` every 3 seconds if SSE connection drops
- Responsive layout — works in a narrow side pane or full browser window

**Font loading:** Uses Google Fonts CDN for Departure Mono and IBM Plex Mono. Falls back to system monospace (`ui-monospace, 'Cascadia Code', 'Fira Code', monospace`) if CDN is unavailable (e.g., air-gapped networks). Font loading is non-blocking (`font-display: swap`).

**Visual Design: "Dark Ops Console"**

Aesthetic direction: refined industrial command center. The focused intensity of a
Bloomberg terminal crossed with the purposeful clarity of a build pipeline monitor.
Every pixel earns its place.

**Typography:**
- Display/Headers: **Departure Mono** — distinctive monospace with character, used for
  engine name, phase labels, agent IDs. Command-center feel without being cliché.
- Body/Values: **IBM Plex Mono** — crisp, legible at small sizes, for data values,
  counts, timestamps, research question text.
- Fallback stack: `ui-monospace, 'Cascadia Code', 'Fira Code', monospace`

**Color System (CSS custom properties):**
- `--bg-deep`: `#0c1017` — page background
- `--bg-surface`: `#141a23` — card backgrounds
- `--border`: `#1e2733` — card borders, dividers
- `--border-active`: `#2a3444` — pipeline connectors
- `--text-primary`: `#e2e8f0` — main text
- `--text-muted`: `#64748b` — secondary text, labels
- `--accent-search`: `#22d3ee` — cyan, searching activity
- `--accent-assess`: `#f59e0b` — amber, assessing activity
- `--accent-refine`: `#a78bfa` — violet, refining activity
- `--accent-write`: `#34d399` — emerald, writing activity
- `--accent-complete`: `#4ade80` — muted green, idle/complete
- `--accent-error`: `#fb7185` — rose, error states

**Background & Atmosphere:**
- Dot-grid pattern (pure CSS `radial-gradient`, 1px dots at 24px intervals,
  `#1a2230` on `#0c1017`). No images, no noise textures, no scan-lines.
- Refined industrial, not retro.
- Minimal box-shadows; border contrast provides depth.
- `::selection` color matches cyan accent.
- Smooth 300ms transitions on all state changes.

**Pipeline Visualization:**
- Horizontal strip of **diamond-shaped phase nodes** (45° rotated squares).
- Active phase diamond pulses with soft glow (`box-shadow` keyframe animation).
- Completed diamonds fill solid green with a subtle checkmark (CSS `::after` content).
- Error diamonds fill rose.
- Pending diamonds are outlined in `--border`.
- Connection lines between diamonds: thin `--border-active` lines.
- Active connection segment shows a traveling dot animation
  (CSS `@keyframes` on pseudo-element) during phase transitions.

**Agent Cards:**
- Left border accent stripe (3px) colored by current activity state.
- Progress bar: thin (4px), activity accent color against `--border` track.
- Current question text in `--text-muted`, IBM Plex Mono, single line,
  `text-overflow: ellipsis`.
- WebFetch budget: segmented meter (small filled/empty blocks), not "4/10" text.
  Instantly glanceable at a distance.
- Stats row: claims and sources as compact `label: value` pairs.
- Entry animation: cards slide in from bottom with staggered `animation-delay`
  on initial load (150ms between cards).

**Completion State:**
- When all phases complete, header background transitions to dark emerald gradient
  (`#0c1017` → `#0a1f1a`).
- "Research Complete" label with total elapsed time replaces live counter.
- Agent cards dim to 70% opacity, progress bars fill completely.

**Responsive Behavior:**
- Below 640px: pipeline nodes stack vertically, agent cards full-width.
- Above 640px: pipeline horizontal, agent cards in a responsive grid
  (2-up if space allows).

### Orchestrator integration

**Change target:** `orchestrator-skill.md.tmpl`

In Phase 0, after creating `_status/` directory and writing `_pipeline.json`:

```markdown
Launch the research dashboard (Standard, Deep, Comprehensive tiers only — skip for Quick):
1. Copy `${CLAUDE_SKILL_DIR}/dashboard-server.js` and
   `${CLAUDE_SKILL_DIR}/dashboard.html` to `BASE_DIR/_status/`
2. Run `node BASE_DIR/_status/server.js` in background via Bash tool
3. Capture the dashboard URL from stdout
4. Update `_pipeline.json` with dashboardUrl
5. Print to user: "Research dashboard: http://localhost:<port>"
```

### Generation logic

**Change target:** `SKILL.md` (engine creator wizard)

Step 8 (Generate skill files) gets a new sub-step:

```
Step 8f: Copy dashboard-server.js.tmpl and dashboard.html.tmpl to the engine's
skill directory, substituting {{dashboardPort}} (default: 3847, configurable
in Section 8 of the wizard).
```

**New wizard question in Section 8 (Advanced Configuration):**

Added to the existing item 2 list in Section 8 (alongside "max iterations", "exploration depth", "max WebFetch calls", etc.):

```
Dashboard port (default 3847): ____
```

**New placeholder derivation rule:**

```
{{dashboardPort}} = advanced.dashboardPort ?? 3847
```

**New engine-config.json field:**

Added under the existing `advanced` key (matching the schema key name):

```json
{
  "advanced": {
    "dashboardPort": 3847
  }
}
```

**Schema change:** Add `dashboardPort` to the `advanced.properties` object in both `engine-config-schema.json` and `preset-schema.json`:

```json
"dashboardPort": {
  "type": "integer",
  "description": "Port for the research dashboard server. Auto-increments if busy.",
  "default": 3847,
  "minimum": 1024,
  "maximum": 65535
}
```

This is required because the `advanced` object uses `"additionalProperties": false`.

### File structure addition

```
BASE_DIR/
├── _status/
│   ├── _pipeline.json
│   ├── [AgentID].json          (one per active agent)
│   ├── server.js               (copied from skill dir at runtime)
│   └── dashboard.html          (copied from skill dir at runtime)
```

Engine skill directory (generated at engine creation time):
```
skills/[engineName]/
├── SKILL.md
├── standards.md
├── research-protocol.md
├── provenance.md
├── vvc-pipeline.md             (if VVC enabled)
├── dashboard-server.js         (new)
└── dashboard.html              (new)
```

## Section 4: Orchestrator Stuck Detection

### Change target: `orchestrator-skill.md.tmpl`

New section inserted between Phase 2 agent deployment and Phase 2.5:

```markdown
### Phase 2 Output Verification

After all Phase 2 agents complete (orchestrator's Task tool signals agent completion),
verify output before proceeding to Phase 2.5:

1. For each deployed agent, check:
   a. `BASE_DIR/_status/[AgentID].json` exists
   b. Status file shows status "complete" (not "error" or "researching")
   c. `BASE_DIR/[TOPIC_SLUG]_Claims_[AgentID].md` exists and is non-empty
   d. `BASE_DIR/[TOPIC_SLUG]_[AgentID]_Bibliography.md` exists and is non-empty

2. Classify each agent's outcome:
   - HEALTHY: status "complete" + non-empty output files
   - PARTIAL: status "complete" but some output files missing/empty (possible write failure)
   - FAILED: status "error" or status file missing entirely
   - EMPTY: status file exists but no output files at all

3. Decision logic:
   - All HEALTHY: proceed to Phase 2.5
   - Mix of HEALTHY + PARTIAL/FAILED: log warnings, proceed with available data
   - All FAILED/EMPTY: halt pipeline, inform user:
     "All Phase 2 agents failed to produce output. Check the dashboard for
      error details. No research data available for synthesis."

4. Log verification results to `BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md`
   (this becomes the first entry in the consolidated methodology log)
```

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `templates/research-protocol.md.tmpl` | Modified | Add Incremental Write Protocol, Agent Status Protocol sections |
| `templates/agent-template.md.tmpl` | Modified | Add Agent Constraints section |
| `templates/orchestrator-skill.md.tmpl` | Modified | Add Phase 0 status init + dashboard launch, phase transition updates, Phase 2 output verification, add `_status/` subtree to File Output Structure section |
| `templates/dashboard-server.js.tmpl` | New | Node.js SSE server for dashboard |
| `templates/dashboard.html.tmpl` | New | Self-contained dashboard UI |
| `SKILL.md` | Modified | Add Step 8f (dashboard files), new placeholder rule, new wizard question in Section 8 item 2 list |
| `engine-config-schema.json` | Modified | Add `dashboardPort` to `advanced.properties` |
| `preset-schema.json` | Modified | Add `dashboardPort` to `advanced.properties` |
| `examples/patent-intelligence-engine/` | Modified | Regenerate with new template output |
| `commands/test-engine.md` | Modified | Renumber duplicate check IDs (4h/4i/4j), add new checks |

## Files NOT Changed

| File | Reason |
|------|--------|
| `templates/standards.md.tmpl` | No quality framework changes |
| `templates/provenance.md.tmpl` | No provenance changes |
| `templates/vvc-pipeline.md.tmpl` | No VVC changes |
| `templates/command-template.md.tmpl` | No command interface changes |
| `templates/sources-command-template.md.tmpl` | No sources command changes |
| `templates/extension-skill.md.tmpl` | **Known limitation:** Extension mode engines delegate to a separate base `/deep-research` plugin. Updating the factory's self-contained templates does NOT cause extension engines to pick up the new protocols. Extension engines will lack observability and incremental writes until the base `/deep-research` plugin is separately updated. This is out of scope for this spec. |
| Domain presets | `dashboardPort` uses schema default; no preset changes needed |

## Migration

Engines generated before this version continue to work — they simply lack observability and incremental writes. To upgrade, users re-run `/create-engine` or `/update-engine` with their existing `engine-config.json`. The new templates produce updated skill files with the new protocols and dashboard assets.

## Test Validation

**Prerequisite:** Renumber the existing duplicate check IDs in `test-engine.md`. The current file has two sets of 4h/4i/4j (lines 96-112 and 121-125). Renumber the second set to 4k/4l/4m before adding new checks.

Add to `/test-engine` suite (starting from 4n after renumbering):

- **Check 4n: Status protocol present.** Grep `research-protocol.md` for "Incremental Write Protocol" and "Agent Status Protocol". Must find both.
- **Check 4o: Agent constraints present.** Grep all agent `.md` files for "Do NOT spawn sub-agents". Must find in every agent file.
- **Check 4p: Dashboard assets present.** Verify `dashboard-server.js` and `dashboard.html` exist in the engine's skill directory.
- **Check 4q: Pipeline status initialization.** Grep `SKILL.md` for `_status/` directory creation and `_pipeline.json` initialization. Must find both.
- **Check 4r: Output verification.** Grep `SKILL.md` for "Phase 2 Output Verification" or "verify output". Must find at least one.
