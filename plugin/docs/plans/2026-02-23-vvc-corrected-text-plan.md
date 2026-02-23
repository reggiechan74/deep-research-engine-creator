# VVC Corrected Text in Verification Report — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Phase 5 (VVC-Verify) produce ready-to-apply corrected text so Phase 6 (VVC-Correct) becomes a mechanical application step instead of an independent rewriting phase.

**Architecture:** Add `Corrected Text` and `New Source` columns to the Phase 5 verification table. Update Phase 5 instructions to write corrections at point of verification. Simplify Phase 6 instructions from "active rewriting" to "mechanical application". Propagate changes across the engine-creator SKILL.md derivation rules, the base template (which uses placeholders), the VVC agent template, and the patent-intelligence-engine example.

**Tech Stack:** Markdown templates with mustache-style placeholder substitution

---

### Task 1: Update the engine-creator SKILL.md — `{{vvcVerifyPhaseBlock}}` derivation rule

**Files:**
- Modify: `plugin/skills/engine-creator/SKILL.md:262`

**Step 1: Edit the `{{vvcVerifyPhaseBlock}}` derivation rule**

On line 262, replace the current derivation rule:

```
| `{{vvcVerifyPhaseBlock}}` | If VVC enabled AND tier behavior is "verify-only" or "full": generate complete Phase 5 VVC-Verify section with instructions to deploy **vvc-specialist** to: read draft report + all bibliographies, extract all [VC] claims with cited sources and confidence tiers, apply verification scope (100% HIGH, {MEDIUM}% MEDIUM, {LOW}% LOW, 0% SPECULATIVE), per-claim protocol (locate source → extract quote → analyze alignment → classify as CONFIRMED/PARAPHRASED/OVERSTATED/UNDERSTATED/DISPUTED/UNSUPPORTED/SOURCE_UNAVAILABLE → recommend KEEP/REVISE/DOWNGRADE/REMOVE/REPLACE_SOURCE), output `_VVC_Verification_Report.md` with summary stats + per-claim table; otherwise: empty string |
```

With:

```
| `{{vvcVerifyPhaseBlock}}` | If VVC enabled AND tier behavior is "verify-only" or "full": generate complete Phase 5 VVC-Verify section with instructions to deploy **vvc-specialist** to: read draft report + all bibliographies, extract all [VC] claims with cited sources and confidence tiers, apply verification scope (100% HIGH, {MEDIUM}% MEDIUM, {LOW}% LOW, 0% SPECULATIVE), per-claim protocol (locate source → extract quote → analyze alignment → classify as CONFIRMED/PARAPHRASED/OVERSTATED/UNDERSTATED/DISPUTED/UNSUPPORTED/SOURCE_UNAVAILABLE → recommend KEEP/REVISE/DOWNGRADE/REMOVE/REPLACE_SOURCE → write corrected text per recommendation rules), corrected text rules (KEEP: "---", REVISE: rewritten claim reflecting accurate source content, DOWNGRADE: claim with qualifying language and lowered confidence tier, REMOVE: "[REMOVE]", REPLACE_SOURCE: corrected claim text citing new source + replacement source URL found during verification), output `_VVC_Verification_Report.md` with summary stats + per-claim table including Corrected Text and New Source columns; otherwise: empty string |
```

**Step 2: Verify the edit**

Read the file around line 262 and confirm the new derivation rule is in place.

**Step 3: Commit**

```bash
git add plugin/skills/engine-creator/SKILL.md
git commit -m "feat(vvc): add corrected text to vvcVerifyPhaseBlock derivation rule"
```

---

### Task 2: Update the engine-creator SKILL.md — `{{vvcCorrectPhaseBlock}}` derivation rule

**Files:**
- Modify: `plugin/skills/engine-creator/SKILL.md:263`

**Step 1: Edit the `{{vvcCorrectPhaseBlock}}` derivation rule**

On line 263, replace the current derivation rule:

```
| `{{vvcCorrectPhaseBlock}}` | If VVC enabled AND tier behavior is "full": generate complete Phase 6 VVC-Correct section with instructions to deploy **vvc-specialist** (second pass) to: read verification report + draft report, implement REVISE/DOWNGRADE/REMOVE/REPLACE_SOURCE recommendations, output `_Comprehensive_Report.md` (final) + `_VVC_Correction_Log.md` + Verification Statement appendix; if tier behavior is "verify-only": empty string (Phase 4 draft becomes final with verification report alongside) |
```

With:

```
| `{{vvcCorrectPhaseBlock}}` | If VVC enabled AND tier behavior is "full": generate complete Phase 6 VVC-Correct section with instructions to deploy **vvc-specialist** (second pass) to: read verification report per-claim table, apply corrected text mechanically into draft report (REVISE/DOWNGRADE: substitute Corrected Text verbatim, REMOVE: delete claim and adjust surrounding narrative for coherence, REPLACE_SOURCE: substitute Corrected Text and update bibliography with New Source), preserve all KEEP/CONFIRMED claims unchanged, NO independent rewriting or source searching — all corrections come from the Phase 5 verification table, output `_Comprehensive_Report.md` (final) + `_VVC_Correction_Log.md` + Verification Statement appendix; if tier behavior is "verify-only": empty string (Phase 4 draft becomes final with verification report alongside) |
```

**Step 2: Verify the edit**

Read the file around line 263 and confirm the new derivation rule is in place.

**Step 3: Commit**

```bash
git add plugin/skills/engine-creator/SKILL.md
git commit -m "feat(vvc): simplify vvcCorrectPhaseBlock to mechanical application"
```

---

### Task 3: Update the patent-intelligence-engine example — Phase 5 verification report structure

**Files:**
- Modify: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md:477-520`

**Step 1: Update the Phase 5 per-claim protocol**

In the Phase 5 section (around line 487-492), update the per-claim verification steps. Replace:

```markdown
- **For each claim selected for verification:**
  1. Locate the cited source (fetch URL via WebFetch or search for the source)
  2. Extract the relevant quote or data point from the source
  3. Analyze alignment between the claim text and the source content
  4. Classify alignment: CONFIRMED | PARAPHRASED | OVERSTATED | UNDERSTATED | DISPUTED | UNSUPPORTED | SOURCE_UNAVAILABLE
  5. Recommend action: KEEP | REVISE | DOWNGRADE | REMOVE | REPLACE_SOURCE
```

With:

```markdown
- **For each claim selected for verification:**
  1. Locate the cited source (fetch URL via WebFetch or search for the source)
  2. Extract the relevant quote or data point from the source
  3. Analyze alignment between the claim text and the source content
  4. Classify alignment: CONFIRMED | PARAPHRASED | OVERSTATED | UNDERSTATED | DISPUTED | UNSUPPORTED | SOURCE_UNAVAILABLE
  5. Recommend action: KEEP | REVISE | DOWNGRADE | REMOVE | REPLACE_SOURCE
  6. Write corrected text per recommendation:
     - **KEEP:** "---" (no change needed)
     - **REVISE:** Rewrite the claim to accurately reflect the source content
     - **DOWNGRADE:** Rewrite the claim with qualifying language (e.g., "approximately", "reportedly") and lower the confidence tier
     - **REMOVE:** "[REMOVE]"
     - **REPLACE_SOURCE:** Rewrite the claim with accurate content, search for and provide a replacement source URL in the New Source column
```

**Step 2: Update the verification report table structure**

In the Verification Report Structure section (around line 511-513), replace:

```markdown
### Per-Claim Verification Table
| # | Claim Text (truncated) | Source | Confidence | Classification | Recommendation | Notes |
|---|------------------------|--------|------------|----------------|----------------|-------|
```

With:

```markdown
### Per-Claim Verification Table
| # | Claim Text (truncated) | Source | Confidence | Classification | Recommendation | Corrected Text | New Source | Notes |
|---|------------------------|--------|------------|----------------|----------------|----------------|------------|-------|
```

**Step 3: Verify edits**

Read Phase 5 section and confirm both changes are in place.

**Step 4: Commit**

```bash
git add plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md
git commit -m "feat(vvc): add corrected text to Phase 5 verification table in patent example"
```

---

### Task 4: Update the patent-intelligence-engine example — Phase 6 correction instructions

**Files:**
- Modify: `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md:528-562`

**Step 1: Replace Phase 6 instructions**

Replace the Phase 6 correction instructions (lines 536-541):

```markdown
- **Implement corrections** for all REVISE/DOWNGRADE/REMOVE/REPLACE_SOURCE recommendations:
  - **REVISE:** Rewrite the claim to accurately reflect the source content
  - **DOWNGRADE:** Lower the confidence tier and add qualifying language
  - **REMOVE:** Delete the claim and adjust surrounding narrative for coherence
  - **REPLACE_SOURCE:** Find and cite a more accurate source for the claim
```

With:

```markdown
- **Apply corrections mechanically** from the Phase 5 verification table's Corrected Text column:
  - **REVISE:** Substitute the Corrected Text from the verification table verbatim
  - **DOWNGRADE:** Substitute the Corrected Text from the verification table verbatim (includes qualifying language and lowered confidence tier)
  - **REMOVE:** Delete the claim and adjust surrounding narrative for coherence
  - **REPLACE_SOURCE:** Substitute the Corrected Text from the verification table and update the bibliography with the New Source URL
- **Do NOT** independently rewrite claims or search for sources — all corrections are pre-written in the verification report
```

**Step 2: Verify edit**

Read Phase 6 section and confirm the instructions now describe mechanical application.

**Step 3: Commit**

```bash
git add plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md
git commit -m "feat(vvc): simplify Phase 6 to mechanical application in patent example"
```

---

### Task 5: Update the VVC specialist agent definition

**Files:**
- Modify: `plugin/examples/patent-intelligence-engine/agents/vvc-specialist.md:52-126`

**Step 1: Update Phase 5 per-claim protocol in agent definition**

In the Phase 5 section (around lines 60-65), replace:

```markdown
5. **For each claim selected for verification:**
   - Locate the cited source (fetch URL via WebFetch or search for the source)
   - Extract the relevant quote or data point from the source
   - Analyze alignment between the claim and the source content
   - Classify: CONFIRMED | PARAPHRASED | OVERSTATED | UNDERSTATED | DISPUTED | UNSUPPORTED | SOURCE_UNAVAILABLE
   - Recommend: KEEP | REVISE | DOWNGRADE | REMOVE | REPLACE_SOURCE
```

With:

```markdown
5. **For each claim selected for verification:**
   - Locate the cited source (fetch URL via WebFetch or search for the source)
   - Extract the relevant quote or data point from the source
   - Analyze alignment between the claim and the source content
   - Classify: CONFIRMED | PARAPHRASED | OVERSTATED | UNDERSTATED | DISPUTED | UNSUPPORTED | SOURCE_UNAVAILABLE
   - Recommend: KEEP | REVISE | DOWNGRADE | REMOVE | REPLACE_SOURCE
   - Write corrected text per recommendation:
     - KEEP: "---"
     - REVISE: Rewritten claim reflecting accurate source content
     - DOWNGRADE: Claim with qualifying language and lowered confidence tier
     - REMOVE: "[REMOVE]"
     - REPLACE_SOURCE: Corrected claim text + search for and provide replacement source URL
```

**Step 2: Update the verification report table in agent definition**

In the Verification Report Structure section (around lines 84-86), replace:

```markdown
### Per-Claim Verification Table
| # | Claim Text (truncated) | Source | Confidence | Classification | Recommendation | Notes |
|---|------------------------|--------|------------|----------------|----------------|-------|
```

With:

```markdown
### Per-Claim Verification Table
| # | Claim Text (truncated) | Source | Confidence | Classification | Recommendation | Corrected Text | New Source | Notes |
|---|------------------------|--------|------------|----------------|----------------|----------------|------------|-------|
```

**Step 3: Update Phase 6 instructions in agent definition**

In the Phase 6 section (around lines 101-105), replace:

```markdown
3. **Implement corrections** for all REVISE/DOWNGRADE/REMOVE/REPLACE_SOURCE recommendations:
   - REVISE: Rewrite claim to accurately reflect the source content
   - DOWNGRADE: Lower the confidence tier and add qualifying language
   - REMOVE: Delete the claim and adjust surrounding narrative
   - REPLACE_SOURCE: Find and cite a more accurate source for the claim
```

With:

```markdown
3. **Apply corrections mechanically** from the Phase 5 verification table's Corrected Text column:
   - REVISE: Substitute the Corrected Text verbatim
   - DOWNGRADE: Substitute the Corrected Text verbatim (includes qualifying language and lowered confidence tier)
   - REMOVE: Delete the claim and adjust surrounding narrative for coherence
   - REPLACE_SOURCE: Substitute the Corrected Text and update bibliography with the New Source URL
   - Do NOT independently rewrite claims or search for sources — all corrections are pre-written in the verification report
```

**Step 4: Verify all edits**

Read the full vvc-specialist.md and confirm Phase 5 has corrected text instructions, the table has new columns, and Phase 6 describes mechanical application.

**Step 5: Commit**

```bash
git add plugin/examples/patent-intelligence-engine/agents/vvc-specialist.md
git commit -m "feat(vvc): update VVC specialist agent with corrected text columns and mechanical Phase 6"
```

---

### Task 6: Final validation

**Step 1: Review all changes**

```bash
cd /workspaces/reggie-life-plan/deep-research-engine-creator
git diff HEAD~4 --stat
git log --oneline -5
```

**Step 2: Verify consistency across files**

Check that all four files have consistent table structures (same column names, same order) and consistent Phase 6 language (mechanical application, not independent rewriting).

Read and scan:
- `plugin/skills/engine-creator/SKILL.md` — lines 262-263
- `plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md` — Phase 5 and Phase 6 sections
- `plugin/examples/patent-intelligence-engine/agents/vvc-specialist.md` — Phase 5 and Phase 6 sections

**Step 3: Run test-engine if available**

```bash
# Validate the example engine against schema
# (if /test-engine command is available)
```
