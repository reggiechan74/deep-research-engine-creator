# Factory Template Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 8 template-level bugs in the engine creator factory so all future generated engines have correct VVC agent instructions, budget-safe exploration depth, comprehensive follow-up rounds, and consistent prompt engineering.

**Architecture:** Changes are pure markdown template edits and generation logic updates in SKILL.md. No code compilation or build system — the factory uses prompt-driven placeholder substitution. Validation uses grep checks and `/test-engine` against regenerated engines.

**Tech Stack:** Markdown templates with `{{placeholder}}` substitution, JSON Schema, Claude Code plugin system

**Spec:** `docs/superpowers/specs/2026-03-18-factory-template-fixes-design.md`

---

### Task 1: Schema — Add new config fields and update defaults

**Files:**
- Modify: `plugin/skills/engine-creator/templates/engine-config-schema.json:664-737` (advanced section)

This task has no dependencies and establishes the schema foundation for later template changes.

- [ ] **Step 1: Add `comprehensiveFollowUpAgentCap` to advanced properties**

In `engine-config-schema.json`, inside the `"advanced"` > `"properties"` object (after the `maxWebFetchesPerAgent` property at line 730-736), add:

```json
"comprehensiveFollowUpAgentCap": {
  "type": "integer",
  "description": "Maximum agents to deploy in Phase 3.5 comprehensive follow-up round",
  "default": 2,
  "minimum": 1,
  "maximum": 5
}
```

- [ ] **Step 2: Add `provenance` to tokenBudgets properties**

In `engine-config-schema.json`, inside `"advanced"` > `"properties"` > `"tokenBudgets"` > `"properties"` (after the `vvc` property at line 705-710), add:

```json
"provenance": {
  "type": "integer",
  "description": "Token budget for provenance audit and citation verification phase",
  "default": 5000,
  "minimum": 0,
  "examples": [5000]
}
```

- [ ] **Step 3: Change explorationDepth default from 5 to 2**

In `engine-config-schema.json`, at line 718-724, change `"default": 5` to `"default": 2` and update description:

```json
"explorationDepth": {
  "type": "integer",
  "description": "Maximum depth for follow-on link exploration from source pages",
  "default": 2,
  "minimum": 1,
  "maximum": 10
}
```

- [ ] **Step 4: Verify schema is valid JSON**

Run: `python3 -c "import json; json.load(open('plugin/skills/engine-creator/templates/engine-config-schema.json'))"`
Expected: No output (success)

- [ ] **Step 5: Commit**

```bash
git add plugin/skills/engine-creator/templates/engine-config-schema.json
git commit -m "fix: add comprehensiveFollowUpAgentCap, provenance budget, update explorationDepth default to 2"
```

---

### Task 2: Template — Fix `research-protocol.md.tmpl` (M-1, M-2)

**Files:**
- Modify: `plugin/skills/engine-creator/templates/research-protocol.md.tmpl:8,124`

Two simple line replacements. No dependencies.

- [ ] **Step 1: Align chat response limit to 450 tokens**

At line 8, replace:
```
- Each agent chat response of 500 tokens or fewer; avoid meta narration
```
With:
```
- Each agent chat response of 450 tokens or fewer; avoid meta narration
```

- [ ] **Step 2: Parameterize provenance budget**

At line 124, replace:
```
Provenance Audit: 5K tokens output max
```
With:
```
Provenance Audit: {{provenanceBudget}} tokens output max
```

- [ ] **Step 3: Add `provenanceBudget` to Placeholder Reference section**

At the end of the Placeholder Reference section (after the `{{vvcBudgetLine}}` entry around line 161), add:

```
- `{{provenanceBudget}}` -- token budget for provenance audit and citation verification phase (default: 5000)
```

- [ ] **Step 4: Verify no "500 tokens" remains**

Run grep on the file for "500 tokens" — should find 0 matches.

- [ ] **Step 5: Commit**

```bash
git add plugin/skills/engine-creator/templates/research-protocol.md.tmpl
git commit -m "fix(M-1,M-2): align 450 token limit, parameterize provenance budget"
```

---

### Task 3: Template — Fix `command-template.md.tmpl` (C-4)

**Files:**
- Modify: `plugin/skills/engine-creator/templates/command-template.md.tmpl:3`

Single line edit. No dependencies.

- [ ] **Step 1: Add `{{vvcArgumentHint}}` to argument-hint**

At line 3, replace:
```
argument-hint: "[research topic] [--quick|--standard|--deep|--comprehensive] [--approve] [--no-approve] [--outline-only] [--extend] [--reverifiable]"
```
With:
```
argument-hint: "[research topic] [--quick|--standard|--deep|--comprehensive] [--approve] [--no-approve] [--outline-only] [--extend] [--reverifiable]{{vvcArgumentHint}}"
```

- [ ] **Step 2: Commit**

```bash
git add plugin/skills/engine-creator/templates/command-template.md.tmpl
git commit -m "fix(C-4): add --no-vvc to command argument-hint when VVC enabled"
```

---

### Task 4: Template — Fix `standards.md.tmpl` (H-2, M-3)

**Files:**
- Modify: `plugin/skills/engine-creator/templates/standards.md.tmpl:22,110,184`

- [ ] **Step 1: Replace claim taxonomy block with summary placeholder (M-3)**

At line 22, replace:
```
{{vvcClaimTaxonomyBlock}}
```
With:
```
{{vvcClaimTaxonomySummary}}
```

- [ ] **Step 2: Add probe-on-discovery budget note (H-2)**

After line 110 (`- This prevents wasted analysis on sources that cannot be independently verified`), add:

```
- **Budget note:** Probe fetches count toward the per-agent WebFetch cap. When probe-on-discovery is enabled, reserve at least 4 WebFetch calls for content retrieval by limiting probes to the top 6 candidate URLs per session. Skip probing Tier 1 government domains (assumed accessible).
```

- [ ] **Step 3: Update Placeholder Reference**

In the Placeholder Reference table at the bottom (around line 184), replace the entry for `{{vvcClaimTaxonomyBlock}}`:
```
| `{{vvcClaimTaxonomyBlock}}` | VVC claim taxonomy block (may be empty) |
```
With:
```
| `{{vvcClaimTaxonomySummary}}` | VVC claim taxonomy summary with cross-reference to vvc-pipeline.md (may be empty when VVC disabled) |
```

- [ ] **Step 4: Commit**

```bash
git add plugin/skills/engine-creator/templates/standards.md.tmpl
git commit -m "fix(H-2,M-3): add probe budget note, deduplicate claim taxonomy to cross-reference"
```

---

### Task 5: Template — Fix `orchestrator-skill.md.tmpl` (C-3, H-3, H-5, H-6)

**Files:**
- Modify: `plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl:105,121-135,141,198`

Four changes in one file. Apply top-to-bottom to avoid line number shifts.

- [ ] **Step 1: Fix exploration depth instruction (C-3)**

At line 105, replace:
```
8. Recursive web exploration up to {{explorationDepth}} levels deep from seed URLs
```
With:
```
8. Follow-on link exploration: when a source references related pages, follow up to {{explorationDepth}} levels deep. Reserve at least 6 WebFetch calls for primary research queries; use remaining budget for follow-on links only.
```

- [ ] **Step 2: Add Phase 3.5 comprehensive follow-up (H-5)**

After the Phase 3 synthesis section (after line ~120, after the `Save to BASE_DIR/[TOPIC_SLUG]_Synthesis_Report.md` line), insert the following new section before Phase 4:

```markdown
### Phase 3.5: Comprehensive Follow-Up (Comprehensive tier only)

Skip this phase for Quick, Standard, and Deep tiers.

After Phase 3 synthesis completes, review the synthesis report's "Gaps & Unresolved Questions" section.

1. **Assess gap severity**: For each gap, determine if it is material to answering the user's research question. Skip cosmetic gaps, nice-to-have expansions, or topics explicitly out of scope.
2. **Select agents**: For each material gap, identify the most relevant Phase 2 agent. Re-deploy using fully qualified name (`{{engineName}}:[agentId]`). Deploy a maximum of {{comprehensiveFollowUpAgentCap}} agents.
3. **Scoped task**: Each follow-up agent receives ONLY its assigned gap as the research question — not the full outline. The agent reads the synthesis report's gap description and conducts targeted research using the same protocols, file isolation rules, and WebFetch cap as Phase 2.
4. **Merge results**: After follow-up agents complete, deploy the synthesis specialist to integrate follow-up findings into the existing synthesis report. The synthesis specialist reads follow-up agent outputs and appends a "Follow-Up Findings" section to `BASE_DIR/[TOPIC_SLUG]_Synthesis_Report.md`.

One follow-up round only — do not recursively follow up on follow-up gaps.
```

- [ ] **Step 3: Update Phase 4.5 for citation verification (H-3)**

Find the existing Phase 4.5 section (starts with `### Phase 4.5: Provenance Audit`). Replace the entire section:

**Current:**
```markdown
### Phase 4.5: Provenance Audit

**Tier behavior:** Quick: skip | {{auditTierBehavior}}

Deploy a **general-purpose** provenance audit agent. Agent FIRST ACTION: Read `${CLAUDE_SKILL_DIR}/provenance.md` and execute the provenance audit protocol.
```

**New:**
```markdown
### Phase 4.5: Provenance Audit & Citation Verification

**Tier behavior:** Quick: skip | {{auditTierBehavior}}

Deploy a **general-purpose** provenance and citation verification agent. Agent instructions:
1. **FIRST ACTION**: Read `${CLAUDE_SKILL_DIR}/provenance.md` and execute the batch provenance audit protocol.
2. Read `${CLAUDE_SKILL_DIR}/standards.md` Source Verification Protocol section.
3. Execute citation verification on `BASE_DIR/[TOPIC_SLUG]_Master_Bibliography.md`: URL liveness check on all entries, source freshness flagging per configured threshold, dead link handling per configured strategy.
4. Generate `BASE_DIR/[TOPIC_SLUG]_Citation_Verification_Report.md` per the report template in standards.md.
5. Generate `BASE_DIR/[TOPIC_SLUG]_Provenance_Log.md` per the provenance log template.
```

- [ ] **Step 4: Remove trailing execution text (H-6)**

Find and delete the line:
```
Now executing research deployment...
```

- [ ] **Step 5: Add `{{comprehensiveFollowUpAgentCap}}` to Placeholder Reference**

In the Placeholder Reference section at the end of the file (around line 198), add:

```
`{{comprehensiveFollowUpAgentCap}}`
```

- [ ] **Step 6: Verify no "Now executing research deployment" remains**

Grep the file for "Now executing research deployment" — should find 0 matches.

- [ ] **Step 7: Verify "Recursive web exploration" is gone**

Grep the file for "Recursive web exploration" — should find 0 matches.

- [ ] **Step 8: Commit**

```bash
git add plugin/skills/engine-creator/templates/orchestrator-skill.md.tmpl
git commit -m "fix(C-3,H-3,H-5,H-6): exploration depth, Phase 3.5 follow-up, Phase 4.5 citation verification, remove trailing text"
```

---

### Task 6: Template — Fix `agent-template.md.tmpl` (C-1, C-2, H-1, H-4, M-4)

**Files:**
- Modify: `plugin/skills/engine-creator/templates/agent-template.md.tmpl`

This is the most significant change. The template currently has hardcoded research agent content. Replace role-specific sections with pre-computed placeholders.

- [ ] **Step 1: Replace YAML examples with `{{agentExamplesBlock}}`**

Replace lines 5-16 (the three `<example>` blocks inside the YAML description) with the single placeholder:

```
  {{agentExamplesBlock}}
```

Keep the surrounding YAML structure intact. The description field should now read:

```yaml
description: >-
  {{agentRole}} for {{engineDisplayName}}. Specializes in {{agentSpecialization}}.
  {{agentExamplesBlock}}
```

- [ ] **Step 2: Remove Domain Context section (M-4)**

Delete the entire `## Domain Context` section (lines 32-34 in current template):

```markdown
## Domain Context

This engine serves {{domain}} research. Apply domain-specific knowledge, terminology, and analytical frameworks appropriate to this field. All research outputs should be relevant and actionable for the target audience.
```

- [ ] **Step 3: Replace Search Protocol through Context Discipline with `{{agentBodyBlock}}`**

Replace everything from `## Search Protocol` (currently line ~44) through the end of `## Context Discipline` (currently line ~87) with:

```markdown
{{agentBodyBlock}}
```

This replaces: Search Protocol, Confidence Scoring, Output Format, and Context Discipline sections.

- [ ] **Step 4: Replace First Actions with `{{agentFirstActionsBlock}}`**

Replace the entire `## First Actions` section (currently lines ~88-93) with:

```markdown
{{agentFirstActionsBlock}}
```

- [ ] **Step 5: Verify the final template structure**

The template should now have this structure (approximately 25-30 lines):

```
---
name: {{agentId}}
description: >-
  {{agentRole}} for {{engineDisplayName}}. Specializes in {{agentSpecialization}}.
  {{agentExamplesBlock}}
model: {{model}}
color: {{color}}
tools: {{tools}}
---

# {{agentRole}} — {{engineDisplayName}}

You are a specialized research agent operating within the {{engineDisplayName}} pipeline. Your role is **{{agentRole}}** with deep expertise in {{domain}}.

## Core Responsibilities

{{agentSpecialization}}

{{promptOverride}}

## Source Strategy

### Source Credibility Hierarchy

{{sourceHierarchy}}

Apply the credibility hierarchy when evaluating and citing sources. No HIGH confidence claim can rest solely on Tier 4-5 sources.

{{agentBodyBlock}}

{{agentFirstActionsBlock}}
```

Verify the template has no leftover Search Protocol, Confidence Scoring, Output Format, Context Discipline, Domain Context, or First Actions sections.

- [ ] **Step 6: Commit**

```bash
git add plugin/skills/engine-creator/templates/agent-template.md.tmpl
git commit -m "fix(C-1,C-2,H-1,H-4,M-4): replace hardcoded agent body with pre-computed placeholders for VVC/research differentiation"
```

---

### Task 7: Generation Logic — Update `SKILL.md` placeholder derivation and Step 7

**Files:**
- Modify: `plugin/skills/engine-creator/SKILL.md:171,244,261-262,292`

This task depends on all template changes being complete (Tasks 1-6). It updates the generation logic to produce the correct placeholder values.

- [ ] **Step 1: Add new placeholders to the Placeholder Derivation Rules table**

Find the Placeholder Derivation Rules table in SKILL.md (starts around line 276). Add these rows:

```
| `{{isVvcAgent}}` | `true` when the agent being generated has `id === "vvc-specialist"`; `false` for all other agents. Applied per-agent in Step 7 loop. Not emitted into templates directly — used to select which pre-computed block to emit for `{{agentExamplesBlock}}`, `{{agentBodyBlock}}`, and `{{agentFirstActionsBlock}}`. |
| `{{agentExamplesBlock}}` | Pre-computed in Step 7 per agent. When `isVvcAgent`: three VVC-specific examples showing claim verification and correction deployment. Otherwise: existing three research examples with `{{agentId}}`, `{{agentRole}}`, `{{domain}}` substituted. |
| `{{agentBodyBlock}}` | Pre-computed in Step 7 per agent. When `isVvcAgent`: VVC verification protocol summary pointing to `vvc-pipeline.md`, WebFetch budget of `{{vvcWebFetchCap}}`, verification output format, verification context discipline. Otherwise: existing Search Protocol + Confidence Scoring + Output Format + Context Discipline with all current placeholders substituted. |
| `{{agentFirstActionsBlock}}` | Pre-computed in Step 7 per agent. When `isVvcAgent`: First Actions reading vvc-pipeline.md, standards.md, and draft report. Otherwise: existing First Actions reading standards.md, research-protocol.md, and research outline. |
| `{{vvcWebFetchCap}}` | `min(advanced.maxWebFetchesPerAgent * 3, 50)`. Default: 30 (when base cap is 10). Used only in VVC agent body block. |
| `{{vvcArgumentHint}}` | If `qualityFramework.vvc.enabled` is true: `" [--no-vvc]"`; otherwise: empty string. |
| `{{comprehensiveFollowUpAgentCap}}` | From `advanced.comprehensiveFollowUpAgentCap` (default: 2). Maximum agents to deploy in Phase 3.5 gap follow-up. |
| `{{provenanceBudget}}` | From `advanced.tokenBudgets.provenance` (default: 5000). |
| `{{tierConfigTable}}` | Update derivation: the Comprehensive row's "Research Agents" column must append "+ gap follow-up" after the agent count (e.g., "3 + gap follow-up"). |
| `{{vvcClaimTaxonomySummary}}` | When VVC enabled: "### Claim Taxonomy (VVC)\n\nWhen VVC is active, tag every factual claim in reports. See `${CLAUDE_SKILL_DIR}/vvc-pipeline.md` for the full claim taxonomy, verification scope, and verification process.\n\nClaim types: `[VC]` Verifiable Claim (requires verification), `[PO]` Professional Opinion (no verification), `[IE]` Inferred/Extrapolated (no verification)." When VVC disabled: empty string. Distinct from `{{vvcClaimTaxonomyBlock}}` which is the full canonical table used in vvc-pipeline.md.tmpl. |
```

- [ ] **Step 2: Update `{{tierConfigTable}}` derivation rule for Comprehensive follow-up**

In the Placeholder Derivation Rules table, find the `{{tierConfigTable}}` row (around line 283). Amend the derivation rule so the Comprehensive tier row includes "+ gap follow-up" in the Research Agents column. The current rule says:

```
Build markdown table rows from `tiers` config, one row per tier, columns: Tier, Planning, Research Agents (fully qualified), Synthesis, Report, Provenance, User Gate
```

Add to the end of this rule:

```
For the Comprehensive tier row, append " + gap follow-up" after the agent count in the Research Agents column.
```

- [ ] **Step 3: Update `{{explorationDepth}}` default**

In the Placeholder Derivation Rules table, find the `{{explorationDepth}}` row (around line 292). Change:

```
| `{{explorationDepth}}` | From `advanced.explorationDepth` (default: 5) |
```
To:
```
| `{{explorationDepth}}` | From `advanced.explorationDepth` (default: 2) |
```

- [ ] **Step 4: Update Step 7 agent generation logic**

Find Step 7 (around line 244). The current text reads:

```
**Step 7 -- Agent files.** For EACH agent: read `agent-template.md.tmpl`, replace with agent-specific values. Cycle `{{color}}` through blue, magenta, yellow. Insert `{{promptOverride}}` from prompts.agentOverrides[agentId] as "## Custom Instructions" if present. Format `{{sourceHierarchy}}` and `{{searchTemplates}}` as text blocks. Write to `{OUTPUT_DIR}/agents/{agentId}.md`.
```

Replace with:

```
**Step 7 -- Agent files.** For EACH agent in `agentPipeline.agents`: determine `isVvcAgent` = (`agent.id === "vvc-specialist"`). Pre-compute `{{agentExamplesBlock}}`, `{{agentBodyBlock}}`, and `{{agentFirstActionsBlock}}` based on `isVvcAgent` (see Placeholder Derivation Rules for expansion logic). If `isVvcAgent`, also compute `{{vvcWebFetchCap}}` = `min(advanced.maxWebFetchesPerAgent * 3, 50)`. Read `agent-template.md.tmpl`, replace with agent-specific values including pre-computed blocks. Cycle `{{color}}` through blue, magenta, yellow. Insert `{{promptOverride}}` from prompts.agentOverrides[agentId] as "## Custom Instructions" if present. Format `{{sourceHierarchy}}` and `{{searchTemplates}}` as text blocks (skip `{{searchTemplates}}` for VVC agent). Write to `{OUTPUT_DIR}/agents/{agentId}.md`.
```

- [ ] **Step 5: Update Step 8b standards.md generation**

Find Step 8b (around line 261). After the existing description, add:

```
Replace `{{vvcClaimTaxonomySummary}}` with the VVC claim taxonomy summary (brief cross-reference to vvc-pipeline.md) when VVC is enabled, or empty string when VVC is disabled. This is distinct from `{{vvcClaimTaxonomyBlock}}` used in Step 8e for the full canonical table in vvc-pipeline.md.
```

- [ ] **Step 6: Update Section 8 wizard defaults**

Find the advanced settings prompt (around line 171). Replace:

```
max iterations (1-5, default 3), exploration depth (1-10, default 5), max WebFetch calls per agent (1-50, default 10), token budgets (planning: 2000, research: 15000, synthesis: 8000, reporting: 10000, vvc: 8000), custom hooks, MCP server integrations.
```

With:

```
max iterations (1-5, default 3), exploration depth (1-10, default 2), max WebFetch calls per agent (1-50, default 10), max follow-up agents for Comprehensive tier (1-5, default 2), token budgets (planning: 2000, research: 15000, synthesis: 8000, reporting: 10000, vvc: 8000, provenance: 5000), custom hooks, MCP server integrations.
```

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/engine-creator/SKILL.md
git commit -m "fix: update generation logic with VVC-aware Step 7, new placeholder derivation rules, updated defaults"
```

---

### Task 8: Validation — Verify all template changes against generated output

**Files:**
- Read: All modified templates
- Read: `generated-engines/not-for-profit/` (as reference of pre-fix output)

This task validates the changes by grepping the templates and checking consistency.

- [ ] **Step 1: Verify agent template has no hardcoded research body**

Run grep on `agent-template.md.tmpl` for "Search Protocol" — should find 0 matches.
Run grep for "Confidence Scoring" — should find 0 matches.
Run grep for "Domain Context" — should find 0 matches.
Run grep for `{{agentBodyBlock}}` — should find 1 match.
Run grep for `{{agentFirstActionsBlock}}` — should find 1 match.
Run grep for `{{agentExamplesBlock}}` — should find 1 match.

- [ ] **Step 2: Verify orchestrator template changes**

Run grep on `orchestrator-skill.md.tmpl`:
- "Now executing research deployment" — 0 matches
- "Recursive web exploration" — 0 matches
- "Follow-on link exploration" — 1 match
- "Phase 3.5" — 1+ matches
- "Provenance Audit & Citation Verification" — 1 match
- `{{comprehensiveFollowUpAgentCap}}` — 1+ matches

- [ ] **Step 3: Verify command template has VVC hint**

Run grep on `command-template.md.tmpl` for `{{vvcArgumentHint}}` — should find 1 match.

- [ ] **Step 4: Verify research-protocol template changes**

Run grep on `research-protocol.md.tmpl`:
- "500 tokens" — 0 matches
- "450 tokens" — 1 match
- `{{provenanceBudget}}` — 1+ matches

- [ ] **Step 5: Verify standards template changes**

Run grep on `standards.md.tmpl`:
- `{{vvcClaimTaxonomyBlock}}` — 0 matches (replaced by summary)
- `{{vvcClaimTaxonomySummary}}` — 1 match
- "Budget note" — 1 match

- [ ] **Step 6: Verify schema changes**

Run: `python3 -c "import json; s=json.load(open('plugin/skills/engine-creator/templates/engine-config-schema.json')); a=s['properties']['advanced']['properties']; print('followup:', 'comprehensiveFollowUpAgentCap' in a); print('provenance:', 'provenance' in a['tokenBudgets']['properties']); print('depth default:', a['explorationDepth']['default'])"`

Expected output:
```
followup: True
provenance: True
depth default: 2
```

- [ ] **Step 7: Verify SKILL.md generation logic**

Run grep on `plugin/skills/engine-creator/SKILL.md`:
- `{{agentExamplesBlock}}` — 1+ matches
- `{{agentBodyBlock}}` — 1+ matches
- `{{agentFirstActionsBlock}}` — 1+ matches
- `{{vvcWebFetchCap}}` — 1+ matches
- `{{vvcArgumentHint}}` — 1+ matches
- `{{comprehensiveFollowUpAgentCap}}` — 1+ matches
- `{{provenanceBudget}}` — 1+ matches
- `{{vvcClaimTaxonomySummary}}` — 1+ matches
- `isVvcAgent` — 1+ matches
- "exploration depth (1-10, default 2)" — 1 match
- "exploration depth (1-10, default 5)" — 0 matches

- [ ] **Step 8: Commit validation results (if any fixes needed)**

If any grep checks fail, fix the relevant file and amend the appropriate commit. Then re-run the failing checks.

---

### Task 9: Integration Test — Regenerate not-for-profit engine and validate

**Files:**
- Read: All template files
- Read: `generated-engines/not-for-profit/` (compare before/after)

This task validates the full pipeline by checking that the existing not-for-profit generated output would be different with the new templates. Since the factory is prompt-driven (not programmatic), this task manually verifies that the spec's 12 testing criteria are satisfiable.

- [ ] **Step 1: Cross-reference generated not-for-profit VVC agent against new template**

Read `generated-engines/not-for-profit/agents/vvc-specialist.md`. Verify it STILL has the old pattern (Search Protocol, research First Actions). This confirms the fix hasn't been retroactively applied to existing output — only future generations will be different.

- [ ] **Step 2: Verify the review findings issues map to template changes**

Read `generated-engines/not-for-profit/REVIEW-FINDINGS.md`. For each issue marked as template-level (C-1, C-2, C-3, C-4, H-1, H-2, H-3, H-4, H-5, H-6, M-1, M-2, M-3, M-4), confirm a corresponding template change exists in the modified files.

- [ ] **Step 3: Run `/test-engine` if available**

If the factory plugin is installed and functional:
```
/test-engine generated-engines/not-for-profit
```

Note: This validates the EXISTING generated engine structure (which predates the fixes). All structural checks should still pass. The template fixes affect FUTURE generations, not existing output.

- [ ] **Step 4: Commit any final adjustments**

If any fixes were needed, commit the specific modified files:
```bash
git add plugin/skills/engine-creator/templates/ plugin/skills/engine-creator/SKILL.md
git commit -m "chore: validation pass — all template fixes verified"
```
