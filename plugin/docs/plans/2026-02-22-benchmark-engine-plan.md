# /benchmark-engine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `/benchmark-engine` command that benchmarks generated research engines against published deep research benchmarks (DRACO, ReportBench, self-eval) with VVC delta analysis and scored reports.

**Architecture:** Thin command (`commands/benchmark-engine.md`) delegates to a full benchmark skill (`skills/engine-benchmarker/SKILL.md`). Follows the proven `create-engine.md` → `skills/engine-creator/SKILL.md` pattern. Subprocess execution runs each benchmark query as a real Claude Code process for honest end-to-end testing.

**Tech Stack:** Claude Code plugin system (markdown commands + skills), JSON config parsing, subprocess execution via `claude -p`, LLM-as-judge scoring via sonnet model.

---

### Task 1: Create the Thin Command File

**Files:**
- Create: `commands/benchmark-engine.md`

**Step 1: Create the command file**

Write `commands/benchmark-engine.md` with this exact content:

```markdown
---
description: "Benchmark a generated research engine against published deep research benchmarks with VVC delta analysis"
argument-hint: "<path-to-engine> [--benchmark draco|reportbench|self-eval] [--subset <domain>] [--limit N] [--tier quick|standard|deep|comprehensive] [--no-vvc-delta] [--output-dir <path>]"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "WebSearch", "WebFetch", "Task"]
---

# Benchmark Research Engine

You are running a benchmark suite against a generated research engine to measure its quality, compare against published baselines, and quantify the impact of VVC (Verification, Validation & Correction).

## 1. Parse Arguments

Parse `$ARGUMENTS`:
- **First argument** (required): path to the engine directory
- **`--benchmark`** (default: `self-eval`): which benchmark to run — `draco`, `reportbench`, or `self-eval`
- **`--subset`** (default: all): domain filter (e.g., `law`, `medicine`, `finance` for DRACO)
- **`--limit`** (default: 5 for self-eval, 10 for draco/reportbench): max queries to run
- **`--tier`** (default: auto-select): override tier auto-selection with a fixed tier
- **`--no-vvc-delta`** (default: false): skip VVC-off comparison run (halves cost)
- **`--output-dir`** (default: `<engine-path>/benchmarks/`): override output location

If no engine path is provided, report an error and exit.

Read `engine-config.json` from the specified path. If the file doesn't exist or is invalid, report an error and exit.

## 2. Validate Engine

Before benchmarking, run a lightweight structural check:
- Verify `engine-config.json` exists and parses as valid JSON
- Verify `commands/research.md` exists (the engine must have a `/research` command)
- Verify at least one agent file exists in `agents/`
- Check if VVC is enabled in `qualityFramework.vvc.enabled` — if not and `--no-vvc-delta` is not set, warn the user that VVC delta will only test with VVC disabled (no meaningful delta)

If validation fails, report what's missing and exit.

## 3. Load the Skill

Read the Engine Benchmarker skill at:
`${CLAUDE_PLUGIN_ROOT}/skills/engine-benchmarker/SKILL.md`

This is your complete reference for dataset management, benchmark execution, scoring rubrics, and report generation.

## 4. Execute the Benchmark

Follow the **Benchmark Execution Protocol** from the skill exactly:

1. **Dataset acquisition** — download/cache benchmark datasets if needed
2. **Cost estimation** — display estimated scope (queries × runs × tier) and confirm with user
3. **Subprocess execution** — run each query as a real Claude Code process
4. **Scoring** — apply benchmark-specific rubrics via LLM-as-judge
5. **VVC delta analysis** — compare VVC-on vs VVC-off scores (unless `--no-vvc-delta`)
6. **Report generation** — produce benchmark-report.md, vvc-delta.md, scores.json
7. **Scoreboard update** — append results to central SCOREBOARD.md

## Key Rules

- **Never modify the original engine.** VVC-off runs use a temporary copy with patched config.
- **Always confirm before executing.** Display cost estimation and get explicit user approval.
- **Use subprocess execution.** Each query runs as `claude -p "/research {query} --{tier}" --plugin-dir {engine-path}`.
- **Clean up temporary directories.** Remove patched engine copies after each query.
- **Save raw outputs.** Store every engine output in `raw/query-NNN-vvc-on/` and `raw/query-NNN-vvc-off/` subdirectories.
```

**Step 2: Verify the command file**

Run: `head -5 commands/benchmark-engine.md` (from the engine-creator directory)
Expected: YAML frontmatter with `description`, `argument-hint`, `allowed-tools`

**Step 3: Verify frontmatter matches existing patterns**

Compare the frontmatter structure against `commands/test-engine.md`:
- Both should have `description`, `argument-hint`, `allowed-tools`
- `benchmark-engine.md` additionally needs `Task` in `allowed-tools` (for subprocess execution via sub-agents)

**Step 4: Commit**

```bash
git add deep-research-engine-creator/commands/benchmark-engine.md
git commit -m "feat(benchmark): add thin benchmark-engine command

Delegates to skills/engine-benchmarker/SKILL.md for full benchmark logic.
Supports --benchmark draco|reportbench|self-eval, --tier override,
--no-vvc-delta, --subset filtering, and --limit cost control.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2: Create the Engine Benchmarker Skill (Part 1 — Header and Dataset Management)

The SKILL.md is large. We split creation across Tasks 2-5.

**Files:**
- Create: `skills/engine-benchmarker/SKILL.md` (first section)

**Step 1: Create the skill directory and file header**

Write `skills/engine-benchmarker/SKILL.md` with the header and dataset management sections:

```markdown
---
name: engine-benchmarker
description: "Benchmark generated research engines against published deep research benchmarks with VVC delta analysis and scored reports"
---

# Engine Benchmarker

You are benchmarking a generated deep research engine against published benchmarks. Your job is to execute benchmark queries as real Claude Code subprocess runs, score the outputs using LLM-as-judge rubrics, measure the impact of VVC, and produce scored reports with baseline comparisons.

## Benchmark Execution Protocol

### Phase 1: Dataset Acquisition

Based on the `--benchmark` flag, acquire the dataset:

#### Self-Evaluation (`--benchmark self-eval`)

No external dataset needed. Read `engine-config.json` from the engine path and extract `sampleQuestions`. These are the benchmark queries (typically 3-5).

Default `--limit`: 5 (or however many sample questions exist, whichever is fewer).
Default `--tier`: `standard`.

#### DRACO (`--benchmark draco`)

Check if the DRACO dataset is cached at `~/.cache/engine-benchmarks/draco/`. If not, download it:

```bash
mkdir -p ~/.cache/engine-benchmarks/draco
# Clone from HuggingFace
git clone https://huggingface.co/datasets/perplexity-ai/draco ~/.cache/engine-benchmarks/draco
```

Parse the dataset to extract task definitions. Each DRACO task has:
- `query`: the research question
- `domain`: one of Academic, Finance, Law, Medicine, Technology, General Knowledge, UX Design, Personal Assistant, Shopping/Product Comparison, Needle in a Haystack
- `difficulty`: simple, moderate, complex
- `rubrics`: per-task evaluation criteria (accuracy, completeness, objectivity, citation quality)

If `--subset` is specified, filter tasks to only that domain (case-insensitive match).

Default `--limit`: 10.
Default `--tier`: auto-select based on task difficulty (see Phase 2).

#### ReportBench (`--benchmark reportbench`)

Check if ReportBench is cached at `~/.cache/engine-benchmarks/reportbench/`. If not, clone it:

```bash
mkdir -p ~/.cache/engine-benchmarks/reportbench
git clone https://github.com/ByteDance-BandAI/ReportBench ~/.cache/engine-benchmarks/reportbench
```

Select evaluation prompts derived from arXiv survey gold standards. Each ReportBench task has:
- `prompt`: the research question
- `gold_citations`: reference citation set for precision/recall
- `gold_statements`: reference statements for hallucination detection

Default `--limit`: 10.
Default `--tier`: `deep` (academic survey tasks require depth).
```

**Step 2: Verify the file was created**

Run: `wc -l skills/engine-benchmarker/SKILL.md` (from the engine-creator directory)
Expected: ~65-70 lines

**Step 3: Commit**

```bash
git add deep-research-engine-creator/skills/engine-benchmarker/SKILL.md
git commit -m "feat(benchmark): add engine-benchmarker skill header and dataset management

Phase 1 of SKILL.md: frontmatter, overview, dataset acquisition for
self-eval, DRACO (HuggingFace), and ReportBench (GitHub) with caching.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 3: Add Execution Pipeline to Skill (Part 2)

**Files:**
- Modify: `skills/engine-benchmarker/SKILL.md` (append)

**Step 1: Append the execution pipeline section**

Append to the end of `skills/engine-benchmarker/SKILL.md`:

````markdown

### Phase 2: Cost Estimation and Confirmation

Before executing any benchmark queries, calculate and display the estimated scope:

```
Benchmark: {benchmark} ({subset or "all"})
Queries: {N}
Tier: {tier} (auto-selected | override)
VVC delta: {enabled | disabled} ({1x | 2x} runs per query)
Total runs: {N × multiplier}

Proceed? [Y/n]
```

Use AskUserQuestion to get confirmation. If the user declines, exit gracefully.

#### Tier Auto-Selection

When `--tier` is not specified:

| Benchmark | Logic |
|-----------|-------|
| self-eval | Always `standard` |
| draco | Map task difficulty: simple → `quick`, moderate → `standard`, complex → `deep` |
| reportbench | Always `deep` |

When `--tier` IS specified, use that tier for all queries regardless of benchmark or difficulty.

### Phase 3: Subprocess Execution

For each benchmark query, execute the engine as a real Claude Code subprocess:

#### Run 1: VVC Enabled (engine's default config)

```bash
claude -p "/research {query} --{tier}" --plugin-dir {engine-path}
```

Capture the full output. Save to `raw/query-{NNN}-vvc-on/output.md`.

#### Run 2: VVC Disabled (if VVC delta enabled)

Only execute if `--no-vvc-delta` was NOT passed:

1. Create a temporary copy of the engine directory:
   ```bash
   TEMP_DIR=$(mktemp -d)
   cp -r {engine-path}/* "$TEMP_DIR/"
   ```
2. Patch the copied `engine-config.json`: set `qualityFramework.vvc.enabled` to `false`
3. Run:
   ```bash
   claude -p "/research {query} --{tier}" --plugin-dir "$TEMP_DIR"
   ```
4. Capture the full output. Save to `raw/query-{NNN}-vvc-off/output.md`.
5. Clean up: `rm -rf "$TEMP_DIR"`

**Important:** The original engine directory is NEVER modified. All VVC-off runs use temporary copies.

#### Error Handling

- If a subprocess fails (non-zero exit, timeout, empty output), record the query as FAILED with the error message.
- Continue to the next query — do not abort the entire benchmark.
- Include failed queries in the final report with status FAILED and reason.
- Timeout: allow up to 10 minutes per subprocess run (600000ms).
````

**Step 2: Verify the appended content**

Run: `grep -c "Phase" skills/engine-benchmarker/SKILL.md` (from the engine-creator directory)
Expected: 3 (Phase 1, Phase 2, Phase 3)

**Step 3: Commit**

```bash
git add deep-research-engine-creator/skills/engine-benchmarker/SKILL.md
git commit -m "feat(benchmark): add execution pipeline to engine-benchmarker skill

Phases 2-3: cost estimation with user confirmation, tier auto-selection,
subprocess execution via claude -p, VVC toggle via temp directory patching,
error handling for failed runs.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 4: Add Scoring Logic to Skill (Part 3)

**Files:**
- Modify: `skills/engine-benchmarker/SKILL.md` (append)

**Step 1: Append the scoring section**

Append to the end of `skills/engine-benchmarker/SKILL.md`:

````markdown

### Phase 4: Scoring

Score each query's output using LLM-as-judge (sonnet model). The scoring method varies by benchmark:

#### Self-Eval Scoring Rubric

For each query output, evaluate on a 0-100 scale across these dimensions:

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| Factual density | 20% | Claims per 500 words — higher is better (target: 8-12) |
| Citation density | 20% | Citations per claim — higher is better (target: 0.8-1.0) |
| Source tier distribution | 20% | % of citations from Tier 1-2 sources vs Tier 4-5 — higher tier ratio is better |
| Structure compliance | 20% | How well the output matches `outputStructure.reportSections` from engine config |
| VVC correction rate | 20% | Claims corrected by VVC (VVC-on run only). 0 for VVC-off runs. |

**Scoring prompt template for self-eval:**

```
You are an expert research quality evaluator. Score the following research output on a 0-100 scale for each dimension.

## Engine Configuration Context
- Domain: {engineMeta.domain}
- Expected report sections: {outputStructure.reportSections}
- Source credibility tiers: {sourceStrategy.credibilityTiers summary}

## Research Output
{output content}

## Score each dimension (0-100):
1. Factual density: How many specific, verifiable claims per 500 words?
2. Citation density: What fraction of claims have explicit source citations?
3. Source tier distribution: What percentage of cited sources would rank in Tier 1-2 of the engine's credibility hierarchy?
4. Structure compliance: How closely does the output match the expected report sections?
5. VVC correction rate: How many claims show evidence of verification/correction? (0 if VVC was disabled)

Return JSON: {"factual_density": N, "citation_density": N, "source_tier": N, "structure": N, "vvc_correction": N, "overall": N, "notes": "..."}
```

#### DRACO Scoring

Use DRACO's published per-task rubrics. Each task defines specific criteria across:
- **Accuracy**: factual correctness of claims
- **Completeness**: coverage of required information
- **Objectivity**: balanced presentation of perspectives
- **Citation quality**: relevance and reliability of cited sources

Score each criterion as pass/fail per DRACO's rubric definitions. The overall score is the percentage of rubrics passed.

**Published baselines for comparison:**
- Perplexity Deep Research: 70.5%
- Gemini Deep Research: 59.0%
- OpenAI o3 Deep Research: 52.1%

#### ReportBench Scoring

Apply ReportBench's evaluation methodology:
- **Citation precision**: % of engine citations that match gold standard citations
- **Citation recall**: % of gold standard citations found in engine output
- **Statement hallucination rate**: % of engine statements not supported by any cited source
- **Citation hallucination rate**: % of engine citations where the claim doesn't appear in the cited source

Use ReportBench's evaluation scripts if available, otherwise replicate the scoring logic via LLM-as-judge.

#### VVC Delta Computation

For each metric, compute:

| Column | Formula |
|--------|---------|
| VVC-on score | Score from Run 1 |
| VVC-off score | Score from Run 2 (or "N/A" if `--no-vvc-delta`) |
| Delta | VVC-on minus VVC-off |
| Delta % | (Delta / VVC-off) × 100 |

Aggregate across all queries to produce mean scores per metric.
````

**Step 2: Verify the appended content**

Run: `grep -c "Phase" skills/engine-benchmarker/SKILL.md` (from the engine-creator directory)
Expected: 4 (Phase 1 through Phase 4)

**Step 3: Commit**

```bash
git add deep-research-engine-creator/skills/engine-benchmarker/SKILL.md
git commit -m "feat(benchmark): add scoring logic to engine-benchmarker skill

Phase 4: self-eval rubric (5 dimensions × 0-100), DRACO published rubrics
with baselines, ReportBench citation precision/recall/hallucination,
VVC delta computation formulas.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 5: Add Report Generation to Skill (Part 4)

**Files:**
- Modify: `skills/engine-benchmarker/SKILL.md` (append)

**Step 1: Append the report generation section**

Append to the end of `skills/engine-benchmarker/SKILL.md`:

````markdown

### Phase 5: Report Generation

Generate all output files in the output directory (default: `<engine-path>/benchmarks/<benchmark>/<timestamp>/`).

#### Output Directory Structure

```
benchmarks/
├── <benchmark>/
│   └── <YYYY-MM-DDTHH-MM-SS>/
│       ├── benchmark-report.md     # Full scored report
│       ├── vvc-delta.md            # VVC on vs off comparison
│       ├── scores.json             # Machine-readable scores
│       └── raw/                    # Raw engine outputs per query
│           ├── query-001-vvc-on/
│           │   └── output.md
│           ├── query-001-vvc-off/
│           │   └── output.md
│           ├── query-002-vvc-on/
│           │   └── output.md
│           └── ...
```

#### benchmark-report.md Template

```markdown
# Benchmark Report: {engine-name}

## Summary
- **Benchmark:** {benchmark} ({subset or "all"})
- **Engine:** {engine-name} v{version}
- **Tier:** {tier} (auto-selected | override)
- **Queries:** {N} (VVC delta: {enabled | disabled})
- **Date:** {timestamp}

## Overall Score

| Metric | VVC On | VVC Off | Delta | Delta % |
|--------|--------|---------|-------|---------|
| Overall | X% | Y% | +Z% | +W% |
| {metric 1} | ... | ... | ... | ... |
| {metric 2} | ... | ... | ... | ... |
| ... | ... | ... | ... | ... |

## Comparison to Published Baselines

> Only shown for DRACO benchmark. Omit for self-eval and reportbench.

| System | Score |
|--------|-------|
| **This engine (VVC on)** | **X%** |
| This engine (VVC off) | Y% |
| Perplexity Deep Research | 70.5% |
| Gemini Deep Research | 59.0% |
| OpenAI o3 Deep Research | 52.1% |

## Per-Query Scores

### Query 1: "{query text}"

| Metric | VVC On | VVC Off | Delta |
|--------|--------|---------|-------|
| {metric} | {score} | {score} | {delta} |
| ... | ... | ... | ... |

**Notes:** {LLM-as-judge observations}

### Query 2: "{query text}"
...

## VVC Delta Analysis

### Correction Categories
| Category | Count | % of Claims |
|----------|-------|-------------|
| CONFIRMED | N | X% |
| PARAPHRASED | N | X% |
| OVERSTATED | N | X% |
| UNDERSTATED | N | X% |
| DISPUTED | N | X% |
| UNSUPPORTED | N | X% |

### Key Findings
- {Summary of what VVC caught}
- {Source credibility improvements}
- {Most common correction type}
```

#### vvc-delta.md Template

```markdown
# VVC Delta Report: {engine-name}

## Overview
- VVC-on overall: X%
- VVC-off overall: Y%
- **Net improvement: +Z% (+W%)**

## Per-Metric Delta
| Metric | VVC On | VVC Off | Delta | Interpretation |
|--------|--------|---------|-------|----------------|
| ... | ... | ... | ... | ... |

## Claim-Level Detail
| Query | Claim | VVC Status | Source Tier | Correction |
|-------|-------|------------|-------------|------------|
| ... | ... | ... | ... | ... |
```

#### scores.json Schema

```json
{
  "engineName": "string",
  "engineVersion": "string",
  "benchmark": "draco|reportbench|self-eval",
  "subset": "string|null",
  "tier": "string",
  "vvcDelta": true,
  "timestamp": "ISO-8601",
  "queries": [
    {
      "id": "query-001",
      "text": "string",
      "tier": "string",
      "status": "completed|failed",
      "scores": {
        "vvcOn": { "metric1": 0.0, "overall": 0.0 },
        "vvcOff": { "metric1": 0.0, "overall": 0.0 },
        "delta": { "metric1": 0.0, "overall": 0.0 }
      }
    }
  ],
  "aggregate": {
    "vvcOn": { "metric1": 0.0, "overall": 0.0 },
    "vvcOff": { "metric1": 0.0, "overall": 0.0 },
    "delta": { "metric1": 0.0, "overall": 0.0 }
  },
  "baselines": {
    "perplexity": 70.5,
    "gemini": 59.0,
    "openai_o3": 52.1
  }
}
```

### Phase 6: Scoreboard Update

After generating per-engine results, update the central scoreboard.

Check if `benchmarks/SCOREBOARD.md` exists at the engine path. If not, create it with the header:

```markdown
# Benchmark Scoreboard

| Engine | Benchmark | Subset | Score (VVC On) | Score (VVC Off) | VVC Delta | Date | Baseline |
|--------|-----------|--------|----------------|-----------------|-----------|------|----------|
```

Append a new row for this benchmark run:

```markdown
| {engine-name} | {benchmark} | {subset} | {overall-vvc-on}% | {overall-vvc-off}% | +{delta}% | {YYYY-MM-DD} | {baseline or "--"} |
```

Baseline column shows the closest published baseline score for context (DRACO only).

### Phase 7: Summary Output

Display a terminal-friendly summary to the user:

```
Benchmark complete: {engine-name} ({benchmark}, {subset})

Overall Score (VVC On):  {X}%
Overall Score (VVC Off): {Y}%
VVC Delta:               +{Z}% improvement

Queries: {completed}/{total} completed ({failed} failed)

Results saved to: {output-dir}/
Scoreboard updated: {engine-path}/benchmarks/SCOREBOARD.md

{If DRACO: "vs. Perplexity 70.5% | Gemini 59.0% | OpenAI o3 52.1%"}
```
````

**Step 2: Verify all phases exist**

Run: `grep -c "^### Phase" skills/engine-benchmarker/SKILL.md` (from the engine-creator directory)
Expected: 7 (Phase 1 through Phase 7)

**Step 3: Verify total file length is reasonable**

Run: `wc -l skills/engine-benchmarker/SKILL.md` (from the engine-creator directory)
Expected: ~300-350 lines

**Step 4: Commit**

```bash
git add deep-research-engine-creator/skills/engine-benchmarker/SKILL.md
git commit -m "feat(benchmark): add report generation and scoreboard to engine-benchmarker skill

Phases 5-7: benchmark-report.md template, vvc-delta.md template,
scores.json schema, central SCOREBOARD.md management, terminal summary.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 6: Update plugin.json Version

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1: Bump version to 1.3.0**

In `.claude-plugin/plugin.json`, change:
```json
"version": "1.2.0",
```
to:
```json
"version": "1.3.0",
```

**Step 2: Verify the change**

Run: `grep '"version"' .claude-plugin/plugin.json` (from the engine-creator directory)
Expected: `"version": "1.3.0",`

**Step 3: Commit**

```bash
git add deep-research-engine-creator/.claude-plugin/plugin.json
git commit -m "chore: bump version to 1.3.0 for benchmark-engine release

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 7: Update CHANGELOG.md

**Files:**
- Modify: `CHANGELOG.md`

**Step 1: Add v1.3.0 entry**

Insert after line 6 (`## [1.2.0] - 2026-02-22`), before the existing v1.2.0 entry:

```markdown
## [1.3.0] - 2026-02-22

### Added
- **`/benchmark-engine` command** — benchmark generated research engines against published deep research benchmarks with VVC delta analysis and scored reports
  - Three benchmark modes: `self-eval` (engine's own sample questions), `draco` (Perplexity's 100-task, 10-domain benchmark), `reportbench` (ByteDance's arXiv survey gold standards)
  - VVC delta analysis: runs each query twice (VVC on/off) to quantify verification impact on citation accuracy, factual correctness, and hallucination reduction
  - Subprocess execution: tests the real plugin stack end-to-end via `claude -p`
  - Tier auto-selection: maps benchmark difficulty to appropriate research tiers, with `--tier` override
  - Cost control: `--limit N` caps queries, `--no-vvc-delta` halves runs, `--subset` filters by domain
  - Published baselines: compares against Perplexity (70.5%), Gemini (59.0%), and OpenAI o3 (52.1%) on DRACO
  - Dual output: per-engine timestamped results + central `SCOREBOARD.md` for cross-engine comparison
  - Machine-readable `scores.json` for programmatic analysis
- **Engine Benchmarker skill** (`skills/engine-benchmarker/SKILL.md`) — full benchmark logic: dataset management, execution pipeline, LLM-as-judge scoring, report generation

```

**Step 2: Verify the entry was added**

Run: `head -20 CHANGELOG.md` (from the engine-creator directory)
Expected: v1.3.0 entry appears before v1.2.0

**Step 3: Commit**

```bash
git add deep-research-engine-creator/CHANGELOG.md
git commit -m "docs: add v1.3.0 changelog entry for benchmark-engine

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 8: Update README.md Commands Table

**Files:**
- Modify: `README.md`

**Step 1: Add benchmark-engine to the commands table**

Find the commands table (around line 102-108). Add a new row after the `/list-engines` row:

```markdown
| `/benchmark-engine <path> [flags]` | Benchmark an engine against DRACO, ReportBench, or self-eval with VVC delta analysis |
```

The table should now read:

```markdown
| Command | Description |
|---------|-------------|
| `/create-engine [--preset name]` | Main wizard -- interviews you and generates a complete engine plugin |
| `/update-engine <path>` | Re-configure specific sections of an existing engine |
| `/test-engine <path> [topic]` | Validate structure and run smoke test on a generated engine |
| `/preview-engine <path>` | Preview what an engine config would generate (read-only) |
| `/list-engines [dir]` | Scan a directory for generated engines and display a summary table |
| `/benchmark-engine <path> [flags]` | Benchmark an engine against DRACO, ReportBench, or self-eval with VVC delta analysis |
```

**Step 2: Verify the table has 6 command rows**

Run: `grep -c "^| \`/" README.md` (from the engine-creator directory)
Expected: 6

**Step 3: Commit**

```bash
git add deep-research-engine-creator/README.md
git commit -m "docs: add benchmark-engine to README commands table

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 9: Final Verification and Squash Commit

**Step 1: Verify all new files exist**

Run from the engine-creator directory:
```bash
ls -la commands/benchmark-engine.md skills/engine-benchmarker/SKILL.md
```
Expected: both files exist

**Step 2: Verify plugin.json version**

Run: `grep version .claude-plugin/plugin.json`
Expected: `"version": "1.3.0"`

**Step 3: Verify changelog has v1.3.0**

Run: `grep "1.3.0" CHANGELOG.md`
Expected: `## [1.3.0]` line found

**Step 4: Verify README commands table**

Run: `grep benchmark-engine README.md`
Expected: command table row found

**Step 5: Run the existing `/test-engine` command mentally**

The benchmark-engine command is a NEW command — it doesn't modify any existing command or skill. The existing plugin should still pass all tests. No regressions expected.

**Step 6: Push to standalone repo**

Run `/push-subproject` to sync the changes to the standalone GitHub repo.
