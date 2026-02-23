# Patent Intelligence Engine

> Intellectual property and patent landscape analysis — built for IP attorneys, technology transfer officers, and R&D strategists

A domain-specialized deep research engine powered by Claude Code's multi-agent architecture. This engine conducts systematic, tiered research with structured confidence scoring, source credibility hierarchies, and professional-grade report generation.

**Mode:** self-contained
**Version:** 1.0.0
**Created:** 2026-02-21T21:54:02-05:00

## Installation

```bash
claude --plugin-dir ./patent-intelligence-engine
```

Or symlink into your Claude Code plugins directory:

```bash
ln -s "$(pwd)/patent-intelligence-engine" ~/.claude/plugins/patent-intelligence-engine
```

## Commands

| Command | Description |
|---------|-------------|
| `/research [topic] [flags]` | Launch multi-agent research pipeline |
| `/sources` | Display source hierarchy and configuration |

### Research Tiers

| Flag | Depth | Description |
|------|-------|-------------|
| `--quick` | Quick | Fast factual lookup, single agent, inline summary |
| *(default)* | Standard | Multi-agent pipeline with planning, synthesis, and reporting |
| `--deep` | Deep | Full agent pipeline with all specialists active |
| `--comprehensive` | Comprehensive | Deep + follow-up rounds for gap closure |
| `--approve` | *(modifier)* | Pause after planning phase for user approval |

## Agent Pipeline

| Agent ID | Role | Model | Type |
|----------|------|-------|------|
| patent-search-specialist | Patent Search Specialist | sonnet | general-purpose |
| prior-art-analyst | Prior Art Analyst | sonnet | expert-instructor |
| ip-landscape-mapper | IP Landscape Mapper | sonnet | intelligence-analyst |
| vvc-specialist | Verification, Validation & Correction Specialist | sonnet | general-purpose |

## Source Credibility Hierarchy

| Tier | Name | Key Sources |
|------|------|-------------|
| 1 | Official Patent Databases | USPTO PATFT and AppFT (patents.google.com, patft.uspto.gov), EPO Espacenet and Global Patent Index, WIPO PATENTSCOPE and PCT publications, Google Patents, National patent office databases (JPO J-PlatPat, KIPO KIPRIS, CNIPA, CIPO) |
| 2 | Patent Analytics & Legal Sources | Patent prosecution histories (USPTO PAIR, EPO Register), Patent litigation databases (PACER, Docket Navigator, Lex Machina), Published patent examiner search reports, PTAB decisions, Patent classification systems (CPC, IPC) |
| 3 | Technical & Scientific Literature | Peer-reviewed technical journals, Conference proceedings, Standards body publications (IEEE, ISO, ASTM), Published doctoral dissertations, ArXiv preprints |
| 4 | Industry & Commercial Sources | Patent analytics platform reports (PatSnap, Orbit Intelligence, Innography), Industry news and trade publications, Company press releases, IP professional blogs, Patent valuation reports |
| 5 | Unreliable / Unverified | Anonymous forum posts, Unverified patent-pending claims, AI-generated summaries, Unverified ownership claims, Social media discussions |

## Sample Questions

1. What is the patent landscape for solid-state battery technology?
2. Who are the top filers in autonomous vehicle LiDAR patents since 2020?
3. Are there freedom-to-operate risks for our graphene-based electrode invention?
4. What patent trends exist in CRISPR gene editing therapeutics?
5. Map the IP portfolio of Tesla vs BYD in battery technology

## Quality Framework

This engine uses a four-tier confidence scoring system (HIGH/MEDIUM/LOW/SPECULATIVE) with mandatory source credibility tracking. All HIGH-confidence claims require verification against Tier 1-3 sources. Patent numbers must be verified against official patent office databases. The engine enforces minimum evidence thresholds and validation rules specific to intellectual property research.

## Verification, Validation & Correction (VVC)

Every research tool cites sources -- but a citation is just a URL. It doesn't mean the AI read the source correctly. VVC goes beyond citations: it extracts every factual claim, re-fetches the cited source, and checks two things: (1) Is the source credible for this claim? (2) Was the source accurately represented? Claims that fail are auto-corrected or flagged.

- **Claim Tagging:** Phase 4 tags every assertion as `[VC]` (Verifiable Claim), `[PO]` (Professional Opinion), or `[IE]` (Inferred/Extrapolated)
- **Phase 5 (VVC-Verify):** Extracts `[VC]` claims, fetches cited sources, classifies alignment (CONFIRMED/PARAPHRASED/OVERSTATED/DISPUTED/UNSUPPORTED), recommends corrections
- **Phase 6 (VVC-Correct):** Implements REVISE/DOWNGRADE/REMOVE/REPLACE_SOURCE recommendations, produces the final Comprehensive Report + correction log
- **Verification Scope:** 100% HIGH, 75% MEDIUM, 0% LOW/SPECULATIVE
- **Tier Behavior:** Quick: none | Standard: verify-only | Deep: full | Comprehensive: full

## Output Structure

Research reports are saved to a timestamped directory using the engine's configured file naming convention (`{date}_{topic_slug}_patent_intelligence.md`).

```
./research-reports/${RUN_TS}_${TOPIC_SLUG}/
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
├── [TOPIC_SLUG]_VVC_Correction_Log.md
├── [TOPIC_SLUG]_Comprehensive_Report.md
├── [TOPIC_SLUG]_Citation_Verification_Report.md
└── [TOPIC_SLUG]_Master_Bibliography.md
```

## License

MIT

---

*Generated by [deep-research-engine-creator](https://github.com/reggiechan74/deep-research-engine-creator) v1.0.0 on 2026-02-21T21:54:02-05:00.*
