# Patent Intelligence Engine

A domain-specialized deep-research engine for intellectual property and patent landscape analysis. Built with the [Deep Research Engine Creator](../../), this engine generates comprehensive patent research reports with prior art analysis, IP landscape mapping, and freedom-to-operate assessments.

## What It Does

The Patent Intelligence Engine provides a complete multi-agent research pipeline specialized for patent research. It supports:

- **Patent Landscape Analysis** -- Map filing trends, top assignees, geographic distribution, and technology clusters across major patent offices (USPTO, EPO, WIPO, JPO, KIPO, CNIPA, CIPO)
- **Prior Art Search** -- Systematic identification of relevant prior art including patents, published applications, technical papers, and commercial products, with TSM/KSR framework analysis
- **Freedom-to-Operate Assessment** -- Identify potentially blocking patents, map claim-to-technology relationships, and rate FTO risks (High/Medium/Low/Clear)
- **Competitive Portfolio Analysis** -- Side-by-side comparison of assignee portfolios across dimensions: size, claim breadth, geographic spread, remaining patent life, and citation impact
- **Technology Trend Mapping** -- Filing velocity analysis, technology lifecycle positioning, and whitespace identification in CPC/IPC classification space

## Installation

Copy or symlink this directory into your Claude Code plugins location:

```bash
# Option 1: Copy the entire engine
cp -r patent-intelligence-engine/ /path/to/your/project/.claude/plugins/patent-intelligence-engine/

# Option 2: Symlink (recommended for development)
ln -s /absolute/path/to/patent-intelligence-engine /path/to/your/project/.claude/plugins/patent-intelligence-engine
```

The engine is self-contained -- no external research plugin dependencies are required.

## Usage

### Research Command

```
/research solid-state battery technology
/research solid-state battery technology --quick
/research solid-state battery technology --deep
/research solid-state battery technology --comprehensive
/research solid-state battery technology --approve
/research solid-state battery technology --outline-only
```

### Tier Depths

| Tier | Planning | Research Agents | Synthesis | Report | User Gate |
|------|----------|----------------|-----------|--------|-----------|
| Quick | No | patent-search-specialist only | No | Inline | No |
| Standard | Yes | patent-search-specialist, prior-art-analyst | Yes | Full | --approve only |
| Deep | Yes | patent-search-specialist, prior-art-analyst, ip-landscape-mapper | Yes | Full | --approve only |
| Comprehensive | Yes | All 3 agents + follow-up round | Yes | Full | Always |

### Sources Command

```
/sources
```

Displays the configured source credibility hierarchy, preferred sites, excluded sources, and search templates.

## Agents

### Patent Search Specialist

Primary patent database researcher. Searches across USPTO, EPO, WIPO, and other major patent offices using CPC/IPC classification codes, keyword strategies, and assignee tracking. Extracts patent data (numbers, dates, assignees, claims, classifications, citations), maps patent families by tracing priority claims, and tracks prosecution histories.

- **Model:** sonnet
- **Color:** blue
- **Citation prefix:** `[PS-01]`, `[PS-02]`, ...

### Prior Art Analyst

Analyzes patent claims for novelty and non-obviousness against the prior art landscape. Applies the Teaching-Suggestion-Motivation (TSM) test and KSR v. Teleflex obviousness framework. Reviews prosecution histories, performs claim-by-claim mapping between subject patents and identified prior art, and assesses claim construction.

- **Model:** sonnet
- **Color:** magenta
- **Citation prefix:** `[PA-01]`, `[PA-02]`, ...

### IP Landscape Mapper

Synthesizes patent data into comprehensive IP landscape assessments. Maps patent portfolios by assignee, analyzes filing trends over time, builds competitive portfolio matrices, identifies whitespace opportunities in CPC/IPC classification space, and assesses freedom-to-operate risks by mapping potentially blocking patent claims.

- **Model:** sonnet
- **Color:** yellow
- **Citation prefix:** `[IL-01]`, `[IL-02]`, ...

## Source Hierarchy

| Tier | Name | Key Sources |
|------|------|-------------|
| 1 | Official Patent Databases | USPTO PATFT/AppFT, EPO Espacenet, WIPO PATENTSCOPE, Google Patents, National offices (JPO, KIPO, CNIPA, CIPO) |
| 2 | Patent Analytics & Legal | Prosecution histories (USPTO PAIR, EPO Register), PTAB decisions, Patent litigation databases, CPC/IPC documentation |
| 3 | Technical & Scientific | Peer-reviewed journals, Conference proceedings, Standards body publications (IEEE, ISO, ASTM), ArXiv preprints |
| 4 | Industry & Commercial | Patent analytics platforms (PatSnap, Orbit), Trade publications, Company press releases, IP professional blogs |
| 5 | Unreliable / Unverified | Anonymous forums, Unverified patent-pending claims, AI-generated summaries, Social media patent discussions |

**Rule:** No HIGH confidence claim can rest solely on Tier 4-5 sources.

## Sample Questions

- What is the patent landscape for solid-state battery technology?
- Who are the top filers in autonomous vehicle LiDAR patents since 2020?
- Are there freedom-to-operate risks for our graphene-based electrode invention?
- What patent trends exist in CRISPR gene editing therapeutics?
- Map the IP portfolio of Tesla vs BYD in battery technology

## Quality Framework

### Confidence Scoring

| Level | Symbol | Criteria |
|-------|--------|----------|
| HIGH | (3/3) | Verified against official patent office databases. Patent numbers confirmed with current status. Claim analysis based on actual claim text from granted patents. |
| MEDIUM | (2/3) | Supported by patent analytics platforms, corroborated by at least 1 official source. Patent family connections verified where possible. |
| LOW | (1/3) | Based on a single commercial database or news source without official verification. Patent status may not be current. |
| SPECULATIVE | (0/3) | Based on published applications (not yet granted), roadmap announcements, or filing trend extrapolation. |

### Validation Rules

- Verify all patent numbers against official patent office databases and confirm current legal status
- Confirm patent assignee information is current (patents may have been transferred or sold)
- Distinguish between granted patents and pending applications when assessing IP strength
- Validate CPC/IPC classification codes against official schemes
- Cross-check patent family connections using priority claim data from multiple offices
- Flag patent status data older than 6 months as potentially outdated
- Confirm FTO assessments reference specific claim elements, not just patent titles

### Citation Standard

APA 7th Edition with patent-specific extensions:

- **Granted patents:** Inventor(s), Patent Title, Patent No. XX,XXX,XXX, Filed [date], Granted [date], Assignee: [name]
- **Applications:** Inventor(s), Title, Pub. No. [number], Filed [date], Published [date]
- **Inline references:** Numbered footnotes `[^1]`, `[^2]` with full bibliography
- **Agent citation IDs:** `[PS-01]` (patent search), `[PA-01]` (prior art), `[IL-01]` (IP landscape)

## Report Structure

Final reports include these sections:

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

## File Output Structure

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

## Disclaimer

This patent intelligence engine is provided for informational purposes only and does not constitute legal advice. Consult with a registered patent attorney for formal legal opinions on patentability, validity, or freedom-to-operate.

## License

MIT
