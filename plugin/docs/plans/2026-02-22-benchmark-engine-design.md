---
title: benchmark-engine Command Design
date: 2026-02-22
keywords: [benchmark, draco, reportbench, vvc-delta, testing]
lastUpdated: 2026-02-22
---

# /benchmark-engine Command Design

## Overview

A new command for the Deep Research Engine Creator plugin that benchmarks generated engines against published deep research benchmarks and produces scored reports with VVC delta analysis. This validates engine quality, measures the impact of VVC, and enables comparison against published baselines (Perplexity, Gemini, OpenAI).

**Release target:** v1.3.0

## Architecture

Follows the existing command + skill delegation pattern:

```
commands/benchmark-engine.md       # Thin command: parse args, load skill
skills/engine-benchmarker/SKILL.md # Full benchmark logic
```

This mirrors `create-engine.md` → `skills/engine-creator/SKILL.md`.

## Command Interface

```
/benchmark-engine <path-to-engine> [--benchmark draco|reportbench|self-eval]
    [--subset <domain>] [--limit N] [--tier quick|standard|deep|comprehensive]
    [--no-vvc-delta] [--output-dir <path>]
```

| Flag | Default | Description |
|------|---------|-------------|
| `<path-to-engine>` | (required) | Path to the generated engine directory |
| `--benchmark` | `self-eval` | Which benchmark to run: `draco`, `reportbench`, `self-eval` |
| `--subset` | all | Domain filter (e.g., `law`, `medicine`, `finance` for DRACO) |
| `--limit` | 5 (self-eval), 10 (draco/reportbench) | Max queries to run (cost control) |
| `--tier` | auto-select | Override tier auto-selection with a fixed tier |
| `--no-vvc-delta` | false | Skip VVC-off comparison run (halves cost) |
| `--output-dir` | `<engine-path>/benchmarks/` | Override output location |

## Three Benchmark Modes

### Mode 1: Self-Evaluation (`--benchmark self-eval`)

Uses the engine's own `sampleQuestions` from `engine-config.json`. No external dataset required.

**Flow:**
1. Read `engine-config.json` -> extract `sampleQuestions` (3-5 queries)
2. For each query, run via subprocess (twice if VVC delta enabled)
3. Score each output using LLM-as-judge (sonnet model) against rubrics:
   - Factual density: claims per 500 words
   - Citation density: citations per claim
   - Source tier distribution: % from Tier 1-2 vs Tier 4-5
   - VVC correction rate: claims corrected (VVC-on run only)
   - Report structure compliance: matches configured `outputStructure.reportSections`
4. Produce comparative scorecard

**Default tier:** `--standard` (representative of typical usage)

### Mode 2: DRACO (`--benchmark draco`)

Uses Perplexity's open DRACO benchmark (100 tasks, 10 domains, ~40 rubrics per task).

**Flow:**
1. Check if DRACO dataset is cached at `~/.cache/engine-benchmarks/draco/`; if not, download from HuggingFace (`perplexity-ai/draco`)
2. Parse task list, filter by `--subset` domain if specified
3. Map each task's difficulty to a tier (unless `--tier` override):
   - Simple tasks -> `--quick`
   - Moderate tasks -> `--standard`
   - Complex tasks -> `--deep`
4. For each task (up to `--limit`), run via subprocess (twice if VVC delta enabled)
5. Score using DRACO's published LLM-as-judge rubrics (per-task criteria)
6. Compare to published baselines:
   - Perplexity Deep Research: 70.5%
   - Gemini Deep Research: 59.0%
   - OpenAI o3 Deep Research: 52.1%

**DRACO domain subsets:** Academic, Finance, Law, Medicine, Technology, General Knowledge, UX Design, Personal Assistant, Shopping/Product Comparison, Needle in a Haystack

### Mode 3: ReportBench (`--benchmark reportbench`)

Uses ByteDance's ReportBench (arXiv survey gold standards, citation-focused metrics).

**Flow:**
1. Check if ReportBench is cached at `~/.cache/engine-benchmarks/reportbench/`; if not, clone from GitHub (`ByteDance-BandAI/ReportBench`)
2. Select evaluation prompts derived from arXiv survey gold standards
3. For each prompt (up to `--limit`), run via subprocess (twice if VVC delta enabled)
4. Score using ReportBench's evaluation scripts:
   - Citation precision and recall against gold standard
   - Statement hallucination rate
   - Citation hallucination rate
5. Report VVC delta specifically on hallucination metrics

**Default tier:** `--deep` (academic survey tasks require depth)

## Execution Pipeline

### Subprocess Execution

Each benchmark query is executed as a separate Claude Code process:

```bash
# Run 1: VVC enabled (engine's default config)
claude -p "/research {query} --{tier}" --plugin-dir {engine-path}

# Run 2: VVC disabled (if VVC delta enabled)
claude -p "/research {query} --{tier}" --plugin-dir {temp-engine-path}
```

### VVC Toggle Mechanism

For the VVC-off run:
1. Create a temporary copy of the engine directory (shallow copy, symlink large files)
2. Patch the copied `engine-config.json`: set `qualityFramework.vvc.enabled: false`
3. Run the benchmark query against the patched copy
4. Clean up temporary directory after each query

The original engine is never modified.

### Tier Auto-Selection

When `--tier` is not specified:

| Benchmark | Logic |
|-----------|-------|
| self-eval | Always `--standard` |
| draco | Map task difficulty metadata: simple -> quick, moderate -> standard, complex -> deep |
| reportbench | Always `--deep` |

### Cost Estimation & User Confirmation

Before executing, display estimated scope and confirm:

```
Benchmark: DRACO (Law subset)
Queries: 10
Tier: deep (auto-selected)
VVC delta: enabled (2x runs per query)
Total runs: 20

Proceed? [Y/n]
```

## Scoring

### Scoring Methods Per Benchmark

| Benchmark | Scoring Method | Key Metrics |
|-----------|---------------|-------------|
| self-eval | LLM-as-judge (sonnet, structured rubric) | Factual density, citation density, source tier distribution, structure compliance, VVC correction rate |
| draco | LLM-as-judge (DRACO's published per-task rubrics) | Accuracy, completeness, objectivity, citation quality |
| reportbench | ReportBench eval scripts + LLM-as-judge | Citation precision, citation recall, statement hallucination rate, citation hallucination rate |

### VVC Delta Scoring

For each metric, compute:
- VVC-on score
- VVC-off score
- Delta (VVC-on minus VVC-off)
- Delta as percentage improvement

When `--no-vvc-delta` is used, VVC-off columns show "N/A".

## Output Structure

### Per-Engine Results

Saved to `<engine-path>/benchmarks/<benchmark>/<timestamp>/`:

```
benchmarks/
├── draco/
│   └── 2026-02-23T14-30-00/
│       ├── benchmark-report.md     # Full scored report
│       ├── vvc-delta.md            # VVC on vs off comparison
│       ├── scores.json             # Machine-readable scores
│       └── raw/                    # Raw engine outputs per query
│           ├── query-001-vvc-on/
│           ├── query-001-vvc-off/
│           ├── query-002-vvc-on/
│           └── ...
```

### Central Scoreboard

Appended to `benchmarks/SCOREBOARD.md` (created if not exists):

```markdown
## Benchmark Scoreboard

| Engine | Benchmark | Subset | Score (VVC On) | Score (VVC Off) | VVC Delta | Date | Baseline |
|--------|-----------|--------|----------------|-----------------|-----------|------|----------|
| legal-research | DRACO | Law | 78.3% | 64.1% | +14.2% | 2026-02-23 | Perplexity: 90.2% |
| patent-intel | self-eval | all | 82/100 | 71/100 | +11 | 2026-02-23 | -- |
```

### benchmark-report.md Structure

```markdown
# Benchmark Report: {engine-name}

## Summary
- Benchmark: {benchmark} ({subset})
- Engine: {engine-name} v{version}
- Tier: {tier} (auto-selected | override)
- Queries: {N} (VVC delta: enabled | disabled)
- Date: {timestamp}

## Overall Score
| Metric | VVC On | VVC Off | Delta |
|--------|--------|---------|-------|
| Overall | X% | Y% | +Z% |
| Citation accuracy | ... | ... | ... |
| Factual correctness | ... | ... | ... |
| Source credibility | ... | ... | ... |

## Comparison to Published Baselines
| System | Score |
|--------|-------|
| This engine (VVC on) | X% |
| This engine (VVC off) | Y% |
| Perplexity Deep Research | 70.5% |
| Gemini Deep Research | 59.0% |
| OpenAI o3 Deep Research | 52.1% |

## Per-Query Scores
[detailed breakdown per query with individual rubric scores]

## VVC Delta Analysis
[which claims were corrected, source credibility improvements, correction categories]
[CONFIRMED/PARAPHRASED/OVERSTATED/UNDERSTATED/DISPUTED/UNSUPPORTED breakdown]
```

## File Inventory

New files to create:

| File | Purpose |
|------|---------|
| `commands/benchmark-engine.md` | Thin command: parse args, load skill, confirm cost |
| `skills/engine-benchmarker/SKILL.md` | Full benchmark logic: dataset management, execution, scoring, reporting |

Files to update:

| File | Change |
|------|--------|
| `.claude-plugin/plugin.json` | Bump version to 1.3.0 |
| `CHANGELOG.md` | Add v1.3.0 entry |
| `README.md` | Update commands table, cross-reference benchmarking section |

## Design Decisions

1. **Subprocess execution** over inline: Tests the real plugin stack end-to-end. More expensive but produces honest, reproducible results.
2. **Always VVC delta by default** with `--no-vvc-delta` opt-out: The VVC comparison is the most valuable data this tool produces. It should be the default, with a cost-saving escape hatch.
3. **Command + Skill architecture**: Matches the existing `create-engine` pattern. Keeps command thin, logic centralized in skill.
4. **Tier auto-selection with override**: Benchmark difficulty should drive tier selection, but users need manual control for cost management or specific testing scenarios.
5. **Dual output (per-engine + central scoreboard)**: Results co-located with the engine they test (version-controllable), but cross-engine comparison available via central scoreboard.
6. **Dataset caching at `~/.cache/engine-benchmarks/`**: Download once, reuse across runs. Avoids re-downloading DRACO/ReportBench datasets on every invocation.
