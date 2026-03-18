# Factory Output Fixes — Design Spec

**Date:** 2026-03-18
**Source:** Post-mortem analysis of RICS AI Governance research run
**Scope:** Changes to the engine factory templates so that generated engines no longer exhibit 5 performance/correctness problems identified in `deep-research-engine-fixes.md`

---

## Context

The deep-research-engine-creator is a factory that produces domain-specialized research engines as Claude Code plugins. The fixes document identifies 7 problems observed in a generated engine at runtime. Two are already solved by the factory's architecture (Fix 2: Bash access via explicit tools lists; Fix 7: already generates skills, not commands). Five require template changes so that future generated engines are fixed at birth.

**Key insight:** The fixes target what the factory *produces*, not the factory itself. Every change below modifies templates, schemas, and the generation protocol so that the output plugins are correct.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Fix 6 (split orchestrator) | Include in this spec | All fixes are interdependent; Fix 6 restructures the file that Fixes 1/3/4/5 modify |
| Phase 2.5 batch hashing executor | Dedicated `general-purpose` subagent | Consistent with Phase 4.5 audit pattern; clean separation of concerns |
| Real-time deduplication (Shared_Sources.md) | Accept the loss | No file locking primitive exists; race conditions caused crashes. Phase 1 task partitioning and Fix 5 WebFetch cap mitigate duplicate fetches |
| `--no-vvc` Phase 4 behavior | Runtime adaptation | Phase 4 switches from "Draft Reporting" to "Professional Reporting" when `--no-vvc` is present, including filename and claim tagging changes |
| WebFetch cap | Configurable, default 10 | Different domains have different needs; exposed in wizard Section 8 advanced settings |
| Reference file loading | Agents read files as first action | Keeps orchestrator SKILL.md lean (~150-200 lines); agents load only what they need |
| Implementation order | Template-first (Approach A) | Templates are the source of truth; define output structure first, update generation protocol second, update example last |

---

## Section 1: New Generated Engine Structure

### Before (current)

```
skills/{name}/
└── SKILL.md                    # 782+ lines, everything in one file
```

### After

```
skills/{name}/
├── SKILL.md                    # ~150-200 lines — orchestrator only
├── standards.md                # confidence scoring, source credibility, citation rules, validation
├── research-protocol.md        # search protocol, iterative refinement, file isolation, WebFetch cap
├── provenance.md               # Phase 2.5 batch hashing, Phase 4.5 audit, hash chain format
└── vvc-pipeline.md             # Phases 5-6 instructions, claim taxonomy (only when VVC enabled)
```

### File Responsibilities

**SKILL.md (orchestrator):** Usage block, Phase 0 (tier detection + all flag parsing including `--no-vvc`), phase overview, tier config table, agent roster, execution strategy (Phases 1-4 as deployment instructions with pointers to reference files), file output structure, domain preamble. Everything the orchestrator needs to route and dispatch — nothing agents need for detailed instructions.

**standards.md:** Confidence scoring framework (HIGH/MEDIUM/LOW/SPECULATIVE), source credibility hierarchy (5 tiers), citation & evidence standards, bibliography dedup rules, structured output standards, validation rules. Read by all agents as first action.

**research-protocol.md:** Search query generation protocol, iterative search-assess-refine protocol, per-agent file isolation rules, WebFetch cap, failure recovery protocol, context discipline guidelines, token budgets. Read by Phase 2 research agents.

**provenance.md:** Phase 2.5 batch hashing protocol, Phase 4.5 provenance audit instructions, hash chain format, provenance log structure, independent verification instructions. Read by the batch hashing agent (Phase 2.5) and the provenance audit agent (Phase 4.5).

**vvc-pipeline.md (conditional):** Claim type taxonomy ([VC]/[PO]/[IE] + custom types), verification scope table, Phase 5 VVC-Verify instructions, Phase 6 VVC-Correct instructions, correction rules (KEEP/REVISE/DOWNGRADE/REMOVE/REPLACE_SOURCE). Read by the VVC specialist agent. Only generated when VVC is enabled in engine config.

### Agent Loading Pattern

Every Phase 2 research agent's first action:
1. Read `${CLAUDE_SKILL_DIR}/standards.md`
2. Read `${CLAUDE_SKILL_DIR}/research-protocol.md`
3. Read `BASE_DIR/{SLUG}_Research_Outline.md`

VVC specialist: reads `${CLAUDE_SKILL_DIR}/vvc-pipeline.md`
Batch hashing agent (Phase 2.5): reads `${CLAUDE_SKILL_DIR}/provenance.md`
Provenance audit agent (Phase 4.5): reads `${CLAUDE_SKILL_DIR}/provenance.md`

---

## Section 2: Template Changes — Fix by Fix

### Fix 1: Batch Hashing (Per-Fetch to Phase 2.5)

**Remove from current `base-research-skill.md.tmpl` (before retirement):**
- Lines 145-165: Entire "Source Hashing Protocol" section under Global Standards
- Line 356: "PROVENANCE: After each WebFetch, apply the Source Hashing Protocol" from Common Agent Requirements
- Lines 85-87: Provenance setup that creates Hash_Manifest.md in Phase 0

**Add to new `provenance.md.tmpl`:**

Phase 2.5 instructions — deploy a `general-purpose` subagent that:
1. Reads all `{SLUG}_{AgentID}_Bibliography.md` files from completed Phase 2 agents
2. Collects all unique URLs across all bibliographies
3. Deduplicates URLs
4. Creates `BASE_DIR/{SLUG}_Hash_Manifest.md` with header row
5. For each unique URL sequentially: fetch content, write to temp file, sha256sum, compute event hash using chain format `[SHA-256]|[URL]|[TIMESTAMP]|[AGENT_ID]|[PREV_HASH]`, append row to Hash_Manifest.md
6. If `--reverifiable`: retain snapshots in `BASE_DIR/Source_Snapshots/`; otherwise delete after hashing

Phase 4.5 audit instructions relocated from current lines 428-469, largely unchanged.

Hash chain format reference, provenance log structure, and independent verification instructions.

**Net effect:** ~72 fewer tool calls per run. Hashing happens once, sequentially, with no race conditions.

### Fix 3: File Isolation (Eliminate Shared Writes)

**Remove:**
- Entire "Cross-Agent Coordination Protocol" section (Shared_Sources.md)
- All references to "coordinates through Shared_Sources.md"
- "Read... Shared_Sources.md" from Common Agent Requirements
- "Append high-value sources to Shared_Sources.md"
- `Shared_Sources.md` from file output structure
- "Cross-agent Shared_Sources.md prevents duplicate work" from Key Workflow Features

**Remove from `agent-template.md.tmpl`:**
- Lines 81-84: Entire "Cross-Agent Coordination" section

**Change per-agent file naming:**
- Claims: `{SLUG}_Claims_{AgentID}.md` (already per-agent, no change)
- Bibliography: `{SLUG}_{AgentID}_Bibliography.md` (already per-agent, no change)
- Methodology log: `{SLUG}_Methodology_Log_{AgentID}.md` (new — currently shared)
- Sources: `{SLUG}_Sources_{AgentID}.md` (new — replaces Shared_Sources.md)

**Update Phase 3 synthesis:** Add explicit instruction to read all per-agent source files and methodology logs, deduplicate, and cross-reference.

**Net effect:** Zero race conditions. Duplicate fetches mitigated by WebFetch cap and Phase 1 task partitioning.

### Fix 4: `--no-vvc` Runtime Flag

**Add to Phase 0 flag parsing in `orchestrator-skill.md.tmpl`:**
- `--no-vvc`: "If present and engine has VVC enabled, skip Phases 5-6. Phase 4 becomes final reporting."

**Add conditional logic to Phase 4:**

When `--no-vvc` is active on a VVC-enabled engine:
- Phase 4 heading: "Professional Reporting" (not "Draft Reporting")
- Claim tagging instructions ([VC]/[PO]/[IE]): skipped
- Output file: `_Comprehensive_Report.md` (not `_Draft_Report.md`)
- Phases 5-6: skipped entirely

Template emits this as a conditional block: "If `--no-vvc` flag is present: [adapted behavior]. Otherwise: [standard VVC behavior]."

**Net effect:** Runtime VVC control without engine regeneration.

### Fix 5: Configurable WebFetch Cap (Default 10)

**Add to `research-protocol.md.tmpl`:**
- "Cap total WebFetch calls at {{maxWebFetches}}. If a URL returns 403/blocked/paywall, note it in methodology log and move on — do not retry."

**Add to `agent-template.md.tmpl`:**
- In Search Protocol section: "Hard cap: {{maxWebFetches}} total WebFetch calls per research session. Prioritize highest-credibility, most-accessible sources."

**New config field:** `advanced.maxWebFetchesPerAgent` (integer, min 1, max 50, default 10)
**New placeholder:** `{{maxWebFetches}}`
**Wizard Section 8:** "Max WebFetch calls per agent? Default: 10"

**Net effect:** ~40% reduction in agent runtime. Configurable per domain.

### Fix 6: Split Orchestrator

**Retire `base-research-skill.md.tmpl` (782 lines).** Replace with:

| New Template | Source Content (from retired template) | Approx Lines |
|---|---|---|
| `orchestrator-skill.md.tmpl` | Usage, Phase 0, phase overview, tier config, agent roster, execution strategy (Phases 1-4 as pointers), file output, domain preamble, operational lessons | 150-200 |
| `standards.md.tmpl` | Global Standards section (confidence, credibility, citation, validation, structured output, bibliography) | 100-130 |
| `research-protocol.md.tmpl` | Search query protocol, iterative refinement, file isolation (Fix 3), WebFetch cap (Fix 5), failure recovery, context discipline, token budgets | 100-130 |
| `provenance.md.tmpl` | Phase 2.5 batch hashing (Fix 1), Phase 4.5 audit, hash chain format, provenance log | 80-100 |
| `vvc-pipeline.md.tmpl` | Claim taxonomy, verification scope, Phase 5, Phase 6, correction rules (conditional) | 80-100 |

Total across all files: ~510-660 lines (down from 782 monolithic, but the orchestrator system prompt drops to ~150-200).

---

## Section 3: Generation Protocol Changes

### Step 8 — Multi-File Output

Current Step 8 reads one template, writes one file. New Step 8:

**Step 8a — Orchestrator SKILL.md:** Read `orchestrator-skill.md.tmpl`. Replace placeholders (engine metadata, tier config, phase overview, agent roster, domain preamble, Phase 0 flags including `--no-vvc`, execution strategy pointers). Write to `{OUTPUT_DIR}/skills/{skillDirName}/SKILL.md`.

**Step 8b — standards.md:** Read `standards.md.tmpl`. Replace placeholders (confidence scoring, source hierarchy, citation standard, validation rules, evidence rules). Write to `{OUTPUT_DIR}/skills/{skillDirName}/standards.md`.

**Step 8c — research-protocol.md:** Read `research-protocol.md.tmpl`. Replace placeholders (search templates, preferred sites, maxIterations, maxWebFetches, explorationDepth, per-agent file naming, context discipline). Write to `{OUTPUT_DIR}/skills/{skillDirName}/research-protocol.md`.

**Step 8d — provenance.md:** Read `provenance.md.tmpl`. Replace placeholders (agent prefixes, audit tier behavior, reverifiable default, chain format). Write to `{OUTPUT_DIR}/skills/{skillDirName}/provenance.md`.

**Step 8e — vvc-pipeline.md (conditional on VVC enabled):** Read `vvc-pipeline.md.tmpl`. Replace placeholders (claim types, verification scope, tier behavior, correction rules, VVC budget). Write to `{OUTPUT_DIR}/skills/{skillDirName}/vvc-pipeline.md`.

### Other Protocol Updates

**Step 2 (directory creation):** No new directories needed — reference files live in `skills/{skillDirName}/` alongside SKILL.md.

**Step 5 (/research command):** Add `--no-vvc` to usage block.

**Wizard Section 8:** Add question: "Max WebFetch calls per agent? Default: 10" → stored as `advanced.maxWebFetchesPerAgent`.

**Placeholder Derivation Rules:** Add `{{maxWebFetches}}` → from `advanced.maxWebFetchesPerAgent` (default: 10).

**Post-generation file list:** Updated to show multi-file structure.

### Schema Updates

**`engine-config-schema.json`:** Add `advanced.maxWebFetchesPerAgent` — type: integer, minimum: 1, maximum: 50, default: 10, description: "Maximum WebFetch calls per research agent per run."

**`preset-schema.json`:** Add same field to preset advanced config.

### Test Engine Updates

**`test-engine.md` Check 1 (plugin structure):** Verify reference files exist alongside SKILL.md (`standards.md`, `research-protocol.md`, `provenance.md`, and `vvc-pipeline.md` when VVC enabled).

**`test-engine.md` Check 4 (config validity):** Add validations:
- SKILL.md is under 200 lines
- No file contains "After each WebFetch" + hashing instructions
- No file contains "Shared_Sources.md" or "append to Shared_Sources"

---

## Section 4: Example Engine Update

The patent intelligence engine (`plugin/examples/patent-intelligence-engine/`) is manually authored and serves as reference documentation.

### Split SKILL.md (943 lines) Into:

- `skills/patent-intelligence-engine/SKILL.md` — ~150-200 lines, orchestrator with patent domain preamble
- `skills/patent-intelligence-engine/standards.md` — patent domain credibility hierarchy (USPTO/EPO Tier 1, etc.), confidence scoring
- `skills/patent-intelligence-engine/research-protocol.md` — patent search protocol, CPC/IPC classification queries, iterative refinement, file isolation, WebFetch cap of 10
- `skills/patent-intelligence-engine/provenance.md` — batch hashing, provenance audit
- `skills/patent-intelligence-engine/vvc-pipeline.md` — patent-specific VVC instructions

### Update Agent Definitions:

All 4 agents (`patent-search-specialist.md`, `prior-art-analyst.md`, `ip-landscape-mapper.md`, `vvc-specialist.md`):
- Remove Shared_Sources.md references
- Add WebFetch cap of 10
- Add reference file loading (`${CLAUDE_SKILL_DIR}/standards.md`, `${CLAUDE_SKILL_DIR}/research-protocol.md`) as first action
- `vvc-specialist.md` references `${CLAUDE_SKILL_DIR}/vvc-pipeline.md` instead of inline instructions

### Update engine-config.json:

- Add `advanced.maxWebFetchesPerAgent: 10`

### Update README.md:

- Reflect new file structure
- Add `--no-vvc` flag to usage section

---

## Section 5: Validation Criteria

### Template-Level Checks

1. `base-research-skill.md.tmpl` no longer exists (retired)
2. `orchestrator-skill.md.tmpl` is under 200 lines
3. No template file contains "After each WebFetch" + hashing instructions
4. No template file contains "Shared_Sources.md" or "append to Shared_Sources"
5. `research-protocol.md.tmpl` contains `{{maxWebFetches}}` cap instruction
6. `orchestrator-skill.md.tmpl` Phase 0 parses `--no-vvc`
7. `orchestrator-skill.md.tmpl` Phase 4 has conditional behavior for `--no-vvc`
8. `provenance.md.tmpl` contains Phase 2.5 batch hashing with `general-purpose` subagent
9. All per-agent file references use `{AgentID}` suffix (methodology log, sources)

### Schema Checks

10. `engine-config-schema.json` includes `advanced.maxWebFetchesPerAgent` with default 10
11. `preset-schema.json` includes same field

### Generation Protocol Checks

12. Engine-creator `SKILL.md` Step 8 emits 4-5 files (not 1)
13. Section 8 wizard asks about WebFetch cap
14. Post-generation file list shows multi-file structure

### Example Engine Checks

15. Patent example `SKILL.md` is under 200 lines
16. Patent example has `standards.md`, `research-protocol.md`, `provenance.md`, `vvc-pipeline.md` alongside SKILL.md
17. Patent example agents reference `${CLAUDE_SKILL_DIR}/` files as first action
18. Patent example agents have no Shared_Sources.md references
19. Patent example `engine-config.json` has `maxWebFetchesPerAgent: 10`

### Smoke Test

20. Run `/test-engine` against the updated patent example — all 5 checks pass

---

## Files Changed

### New Template Files (in `plugin/skills/engine-creator/templates/`)
- `orchestrator-skill.md.tmpl` (new, ~150-200 lines)
- `standards.md.tmpl` (new, ~100-130 lines)
- `research-protocol.md.tmpl` (new, ~100-130 lines)
- `provenance.md.tmpl` (new, ~80-100 lines)
- `vvc-pipeline.md.tmpl` (new, ~80-100 lines)

### Retired Template Files
- `base-research-skill.md.tmpl` (deleted, 782 lines)

### Modified Files
- `plugin/skills/engine-creator/SKILL.md` — Step 8 multi-file output, Section 8 WebFetch cap question, placeholder derivation rules
- `plugin/skills/engine-creator/templates/agent-template.md.tmpl` — remove Cross-Agent Coordination, add WebFetch cap, add reference file loading
- `plugin/skills/engine-creator/templates/engine-config-schema.json` — add `maxWebFetchesPerAgent`
- `plugin/skills/engine-creator/templates/preset-schema.json` — add `maxWebFetchesPerAgent`
- `plugin/commands/test-engine.md` — updated structural and content validation checks

### Example Engine Files (in `plugin/examples/patent-intelligence-engine/`)
- `skills/patent-intelligence-engine/SKILL.md` — rewritten as lean orchestrator
- `skills/patent-intelligence-engine/standards.md` (new)
- `skills/patent-intelligence-engine/research-protocol.md` (new)
- `skills/patent-intelligence-engine/provenance.md` (new)
- `skills/patent-intelligence-engine/vvc-pipeline.md` (new)
- `agents/patent-search-specialist.md` — updated
- `agents/prior-art-analyst.md` — updated
- `agents/ip-landscape-mapper.md` — updated
- `agents/vvc-specialist.md` — updated
- `engine-config.json` — add `maxWebFetchesPerAgent`
- `README.md` — updated structure and usage
