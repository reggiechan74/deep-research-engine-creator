# Observability & Interim Writes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add incremental writes, agent status protocol, live dashboard, and stuck detection to the research engine factory templates.

**Architecture:** Template-level changes to the factory's `.tmpl` files that propagate into all newly generated engines. Two new template files (dashboard server + dashboard HTML). No runtime infrastructure changes — agents write status JSON files, a Node.js server watches them via `fs.watch` and pushes updates to a browser dashboard via SSE.

**Tech Stack:** Node.js (built-in `http`, `fs`, `path` modules), HTML/CSS/JS (single-file dashboard), Google Fonts (Departure Mono, IBM Plex Mono), CSS animations, Server-Sent Events.

**Spec:** `docs/superpowers/specs/2026-03-19-observability-interim-writes-design.md`

---

### Task 1: Renumber duplicate test check IDs

**Files:**
- Modify: `plugin/commands/test-engine.md:121-125`

The existing `test-engine.md` has duplicate check IDs: 4h, 4i, 4j appear at both lines 96-112 and 121-125. Renumber the second set before adding new checks.

- [ ] **Step 1: Rename duplicate 4h to 4k**

In `plugin/commands/test-engine.md`, change line 121:

```
**4h: SKILL.md line count.**
```
to:
```
**4k: SKILL.md line count.**
```

- [ ] **Step 2: Rename duplicate 4i to 4l**

Change line 123:

```
**4i: No per-fetch hashing.**
```
to:
```
**4l: No per-fetch hashing.**
```

- [ ] **Step 3: Rename duplicate 4j to 4m**

Change line 125:

```
**4j: No shared file writes.**
```
to:
```
**4m: No shared file writes.**
```

- [ ] **Step 4: Commit**

```bash
git add plugin/commands/test-engine.md
git commit -m "fix: renumber duplicate test check IDs 4h/4i/4j to 4k/4l/4m"
```

---

### Task 2: Add Incremental Write Protocol to research-protocol template

**Files:**
- Modify: `plugin/skills/engine-creator/templates/research-protocol.md.tmpl`

- [ ] **Step 1: Read the current template**

Read `plugin/skills/engine-creator/templates/research-protocol.md.tmpl` to identify the insertion point (after the "Iterative Search-Assess-Refine Protocol" section, before "File Isolation Protocol").

- [ ] **Step 2: Insert the Incremental Write Protocol section**

After the closing ` ``` ` of the Iterative Search-Assess-Refine Protocol section (after line 73), insert:

```markdown
---

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

- [ ] **Step 3: Verify insertion**

Grep the file for "Incremental Write Protocol" to confirm it's present.

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/engine-creator/templates/research-protocol.md.tmpl
git commit -m "feat: add Incremental Write Protocol to research-protocol template"
```

---

### Task 3: Add Agent Status Protocol to research-protocol template

**Files:**
- Modify: `plugin/skills/engine-creator/templates/research-protocol.md.tmpl`

- [ ] **Step 1: Insert the Agent Status Protocol section**

After the Incremental Write Protocol section (added in Task 2), insert:

```markdown
---

## Agent Status Protocol

Maintain a status file at `BASE_DIR/_status/[AgentID].json`. This file is OVERWRITTEN
(not appended) after each research question — it represents current state only.

The `_status/` directory is created by the orchestrator before agents are deployed.

### Status JSON Schema

```json
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
```

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

- [ ] **Step 2: Verify insertion**

Grep the file for "Agent Status Protocol" to confirm it's present.

- [ ] **Step 3: Commit**

```bash
git add plugin/skills/engine-creator/templates/research-protocol.md.tmpl
git commit -m "feat: add Agent Status Protocol to research-protocol template"
```

---

### Task 4: Add Agent Constraints to agent template

**Files:**
- Modify: `plugin/skills/engine-creator/templates/agent-template.md.tmpl`

- [ ] **Step 1: Read the current template**

Read `plugin/skills/engine-creator/templates/agent-template.md.tmpl` (currently 31 lines).

- [ ] **Step 2: Append Agent Constraints section**

After line 31 (`{{agentFirstActionsBlock}}`), append:

```markdown

## Agent Constraints

- Do NOT spawn sub-agents or use the Agent tool
- Do NOT create background tasks via TaskCreate
- All research must happen within this single agent session
- Write findings to disk after EACH research question — never accumulate
  all findings for a single large write at the end (see Incremental Write Protocol
  in research-protocol.md)
```

- [ ] **Step 3: Verify the constraint is present**

Grep the file for "Do NOT spawn sub-agents" to confirm.

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/engine-creator/templates/agent-template.md.tmpl
git commit -m "feat: add Agent Constraints (no sub-agent spawning) to agent template"
```

---

### Task 5: Add Phase 0 status initialization and phase transitions to orchestrator template

**Files:**
- Modify: `plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl`

- [ ] **Step 1: Read the current template**

Read `plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl` to identify insertion points.

- [ ] **Step 2: Add status initialization to Phase 0**

After the "Derive Configuration" code block (after line 59, the closing ` ``` `), insert:

```markdown

### Status Directory & Pipeline State

Create `BASE_DIR/_status/` directory. Write `BASE_DIR/_status/_pipeline.json` with initial pipeline state. Substitute all runtime variables (ENGINE_ID, TOPIC_SLUG, detected tier, agent IDs for this tier):

```json
{
  "engineId": "${ENGINE_ID}",
  "topic": "${TOPIC_SLUG}",
  "tier": "${DETECTED_TIER}",
  "currentPhase": 0,
  "phaseLabel": "Tier Detection",
  "phases": [],
  "agents": [],
  "dashboardUrl": null,
  "startedAt": "ISO-8601 timestamp",
  "lastUpdated": "ISO-8601 timestamp"
}
```

**Phases array** -- build at Phase 0 based on detected tier and VVC config:

| Phase | Label | Include When |
|-------|-------|-------------|
| 0 | Tier Detection | Always |
| 1 | Research Planning | Always |
| 2 | Parallel Research | Always |
| 2.5 | Batch Source Hashing | Always |
| 3 | Research Synthesis | Always |
| 3.5 | Comprehensive Follow-Up | Comprehensive tier only |
| 4 | If `--no-vvc` or VVC disabled: "Professional Reporting"; otherwise: "Draft Reporting" | Always |
| 4.5 | Provenance Audit | Standard, Deep, Comprehensive |
| 5 | VVC-Verify | VVC enabled AND --no-vvc not set |
| 6 | VVC-Correct | VVC enabled AND --no-vvc not set |

All phases start with status `"pending"` except Phase 0 which is `"complete"`. The `agents` array lists only Phase 2 research agent IDs for the detected tier.
```

- [ ] **Step 3: Add phase transition updates**

After the Phase 0 section, insert:

```markdown

### Phase Transition Protocol

Before each phase begins, update `_pipeline.json`:
- Set `currentPhase` and `phaseLabel` to the new phase
- Set the phase's status to `"in_progress"`
- Update `lastUpdated` timestamp

After each phase completes:
- Set the phase's status to `"complete"`
- Update `lastUpdated` timestamp
```

- [ ] **Step 4: Add dashboard launch for Standard+ tiers**

After the phase transition protocol, insert:

```markdown

### Research Dashboard (Standard, Deep, Comprehensive tiers only)

Skip this step for Quick tier.

1. Copy `${CLAUDE_SKILL_DIR}/dashboard-server.js` and `${CLAUDE_SKILL_DIR}/dashboard.html` to `BASE_DIR/_status/`
2. Run `node BASE_DIR/_status/server.js` in background via Bash tool
3. Capture the dashboard URL from stdout
4. Update `_pipeline.json` with `dashboardUrl`
5. Print to user: "Research dashboard: http://localhost:<port>"
```

- [ ] **Step 5: Add `_status/` to File Output Structure**

In the File Output Structure section (line 164 of `orchestrator-skill.md.tmpl`), find the line:

```
{{reportOutputDir}}/${RUN_TS}_${TOPIC_SLUG}/
├── [TOPIC_SLUG]_Research_Outline.md
```

Replace with:

```
{{reportOutputDir}}/${RUN_TS}_${TOPIC_SLUG}/
├── _status/
│   ├── _pipeline.json
│   ├── [AgentID].json                              # Per-agent status
│   ├── server.js                                   # Dashboard server
│   └── dashboard.html                              # Dashboard UI
├── [TOPIC_SLUG]_Research_Outline.md
```

- [ ] **Step 6: Verify all insertions**

Grep for "_pipeline.json", "Phase Transition Protocol", and "Research Dashboard" in the file.

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl
git commit -m "feat: add Phase 0 status init, phase transitions, dashboard launch to orchestrator"
```

---

### Task 6: Add Phase 2 Output Verification to orchestrator template

**Files:**
- Modify: `plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl`

- [ ] **Step 1: Identify insertion point**

Find the "Phase 2.5: Batch Source Hashing" section in the orchestrator template (around line 107).

- [ ] **Step 2: Insert Phase 2 Output Verification**

Before Phase 2.5 (between Phase 2 agent deployment and Phase 2.5), insert:

```markdown

### Phase 2 Output Verification

After all Phase 2 agents complete, verify output before proceeding to Phase 2.5:

1. For each deployed agent, check:
   a. `BASE_DIR/_status/[AgentID].json` exists
   b. Status file shows status `"complete"` (not `"error"` or `"researching"`)
   c. `BASE_DIR/[TOPIC_SLUG]_Claims_[AgentID].md` exists and is non-empty
   d. `BASE_DIR/[TOPIC_SLUG]_[AgentID]_Bibliography.md` exists and is non-empty

2. Classify each agent's outcome:
   - **HEALTHY**: status "complete" + non-empty output files
   - **PARTIAL**: status "complete" but some output files missing/empty (possible write failure)
   - **FAILED**: status "error" or status file missing entirely
   - **EMPTY**: status file exists but no output files at all

3. Decision logic:
   - All HEALTHY: proceed to Phase 2.5
   - Mix of HEALTHY + PARTIAL/FAILED: log warnings, proceed with available data
   - All FAILED/EMPTY: halt pipeline, inform user: "All Phase 2 agents failed to produce output. Check the dashboard for error details. No research data available for synthesis."

4. Log verification results to `BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md` (this becomes the first entry in the consolidated methodology log)
```

- [ ] **Step 3: Verify insertion**

Grep for "Phase 2 Output Verification" in the file.

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl
git commit -m "feat: add Phase 2 Output Verification (stuck agent detection) to orchestrator"
```

---

### Task 7: Create dashboard server template

**Files:**
- Create: `plugin/skills/engine-creator/templates/dashboard-server.js.tmpl`

- [ ] **Step 1: Create the dashboard server template**

Write `plugin/skills/engine-creator/templates/dashboard-server.js.tmpl`:

```javascript
// Research Dashboard Server — {{engineDisplayName}}
// Zero-dependency Node.js server using built-in http, fs, path modules.
// Serves dashboard HTML and provides SSE endpoint for real-time status updates.

const http = require('http');
const fs = require('fs');
const path = require('path');

const STATUS_DIR = __dirname;
const DASHBOARD_HTML = path.join(STATUS_DIR, 'dashboard.html');
const PIPELINE_FILE = path.join(STATUS_DIR, '_pipeline.json');
const DEFAULT_PORT = {{dashboardPort}};
const SHUTDOWN_DELAY_MS = 5 * 60 * 1000; // 5 minutes after completion

function readJsonSafe(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch {
    return null;
  }
}

function getStatus() {
  const pipeline = readJsonSafe(PIPELINE_FILE);
  const agents = {};
  if (fs.existsSync(STATUS_DIR)) {
    for (const file of fs.readdirSync(STATUS_DIR)) {
      if (file.endsWith('.json') && !file.startsWith('_')) {
        const agentId = file.replace('.json', '');
        const data = readJsonSafe(path.join(STATUS_DIR, file));
        if (data) agents[agentId] = data;
      }
    }
  }
  return { pipeline, agents };
}

// SSE clients
const sseClients = new Set();

function broadcastStatus() {
  const status = getStatus();
  const data = `data: ${JSON.stringify(status)}\n\n`;
  for (const res of sseClients) {
    try { res.write(data); } catch { sseClients.delete(res); }
  }
  // Check for pipeline completion
  if (status.pipeline && status.pipeline.phases) {
    const allComplete = status.pipeline.phases.every(p => p.status === 'complete');
    if (allComplete && !shutdownScheduled) {
      shutdownScheduled = true;
      console.log(`Pipeline complete. Server will shut down in 5 minutes.`);
      setTimeout(() => process.exit(0), SHUTDOWN_DELAY_MS);
    }
  }
}

let shutdownScheduled = false;

// Watch for status file changes
let debounceTimer = null;
fs.watch(STATUS_DIR, (eventType, filename) => {
  if (filename && filename.endsWith('.json')) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(broadcastStatus, 100);
  }
});

const server = http.createServer((req, res) => {
  if (req.url === '/' || req.url === '/index.html') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    try {
      res.end(fs.readFileSync(DASHBOARD_HTML, 'utf8'));
    } catch {
      res.end('<h1>Dashboard not found</h1>');
    }
  } else if (req.url === '/api/status') {
    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    });
    res.end(JSON.stringify(getStatus()));
  } else if (req.url === '/api/events') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*'
    });
    res.write(`data: ${JSON.stringify(getStatus())}\n\n`);
    sseClients.add(res);
    req.on('close', () => sseClients.delete(res));
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

function tryListen(port) {
  server.listen(port, () => {
    console.log(`Research dashboard: http://localhost:${port}`);
  });
  server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      tryListen(port + 1);
    } else {
      console.error(`Server error: ${err.message}`);
      process.exit(1);
    }
  });
}

tryListen(DEFAULT_PORT);
```

- [ ] **Step 2: Verify the file was created**

Check that the file exists and contains `{{dashboardPort}}` placeholder.

- [ ] **Step 3: Commit**

```bash
git add plugin/skills/engine-creator/templates/dashboard-server.js.tmpl
git commit -m "feat: add dashboard-server.js.tmpl (Node SSE server for research dashboard)"
```

---

### Task 8: Create dashboard HTML template

**Files:**
- Create: `plugin/skills/engine-creator/templates/dashboard.html.tmpl`

This is the largest single file. Use the frontend-design skill's "Dark Ops Console" aesthetic. The dashboard has no template placeholders — all data comes from the API at runtime.

- [ ] **Step 1: Create the dashboard HTML template**

Write `plugin/skills/engine-creator/templates/dashboard.html.tmpl` — a single self-contained HTML file with embedded CSS and JS implementing:

**Structure:**
1. Google Fonts link (Departure Mono, IBM Plex Mono) with system monospace fallback
2. CSS with custom properties for the Dark Ops Console color system
3. Dot-grid background pattern via CSS `radial-gradient`
4. Pipeline visualization: diamond-shaped phase nodes, pulse animation on active, checkmark on complete
5. Agent cards: left accent stripe, thin progress bar, segmented WebFetch meter, stats row, current question
6. Completion state: emerald gradient header, dimmed cards
7. JS: SSE connection to `/api/events`, fallback polling to `/api/status` every 3s, elapsed time counter

**Key CSS details:**
- `--bg-deep: #0c1017`, `--bg-surface: #141a23`, `--border: #1e2733`
- Activity colors: search `#22d3ee`, assess `#f59e0b`, refine `#a78bfa`, write `#34d399`, complete `#4ade80`, error `#fb7185`
- Diamond nodes: `transform: rotate(45deg)` with 24px squares
- `@keyframes pulse` for active phase glow
- `@keyframes slideIn` for agent card entry animation with staggered delay
- Responsive: vertical pipeline and full-width cards below 640px

**Key JS details:**
- `connectSSE()`: opens EventSource to `/api/events`, parses `data` events, calls `render()`
- `fallbackPoll()`: `setInterval` fetching `/api/status` every 3000ms, used when SSE fails
- `render(status)`: updates pipeline nodes, agent cards, header, elapsed time
- `formatElapsed(startedAt)`: computes and formats `HH:MM:SS` from start time
- `createWebFetchMeter(used, cap)`: returns segmented block HTML
- `activityColor(activity)`: maps activity string to CSS variable name

- [ ] **Step 2: Verify the file was created**

Check that the file exists and contains no `{{` template placeholders.

- [ ] **Step 3: Commit**

```bash
git add plugin/skills/engine-creator/templates/dashboard.html.tmpl
git commit -m "feat: add dashboard.html.tmpl (Dark Ops Console live research monitor)"
```

---

### Task 9: Add dashboardPort to JSON schemas

**Files:**
- Modify: `plugin/skills/engine-creator/templates/engine-config-schema.json:744-751`
- Modify: `plugin/skills/engine-creator/templates/preset-schema.json` (corresponding `advanced.properties` section)

- [ ] **Step 1: Read the preset schema to find the insertion point**

Read the `advanced.properties` section of `preset-schema.json`.

- [ ] **Step 2: Add dashboardPort to engine-config-schema.json**

In `engine-config-schema.json`, inside the `advanced.properties` object (after the `comprehensiveFollowUpAgentCap` property, before the closing `}` of `properties` around line 750), add:

```json
,
"dashboardPort": {
  "type": "integer",
  "description": "Port for the research dashboard server. Auto-increments if busy.",
  "default": 3847,
  "minimum": 1024,
  "maximum": 65535
}
```

- [ ] **Step 3: Add dashboardPort to preset-schema.json**

Add the same property definition to the `advanced.properties` object in `preset-schema.json`.

- [ ] **Step 4: Verify both schemas are valid JSON**

```bash
node -e "JSON.parse(require('fs').readFileSync('plugin/skills/engine-creator/templates/engine-config-schema.json', 'utf8')); console.log('engine-config-schema: valid')"
node -e "JSON.parse(require('fs').readFileSync('plugin/skills/engine-creator/templates/preset-schema.json', 'utf8')); console.log('preset-schema: valid')"
```

Expected: both print "valid".

- [ ] **Step 5: Commit**

```bash
git add plugin/skills/engine-creator/templates/engine-config-schema.json plugin/skills/engine-creator/templates/preset-schema.json
git commit -m "feat: add dashboardPort to engine-config and preset schemas"
```

---

### Task 10: Add Step 8f and dashboardPort placeholder rule to SKILL.md

**Files:**
- Modify: `plugin/skills/engine-creator/SKILL.md`

- [ ] **Step 1: Read the current SKILL.md to find Step 8e and the Placeholder Derivation Rules table**

Read `plugin/skills/engine-creator/SKILL.md` and locate Step 8e (~line 267) and the placeholder derivation table (~line 275).

- [ ] **Step 2: Add Step 8f after Step 8e**

After the Step 8e paragraph (vvc-pipeline.md generation), before "Steps 8a-8e are independent", insert:

```markdown

**Step 8f -- Dashboard files.** Read `dashboard-server.js.tmpl`, replace `{{dashboardPort}}` with `advanced.dashboardPort ?? 3847`. Write to `{OUTPUT_DIR}/skills/{skillDirName}/dashboard-server.js`. Copy `dashboard.html.tmpl` unchanged (no placeholders) to `{OUTPUT_DIR}/skills/{skillDirName}/dashboard.html`.
```

Update the "Steps 8a-8e are independent" line to "Steps 8a-8f are independent".

- [ ] **Step 3: Add dashboardPort to the Placeholder Derivation Rules table**

After the `{{provenanceBudget}}` row in the derivation table, add:

```markdown
| `{{dashboardPort}}` | From `advanced.dashboardPort` (default: 3847). Port for the research dashboard SSE server. |
```

- [ ] **Step 4: Add dashboardPort to Section 8 wizard question list**

In `plugin/skills/engine-creator/SKILL.md`, line 171, find the exact string:

```
custom hooks, MCP server integrations.
```

Replace with:

```
dashboard port (1024-65535, default 3847), custom hooks, MCP server integrations.
```

- [ ] **Step 5: Update Template Reference table**

Add two new rows to the Template Reference table at the end of SKILL.md:

```markdown
| `dashboard-server.js.tmpl` | Dashboard SSE server (Node.js, zero dependencies) |
| `dashboard.html.tmpl` | Live research dashboard (self-contained HTML) |
```

- [ ] **Step 6: Commit**

```bash
git add plugin/skills/engine-creator/SKILL.md
git commit -m "feat: add Step 8f (dashboard files), dashboardPort placeholder rule, wizard question"
```

---

### Task 11: Add new test validation checks

**Files:**
- Modify: `plugin/commands/test-engine.md`

- [ ] **Step 1: Read the current test-engine.md to find the insertion point**

Find the line after check 4m (previously 4j, renumbered in Task 1): "No shared file writes."

- [ ] **Step 2: Add new checks 4n through 4r**

After the renamed check 4m, insert:

```markdown

**4n: Status protocol present.** Grep `skills/*/research-protocol.md` for "Incremental Write Protocol" and "Agent Status Protocol". Must find both.

**4o: Agent constraints present.** Grep all agent `.md` files in `agents/` for "Do NOT spawn sub-agents". Must find the phrase in every agent file.

**4p: Dashboard assets present.** Verify `dashboard-server.js` and `dashboard.html` exist in the engine's skill directory (`skills/*/`).

**4q: Pipeline status initialization.** Grep `skills/*/SKILL.md` for `_status/` directory creation and `_pipeline.json`. Must find both.

**4r: Output verification.** Grep `skills/*/SKILL.md` for "Phase 2 Output Verification" or "verify output". Must find at least one match.
```

- [ ] **Step 3: Update Check 1 (Plugin Structure)**

Add to the file existence checks in Check 1 (around line 31):

```markdown
- `skills/*/dashboard-server.js`
- `skills/*/dashboard.html`
```

- [ ] **Step 4: Commit**

```bash
git add plugin/commands/test-engine.md
git commit -m "feat: add test checks 4n-4r for observability and dashboard validation"
```

---

### Task 12: Regenerate patent-intelligence-engine example

**Files:**
- Modify: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md`
- Modify: `plugin/examples/patent-intelligence-engine/agents/*.md`

The example engine must reflect the new template output.

- [ ] **Step 1: Read the current example SKILL.md**

Read `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md`.

- [ ] **Step 2: Add Phase 0 status initialization and dashboard launch**

Mirror the changes from Task 5 into the example: add status directory creation, `_pipeline.json` initialization, phase transition protocol, and dashboard launch section after Phase 0's Derive Configuration block.

- [ ] **Step 3: Add Phase 2 Output Verification**

Mirror the changes from Task 6: add the verification section between Phase 2 and Phase 2.5.

- [ ] **Step 4: Add `_status/` to File Output Structure**

Add the `_status/` subtree to the example's file output structure section.

- [ ] **Step 5: Read the example research-protocol.md**

Read `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/research-protocol.md`.

- [ ] **Step 6: Add Incremental Write Protocol and Agent Status Protocol**

Mirror the changes from Tasks 2-3 into the example's research-protocol.md.

- [ ] **Step 7: Add Agent Constraints to each example agent file**

Read each agent file in `plugin/examples/patent-intelligence-engine/agents/` and append the Agent Constraints section from Task 4.

- [ ] **Step 8: Create example dashboard files**

Copy the dashboard-server.js.tmpl content to `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/dashboard-server.js`, substituting `{{dashboardPort}}` with `3847`. Copy dashboard.html.tmpl to `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/dashboard.html`.

- [ ] **Step 9: Commit**

```bash
git add plugin/examples/patent-intelligence-engine/
git commit -m "feat: regenerate patent-intelligence-engine example with observability features"
```

---

### Task 13: Update CHANGELOG and SKILL.md version

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Read the current CHANGELOG.md header**

Read the first 40 lines of `CHANGELOG.md` to see the latest version format.

- [ ] **Step 2: Add v1.8.0 changelog entry**

Insert a new `## [1.8.0]` section at the top (after the file header, before `## [1.7.0]`):

```markdown
## [1.8.0] - 2026-03-19

### Added
- **Incremental Write Protocol** -- agents now write findings to disk after each research question instead of accumulating all findings for a single write at the end. Prevents silent data loss when output exceeds the model's token limit
- **Agent Status Protocol** -- agents maintain structured JSON status files (`_status/[AgentID].json`) with real-time progress: questions completed, activity state, WebFetch budget usage, claims/sources counts
- **Live Research Dashboard** -- real-time web dashboard ("Dark Ops Console" aesthetic) showing pipeline phases, agent progress, and activity states. Node.js SSE server with `fs.watch` for instant updates. Launched automatically for Standard/Deep/Comprehensive tiers
- **Phase 2 Output Verification** -- orchestrator verifies agent output files exist and are non-empty before proceeding to synthesis. Classifies agents as HEALTHY/PARTIAL/FAILED/EMPTY and halts pipeline if all agents failed
- **Agent Constraints** -- explicit no-spawn rule prevents Phase 2 agents from creating sub-agents or background tasks, closing an uncontrolled recursion path
- **Pipeline state tracking** -- `_pipeline.json` tracks all phase transitions with tier-aware phase inclusion (VVC phases, comprehensive follow-up, provenance audit)
- `dashboardPort` advanced config option (default: 3847)
- Dashboard template files: `dashboard-server.js.tmpl`, `dashboard.html.tmpl`
- Test checks 4n-4r for observability validation

### Fixed
- Duplicate test check IDs (4h/4i/4j appeared twice) renumbered to 4k/4l/4m

### Changed
- Template count increased from 11 to 13 `.tmpl` files
- Patent Intelligence Engine example regenerated with observability features
```

- [ ] **Step 3: Update SKILL.md version**

In `plugin/skills/engine-creator/SKILL.md`, update the frontmatter `version` from `1.6.0` to `1.8.0`.

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md plugin/skills/engine-creator/SKILL.md
git commit -m "docs: update CHANGELOG for v1.8.0 observability features"
```

---

### Task 14: Final verification

- [ ] **Step 1: Run placeholder residue scan on templates**

```bash
grep -rn '{{[a-zA-Z0-9_-]*}}' plugin/skills/engine-creator/templates/dashboard-server.js.tmpl
```

Expected: only `{{dashboardPort}}` found. No other placeholders.

```bash
grep -rn '{{[a-zA-Z0-9_-]*}}' plugin/skills/engine-creator/templates/dashboard.html.tmpl
```

Expected: no matches (HTML has no placeholders).

- [ ] **Step 2: Verify JSON schemas are valid**

```bash
node -e "JSON.parse(require('fs').readFileSync('plugin/skills/engine-creator/templates/engine-config-schema.json', 'utf8')); console.log('PASS')"
node -e "JSON.parse(require('fs').readFileSync('plugin/skills/engine-creator/templates/preset-schema.json', 'utf8')); console.log('PASS')"
```

- [ ] **Step 3: Verify all template files exist**

```bash
ls -la plugin/skills/engine-creator/templates/*.tmpl plugin/skills/engine-creator/templates/*.json | wc -l
```

Expected: 16 files (13 `.tmpl` + 3 `.json`).

- [ ] **Step 4: Verify example engine dashboard files exist**

```bash
ls plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/dashboard-server.js plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/dashboard.html
```

Expected: both files exist.

- [ ] **Step 5: Run grep checks matching test-engine expectations**

```bash
grep -l "Incremental Write Protocol" plugin/skills/engine-creator/templates/research-protocol.md.tmpl
grep -l "Agent Status Protocol" plugin/skills/engine-creator/templates/research-protocol.md.tmpl
grep -l "Do NOT spawn sub-agents" plugin/skills/engine-creator/templates/agent-template.md.tmpl
grep -l "_pipeline.json" plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl
grep -l "Phase 2 Output Verification" plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl
```

Expected: all 5 greps return a match.
