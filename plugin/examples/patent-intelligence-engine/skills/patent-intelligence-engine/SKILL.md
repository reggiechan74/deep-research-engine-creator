---
name: patent-intelligence-engine
description: "Domain-specialized research engine for intellectual property and patent landscape analysis. Multi-agent pipeline with tiered depth, iterative refinement, and structured confidence scoring for IP attorneys, technology transfer officers, and R&D strategists."
---

# Patent Intelligence Engine Research Engine

Launch a comprehensive multi-agent research system specialized for **Intellectual property and patent landscape analysis** research,
serving **IP attorneys, technology transfer officers, and R&D strategists**.

This engine implements a seven-phase research pipeline with tier-based depth routing. It is
fully self-contained -- no external research plugin dependencies are required. All protocols,
agent definitions, quality standards, and output specifications are defined in this file.

## Usage

- `/research [topic]` -- Standard tier (default): 2 agents: Patent Search Specialist, Prior Art Analyst
- `/research [URL]` -- Research starting from a specific webpage (Standard tier)
- `/research [topic] --quick` -- Quick tier: Single-agent lookup using Patent Search Specialist
- `/research [topic] --deep` -- Deep tier: Full pipeline with 3 agents: Patent Search Specialist, Prior Art Analyst, IP Landscape Mapper
- `/research [topic] --comprehensive` -- Comprehensive tier: All 3 agents + follow-up round
- `/research [topic] --outline-only` -- Planning phase only (produces outline, then stops)
- `/research [topic] --approve` -- Pause for user approval after Phase 1 before proceeding

---

## Research Architecture

This engine implements a **seven-phase research system** with tier-based depth routing:

1. **Phase 0: Tier Detection** -- Parse flags, configure paths and depth
2. **Phase 1: Research Planning** -- Strategic framework development and agent task design
3. **Phase 2: Parallel Research** -- Multiple specialist agents research simultaneously with iterative refinement
4. **Phase 3: Synthesis** -- Multi-source integration, contradiction resolution, and gap analysis
5. **Phase 4: Draft Reporting** -- Draft report generation with claim tagging for VVC verification
6. **Phase 5: VVC-Verify** -- Verify draft report claims against cited sources, produce verification report
7. **Phase 6: VVC-Correct** -- Implement corrections, produce final Comprehensive Report + correction log

### Tier Configuration

| Tier | Planning | Research Agents | Synthesis | Report | VVC | User Gate |
|------|----------|----------------|-----------|--------|-----|-----------|
| Quick | No | patent-search-specialist | No | Inline | None | No |
| Standard | Yes | patent-search-specialist, prior-art-analyst | Yes | Draft | Verify-only | --approve only |
| Deep | Yes | patent-search-specialist, prior-art-analyst, ip-landscape-mapper | Yes | Draft | Full | --approve only |
| Comprehensive | Yes | patent-search-specialist, prior-art-analyst, ip-landscape-mapper + follow-up round | Yes | Draft | Full | Always |

---

## Phase 0: Tier Detection & Global Configuration

Parse tier from `$ARGUMENTS`:

- If `--quick` is present, set tier to **Quick**
- If `--standard` is present, set tier to **Standard**
- If `--deep` is present, set tier to **Deep**
- If `--comprehensive` is present, set tier to **Comprehensive**
- If `--outline-only` is present, set tier to Standard but stop after Phase 1
- If `--approve` is present, pause after Phase 1 for user approval
- Otherwise, default to **Standard** tier
- Strip flag tokens from `$ARGUMENTS` to derive the research topic
- If topic starts with `http://` or `https://`, treat it as a URL seed
  - Fetch the page content using WebFetch
  - Extract topic/title from the page
  - Use URL as primary seed for recursive web exploration
  - Derive TOPIC_SLUG from extracted title

### Derive Configuration

```
TOPIC_SLUG  = lowercase topic, hyphenate spaces, strip punctuation
RUN_TS      = YYYY-MM-DD_HHMMSS_ET (Eastern Time via bash: TZ='America/New_York' date '+%Y-%m-%d_%H%M%S_ET')
BASE_DIR    = "02_KNOWLEDGE/5_RESEARCH_REPORTS/${RUN_TS}_${TOPIC_SLUG}"
ENGINE_ID   = "patent-intelligence-engine"
```

All files and directories live under `BASE_DIR`. Use `patent-intelligence-engine` as prefix in
file naming where engine identification is needed. Never restate the prompt in chat;
write long data to files and keep chat responses concise.

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

### Claim Type Taxonomy

Every factual assertion in the draft report (Phase 4) MUST be tagged with one of these claim types:

| Tag | Label | Description | Requires Verification |
|-----|-------|-------------|----------------------|
| `[VC]` | Verifiable Claim | Factual assertion about patent data (numbers, dates, assignees, claim counts, filing status) with a cited source that can be independently verified against official patent office records | Yes |
| `[PO]` | Professional Opinion | Expert interpretation or analytical judgment derived from patent landscape evidence, such as FTO risk assessments, whitespace opportunity evaluations, or portfolio strength comparisons | No |
| `[IE]` | Inferred/Extrapolated | Logical inference or extrapolation from patent filing trends, classification patterns, or market data without direct source confirmation | No |

### VVC Verification Scope

| Confidence Level | Verification Rate | Rationale |
|-----------------|-------------------|-----------|
| HIGH | 100% | All HIGH confidence verifiable claims are always verified |
| MEDIUM | 75% | Balanced depth for MEDIUM confidence claims |
| LOW | 0% | LOW confidence claims are not verified by default |
| SPECULATIVE | 0% | Speculative claims cannot be verified against sources |

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
- Log queries, engines, and filters to `BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md`
- Save claims tables per agent as `BASE_DIR/[TOPIC_SLUG]_Claims_[AgentID].md`
- Each claims table row must include: Claim | Evidence | Confidence Tier | Source IDs | Source Credibility Tier

### Context Discipline

- Summarize sources immediately; per-source abstracts of 120 words or fewer; use IDs not full citations in chat
- Each agent chat response of 500 tokens or fewer; avoid meta narration
- Pass-based workflow: Pass 1 (initial sweep + notes), Pass 2 (synthesis of top claims/gaps), Pass 3 (targeted follow-up on gaps)
- Before each pass, reload only outline + top notes to manage context window
- Abort conditions: stop recursion when no new credible sources after 2 alternate branches or depth cap reached
- Note all stops and aborts in methodology log

---

## Search Query Generation Protocol

For each research question, generate a minimum of 4 queries before searching:

1. **Direct query** -- Core terminology and primary keywords for the question
2. **Synonym variant** -- Alternative terms, Intellectual property and patent landscape analysis-specific jargon, regional naming conventions
3. **Adversarial** -- "problems with [X]", "criticism of [X]", "failure of [X]", "[X] controversy"
4. **Expert-source targeted** -- `site:` filters for preferred authoritative domains

### Preferred Sites for Targeted Queries

1. patents.google.com
2. patft.uspto.gov
3. appft.uspto.gov
4. worldwide.espacenet.com
5. patentscope.wipo.int
6. epo.org
7. scholar.google.com
8. lens.org
9. ipo.gov.uk
10. cipo.ic.gc.ca

### Domain-Specific Search Templates

- **patent-number-lookup**: `"{patent_number}" patent claims abstract assignee site:{preferred_site}`
- **technology-landscape**: `"{technology_keyword}" patent landscape {cpc_class} filing trend {year_range}`
- **assignee-portfolio**: `"{assignee_name}" patent portfolio {technology_area} site:{preferred_site}`
- **classification-search**: `{cpc_code} OR {ipc_code} "{technology_keyword}" patent site:patents.google.com`
- **prior-art-search**: `"{invention_keyword}" prior art {technical_field} before:{priority_date}`
- **patent-family**: `"{patent_number}" family continuation divisional priority claim`
- **fto-risk-search**: `"{technology_keyword}" patent infringement freedom-to-operate {jurisdiction}`
- **patent-litigation**: `"{patent_number}" OR "{assignee_name}" patent litigation lawsuit infringement {year}`
- **patent-citation-network**: `"{patent_number}" cited-by references forward-citation backward-citation`

Additional queries may be generated for geographic variants, temporal slices, or
domain-specific databases as the topic demands. All queries must be logged to
`BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md` with timestamps and result counts.

---

## Iterative Search-Assess-Refine Protocol

Each Phase 2 agent follows this protocol for each assigned research question:

```
For each assigned research question:

  Pass 1 -- SEARCH: Execute diversified query set (4+ queries per question)
    - Apply Search Query Generation Protocol
    - Cast wide net across source types and credibility tiers
    - Record all queries and results in Methodology_Log.md

  Pass 2 -- ASSESS: Evaluate sufficiency
    - Are there 2+ independent sources for key claims?
    - Are there unanswered sub-questions?
    - Are there contradictions needing resolution?
    - Score current evidence against Confidence Scoring Framework

  Pass 3 -- REFINE (if gaps found):
    - Generate targeted follow-up queries addressing specific gaps
    - Execute search with refined queries
    - Assess again against sufficiency criteria
    - Max 4 iterations per research question

  ABORT when:
    - No new credible sources after 2 alternate query branches
    - Depth cap reached (4 iterations)
    - Topic branch determined to be outside engine scope

  LOG: Each iteration recorded in Methodology_Log.md with:
    - Queries executed (with engine/filters)
    - Results found (count, top sources)
    - Sufficiency assessment
    - Decision (continue, refine, or abort)
```

---

## Cross-Agent Coordination Protocol

To prevent duplicate work and maximize coverage across parallel research agents:

- **Shared file:** `BASE_DIR/[TOPIC_SLUG]_Shared_Sources.md`
- **Format:** table with columns `| URL | Title | Relevance | Agent_ID | Timestamp |`
- Each Phase 2 agent: append high-value discoveries immediately after finding them
- Each Phase 2 agent: read Shared_Sources.md before starting each new search branch
- Skip already-covered sources; prioritize coverage gaps
- Create Shared_Sources.md if it does not exist on first write

---

## Failure Recovery Protocol

```
- Agent timeout with no output       --> Log gap in methodology file; proceed with remaining agents
- Agent produces no useful findings   --> Record gap; synthesis agent prioritizes gap-closing
- All agents fail on research question --> Flag as UNRESEARCHABLE with explanation
- Cross-agent contradictions          --> Synthesis runs dedicated reconciliation sub-task
- User reports factual error          --> Trigger targeted verification mini-search
```

---

## Sub-Agent System

The Patent Intelligence Engine research system uses these available sub-agents:

- research-planning-specialist
- synthesis-specialist
- research-reporting-specialist
- patent-search-specialist (Patent Search Specialist)
- prior-art-analyst (Prior Art Analyst)
- ip-landscape-mapper (IP Landscape Mapper)
- vvc-specialist (Verification, Validation & Correction Specialist)

Each sub-agent type provides different capabilities matched to its pipeline role. The
planning, synthesis, and reporting specialists are fixed pipeline roles; research agents
are domain-specialized instances configured for this engine's specific focus areas.
The vvc-specialist is a pipeline agent that runs in Phases 5-6 (post-reporting). It does NOT participate in Phase 2 research.

---

## Execution Strategy -- Quick Tier

If `--quick` detected, deploy a SINGLE agent (**patent-search-specialist**) with the following
instructions:

**Domain:** Intellectual property and patent landscape analysis

**Instructions:**
- Conduct focused web research on the topic within the Intellectual property and patent landscape analysis domain
- Apply Search Query Generation Protocol (minimum 4 query types per question)
- Apply Iterative Search-Assess-Refine Protocol (max 2 iterations)
- Apply Global Standards for evidence quality and confidence scoring
- Include confidence tier (HIGH/MEDIUM/LOW/SPECULATIVE) for every claim
- Note source credibility tier (1-5) for each source used
- Produce inline summary directly in chat response (no file output structure needed)
- Format: `## Summary | ## Key Findings (with confidence) | ## Sources | ## Limitations`

After deploying the quick agent, skip all remaining phases.

---

## Execution Strategy -- Standard / Deep / Comprehensive Tiers

### Phase 1: Strategic Research Planning

Deploy **research-planning-specialist** with instructions to:

- Analyze Intellectual property and patent landscape analysis research topic complexity, scope, and domain requirements
- Create systematic research framework mapping key investigation areas
- Build scope grid:
  - Core research questions
  - Sub-questions and hypotheses
  - Dissenting angles and contrarian viewpoints
  - Geographic and temporal slices relevant to Intellectual property and patent landscape analysis
- Identify optimal source types, authorities, and investigation methods
- Rank sources: primary > secondary > tertiary per the Source Credibility Hierarchy
- Design specific task assignments for downstream agents by question/region/era/counterposition to reduce overlap
- Establish quality standards, verification protocols, and synthesis strategies
- Generate research timeline and dependency mapping
- Create output specifications and integration protocols
- Include specific agent assignments, methodologies, and quality standards in the outline
- Create the foundation document that all subsequent research agents will read and follow
- Add gap-closing loop plan to revisit open questions after initial synthesis
- Save outline to `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md`
- Output format (300 tokens or fewer in chat): `## Focus | ## Scope Grid | ## Tasking | ## Risks/Gaps | ## Files Written`

**User Gates:**
- If `--outline-only`: Stop here. Present outline summary and exit.
- If `--comprehensive` OR `--approve`: Present outline to user for approval before proceeding to Phase 2.

---

### Phase 2: Parallel Research Execution

Deploy research agents simultaneously per tier configuration. Each agent operates
independently but coordinates through Shared_Sources.md.

#### Agent: Patent Search Specialist

Deploy **patent-search-specialist** (model: sonnet, type: general-purpose) with specialization:

Conducts comprehensive patent searches across major patent offices (USPTO, EPO, WIPO, JPO, KIPO, CNIPA, CIPO) using classification codes (CPC, IPC), keyword strategies, and assignee tracking. Identifies relevant patent families, prosecution histories, and citation networks. Assesses patent claim scope, priority dates, and geographic coverage to map intellectual property positions. Extracts key data points: patent numbers, filing dates, grant dates, assignees, inventors, claim counts, and citation metrics.

Search across all major patent offices (USPTO, EPO, WIPO, JPO, KIPO, CNIPA, CIPO as relevant). For each key patent, document: patent number, title, abstract summary, filing date, grant date (or publication date for applications), current assignee, independent claim count, total claim count, CPC/IPC classifications, and forward citation count. Identify patent families by tracing priority claims across jurisdictions. Track prosecution history for key patents to assess claim scope evolution, examiner rejections, and any narrowing amendments.

#### Agent: Prior Art Analyst

Deploy **prior-art-analyst** (model: sonnet, type: expert-instructor) with specialization:

Analyzes patent claims for novelty and non-obviousness against the prior art landscape. Applies the Teaching-Suggestion-Motivation (TSM) test and KSR obviousness framework to evaluate patentability. Reviews prosecution histories to understand claim scope evolution and examiner objections. Identifies relevant prior art references including patents, published applications, technical papers, conference proceedings, and commercial products. Assesses claim construction and identifies potential invalidity arguments.

For each technology area under investigation, build a comprehensive prior art map including: (1) patent prior art -- earlier patents and published applications with relevant claims, (2) non-patent literature -- technical papers, conference proceedings, standards documents, (3) commercial prior art -- products or services publicly available before the priority date. Apply the TSM (Teaching-Suggestion-Motivation) framework and KSR v. Teleflex obviousness analysis where assessing patentability. Document claim-by-claim mapping between subject patents and identified prior art.

#### Agent: IP Landscape Mapper

Deploy **ip-landscape-mapper** (model: sonnet, type: intelligence-analyst) with specialization:

Synthesizes patent data into comprehensive IP landscape assessments. Maps patent portfolios by assignee, filing trends over time, geographic distribution, and technology cluster analysis using CPC/IPC classification hierarchies. Identifies whitespace opportunities where patent protection is sparse. Builds competitive patent matrices comparing key players by portfolio size, claim breadth, geographic coverage, and remaining patent life. Assesses freedom-to-operate risks by mapping overlapping claims and identifies potential licensing opportunities or infringement risks.

Build a comprehensive IP landscape showing: filing trends over time by year, top assignees ranked by patent count and claim breadth, geographic filing patterns across major jurisdictions, and technology cluster mapping using CPC classification hierarchies. Create competitive portfolio matrices comparing key players across dimensions: portfolio size, average claim count, geographic spread, average remaining patent life, and citation impact. Identify whitespace regions in the CPC/IPC classification space where filing density is low relative to commercial activity. Assess freedom-to-operate risks by mapping potentially blocking patent claims against the subject technology.

#### Common Agent Requirements

Every Phase 2 research agent MUST:

1. **FIRST ACTION**: Read `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md` AND `BASE_DIR/[TOPIC_SLUG]_Shared_Sources.md` (create Shared_Sources.md if it does not exist)
2. Follow assigned research domains and methodologies from the outline
3. Apply Search Query Generation Protocol (minimum 4 query types per research question)
4. Apply Iterative Search-Assess-Refine Protocol (max 4 iterations per question)
5. Append high-value sources to `Shared_Sources.md` as discovered
6. Apply domain-specific focus: Conducts comprehensive patent searches across major patent offices (USPTO, EPO, WIPO, JPO, KIPO, CNIPA, CIPO) using classification codes (CPC, IPC), keyword strategies, and assignee tracking. Identifies relevant patent families, prosecution histories, and citation networks. Assesses patent claim scope, priority dates, and geographic coverage to map intellectual property positions. Extracts key data points: patent numbers, filing dates, grant dates, assignees, inventors, claim counts, and citation metrics.; Analyzes patent claims for novelty and non-obviousness against the prior art landscape. Applies the Teaching-Suggestion-Motivation (TSM) test and KSR obviousness framework to evaluate patentability. Reviews prosecution histories to understand claim scope evolution and examiner objections. Identifies relevant prior art references including patents, published applications, technical papers, conference proceedings, and commercial products. Assesses claim construction and identifies potential invalidity arguments.; Synthesizes patent data into comprehensive IP landscape assessments. Maps patent portfolios by assignee, filing trends over time, geographic distribution, and technology cluster analysis using CPC/IPC classification hierarchies. Identifies whitespace opportunities where patent protection is sparse. Builds competitive patent matrices comparing key players by portfolio size, claim breadth, geographic coverage, and remaining patent life. Assesses freedom-to-operate risks by mapping overlapping claims and identifies potential licensing opportunities or infringement risks.
7. Include confidence tier (HIGH/MEDIUM/LOW/SPECULATIVE) for every claim
8. Note source credibility tier (1-5) for each source used
9. Save bibliography file: `BASE_DIR/[TOPIC_SLUG]_[AgentID]_Bibliography.md`
10. Save claims table: `BASE_DIR/[TOPIC_SLUG]_Claims_[AgentID].md`
11. Log all search iterations to `BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md`
12. Apply Global Standards and outline quality standards
13. Output format (450 tokens or fewer in chat): `## Focus | ## Top Findings (7 bullets or fewer, with IDs + confidence) | ## Gaps/Next | ## Files Written`
14. Recursive web exploration up to 5 levels deep from authoritative seed URLs and alternate seeds — follow citation chains, linked references, and related pages
15. Document "unanswered questions" — research questions that remain open or partially answered after exhausting search iterations
16. Document "important absences" — information you expected to find based on the domain and topic but could not locate (negative evidence is itself evidence)
17. Run contrarian sweep: actively search for refutations, critiques, failure cases, and contradictory data for key claims found during research — do not only search for confirming evidence

---

### Phase 3: Research Synthesis

After all Phase 2 research agents complete, deploy the **synthesis-specialist** with
instructions to:

- **FIRST ACTION**: Read the research outline file `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md`
- Compare planned research coverage against actual research execution
- Read ALL agent output files: results, claims tables, bibliographies, shared sources
- Integrate findings from all research agents into coherent knowledge framework
- Cross-reference facts and claims across multiple independent sources
- Mark claims with confidence scores using the Confidence Scoring Framework
- Resolve contradictions and inconsistencies in research findings
- Generate meta-insights and higher-level implications
- Create unified understanding from fragmented information streams
- Note gaps between planned and executed research for the reporting agent
- Structure the analysis to support strategic IP decisions. Lead with the patent landscape overview showing the competitive environment. Present filing trend data with clear temporal patterns. Build competitive matrices that enable side-by-side portfolio comparison. For FTO assessments, clearly map the relationship between identified patent claims and the subject technology, using a risk-rating system (High/Medium/Low) for each potentially blocking patent. Quantify IP risks where possible: number of potentially blocking patents, years of remaining patent life, geographic coverage gaps, and litigation history of key patent holders. Identify actionable whitespace opportunities with supporting evidence from the landscape analysis.
- **Comprehensive tier only:** Propose targeted follow-up searches for uncovered gaps and dispatch mini-search tasks (200 tokens or fewer per gap) with results saved as new claim rows and bibliography entries
- Apply outline-specified synthesis protocols and quality standards
- Save synthesis to `BASE_DIR/[TOPIC_SLUG]_Synthesis_Report.md`
- Output format (400 tokens or fewer in chat): `## Coverage Check | ## Integrated Findings (7 bullets or fewer, with IDs + confidence) | ## Conflicts/Confidence | ## Gaps/Follow-ups | ## Files Written`

---

### Phase 4: Draft Reporting

After synthesis completion, deploy the **research-reporting-specialist** with instructions to:

- Reference original research objectives and report specifications from the outline
- Transform synthesized findings into comprehensive professional report
- Create executive summary with key findings and strategic recommendations
- Develop structured content with logical flow and narrative coherence
- Include actionable implementation guidelines and practical applications
- Reporting tone: Professional patent intelligence assessment suitable for IP attorneys, technology transfer officers, and C-suite decision-makers. Precise, evidence-based, and legally informed without constituting legal advice. Use correct patent terminology (claims, specifications, prosecution history, continuations, divisionals, priority dates) but define specialized terms on first use. Write for an audience that understands IP fundamentals but may not be specialists in the specific technology domain. Include appropriate disclaimers that the analysis is informational and does not constitute a legal opinion.
- **CLAIM TAGGING (REQUIRED):** Tag every factual assertion with its claim type: `[VC]` for verifiable claims with cited sources, `[PO]` for professional opinions/analytical judgments, `[IE]` for inferences/extrapolations. Place tags at the end of each claim sentence before the citation. Example: 'Toyota invested $142M in solid-state battery research [VC][^3]'. This tagging is essential for the VVC verification phase.

#### Report Sections

The draft report MUST include these sections in order:

1. Executive Summary
2. Patent Landscape Overview
3. Key Patent Families
4. Claims Analysis
5. Prior Art Assessment
6. Competitive Portfolio Matrix
7. Freedom-to-Operate Assessment
8. Whitespace & Opportunity Analysis
9. IP Risk Matrix
10. Recommendations
11. Methodology
12. Bibliography

#### Citation Requirements

- **USE FOOTNOTES**: Include numbered footnote citations throughout the report: `[^1]`, `[^2]`, etc.
- Place footnotes at end of each major section with full citations and clickable URLs
- Use APA 7th Edition with patent-specific extensions. Patents: Inventor(s), Patent Title, Patent No. XX,XXX,XXX, Filed [date], Granted [date], Assignee: [name]. Applications: Inventor(s), Title, Pub. No. [number], Filed [date], Published [date]. Inline numbered references [1] with full bibliography. Include patent office URLs where available. format throughout
- **BIBLIOGRAPHY CONSOLIDATION**: Create master bibliography file: `BASE_DIR/[TOPIC_SLUG]_Master_Bibliography.md`
- Read all agent bibliography files and consolidate
- Deduplicate using Bibliography Deduplication Rules (below)
- Organize by source type and credibility tier
- Include source attribution (which agent/method found each source)
- Cross-reference footnote numbers with master bibliography entries

#### Reporting Standards

- Include methodology section referencing the original research outline
- Document any deviations from planned research approach
- Add limitations/risks section and "so what" analysis tied to decision impact
- Note any deviations from planned approach identified during synthesis
- Save report to `BASE_DIR/[TOPIC_SLUG]_Draft_Report.md`
- Output format (500 tokens or fewer in chat): `## Executive Brief | ## Key Findings (with IDs + confidence) | ## Recommendations | ## Limitations/Risks | ## Files Written`

---

### Phase 5: VVC-Verify

**Tier behavior:** Quick: skip | Standard: run | Deep: run | Comprehensive: run

After the draft report is complete, deploy the **vvc-specialist** with instructions to:

- **FIRST ACTION**: Read the draft report at `BASE_DIR/[TOPIC_SLUG]_Draft_Report.md`
- Read all bibliography files and the master bibliography at `BASE_DIR/[TOPIC_SLUG]_Master_Bibliography.md`
- **Extract** all `[VC]`-tagged claims with their cited sources and confidence tiers
- **Apply verification scope:** 100% of HIGH confidence [VC] claims, 75% of MEDIUM confidence [VC] claims, 0% of LOW and SPECULATIVE claims
- **For each claim selected for verification:**
  1. Locate the cited source (fetch URL via WebFetch or search for the source)
  2. Extract the relevant quote or data point from the source
  3. Analyze alignment between the claim text and the source content
  4. Classify alignment: CONFIRMED | PARAPHRASED | OVERSTATED | UNDERSTATED | DISPUTED | UNSUPPORTED | SOURCE_UNAVAILABLE
  5. Recommend action: KEEP | REVISE | DOWNGRADE | REMOVE | REPLACE_SOURCE
- **Output:** Save verification report to `BASE_DIR/[TOPIC_SLUG]_VVC_Verification_Report.md`

#### Verification Report Structure

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
| # | Claim Text (truncated) | Source | Confidence | Classification | Recommendation | Notes |
|---|------------------------|--------|------------|----------------|----------------|-------|

### Issues Found
[List of claims requiring correction with details]

### Recommendations
[Prioritized list of corrections to implement in Phase 6]
```

- Output format (400 tokens or fewer in chat): `## Verification Summary | ## Key Issues (with claim refs) | ## Stats | ## Files Written`

**Standard tier:** Stop after Phase 5. The draft report becomes the final report alongside the verification report. Do NOT proceed to Phase 6.

---

### Phase 6: VVC-Correct

**Tier behavior:** Quick: skip | Standard: skip | Deep: run | Comprehensive: run

After verification is complete, deploy the **vvc-specialist** (second pass) with instructions to:

- **FIRST ACTION**: Read the verification report at `BASE_DIR/[TOPIC_SLUG]_VVC_Verification_Report.md`
- Read the draft report at `BASE_DIR/[TOPIC_SLUG]_Draft_Report.md`
- **Implement corrections** for all REVISE/DOWNGRADE/REMOVE/REPLACE_SOURCE recommendations:
  - **REVISE:** Rewrite the claim to accurately reflect the source content
  - **DOWNGRADE:** Lower the confidence tier and add qualifying language
  - **REMOVE:** Delete the claim and adjust surrounding narrative for coherence
  - **REPLACE_SOURCE:** Find and cite a more accurate source for the claim
- **Preserve** all KEEP and CONFIRMED claims unchanged
- **Add Verification Statement** appendix to the final report documenting the VVC process
- **Output:**
  - `BASE_DIR/[TOPIC_SLUG]_Comprehensive_Report.md` (final corrected report)
  - `BASE_DIR/[TOPIC_SLUG]_VVC_Correction_Log.md` (detailed log of all changes made)

#### Correction Log Structure

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

Now executing research deployment...

---

## File Output Structure

Research reports will be saved to:

```
02_KNOWLEDGE/5_RESEARCH_REPORTS/${RUN_TS}_${TOPIC_SLUG}/
├── [TOPIC_SLUG]_Research_Outline.md
├── [TOPIC_SLUG]_Shared_Sources.md
├── [TOPIC_SLUG]_Claims_patent-search-specialist.md
├── [TOPIC_SLUG]_patent-search-specialist_Bibliography.md
├── [TOPIC_SLUG]_Claims_prior-art-analyst.md
├── [TOPIC_SLUG]_prior-art-analyst_Bibliography.md
├── [TOPIC_SLUG]_Claims_ip-landscape-mapper.md
├── [TOPIC_SLUG]_ip-landscape-mapper_Bibliography.md
├── [TOPIC_SLUG]_Methodology_Log.md
├── [TOPIC_SLUG]_Synthesis_Report.md
├── [TOPIC_SLUG]_Draft_Report.md
├── [TOPIC_SLUG]_VVC_Verification_Report.md
├── [TOPIC_SLUG]_VVC_Correction_Log.md            # When tier behavior is 'full'
├── [TOPIC_SLUG]_Comprehensive_Report.md
├── [TOPIC_SLUG]_Citation_Verification_Report.md   # When verification enabled
└── [TOPIC_SLUG]_Master_Bibliography.md
```

File naming follows the convention: {date}_{topic_slug}_patent_intelligence.md

---

## Key Workflow Features

- **Planning agent creates outline first** -- all downstream agents read it as their first action, ensuring coordinated coverage
- **Iterative Search-Assess-Refine loops** prevent one-shot shallow research; each question gets up to 4 refinement passes
- **Cross-agent Shared_Sources.md** prevents duplicate work and maximizes coverage across parallel agents
- **Individual bibliography creation** with fault tolerance -- if one agent fails, other citations are preserved
- **Gap-closing loop after synthesis** (Comprehensive tier) -- targeted follow-up searches for uncovered gaps
- **Methodology logs** record every search query, engine, filter, and assessment for reproducibility
- **Confidence scoring on every claim** using the four-tier framework (HIGH/MEDIUM/LOW/SPECULATIVE)
- **Source credibility hierarchy** enforces evidence quality -- no HIGH confidence claim on Tier 4-5 sources alone
- **Tier-based depth routing** matches research effort to topic complexity
- **Domain specialization** -- all agents operate within Intellectual property and patent landscape analysis context, applying field-specific knowledge and source preferences
- **Structured output standards** ensure consistent, parseable research artifacts across all agents
- **Verification, Validation & Correction (VVC)** -- two-pass post-reporting system that verifies [VC]-tagged claims against cited sources and auto-corrects the draft
- **Claim type taxonomy** -- claims tagged as [VC] (verifiable), [PO] (professional opinion), or [IE] (inferred) to focus verification effort
- **Tier-aware VVC** -- Quick: no VVC, Standard: verify-only, Deep/Comprehensive: full verify+correct

---

## Bibliography & Footnote Standards

### In-Text Citations

- Use numbered footnotes for immediate source reference: `[^1]`, `[^2]`, etc.
- Sequential numbering per document (not per section)
- Place footnote markers immediately after relevant statements
- Example: `According to the report[^1], the market grew at 15% CAGR.`

### Footnote Placement

- Place footnotes at the end of each major section for immediate context
- Use APA 7th Edition with patent-specific extensions. Patents: Inventor(s), Patent Title, Patent No. XX,XXX,XXX, Filed [date], Granted [date], Assignee: [name]. Applications: Inventor(s), Title, Pub. No. [number], Filed [date], Published [date]. Inline numbered references [1] with full bibliography. Include patent office URLs where available. format in footnotes with clickable URLs
- Cross-reference master bibliography when applicable

### Master Bibliography

- All citations follow APA 7th Edition with patent-specific extensions. Patents: Inventor(s), Patent Title, Patent No. XX,XXX,XXX, Filed [date], Granted [date], Assignee: [name]. Applications: Inventor(s), Title, Pub. No. [number], Filed [date], Published [date]. Inline numbered references [1] with full bibliography. Include patent office URLs where available. format with clickable URLs
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

Verify a random sample of HIGH-confidence citations (minimum 3 or 20% of HIGH citations, whichever is greater). Record verification results in Methodology_Log.md.

### Probe on Discovery: true

When probe-on-discovery is enabled, each Phase 2 research agent must:
- Verify source URL resolves (HTTP 200) immediately when found
- If source is unreachable, note in Methodology_Log.md and do NOT use for HIGH confidence claims
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

---

## Context Management Guidelines

Keep each agent's working set lean to maximize effective research within token budgets.

### Token Budgets (approximate)

```
Planning:       2500 tokens output max
Research:       18000 tokens output max (per agent, files + chat)
Synthesis:      12000 tokens output max
Reporting:      12000 tokens output max
VVC:            8000 tokens output max (verification + correction combined)
```

### Context Efficiency Rules

- Always read the outline first; then load only the question-specific files/notes needed
- Use structured outputs (tables, bullet summaries, query logs) instead of long prose to minimize token footprint
- Chunk long-source notes: summarize per source immediately after reading; store extended quotes in per-source appendices if needed
- Use citation IDs (`[W-01]`, `[E-01]`, `[I-01]`) and refer to them instead of repeating full citations
- For long runs, operate in passes: (1) initial sweep + notes, (2) synthesis of top claims/gaps, (3) targeted follow-up on gaps, resetting context to only outline + top notes each pass
- When a document is large, capture a condensed abstract, key data points, and contradictions; keep raw text out of the main context
- Encourage tool-side chunked reading (page/section-level) and avoid reloading full documents once summarized

---

## Domain Preamble

You are conducting patent intelligence analysis to the standard expected by a senior IP attorney or head of technology transfer evaluating patent landscapes for strategic decision-making. Accuracy of patent data is paramount: every patent number, filing date, assignee, and claim reference must be verified against official patent office records. Distinguish between granted patents (enforceable rights) and published applications (potential future rights with claims subject to change). When assessing patent strength, consider claim breadth, prosecution history estoppel, geographic coverage, and remaining patent term. Evaluate not just individual patents but portfolio-level metrics: filing velocity, technology concentration, geographic strategy, and citation influence. Always consider the practical enforceability of patent rights in the relevant jurisdictions.

This preamble applies to all agents in the pipeline. Every research action, source
evaluation, and analytical judgment should be informed by this domain context. Agents
should apply Intellectual property and patent landscape analysis-specific knowledge, terminology, and analytical frameworks
appropriate to this field. All research outputs should be relevant and actionable for
IP attorneys, technology transfer officers, and R&D strategists.

---

## Operational Lessons

Accumulated findings from past research runs using this engine. Update this section after
each research run review or post-mortem analysis.

No entries yet — update after first research run with `/post-mortem`.

When no lessons have been recorded yet, include this placeholder text:
"No entries yet — update after first research run with `/post-mortem`."

---

## Placeholder Reference

This section documents all template variables used in this skill file. When the engine
generator processes this template, each placeholder is replaced with values from the
engine configuration (engine-config.json).

### Engine Metadata
- `{{engineName}}` -- kebab-case plugin name for directory and file naming
- `{{engineDisplayName}}` -- human-readable engine name for display
- `{{engineVersion}}` -- semantic version of the engine configuration
- `{{domain}}` -- short description of the research domain
- `{{audience}}` -- target users for this research engine

### Scope Configuration
- `{{standardTierDescription}}` -- description of standard tier capabilities
- `{{quickTierDescription}}` -- description of quick tier capabilities
- `{{deepTierDescription}}` -- description of deep tier capabilities
- `{{comprehensiveTierDescription}}` -- description of comprehensive tier capabilities

### Source Strategy
- `{{tier1Name}}` / `{{tier1Sources}}` -- Tier 1 credibility definition
- `{{tier2Name}}` / `{{tier2Sources}}` -- Tier 2 credibility definition
- `{{tier3Name}}` / `{{tier3Sources}}` -- Tier 3 credibility definition
- `{{tier4Name}}` / `{{tier4Sources}}` -- Tier 4 credibility definition
- `{{tier5Name}}` / `{{tier5Sources}}` -- Tier 5 credibility definition
- `{{additionalSearchTemplates}}` -- domain-specific search query templates
- `{{preferredSites}}` -- prioritized domains for web searches

### Agent Pipeline
- `{{tierConfigTable}}` -- markdown table of tier configurations
- `{{quickAgentId}}` -- agent ID used for the quick tier
- `{{agentDeploymentBlocks}}` -- per-agent deployment instructions
- `{{subAgentList}}` -- list of available sub-agent types
- `{{agentSpecialization}}` -- domain-specific agent focus areas

### Quality Framework
- `{{confidenceHigh}}` -- criteria for HIGH confidence scoring
- `{{confidenceMedium}}` -- criteria for MEDIUM confidence scoring
- `{{confidenceLow}}` -- criteria for LOW confidence scoring
- `{{confidenceSpeculative}}` -- criteria for SPECULATIVE confidence scoring
- `{{minimumEvidence}}` -- minimum evidence threshold for claim inclusion
- `{{validationRules}}` -- validation rules applied during synthesis
- `{{citationStandard}}` -- citation format and referencing style

### Output Structure
- `{{reportSections}}` -- ordered list of report section headings
- `{{fileStructure}}` -- per-agent file output entries
- `{{fileNaming}}` -- file naming convention template

### Prompts
- `{{globalPreamble}}` -- domain-wide context prepended to all agent prompts
- `{{synthesisInstructions}}` -- additional instructions for the synthesis agent
- `{{reportingTone}}` -- desired tone and style for the final report

### Advanced Configuration
- `{{maxIterations}}` -- maximum research-refine cycles per question
- `{{explorationDepth}}` -- maximum depth for recursive web exploration from seed URLs
- `{{planningBudget}}` -- token budget for planning phase
- `{{researchBudget}}` -- token budget for research phase (per agent)
- `{{synthesisBudget}}` -- token budget for synthesis phase
- `{{reportingBudget}}` -- token budget for reporting phase

### Citation Management
- `{{verificationMode}}` -- source verification depth (none, spot-check, comprehensive)
- `{{verificationModeInstructions}}` -- expanded instructions for the selected verification mode
- `{{urlLivenessCheck}}` -- whether to verify URL resolution
- `{{contentClaimMatching}}` -- whether to verify claims match source content
- `{{sourceFreshnessThreshold}}` -- age threshold for flagging stale sources
- `{{deadLinkHandling}}` -- how to handle dead/unreachable URLs
- `{{deadLinkInstructions}}` -- expanded instructions for the selected dead link strategy
- `{{probeOnDiscovery}}` -- whether to verify sources immediately when found
- `{{verificationReportConfig}}` -- verification report generation instructions

### Operational
- `{{operationalLessons}}` -- accumulated post-mortem findings from past research runs
