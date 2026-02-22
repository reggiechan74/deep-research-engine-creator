---
name: Patent Intelligence Research Engine
description: >-
  This skill should be used when the user invokes the /research command or asks about
  intellectual property and patent landscape analysis. It provides a complete multi-agent
  research pipeline specialized for patent research.
version: 1.0.0
---

# Patent Intelligence Research Engine

Launch a comprehensive multi-agent research system specialized for **intellectual property
and patent landscape analysis** research, serving **IP attorneys, technology transfer
officers, and R&D strategists**.

This engine implements a four-phase research pipeline with tier-based depth routing. It is
fully self-contained -- no external research plugin dependencies are required. All protocols,
agent definitions, quality standards, and output specifications are defined in this file.

## Usage

- `/research [topic]` -- Standard tier (default): multi-agent pipeline with patent search + prior art analysis
- `/research [topic] --quick` -- Quick tier: fast patent lookup with single specialist agent
- `/research [topic] --deep` -- Deep tier: full 3-agent pipeline including IP landscape mapping
- `/research [topic] --comprehensive` -- Comprehensive tier: deep + follow-up rounds for gap closure
- `/research [topic] --outline-only` -- Planning phase only (produces outline, then stops)
- `/research [topic] --approve` -- Pause for user approval after Phase 1 before proceeding

---

## Research Architecture

This engine implements a **four-phase research system** with tier-based depth routing:

1. **Phase 0: Tier Detection** -- Parse flags, configure paths and depth
2. **Phase 1: Research Planning** -- Strategic framework development and agent task design
3. **Phase 2: Parallel Research** -- Multiple specialist agents research simultaneously with iterative refinement
4. **Phase 3: Synthesis** -- Multi-source integration, contradiction resolution, and gap analysis
5. **Phase 4: Professional Reporting** -- Comprehensive report generation with consolidated bibliography

### Tier Configuration

| Tier | Planning | Research Agents | Synthesis | Report | User Gate |
|------|----------|----------------|-----------|--------|-----------|
| Quick | No | patent-search-specialist only | No | Inline | No |
| Standard | Yes | patent-search-specialist, prior-art-analyst | Yes | Full | --approve only |
| Deep | Yes | patent-search-specialist, prior-art-analyst, ip-landscape-mapper | Yes | Full | --approve only |
| Comprehensive | Yes | All 3 agents + follow-up round | Yes | Full | Always |

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
HIGH        (3/3): Verified against official patent office databases (USPTO, EPO, WIPO). Patent numbers confirmed as valid with current status checked. Claim analysis based on actual claim text from granted patents. Multiple authoritative sources agree on assignee, dates, and classification.
MEDIUM      (2/3): Supported by patent analytics platforms or secondary patent databases, corroborated by at least 1 official patent office source. Patent family connections inferred from priority claims and verified where possible. Claim scope assessments are consistent with prosecution history.
LOW         (1/3): Based on a single commercial patent database, industry report, or news source without verification against official patent office records. Patent status may not be current. Claim analysis based on abstracts rather than full claim text.
SPECULATIVE (0/3): Based on published patent applications (not yet granted), roadmap announcements of IP strategy, or extrapolation from filing trends. Represents projected IP positions rather than confirmed rights. Includes freedom-to-operate assessments based on pending claims that may change during prosecution.
```

**Rule:** Every claim in claims tables MUST include a confidence tier. All HIGH-impact
claims MUST be HIGH confidence or explicitly flagged as exceptions. All patent claims require patent number verification against at least one official patent office database (USPTO, EPO, WIPO). Patent status (active, expired, abandoned, pending) must be confirmed. Claim scope assessments require reference to actual claim text. FTO conclusions require identification of specific patent claims and their relationship to the subject technology.

### Source Credibility Hierarchy

```
Tier 1 (Official Patent Databases):     USPTO PATFT/AppFT (patents.google.com, patft.uspto.gov), EPO Espacenet and Global Patent Index, WIPO PATENTSCOPE and PCT publications, Google Patents with full-text search and classification browsing, National patent office databases (JPO J-PlatPat, KIPO KIPRIS, CNIPA, CIPO)
Tier 2 (Patent Analytics & Legal):      Patent prosecution histories (USPTO PAIR, EPO Register), Patent litigation databases (PACER, Docket Navigator, Lex Machina), Published patent examiner search reports and office actions, PTAB decisions and inter partes review proceedings, Patent classification systems (CPC, IPC) official documentation
Tier 3 (Technical & Scientific):        Peer-reviewed technical journals related to the patent domain, Conference proceedings from major technical conferences, Standards body publications (IEEE, ISO, ASTM) relevant to patent claims, Published doctoral dissertations and technical reports, ArXiv preprints and academic working papers with disclosed methodology
Tier 4 (Industry & Commercial):         Patent analytics platform reports (PatSnap, Orbit Intelligence, Innography), Industry news and trade publications covering patent activity, Company press releases and investor presentations mentioning IP, Technology blog posts from recognized patent attorneys and IP professionals, Patent valuation and licensing market reports
Tier 5 (Unreliable / Unverified):       Anonymous forum posts and unattributed patent commentary, Marketing materials claiming patent-pending status without application numbers, AI-generated patent summaries without verification against original filings, Unverified patent ownership claims on company websites, Social media discussions about patent disputes without case citations
```

**Rule:** No HIGH confidence claim can rest solely on Tier 4-5 sources. At minimum,
one Tier 1-3 source is required for any HIGH confidence assertion.

### Citation & Evidence Standards

- **Citation format:** APA 7th Edition with patent-specific extensions. Patents: Inventor(s), Patent Title, Patent No. XX,XXX,XXX, Filed [date], Granted [date], Assignee: [name]. Applications: Inventor(s), Title, Pub. No. [number], Filed [date], Published [date]. Inline numbered references [1] with full bibliography. Include patent office URLs where available.
- Use numbered footnotes `[^1]`, `[^2]`, etc. for inline source references
- Use citation IDs by agent type: `[PS-01]` (patent search), `[PA-01]` (prior art), `[IL-01]` (IP landscape)
- Master bibliography maps IDs to full citations with clickable URLs
- Do not repeat full citations in chat; use IDs and defer to bibliography files
- **Evidence rules:** No high-impact claim without 2+ independent sources, or mark as LOW confidence
- **Adversarial sweep:** Always look for patent invalidation arguments, prosecution history estoppel, expired coverage, and contradictory data
- Log contradictions in methodology file

### Validation Rules

- Verify all patent numbers against official patent office databases (USPTO PATFT/AppFT, EPO Espacenet, WIPO PATENTSCOPE) and confirm current legal status.
- Confirm patent assignee information is current by checking assignment records -- patents may have been transferred, licensed, or sold.
- Distinguish between granted patents and pending applications when assessing IP strength and enforceability.
- Validate CPC and IPC classification codes against official classification schemes to ensure accuracy of landscape mapping.
- Cross-check patent family connections using priority claim data from multiple patent offices.
- Verify that cited prior art references are actually relevant to the claims under analysis, not just topically related.
- Flag any patent status data older than 6 months as potentially outdated -- maintenance fees, assignments, and litigation may have changed status.
- Assess patent term calculations considering any patent term adjustments (PTA) or terminal disclaimers.
- Confirm that freedom-to-operate assessments reference specific claim elements, not just patent titles or abstracts.

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

1. **Direct query** -- Core patent terminology, technology keywords, and patent numbers
2. **Synonym variant** -- Alternative technical terms, CPC/IPC classification codes, regional naming conventions
3. **Adversarial** -- "patent invalidation [X]", "prior art [X]", "[X] patent challenge", "[X] patent expired"
4. **Expert-source targeted** -- `site:` filters for preferred authoritative domains

### Preferred Sites for Targeted Queries

- `patents.google.com` -- Google Patents (full-text search, classification browsing, family links)
- `patft.uspto.gov` -- USPTO granted patents full-text database
- `appft.uspto.gov` -- USPTO published applications full-text database
- `worldwide.espacenet.com` -- EPO Espacenet worldwide patent search
- `patentscope.wipo.int` -- WIPO PATENTSCOPE international patent search
- `epo.org` -- European Patent Office official site and register
- `scholar.google.com` -- Google Scholar for non-patent literature and prior art
- `lens.org` -- The Lens open patent and scholarly search
- `ipo.gov.uk` -- UK Intellectual Property Office
- `cipo.ic.gc.ca` -- Canadian Intellectual Property Office

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
office-specific databases as the topic demands. All queries must be logged to
`BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md` with timestamps and result counts.

---

## Iterative Search-Assess-Refine Protocol

Each Phase 2 agent follows this protocol for each assigned research question:

```
For each assigned research question:

  Pass 1 -- SEARCH: Execute diversified query set (4+ queries per question)
    - Apply Search Query Generation Protocol
    - Cast wide net across patent databases and source types
    - Record all queries and results in Methodology_Log.md

  Pass 2 -- ASSESS: Evaluate sufficiency
    - Are there 2+ independent sources for key patent claims?
    - Are there unanswered sub-questions (missing jurisdictions, unchecked assignees)?
    - Are there contradictions needing resolution (conflicting assignee data, status discrepancies)?
    - Score current evidence against Confidence Scoring Framework

  Pass 3 -- REFINE (if gaps found):
    - Generate targeted follow-up queries addressing specific gaps
    - Try alternative classification codes, different patent offices, or date-range adjustments
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
- Patent number verification fails    --> Flag patent as UNVERIFIED; do not assign HIGH confidence
- User reports factual error          --> Trigger targeted verification mini-search against official patent office
```

---

## Sub-Agent System

The Patent Intelligence Engine research system uses these available sub-agents:

- **research-planning-specialist** (general-purpose) -- Creates systematic research frameworks, decomposes complex patent research questions into agent-specific tasks, and designs the research outline that all downstream agents follow.
- **patent-search-specialist** (general-purpose, sonnet) -- Conducts comprehensive patent searches across major patent offices using classification codes, keyword strategies, and assignee tracking. Extracts patent data, maps patent families, and tracks prosecution histories.
- **prior-art-analyst** (expert-instructor, sonnet) -- Analyzes patent claims for novelty and non-obviousness against the prior art landscape using TSM and KSR frameworks. Maps prior art references to specific claim elements.
- **ip-landscape-mapper** (intelligence-analyst, sonnet) -- Maps patent portfolios by assignee, analyzes filing trends, builds competitive matrices, identifies whitespace opportunities, and assesses freedom-to-operate risks.
- **synthesis-specialist** (general-purpose) -- Integrates findings from all research agents, resolves contradictions, scores confidence levels, and builds a unified patent intelligence picture.
- **research-reporting-specialist** (general-purpose) -- Transforms synthesized findings into professional patent intelligence reports with proper structure, citations, and actionable recommendations.

Each sub-agent type provides different capabilities matched to its pipeline role. The
planning and synthesis specialists are fixed roles; research agents are domain-specialized
instances configured for this engine's specific focus areas.

---

## Execution Strategy -- Quick Tier

If `--quick` detected, deploy a SINGLE agent (**patent-search-specialist**) with the following
instructions:

**Domain:** Intellectual property and patent landscape analysis

**Instructions:**
- Conduct focused patent search on the topic using official patent databases
- Apply Search Query Generation Protocol (minimum 4 query types per question)
- Apply Iterative Search-Assess-Refine Protocol (max 2 iterations)
- Apply Global Standards for evidence quality and confidence scoring
- Include confidence tier (HIGH/MEDIUM/LOW/SPECULATIVE) for every claim
- Note source credibility tier (1-5) for each source used
- For each key patent found, extract: patent number, title, assignee, filing date, grant date, status
- Produce inline summary directly in chat response (no file output structure needed)
- Format: `## Summary | ## Key Patents Found (with confidence) | ## Sources | ## Limitations`

After deploying the quick agent, skip all remaining phases.

---

## Execution Strategy -- Standard / Deep / Comprehensive Tiers

### Phase 1: Strategic Research Planning

Deploy **research-planning-specialist** with instructions to:

- Analyze patent research topic complexity, scope, and jurisdictional requirements
- Create systematic research framework mapping key investigation areas
- Build scope grid:
  - Core research questions (landscape, prior art, FTO, competitive)
  - Sub-questions and hypotheses about patent ownership, validity, and scope
  - Dissenting angles and potential invalidity arguments
  - Geographic slices (which jurisdictions to prioritize) and temporal boundaries
- Identify optimal patent databases, classification codes, and investigation methods
- Rank sources: primary patent office databases > analytics platforms > industry reports per the Source Credibility Hierarchy
- Design specific task assignments for downstream agents by research question, jurisdiction, and technology sub-area to reduce overlap
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

#### Agent: patent-search-specialist

Deploy **patent-search-specialist** as a Task sub-agent with the following instructions:

**Role:** Patent Search Specialist
**Model:** sonnet
**Sub-agent type:** general-purpose

**Instructions:**
- **FIRST ACTION**: Read `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md` AND `BASE_DIR/[TOPIC_SLUG]_Shared_Sources.md` (create Shared_Sources.md if it does not exist)
- Follow assigned research domains and methodologies from the outline
- Conduct comprehensive patent searches across USPTO, EPO, WIPO, and other relevant patent offices
- Use CPC/IPC classification codes, keyword strategies, and assignee tracking to identify relevant patents
- For each key patent, document: patent number, title, abstract summary, filing date, grant date, current assignee, independent claim count, total claim count, CPC/IPC classifications, and forward citation count
- Identify patent families by tracing priority claims across jurisdictions
- Track prosecution history for key patents to assess claim scope evolution and examiner rejections
- Apply Search Query Generation Protocol (minimum 4 query types per research question)
- Apply Iterative Search-Assess-Refine Protocol (max 4 iterations per question)
- Append high-value sources to `Shared_Sources.md` as discovered
- Include confidence tier (HIGH/MEDIUM/LOW/SPECULATIVE) for every claim
- Note source credibility tier (1-5) for each source used
- Save bibliography file: `BASE_DIR/[TOPIC_SLUG]_patent-search-specialist_Bibliography.md`
- Save claims table: `BASE_DIR/[TOPIC_SLUG]_Claims_patent-search-specialist.md`
- Log all search iterations to `BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md`
- Apply Global Standards and outline quality standards
- Output format (450 tokens or fewer in chat): `## Focus | ## Top Findings (7 bullets or fewer, with IDs + confidence) | ## Gaps/Next | ## Files Written`

#### Agent: prior-art-analyst

Deploy **prior-art-analyst** as a Task sub-agent with the following instructions (Standard tier and above):

**Role:** Prior Art Analyst
**Model:** sonnet
**Sub-agent type:** expert-instructor

**Instructions:**
- **FIRST ACTION**: Read `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md` AND `BASE_DIR/[TOPIC_SLUG]_Shared_Sources.md` (create Shared_Sources.md if it does not exist)
- Follow assigned research domains and methodologies from the outline
- Build comprehensive prior art maps including patent prior art, non-patent literature, and commercial prior art
- Apply TSM (Teaching-Suggestion-Motivation) test and KSR v. Teleflex obviousness framework for patentability assessments
- Review prosecution histories to understand claim scope evolution and examiner objections
- Document claim-by-claim mapping between subject patents and identified prior art
- Assess claim construction and identify potential invalidity arguments
- Apply Search Query Generation Protocol (minimum 4 query types per research question)
- Apply Iterative Search-Assess-Refine Protocol (max 4 iterations per question)
- Append high-value sources to `Shared_Sources.md` as discovered
- Include confidence tier (HIGH/MEDIUM/LOW/SPECULATIVE) for every claim
- Note source credibility tier (1-5) for each source used
- Save bibliography file: `BASE_DIR/[TOPIC_SLUG]_prior-art-analyst_Bibliography.md`
- Save claims table: `BASE_DIR/[TOPIC_SLUG]_Claims_prior-art-analyst.md`
- Log all search iterations to `BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md`
- Apply Global Standards and outline quality standards
- Output format (450 tokens or fewer in chat): `## Focus | ## Top Findings (7 bullets or fewer, with IDs + confidence) | ## Gaps/Next | ## Files Written`

#### Agent: ip-landscape-mapper

Deploy **ip-landscape-mapper** as a Task sub-agent with the following instructions (Deep tier and above):

**Role:** IP Landscape Mapper
**Model:** sonnet
**Sub-agent type:** intelligence-analyst

**Instructions:**
- **FIRST ACTION**: Read `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md` AND `BASE_DIR/[TOPIC_SLUG]_Shared_Sources.md` (create Shared_Sources.md if it does not exist)
- Follow assigned research domains and methodologies from the outline
- Map patent portfolios by assignee, filing trends over time, geographic distribution, and technology clusters
- Build competitive portfolio matrices comparing key players across portfolio size, claim breadth, geographic spread, remaining patent life, and citation impact
- Identify whitespace opportunities in CPC/IPC classification space where filing density is low
- Assess freedom-to-operate risks by mapping potentially blocking patent claims against the subject technology
- Create filing trend timelines and assignee ranking tables
- Apply Search Query Generation Protocol (minimum 4 query types per research question)
- Apply Iterative Search-Assess-Refine Protocol (max 4 iterations per question)
- Append high-value sources to `Shared_Sources.md` as discovered
- Include confidence tier (HIGH/MEDIUM/LOW/SPECULATIVE) for every claim
- Note source credibility tier (1-5) for each source used
- Save bibliography file: `BASE_DIR/[TOPIC_SLUG]_ip-landscape-mapper_Bibliography.md`
- Save claims table: `BASE_DIR/[TOPIC_SLUG]_Claims_ip-landscape-mapper.md`
- Log all search iterations to `BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md`
- Apply Global Standards and outline quality standards
- Output format (450 tokens or fewer in chat): `## Focus | ## Top Findings (7 bullets or fewer, with IDs + confidence) | ## Gaps/Next | ## Files Written`

#### Common Agent Requirements

Every Phase 2 research agent MUST:

1. **FIRST ACTION**: Read `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md` AND `BASE_DIR/[TOPIC_SLUG]_Shared_Sources.md` (create Shared_Sources.md if it does not exist)
2. Follow assigned research domains and methodologies from the outline
3. Apply Search Query Generation Protocol (minimum 4 query types per research question)
4. Apply Iterative Search-Assess-Refine Protocol (max 4 iterations per question)
5. Append high-value sources to `Shared_Sources.md` as discovered
6. Apply domain-specific focus: patent data extraction, prior art mapping, landscape analysis, and FTO risk assessment as assigned
7. Include confidence tier (HIGH/MEDIUM/LOW/SPECULATIVE) for every claim
8. Note source credibility tier (1-5) for each source used
9. Save bibliography file: `BASE_DIR/[TOPIC_SLUG]_[AgentID]_Bibliography.md`
10. Save claims table: `BASE_DIR/[TOPIC_SLUG]_Claims_[AgentID].md`
11. Log all search iterations to `BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md`
12. Apply Global Standards and outline quality standards
13. Output format (450 tokens or fewer in chat): `## Focus | ## Top Findings (7 bullets or fewer, with IDs + confidence) | ## Gaps/Next | ## Files Written`

---

### Phase 3: Research Synthesis

After all Phase 2 research agents complete, deploy the **synthesis-specialist** with
instructions to:

- **FIRST ACTION**: Read the research outline file `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md`
- Compare planned research coverage against actual research execution
- Read ALL agent output files: results, claims tables, bibliographies, shared sources
- Integrate findings from all research agents into coherent patent intelligence framework
- Cross-reference patent data across agents: verify patent numbers, assignees, dates, and status are consistent
- Mark claims with confidence scores using the Confidence Scoring Framework
- Resolve contradictions and inconsistencies in research findings (conflicting assignee data, status discrepancies, different claim counts)
- Generate meta-insights and higher-level implications for IP strategy
- Create unified understanding from fragmented information streams
- Note gaps between planned and executed research for the reporting agent
- Structure the analysis to support strategic IP decisions. Lead with the patent landscape overview showing the competitive environment. Present filing trend data with clear temporal patterns. Build competitive matrices that enable side-by-side portfolio comparison. For FTO assessments, clearly map the relationship between identified patent claims and the subject technology, using a risk-rating system (High/Medium/Low) for each potentially blocking patent. Quantify IP risks where possible: number of potentially blocking patents, years of remaining patent life, geographic coverage gaps, and litigation history of key patent holders. Identify actionable whitespace opportunities with supporting evidence from the landscape analysis.
- **Comprehensive tier only:** Propose targeted follow-up searches for uncovered gaps and dispatch mini-search tasks (200 tokens or fewer per gap) with results saved as new claim rows and bibliography entries
- Apply outline-specified synthesis protocols and quality standards
- Save synthesis to `BASE_DIR/[TOPIC_SLUG]_Synthesis_Report.md`
- Output format (400 tokens or fewer in chat): `## Coverage Check | ## Integrated Findings (7 bullets or fewer, with IDs + confidence) | ## Conflicts/Confidence | ## Gaps/Follow-ups | ## Files Written`

---

### Phase 4: Professional Reporting

After synthesis completion, deploy the **research-reporting-specialist** with instructions to:

- Reference original research objectives and report specifications from the outline
- Transform synthesized findings into comprehensive professional patent intelligence report
- Create executive summary with key findings and strategic recommendations
- Develop structured content with logical flow and narrative coherence
- Include actionable implementation guidelines and practical applications
- Reporting tone: Professional patent intelligence assessment suitable for IP attorneys, technology transfer officers, and C-suite decision-makers. Precise, evidence-based, and legally informed without constituting legal advice. Use correct patent terminology (claims, specifications, prosecution history, continuations, divisionals, priority dates) but define specialized terms on first use. Write for an audience that understands IP fundamentals but may not be specialists in the specific technology domain. Include appropriate disclaimers that the analysis is informational and does not constitute a legal opinion.

#### Report Sections

The final report MUST include these sections in order:

1. **Executive Summary** -- Key findings, strategic implications, and top-level recommendations in 500 words or fewer
2. **Patent Landscape Overview** -- Technology domain definition, scope of analysis, filing trend summary, key statistics
3. **Key Patent Families** -- Detailed analysis of the most significant patent families including claims, assignees, geographic coverage, and citation impact
4. **Claims Analysis** -- Independent claim mapping, claim breadth assessment, prosecution history highlights, and claim scope evolution
5. **Prior Art Assessment** -- Prior art landscape summary, key references identified, TSM/KSR analysis results, and patentability opinions
6. **Competitive Portfolio Matrix** -- Side-by-side comparison of key assignee portfolios across standard dimensions (size, breadth, geography, remaining life, citations)
7. **Freedom-to-Operate Assessment** -- Identified blocking patents, risk ratings (High/Medium/Low/Clear), claim-to-technology mapping, and recommended mitigation strategies
8. **Whitespace & Opportunity Analysis** -- Under-patented technology segments, geographic gaps, expiring foundational patents, and strategic filing recommendations
9. **IP Risk Matrix** -- Consolidated risk assessment table with likelihood, impact, and recommended actions for each identified IP risk
10. **Recommendations** -- Prioritized strategic recommendations for IP decision-makers, organized by timeframe (immediate, short-term, long-term)
11. **Methodology** -- Research approach, databases searched, classification codes used, agent pipeline description, and limitations
12. **Bibliography** -- Consolidated master bibliography with patent-specific citations and clickable URLs

#### Citation Requirements

- **USE FOOTNOTES**: Include numbered footnote citations throughout the report: `[^1]`, `[^2]`, etc.
- Place footnotes at end of each major section with full citations and clickable URLs
- Use APA 7th Edition with patent-specific extensions format throughout
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
- Include disclaimer: "This patent intelligence report is provided for informational purposes only and does not constitute legal advice. Consult with a registered patent attorney for formal legal opinions on patentability, validity, or freedom-to-operate."
- Save report to `BASE_DIR/[TOPIC_SLUG]_Comprehensive_Report.md`
- Output format (500 tokens or fewer in chat): `## Executive Brief | ## Key Findings (with IDs + confidence) | ## Recommendations | ## Limitations/Risks | ## Files Written`

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
├── [TOPIC_SLUG]_Comprehensive_Report.md
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
- **Domain specialization** -- all agents operate within patent intelligence context, applying IP-specific knowledge and source preferences
- **Structured output standards** ensure consistent, parseable research artifacts across all agents
- **Patent-specific validation** -- patent numbers verified against official databases, status confirmed, claim text referenced

---

## Bibliography & Footnote Standards

### In-Text Citations

- Use numbered footnotes for immediate source reference: `[^1]`, `[^2]`, etc.
- Sequential numbering per document (not per section)
- Place footnote markers immediately after relevant statements
- Example: `Samsung SDI holds 47 granted patents in solid-state electrolyte compositions[^1].`

### Patent-Specific Citation Format

- **Granted patents**: Inventor(s), Patent Title, Patent No. XX,XXX,XXX, Filed [date], Granted [date], Assignee: [name].
- **Published applications**: Inventor(s), Title, Pub. No. [number], Filed [date], Published [date].
- **PCT applications**: Inventor(s), Title, WO [number], Filed [date], Published [date], Designated States.
- Example: `Smith, J., & Lee, K., Solid-State Electrolyte Composition, U.S. Patent No. 11,234,567, Filed Jan. 15, 2020, Granted Mar. 1, 2022, Assignee: Samsung SDI Co., Ltd.`

### Footnote Placement

- Place footnotes at the end of each major section for immediate context
- Use APA 7th Edition with patent-specific extensions format in footnotes with clickable URLs
- Cross-reference master bibliography when applicable

### Master Bibliography

- All citations follow APA 7th Edition with patent-specific extensions format with clickable URLs
- Include complete source information with access dates
- Organize by source type: (1) Granted Patents, (2) Published Applications, (3) Patent Analytics, (4) Technical Literature, (5) Other Sources
- Secondary organization by credibility tier within each source type
- Cross-reference footnote numbers where sources appear in reports
- Include source attribution indicating which agent discovered each source

### Bibliography Deduplication Rules

- Same URL --> merge, keep earliest discovery timestamp
- Same patent number from different databases --> merge, prefer official patent office source
- Same content, different URLs --> note both, mark canonical (prefer official patent office)
- Different editions/versions --> keep most recent unless historical context needed
- Conflicting information from same source --> note both dates and what changed

---

## Context Management Guidelines

Keep each agent's working set lean to maximize effective research within token budgets.

### Token Budgets (approximate)

```
Planning:       2500 tokens output max
Research:       18000 tokens output max (per agent, files + chat)
Synthesis:      12000 tokens output max
Reporting:      12000 tokens output max
```

### Context Efficiency Rules

- Always read the outline first; then load only the question-specific files/notes needed
- Use structured outputs (tables, bullet summaries, query logs) instead of long prose to minimize token footprint
- Chunk long-source notes: summarize per source immediately after reading; store extended quotes in per-source appendices if needed
- Use citation IDs (`[PS-01]`, `[PA-01]`, `[IL-01]`) and refer to them instead of repeating full citations
- For long runs, operate in passes: (1) initial sweep + notes, (2) synthesis of top claims/gaps, (3) targeted follow-up on gaps, resetting context to only outline + top notes each pass
- When a patent document is large, capture a condensed abstract, key claims, and classification codes; keep raw text out of the main context
- Encourage tool-side chunked reading (page/section-level) and avoid reloading full documents once summarized

---

## Domain Preamble

You are conducting patent intelligence analysis to the standard expected by a senior IP attorney or head of technology transfer evaluating patent landscapes for strategic decision-making. Accuracy of patent data is paramount: every patent number, filing date, assignee, and claim reference must be verified against official patent office records. Distinguish between granted patents (enforceable rights) and published applications (potential future rights with claims subject to change). When assessing patent strength, consider claim breadth, prosecution history estoppel, geographic coverage, and remaining patent term. Evaluate not just individual patents but portfolio-level metrics: filing velocity, technology concentration, geographic strategy, and citation influence. Always consider the practical enforceability of patent rights in the relevant jurisdictions.

This preamble applies to all agents in the pipeline. Every research action, source
evaluation, and analytical judgment should be informed by this domain context. Agents
should apply intellectual property and patent landscape analysis-specific knowledge,
terminology, and analytical frameworks appropriate to this field. All research outputs
should be relevant and actionable for IP attorneys, technology transfer officers, and
R&D strategists.
