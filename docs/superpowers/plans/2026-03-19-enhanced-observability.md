# Enhanced Observability — Implementation Plan (Plan B)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the research dashboard from a basic progress-bar view to a full observability console with per-question tracking, structured claims, append-only action logs, expandable agent cards with tabbed detail views, phase duration display, and a dedicated VVC verification panel.

**Architecture:** Five template files modified (protocol markdown + JS server + HTML dashboard), plus the patent-intelligence-engine example regenerated. All changes are runtime protocol instructions (for agents) and client/server code (for the dashboard). No Python code, no new dependencies.

**Tech Stack:** Markdown templates (agent protocol instructions), vanilla JS + HTML/CSS (dashboard), Node.js stdlib (server). Zero external dependencies.

**Spec:** `docs/superpowers/specs/2026-03-19-deterministic-generator-design.md` (Section 7: 7a through 7i)

---

## File Structure

```
plugin/skills/engine-creator/templates/
├── research-protocol.md.tmpl           # MODIFY — questions array, currentAction, claims JSON, action log
├── orchestrator-skill.md.tmpl          # MODIFY — phase startedAt/completedAt timestamps
├── vvc-pipeline.md.tmpl               # MODIFY — VVC verification JSON writing protocol
├── dashboard-server.js.tmpl           # MODIFY — read claims/log/VVC, /api/agent/:id/log, SSE capping
└── dashboard.html.tmpl               # MODIFY — full UI overhaul (question tracker, tabs, VVC panel)

plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/
├── research-protocol.md               # MODIFY — apply template changes
├── SKILL.md                           # MODIFY — apply template changes (phase transitions)
├── vvc-pipeline.md                    # MODIFY — apply template changes
├── dashboard-server.js                # MODIFY — apply template changes
└── dashboard.html                     # MODIFY — apply template changes
```

---

### Task 1: Update research-protocol.md.tmpl — status model, claims JSON, action log

**Files:**
- Modify: `plugin/skills/engine-creator/templates/research-protocol.md.tmpl`

**Spec sections:** 7a (Live Action Tracking), 7b (Structured Claims Tracking), 7c (Append-Only Action Log), 7h (Data Model Changes — questions array)

- [ ] **Step 1: Read the current template**

Read `plugin/skills/engine-creator/templates/research-protocol.md.tmpl` in full to confirm line numbers for edits.

- [ ] **Step 2: Replace the Status JSON Schema (lines 116-134)**

Replace the existing status JSON schema block with the v1.9.0 schema from spec Section 7h. Key changes:
- Remove `currentQuestion`, `questionsCompleted`, `questionsTotal` fields
- Add `currentAction` field (string, max ~120 chars)
- Add `questions` array with per-question objects (`text`, `status`, `startedAt`, `completedAt`, `durationMs`)
- Add `errors` and `aborts` counter fields
- Keep all existing fields (`agentId`, `engineId`, `phase`, `status`, `activity`, `webFetchesUsed`, `webFetchCap`, `claimsFound`, `sourcesCollected`, `iterationPass`, `maxIterations`, `lastUpdated`)

New schema block:

```json
{
  "agentId": "[AgentID]",
  "engineId": "${ENGINE_ID}",
  "phase": 2,
  "status": "researching | writing | assessing | refining | complete | error",
  "currentAction": "Searching 'solid-state battery cathode 2024'",
  "activity": "searching | assessing | refining | writing | idle",
  "questions": [
    {
      "text": "The research question text",
      "status": "complete | active | pending",
      "startedAt": "ISO-8601 timestamp or null",
      "completedAt": "ISO-8601 timestamp or null",
      "durationMs": 102000
    }
  ],
  "webFetchesUsed": 4,
  "webFetchCap": 10,
  "claimsFound": 7,
  "sourcesCollected": 4,
  "iterationPass": 2,
  "maxIterations": 3,
  "errors": 0,
  "aborts": 0,
  "lastUpdated": "ISO-8601 timestamp"
}
```

- [ ] **Step 3: Replace "When to Write Status" rules (lines 136-146)**

Replace the existing rules with expanded rules from spec Section 7a. New rules:

```markdown
### When to Write Status

- On agent start: status "researching", initialize questions array with all assigned
  questions (status "pending"), set first question to "active" with startedAt timestamp,
  activity "searching", errors 0, aborts 0
- Before each WebSearch call: update currentAction to the search query string
  (e.g., "Searching 'solid-state battery cathode patent 2024'")
- Before each WebFetch call: update currentAction to the URL being fetched
  (e.g., "Fetching https://patents.google.com/patent/US20240123456")
- After each Search pass: update activity to "searching"
- During assessment: update currentAction to what is being assessed
  (e.g., "Assessing claim C-03 against 2 sources")
- After each Assess pass: update activity to "assessing"
- During refinement: update currentAction to the refinement query
  (e.g., "Refining: searching for contradictory evidence on cathode materials")
- After each Refine pass: update activity to "refining"
- After writing files for a completed question: set the question's status to "complete"
  with completedAt and durationMs, set next question to "active" with startedAt,
  update claimsFound and sourcesCollected totals, activity "writing"
- On error: increment errors counter, status "error" if fatal, add "message" field
- On abort: increment aborts counter, log abort reason
- On completion of all questions: status "complete", activity "idle"
```

- [ ] **Step 4: Add claims JSON writing to Incremental Write Protocol (after line 88)**

After the existing step 5 ("OVERWRITE status JSON to `BASE_DIR/_status/[AgentID].json`"), add step 6:

```markdown
6. OVERWRITE claims status to `BASE_DIR/_status/[AgentID]_claims.json` with all claims
   discovered so far (cumulative, not per-question). Each claim is a JSON object:
   `{"id": "C-01", "text": "...", "confidence": "HIGH|MEDIUM|LOW|SPECULATIVE|null",
    "status": "pending|under_investigation|investigated", "sourceCount": 2,
    "question": "The originating research question"}`
   The file is a JSON array of these objects. On first write, create as `[]` then populate.
```

- [ ] **Step 5: Add Action Logging Protocol section**

After the "Agent Status Protocol" section (after the "When to Write Status" rules), insert a new section:

```markdown
---

## Action Logging Protocol

Maintain an append-only action log at `BASE_DIR/_status/[AgentID]_log.json`.
This file is a JSON array. Append new entries after each significant action.

Log these events:
- Before starting each research question: type "start"
- After each WebSearch call: type "search" with query and result count
- After each WebFetch call: type "fetch" with URL and status (success/403_blocked/timeout/error)
- When a new claim is identified: type "claim" with ID, text, initial confidence
- When assessing a claim: type "assess" with claim ID and result
- After writing files to disk: type "write" with file list and counts
- After completing a research question: type "question_complete" with totals
- On error or abort: type "error" or "abort" with message/reason

Each entry includes a timestamp. The log is append-only — never overwrite or truncate.
On agent start, create the file with an empty array `[]`. Append by reading the current
array, pushing the new entry, and writing back.

**Size limit:** Cap the log at 500 entries per agent. If the array exceeds 500 entries,
drop the oldest entries to stay within the limit.

### Log Entry Schema

```json
{
  "type": "start | search | fetch | claim | assess | write | question_complete | error | abort",
  "timestamp": "ISO-8601 timestamp",
  // type-specific fields:
  // start: "question", "questionIndex"
  // search: "query", "engine", "resultCount"
  // fetch: "url", "status" (success/403_blocked/timeout/error)
  // claim: "claimId", "text", "confidence"
  // assess: "claimId", "result", "sourcesChecked"
  // write: "files", "claimsAdded", "sourcesAdded"
  // question_complete: "question", "questionIndex", "claimsTotal", "sourcesTotal"
  // error: "message"
  // abort: "reason"
}
```
```

- [ ] **Step 6: Update File Isolation Protocol (line 149-177)**

Add the new status files to the per-agent output files list:

```markdown
- Status: `BASE_DIR/_status/[AgentID].json`
- Claims status: `BASE_DIR/_status/[AgentID]_claims.json`
- Action log: `BASE_DIR/_status/[AgentID]_log.json`
```

- [ ] **Step 7: Verify the template**

```bash
# Verify new sections exist
grep -c "Action Logging Protocol" plugin/skills/engine-creator/templates/research-protocol.md.tmpl
# Expected: 1

grep -c "currentAction" plugin/skills/engine-creator/templates/research-protocol.md.tmpl
# Expected: at least 4 (schema + 3 "When to Write" rules)

grep -c "_claims.json" plugin/skills/engine-creator/templates/research-protocol.md.tmpl
# Expected: at least 2

grep -c "questions" plugin/skills/engine-creator/templates/research-protocol.md.tmpl
# Expected: at least 3 (schema array + status rules)

# Verify no stale fields remain
grep -c "questionsCompleted" plugin/skills/engine-creator/templates/research-protocol.md.tmpl
# Expected: 0

grep -c "questionsTotal" plugin/skills/engine-creator/templates/research-protocol.md.tmpl
# Expected: 0
```

- [ ] **Step 8: Commit**

```bash
git add plugin/skills/engine-creator/templates/research-protocol.md.tmpl
git commit -m "feat: add questions array, currentAction, claims JSON, and action logging to research protocol template"
```

---

### Task 2: Update orchestrator-skill.md.tmpl — phase timing

**Files:**
- Modify: `plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl`

**Spec section:** 7h (Data Model Changes — phase timing)

- [ ] **Step 1: Read the current template**

Read `plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl` in full to confirm line numbers.

- [ ] **Step 2: Add startedAt/completedAt to _pipeline.json initial state (lines 66-78)**

Add `startedAt` and `completedAt` fields to each phase object template. In the phases array documentation (lines 80-97), update the description to note that each phase object includes:

```json
{
  "phase": 0,
  "label": "Tier Detection",
  "status": "complete",
  "startedAt": "ISO-8601 timestamp",
  "completedAt": "ISO-8601 timestamp"
}
```

All phases start with `startedAt: null` and `completedAt: null` except Phase 0 which gets both set at init time.

- [ ] **Step 3: Update Phase Transition Protocol (lines 99-107)**

Replace the existing Phase Transition Protocol with timing-aware version:

```markdown
### Phase Transition Protocol

Before each phase begins, update `_pipeline.json`:
- Set `currentPhase` and `phaseLabel` to the new phase
- Set the phase's status to `"in_progress"`
- Set the phase's `startedAt` to the current ISO-8601 timestamp
- Update `lastUpdated` timestamp

After each phase completes:
- Set the phase's status to `"complete"`
- Set the phase's `completedAt` to the current ISO-8601 timestamp
- Update `lastUpdated` timestamp
```

- [ ] **Step 4: Update File Output Structure (lines 244-264)**

Add the new status files to the `_status/` directory listing:

```
├── _status/
│   ├── _pipeline.json
│   ├── [AgentID].json                              # Per-agent status
│   ├── [AgentID]_claims.json                       # Per-agent claims (new)
│   ├── [AgentID]_log.json                          # Per-agent action log (new)
│   ├── vvc-specialist_verification.json            # VVC verdicts (new, Phase 5-6)
│   ├── server.js                                   # Dashboard server
│   └── dashboard.html                              # Dashboard UI
```

- [ ] **Step 5: Verify**

```bash
grep -c "startedAt" plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl
# Expected: at least 3 (initial state + transition start + transition complete)

grep -c "completedAt" plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl
# Expected: at least 3

grep -c "_claims.json" plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl
# Expected: at least 1 (in file structure)

grep -c "_log.json" plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl
# Expected: at least 1 (in file structure)
```

- [ ] **Step 6: Commit**

```bash
git add plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl
git commit -m "feat: add startedAt/completedAt timestamps to phase transitions and updated file structure"
```

---

### Task 3: Update vvc-pipeline.md.tmpl — VVC verification JSON writing

**Files:**
- Modify: `plugin/skills/engine-creator/templates/vvc-pipeline.md.tmpl`

**Spec section:** 7i (VVC Verification Panel — data flow)

- [ ] **Step 1: Read the current template**

Read `plugin/skills/engine-creator/templates/vvc-pipeline.md.tmpl` in full.

- [ ] **Step 2: Add VVC Verification Status Protocol section**

After the `## Phase 5: VVC-Verify` placeholder block (`{{vvcVerifyPhaseBlock}}`), before `## Phase 6: VVC-Correct`, insert a new section:

```markdown
---

## VVC Verification Status Protocol

Maintain a verification status file at `BASE_DIR/_status/vvc-specialist_verification.json`.
This file enables real-time dashboard tracking of the VVC verification and correction process.

### Initial Write (Phase 5 start)

After extracting all [VC]-tagged claims from the draft report, write the initial verification file:

```json
{
  "phase": 5,
  "mode": "full | verify-only",
  "totalClaims": 47,
  "verified": 0,
  "claims": [
    {
      "id": "VC-01",
      "text": "Claim text from draft report",
      "confidence": "HIGH",
      "sourceUrl": null,
      "sourceQuote": null,
      "verdict": null,
      "recommendation": null,
      "correctedText": null,
      "correctionApplied": null
    }
  ],
  "lastUpdated": "ISO-8601 timestamp"
}
```

Set `mode` to `"full"` if Phase 6 will run, `"verify-only"` if this tier skips Phase 6.

### Per-Claim Updates (Phase 5)

After verifying each claim, OVERWRITE the file with the updated claims array:
- Set the claim's `verdict` (CONFIRMED | PARAPHRASED | OVERSTATED | UNDERSTATED | DISPUTED | UNSUPPORTED | SOURCE_UNAVAILABLE)
- Set the claim's `recommendation` (KEEP | REVISE | DOWNGRADE | REMOVE | REPLACE_SOURCE)
- Set `sourceUrl` and `sourceQuote` with the verification evidence
- Set `correctedText` if recommendation is REVISE or DOWNGRADE
- Increment the top-level `verified` counter
- Update `lastUpdated`

**Write one claim at a time** — overwrite after each individual claim verification, not in batch. This drives live dashboard updates.

### Phase 6 Updates (Correction)

During Phase 6, update each claim's `correctionApplied` field as corrections are applied:
- `"applied"` — correction was applied to the report
- `"kept"` — claim was kept unchanged (verdict was CONFIRMED/PARAPHRASED)
- `"removed"` — claim was removed from the report

Set `phase` to `6` when Phase 6 begins.

### Verify-Only Mode

If `mode` is `"verify-only"` (Standard tier), Phase 6 does not run. After Phase 5 completes, set `correctionApplied` to `"skipped"` for all claims.
```

- [ ] **Step 3: Verify**

```bash
grep -c "vvc-specialist_verification.json" plugin/skills/engine-creator/templates/vvc-pipeline.md.tmpl
# Expected: at least 1

grep -c "correctionApplied" plugin/skills/engine-creator/templates/vvc-pipeline.md.tmpl
# Expected: at least 3

grep -c "VVC Verification Status Protocol" plugin/skills/engine-creator/templates/vvc-pipeline.md.tmpl
# Expected: 1
```

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/engine-creator/templates/vvc-pipeline.md.tmpl
git commit -m "feat: add VVC verification JSON writing protocol for dashboard integration"
```

---

### Task 4: Update dashboard-server.js.tmpl — claims, log, VVC, new endpoint

**Files:**
- Modify: `plugin/skills/engine-creator/templates/dashboard-server.js.tmpl`

**Spec sections:** 7e (Dashboard Server Changes), 7i (VVC data flow)

- [ ] **Step 1: Read the current template**

Read `plugin/skills/engine-creator/templates/dashboard-server.js.tmpl` in full. Current file is 114 lines.

- [ ] **Step 2: Replace the getStatus() function (lines 25-37)**

Replace the existing `getStatus()` function with the expanded version from spec Section 7e. The new version:
- Skips `_claims` and `_log` files when matching agent status files
- Attaches `claims` and `log` data to each agent object
- Reads `vvc-specialist_verification.json` and attaches as `vvc` key
- For SSE broadcasts, caps the log to the last 50 entries per agent

```javascript
function getStatus(capLog) {
  const pipeline = readJsonSafe(PIPELINE_FILE);
  const agents = {};
  const vvcFile = path.join(STATUS_DIR, 'vvc-specialist_verification.json');
  try {
    for (const file of fs.readdirSync(STATUS_DIR)) {
      if (file.endsWith('.json') && !file.startsWith('_')) {
        if (!file.includes('_claims') && !file.includes('_log') && !file.includes('_verification')) {
          const agentId = file.replace('.json', '');
          const data = readJsonSafe(path.join(STATUS_DIR, file));
          if (data) {
            data.claims = readJsonSafe(path.join(STATUS_DIR, `${agentId}_claims.json`)) || [];
            const fullLog = readJsonSafe(path.join(STATUS_DIR, `${agentId}_log.json`)) || [];
            data.log = capLog ? fullLog.slice(-50) : fullLog;
            agents[agentId] = data;
          }
        }
      }
    }
  } catch { /* directory read failed */ }
  const vvc = readJsonSafe(vvcFile) || null;
  return { pipeline, agents, vvc };
}
```

- [ ] **Step 3: Update broadcastStatus() to use capped log (line 41-55)**

Change the `getStatus()` call in `broadcastStatus()` to pass `true` for the `capLog` parameter:

```javascript
function broadcastStatus() {
  const status = getStatus(true);  // cap log to last 50 entries for SSE
```

- [ ] **Step 4: Update /api/status handler to pass full log (line 77-83)**

Change the `getStatus()` call in the `/api/status` handler to pass `false`:

```javascript
res.end(JSON.stringify(getStatus(false)));
```

- [ ] **Step 5: Update /api/events handler to pass capped log (line 83-92)**

Change the initial SSE push to use capped log:

```javascript
res.write(`data: ${JSON.stringify(getStatus(true))}\n\n`);
```

- [ ] **Step 6: Add GET /api/agent/:id/log endpoint**

Before the 404 handler (line 93-96), add a new route:

```javascript
  } else if (req.url.startsWith('/api/agent/') && req.url.endsWith('/log')) {
    const agentId = req.url.replace('/api/agent/', '').replace('/log', '');
    const logFile = path.join(STATUS_DIR, `${agentId}_log.json`);
    const logData = readJsonSafe(logFile) || [];
    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*'
    });
    res.end(JSON.stringify(logData));
  } else {
```

- [ ] **Step 7: Verify**

```bash
# Check all new features present
grep -c "capLog" plugin/skills/engine-creator/templates/dashboard-server.js.tmpl
# Expected: at least 3

grep -c "_claims.json" plugin/skills/engine-creator/templates/dashboard-server.js.tmpl
# Expected: at least 1

grep -c "_log.json" plugin/skills/engine-creator/templates/dashboard-server.js.tmpl
# Expected: at least 2

grep -c "verification.json" plugin/skills/engine-creator/templates/dashboard-server.js.tmpl
# Expected: at least 1

grep -c "/api/agent/" plugin/skills/engine-creator/templates/dashboard-server.js.tmpl
# Expected: at least 1

# Verify valid JS syntax
node -e "
const fs = require('fs');
const src = fs.readFileSync('plugin/skills/engine-creator/templates/dashboard-server.js.tmpl', 'utf8');
const replaced = src.replace(/\{\{dashboardPort\}\}/g, '3847');
try { new Function(replaced); console.log('SYNTAX OK'); } catch(e) { console.log('SYNTAX ERROR:', e.message); }
"
```

- [ ] **Step 8: Commit**

```bash
git add plugin/skills/engine-creator/templates/dashboard-server.js.tmpl
git commit -m "feat: add claims/log/VVC reading, /api/agent/:id/log endpoint, SSE log capping to dashboard server"
```

---

### Task 5: Rewrite dashboard.html.tmpl — full UI overhaul

**Files:**
- Modify: `plugin/skills/engine-creator/templates/dashboard.html.tmpl`

**Spec sections:** 7d (Dashboard UI Enhancements), 7i (VVC Verification Panel)

This is the largest task — a complete rewrite of the 930-line dashboard HTML. The implementer MUST read the existing file first and preserve the design system (CSS custom properties, fonts, animations, Dark Ops Console aesthetic).

#### Sub-step A: CSS additions

- [ ] **Step 1: Read the existing dashboard.html.tmpl**

Read `plugin/skills/engine-creator/templates/dashboard.html.tmpl` in full. Note the design system:
- CSS custom properties (lines 13-28): `--bg-deep`, `--bg-surface`, `--border`, `--accent-*` colors
- Fonts: `Departure Mono` (display), `IBM Plex Mono` (body)
- Existing component styles: header, pipeline, agent cards, progress bar, WebFetch meter, stats row

- [ ] **Step 2: Add new CSS for aggregate stats bar**

After the `.header-time .elapsed-value` rule (around line 112), add styles for:

```css
/* ── Aggregate Stats Bar ────────────────────────── */

.stats-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 24px;
  border-bottom: 1px solid var(--border);
  font-family: var(--font-body);
  font-size: 0.75rem;
  color: var(--text-muted);
  flex-wrap: wrap;
}

.stats-bar .stat-value {
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.stats-bar .stat-separator {
  color: var(--border-active);
}
```

- [ ] **Step 3: Add CSS for question tracker**

Replace the existing progress bar CSS (`.progress-row`, `.progress-track`, `.progress-fill`, `.progress-text` — lines 316-346) with question tracker styles:

```css
/* ── Question Tracker ──────────────────────────── */

.question-list {
  list-style: none;
  margin-bottom: 10px;
}

.question-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 3px 0;
  font-family: var(--font-body);
  font-size: 0.72rem;
  line-height: 1.4;
}

.question-icon {
  flex-shrink: 0;
  width: 14px;
  text-align: center;
  font-size: 0.7rem;
}

.question-icon.complete { color: var(--accent-complete); }
.question-icon.active { color: var(--accent-search); animation: pulse-text 2s ease-in-out infinite; }
.question-icon.pending { color: var(--text-muted); }

@keyframes pulse-text {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.question-text {
  flex: 1;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.question-item.active .question-text { color: var(--text-primary); }

.question-duration {
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
  color: var(--text-muted);
  font-size: 0.65rem;
}

.question-action {
  padding-left: 22px;
  font-size: 0.65rem;
  color: var(--accent-search);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  opacity: 0.8;
}
```

- [ ] **Step 4: Add CSS for expandable cards, tabs, and error badges**

After the question tracker CSS, add:

```css
/* ── Expandable Cards ──────────────────────────── */

.expand-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: var(--font-body);
  font-size: 0.65rem;
  color: var(--text-muted);
  cursor: pointer;
  border: none;
  background: none;
  padding: 4px 0;
  margin-top: 6px;
}

.expand-toggle:hover { color: var(--text-primary); }

.agent-detail {
  display: none;
  margin-top: 10px;
  border-top: 1px solid var(--border);
  padding-top: 10px;
}

.agent-card.expanded .agent-detail { display: block; }

.tab-bar {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 10px;
}

.tab-btn {
  font-family: var(--font-body);
  font-size: 0.7rem;
  color: var(--text-muted);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 6px 12px;
  cursor: pointer;
  transition: color 200ms, border-color 200ms;
}

.tab-btn:hover { color: var(--text-primary); }
.tab-btn.active { color: var(--text-primary); border-bottom-color: var(--accent-search); }

.tab-panel { display: none; }
.tab-panel.active { display: block; }

/* ── Error Badge ────────────────────────────────── */

.error-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  font-family: var(--font-body);
  font-size: 0.6rem;
  color: var(--accent-error);
  background: var(--bg-deep);
  border: 1px solid var(--accent-error);
  border-radius: 8px;
  padding: 1px 6px;
  white-space: nowrap;
}

.agent-card { position: relative; }
```

- [ ] **Step 5: Add CSS for Claims tab table**

```css
/* ── Claims Table ──────────────────────────────── */

.claims-table {
  width: 100%;
  font-family: var(--font-body);
  font-size: 0.68rem;
  border-collapse: collapse;
}

.claims-table th {
  text-align: left;
  color: var(--text-muted);
  font-weight: 500;
  padding: 4px 8px;
  border-bottom: 1px solid var(--border);
  text-transform: uppercase;
  font-size: 0.6rem;
  letter-spacing: 0.05em;
}

.claims-table td {
  padding: 4px 8px;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.claim-pill {
  display: inline-block;
  font-size: 0.6rem;
  padding: 1px 6px;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.claim-pill.pending { background: var(--border); color: var(--text-muted); }
.claim-pill.under_investigation { background: rgba(245,158,11,0.2); color: var(--accent-assess); }
.claim-pill.investigated { background: rgba(74,222,128,0.2); color: var(--accent-complete); }
```

- [ ] **Step 6: Add CSS for Activity Log tab**

```css
/* ── Activity Log ──────────────────────────────── */

.log-feed {
  max-height: 300px;
  overflow-y: auto;
  font-family: var(--font-body);
  font-size: 0.68rem;
}

.log-entry {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px solid var(--border);
}

.log-icon {
  flex-shrink: 0;
  width: 14px;
  text-align: center;
  font-size: 0.65rem;
}

.log-icon.search, .log-icon.fetch { color: var(--accent-search); }
.log-icon.claim, .log-icon.write { color: var(--accent-complete); }
.log-icon.assess { color: var(--accent-assess); }
.log-icon.error, .log-icon.abort { color: var(--accent-error); }
.log-icon.question_complete { color: var(--accent-complete); }
.log-icon.start { color: var(--accent-refine); }

.log-text {
  flex: 1;
  color: var(--text-primary);
  word-break: break-word;
}

.log-time {
  flex-shrink: 0;
  color: var(--text-muted);
  font-size: 0.6rem;
  font-variant-numeric: tabular-nums;
}

.log-query {
  font-family: var(--font-display);
  font-size: 0.62rem;
  color: var(--accent-search);
  opacity: 0.8;
}

.log-status-badge {
  display: inline-block;
  font-size: 0.55rem;
  padding: 0 4px;
  border-radius: 2px;
  text-transform: uppercase;
}

.log-status-badge.success { background: rgba(74,222,128,0.2); color: var(--accent-complete); }
.log-status-badge.blocked { background: rgba(251,113,133,0.2); color: var(--accent-error); }
.log-status-badge.timeout { background: rgba(245,158,11,0.2); color: var(--accent-assess); }
```

- [ ] **Step 7: Add CSS for phase duration display**

After the `.phase-label` rule (around line 213), add:

```css
.phase-duration {
  font-family: var(--font-body);
  font-size: 0.55rem;
  color: var(--text-muted);
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.phase-duration.active {
  color: var(--accent-search);
}
```

- [ ] **Step 8: Add CSS for VVC Verification Panel**

```css
/* ── VVC Panel ─────────────────────────────────── */

.vvc-panel {
  padding: 24px;
  border-bottom: 1px solid var(--border);
}

.vvc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.vvc-title {
  font-family: var(--font-display);
  font-size: 1rem;
  color: var(--text-primary);
  letter-spacing: 0.02em;
}

.vvc-phase-info {
  font-family: var(--font-body);
  font-size: 0.75rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.vvc-mode {
  font-family: var(--font-body);
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.vvc-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  font-family: var(--font-body);
  font-size: 0.72rem;
  flex-wrap: wrap;
}

.vvc-progress-track {
  flex: 1;
  min-width: 200px;
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}

.vvc-progress-fill {
  height: 100%;
  background: var(--accent-search);
  border-radius: 3px;
  transition: width 400ms ease;
}

.vvc-verdict-counts {
  font-family: var(--font-body);
  font-size: 0.68rem;
  color: var(--text-muted);
  margin-bottom: 16px;
}

.vvc-table {
  width: 100%;
  font-family: var(--font-body);
  font-size: 0.68rem;
  border-collapse: collapse;
}

.vvc-table th {
  text-align: left;
  color: var(--text-muted);
  font-weight: 500;
  padding: 6px 8px;
  border-bottom: 1px solid var(--border);
  text-transform: uppercase;
  font-size: 0.6rem;
  letter-spacing: 0.05em;
}

.vvc-table td {
  padding: 6px 8px;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
}

.vvc-table tr { cursor: pointer; }
.vvc-table tr:hover { background: rgba(255,255,255,0.02); }

.vvc-row-detail {
  display: none;
  padding: 8px 8px 8px 40px;
  font-size: 0.65rem;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
  background: rgba(0,0,0,0.15);
}

.vvc-row-detail.visible { display: table-row; }

.verdict-badge {
  display: inline-block;
  font-size: 0.6rem;
  padding: 1px 6px;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.verdict-badge.confirmed, .verdict-badge.paraphrased { color: var(--accent-complete); }
.verdict-badge.overstated, .verdict-badge.understated { color: var(--accent-assess); }
.verdict-badge.disputed, .verdict-badge.unsupported { color: var(--accent-error); }
.verdict-badge.source_unavailable { color: var(--accent-error); opacity: 0.7; }

.applied-badge {
  display: inline-block;
  font-size: 0.6rem;
  padding: 1px 6px;
  border-radius: 3px;
}

.applied-badge.kept { color: var(--accent-complete); }
.applied-badge.applied { color: var(--accent-assess); }
.applied-badge.removed { color: var(--accent-error); }
.applied-badge.applying { color: var(--accent-search); animation: pulse-text 2s ease-in-out infinite; }
```

- [ ] **Step 9: Add CSS for collapsible legend**

```css
/* ── Legend ─────────────────────────────────────── */

.legend-toggle {
  font-family: var(--font-display);
  font-size: 0.75rem;
  color: var(--text-muted);
  cursor: pointer;
  border: 1px solid var(--border);
  background: none;
  width: 24px;
  height: 24px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.legend-toggle:hover { color: var(--text-primary); border-color: var(--border-active); }

.legend-panel {
  display: none;
  position: absolute;
  top: 100%;
  right: 0;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 12px 16px;
  z-index: 10;
  min-width: 300px;
  font-family: var(--font-body);
  font-size: 0.68rem;
  color: var(--text-muted);
}

.legend-panel.visible { display: block; }

.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
}

.legend-swatch {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}

.legend-label {
  flex-shrink: 0;
  min-width: 60px;
  font-weight: 500;
  color: var(--text-primary);
}
```

- [ ] **Step 10: Add WebFetch meter label update**

Update the existing `.wf-label` style (around line 359) — no change needed to the CSS, but note that the JS will change "WF" to "Web Fetches" as the label text.

#### Sub-step B: HTML structure changes

- [ ] **Step 11: Update header HTML to include legend and aggregate stats bar**

Replace the header HTML (lines 522-530) with:

```html
<header class="header" id="header" style="position:relative">
  <span class="header-title" id="engine-name">---</span>
  <span class="header-topic" id="topic">---</span>
  <span class="tier-badge" id="tier-badge">---</span>
  <span class="header-time">
    <span class="live-timer"><span class="elapsed-value" id="elapsed">00:00:00</span></span>
    <span class="complete-label" id="complete-label">RESEARCH COMPLETE <span id="final-time"></span></span>
  </span>
  <button class="legend-toggle" id="legend-toggle" title="Legend">?</button>
  <div class="legend-panel" id="legend-panel">
    <!-- Legend content rendered by JS -->
  </div>
</header>

<div class="stats-bar" id="stats-bar">
  Claims: <span class="stat-value" id="agg-claims">0</span>
  <span class="stat-separator">|</span>
  Sources: <span class="stat-value" id="agg-sources">0</span>
  <span class="stat-separator">|</span>
  Web Fetches: <span class="stat-value" id="agg-fetches">0/0</span>
</div>
```

- [ ] **Step 12: Add VVC panel and agent card sections to HTML body**

After the pipeline section, before the footer, replace the agents section (lines 541-545) with:

```html
<section class="vvc-panel" id="vvc-panel" style="display:none">
  <!-- VVC Verification Panel rendered by JS -->
</section>

<section class="agents-section" id="agents-section">
  <div class="agents-grid" id="agents-grid">
    <!-- Agent cards rendered dynamically -->
  </div>
</section>
```

#### Sub-step C: JavaScript rewrite

- [ ] **Step 13: Update state and DOM refs**

At the top of the script IIFE (after line 562), add new state variables:

```javascript
let expandedCards = {};   // agentId -> boolean
let activeTabMap = {};    // agentId -> tab name ('claims'|'log'|'sources')
let fullLogCache = {};    // agentId -> full log array (loaded on tab open)
```

Add new DOM refs:

```javascript
const statsBarEl = $("stats-bar");
const aggClaimsEl = $("agg-claims");
const aggSourcesEl = $("agg-sources");
const aggFetchesEl = $("agg-fetches");
const vvcPanelEl = $("vvc-panel");
const agentsSectionEl = $("agents-section");
const legendToggleEl = $("legend-toggle");
const legendPanelEl = $("legend-panel");
```

- [ ] **Step 14: Add phase duration formatting helpers**

Add helper functions:

```javascript
function formatDurationMs(ms) {
  if (!ms && ms !== 0) return "";
  var s = Math.floor(ms / 1000);
  var m = Math.floor(s / 60);
  s = s % 60;
  if (m > 0) return m + "m " + String(s).padStart(2, "0") + "s";
  return s + "s";
}

function formatDurationFromTo(from, to) {
  if (!from) return "";
  var end = to ? new Date(to).getTime() : Date.now();
  return formatDurationMs(end - new Date(from).getTime());
}

function relativeTime(isoStr) {
  if (!isoStr) return "";
  var diff = Math.max(0, Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000));
  if (diff < 60) return diff + "s ago";
  if (diff < 3600) return Math.floor(diff / 60) + "m ago";
  return Math.floor(diff / 3600) + "h ago";
}
```

- [ ] **Step 15: Update renderPipeline() to show phase durations**

Modify the `renderPipeline()` function (lines 632-658) to include duration below each phase label:

- For `complete` phases: show fixed duration from `startedAt` to `completedAt`
- For `in_progress` phases: show live counter from `startedAt` (CSS class `active`)
- For `pending` phases: show nothing

Add duration HTML after the phase label div:

```javascript
var durationHtml = '';
if (status === 'complete' && p.startedAt && p.completedAt) {
  durationHtml = '<div class="phase-duration">' + formatDurationFromTo(p.startedAt, p.completedAt) + '</div>';
} else if (status === 'in_progress' && p.startedAt) {
  durationHtml = '<div class="phase-duration active" data-started="' + p.startedAt + '">' + formatDurationFromTo(p.startedAt, null) + '</div>';
}
```

- [ ] **Step 16: Rewrite buildAgentCard() for question tracker + expandable tabs**

Replace the existing `buildAgentCard()` function (lines 694-722) with the new version. The new card layout:

1. Header: agent ID + activity badge + error badge (if errors > 0)
2. Question tracker: list of questions with status icons, text, durations
3. Current action line under the active question
4. WebFetch meter with full "Web Fetches" label
5. Stats row: claims + sources counts
6. Expand toggle button
7. Hidden detail div with 3 tabs: Claims, Activity Log, Sources

Key implementation details:
- Question status icons: complete = green checkmark, active = cyan pulsing dot, pending = gray circle
- Error badge only appears if `a.errors > 0` or `a.aborts > 0`
- Expand toggle text: "expand" when collapsed, "collapse" when expanded
- Use `expandedCards[id]` to persist expand state across re-renders

- [ ] **Step 17: Rewrite updateAgentCard() for question tracker updates**

Replace the existing `updateAgentCard()` function (lines 725-776) to handle:
- Updating question status icons and durations
- Updating the current action text under the active question
- Updating WebFetch meter blocks
- Updating claims count, sources count
- Updating error badge count
- Updating expanded tab content if the card is expanded

- [ ] **Step 18: Add tab rendering functions**

Add functions for rendering each tab's content:

```javascript
function renderClaimsTab(id, claims) { ... }
function renderLogTab(id, log) { ... }
function renderSourcesTab(id, log) { ... }
```

- `renderClaimsTab`: Builds the claims table with ID, Text, Confidence badge, Status pill, Sources count. Count header shows breakdown by status.
- `renderLogTab`: Builds the scrollable log feed. Each entry has icon (colored by type), text, and relative timestamp. Search entries show the query in monospace. Fetch entries show URL + status badge. `question_complete` entries show as green dividers.
- `renderSourcesTab`: Extracts `fetch` entries from the log, groups by status (success first), shows URL + status badge. Source count header.

- [ ] **Step 19: Add expand/collapse and tab switching handlers**

Add event delegation on `agentsGridEl`:

```javascript
agentsGridEl.addEventListener('click', function(e) {
  // Expand toggle
  var toggle = e.target.closest('.expand-toggle');
  if (toggle) {
    var cardId = toggle.dataset.agent;
    expandedCards[cardId] = !expandedCards[cardId];
    var card = document.getElementById('card-' + cardId);
    if (card) {
      card.classList.toggle('expanded', expandedCards[cardId]);
      toggle.textContent = expandedCards[cardId] ? '▼ collapse' : '▶ expand';
    }
    // Load full log on first expand
    if (expandedCards[cardId] && !fullLogCache[cardId]) {
      fetch('/api/agent/' + cardId + '/log')
        .then(function(r) { return r.json(); })
        .then(function(data) {
          fullLogCache[cardId] = data;
          // re-render log tab if visible
        })
        .catch(function() {});
    }
    return;
  }

  // Tab switching
  var tabBtn = e.target.closest('.tab-btn');
  if (tabBtn) {
    var agentId = tabBtn.dataset.agent;
    var tab = tabBtn.dataset.tab;
    activeTabMap[agentId] = tab;
    // Update active states
    var card = document.getElementById('card-' + agentId);
    if (card) {
      card.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.toggle('active', b.dataset.tab === tab); });
      card.querySelectorAll('.tab-panel').forEach(function(p) { p.classList.toggle('active', p.dataset.tab === tab); });
    }
  }
});
```

- [ ] **Step 20: Add renderAggregateStats() function**

```javascript
function renderAggregateStats(agents) {
  var totalClaims = 0, totalSources = 0, totalFetchUsed = 0, totalFetchCap = 0;
  for (var id in agents) {
    var a = agents[id];
    totalClaims += (a.claimsFound || 0);
    totalSources += (a.sourcesCollected || 0);
    totalFetchUsed += (a.webFetchesUsed || 0);
    totalFetchCap += (a.webFetchCap || 0);
  }
  aggClaimsEl.textContent = totalClaims;
  aggSourcesEl.textContent = totalSources;
  aggFetchesEl.textContent = totalFetchUsed + '/' + totalFetchCap + ' used';
}
```

- [ ] **Step 21: Add renderVvcPanel() function**

Implement the VVC panel rendering per spec Section 7i:

```javascript
function renderVvcPanel(vvc) {
  if (!vvc) {
    vvcPanelEl.style.display = 'none';
    return;
  }
  vvcPanelEl.style.display = '';
  // Build panel HTML:
  // - Header: "VVC Verification" or "VVC Correction" based on vvc.phase
  // - Mode line: "full" or "verify-only"
  // - Summary progress bar: verified / totalClaims
  // - Verdict counts breakdown
  // - Claims table with columns: ID, Claim, Confidence, Verdict, Recommendation
  // - Phase 6 adds "Applied" column
  // - Expandable rows showing sourceUrl, sourceQuote, correctedText
  // - Verify-only mode: no Recommendation/Applied columns, header note
}
```

Key rendering rules:
- Verdict icons: CONFIRMED = green checkmark, PARAPHRASED = tilde, OVERSTATED/UNDERSTATED = warning, DISPUTED/UNSUPPORTED = red X, SOURCE_UNAVAILABLE = red X (dimmed), null + actively being verified = cyan pulsing, null + pending = gray circle
- Phase 6: add Applied column with color-coded badges (kept=green, applied=amber, removed=rose, applying=cyan pulsing)
- Expandable rows: click a row to toggle the detail row showing source URL, quote, corrected text
- Verify-only mode: header states "verify only -- no corrections applied", hide Recommendation column

- [ ] **Step 22: Add legend rendering and toggle**

```javascript
function renderLegend() {
  var html = '<strong style="color:var(--text-primary)">Legend</strong>';
  html += '<div class="legend-row"><span class="legend-label">Pipeline</span>';
  html += '<span class="legend-swatch" style="background:var(--border)"></span> pending ';
  html += '<span class="legend-swatch" style="background:var(--accent-search)"></span> active ';
  html += '<span class="legend-swatch" style="background:var(--accent-complete)"></span> complete ';
  html += '<span class="legend-swatch" style="background:var(--accent-error)"></span> error</div>';
  // ... Activity, Claims, Questions, Web Fetches rows
  legendPanelEl.innerHTML = html;
}

legendToggleEl.addEventListener('click', function() {
  legendPanelEl.classList.toggle('visible');
});

renderLegend();
```

- [ ] **Step 23: Update main render() function**

Update the `render()` function (lines 779-825) to:

1. Call `renderAggregateStats(agents)` after rendering agent cards
2. Call `renderVvcPanel(status.vvc)` for VVC data
3. When pipeline reaches Phase 3+, hide agent cards if all agents are complete (collapse Phase 2 cards since agents are done)
4. When pipeline reaches Phase 5, show VVC panel
5. Update live phase duration counters for in_progress phases

```javascript
// In render():
renderAggregateStats(agents);

if (status.vvc) {
  renderVvcPanel(status.vvc);
}

// Hide agent cards during non-Phase-2 phases if all agents complete
if (pipeline && pipeline.currentPhase > 2) {
  var allAgentsDone = Object.keys(agents).every(function(id) {
    return agents[id].status === 'complete' || agents[id].status === 'error';
  });
  if (allAgentsDone && !status.vvc) {
    agentsSectionEl.style.display = 'none';
  }
}

// Update live phase durations
document.querySelectorAll('.phase-duration.active').forEach(function(el) {
  var started = el.dataset.started;
  if (started) el.textContent = formatDurationFromTo(started, null);
});
```

- [ ] **Step 24: Add phase duration timer to the 1-second interval**

Add a second interval timer that updates live phase durations every second:

```javascript
setInterval(function() {
  document.querySelectorAll('.phase-duration.active').forEach(function(el) {
    var started = el.dataset.started;
    if (started) el.textContent = formatDurationFromTo(started, null);
  });
  // Also update active question durations
  document.querySelectorAll('.question-duration.active').forEach(function(el) {
    var started = el.dataset.started;
    if (started) el.textContent = formatDurationFromTo(started, null);
  });
}, 1000);
```

- [ ] **Step 25: Verify the dashboard HTML**

```bash
# Verify key elements exist
grep -c "vvc-panel" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: at least 3 (CSS + HTML + JS)

grep -c "question-list" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: at least 2

grep -c "stats-bar" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: at least 2

grep -c "legend-panel" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: at least 3

grep -c "expand-toggle" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: at least 2

grep -c "tab-btn" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: at least 2

grep -c "claims-table" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: at least 2

grep -c "log-feed" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: at least 2

grep -c "/api/agent/" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: at least 1

grep -c "currentAction" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: at least 1

grep -c "renderVvcPanel" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: at least 2

# Verify no template placeholders leaked (file should contain no {{ }} except the template name)
grep -c "{{" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: 0 (this template has no placeholders — it's static HTML/JS)

# Verify HTML is well-formed (basic check)
grep -c "</html>" plugin/skills/engine-creator/templates/dashboard.html.tmpl
# Expected: 1
```

- [ ] **Step 26: Commit**

```bash
git add plugin/skills/engine-creator/templates/dashboard.html.tmpl
git commit -m "feat: overhaul dashboard with question tracker, expandable cards, claims/log tabs, VVC panel, legend"
```

---

### Task 6: Update patent-intelligence-engine example

**Files:**
- Modify: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/research-protocol.md`
- Modify: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md`
- Modify: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/vvc-pipeline.md`
- Modify: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/dashboard-server.js`
- Modify: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/dashboard.html`

Apply all template changes from Tasks 1-5 to the concrete example engine. The example engine is the template output with placeholders resolved for the patent-intelligence domain.

- [ ] **Step 1: Update research-protocol.md**

Apply the same structural changes from Task 1:
- Replace Status JSON Schema with the v1.9.0 schema (questions array, currentAction, errors, aborts)
- Replace "When to Write Status" rules with the expanded rules
- Add step 6 to Incremental Write Protocol (claims JSON)
- Add Action Logging Protocol section
- Add claims and log files to File Isolation Protocol

The example file has patent-specific values substituted (e.g., `10` for maxWebFetches, `4` for maxIterations) — preserve these concrete values while changing the structure.

- [ ] **Step 2: Update SKILL.md (Phase Transition Protocol and file structure)**

Apply the same structural changes from Task 2:
- Add `startedAt` and `completedAt` fields to the `_pipeline.json` initial state example
- Update Phase Transition Protocol with timing instructions
- Add `[AgentID]_claims.json`, `[AgentID]_log.json`, `vvc-specialist_verification.json` to the File Output Structure

- [ ] **Step 3: Update vvc-pipeline.md**

Apply the same structural changes from Task 3:
- Add VVC Verification Status Protocol section after Phase 5 block

- [ ] **Step 4: Update dashboard-server.js**

Apply the same code changes from Task 4:
- Replace `getStatus()` with the expanded version (claims, log, VVC reading, capLog parameter)
- Update `broadcastStatus()` to pass `true` to `getStatus()`
- Update `/api/status` handler to pass `false`
- Update `/api/events` initial push to pass `true`
- Add `GET /api/agent/:id/log` endpoint

Note: The example file has `DEFAULT_PORT = 3847` (no placeholder).

- [ ] **Step 5: Update dashboard.html**

Apply the same changes from Task 5. The example dashboard.html is identical to the template output (no placeholders were used in this template).

- [ ] **Step 6: Verify example engine**

```bash
# Verify research-protocol.md changes
grep -c "currentAction" plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/research-protocol.md
# Expected: at least 4

grep -c "Action Logging Protocol" plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/research-protocol.md
# Expected: 1

grep -c "_claims.json" plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/research-protocol.md
# Expected: at least 2

# Verify SKILL.md changes
grep -c "startedAt" plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md
# Expected: at least 3

grep -c "_claims.json" plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md
# Expected: at least 1

# Verify vvc-pipeline.md changes
grep -c "vvc-specialist_verification.json" plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/vvc-pipeline.md
# Expected: at least 1

# Verify dashboard-server.js changes
grep -c "capLog" plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/dashboard-server.js
# Expected: at least 3

grep -c "/api/agent/" plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/dashboard-server.js
# Expected: at least 1

# Verify dashboard.html changes
grep -c "vvc-panel" plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/dashboard.html
# Expected: at least 3

grep -c "question-list" plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/dashboard.html
# Expected: at least 2
```

- [ ] **Step 7: Commit**

```bash
git add plugin/examples/patent-intelligence-engine/
git commit -m "feat: apply enhanced observability changes to patent-intelligence-engine example"
```

---

### Task 7: End-to-end verification

- [ ] **Step 1: Create mock status data for dashboard testing**

Create a temporary test directory with mock JSON files that exercise all dashboard features:

```bash
mkdir -p /tmp/dashboard-test/_status
```

Write mock files:
- `_pipeline.json` — 7 phases, Phase 2 in_progress, Phase 0-1 complete with startedAt/completedAt timestamps
- `patent-search-specialist.json` — agent status with questions array (2 complete, 1 active, 2 pending), currentAction set, errors: 1
- `patent-search-specialist_claims.json` — 5 claims with mixed statuses
- `patent-search-specialist_log.json` — 15 log entries of various types
- `prior-art-analyst.json` — second agent, all questions pending
- `prior-art-analyst_claims.json` — empty array
- `prior-art-analyst_log.json` — 3 start entries

- [ ] **Step 2: Copy dashboard files and start server**

```bash
cp plugin/skills/engine-creator/templates/dashboard-server.js.tmpl /tmp/dashboard-test/_status/server.js
cp plugin/skills/engine-creator/templates/dashboard.html.tmpl /tmp/dashboard-test/_status/dashboard.html

# Replace template placeholder with concrete port
sed -i 's/{{dashboardPort}}/3899/g' /tmp/dashboard-test/_status/server.js

# Start server
node /tmp/dashboard-test/_status/server.js &
SERVER_PID=$!
echo "Dashboard server PID: $SERVER_PID"
```

- [ ] **Step 3: Verify API responses**

```bash
# Wait for server to start
sleep 1

# Test /api/status returns agents with claims and log
curl -s http://localhost:3899/api/status | node -e "
const data = JSON.parse(require('fs').readFileSync('/dev/stdin', 'utf8'));
const checks = [
  ['pipeline exists', !!data.pipeline],
  ['agents exist', Object.keys(data.agents).length > 0],
  ['agent has claims', data.agents['patent-search-specialist'] && Array.isArray(data.agents['patent-search-specialist'].claims)],
  ['agent has log', data.agents['patent-search-specialist'] && Array.isArray(data.agents['patent-search-specialist'].log)],
  ['vvc key exists', 'vvc' in data],
];
checks.forEach(([name, pass]) => console.log((pass ? 'PASS' : 'FAIL') + ': ' + name));
"

# Test /api/agent/:id/log returns full log
curl -s http://localhost:3899/api/agent/patent-search-specialist/log | node -e "
const data = JSON.parse(require('fs').readFileSync('/dev/stdin', 'utf8'));
console.log(Array.isArray(data) ? 'PASS: log is array (' + data.length + ' entries)' : 'FAIL: log is not array');
"

# Test dashboard HTML loads
curl -s http://localhost:3899/ | grep -c 'question-list'
# Expected: at least 1
```

- [ ] **Step 4: Test VVC panel with mock VVC data**

```bash
# Write mock VVC verification data
cat > /tmp/dashboard-test/_status/vvc-specialist_verification.json << 'VVCEOF'
{
  "phase": 5,
  "mode": "full",
  "totalClaims": 5,
  "verified": 3,
  "claims": [
    {"id":"VC-01","text":"Test claim 1","confidence":"HIGH","sourceUrl":"https://example.com","sourceQuote":"Supporting text","verdict":"CONFIRMED","recommendation":"KEEP","correctedText":null,"correctionApplied":null},
    {"id":"VC-02","text":"Test claim 2","confidence":"HIGH","sourceUrl":"https://example.com/2","sourceQuote":"Slightly different","verdict":"OVERSTATED","recommendation":"REVISE","correctedText":"Revised claim 2","correctionApplied":null},
    {"id":"VC-03","text":"Test claim 3","confidence":"MEDIUM","sourceUrl":null,"sourceQuote":null,"verdict":"SOURCE_UNAVAILABLE","recommendation":"REMOVE","correctedText":null,"correctionApplied":null},
    {"id":"VC-04","text":"Test claim 4","confidence":"HIGH","sourceUrl":null,"sourceQuote":null,"verdict":null,"recommendation":null,"correctedText":null,"correctionApplied":null},
    {"id":"VC-05","text":"Test claim 5","confidence":"LOW","sourceUrl":null,"sourceQuote":null,"verdict":null,"recommendation":null,"correctedText":null,"correctionApplied":null}
  ],
  "lastUpdated": "2026-03-19T15:00:00Z"
}
VVCEOF

# Verify VVC data appears in API
curl -s http://localhost:3899/api/status | node -e "
const data = JSON.parse(require('fs').readFileSync('/dev/stdin', 'utf8'));
console.log(data.vvc ? 'PASS: VVC data present (' + data.vvc.verified + '/' + data.vvc.totalClaims + ' verified)' : 'FAIL: no VVC data');
"
```

- [ ] **Step 5: Clean up**

```bash
kill $SERVER_PID 2>/dev/null
rm -rf /tmp/dashboard-test
```

- [ ] **Step 6: Final cross-file consistency checks**

```bash
# Verify all templates reference the same new file names
echo "=== _claims.json references ==="
grep -rl "_claims.json" plugin/skills/engine-creator/templates/ | sort

echo "=== _log.json references ==="
grep -rl "_log.json" plugin/skills/engine-creator/templates/ | sort

echo "=== verification.json references ==="
grep -rl "verification.json" plugin/skills/engine-creator/templates/ | sort

echo "=== currentAction references ==="
grep -rl "currentAction" plugin/skills/engine-creator/templates/ | sort

echo "=== questions array references ==="
grep -rl '"questions"' plugin/skills/engine-creator/templates/ | sort

# Expected: each should appear in at least 2 template files
# _claims.json: research-protocol.md.tmpl, dashboard-server.js.tmpl
# _log.json: research-protocol.md.tmpl, dashboard-server.js.tmpl
# verification.json: vvc-pipeline.md.tmpl, dashboard-server.js.tmpl
# currentAction: research-protocol.md.tmpl, dashboard.html.tmpl
# questions: research-protocol.md.tmpl, dashboard.html.tmpl
```
