---
description: "Launch patent intelligence research on a topic with configurable depth"
argument-hint: "<topic> [--quick|--standard|--deep|--comprehensive] [--approve]"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebSearch", "WebFetch", "Task"]
---

# Patent Intelligence Engine -- Research Command

Launch a domain-specialized multi-agent research system for **intellectual property and patent landscape analysis**. The system uses tiered research depth, iterative search refinement, cross-agent coordination, and structured confidence scoring to produce professional-grade patent intelligence reports.

This engine specializes in patent landscape analysis, prior art assessment, freedom-to-operate evaluations, and competitive IP portfolio mapping for **IP attorneys, technology transfer officers, and patent analysts**.

## Usage

- `/research [topic]` -- Standard tier (default): multi-agent pipeline with patent search + prior art analysis
- `/research [topic] --quick` -- Quick tier: fast patent lookup with single agent, inline summary
- `/research [topic] --deep` -- Deep tier: full 3-agent pipeline including landscape mapping
- `/research [topic] --comprehensive` -- Comprehensive tier: deep + follow-up rounds for gap closure
- `/research [topic] --approve` -- Pause for user approval after planning phase

## Phase 0: Tier Detection & Configuration

Parse tier from `$ARGUMENTS`:
- If `--quick` is present, set tier to Quick
- If `--standard` is present, set tier to Standard
- If `--deep` is present, set tier to Deep
- If `--comprehensive` is present, set tier to Comprehensive
- If `--outline-only` is present, set tier to Standard but stop after Phase 1
- If `--approve` is present, pause after Phase 1 for user approval
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
| Quick | No | patent-search-specialist only | No | Inline | No |
| Standard | Yes | patent-search-specialist, prior-art-analyst | Yes | Full | --approve only |
| Deep | Yes | patent-search-specialist, prior-art-analyst, ip-landscape-mapper | Yes | Full | --approve only |
| Comprehensive | Yes | All 3 agents + follow-up round | Yes | Full | Always |

## Research Engine Skill

Follow the research engine skill at `${CLAUDE_PLUGIN_ROOT}/skills/patent-research/SKILL.md`.

The skill file contains the complete multi-phase research pipeline, agent definitions, source strategy, quality framework, and output structure for this engine. Execute all phases as defined there.

## Execution

Parse the tier from arguments, configure paths, then hand off to the skill file for full pipeline execution.

Starting Patent Intelligence Engine research system...
