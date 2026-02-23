---
title: VVC Corrected Text in Verification Report
date: 2026-02-23
keywords: [vvc, verification, correction, phase-5, phase-6]
lastUpdated: 2026-02-23
---

# VVC Corrected Text in Verification Report

## Problem

Phase 5 (VVC-Verify) identifies claim-source misalignments and recommends actions (REVISE, DOWNGRADE, REMOVE, REPLACE_SOURCE), but does not provide the corrected text. Phase 6 (VVC-Correct) must independently figure out what the correction should be, duplicating work and losing context that Phase 5 already had when it fetched and compared the source.

## Design

Add `Corrected Text` and `New Source` columns to the Phase 5 verification table. Phase 5 writes ready-to-apply corrections at the point of maximum context. Phase 6 becomes a mechanical application step.

## Verification Table (Before)

```
| # | Claim Text | Source | Confidence | Classification | Recommendation | Notes |
```

## Verification Table (After)

```
| # | Claim Text | Source | Confidence | Classification | Recommendation | Corrected Text | New Source | Notes |
```

## Corrected Text Rules by Recommendation

| Recommendation | Corrected Text | New Source |
|---|---|---|
| KEEP | --- | --- |
| REVISE | Rewritten claim reflecting accurate source content | --- |
| DOWNGRADE | Claim with qualifying language (e.g., "approximately", "reportedly") and lowered confidence tier | --- |
| REMOVE | [REMOVE] | --- |
| REPLACE_SOURCE | Corrected claim text citing new source | Replacement source URL and citation |

For REPLACE_SOURCE: Phase 5 searches for and provides the replacement source during verification rather than deferring to Phase 6.

## Phase 6 Role Change

Phase 6 changes from "active rewriting with independent research" to "mechanical application":

1. Read verification table
2. Apply each `Corrected Text` entry verbatim into the draft report
3. Remove [REMOVE]-flagged claims and adjust surrounding narrative for coherence
4. Update source references and bibliography for REPLACE_SOURCE entries
5. Add Verification Statement appendix
6. Produce `_Comprehensive_Report.md` and `_VVC_Correction_Log.md`

Phase 6 does NOT independently rewrite claims or search for sources.

## Files to Modify

1. **`plugin/skills/engine-creator/SKILL.md`** (lines 262-263) -- Update `{{vvcVerifyPhaseBlock}}` and `{{vvcCorrectPhaseBlock}}` derivation rules
2. **`plugin/skills/engine-creator/templates/base-research-skill.md.tmpl`** -- No direct changes (template uses placeholders)
3. **`plugin/examples/patent-intelligence-engine/agents/vvc-specialist.md`** -- Update Phase 5 table structure and Phase 6 instructions
4. **`plugin/examples/patent-intelligence-engine/skills/patent-intelligence-engine/SKILL.md`** -- Update VVC phase blocks in the generated example

## What Doesn't Change

- Phase structure (7 phases with VVC)
- Claim taxonomy ([VC]/[PO]/[IE])
- Verification scope percentages
- Classification labels (CONFIRMED/PARAPHRASED/OVERSTATED/UNDERSTATED/DISPUTED/UNSUPPORTED/SOURCE_UNAVAILABLE)
- Recommendation action codes (KEEP/REVISE/DOWNGRADE/REMOVE/REPLACE_SOURCE)
- Output file names and structure
- Token budget configuration
