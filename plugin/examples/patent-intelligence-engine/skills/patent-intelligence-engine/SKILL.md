---
name: patent-intelligence-engine
description: "Domain-specialized research engine for intellectual property and patent landscape analysis. Multi-agent pipeline with tiered depth, iterative refinement, and structured confidence scoring for IP attorneys, technology transfer officers, and R&D strategists."
---

# Patent Intelligence Engine Research Engine

Launch a comprehensive multi-agent research system specialized for **Intellectual property and patent landscape analysis** research, serving **IP attorneys, technology transfer officers, and R&D strategists**.

This engine implements a seven-phase research pipeline with tier-based depth routing. It is fully self-contained -- no external research plugin dependencies are required. Agent protocols, quality standards, and detailed instructions are in reference files that agents load on-demand.

## Usage

- `/research [topic]` -- Standard tier (default): 2 agents: Patent Search Specialist, Prior Art Analyst
- `/research [URL]` -- Research starting from a specific webpage (Standard tier)
- `/research [topic] --quick` -- Quick tier: Single-agent lookup using Patent Search Specialist
- `/research [topic] --deep` -- Deep tier: Full pipeline with 3 agents: Patent Search Specialist, Prior Art Analyst, IP Landscape Mapper
- `/research [topic] --comprehensive` -- Comprehensive tier: All 3 agents + follow-up round
- `/research [topic] --outline-only` -- Planning phase only (produces outline, then stops)
- `/research [topic] --approve` -- Pause for user approval after Phase 1 (default for Standard+ tiers)
- `/research [topic] --no-approve` -- Skip outline approval gate (for automation or fast iteration)
- `/research [topic] --extend` -- Build on prior research in this project (default: standalone)
- `/research [topic] --reverifiable` -- Store source snapshots alongside hashes for independent re-verification
- `/research [topic] --no-vvc` -- Skip VVC verification phases (Phases 5-6)

---

## Research Architecture

| Phase | Name | Description |
|-------|------|-------------|
| 0 | Tier Detection | Parse flags, configure paths and depth |
| 1 | Research Planning | Strategic framework development and agent task design |
| 2 | Parallel Research | Multiple specialist agents research simultaneously |
| 3 | Synthesis | Multi-source integration, contradiction resolution, gap analysis |
| 4 | Draft Reporting | Draft report generation with claim tagging for VVC |
| 5 | VVC-Verify | Verify draft claims against sources (see `vvc-pipeline.md`) |
| 6 | VVC-Correct | Apply corrections, produce final report (see `vvc-pipeline.md`) |

| Tier | Planning | Research Agents | Synthesis | Report | VVC | Provenance | User Gate |
|------|----------|----------------|-----------|--------|-----|------------|-----------|
| Quick | No | patent-intelligence-engine:patent-search-specialist | No | Inline | None | Hash-only | No |
| Standard | Yes | patent-intelligence-engine:patent-search-specialist, patent-intelligence-engine:prior-art-analyst | Yes | Draft | Verify-only | Hash + Audit | --approve only |
| Deep | Yes | patent-intelligence-engine:patent-search-specialist, patent-intelligence-engine:prior-art-analyst, patent-intelligence-engine:ip-landscape-mapper | Yes | Draft | Full | Hash + Audit | --approve only |
| Comprehensive | Yes | All 3 agents + follow-up round | Yes | Draft | Full | Hash + Audit | Always |

---

## Phase 0: Tier Detection & Global Configuration

Parse tier from `$ARGUMENTS`: `--quick` / `--standard` / `--deep` / `--comprehensive` (default: Standard). Additional flags: `--outline-only` (stop after Phase 1), `--approve` / `--no-approve` (user gate control), `--extend` (project-aware context), `--reverifiable` (retain source snapshots), `--no-vvc` (skip Phases 5-6, Phase 4 becomes final reporting).

- If `--no-vvc` is present, set NO_VVC to **true** (skip Phases 5-6, Phase 4 becomes final reporting)
- If topic starts with `http://` or `https://`, treat as URL seed — fetch, extract topic, derive slug from title

### Derive Configuration

```
TOPIC_SLUG  = lowercase topic, hyphenate spaces, strip punctuation
RUN_TS      = YYYY-MM-DD_HHMMSS_ET (Eastern Time via bash: TZ='America/New_York' date '+%Y-%m-%d_%H%M%S_ET')
BASE_DIR    = "./research-reports/${RUN_TS}_${TOPIC_SLUG}"
ENGINE_ID   = "patent-intelligence-engine"
```

All files live under `BASE_DIR`. Never restate the prompt in chat; write long data to files and keep chat responses concise.

---

## Sub-Agent System

- research-planning-specialist
- synthesis-specialist
- research-reporting-specialist
- patent-intelligence-engine:patent-search-specialist (Patent Search Specialist)
- patent-intelligence-engine:prior-art-analyst (Prior Art Analyst)
- patent-intelligence-engine:ip-landscape-mapper (IP Landscape Mapper)
- vvc-specialist (Verification, Validation & Correction Specialist)

Research agents MUST be referenced by fully qualified name (`patent-intelligence-engine:[agentId]`) when deploying via Task tool.
The vvc-specialist is a pipeline agent that runs in Phases 5-6 (post-reporting). It does NOT participate in Phase 2 research.

---

## Quick Tier

If `--quick` detected, deploy a SINGLE agent (**patent-intelligence-engine:patent-search-specialist**). Agent FIRST ACTION: Read `${CLAUDE_SKILL_DIR}/standards.md`. Conduct focused patent intelligence research. Cap total WebFetch calls at 10. Format: `## Summary | ## Key Findings (with confidence) | ## Sources | ## Limitations`. Skip all remaining phases.

---

## Standard / Deep / Comprehensive Tiers

### Phase 1: Strategic Research Planning

Deploy **research-planning-specialist**: Analyze topic complexity within IP and patent landscape analysis. Build scope grid: core questions, sub-questions, dissenting angles, geographic/temporal slices. Design task assignments for downstream agents to reduce overlap. Save outline to `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md`.

**User Gates:** `--outline-only`: stop here | `--no-approve`: skip gate | Otherwise: present outline for approval.

### Phase 2: Parallel Research Execution

Deploy research agents per tier config. Each agent operates independently. Each agent writes to its own files only.

#### Agent: Patent Search Specialist
Deploy **patent-intelligence-engine:patent-search-specialist** — comprehensive patent searches across USPTO, EPO, WIPO, JPO, KIPO, CNIPA, CIPO using CPC/IPC codes, keyword strategies, and assignee tracking. Documents patent numbers, dates, assignees, claim counts, classifications, and citation metrics.

#### Agent: Prior Art Analyst
Deploy **patent-intelligence-engine:prior-art-analyst** — analyzes claims for novelty/non-obviousness using TSM and KSR frameworks. Reviews prosecution histories, identifies prior art (patents, NPL, commercial products), and maps claim-by-claim relationships.

#### Agent: IP Landscape Mapper
Deploy **patent-intelligence-engine:ip-landscape-mapper** — filing trends, top assignees, geographic patterns, CPC technology clusters, competitive matrices, whitespace identification, and FTO risk mapping.

**Common Agent Requirements** -- every Phase 2 agent MUST:
1. **FIRST ACTION**: Read `${CLAUDE_SKILL_DIR}/standards.md`, `${CLAUDE_SKILL_DIR}/research-protocol.md`, and `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md`
2. Apply Search Query Generation Protocol (4+ query types) and Iterative Search-Assess-Refine (max 4 iterations)
3. Include confidence tier (HIGH/MEDIUM/LOW/SPECULATIVE) and source credibility tier (1-5) for every claim
4. Save: bibliography (`_[AgentID]_Bibliography.md`), claims table (`_Claims_[AgentID].md`), methodology log (`_Methodology_Log_[AgentID].md`), sources (`_Sources_[AgentID].md`)
5. Cap total WebFetch calls at 10. If a URL returns 403/blocked/paywall, note in methodology log and move on -- do not retry.
6. Run contrarian sweep: search for refutations, critiques, failure cases, contradictory data
7. Recursive web exploration up to 5 levels deep from seed URLs

### Phase 2.5: Batch Source Hashing

After all Phase 2 agents complete, deploy a **general-purpose** batch hashing agent. Agent FIRST ACTION: Read `${CLAUDE_SKILL_DIR}/provenance.md` and execute the batch hashing protocol.

### Phase 3: Research Synthesis

Deploy **synthesis-specialist**:
- **FIRST ACTION**: Read `BASE_DIR/[TOPIC_SLUG]_Research_Outline.md`
- Read ALL agent output: claims tables (`_Claims_[AgentID].md`), bibliographies (`_[AgentID]_Bibliography.md`), sources (`_Sources_[AgentID].md`), methodology logs (`_Methodology_Log_[AgentID].md`)
- Consolidate per-agent methodology logs into `BASE_DIR/[TOPIC_SLUG]_Methodology_Log.md`
- Consolidate per-agent sources into `BASE_DIR/[TOPIC_SLUG]_Sources.md`
- Integrate findings, cross-reference claims, resolve contradictions, mark confidence scores
- Structure analysis for strategic IP decisions: landscape overview, filing trends, competitive matrices, FTO risk ratings, whitespace opportunities
- Save to `BASE_DIR/[TOPIC_SLUG]_Synthesis_Report.md`

### Phase 4: Conditional Reporting

If `--no-vvc` flag is present: Phase 4 heading is "Professional Reporting". Output file: `_Comprehensive_Report.md`. Skip claim tagging. Phases 5-6 are skipped.

Otherwise (VVC enabled, no `--no-vvc` flag): Phase 4 heading is "Draft Reporting". Output file: `_Draft_Report.md`. Apply claim tagging per `${CLAUDE_SKILL_DIR}/vvc-pipeline.md`.

Deploy **research-reporting-specialist**: transform synthesis into professional report. Tone: Professional patent intelligence assessment for IP attorneys, technology transfer officers, and C-suite. Sections: Executive Summary, Patent Landscape Overview, Key Patent Families, Claims Analysis, Prior Art Assessment, Competitive Portfolio Matrix, Freedom-to-Operate Assessment, Whitespace & Opportunity Analysis, IP Risk Matrix, Recommendations, Methodology, Bibliography. Use APA 7th Edition with patent extensions. Consolidate master bibliography.

### Phase 4.5: Provenance Audit

**Tier behavior:** Quick: skip | Standard/Deep/Comprehensive: run. Deploy a **general-purpose** provenance audit agent. Agent FIRST ACTION: Read `${CLAUDE_SKILL_DIR}/provenance.md` and execute the provenance audit protocol.

### Phase 5-6: VVC Verification & Correction

VVC specialist reads `${CLAUDE_SKILL_DIR}/vvc-pipeline.md` for full instructions. If NO_VVC is **true**, skip entirely. Now executing research deployment...

---

## File Output Structure

```
./research-reports/${RUN_TS}_${TOPIC_SLUG}/
├── [TOPIC_SLUG]_Research_Outline.md
├── [TOPIC_SLUG]_Claims_[AgentID].md              # Per-agent
├── [TOPIC_SLUG]_Sources_[AgentID].md              # Per-agent
├── [TOPIC_SLUG]_Methodology_Log_[AgentID].md      # Per-agent
├── [TOPIC_SLUG]_[AgentID]_Bibliography.md         # Per-agent
├── [TOPIC_SLUG]_Methodology_Log.md                # Consolidated
├── [TOPIC_SLUG]_Sources.md                        # Consolidated
├── [TOPIC_SLUG]_Synthesis_Report.md
├── [TOPIC_SLUG]_Draft_Report.md
├── [TOPIC_SLUG]_VVC_Verification_Report.md        # Phase 5
├── [TOPIC_SLUG]_VVC_Correction_Log.md             # Phase 6 (Deep/Comprehensive)
├── [TOPIC_SLUG]_Hash_Manifest.md                  # Provenance
├── [TOPIC_SLUG]_Provenance_Log.md                 # Provenance audit
├── [TOPIC_SLUG]_Comprehensive_Report.md           # Final output
└── [TOPIC_SLUG]_Master_Bibliography.md
```

---

## Key Workflow Features

- **Planning-first coordination** -- all agents read the outline as their first action
- **Iterative Search-Assess-Refine** -- up to 4 refinement passes per question
- **Per-agent file isolation** -- each agent writes to its own files; synthesis consolidates
- **Confidence scoring** on every claim (HIGH/MEDIUM/LOW/SPECULATIVE)
- **Source credibility hierarchy** -- no HIGH confidence claim on Tier 4-5 sources alone
- **Domain specialization** -- all agents operate within IP and patent landscape analysis context
- **Cryptographic provenance** -- batch hashing after Phase 2; `--reverifiable` retains snapshots
- **VVC pipeline** -- two-pass verify+correct with `--no-vvc` opt-out
- **Claim type taxonomy** -- [VC]/[PO]/[IE] tagging focuses verification effort

---

## Domain Preamble

You are conducting patent intelligence analysis to the standard expected by a senior IP attorney or head of technology transfer. Accuracy of patent data is paramount: every patent number, filing date, assignee, and claim reference must be verified against official records. Distinguish granted patents (enforceable rights) from published applications (potential future rights). Assess patent strength via claim breadth, prosecution history estoppel, geographic coverage, and remaining term.

All agents apply IP and patent landscape analysis-specific knowledge, terminology, and analytical frameworks for IP attorneys, technology transfer officers, and R&D strategists.

---

## Operational Lessons

No entries yet -- update after first research run with `/post-mortem`.
