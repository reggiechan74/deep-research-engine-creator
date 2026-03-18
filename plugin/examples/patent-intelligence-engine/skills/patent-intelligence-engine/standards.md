# Quality Standards Reference — Patent Intelligence Engine

---

## Global Standards

Apply to ALL agents across ALL tiers. These standards are non-negotiable and must be
followed by every agent in the pipeline.

### Confidence Scoring Framework

```
HIGH        (●●●): Verified against official patent office databases (USPTO, EPO, WIPO). Patent numbers confirmed as valid with current status checked. Claim analysis based on actual claim text from granted patents. Multiple authoritative sources agree on assignee, dates, and classification.
MEDIUM      (●●○): Supported by patent analytics platforms or secondary patent databases, corroborated by at least 1 official patent office source. Patent family connections inferred from priority claims and verified where possible. Claim scope assessments are consistent with prosecution history.
LOW         (●○○): Based on a single commercial patent database, industry report, or news source without verification against official patent office records. Patent status may not be current. Claim analysis based on abstracts rather than full claim text.
SPECULATIVE (○○○): Based on published patent applications (not yet granted), roadmap announcements of IP strategy, or extrapolation from filing trends. Represents projected IP positions rather than confirmed rights. Includes freedom-to-operate assessments based on pending claims that may change during prosecution.
```

**Rule:** Every claim in claims tables MUST include a confidence tier. All HIGH-impact
claims MUST be HIGH confidence or explicitly flagged as exceptions. All patent claims require patent number verification against at least one official patent office database (USPTO, EPO, WIPO). Patent status (active, expired, abandoned, pending) must be confirmed. Claim scope assessments require reference to actual claim text. FTO conclusions require identification of specific patent claims and their relationship to the subject technology.

### Source Credibility Hierarchy

```
Tier 1 (Official Patent Databases):  USPTO PATFT and AppFT (patents.google.com, patft.uspto.gov), European Patent Office (EPO) Espacenet and Global Patent Index, WIPO PATENTSCOPE and PCT publications, Google Patents with full-text search and classification browsing, National patent office databases (JPO J-PlatPat, KIPO KIPRIS, CNIPA, CIPO)
Tier 2 (Patent Analytics & Legal Sources):  Patent prosecution histories (USPTO PAIR, EPO Register), Patent litigation databases (PACER, Docket Navigator, Lex Machina), Published patent examiner search reports and office actions, PTAB decisions and inter partes review proceedings, Patent classification systems (CPC, IPC) official documentation
Tier 3 (Technical & Scientific Literature):  Peer-reviewed technical journals related to the patent domain, Conference proceedings from major technical conferences, Standards body publications (IEEE, ISO, ASTM) relevant to patent claims, Published doctoral dissertations and technical reports, ArXiv preprints and academic working papers with disclosed methodology
Tier 4 (Industry & Commercial Sources):  Patent analytics platform reports (PatSnap, Orbit Intelligence, Innography), Industry news and trade publications covering patent activity, Company press releases and investor presentations mentioning IP, Technology blog posts from recognized patent attorneys and IP professionals, Patent valuation and licensing market reports
Tier 5 (Unreliable / Unverified):  Anonymous forum posts and unattributed patent commentary, Marketing materials claiming patent-pending status without application numbers, AI-generated patent summaries without verification against original filings, Unverified patent ownership claims on company websites, Social media discussions about patent disputes without case citations
```

**Rule:** No HIGH confidence claim can rest solely on Tier 4-5 sources. At minimum,
one Tier 1-3 source is required for any HIGH confidence assertion.

### Citation & Evidence Standards

- **Citation format:** APA 7th Edition with patent-specific extensions. Patents: Inventor(s), Patent Title, Patent No. XX,XXX,XXX, Filed [date], Granted [date], Assignee: [name]. Applications: Inventor(s), Title, Pub. No. [number], Filed [date], Published [date]. Inline numbered references [1] with full bibliography. Include patent office URLs where available.
- Use numbered footnotes `[^1]`, `[^2]`, etc. for inline source references
- Use citation IDs by agent type: `[W-01]` (web), `[E-01]` (expert), `[I-01]` (intel)
- Master bibliography maps IDs to full citations with clickable URLs
- Do not repeat full citations in chat; use IDs and defer to bibliography files
- **Evidence rules:** No high-impact claim without 2+ independent sources, or mark as LOW confidence
- **Adversarial sweep:** Always look for refutations, critiques, failure cases, and contradictory data
- Log contradictions in methodology file

### Validation Rules

1. Verify all patent numbers against official patent office databases (USPTO PATFT/AppFT, EPO Espacenet, WIPO PATENTSCOPE) and confirm current legal status.
2. Confirm patent assignee information is current by checking assignment records -- patents may have been transferred, licensed, or sold.
3. Distinguish between granted patents and pending applications when assessing IP strength and enforceability.
4. Validate CPC and IPC classification codes against official classification schemes to ensure accuracy of landscape mapping.
5. Cross-check patent family connections using priority claim data from multiple patent offices.
6. Verify that cited prior art references are actually relevant to the claims under analysis, not just topically related.
7. Flag any patent status data older than 6 months as potentially outdated -- maintenance fees, assignments, and litigation may have changed status.
8. Assess patent term calculations considering any patent term adjustments (PTA) or terminal disclaimers.
9. Confirm that freedom-to-operate assessments reference specific claim elements, not just patent titles or abstracts.

### Structured Output Standards

- Use claims/evidence/confidence tables for all findings
- Log queries, engines, and filters to `BASE_DIR/[TOPIC_SLUG]_Methodology_Log_[AgentID].md`
- Save claims tables per agent as `BASE_DIR/[TOPIC_SLUG]_Claims_[AgentID].md`
- Save source lists per agent as `BASE_DIR/[TOPIC_SLUG]_Sources_[AgentID].md`
- Each claims table row must include: Claim | Evidence | Confidence Tier | Source IDs | Source Credibility Tier

---

## Bibliography & Footnote Standards

### In-Text Citations

- Use numbered footnotes for immediate source reference: `[^1]`, `[^2]`, etc.
- Sequential numbering per document (not per section)
- Place footnote markers immediately after relevant statements
- Example: `According to the report[^1], the market grew at 15% CAGR.`

### Footnote Placement

- Place footnotes at the end of each major section for immediate context
- Use APA 7th Edition with patent-specific extensions format in footnotes with clickable URLs
- Cross-reference master bibliography when applicable

### Master Bibliography

- All citations follow APA 7th Edition with patent-specific extensions format with clickable URLs
- Include complete source information with access dates
- Organize by source type and credibility tier
- Cross-reference footnote numbers where sources appear in reports
- Include source attribution indicating which agent discovered each source

### Bibliography Deduplication Rules

- Same URL --> merge, keep earliest discovery timestamp
- Same content, different URLs --> note both, mark canonical
- Different editions/versions --> keep most recent unless historical context needed
- Conflicting information from same source --> note both dates and what changed

---

## Source Verification Protocol

Every research run must include source verification proportional to the configured
verification mode. This protocol prevents citation rot, dead links, and claim-source
mismatches from undermining research quality.

### Verification Mode: spot-check

Verify a random sample of HIGH-confidence citations (minimum 3 or 20% of HIGH citations, whichever is greater). Record verification results in methodology log.

### Probe on Discovery: true

When probe-on-discovery is enabled, each Phase 2 research agent must:
- Verify source URL resolves (HTTP 200) immediately when found
- If source is unreachable, note in `_Methodology_Log_[AgentID].md` and do NOT use for HIGH confidence claims
- Attempt archive.org fallback if configured: `https://web.archive.org/web/*/[URL]`
- This prevents wasted analysis on sources that cannot be independently verified

### URL Liveness Checking: true

When enabled, the reporting agent (Phase 4) or a dedicated verification pass must:
- Check every cited URL in the master bibliography resolves
- Record HTTP status codes for each URL
- Flag any non-200 responses in the verification report

### Source Freshness: 2-year

Sources older than the freshness threshold are flagged (not automatically excluded):
- Flag in claims tables with `[STALE: published YYYY]` marker
- Stale sources cannot be the sole basis for HIGH confidence claims
- Stale but still-relevant sources should note: "Historical source — verify current applicability"

### Dead Link Handling: archive-fallback

Attempt Wayback Machine retrieval at https://web.archive.org/web/*/[URL]. If archived version found, use it and note [ARCHIVED: date] in bibliography. If not found, mark as [DEAD LINK].

### Content-Claim Matching: false

When enabled (token-expensive):
- For each HIGH confidence claim, fetch the cited source
- Verify the claim accurately reflects the source content
- Flag mismatches as: CONFIRMED (exact match), PARAPHRASED (reasonable interpretation), DISPUTED (source says something different), UNSUPPORTED (claim not found in source)
- Record results in the verification report

### Citation Verification Report

Generate a standalone Citation Verification Report. Scope: high-confidence-only. Include summary statistics, per-citation verification table, issues found, and remediation recommendations.

When verification reporting is enabled, generate:
`BASE_DIR/[TOPIC_SLUG]_Citation_Verification_Report.md`

Report structure:
```
## Citation Verification Report: [TOPIC]

### Summary
- Total citations: N
- Verified: N (%)
- URL alive: N (%)
- URL dead/unreachable: N
- Stale sources (> threshold): N
- Content-claim matches: N/A or N verified

### Verification Details
| Citation ID | URL | Status | Freshness | Content Match | Notes |
|-------------|-----|--------|-----------|---------------|-------|
| [W-01] | url | ALIVE/DEAD/REDIRECT | Current/Stale(YYYY) | N/A or CONFIRMED/DISPUTED | ... |

### Issues Found
[List any dead links, stale sources, content mismatches, or unverifiable claims]

### Recommendations
[Suggested actions: replace dead sources, update stale references, verify disputed claims]
```
