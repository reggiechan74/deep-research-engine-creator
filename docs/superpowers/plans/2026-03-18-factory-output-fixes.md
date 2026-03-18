# Factory Output Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modify the engine factory templates so generated engines no longer exhibit per-fetch hashing overhead, shared-file race conditions, missing `--no-vvc` flag, uncapped WebFetch calls, and monolithic orchestrator bloat.

**Architecture:** Split the monolithic `base-research-skill.md.tmpl` (782 lines) into 5 focused templates that produce a lean orchestrator SKILL.md (~150-200 lines) plus reference files agents load on-demand. Apply fixes 1/3/4/5 during the split. Update generation protocol, schemas, agent template, extension template, and patent example.

**Tech Stack:** Markdown templates with `{{placeholder}}` syntax, JSON Schema, Claude Code plugin architecture.

**Spec:** `docs/superpowers/specs/2026-03-18-factory-output-fixes-design.md`

---

## File Map

### New Files (templates)
- `plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl` — lean orchestrator (~150-200 lines)
- `plugin/skills/engine-creator/templates/standards.md.tmpl` — quality standards reference (~100-130 lines)
- `plugin/skills/engine-creator/templates/research-protocol.md.tmpl` — research protocol reference (~100-130 lines)
- `plugin/skills/engine-creator/templates/provenance.md.tmpl` — batch hashing + audit reference (~80-100 lines)
- `plugin/skills/engine-creator/templates/vvc-pipeline.md.tmpl` — VVC phases reference (~80-100 lines)

### New Files (patent example)
- `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/standards.md`
- `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/research-protocol.md`
- `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/provenance.md`
- `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/vvc-pipeline.md`

### Modified Files
- `plugin/skills/engine-creator/templates/agent-template.md.tmpl` — remove shared writes, add WebFetch cap, add reference file loading
- `plugin/skills/engine-creator/templates/extension-skill.md.tmpl` — all 5 fixes applied in-place
- `plugin/skills/engine-creator/templates/engine-config-schema.json` — add `maxWebFetchesPerAgent`
- `plugin/skills/engine-creator/templates/preset-schema.json` — add `maxWebFetchesPerAgent`
- `plugin/skills/engine-creator/SKILL.md` — Step 8 multi-file, Section 8 WebFetch cap, placeholder rules, template reference
- `plugin/commands/test-engine.md` — updated validation checks
- `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md` — rewrite as lean orchestrator
- `plugin/examples/patent-intelligence-engine/agents/patent-search-specialist.md` — fix references
- `plugin/examples/patent-intelligence-engine/agents/prior-art-analyst.md` — fix references
- `plugin/examples/patent-intelligence-engine/agents/ip-landscape-mapper.md` — fix references
- `plugin/examples/patent-intelligence-engine/agents/vvc-specialist.md` — fix references
- `plugin/examples/patent-intelligence-engine/engine-config.json` — add `maxWebFetchesPerAgent`
- `plugin/examples/patent-intelligence-engine/README.md` — update structure and usage

### Deleted Files
- `plugin/skills/engine-creator/templates/base-research-skill.md.tmpl` — retired, replaced by 5 new templates

---

## Task 1: Create `orchestrator-skill.md.tmpl`

Extract the orchestrator-only content from `base-research-skill.md.tmpl` into a lean new template. This is the file that loads into the system prompt of generated engines.

**Files:**
- Create: `plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl`
- Reference: `plugin/skills/engine-creator/templates/base-research-skill.md.tmpl` (source material)

- [ ] **Step 1: Create the orchestrator template**

Extract these sections from `base-research-skill.md.tmpl` into the new file:
- Lines 1-4: YAML frontmatter (unchanged)
- Lines 6-14: Title and description — change line 13 from "All protocols, agent definitions, quality standards, and output specifications are defined in this file." to "Agent protocols, quality standards, and detailed instructions are in reference files that agents load on-demand."
- Lines 15-27: Usage block — add `--no-vvc` flag: `- /research [topic] --no-vvc -- Skip VVC verification phases (when VVC is enabled)`
- Lines 30-46: Research Architecture (phase overview, tier config table, unchanged)
- Lines 49-64: Phase 0 flag parsing — add `--no-vvc` flag parsing after line 63: `- If --no-vvc is present and engine has VVC enabled, set NO_VVC to true (skip Phases 5-6, Phase 4 becomes final reporting)`
- Lines 72-83: Derive Configuration (unchanged, subset of Phase 0)
- Skip lines 85-87: Provenance setup (moves to provenance.md.tmpl — do NOT include)
- Lines 263-274: Sub-Agent System (unchanged)
- Lines 278-296: Quick Tier execution strategy — add instruction: "Agent FIRST ACTION: Read `${CLAUDE_SKILL_DIR}/standards.md`". Add WebFetch cap: "Cap total WebFetch calls at {{maxWebFetches}}."
- Lines 299-331: Phase 1 planning (unchanged)
- Lines 334-363: Phase 2 — rewrite to remove Shared_Sources.md references and per-fetch hashing. Replace line 337 ("coordinates through Shared_Sources.md") with "Each agent writes to its own files only." Replace Common Agent Requirements:
  - Item 1: Change FIRST ACTION to read `${CLAUDE_SKILL_DIR}/standards.md`, `${CLAUDE_SKILL_DIR}/research-protocol.md`, and `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md`
  - Remove item 5 (append to Shared_Sources.md)
  - Item 11: Change to per-agent methodology log: `BASE_DIR/[TOPIC_SLUG]_Methodology_Log_[AgentID].md`
  - Replace item 12 (per-fetch hashing) with: "Save discovered sources to `BASE_DIR/[TOPIC_SLUG]_Sources_[AgentID].md`"
  - Add new item: "Cap total WebFetch calls at {{maxWebFetches}}. If a URL returns 403/blocked/paywall, note in methodology log and move on — do not retry."
- NEW: Phase 2.5 — add pointer: "After all Phase 2 agents complete, deploy a **general-purpose** batch hashing agent. Agent FIRST ACTION: Read `${CLAUDE_SKILL_DIR}/provenance.md` and execute the batch hashing protocol."
- Lines 366-385: Phase 3 synthesis — update to read per-agent files:
  - Change "Read ALL agent output files: results, claims tables, bibliographies, shared sources" to "Read ALL per-agent output files: claims tables (`_Claims_[AgentID].md`), bibliographies (`_[AgentID]_Bibliography.md`), sources (`_Sources_[AgentID].md`), methodology logs (`_Methodology_Log_[AgentID].md`)"
  - Add: "Consolidate per-agent methodology logs into `BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md`"
  - Add: "Consolidate per-agent sources into `BASE_DIR/[TOPIC_SLUG]_Sources.md`"
- Lines 389-427: Phase 4 reporting — add `--no-vvc` conditional:
  - "If `--no-vvc` flag is present: Phase 4 heading is 'Professional Reporting'. Output file: `_Comprehensive_Report.md`. Skip claim tagging. Phases 5-6 are skipped."
  - "Otherwise (VVC enabled, no `--no-vvc` flag): Phase 4 heading is '{{phase4Name}}'. Output file: `_{{phase4OutputFile}}`. Apply claim tagging per `${CLAUDE_SKILL_DIR}/vvc-pipeline.md`."
- Lines 428-469: Phase 4.5 — change to pointer: "Deploy a **general-purpose** provenance audit agent. Agent FIRST ACTION: Read `${CLAUDE_SKILL_DIR}/provenance.md` and execute the provenance audit protocol." Update methodology log reference to consolidated file.
- Lines 471-473: VVC phase blocks (just the placeholders, unchanged)
- Lines 479-500: File Output Structure — remove `Shared_Sources.md` (line 486), change `Methodology_Log.md` to show both per-agent and consolidated forms, add per-agent `Sources_[AgentID].md`
- Lines 504-518: Key Workflow Features — remove line 508 (Shared_Sources.md bullet), update line 517 (provenance) to say "batch hashing after Phase 2" instead of "every WebFetch is SHA-256 hashed"
- Lines 658-678: Domain Preamble and Operational Lessons (unchanged)
- Do NOT include: Global Standards (lines 91-174), Search Query Generation Protocol (lines 177-197), Iterative Search-Assess-Refine (lines 200-234), Cross-Agent Coordination (lines 238-248), Failure Recovery (lines 251-259), Bibliography & Footnote Standards (lines 522-551), Source Verification Protocol (lines 554-627), Context Management Guidelines (lines 631-654), Placeholder Reference (lines 682-782) — these move to reference files.
- Add a brief Placeholder Reference at the bottom listing only the placeholders used in this file (including new `{{maxWebFetches}}`).

- [ ] **Step 2: Verify line count**

Run: `wc -l plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl`
Expected: 150-200 lines

- [ ] **Step 3: Verify no prohibited content leaked in**

Run these searches against the new file:
- Grep for "After each WebFetch" — should find 0 matches
- Grep for "Shared_Sources" — should find 0 matches
- Grep for "Source Hashing Protocol" — should find 0 matches
- Grep for `--no-vvc` — should find 2+ matches (usage block + Phase 0)
- Grep for "Professional Reporting" — should find 1+ matches (Phase 4 `--no-vvc` conditional)
- Grep for `{{maxWebFetches}}` — should find 1+ matches

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl
git commit -m "feat: create orchestrator-skill.md.tmpl — lean orchestrator template (Fix 6)"
```

---

## Task 2: Create `standards.md.tmpl`

Extract quality standards that all agents need into a standalone reference file.

**Files:**
- Create: `plugin/skills/engine-creator/templates/standards.md.tmpl`
- Reference: `plugin/skills/engine-creator/templates/base-research-skill.md.tmpl` lines 91-143, 522-551

- [ ] **Step 1: Create the standards template**

Extract and assemble from `base-research-skill.md.tmpl`:
- Title: `# Quality Standards Reference — {{engineDisplayName}}`
- Lines 91-143: Global Standards section (confidence scoring, source credibility hierarchy, citation & evidence standards, validation rules, structured output standards) — but change line 141 from `_Methodology_Log.md` to `_Methodology_Log_[AgentID].md` and add line for `_Sources_[AgentID].md`
- Remove lines 145-164 (Source Hashing Protocol — moves to provenance.md.tmpl)
- Lines 522-551: Bibliography & Footnote Standards (in-text citations, footnote placement, master bibliography, dedup rules)
- Lines 554-627: Source Verification Protocol (verification mode, probe on discovery, URL liveness, freshness, dead link handling, content-claim matching, citation verification report)
- Add Placeholder Reference section at bottom listing all placeholders used in this file

- [ ] **Step 2: Verify no prohibited content**

- Grep for "After each WebFetch" — should find 0 matches
- Grep for "Shared_Sources" — should find 0 matches
- Grep for "Source Hashing Protocol" — should find 0 matches

- [ ] **Step 3: Commit**

```bash
git add plugin/skills/engine-creator/templates/standards.md.tmpl
git commit -m "feat: create standards.md.tmpl — quality standards reference template"
```

---

## Task 3: Create `research-protocol.md.tmpl`

Extract research execution protocols into a standalone reference file. Includes Fix 3 (file isolation) and Fix 5 (WebFetch cap).

**Files:**
- Create: `plugin/skills/engine-creator/templates/research-protocol.md.tmpl`
- Reference: `plugin/skills/engine-creator/templates/base-research-skill.md.tmpl` lines 166-259, 631-654

- [ ] **Step 1: Create the research protocol template**

Extract and assemble from `base-research-skill.md.tmpl`:
- Title: `# Research Protocol Reference — {{engineDisplayName}}`
- Lines 166-173: Context Discipline
- Lines 177-197: Search Query Generation Protocol — change line 196 from `_Methodology_Log.md` to `_Methodology_Log_[AgentID].md`
- Lines 200-234: Iterative Search-Assess-Refine Protocol — change line 210 from `Methodology_Log.md` to per-agent `Methodology_Log_[AgentID].md`
- NEW section — **File Isolation Protocol** (replaces Cross-Agent Coordination, lines 238-248):
  ```
  ## File Isolation Protocol

  Each Phase 2 agent writes ONLY to its own files. No shared files during parallel research.

  Per-agent output files:
  - Claims: `BASE_DIR/[TOPIC_SLUG]_Claims_[AgentID].md`
  - Bibliography: `BASE_DIR/[TOPIC_SLUG]_[AgentID]_Bibliography.md`
  - Methodology log: `BASE_DIR/[TOPIC_SLUG]_Methodology_Log_[AgentID].md`
  - Sources: `BASE_DIR/[TOPIC_SLUG]_Sources_[AgentID].md`

  Phase 3 synthesis consolidates per-agent files into unified versions.
  Do NOT write to any file that another agent might also be writing to.
  ```
- NEW section — **WebFetch Cap**:
  ```
  ## WebFetch Cap

  Cap total WebFetch calls at {{maxWebFetches}} per agent per research session.
  Prioritize highest-credibility, most-accessible sources.
  If a URL returns 403/blocked/paywall, note it in methodology log and move on — do not retry.
  ```
- Lines 251-259: Failure Recovery Protocol
- Lines 631-654: Context Management Guidelines (token budgets, context efficiency rules)
- Add Placeholder Reference section at bottom listing all placeholders used in this file (including `{{maxWebFetches}}`, `{{maxIterations}}`, `{{explorationDepth}}`, token budget placeholders)

- [ ] **Step 2: Verify content**

- Grep for "Shared_Sources" — should find 0 matches
- Grep for `{{maxWebFetches}}` — should find 1+ matches
- Grep for "File Isolation" — should find 1+ matches

- [ ] **Step 3: Commit**

```bash
git add plugin/skills/engine-creator/templates/research-protocol.md.tmpl
git commit -m "feat: create research-protocol.md.tmpl — file isolation (Fix 3) + WebFetch cap (Fix 5)"
```

---

## Task 4: Create `provenance.md.tmpl`

New template for batch hashing (Fix 1) and relocated provenance audit. This replaces the per-fetch Source Hashing Protocol.

**Files:**
- Create: `plugin/skills/engine-creator/templates/provenance.md.tmpl`
- Reference: `plugin/skills/engine-creator/templates/base-research-skill.md.tmpl` lines 85-87, 145-164, 428-469

- [ ] **Step 1: Create the provenance template**

Build new content with relocated material from `base-research-skill.md.tmpl`:

```markdown
# Provenance Reference — {{engineDisplayName}}

## Phase 2.5: Batch Source Hashing

After all Phase 2 research agents complete, deploy a **general-purpose** batch hashing agent.

### Instructions

1. Read all bibliography files: `BASE_DIR/[TOPIC_SLUG]_*_Bibliography.md`
2. Collect all unique URLs across all bibliographies
3. Deduplicate URLs (same URL from multiple agents = hash once)
4. Create `BASE_DIR/[TOPIC_SLUG]_Hash_Manifest.md` with header:
   `| # | URL | SHA-256 | Timestamp | Agent_ID | Event_Hash | Prev_Hash |`
5. If `--reverifiable`: create `BASE_DIR/Source_Snapshots/` directory via Bash: `mkdir -p`
6. For each unique URL sequentially:
   a. Fetch content using WebFetch
   b. Write fetched content to temp file: `BASE_DIR/Source_Snapshots/[AGENT_PREFIX]-[SEQ]_[url-slug].txt`
   c. Compute content hash via Bash: `sha256sum "BASE_DIR/Source_Snapshots/[file]" | cut -d' ' -f1`
   d. Get PREV_HASH: last row's Event_Hash from Hash_Manifest.md, or "GENESIS" if first entry
   e. Compute event hash via Bash: `echo -n "[SHA-256]|[URL]|[TIMESTAMP]|BATCH|[PREV_HASH]" | sha256sum | cut -d' ' -f1`
   f. Append row to Hash_Manifest.md: `| [#] | [URL] | [SHA-256] | [Timestamp] | BATCH | [Event_Hash] | [Prev_Hash] |`
   g. If `--reverifiable` is NOT set: `rm "BASE_DIR/Source_Snapshots/[file]"`
   h. If `--reverifiable` IS set: retain snapshot for independent re-verification

### Naming Conventions

- `[AGENT_PREFIX]`: `B` (for batch hashing agent)
- `[SEQ]`: zero-padded counter (e.g., `B-001`, `B-002`)
- `[url-slug]`: domain + path slug, max 60 chars, lowercase, special chars removed

### Hash Chain Format

`[SHA-256]|[URL]|[TIMESTAMP]|[AGENT_ID]|[PREV_HASH]`

---

## Phase 4.5: Provenance Audit
```

Then append the relocated Phase 4.5 content from lines 428-469, with one change: line 437 "Cross-reference with Methodology_Log.md" becomes "Cross-reference with consolidated `BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md`" (the consolidated file produced by Phase 3).

Add the Provenance Log Structure block (lines 441-467) and output format (line 469).

Add Placeholder Reference at bottom listing: `{{auditTierBehavior}}`, `{{reverifiableDefault}}`.

- [ ] **Step 2: Verify content**

- Grep for "After each WebFetch" — should find 0 matches (this is batch, not per-fetch)
- Grep for "general-purpose" — should find 2 matches (Phase 2.5 agent + Phase 4.5 agent)
- Grep for "Methodology_Log.md" — should reference the consolidated version, not per-agent

- [ ] **Step 3: Commit**

```bash
git add plugin/skills/engine-creator/templates/provenance.md.tmpl
git commit -m "feat: create provenance.md.tmpl — batch hashing replaces per-fetch (Fix 1)"
```

---

## Task 5: Create `vvc-pipeline.md.tmpl`

Extract VVC content into a conditional reference file.

**Files:**
- Create: `plugin/skills/engine-creator/templates/vvc-pipeline.md.tmpl`

- [ ] **Step 1: Create the VVC pipeline template**

This file's content is entirely generated from placeholder expansion. It wraps the VVC-specific placeholders that are already conditionally populated by the generation protocol:

```markdown
# VVC Pipeline Reference — {{engineDisplayName}}

{{vvcClaimTaxonomyBlock}}

## Phase 5: VVC-Verify

{{vvcVerifyPhaseBlock}}

## Phase 6: VVC-Correct

{{vvcCorrectPhaseBlock}}

## Placeholder Reference

- `{{vvcClaimTaxonomyBlock}}` — claim type taxonomy with [VC]/[PO]/[IE] definitions and verification scope
- `{{vvcVerifyPhaseBlock}}` — Phase 5 verification instructions
- `{{vvcCorrectPhaseBlock}}` — Phase 6 correction instructions
- `{{vvcBudgetLine}}` — token budget for VVC phases
```

Note: This template is only generated when VVC is enabled (Step 8e is conditional). The placeholders are the same ones currently embedded in `base-research-skill.md.tmpl` via `{{vvcVerifyPhaseBlock}}` and `{{vvcCorrectPhaseBlock}}`.

- [ ] **Step 2: Commit**

```bash
git add plugin/skills/engine-creator/templates/vvc-pipeline.md.tmpl
git commit -m "feat: create vvc-pipeline.md.tmpl — VVC phases reference template"
```

---

## Task 6: Update `agent-template.md.tmpl`

Apply Fix 3 (remove shared writes), Fix 5 (WebFetch cap), and add reference file loading.

**Files:**
- Modify: `plugin/skills/engine-creator/templates/agent-template.md.tmpl`

- [ ] **Step 1: Remove Cross-Agent Coordination section (lines 79-84)**

Delete the entire section:
```
## Cross-Agent Coordination

- Read `Shared_Sources.md` before starting each new search branch
- Append high-value source discoveries to `Shared_Sources.md` immediately
- Skip already-covered sources; prioritize coverage gaps
- Use citation IDs (e.g., `[A-01]`, `[A-02]`) and refer to them instead of repeating full citations
```

- [ ] **Step 2: Add WebFetch cap to Search Protocol section**

After line 63 ("Abort when no new credible sources after 2 alternate query branches"), add:

```markdown

4. **WebFetch cap**: Hard cap of {{maxWebFetches}} total WebFetch calls per research session. Prioritize highest-credibility, most-accessible sources. If a URL returns 403/blocked/paywall, note in methodology log and move on — do not retry.
```

- [ ] **Step 3: Update Output Format section**

Change line 74 from:
```
- Log all search queries, engines, filters, and assessments to Methodology_Log.md
```
to:
```
- Log all search queries, engines, filters, and assessments to your per-agent Methodology_Log_[AgentID].md
- Save discovered sources to your per-agent Sources_[AgentID].md
```

- [ ] **Step 4: Add reference file loading note**

After the "## Context Discipline" section (ends at line 91, end of file), append:

```markdown

## First Actions

Before starting research, read these reference files:
1. `${CLAUDE_SKILL_DIR}/standards.md` — quality standards, confidence scoring, source credibility
2. `${CLAUDE_SKILL_DIR}/research-protocol.md` — search protocol, file isolation rules, WebFetch cap
3. Read the research outline from `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md`
```

- [ ] **Step 5: Verify changes**

- Grep for "Shared_Sources" in the file — should find 0 matches
- Grep for `{{maxWebFetches}}` — should find 1 match
- Grep for "CLAUDE_SKILL_DIR" — should find 2 matches

- [ ] **Step 6: Commit**

```bash
git add plugin/skills/engine-creator/templates/agent-template.md.tmpl
git commit -m "feat: update agent template — file isolation (Fix 3), WebFetch cap (Fix 5), reference loading"
```

---

## Task 7: Update `extension-skill.md.tmpl`

Apply all 5 fixes in-place. The extension template stays as a single file.

**Files:**
- Modify: `plugin/skills/engine-creator/templates/extension-skill.md.tmpl`

- [ ] **Step 1: Fix 1 — Update provenance reference (line 126)**

Replace:
```
Provenance is always on. The base skill's Source Hashing Protocol applies to all agents in this extension. Phase 4.5 Provenance Audit runs on Standard/Deep/Comprehensive tiers.
```
With:
```
Provenance is always on. Provenance uses batch hashing (Phase 2.5). The base skill's batch hashing agent collects all cited URLs after Phase 2 completes and hashes them in a single sequential pass. Per-fetch hashing is not used. Phase 4.5 Provenance Audit runs on Standard/Deep/Comprehensive tiers.
```

- [ ] **Step 2: Fix 3 — Add File Isolation Override and update inherited list**

Before the "### Output Structure Override" section (line 134), add:

```markdown
### File Isolation Override

Each Phase 2 agent writes to its own files only. No shared files during parallel research.
- Sources: `BASE_DIR/[TOPIC_SLUG]_Sources_[AgentID].md`
- Methodology log: `BASE_DIR/[TOPIC_SLUG]_Methodology_Log_[AgentID].md`

Phase 3 synthesis consolidates per-agent files.

```

Then update the inherited protocols list (lines 209-215). Remove "Cross-Agent Coordination Protocol" from the list. The list becomes:
```
All base skill protocols remain in effect unless explicitly overridden above:
- Iterative Search-Assess-Refine Protocol
- Failure Recovery Protocol
- Context Management Guidelines
- Bibliography and Footnote Standards
- Search Query Generation Protocol (extended by domain-specific templates above)
```

- [ ] **Step 3: Fix 4 — Add `--no-vvc` flag**

In the "### Agent Pipeline Override" section (after line 91 `{{agentDeploymentBlocks}}`), add:

```markdown

**Runtime flags:**
- If `--no-vvc` is present: skip Phases 5-6, Phase 4 becomes final reporting (heading: Professional Reporting, output: `_Comprehensive_Report.md`, claim tagging skipped).
```

- [ ] **Step 4: Fix 5 — Add WebFetch cap**

In the "### Agent Pipeline Override" section, after the runtime flags block, add:

```markdown

**WebFetch cap:** All Phase 2 agents: cap total WebFetch calls at {{maxWebFetches}}. If a URL returns 403/blocked/paywall, note in methodology log and move on.
```

- [ ] **Step 5: Update Placeholder Reference**

Add to the "### Advanced Configuration" section (lines 274-280):
```
- `{{maxWebFetches}}` -- maximum WebFetch calls per agent per research session (default: 10)
```

- [ ] **Step 6: Update line 22 descriptive text**

Change line 22-23 from:
```
cross-agent coordination, failure recovery, context management -- is inherited from the
```
to:
```
failure recovery, context management -- is inherited from the
```

- [ ] **Step 7: Verify changes**

- Grep for "Shared_Sources" — should find 0 matches
- Grep for "Source Hashing Protocol" — should find 0 matches
- Grep for "Cross-Agent Coordination" — should find 0 matches
- Grep for `--no-vvc` — should find 1+ matches
- Grep for `{{maxWebFetches}}` — should find 1+ matches
- Grep for "File Isolation" — should find 1 match

- [ ] **Step 8: Commit**

```bash
git add plugin/skills/engine-creator/templates/extension-skill.md.tmpl
git commit -m "feat: update extension template — all 5 fixes applied in-place"
```

---

## Task 8: Update JSON Schemas

Add `maxWebFetchesPerAgent` to both schemas.

**Files:**
- Modify: `plugin/skills/engine-creator/templates/engine-config-schema.json`
- Modify: `plugin/skills/engine-creator/templates/preset-schema.json`

- [ ] **Step 1: Update engine-config-schema.json**

In the `advanced.properties` object (after `mcpServers` ending at line 729, before the closing `}` of `properties` on line 730), add:

```json
,
"maxWebFetchesPerAgent": {
  "type": "integer",
  "description": "Maximum WebFetch calls per research agent per run. Limits total fetches to control runtime and avoid excessive 403/blocked responses.",
  "default": 10,
  "minimum": 1,
  "maximum": 50
}
```

- [ ] **Step 2: Update preset-schema.json**

In the `advanced.properties` object (after `explorationDepth` at line 243), add:

```json
,
"maxWebFetchesPerAgent": { "type": "integer", "minimum": 1, "maximum": 50 }
```

- [ ] **Step 3: Validate JSON syntax**

Run: `python3 -c "import json; json.load(open('plugin/skills/engine-creator/templates/engine-config-schema.json')); print('OK')"` and same for preset-schema.json.

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/engine-creator/templates/engine-config-schema.json plugin/skills/engine-creator/templates/preset-schema.json
git commit -m "feat: add maxWebFetchesPerAgent to schemas (Fix 5)"
```

---

## Task 9: Update Engine Creator `SKILL.md`

Update the generation protocol: Step 8 multi-file output, Section 8 wizard question, placeholder derivation rules, template reference table.

**Files:**
- Modify: `plugin/skills/engine-creator/SKILL.md`

- [ ] **Step 1: Update Wizard Section 8 (line 171)**

Change line 171 from:
```
2. If yes: max iterations (1-5, default 3), exploration depth (1-10, default 5), token budgets (planning: 2000, research: 15000, synthesis: 8000, reporting: 10000, vvc: 8000), custom hooks, MCP server integrations.
```
to:
```
2. If yes: max iterations (1-5, default 3), exploration depth (1-10, default 5), max WebFetch calls per agent (1-50, default 10), token budgets (planning: 2000, research: 15000, synthesis: 8000, reporting: 10000, vvc: 8000), custom hooks, MCP server integrations.
```

- [ ] **Step 2: Replace Step 8 (lines 246-253)**

Replace the entire Step 8 block starting at line 246 ("**Step 8 -- SKILL.md.**") through line 253 ("- Missing optionals: sensible defaults or empty string") with:

```markdown
**Step 8 -- Skill files.** Select template set by mode.

**Extension mode:** read `extension-skill.md.tmpl`, replace placeholders, write single file to `{OUTPUT_DIR}/skills/{skillDirName}/SKILL.md`.

**Self-contained mode:** execute Steps 8a-8e below. Placeholder substitution rules apply to all sub-steps:
- Simple values: direct substitution
- Arrays (`{{reportSections}}`, `{{preferredSites}}`): markdown numbered list
- Objects (`{{tierConfigTable}}`): markdown table rows
- Nested (`{{agentDeploymentBlocks}}`): one block per agent with ID, role, model, specialization, tools, prompt override
- `{{subAgentList}}`: research-planning-specialist, synthesis-specialist, research-reporting-specialist, plus custom agents
- `{{fileStructure}}`: per-agent file entries (Claims, Bibliography, Sources, Methodology_Log)
- Missing optionals: sensible defaults or empty string

**Step 8a -- Orchestrator SKILL.md.** Read `orchestrator-skill.md.tmpl`. Replace placeholders (engine metadata, tier config, phase overview, agent roster, domain preamble, Phase 0 flags including `--no-vvc`, execution strategy pointers, `{{maxWebFetches}}`). Write to `{OUTPUT_DIR}/skills/{skillDirName}/SKILL.md`.

**Step 8b -- standards.md.** Read `standards.md.tmpl`. Replace placeholders (confidence scoring, source hierarchy, citation standard, validation rules, evidence rules, verification protocol). Write to `{OUTPUT_DIR}/skills/{skillDirName}/standards.md`.

**Step 8c -- research-protocol.md.** Read `research-protocol.md.tmpl`. Replace placeholders (search templates, preferred sites, maxIterations, maxWebFetches, explorationDepth, per-agent file naming, context discipline, token budgets). Write to `{OUTPUT_DIR}/skills/{skillDirName}/research-protocol.md`.

**Step 8d -- provenance.md.** Read `provenance.md.tmpl`. Replace placeholders (audit tier behavior, reverifiable default, chain format). Write to `{OUTPUT_DIR}/skills/{skillDirName}/provenance.md`.

**Step 8e -- vvc-pipeline.md (only when VVC enabled).** Read `vvc-pipeline.md.tmpl`. Replace placeholders (claim types, verification scope, tier behavior, correction rules, VVC budget). Write to `{OUTPUT_DIR}/skills/{skillDirName}/vvc-pipeline.md`.

Steps 8a-8e are independent and can be executed in any order.
```

- [ ] **Step 3: Add `{{maxWebFetches}}` to Placeholder Derivation Rules (after line 303)**

Add a new row to the derivation rules table:

```markdown
| `{{maxWebFetches}}` | From `advanced.maxWebFetchesPerAgent` (default: 10) |
```

- [ ] **Step 4: Update Template Reference table (lines 328-343)**

Replace the row:
```
| `base-research-skill.md.tmpl` | Self-contained engine SKILL.md |
```
with:
```
| `orchestrator-skill.md.tmpl` | Self-contained engine orchestrator SKILL.md (~150-200 lines) |
| `standards.md.tmpl` | Confidence scoring, source credibility, citation rules |
| `research-protocol.md.tmpl` | Search protocol, iterative refinement, file isolation, WebFetch cap |
| `provenance.md.tmpl` | Phase 2.5 batch hashing, Phase 4.5 provenance audit |
| `vvc-pipeline.md.tmpl` | VVC Phases 5-6 instructions (conditional on VVC enabled) |
```

- [ ] **Step 5: Commit**

```bash
git add plugin/skills/engine-creator/SKILL.md
git commit -m "feat: update generation protocol — multi-file output, WebFetch cap wizard, placeholder rules"
```

---

## Task 10: Update `test-engine.md`

Update validation checks for the new generated engine structure.

**Files:**
- Modify: `plugin/commands/test-engine.md`

- [ ] **Step 1: Update Check 1 (plugin structure)**

Add to the file existence checks:
```
- `skills/*/standards.md`
- `skills/*/research-protocol.md`
- `skills/*/provenance.md`
- `skills/*/vvc-pipeline.md` (when `qualityFramework.vvc.enabled` is true in engine-config.json)
```

- [ ] **Step 2: Update Check 4 (config validity)**

Add new sub-checks:

```markdown
**4h: SKILL.md line count.** Count lines in `skills/*/SKILL.md`. Must be under 200 lines.

**4i: No per-fetch hashing.** Grep all files in `skills/*/` for "After each WebFetch". Must find 0 matches.

**4j: No shared file writes.** Grep all files in `skills/*/` and `agents/` for "Shared_Sources". Must find 0 matches.
```

- [ ] **Step 3: Update Check 4g (provenance validation)**

Change line 112 from:
```
- Read `skills/*/SKILL.md` and verify it contains "Source Hashing Protocol" section
```
to:
```
- Read `skills/*/provenance.md` and verify it contains "Batch Source Hashing" section
```

Change line 113 from:
```
- Read `skills/*/SKILL.md` and verify it contains "Phase 4.5: Provenance Audit" section
```
to:
```
- Read `skills/*/provenance.md` and verify it contains "Phase 4.5: Provenance Audit" section
```

Change line 115 from:
```
- Read agent `.md` files and verify they contain "PROVENANCE" instruction line
```
to:
```
- Read agent `.md` files and verify they reference `${CLAUDE_SKILL_DIR}/standards.md` as a first action
```

- [ ] **Step 4: Commit**

```bash
git add plugin/commands/test-engine.md
git commit -m "feat: update test-engine validation for split orchestrator structure"
```

---

## Task 11: Delete `base-research-skill.md.tmpl`

Retire the monolithic template now that all content has been distributed to the 5 new templates.

**Files:**
- Delete: `plugin/skills/engine-creator/templates/base-research-skill.md.tmpl`

- [ ] **Step 1: Verify no references remain**

Grep the entire `plugin/` directory for `base-research-skill.md.tmpl`. After Task 9, there should be 0 matches (the SKILL.md reference was replaced in Step 4).

- [ ] **Step 2: Delete the file**

```bash
git rm plugin/skills/engine-creator/templates/base-research-skill.md.tmpl
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: retire base-research-skill.md.tmpl — replaced by 5 focused templates"
```

---

## Task 12: Update Patent Example — Split SKILL.md

Rewrite the patent example engine to match the new generated structure.

**Files:**
- Rewrite: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md`
- Create: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/standards.md`
- Create: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/research-protocol.md`
- Create: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/provenance.md`
- Create: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/vvc-pipeline.md`

- [ ] **Step 1: Read current patent SKILL.md**

Read the full 943-line file to understand the patent-specific content.

- [ ] **Step 2: Create patent `standards.md`**

Extract from the patent SKILL.md:
- Confidence scoring framework (patent-specific criteria)
- Source credibility hierarchy (USPTO/EPO as Tier 1, etc.)
- Citation & evidence standards
- Validation rules
- Bibliography & footnote standards
- Source verification protocol

- [ ] **Step 3: Create patent `research-protocol.md`**

Extract:
- Context discipline
- Search query generation protocol (patent-specific templates: CPC/IPC classification, assignee portfolio, etc.)
- Iterative search-assess-refine protocol
- File isolation protocol (new — per-agent files)
- WebFetch cap of 10
- Failure recovery protocol
- Context management guidelines with token budgets

- [ ] **Step 4: Create patent `provenance.md`**

Write batch hashing (Phase 2.5) and provenance audit (Phase 4.5) instructions matching the template output, with patent-specific agent prefix conventions.

- [ ] **Step 5: Create patent `vvc-pipeline.md`**

Extract VVC content:
- Claim type taxonomy ([VC]/[PO]/[IE] with patent-specific additions if any)
- Verification scope table
- Phase 5 VVC-Verify instructions
- Phase 6 VVC-Correct instructions

- [ ] **Step 6: Rewrite patent `SKILL.md` as lean orchestrator**

Keep only:
- YAML frontmatter
- Usage block (add `--no-vvc`)
- Research architecture overview
- Phase 0 (add `--no-vvc` parsing)
- Sub-agent system
- Quick tier execution
- Standard/Deep/Comprehensive execution (Phases 1-4 as pointers to reference files)
- Phase 2.5 pointer
- Phase 4 with `--no-vvc` conditional
- Phase 4.5 pointer
- VVC phase placeholders
- File output structure (updated — no Shared_Sources.md, per-agent files)
- Key workflow features (updated)
- Domain preamble
- Operational lessons

- [ ] **Step 7: Verify line count**

Run: `wc -l plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md`
Expected: under 200 lines

- [ ] **Step 8: Commit**

```bash
git add plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/
git commit -m "feat: split patent example SKILL.md into orchestrator + reference files"
```

---

## Task 13: Update Patent Example — Agent Definitions

Update all 4 patent agent files to remove shared writes, add WebFetch cap, and add reference file loading.

**Files:**
- Modify: `plugin/examples/patent-intelligence-engine/agents/patent-search-specialist.md`
- Modify: `plugin/examples/patent-intelligence-engine/agents/prior-art-analyst.md`
- Modify: `plugin/examples/patent-intelligence-engine/agents/ip-landscape-mapper.md`
- Modify: `plugin/examples/patent-intelligence-engine/agents/vvc-specialist.md`

- [ ] **Step 1: Update patent-search-specialist.md**

- Remove any "Shared_Sources.md" references
- Remove any "PROVENANCE: After each WebFetch" instructions
- Add to Search Protocol: "Hard cap: 10 total WebFetch calls. If a URL returns 403/blocked/paywall, note and move on."
- Change methodology log references to per-agent: `Methodology_Log_patent-search-specialist.md`
- Add first actions section:
  ```
  ## First Actions
  1. Read `${CLAUDE_SKILL_DIR}/standards.md`
  2. Read `${CLAUDE_SKILL_DIR}/research-protocol.md`
  3. Read the research outline
  ```

- [ ] **Step 2: Update prior-art-analyst.md**

Same changes as Step 1, adapted for this agent's ID.

- [ ] **Step 3: Update ip-landscape-mapper.md**

Same changes as Step 1, adapted for this agent's ID.

- [ ] **Step 4: Update vvc-specialist.md**

- Remove any "Shared_Sources.md" references
- Add first action: `Read ${CLAUDE_SKILL_DIR}/vvc-pipeline.md`
- This agent does NOT need research-protocol.md (it runs in Phases 5-6, not Phase 2)

- [ ] **Step 5: Verify across all agents**

- Grep all agent files for "Shared_Sources" — should find 0 matches
- Grep all agent files for "After each WebFetch" — should find 0 matches
- Grep all agent files for "CLAUDE_SKILL_DIR" — should find matches in all 4 files

- [ ] **Step 6: Commit**

```bash
git add plugin/examples/patent-intelligence-engine/agents/
git commit -m "feat: update patent agents — file isolation, WebFetch cap, reference loading"
```

---

## Task 14: Update Patent Example — Config and README

**Files:**
- Modify: `plugin/examples/patent-intelligence-engine/engine-config.json`
- Modify: `plugin/examples/patent-intelligence-engine/README.md`

- [ ] **Step 1: Update engine-config.json**

Add `"maxWebFetchesPerAgent": 10` to the `advanced` object.

- [ ] **Step 2: Validate JSON**

Run: `python3 -c "import json; json.load(open('plugin/examples/patent-intelligence-engine/engine-config.json')); print('OK')"`

- [ ] **Step 3: Update README.md**

- Update the file structure section to show the split: `SKILL.md`, `standards.md`, `research-protocol.md`, `provenance.md`, `vvc-pipeline.md`
- Add `--no-vvc` to the usage/flags section
- Update any mention of Shared_Sources.md to per-agent file isolation

- [ ] **Step 4: Commit**

```bash
git add plugin/examples/patent-intelligence-engine/engine-config.json plugin/examples/patent-intelligence-engine/README.md
git commit -m "feat: update patent config and README for factory output fixes"
```

---

## Task 15: Final Validation

Run all validation criteria from the spec.

**Files:**
- All files from previous tasks

- [ ] **Step 1: Template-level checks**

```bash
# 1. base-research-skill.md.tmpl no longer exists
test ! -f plugin/skills/engine-creator/templates/base-research-skill.md.tmpl && echo "PASS: retired" || echo "FAIL"

# 2. orchestrator under 200 lines
lines=$(wc -l < plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl)
[ "$lines" -le 200 ] && echo "PASS: $lines lines" || echo "FAIL: $lines lines"

# 3. No per-fetch hashing in templates
count=$(grep -rl "After each WebFetch" plugin/skills/engine-creator/templates/ | wc -l)
[ "$count" -eq 0 ] && echo "PASS: no per-fetch hashing" || echo "FAIL: $count files"

# 4. No Shared_Sources in templates
count=$(grep -rl "Shared_Sources" plugin/skills/engine-creator/templates/ | wc -l)
[ "$count" -eq 0 ] && echo "PASS: no shared sources" || echo "FAIL: $count files"

# 5. WebFetch cap in research-protocol
grep -q "maxWebFetches" plugin/skills/engine-creator/templates/research-protocol.md.tmpl && echo "PASS" || echo "FAIL"

# 6. --no-vvc in orchestrator Phase 0
grep -q "\-\-no-vvc" plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl && echo "PASS" || echo "FAIL"

# 7. Phase 4 --no-vvc conditional in orchestrator
grep -q "Professional Reporting" plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl && echo "PASS: Phase 4 conditional" || echo "FAIL"

# 8. Phase 2.5 batch hashing
grep -q "general-purpose" plugin/skills/engine-creator/templates/provenance.md.tmpl && echo "PASS" || echo "FAIL"

# 9. Per-agent file references use {AgentID} suffix
grep -q "Methodology_Log_\[AgentID\]" plugin/skills/engine-creator/templates/research-protocol.md.tmpl && echo "PASS: methodology log" || echo "FAIL"
grep -q "Sources_\[AgentID\]" plugin/skills/engine-creator/templates/research-protocol.md.tmpl && echo "PASS: sources" || echo "FAIL"
```

- [ ] **Step 2: Schema checks**

```bash
# 10. maxWebFetchesPerAgent in engine-config-schema
grep -q "maxWebFetchesPerAgent" plugin/skills/engine-creator/templates/engine-config-schema.json && echo "PASS" || echo "FAIL"

# 11. maxWebFetchesPerAgent in preset-schema
grep -q "maxWebFetchesPerAgent" plugin/skills/engine-creator/templates/preset-schema.json && echo "PASS" || echo "FAIL"
```

- [ ] **Step 3: Generation protocol checks**

```bash
# 12. Step 8 multi-file
grep -q "Step 8a" plugin/skills/engine-creator/SKILL.md && echo "PASS" || echo "FAIL"

# 13. Section 8 WebFetch cap
grep -q "WebFetch calls per agent" plugin/skills/engine-creator/SKILL.md && echo "PASS" || echo "FAIL"

# 14. Post-generation mentions multi-file structure
grep -q "standards.md" plugin/skills/engine-creator/SKILL.md && echo "PASS: post-gen file list" || echo "FAIL"
```

- [ ] **Step 4: Example engine checks**

```bash
# 15. Patent SKILL.md under 200 lines
lines=$(wc -l < plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md)
[ "$lines" -le 200 ] && echo "PASS: $lines lines" || echo "FAIL: $lines lines"

# 16. Reference files exist
for f in standards.md research-protocol.md provenance.md vvc-pipeline.md; do
  test -f "plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/$f" && echo "PASS: $f" || echo "FAIL: $f"
done

# 17. Agents reference CLAUDE_SKILL_DIR
count=$(grep -rl "CLAUDE_SKILL_DIR" plugin/examples/patent-intelligence-engine/agents/ | wc -l)
[ "$count" -eq 4 ] && echo "PASS: all 4 agents" || echo "FAIL: $count agents"

# 18. No Shared_Sources in agents
count=$(grep -rl "Shared_Sources" plugin/examples/patent-intelligence-engine/agents/ | wc -l)
[ "$count" -eq 0 ] && echo "PASS" || echo "FAIL: $count files"

# 19. maxWebFetchesPerAgent in config
grep -q "maxWebFetchesPerAgent" plugin/examples/patent-intelligence-engine/engine-config.json && echo "PASS" || echo "FAIL"
```

- [ ] **Step 5: Final commit if all pass**

```bash
git add -A
git status
# Only commit if there are remaining uncommitted changes
git diff --cached --quiet || git commit -m "chore: final validation pass — all checks green"
```
