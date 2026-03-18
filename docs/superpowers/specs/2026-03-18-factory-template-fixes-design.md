# Factory Template Fixes — Design Spec

**Date:** 2026-03-18
**Status:** Draft
**Origin:** Code review of `generated-engines/not-for-profit/` (see `REVIEW-FINDINGS.md`)

---

## Problem

A code and prompt engineering review of the not-for-profit generated engine identified 16 issues, 8 of which are factory template bugs that reproduce in every generated engine. The most critical: the VVC specialist agent is a carbon copy of the research agent template, causing it to receive research instructions instead of verification instructions at runtime.

## Scope

This spec covers **template-level fixes only** — changes to files under `plugin/skills/engine-creator/templates/` and the generation logic in `plugin/skills/engine-creator/SKILL.md`. Instance-specific or config-driven issues (C-4 command hint, H-2 budget accounting, H-3 citation protocol orchestration, H-4 VVC WebFetch cap, H-6 trailing text, M-1 provenance budget, M-5 variable resolution, M-6 file naming) are also addressed where they trace back to template or generation logic.

## Design Decisions

1. **VVC agent template approach:** Conditional branches within the existing `agent-template.md.tmpl` (not a separate template file). The VVC agent shares ~40% of research agent content (source hierarchy, confidence scoring, domain context), so a single template avoids drift.
2. **Comprehensive follow-up round:** Post-synthesis gap closure (Phase 3.5, after Phase 3, before Phase 4). The synthesis agent already identifies gaps, so the follow-up is a natural extension. One round only, no recursion.

---

## Changes by File

### 1. `agent-template.md.tmpl`

**Issues addressed:** C-1 (VVC uses research template), C-2 (VVC First Actions wrong), H-1 (boilerplate examples), M-2 (450 vs 500 — agent side already correct), M-4 (redundant Domain Context)

#### 1a. Conditional YAML examples (H-1)

Replace the three hardcoded research examples with a conditional:

```
{{#if isVvcAgent}}
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
{{else}}
  <example>Context: User needs {{domain}} research requiring {{agentRole}} capabilities.
  user: 'Research the latest developments in {{domain}}'
  assistant: 'I will deploy the {{agentId}} agent to conduct specialized research in this area.'
  <commentary>The user needs domain-specific research that matches this agent's specialization in {{domain}}.</commentary></example>
  <example>Context: A research pipeline needs a {{agentRole}} to gather and analyze information.
  user: 'I need detailed analysis of trends and data in {{domain}}'
  assistant: 'Let me engage the {{agentId}} agent for in-depth {{domain}} analysis using authoritative sources.'
  <commentary>The request requires specialized analytical capabilities that align with this agent's role.</commentary></example>
  <example>Context: Multi-agent research requiring coordinated specialist contributions.
  user: 'Run a comprehensive investigation covering multiple angles of this topic'
  assistant: 'The {{agentId}} agent will handle the {{agentRole}} component of this multi-agent research effort.'
  <commentary>The comprehensive research request benefits from this agent's focused specialization within the pipeline.</commentary></example>
{{/if}}
```

#### 1b. Remove redundant Domain Context section (M-4)

Delete lines 33-34 entirely:

```markdown
## Domain Context

This engine serves {{domain}} research. Apply domain-specific knowledge, terminology, and analytical frameworks appropriate to this field. All research outputs should be relevant and actionable for the target audience.
```

The `## Core Responsibilities` section already contains `{{promptOverride}}` which includes the global preamble with identical domain context. Removing this eliminates ~50 tokens of redundancy per agent.

#### 1c. Conditional body: research vs. VVC (C-1)

After the Source Credibility Hierarchy section (which remains shared), replace the Search Protocol, Confidence Scoring, Output Format, and Context Discipline sections with a conditional:

```markdown
{{#if isVvcAgent}}
## Verification Protocol

Your role is to verify and correct factual claims in draft reports. You do NOT conduct original research. You do NOT participate in Phase 2.

### Phase 5: Verification
1. Read the draft report and extract all `[VC]`-tagged claims with their cited sources
2. For each claim per verification scope percentages:
   a. Fetch the cited source via WebFetch
   b. Verify the claim accurately reflects the source content
   c. Score as: CONFIRMED | PARAPHRASED | DISPUTED | UNSUPPORTED | UNREACHABLE
   d. Record confidence level and source credibility tier
3. Flag claims where source does not support the claim, source is unreachable, confidence appears inflated, or source credibility tier is too low
4. Save verification report to `BASE_DIR/[TOPIC_SLUG]_VVC_Verification_Report.md`

### Phase 6: Correction
1. Read the verification report per-claim table
2. Apply corrections mechanically from the verification findings:
   - DISPUTED claims: correct to match source, or remove if irreconcilable
   - UNSUPPORTED claims: add caveat language, downgrade confidence, or remove
   - UNREACHABLE sources: note as unverifiable, attempt archive fallback, downgrade confidence
   - Inflated confidence: downgrade to appropriate level
3. Preserve all `[VC]`/`[PO]`/`[IE]` tags in the final report
4. Save final report to `BASE_DIR/[TOPIC_SLUG]_Comprehensive_Report.md`
5. Save correction log to `BASE_DIR/[TOPIC_SLUG]_VVC_Correction_Log.md`

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

{{else}}
## Search Protocol

When conducting research:

1. **Generate diversified queries** -- minimum 4 query types per research question:
   - Direct query with primary keywords
   - Synonym/alternative terminology variant
   - Adversarial query (problems, criticism, failures, controversy)
   - Expert-source targeted query (authoritative domains)

2. **Apply search templates** where applicable:

{{searchTemplates}}

3. **Iterative Search-Assess-Refine**:
   - Pass 1 (SEARCH): Execute diversified query set
   - Pass 2 (ASSESS): Evaluate evidence sufficiency -- 2+ independent sources for key claims? Contradictions? Gaps?
   - Pass 3 (REFINE): If gaps found, generate targeted follow-up queries
   - Max {{maxIterations}} iterations per research question
   - Abort when no new credible sources after 2 alternate query branches

4. **WebFetch cap**: Hard cap of {{maxWebFetches}} total WebFetch calls per research session. Prioritize highest-credibility, most-accessible sources. If a URL returns 403/blocked/paywall, note in methodology log and move on — do not retry.

## Confidence Scoring

Tag every claim with a confidence level:

{{confidenceScoring}}

## Output Format

- Use claims/evidence/confidence tables for all findings
- Log all search queries, engines, filters, and assessments to your per-agent Methodology_Log_[AgentID].md
- Save discovered sources to your per-agent Sources_[AgentID].md
- Save citations using the configured citation standard: {{citationStandard}}
- Keep chat responses concise (450 tokens or fewer)
- Format: `## Focus | ## Top Findings (with IDs + confidence) | ## Gaps/Next | ## Files Written`

## Context Discipline

- Summarize sources immediately; per-source abstracts of 120 words or fewer
- Operate in passes: (1) initial sweep + notes, (2) synthesis of top claims/gaps, (3) targeted follow-up
- Use structured outputs (tables, bullet summaries, query logs) to minimize token footprint
{{/if}}
```

#### 1d. Conditional First Actions (C-2)

Replace the First Actions section:

```markdown
{{#if isVvcAgent}}
## First Actions

Before starting verification, read these reference files:
1. `${CLAUDE_SKILL_DIR}/vvc-pipeline.md` — verification process, correction process, claim taxonomy
2. `${CLAUDE_SKILL_DIR}/standards.md` — confidence scoring, source credibility hierarchy
3. Read the draft report from `BASE_DIR/[TOPIC_SLUG]_Draft_Report.md`
{{else}}
## First Actions

Before starting research, read these reference files:
1. `${CLAUDE_SKILL_DIR}/standards.md` — quality standards, confidence scoring, source credibility
2. `${CLAUDE_SKILL_DIR}/research-protocol.md` — search protocol, file isolation rules, WebFetch cap
3. Read the research outline from `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md`
{{/if}}
```

---

### 2. `orchestrator-skill.md.tmpl`

**Issues addressed:** C-3 (recursive exploration vs WebFetch cap), H-5 (comprehensive follow-up undefined), H-6 (trailing execution text)

#### 2a. Fix recursive exploration instruction (C-3)

Replace line 105:
```
8. Recursive web exploration up to {{explorationDepth}} levels deep from seed URLs
```

With:
```
8. Follow-on link exploration: when a source references related pages, follow up to 2 levels deep. Reserve at least 6 WebFetch calls for primary research queries; use remaining budget for follow-on links only.
```

The `{{explorationDepth}}` placeholder is removed from this context. The `advanced.explorationDepth` config field remains in the schema for potential future use but is no longer injected into Common Agent Requirements.

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

Update the tier config table row for Comprehensive to reflect the mechanic:
```
| Comprehensive | Yes | {{comprehensiveAgentCount}} + gap follow-up | Yes | Full | Hash + Audit | Always |
```

#### 2c. Remove trailing execution text (H-6)

Delete line 141:
```
Now executing research deployment...
```

The `/research` command template already has `Starting {{engineDisplayName}} research system...` at the correct invocation point.

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

**Issues addressed:** H-2 (probe-on-discovery budget), H-3 (citation verification unorchestrated), M-3 (claim taxonomy duplication)

#### 5a. Probe-on-discovery budget note (H-2)

After the existing probe-on-discovery bullets (line 110), add:

```markdown
- **Budget note:** Probe fetches count toward the per-agent WebFetch cap. When probe-on-discovery is enabled, reserve at least 4 WebFetch calls for content retrieval by limiting probes to the top 6 candidate URLs per session. Skip probing Tier 1 government domains (assumed accessible).
```

#### 5b. Deduplicate claim taxonomy (M-3)

Replace line 22 (`{{vvcClaimTaxonomyBlock}}`) with a conditional summary:

```markdown
{{#if vvcEnabled}}
### Claim Taxonomy (VVC)

When VVC is active, tag every factual claim in reports. See `${CLAUDE_SKILL_DIR}/vvc-pipeline.md` for the full claim taxonomy, verification scope, and verification process.

Claim types: `[VC]` Verifiable Claim (requires verification), `[PO]` Professional Opinion (no verification), `[IE]` Inferred/Extrapolated (no verification).
{{/if}}
```

The canonical full taxonomy remains in `vvc-pipeline.md.tmpl` (unchanged). Standards.md gets a brief summary with a pointer — enough for Phase 2 research agents to know the tags without duplicating the verification scope table.

#### 5c. Integrate citation verification into Phase 4.5 (H-3)

No changes to `standards.md.tmpl` itself — the Source Verification Protocol section stays as-is (it defines the protocol). The fix is in `orchestrator-skill.md.tmpl` Phase 4.5 (see section 2 above), which now explicitly tells the provenance audit agent to also execute the citation verification protocol from standards.md.

Update Phase 4.5 in `orchestrator-skill.md.tmpl`:

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

---

### 6. `SKILL.md` (Generation Logic)

**Issues addressed:** New placeholder support, schema updates, wizard updates

#### 6a. New placeholders — add to Placeholder Derivation Rules table

| Placeholder | Derivation Rule |
|---|---|
| `{{isVvcAgent}}` | `true` when the agent being generated has `id === "vvc-specialist"`; `false` for all other agents. Applied per-agent in Step 7 loop. |
| `{{vvcWebFetchCap}}` | `min(advanced.maxWebFetchesPerAgent * 3, 50)`. Default: 30 (when base cap is 10). Used only in VVC agent template conditional body. |
| `{{vvcArgumentHint}}` | If `qualityFramework.vvc.enabled` is true: `" [--no-vvc]"`; otherwise: empty string. |
| `{{comprehensiveFollowUpAgentCap}}` | From `advanced.comprehensiveFollowUpAgentCap` (default: 2). Maximum agents to deploy in Phase 3.5 gap follow-up. |
| `{{provenanceBudget}}` | From `advanced.tokenBudgets.provenance` (default: 5000). |
| `{{vvcEnabled}}` | Mirror of `qualityFramework.vvc.enabled`. Used for conditional blocks in standards.md.tmpl. |

#### 6b. Step 7 agent generation update

Add `isVvcAgent` and `vvcWebFetchCap` derivation to the per-agent loop. Current Step 7 description (line 244):

> For EACH agent: read `agent-template.md.tmpl`, replace with agent-specific values.

Amend to:

> For EACH agent: set `{{isVvcAgent}}` = (`agent.id === "vvc-specialist"`). Set `{{vvcWebFetchCap}}` = `min(advanced.maxWebFetchesPerAgent * 3, 50)`. Read `agent-template.md.tmpl`, replace with agent-specific values including conditional blocks. Cycle `{{color}}` through blue, magenta, yellow.

#### 6c. `engine-config-schema.json` updates

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

#### 6d. Section 8 wizard update

In the advanced settings prompt (SKILL.md line 171), add after "token budgets":

```
max follow-up agents for Comprehensive tier (1-5, default 2)
```

---

## Files Modified (Summary)

| File | Changes | Issues Fixed |
|---|---|---|
| `templates/agent-template.md.tmpl` | Add `{{#if isVvcAgent}}` conditionals for examples, body, First Actions; remove Domain Context section | C-1, C-2, H-1, M-4 |
| `templates/orchestrator-skill.md.tmpl` | Fix exploration depth instruction; add Phase 3.5 follow-up; remove trailing text; update Phase 4.5 | C-3, H-3, H-5, H-6 |
| `templates/command-template.md.tmpl` | Add `{{vvcArgumentHint}}` to argument-hint | C-4 |
| `templates/research-protocol.md.tmpl` | Align 450 token limit; parameterize provenance budget | M-1, M-2 |
| `templates/standards.md.tmpl` | Add probe budget note; replace claim taxonomy with cross-reference | H-2, M-3 |
| `templates/engine-config-schema.json` | Add `comprehensiveFollowUpAgentCap`, `tokenBudgets.provenance` | M-1, H-5 |
| `SKILL.md` (generation logic) | Add 6 new placeholder derivation rules; update Step 7 loop; update Section 8 wizard | All |

## Files NOT Modified

| File | Reason |
|---|---|
| `templates/vvc-pipeline.md.tmpl` | Already correct — canonical claim taxonomy stays here |
| `templates/provenance.md.tmpl` | No issues found |
| `templates/extension-skill.md.tmpl` | Out of scope (extension mode) |
| `templates/plugin-json.tmpl` | No issues found |
| `templates/readme-template.md.tmpl` | No issues found |
| `templates/sources-command-template.md.tmpl` | No issues found |

## Testing

After implementation, validate by:

1. Run `/test-engine` against a freshly generated engine with VVC enabled — verify VVC specialist agent file contains verification protocol (not search protocol) and reads `vvc-pipeline.md` in First Actions
2. Run `/test-engine` against a freshly generated engine with VVC disabled — verify no VVC conditionals leak into agent files
3. Grep generated SKILL.md for "Now executing research deployment" — should not appear
4. Grep generated SKILL.md for "Recursive web exploration up to" — should not appear
5. Verify generated `research.md` command argument-hint contains `--no-vvc` when VVC enabled
6. Verify generated `standards.md` contains claim taxonomy cross-reference (not full table) when VVC enabled
7. Verify generated `research-protocol.md` says "450 tokens" (not 500)
8. Verify `engine-config.json` schema validates with new `comprehensiveFollowUpAgentCap` and `tokenBudgets.provenance` fields
9. Verify Phase 3.5 block appears in generated SKILL.md only in comprehensive tier documentation
10. Verify Phase 4.5 references both provenance audit AND citation verification
