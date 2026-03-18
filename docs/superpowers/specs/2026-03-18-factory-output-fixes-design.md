# Factory Output Fixes — Design Spec

**Date:** 2026-03-18
**Source:** Post-mortem analysis of RICS AI Governance research run
**Scope:** Changes to the engine factory templates so that generated engines no longer exhibit 5 performance/correctness problems identified in [`deep-research-engine-fixes.md`](../../../deep-research-engine-fixes.md)

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
- Lines 145-164: Entire "Source Hashing Protocol" section under Global Standards
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
- Lines 79-84: Entire "Cross-Agent Coordination" section (header + body)

**Change per-agent file naming:**
- Claims: `{SLUG}_Claims_{AgentID}.md` (already per-agent, no change)
- Bibliography: `{SLUG}_{AgentID}_Bibliography.md` (already per-agent, no change)
- Methodology log: `{SLUG}_Methodology_Log_{AgentID}.md` (new — currently shared)
- Sources: `{SLUG}_Sources_{AgentID}.md` (new — replaces Shared_Sources.md)

**Update Phase 3 synthesis:** Add explicit instruction to read all per-agent source files and methodology logs, deduplicate, and cross-reference into consolidated files (`{SLUG}_Methodology_Log.md` and `{SLUG}_Sources.md`).

**Update Phase 4.5 provenance audit:** The provenance audit cross-references methodology logs. Update `provenance.md.tmpl` to read the consolidated `{SLUG}_Methodology_Log.md` produced by Phase 3 synthesis (not the per-agent files directly).

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

### Extension Template (`extension-skill.md.tmpl`)

The extension template (280 lines) overlays on a base `/deep-research` skill and inherits its protocols. It is affected by all 5 fixes:

**Fix 1 (line 126):** Replace "The base skill's Source Hashing Protocol applies to all agents in this extension." with: "Provenance uses batch hashing (Phase 2.5). The base skill's batch hashing agent collects all cited URLs after Phase 2 completes and hashes them in a single sequential pass. Per-fetch hashing is not used."

**Fix 3 (line 211):** Remove "Cross-Agent Coordination Protocol" from the inherited protocols list (lines 209-215). Add to the overrides section above it: "### File Isolation Override\n\nEach Phase 2 agent writes to its own files only. No shared files during parallel research.\n- Sources: `{SLUG}_Sources_{AgentID}.md`\n- Methodology log: `{SLUG}_Methodology_Log_{AgentID}.md`\n\nPhase 3 synthesis consolidates per-agent files." The inherited list becomes:
```
- Iterative Search-Assess-Refine Protocol
- Failure Recovery Protocol
- Context Management Guidelines
- Bibliography and Footnote Standards
- Search Query Generation Protocol (extended by domain-specific templates above)
```

**Fix 4:** Add to the extension's flag parsing section (near line 80-90 where tier flags are handled): "- If `--no-vvc` is present: skip Phases 5-6, Phase 4 becomes final reporting (heading: Professional Reporting, output: `_Comprehensive_Report.md`, claim tagging skipped)."

**Fix 5:** Add to the "Agent Pipeline Override" section (near line 100): "All Phase 2 agents: cap total WebFetch calls at {{maxWebFetches}}. If a URL returns 403/blocked/paywall, note in methodology log and move on."

**Fix 6:** The extension template does not need splitting — it is already lean by design (~280 lines, inherits most content from the base skill). However, the inherited protocols list (lines 209-215) must reflect that the base skill now uses split reference files. No structural change needed.

**Approach:** Update `extension-skill.md.tmpl` in-place with the specific text changes above. It remains a single template.

### Domain Presets

21 preset JSON files exist in `domain-presets/`. The new `advanced.maxWebFetchesPerAgent` field is added to `preset-schema.json` with a default of 10. Presets that omit this field inherit the schema default — no individual preset file updates are required. The generation protocol already falls back to schema defaults for missing optional fields.

---

## Section 3: Generation Protocol Changes

### Step 8 — Multi-File Output

**Replace the entire Step 8 block (SKILL.md lines 246-253)** including the template selection, placeholder substitution rules, and missing-optionals handling. The placeholder substitution rules (simple values, arrays, objects, nested, subAgentList, fileStructure, missing optionals) apply to all sub-steps below and should be stated once at the top of the new Step 8.

**New Step 8:** "Select template set by mode. Extension mode: read `extension-skill.md.tmpl`, replace placeholders, write single file to `{OUTPUT_DIR}/skills/{skillDirName}/SKILL.md`. Self-contained mode: execute Steps 8a-8e below."

**Step 8a — Orchestrator SKILL.md:** Read `orchestrator-skill.md.tmpl`. Replace placeholders (engine metadata, tier config, phase overview, agent roster, domain preamble, Phase 0 flags including `--no-vvc`, execution strategy pointers). Write to `{OUTPUT_DIR}/skills/{skillDirName}/SKILL.md`.

**Step 8b — standards.md:** Read `standards.md.tmpl`. Replace placeholders (confidence scoring, source hierarchy, citation standard, validation rules, evidence rules). Write to `{OUTPUT_DIR}/skills/{skillDirName}/standards.md`.

**Step 8c — research-protocol.md:** Read `research-protocol.md.tmpl`. Replace placeholders (search templates, preferred sites, maxIterations, maxWebFetches, explorationDepth, per-agent file naming, context discipline). Write to `{OUTPUT_DIR}/skills/{skillDirName}/research-protocol.md`.

**Step 8d — provenance.md:** Read `provenance.md.tmpl`. Replace placeholders (agent prefixes, audit tier behavior, reverifiable default, chain format). Write to `{OUTPUT_DIR}/skills/{skillDirName}/provenance.md`.

**Step 8e — vvc-pipeline.md (conditional on VVC enabled):** Read `vvc-pipeline.md.tmpl`. Replace placeholders (claim types, verification scope, tier behavior, correction rules, VVC budget). Write to `{OUTPUT_DIR}/skills/{skillDirName}/vvc-pipeline.md`.

### Other Protocol Updates

**Step 2 (directory creation):** No new directories needed — reference files live in `skills/{skillDirName}/` alongside SKILL.md.

**Step 5 (/research command):** Add `--no-vvc` to usage block.

**Wizard Section 8:** Add question: "Max WebFetch calls per agent? Default: 10" → stored as `advanced.maxWebFetchesPerAgent`.

**Placeholder Derivation Rules table (SKILL.md lines 258-303):** Add row:

| Placeholder | Derivation Rule |
|---|---|
| `{{maxWebFetches}}` | From `advanced.maxWebFetchesPerAgent` (default: 10) |

**Template Reference table (SKILL.md lines 328-343):** Replace the `base-research-skill.md.tmpl` row with:

| Template | Purpose |
|---|---|
| `orchestrator-skill.md.tmpl` | Self-contained engine orchestrator SKILL.md (~150-200 lines) |
| `standards.md.tmpl` | Confidence scoring, source credibility, citation rules |
| `research-protocol.md.tmpl` | Search protocol, iterative refinement, file isolation, WebFetch cap |
| `provenance.md.tmpl` | Phase 2.5 batch hashing, Phase 4.5 provenance audit |
| `vvc-pipeline.md.tmpl` | VVC Phases 5-6 instructions (conditional on VVC enabled) |

The `extension-skill.md.tmpl` row remains unchanged.

**Wizard Section 8 placement:** The WebFetch cap question is asked only when the user selects "Yes" to "Configure advanced settings?" (SKILL.md line 171). It appears alongside max iterations, exploration depth, and token budgets. When the user selects "No," the default of 10 is used.

**Step ordering:** Steps 8a-8e are independent — no step depends on output from a prior step. They can be executed in any order or parallelized.

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

### Modified Files (continued)
- `plugin/skills/engine-creator/templates/extension-skill.md.tmpl` — update inherited protocol references, add `--no-vvc` flag, add WebFetch cap, remove Shared_Sources.md references

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

---

## Migration

Engines previously generated from `base-research-skill.md.tmpl` have the old monolithic SKILL.md with per-fetch hashing, Shared_Sources.md, and no WebFetch cap. These engines are **out of scope** for this spec — they continue to work as-is but carry the performance/correctness issues.

Owners of existing engines have two options:
1. **Regenerate** using the updated factory (recommended). Run `/create-engine` with the same domain preset and config choices.
2. **Manual migration.** Apply the fixes from `deep-research-engine-fixes.md` directly to the engine's SKILL.md by hand.

A future `/upgrade-engine` command could automate option 2 but is not part of this spec.

---

## Placeholder Reference

Each new template includes a placeholder reference section at the bottom listing all placeholders it uses. The `{{maxWebFetches}}` placeholder appears in `orchestrator-skill.md.tmpl` (usage block), `research-protocol.md.tmpl` (cap instruction), and `agent-template.md.tmpl` (search protocol).
