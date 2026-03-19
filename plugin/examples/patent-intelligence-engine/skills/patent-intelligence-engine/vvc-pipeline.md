# VVC Pipeline Reference — Patent Intelligence Engine

## Claim Type Taxonomy

Every factual assertion in the draft report (Phase 4) MUST be tagged with one of these claim types:

| Tag | Label | Description | Requires Verification |
|-----|-------|-------------|----------------------|
| `[VC]` | Verifiable Claim | Factual assertion about patent data (numbers, dates, assignees, claim counts, filing status) with a cited source that can be independently verified against official patent office records | Yes |
| `[PO]` | Professional Opinion | Expert interpretation or analytical judgment derived from patent landscape evidence, such as FTO risk assessments, whitespace opportunity evaluations, or portfolio strength comparisons | No |
| `[IE]` | Inferred/Extrapolated | Logical inference or extrapolation from patent filing trends, classification patterns, or market data without direct source confirmation | No |

## VVC Verification Scope

| Confidence Level | Verification Rate | Rationale |
|-----------------|-------------------|-----------|
| HIGH | 100% | All HIGH confidence verifiable claims are always verified |
| MEDIUM | 100% | All MEDIUM confidence verifiable claims are verified |
| LOW | 100% | All LOW confidence verifiable claims are verified |
| SPECULATIVE | 100% | All SPECULATIVE confidence claims are verified |

---

## Phase 5: VVC-Verify

**Tier behavior:** Quick: skip | Standard: run | Deep: run | Comprehensive: run

After the draft report is complete, deploy the **vvc-specialist** with instructions to:

- **FIRST ACTION**: Read the draft report at `BASE_DIR/[TOPIC_SLUG]_Draft_Report.md`
- Read all bibliography files and the master bibliography at `BASE_DIR/[TOPIC_SLUG]_Master_Bibliography.md`
- **Extract** all `[VC]`-tagged claims with their cited sources and confidence tiers
- **Apply verification scope:** 100% of HIGH confidence [VC] claims, 100% of MEDIUM confidence [VC] claims, 100% of LOW confidence [VC] claims, 100% of SPECULATIVE claims
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
- **Output:** Save verification report to `BASE_DIR/[TOPIC_SLUG]_VVC_Verification_Report.md`

### Verification Report Structure

```
## VVC Verification Report: [TOPIC]

### Summary
- Total [VC] claims extracted: N
- Claims selected for verification: N (per scope rules)
- CONFIRMED: N (%)
- PARAPHRASED: N (%)
- OVERSTATED: N (%)
- UNDERSTATED: N (%)
- DISPUTED: N (%)
- UNSUPPORTED: N (%)
- SOURCE_UNAVAILABLE: N (%)

### Per-Claim Verification Table
| # | Claim Text (truncated) | Source | Confidence | Classification | Recommendation | Corrected Text | New Source | Notes |
|---|------------------------|--------|------------|----------------|----------------|----------------|------------|-------|

### Issues Found
[List of claims requiring correction with details]

### Recommendations
[Prioritized list of corrections to implement in Phase 6]
```

- Output format (400 tokens or fewer in chat): `## Verification Summary | ## Key Issues (with claim refs) | ## Stats | ## Files Written`

**Standard tier:** Stop after Phase 5. The draft report becomes the final report alongside the verification report. Do NOT proceed to Phase 6.

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

---

## Phase 6: VVC-Correct

**Tier behavior:** Quick: skip | Standard: skip | Deep: run | Comprehensive: run

After verification is complete, deploy the **vvc-specialist** (second pass) with instructions to:

- **FIRST ACTION**: Read the verification report at `BASE_DIR/[TOPIC_SLUG]_VVC_Verification_Report.md`
- Read the draft report at `BASE_DIR/[TOPIC_SLUG]_Draft_Report.md`
- **Apply corrections mechanically** from the Phase 5 verification table's Corrected Text column:
  - **REVISE:** Substitute the Corrected Text from the verification table verbatim
  - **DOWNGRADE:** Substitute the Corrected Text from the verification table verbatim (includes qualifying language and lowered confidence tier)
  - **REMOVE:** Delete the claim and adjust surrounding narrative for coherence
  - **REPLACE_SOURCE:** Substitute the Corrected Text from the verification table and update the bibliography with the New Source URL
- **Do NOT** independently rewrite claims or search for sources — all corrections are pre-written in the verification report
- **Preserve** all KEEP and CONFIRMED claims unchanged
- **Add Verification Statement** appendix to the final report documenting the VVC process
- **Add Provenance Appendix** summarizing the hash chain from `BASE_DIR/[TOPIC_SLUG]_Provenance_Log.md`: chain integrity status, total events, unique domains, and independent verification instructions
- **Output:**
  - `BASE_DIR/[TOPIC_SLUG]_Comprehensive_Report.md` (final corrected report)
  - `BASE_DIR/[TOPIC_SLUG]_VVC_Correction_Log.md` (detailed log of all changes made)

### Correction Log Structure

```
## VVC Correction Log: [TOPIC]

### Summary
- Total corrections applied: N
- Revisions: N
- Downgrades: N
- Removals: N
- Source replacements: N

### Correction Details
| # | Original Claim | Issue | Action Taken | Corrected Text | Source Change |
|---|----------------|-------|--------------|----------------|--------------|
```

- Output format (400 tokens or fewer in chat): `## Corrections Applied | ## Changes Summary | ## Final Report Stats | ## Files Written`
