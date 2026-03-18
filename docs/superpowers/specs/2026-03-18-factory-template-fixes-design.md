# Factory Template Fixes — Design Spec

**Date:** 2026-03-18
**Status:** Approved (Rev 2 — passed spec review)
**Origin:** Code review of `generated-engines/not-for-profit/` (see `REVIEW-FINDINGS.md`)

---

## Problem

A code and prompt engineering review of the not-for-profit generated engine identified 16 issues, 8 of which are factory template bugs that reproduce in every generated engine. The most critical: the VVC specialist agent is a carbon copy of the research agent template, causing it to receive research instructions instead of verification instructions at runtime.

## Scope

This spec covers **template-level fixes only** — changes to files under `plugin/skills/engine-creator/templates/` and the generation logic in `plugin/skills/engine-creator/SKILL.md`. Instance-specific or config-driven issues (C-4 command hint, H-2 budget accounting, H-3 citation protocol orchestration, H-4 VVC WebFetch cap, H-6 trailing text, M-1 provenance budget, M-5 variable resolution, M-6 file naming) are also addressed where they trace back to template or generation logic.

## Design Decisions

1. **VVC agent template approach:** Conditional content within the existing `agent-template.md.tmpl` using pre-computed placeholder blocks (matching existing conventions like `{{vvcClaimTaxonomyBlock}}`). No Handlebars-style `{{#if}}` syntax — the templates use simple placeholder substitution driven by the generation logic in SKILL.md. The VVC agent shares ~40% of research agent content (source hierarchy, confidence scoring, domain context), so a single template avoids drift.
2. **Comprehensive follow-up round:** Post-synthesis gap closure (Phase 3.5, after Phase 3, before Phase 4). The synthesis agent already identifies gaps, so the follow-up is a natural extension. One round only, no recursion.
3. **Exploration depth:** Change the default from 5 to 2 and add budget-reservation language. Keep `{{explorationDepth}}` as the single source of truth in both `orchestrator-skill.md.tmpl` and `research-protocol.md.tmpl`.

---

## Changes by File

### 1. `agent-template.md.tmpl`

**Issues addressed:** C-1 (VVC uses research template), C-2 (VVC First Actions wrong), H-1 (boilerplate examples), H-4 (VVC WebFetch cap insufficient), M-4 (redundant Domain Context)

#### 1a. Pre-computed YAML examples block (H-1)

Replace the three hardcoded example blocks in the YAML description with a single placeholder:

**Current** (lines 5-16):
```yaml
  <example>Context: User needs {{domain}} research requiring {{agentRole}} capabilities.
  ...three hardcoded research examples...
```

**New:**
```yaml
  {{agentExamplesBlock}}
```

**Derivation rule** (added to SKILL.md Step 7):

When `isVvcAgent` is true, `{{agentExamplesBlock}}` expands to:
```
<example>Context: Research pipeline has completed draft report and needs claim verification.
  user: 'Verify the claims in the draft report against cited sources'
  assistant: 'I will deploy the {{agentId}} agent to systematically verify [VC]-tagged claims against their cited sources.'
  <commentary>The VVC specialist is deployed post-reporting to verify factual claims in Phases 5-6.</commentary></example>
  <example>Context: Draft report needs corrections based on verification findings.
  user: 'Apply corrections to disputed and unsupported claims in the report'
  assistant: 'The {{agentId}} agent will read the verification report and apply corrections to produce the final comprehensive report.'
  <commentary>Phase 6 correction is a mechanical application of Phase 5 verification findings.</commentary></example>
  <example>Context: Multi-agent pipeline completing VVC phases.
  user: 'Run verification and correction on the draft'
  assistant: 'The {{agentId}} agent will handle Phases 5-6: first verifying [VC]-tagged claims, then correcting the draft report based on findings.'
  <commentary>The VVC specialist operates only in Phases 5-6, never during Phase 2 research.</commentary></example>
```

When `isVvcAgent` is false, `{{agentExamplesBlock}}` expands to the existing three research examples (current lines 5-16, unchanged).

#### 1b. Remove redundant Domain Context section (M-4)

Delete the `## Domain Context` block entirely (current lines 33-34):

```markdown
## Domain Context

This engine serves {{domain}} research. Apply domain-specific knowledge, terminology, and analytical frameworks appropriate to this field. All research outputs should be relevant and actionable for the target audience.
```

The `## Core Responsibilities` section already contains `{{promptOverride}}` which includes the global preamble with identical domain context. Removing this eliminates ~50 tokens of redundancy per agent.

#### 1c. Pre-computed body block: research vs. VVC (C-1, H-4)

Replace everything from `## Search Protocol` through `## Context Discipline` (current lines 44-87) with a single placeholder:

**New:**
```markdown
{{agentBodyBlock}}
```

**Derivation rule** (added to SKILL.md Step 7):

When `isVvcAgent` is true, `{{agentBodyBlock}}` expands to:
```markdown
## Verification Protocol

Your role is to verify and correct factual claims in draft reports. You do NOT conduct original research. You do NOT participate in Phase 2. Follow the detailed verification and correction protocol in `${CLAUDE_SKILL_DIR}/vvc-pipeline.md`.

### WebFetch Budget

Cap at {{vvcWebFetchCap}} total WebFetch calls across Phases 5-6. Prioritize verification of HIGH-confidence claims first, then MEDIUM, then lower tiers. If budget is exhausted before all claims are verified, note unverified claims in the verification report with status UNVERIFIED.

## Output Format

- Use verification detail tables for all findings
- Keep chat responses concise (450 tokens or fewer)
- Format: `## Verification Summary | ## Issues Found | ## Corrections Applied | ## Files Written`

## Context Discipline

- Read the draft report once; extract claims into a working table
- Process claims sequentially by confidence tier (HIGH first)
- Do not re-fetch sources already verified — note result and move on
- Use structured tables for all verification output
```

Note: The VVC body is intentionally brief. It states the role and points to `vvc-pipeline.md` for the detailed protocol rather than duplicating the Phase 5/6 instructions that already exist in `vvc-pipeline.md.tmpl`. This follows the same deduplication principle applied to the claim taxonomy (M-3).

When `isVvcAgent` is false, `{{agentBodyBlock}}` expands to the existing Search Protocol + Confidence Scoring + Output Format + Context Discipline sections (current lines 44-87, unchanged).

#### 1d. Pre-computed First Actions block (C-2)

Replace the First Actions section (current lines 88-93) with a placeholder:

**New:**
```markdown
{{agentFirstActionsBlock}}
```

**Derivation rule** (added to SKILL.md Step 7):

When `isVvcAgent` is true, `{{agentFirstActionsBlock}}` expands to:
```markdown
## First Actions

Before starting verification, read these reference files:
1. `${CLAUDE_SKILL_DIR}/vvc-pipeline.md` — verification process, correction process, claim taxonomy
2. `${CLAUDE_SKILL_DIR}/standards.md` — confidence scoring, source credibility hierarchy
3. Read the draft report from `BASE_DIR/[TOPIC_SLUG]_Draft_Report.md`
```

When `isVvcAgent` is false, `{{agentFirstActionsBlock}}` expands to the existing First Actions (current lines 88-93, unchanged).

---

### 2. `orchestrator-skill.md.tmpl`

**Issues addressed:** C-3 (recursive exploration vs WebFetch cap), H-3 (citation verification unorchestrated), H-5 (comprehensive follow-up undefined), H-6 (trailing execution text)

#### 2a. Fix recursive exploration instruction (C-3)

Replace line 105:
```
8. Recursive web exploration up to {{explorationDepth}} levels deep from seed URLs
```

With:
```
8. Follow-on link exploration: when a source references related pages, follow up to {{explorationDepth}} levels deep. Reserve at least 6 WebFetch calls for primary research queries; use remaining budget for follow-on links only.
```

Keep the `{{explorationDepth}}` placeholder but change the **default value** from 5 to 2 (see section 6 for SKILL.md derivation rule update and section 7 for schema update). This keeps `{{explorationDepth}}` as the single source of truth across both `orchestrator-skill.md.tmpl` and `research-protocol.md.tmpl`.

#### 2b. Add Phase 3.5 comprehensive follow-up (H-5)

Insert between Phase 3 (synthesis) and Phase 4 (reporting):

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

Update the tier config table row for Comprehensive:
```
| Comprehensive | Yes | {{comprehensiveAgentCount}} + gap follow-up | Yes | Full | Hash + Audit | Always |
```

Add `{{comprehensiveFollowUpAgentCap}}` to the Placeholder Reference section at the end of the template.

#### 2c. Remove trailing execution text (H-6)

Delete line 141:
```
Now executing research deployment...
```

The `/research` command template already has `Starting {{engineDisplayName}} research system...` at the correct invocation point.

#### 2d. Update Phase 4.5 for citation verification (H-3)

Replace the existing Phase 4.5 block:

```markdown
### Phase 4.5: Provenance Audit

**Tier behavior:** Quick: skip | {{auditTierBehavior}}

Deploy a **general-purpose** provenance audit agent. Agent FIRST ACTION: Read `${CLAUDE_SKILL_DIR}/provenance.md` and execute the provenance audit protocol.
```

With:

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

This gives the Citation Verification Protocol in `standards.md` an explicit phase owner without adding a new phase. The protocol definition stays in `standards.md.tmpl` (unchanged); the orchestration happens here.

---

### 3. `command-template.md.tmpl`

**Issues addressed:** C-4 (`--no-vvc` missing from argument-hint)

#### 3a. Add conditional `--no-vvc` to argument-hint

Replace line 3:
```
argument-hint: "[research topic] [--quick|--standard|--deep|--comprehensive] [--approve] [--no-approve] [--outline-only] [--extend] [--reverifiable]"
```

With:
```
argument-hint: "[research topic] [--quick|--standard|--deep|--comprehensive] [--approve] [--no-approve] [--outline-only] [--extend] [--reverifiable]{{vvcArgumentHint}}"
```

---

### 4. `research-protocol.md.tmpl`

**Issues addressed:** M-1 (provenance budget missing from config), M-2 (500 vs 450 tokens)

#### 4a. Align chat response limit (M-2)

Replace line 8:
```
- Each agent chat response of 500 tokens or fewer; avoid meta narration
```

With:
```
- Each agent chat response of 450 tokens or fewer; avoid meta narration
```

#### 4b. Parameterize provenance budget (M-1)

Replace line 124:
```
Provenance Audit: 5K tokens output max
```

With:
```
Provenance Audit: {{provenanceBudget}} tokens output max
```

---

### 5. `standards.md.tmpl`

**Issues addressed:** H-2 (probe-on-discovery budget), M-3 (claim taxonomy duplication)

#### 5a. Probe-on-discovery budget note (H-2)

After the existing probe-on-discovery bullets (line 110), add:

```markdown
- **Budget note:** Probe fetches count toward the per-agent WebFetch cap. When probe-on-discovery is enabled, reserve at least 4 WebFetch calls for content retrieval by limiting probes to the top 6 candidate URLs per session. Skip probing Tier 1 government domains (assumed accessible).
```

#### 5b. Deduplicate claim taxonomy (M-3)

Replace line 22 (`{{vvcClaimTaxonomyBlock}}`) with a new placeholder:

```markdown
{{vvcClaimTaxonomySummary}}
```

**Derivation rule** (added to SKILL.md Step 8b):

When VVC is enabled, `{{vvcClaimTaxonomySummary}}` expands to:
```markdown
### Claim Taxonomy (VVC)

When VVC is active, tag every factual claim in reports. See `${CLAUDE_SKILL_DIR}/vvc-pipeline.md` for the full claim taxonomy, verification scope, and verification process.

Claim types: `[VC]` Verifiable Claim (requires verification), `[PO]` Professional Opinion (no verification), `[IE]` Inferred/Extrapolated (no verification).
```

When VVC is disabled, `{{vvcClaimTaxonomySummary}}` is empty string.

The canonical full taxonomy (with verification scope table) remains in `vvc-pipeline.md.tmpl` via the existing `{{vvcClaimTaxonomyBlock}}` placeholder (unchanged). Standards.md gets a brief summary with a pointer — enough for Phase 2 research agents to know the tags without duplicating the verification scope table.

---

### 6. `SKILL.md` (Generation Logic)

**Issues addressed:** New placeholder support, schema updates, wizard updates, default value changes

#### 6a. New placeholders — add to Placeholder Derivation Rules table

| Placeholder | Derivation Rule |
|---|---|
| `{{isVvcAgent}}` | `true` when the agent being generated has `id === "vvc-specialist"`; `false` for all other agents. Applied per-agent in Step 7 loop. Not emitted into templates directly — used to select which pre-computed block to emit for `{{agentExamplesBlock}}`, `{{agentBodyBlock}}`, and `{{agentFirstActionsBlock}}`. |
| `{{agentExamplesBlock}}` | Pre-computed in Step 7 per agent. When `isVvcAgent`: VVC-specific examples (see section 1a). Otherwise: existing research examples with `{{agentId}}`, `{{agentRole}}`, `{{domain}}` substituted. |
| `{{agentBodyBlock}}` | Pre-computed in Step 7 per agent. When `isVvcAgent`: VVC verification protocol summary with `{{vvcWebFetchCap}}` (see section 1c). Otherwise: existing Search Protocol + Confidence Scoring + Output Format + Context Discipline with all current placeholders substituted. |
| `{{agentFirstActionsBlock}}` | Pre-computed in Step 7 per agent. When `isVvcAgent`: VVC First Actions reading vvc-pipeline.md, standards.md, draft report (see section 1d). Otherwise: existing research First Actions reading standards.md, research-protocol.md, research outline. |
| `{{vvcWebFetchCap}}` | `min(advanced.maxWebFetchesPerAgent * 3, 50)`. Default: 30 (when base cap is 10). Used only in VVC agent body block. |
| `{{vvcArgumentHint}}` | If `qualityFramework.vvc.enabled` is true: `" [--no-vvc]"`; otherwise: empty string. |
| `{{comprehensiveFollowUpAgentCap}}` | From `advanced.comprehensiveFollowUpAgentCap` (default: 2). Maximum agents to deploy in Phase 3.5 gap follow-up. |
| `{{provenanceBudget}}` | From `advanced.tokenBudgets.provenance` (default: 5000). |
| `{{vvcClaimTaxonomySummary}}` | When VVC enabled: brief claim taxonomy summary with cross-reference to vvc-pipeline.md (see section 5b). When VVC disabled: empty string. Distinct from existing `{{vvcClaimTaxonomyBlock}}` which remains the full canonical table used in vvc-pipeline.md.tmpl. |

#### 6b. Updated default value

Change the default for `{{explorationDepth}}` from 5 to 2:

**Current** (SKILL.md line 292):
```
| `{{explorationDepth}}` | From `advanced.explorationDepth` (default: 5) |
```

**New:**
```
| `{{explorationDepth}}` | From `advanced.explorationDepth` (default: 2) |
```

This aligns the default with the WebFetch budget constraint. Users can still configure higher values via the Section 8 wizard, but the default is safe.

#### 6c. Step 7 agent generation update

Current Step 7 description (SKILL.md line 244):

> For EACH agent: read `agent-template.md.tmpl`, replace with agent-specific values. Cycle `{{color}}` through blue, magenta, yellow. Insert `{{promptOverride}}` from prompts.agentOverrides[agentId] as "## Custom Instructions" if present. Format `{{sourceHierarchy}}` and `{{searchTemplates}}` as text blocks. Write to `{OUTPUT_DIR}/agents/{agentId}.md`.

Amend to:

> For EACH agent: determine `isVvcAgent` = (`agent.id === "vvc-specialist"`). Pre-compute `{{agentExamplesBlock}}`, `{{agentBodyBlock}}`, and `{{agentFirstActionsBlock}}` based on `isVvcAgent` (see Placeholder Derivation Rules for expansion logic). If `isVvcAgent`, also compute `{{vvcWebFetchCap}}` = `min(advanced.maxWebFetchesPerAgent * 3, 50)`. Read `agent-template.md.tmpl`, replace with agent-specific values including pre-computed blocks. Cycle `{{color}}` through blue, magenta, yellow. Insert `{{promptOverride}}` from prompts.agentOverrides[agentId] as "## Custom Instructions" if present. Format `{{sourceHierarchy}}` and `{{searchTemplates}}` as text blocks (skip `{{searchTemplates}}` for VVC agent). Write to `{OUTPUT_DIR}/agents/{agentId}.md`.

#### 6d. Step 8b standards.md update

Add to Step 8b description:

> Replace `{{vvcClaimTaxonomySummary}}` with the VVC claim taxonomy summary (brief cross-reference) when VVC is enabled, or empty string when disabled. This is distinct from `{{vvcClaimTaxonomyBlock}}` used in Step 8e.

#### 6e. Section 8 wizard update

In the advanced settings prompt (SKILL.md line 171):

**Current:**
```
max iterations (1-5, default 3), exploration depth (1-10, default 5), max WebFetch calls per agent (1-50, default 10), token budgets (planning: 2000, research: 15000, synthesis: 8000, reporting: 10000, vvc: 8000), custom hooks, MCP server integrations.
```

**New:**
```
max iterations (1-5, default 3), exploration depth (1-10, default 2), max WebFetch calls per agent (1-50, default 10), max follow-up agents for Comprehensive tier (1-5, default 2), token budgets (planning: 2000, research: 15000, synthesis: 8000, reporting: 10000, vvc: 8000, provenance: 5000), custom hooks, MCP server integrations.
```

---

### 7. `engine-config-schema.json`

**Issues addressed:** M-1 (provenance budget), H-5 (follow-up cap), C-3 (exploration depth default)

#### 7a. Add new schema properties

Add under `advanced` properties:

```json
"comprehensiveFollowUpAgentCap": {
  "type": "integer",
  "minimum": 1,
  "maximum": 5,
  "default": 2,
  "description": "Maximum agents to deploy in Phase 3.5 comprehensive follow-up round"
}
```

Add under `advanced.tokenBudgets` properties:

```json
"provenance": {
  "type": "integer",
  "default": 5000,
  "description": "Token budget for provenance audit and citation verification phase"
}
```

#### 7b. Update exploration depth default

Change `advanced.explorationDepth` default from 5 to 2:

```json
"explorationDepth": {
  "type": "integer",
  "minimum": 1,
  "maximum": 10,
  "default": 2,
  "description": "Maximum depth for follow-on link exploration from source pages"
}
```

---

## Files Modified (Summary)

| File | Changes | Issues Fixed |
|---|---|---|
| `templates/agent-template.md.tmpl` | Replace examples, body, First Actions with pre-computed placeholders (`{{agentExamplesBlock}}`, `{{agentBodyBlock}}`, `{{agentFirstActionsBlock}}`); remove Domain Context section | C-1, C-2, H-1, H-4, M-4 |
| `templates/orchestrator-skill.md.tmpl` | Fix exploration depth instruction with budget reservation; add Phase 3.5 follow-up; remove trailing text; update Phase 4.5 with citation verification | C-3, H-3, H-5, H-6 |
| `templates/command-template.md.tmpl` | Add `{{vvcArgumentHint}}` to argument-hint | C-4 |
| `templates/research-protocol.md.tmpl` | Align 450 token limit; parameterize provenance budget | M-1, M-2 |
| `templates/standards.md.tmpl` | Add probe budget note; replace `{{vvcClaimTaxonomyBlock}}` with `{{vvcClaimTaxonomySummary}}` cross-reference | H-2, M-3 |
| `templates/engine-config-schema.json` | Add `comprehensiveFollowUpAgentCap`, `tokenBudgets.provenance`; change `explorationDepth` default to 2 | M-1, H-5, C-3 |
| `SKILL.md` (generation logic) | Add 9 new placeholder derivation rules; update Step 7 loop for VVC-aware generation; update Step 8b for taxonomy summary; update Section 8 wizard defaults; change exploration depth default | All |

## Files NOT Modified

| File | Reason |
|---|---|
| `templates/vvc-pipeline.md.tmpl` | Already correct — canonical claim taxonomy stays here via `{{vvcClaimTaxonomyBlock}}` |
| `templates/provenance.md.tmpl` | No issues found |
| `templates/extension-skill.md.tmpl` | Out of scope (extension mode) |
| `templates/plugin-json.tmpl` | No issues found |
| `templates/readme-template.md.tmpl` | No issues found |
| `templates/sources-command-template.md.tmpl` | No issues found |

## Out of Scope

| Issue | Reason |
|---|---|
| M-5 (`${CLAUDE_SKILL_DIR}` resolution in agent context) | Requires runtime verification in Claude Code's plugin system, not a template change. Should be tested empirically and filed as a separate issue if it fails. |
| M-6 (file naming mismatch in config vs SKILL.md) | Config's `fileNaming` field is informational/metadata only. Low impact; can be addressed in a future config cleanup pass. |

## Testing

After implementation, validate by:

1. Run `/test-engine` against a freshly generated engine with VVC enabled — verify VVC specialist agent file contains verification protocol pointer to `vvc-pipeline.md` (not search protocol) and reads `vvc-pipeline.md` in First Actions
2. Run `/test-engine` against a freshly generated engine with VVC disabled — verify no VVC-specific content appears in agent files or standards.md claim taxonomy section
3. Grep generated SKILL.md for "Now executing research deployment" — should not appear
4. Grep generated SKILL.md for "Recursive web exploration up to" — should not appear; instead find "Follow-on link exploration" with budget reservation language
5. Verify generated `research.md` command argument-hint contains `--no-vvc` when VVC enabled, and does not contain it when VVC disabled
6. Verify generated `standards.md` contains claim taxonomy cross-reference pointing to `vvc-pipeline.md` (not a full taxonomy table) when VVC enabled
7. Verify generated `research-protocol.md` says "450 tokens" (not 500) and contains `provenance` token budget line
8. Verify `engine-config.json` schema validates with new `comprehensiveFollowUpAgentCap` and `tokenBudgets.provenance` fields
9. Verify Phase 3.5 block appears in generated SKILL.md AND contains "Skip this phase for Quick, Standard, and Deep tiers"
10. Verify Phase 4.5 heading is "Provenance Audit & Citation Verification" and references both `provenance.md` and `standards.md`
11. Verify generated `engine-config.json` has `explorationDepth` default of 2 (not 5)
12. Verify VVC specialist agent has `{{vvcWebFetchCap}}` value (default: 30) in its WebFetch Budget section, distinct from research agents' cap (default: 10)
