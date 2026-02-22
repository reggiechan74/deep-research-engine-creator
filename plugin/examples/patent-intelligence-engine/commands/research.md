---
description: "Launch Patent Intelligence Engine for domain-specialized deep research"
argument-hint: "[research topic] [--quick|--standard|--deep|--comprehensive] [--approve] [--outline-only]"
allowed-tools: ["Task", "WebFetch", "WebSearch", "Write", "Read", "Edit", "Glob", "Grep"]
---

# Patent Intelligence Engine — Research Command

Launch a domain-specialized multi-agent research system for Intellectual property and patent landscape analysis research. The system uses tiered research depth, iterative search refinement, cross-agent coordination, and structured confidence scoring to produce professional-grade research outputs.

This engine specializes in Intellectual property and patent landscape analysis research for IP attorneys, technology transfer officers, and R&D strategists.

## Usage

- `/research [topic]` -- Standard tier (default)
- `/research [topic] --quick` -- Quick tier: fast factual lookup
- `/research [topic] --deep` -- Deep tier: full multi-agent pipeline
- `/research [topic] --comprehensive` -- Comprehensive tier: deep + follow-up rounds
- `/research [topic] --approve` -- Pause for user approval after planning phase
- `/research [topic] --outline-only` -- Stop after planning phase (outline only)

## Phase 0: Tier Detection & Configuration

Parse tier from `$ARGUMENTS`:
- If `--quick` is present, set tier to Quick
- If `--standard` is present, set tier to Standard
- If `--deep` is present, set tier to Deep
- If `--comprehensive` is present, set tier to Comprehensive
- If `--outline-only` is present, set tier to Standard but stop after Phase 1
- If `--approve` is present, pause after planning phase for user approval
- Otherwise, default to Standard tier
- Strip flag tokens from `$ARGUMENTS` to derive the research topic

Derive configuration:
- `TOPIC_SLUG` from topic: lowercase, hyphenate spaces, strip punctuation
- `RUN_TS` as `YYYY-MM-DD_HHMMSS_ET` (Eastern Time via bash: `TZ='America/New_York' date '+%Y-%m-%d_%H%M%S_ET'`)
- `BASE_DIR="02_KNOWLEDGE/5_RESEARCH_REPORTS/${RUN_TS}_${TOPIC_SLUG}"`
- All files and directories live under `BASE_DIR`

## Tier Configuration

| Tier | Planning | Research Agents | Synthesis | Report | User Gate |
|------|----------|----------------|-----------|--------|-----------|
| Quick | No | patent-search-specialist | No | Inline | No |
| Standard | Yes | patent-search-specialist, prior-art-analyst | Yes | Full | --approve only |
| Deep | Yes | patent-search-specialist, prior-art-analyst, ip-landscape-mapper | Yes | Full | --approve only |
| Comprehensive | Yes | patent-search-specialist, prior-art-analyst, ip-landscape-mapper + follow-up round | Yes | Full | Always |

## Research Engine Skill

Follow the research engine skill at `${CLAUDE_PLUGIN_ROOT}/skills/patent-intelligence-engine/SKILL.md`.

The skill file contains the complete multi-phase research pipeline, agent definitions, source strategy, quality framework, and output structure for this engine. Execute all phases as defined there.

## Execution

Parse the tier from arguments, configure paths, then hand off to the skill file for full pipeline execution.

Starting Patent Intelligence Engine research system...
