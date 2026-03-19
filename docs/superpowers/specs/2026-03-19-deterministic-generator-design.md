# Deterministic Python Generator & Enhanced Observability — Design Spec

**Date:** 2026-03-19
**Status:** Draft
**Scope:** Replace LLM-driven file generation with a deterministic Python script; enhance dashboard with granular agent visibility

## Problem Statement

The engine creator uses the LLM as its template engine — SKILL.md instructs Claude to read `.tmpl` files, substitute placeholders, and write output. This is unreliable:

1. **Non-deterministic output.** Same config can produce slightly different files across runs. The LLM may rephrase, reformat, or skip content.
2. **Skipped steps.** The model can miss generation steps entirely (v1.8.0: Step 8f was skipped because the preamble said "8a-8e" instead of "8a-8f"). A code generator never forgets to write a file.
3. **Expensive validation.** The `/test-engine` suite exists primarily because LLM output can't be trusted — placeholder residue scans, file existence checks, line count limits. A deterministic generator makes most of these checks unnecessary.
4. **Wasted tokens.** Template substitution is mechanical string replacement. Using the most expensive tool (an LLM) for work that `str.replace()` handles is wasteful.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Wizard interview | Stays as LLM conversation | Benefits from LLM judgment (sample question analysis, agent suggestions, contextual recommendations) |
| File generation | Python script | Deterministic, testable, guaranteed file completeness |
| Creative content | LLM pre-computes, stores in `config._derived` | Clean split: LLM handles judgment, Python handles mechanics |
| Generator structure | Single file (`generate.py`) | 74 rules is manageable in one file; premature modularity adds complexity |
| Template engine | Custom `{{key}}` substitution | Zero dependencies; Jinja2 adds a pip requirement and syntax migration |
| Invocation | LLM runs `python3 generate.py config.json ./output/` via Bash | Single command, validate-then-generate, clear error codes |
| Old generation path | Removed entirely | Maintaining two paths guarantees divergence |
| Test changes | Drop impossible-to-fail checks, keep semantic checks | Script guarantees file completeness and placeholder substitution |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  SKILL.md Wizard (LLM)                                     │
│                                                             │
│  Sections 1-9: Interview → engine-config.json               │
│  Derived Content: Compute _derived section                  │
│  Preview: Show user what will be generated                  │
│  Invoke: python3 generate.py config.json ./output/          │
└────────────┬────────────────────────────────────────────────┘
             │ engine-config.json (with _derived)
             ▼
┌─────────────────────────────────────────────────────────────┐
│  generate.py (Python, zero dependencies)                    │
│                                                             │
│  1. load_config(path)        → dict                         │
│  2. validate(config)         → pass or sys.exit(1)          │
│  3. derive_placeholders(config) → dict (70+ rules)          │
│  4. generate_files(config, placeholders, output_dir)        │
│     - Read each .tmpl file                                  │
│     - Substitute {{placeholders}}                           │
│     - Write output files                                    │
│  5. verify_output(output_dir) → pass or sys.exit(2)         │
│  6. print_summary()                                         │
└────────────┬────────────────────────────────────────────────┘
             │ Deterministic output
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Generated Engine (self-contained mode)                      │
│  .claude-plugin/plugin.json                                 │
│  commands/research.md, sources.md                           │
│  agents/{agentId}.md (one per agent)                        │
│  skills/{name}/SKILL.md, standards.md, research-protocol.md │
│  skills/{name}/provenance.md, vvc-pipeline.md (if VVC)      │
│  skills/{name}/dashboard-server.js, dashboard.html          │
│  README.md                                                  │
│                                                             │
│  Generated Engine (extension mode)                          │
│  .claude-plugin/plugin.json                                 │
│  commands/research.md, sources.md                           │
│  agents/{agentId}.md (one per agent)                        │
│  skills/{name}/SKILL.md (from extension template)           │
│  README.md                                                  │
└─────────────────────────────────────────────────────────────┘
```

## Section 1: Generator Script

### File: `plugin/generator/generate.py`

**Interface:**
```
python3 plugin/generator/generate.py <config-path> <output-dir>
```

**Exit codes:**
- `0` — success, all files generated
- `1` — validation error (config malformed, missing required fields)
- `2` — template error (template file not found, substitution failure)

**Stdout:** progress log (one line per file written), final summary count.
**Stderr:** errors and warnings.

### Function Structure

```python
def main(config_path: str, output_dir: str) -> None:
    config = load_config(config_path)
    validate(config)
    placeholders = derive_placeholders(config)
    generate_files(config, placeholders, output_dir)
    verify_output(output_dir, config)
    print_summary(output_dir)

def load_config(path: str) -> dict:
    """Read and parse engine-config.json."""

def validate(config: dict) -> None:
    """Check required fields, types, relational constraints.
    Exits with code 1 and descriptive error on failure."""

def derive_placeholders(config: dict) -> dict:
    """Apply all 70+ mechanical derivation rules.
    Returns flat dict: placeholder name → substitution value."""

def substitute(template: str, placeholders: dict) -> str:
    """Replace all {{key}} occurrences in template string.
    Warns on any unresolved {{...}} remaining after substitution."""

def generate_files(config: dict, placeholders: dict, output_dir: str) -> None:
    """Create directories, read templates, substitute, write output files."""

def verify_output(output_dir: str, config: dict) -> None:
    """Post-generation check: all expected files exist and are non-empty.
    Exits with code 2 if any file is missing."""

def print_summary(output_dir: str) -> None:
    """List all generated files with sizes."""
```

### Template Discovery

Templates are located relative to the script at `../skills/engine-creator/templates/`. Resolved at runtime:

```python
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, '..', 'skills', 'engine-creator', 'templates')
```

### Substitution Behavior

The `substitute()` function performs simple string replacement:

```python
def substitute(template: str, placeholders: dict) -> str:
    result = template
    for key, value in placeholders.items():
        result = result.replace('{{' + key + '}}', str(value))
    # Warn about unresolved placeholders
    remaining = re.findall(r'\{\{[a-zA-Z0-9_-]+\}\}', result)
    if remaining:
        print(f"WARNING: unresolved placeholders: {remaining}", file=sys.stderr)
    return result
```

No Jinja2, no template engine. Raw string replacement. The warning catches any derivation rules that were missed.

## Section 2: Wizard Changes

### Config Assembly: New `_derived` Section

After assembling `engine-config.json` (current "Config Assembly" section in SKILL.md) and before the preview, the LLM computes creative content and stores it in `config._derived`:

```
## Derived Content Generation

Before preview, compute creative/contextual content that requires LLM judgment
and store in config._derived:

1. For each agent in agentPipeline.agents:
   - Determine isVvcAgent (id === "vvc-specialist")
   - Generate agentExamplesBlock: 3 domain-specific examples using <example> XML blocks
     - VVC agent: verification-specific examples
     - Research agents: research-specific examples with domain terms
   - Generate agentBodyBlock:
     - VVC agent: Verification Protocol, WebFetch Budget, Output Format, Context Discipline
     - Research agents: Search Protocol, Confidence Scoring, Output Format, Context Discipline
   - Generate agentFirstActionsBlock:
     - VVC agent: read vvc-pipeline.md, standards.md, draft report
     - Research agents: read standards.md, research-protocol.md, research outline
2. Generate scopeDisciplineBlock: both standalone and --extend variants,
   incorporating domain-specific terminology
3. Set operationalLessons: "No entries yet -- update after first research run with /post-mortem."

Store all values in engine-config.json under "_derived" key.
```

### Generation Step Replacement

Steps 1-7 (directory creation, plugin.json, engine-config.json, commands, sources, agent files) and Steps 8a-8f (skill files, dashboard files) and Step 9 (README) are ALL replaced with a single step:

```
**Step 8 -- Generate engine files.** Run the generator script:

    python3 ${CLAUDE_PLUGIN_ROOT}/generator/generate.py {OUTPUT_DIR}/engine-config.json {OUTPUT_DIR}

The script reads engine-config.json (including _derived content), loads all templates,
performs placeholder substitution, and writes every output file deterministically.

If the script exits with error code 1 (validation), review the error message and fix
the config. Re-run the script.
If exit code 2 (template error), report the error to the user.
If exit code 0, proceed to Post-Generation.
```

Note: The LLM still writes `engine-config.json` to `{OUTPUT_DIR}/` before invoking the script. The script reads it as input.

### Post-Generation Simplified

Drop the manual file verification checklist (the script's `verify_output()` does this). Keep:
- Suggest `/test-engine` for semantic validation
- Copy install command
- Suggest publish

## Section 3: File Generation Mapping

The script generates ALL files. It reads `config.engineMeta.mode` to determine the output mode.

### Self-Contained Mode (mode: "self-contained")

| Template | Output | Key Placeholders |
|----------|--------|-----------------|
| `plugin-json.tmpl` | `.claude-plugin/plugin.json` | engineName, engineDescription, authorName, authorEmail, keywords |
| `command-template.md.tmpl` | `commands/research.md` | tierSummary, vvcArgumentHint, engineName, skillDirName |
| `sources-command-template.md.tmpl` | `commands/sources.md` | sourceHierarchyTable, searchTemplatesTable, filters |
| `agent-template.md.tmpl` | `agents/{agentId}.md` (loop) | agentId, agentRole, agentSpecialization, agentExamplesBlock*, agentBodyBlock*, agentFirstActionsBlock*, sourceHierarchy, promptOverride, color, tools |
| `orchestrator-skill.md.tmpl` | `skills/{name}/SKILL.md` | All orchestrator placeholders (~40) |
| `standards.md.tmpl` | `skills/{name}/standards.md` | Confidence levels, tier names/sources, citation management fields, VVC taxonomy summary |
| `research-protocol.md.tmpl` | `skills/{name}/research-protocol.md` | Search templates, iteration limits, WebFetch cap, token budgets |
| `provenance.md.tmpl` | `skills/{name}/provenance.md` | Audit tier behavior, reverifiable default, chain format |
| `vvc-pipeline.md.tmpl` | `skills/{name}/vvc-pipeline.md` | VVC claim types, verification scope, tier behavior (only when VVC enabled) |
| `dashboard-server.js.tmpl` | `skills/{name}/dashboard-server.js` | dashboardPort |
| `dashboard.html.tmpl` | `skills/{name}/dashboard.html` | None (no placeholders, but UI enhanced in Section 7) |
| `readme-template.md.tmpl` | `README.md` | agentTable, sourceTable, sampleQuestions, qualitySummary, mode, createdAt, outputFiles |

\* Per-agent values from `config._derived`

### Extension Mode (mode: "extension")

Extension mode produces fewer files — the core pipeline is inherited from the base `/deep-research` plugin.

| Template | Output | Key Placeholders |
|----------|--------|-----------------|
| `plugin-json.tmpl` | `.claude-plugin/plugin.json` | Same as self-contained |
| `command-template.md.tmpl` | `commands/research.md` | Same as self-contained |
| `sources-command-template.md.tmpl` | `commands/sources.md` | Same as self-contained |
| `agent-template.md.tmpl` | `agents/{agentId}.md` (loop) | Same as self-contained |
| `extension-skill.md.tmpl` | `skills/{name}/SKILL.md` | baseSkillPath, tier/source/confidence/citation overrides (~30 placeholders) |
| `readme-template.md.tmpl` | `README.md` | Same as self-contained |

Extension mode does NOT generate: `standards.md`, `research-protocol.md`, `provenance.md`, `vvc-pipeline.md`, `dashboard-server.js`, `dashboard.html`. These are inherited from the base plugin.

### Mode Branching in `generate.py`

```python
def generate_files(config, placeholders, output_dir):
    mode = config["engineMeta"]["mode"]
    # Common files (both modes)
    generate_plugin_json(...)
    generate_commands(...)
    generate_agents(...)
    generate_readme(...)
    if mode == "self-contained":
        generate_skill_files(...)  # orchestrator + standards + protocol + provenance + VVC + dashboard
    elif mode == "extension":
        generate_extension_skill(...)  # single SKILL.md from extension template
```

**Directory creation:** The script creates `.claude-plugin/`, `commands/`, `agents/`, `skills/{engineName}/` under the output directory.

**`engine-config.json`:** Written by the LLM before script invocation. The script reads it as input only.

**`plugin-manifest-schema.json`:** Used only by `/test-engine` for validation. The script does not use it.

## Section 4: Derivation Rules

The `derive_placeholders(config)` function returns a flat `dict[str, str]`. Rules grouped by type:

### Direct Config Reads (~20 rules)

| Placeholder | Source |
|-------------|--------|
| `{{engineName}}` | `config.engineMeta.name` |
| `{{engineDisplayName}}` | `config.engineMeta.displayName` |
| `{{domain}}` | `config.engineMeta.domain` |
| `{{audience}}` | `config.engineMeta.audience` |
| `{{engineVersion}}` | `config.engineMeta.version` |
| `{{maxIterations}}` | `config.advanced.maxIterationsPerQuestion` (default: 3) |
| `{{explorationDepth}}` | `config.advanced.explorationDepth` (default: 2) |
| `{{maxWebFetches}}` | `config.advanced.maxWebFetchesPerAgent` (default: 10) |
| `{{dashboardPort}}` | `config.advanced.dashboardPort` (default: 3847) |
| `{{planningBudget}}` | `config.advanced.tokenBudgets.planning` (default: 2000) |
| `{{researchBudget}}` | `config.advanced.tokenBudgets.research` (default: 15000) |
| `{{synthesisBudget}}` | `config.advanced.tokenBudgets.synthesis` (default: 8000) |
| `{{reportingBudget}}` | `config.advanced.tokenBudgets.reporting` (default: 10000) |
| `{{provenanceBudget}}` | `config.advanced.tokenBudgets.provenance` (default: 5000) |
| `{{citationStandard}}` | `config.qualityFramework.citationStandard` |
| `{{reportOutputDir}}` | `config.outputStructure.reportOutputDir` |
| `{{fileNaming}}` | `config.outputStructure.fileNaming` |
| `{{comprehensiveFollowUpAgentCap}}` | `config.advanced.comprehensiveFollowUpAgentCap` (default: 2) |
| `{{reportingTone}}` | `config.prompts.reportingTone` |
| `{{globalPreamble}}` | `config.prompts.globalPreamble` |
| `{{confidenceHigh}}` | `config.qualityFramework.confidenceScoring.HIGH` |
| `{{confidenceMedium}}` | `config.qualityFramework.confidenceScoring.MEDIUM` |
| `{{confidenceLow}}` | `config.qualityFramework.confidenceScoring.LOW` |
| `{{confidenceSpeculative}}` | `config.qualityFramework.confidenceScoring.SPECULATIVE` |
| `{{minimumEvidence}}` | `config.qualityFramework.minimumEvidence` |
| `{{tier1Name}}` | `config.sourceStrategy.credibilityTiers.tier1.name` |
| `{{tier1Sources}}` | `config.sourceStrategy.credibilityTiers.tier1.sources` (joined) |
| `{{tier2Name}}` | `config.sourceStrategy.credibilityTiers.tier2.name` |
| `{{tier2Sources}}` | `config.sourceStrategy.credibilityTiers.tier2.sources` (joined) |
| `{{tier3Name}}` | `config.sourceStrategy.credibilityTiers.tier3.name` |
| `{{tier3Sources}}` | `config.sourceStrategy.credibilityTiers.tier3.sources` (joined) |
| `{{tier4Name}}` | `config.sourceStrategy.credibilityTiers.tier4.name` |
| `{{tier4Sources}}` | `config.sourceStrategy.credibilityTiers.tier4.sources` (joined) |
| `{{tier5Name}}` | `config.sourceStrategy.credibilityTiers.tier5.name` |
| `{{tier5Sources}}` | `config.sourceStrategy.credibilityTiers.tier5.sources` (joined) |
| `{{verificationMode}}` | `config.qualityFramework.citationManagement.verificationMode` |
| `{{urlLivenessCheck}}` | `config.qualityFramework.citationManagement.urlLivenessCheck` |
| `{{contentClaimMatching}}` | `config.qualityFramework.citationManagement.contentClaimMatching` |
| `{{sourceFreshnessThreshold}}` | `config.qualityFramework.citationManagement.sourceFreshnessThreshold` |
| `{{deadLinkHandling}}` | `config.qualityFramework.citationManagement.deadLinkHandling` |
| `{{probeOnDiscovery}}` | `config.qualityFramework.citationManagement.probeOnDiscovery` |
| `{{skillDirName}}` | `config.engineMeta.name` (same as engineName) |
| `{{mode}}` | `config.engineMeta.mode` ("self-contained" or "extension") |
| `{{createdAt}}` | `config.engineMeta.createdAt` |
| `{{baseSkillPath}}` | `config.engineMeta.baseSkillPath` (extension mode only) |
| `{{engineDescription}}` | `config.engineMeta.description` |
| `{{authorName}}` | `config.engineMeta.author.name` (default: empty) |
| `{{authorEmail}}` | `config.engineMeta.author.email` (default: empty, see special handling) |

### Formatted Outputs (~30 rules)

Built by iterating config structures and emitting markdown:

| Placeholder | Logic |
|-------------|-------|
| `{{tierConfigTable}}` | Iterate `config.agentPipeline.tiers`, emit one markdown table row per tier with columns: Tier, Planning, Research Agents (fully qualified), Synthesis, Report, Provenance, User Gate |
| `{{agentDeploymentBlocks}}` | For each agent: emit `#### Agent: [role]\n\nDeploy **{engineName}:[id]**` block with specialization and prompt override |
| `{{subAgentList}}` | Built-in agents (planning, synthesis, reporting) + custom agents as bullet list. VVC specialist appended if VVC enabled |
| `{{fileStructure}}` | Per-agent: `├── [TOPIC_SLUG]_Claims_[agentId].md` + bibliography line |
| `{{reportSections}}` | `config.outputStructure.reportSections` as numbered markdown list |
| `{{preferredSites}}` | `config.sourceStrategy.preferredSources` as bullet list |
| `{{excludedSources}}` | `config.sourceStrategy.excludedSources` as bullet list |
| `{{additionalSearchTemplates}}` | `config.sourceStrategy.searchTemplates` formatted as numbered list |
| `{{sourceHierarchy}}` | All 5 tiers formatted as text block |
| `{{validationRules}}` | `config.qualityFramework.validationRules` as numbered list |
| `{{specialDeliverables}}` | `config.outputStructure.specialDeliverables` as bullet list |
| `{{sampleQuestions}}` | `config.sampleQuestions` as numbered list |
| `{{agentTable}}` | Agent pipeline as markdown table for README |
| `{{sourceTable}}` | Source hierarchy as markdown table for README |
| `{{qualitySummary}}` | Brief text from quality framework for README |
| `{{agentSpecialization}}` | All agent specializations joined by "; " |
| `{{synthesisInstructions}}` | `config.prompts.synthesisInstructions` |
| `{{agentOverrides}}` | `config.prompts.agentOverrides` formatted per-agent |
| `{{quickTierDescription}}` | "Single-agent lookup using [first agent role]" |
| `{{standardTierDescription}}` | "[N] agents: [role1], [role2]" |
| `{{deepTierDescription}}` | "Full pipeline with [N] agents: [roles]" |
| `{{comprehensiveTierDescription}}` | "All [N] agents + follow-up round" |
| `{{quickAgentId}}` | `{engineName}:{first agent from quick tier}` |
| `{{tierSummary}}` | Markdown table for command help |
| `{{sourceHierarchyTable}}` | Formatted table for sources command |
| `{{searchTemplatesTable}}` | Formatted table for sources command |
| `{{keywords}}` | `config.engineMeta.keywords` as quoted comma-separated |
| `{{verificationModeInstructions}}` | Expand from `citationManagement.verificationMode`: "none" → trust text, "spot-check" → sample HIGH, "comprehensive" → verify all |
| `{{deadLinkInstructions}}` | Expand from `citationManagement.deadLinkHandling`: "flag-only" → tag, "archive-fallback" → Wayback, "exclude-from-high" → downgrade |
| `{{verificationReportConfig}}` | If `verificationReport.enabled`: generate scope text; else: "disabled" |
| `{{filters}}` | `config.sourceStrategy.filters` formatted as text block |
| `{{outputFiles}}` | List of output files for README based on mode and VVC config |
| `{{tools}}` | Per-agent tool list from `config.agentPipeline.agents[i].tools` (joined) |

### Conditional Blocks (~15 rules)

All follow the pattern: if VVC enabled → content, else → empty string.

| Placeholder | Content When VVC Enabled |
|-------------|------------------------|
| `{{vvcPhaseLines}}` | Phase 5-6 table rows |
| `{{vvcClaimTaggingInstructions}}` | Claim tagging paragraph with [VC]/[PO]/[IE] |
| `{{vvcVerifyPhaseBlock}}` | Complete Phase 5 section |
| `{{vvcCorrectPhaseBlock}}` | Complete Phase 6 section |
| `{{vvcFileStructure}}` | Draft report + VVC files in tree |
| `{{vvcFeatureBullets}}` | Feature list bullets |
| `{{vvcBudgetLine}}` | Token budget line |
| `{{vvcSubAgentNote}}` | Pipeline agent note |
| `{{vvcExtensionOverride}}` | Extension VVC config block |
| `{{vvcTierNote}}` | Tier behavior note |
| `{{vvcReadmeSection}}` | README VVC section |
| `{{vvcArgumentHint}}` | ` [--no-vvc]` |
| `{{vvcClaimTaxonomyBlock}}` | Full claim taxonomy table |
| `{{vvcClaimTaxonomySummary}}` | Brief cross-reference to vvc-pipeline.md |

### Computed Values (~10 rules)

| Placeholder | Computation |
|-------------|------------|
| `{{pipelinePhaseCount}}` | "seven" if VVC, "five" if not |
| `{{pipelinePhaseDescription}}` | "seven-phase" if VVC, "five-phase" if not |
| `{{phase4Name}}` | "Draft Reporting" if VVC, "Professional Reporting" if not |
| `{{phase4Description}}` | Conditional description |
| `{{phase4ReportType}}` | "draft" if VVC, "final" if not |
| `{{phase4OutputFile}}` | "Draft_Report.md" if VVC, "Comprehensive_Report.md" if not |
| `{{vvcWebFetchCap}}` | `min(maxWebFetchesPerAgent * 3, 50)` |
| `{{agentPrefix}}` | First char of agent ID, uppercased |
| `{{auditTierBehavior}}` | "Standard: run | Deep: run | Comprehensive: run" from tier list |
| `{{provenanceTierColumn}}` | "Hash-only" for Quick, "Hash + Audit" for audit tiers |
| `{{reverifiableDefault}}` | From config provenance setting |

### From `_derived` (~5 rules)

Passed through verbatim from `config._derived`. For optional fields with defaults (e.g., `operationalLessons`), the script uses `config._derived.get(key, default_value)`:

| Placeholder | Source |
|-------------|--------|
| `{{agentExamplesBlock}}` | `config._derived.agentExamplesBlocks[agentId]` (per-agent) |
| `{{agentBodyBlock}}` | `config._derived.agentBodyBlocks[agentId]` (per-agent) |
| `{{agentFirstActionsBlock}}` | `config._derived.agentFirstActionsBlocks[agentId]` (per-agent) |
| `{{scopeDisciplineBlock}}` | `config._derived.scopeDisciplineBlock` |
| `{{operationalLessons}}` | `config._derived.operationalLessons` |

### Per-Agent Loop

Agent files are generated in a loop. For each agent in `config.agentPipeline.agents`:

1. Determine `isVvcAgent` = (agent.id === "vvc-specialist")
2. Build agent-specific placeholders: `{{agentId}}`, `{{agentRole}}`, `{{agentSpecialization}}`, `{{model}}`, `{{color}}` (cycled: blue, magenta, yellow), `{{tools}}`
3. Pull per-agent `_derived` blocks based on agent ID
4. Pull `{{promptOverride}}` from `config.prompts.agentOverrides[agentId]` if present
5. For VVC agent: use `{{vvcWebFetchCap}}` instead of `{{maxWebFetches}}`
6. Substitute into `agent-template.md.tmpl`, write to `agents/{agentId}.md`

### Special Handling: plugin.json Author Email

If `config.engineMeta.author.email` is empty or absent, the entire `"email": "..."` line must be removed from the generated plugin.json (not emitted as empty string). The script handles this as a post-substitution fixup.

## Section 5: Test Changes

### Checks Removed

These checks become unnecessary because the script guarantees them:

| Check | Reason for Removal |
|-------|-------------------|
| 4f (placeholder residue scan) | Script warns on unresolved placeholders; substitution is deterministic |
| 4k (SKILL.md line count) | Script output is deterministic from template |
| 4l (no per-fetch hashing) | Template content is fixed |
| 4m (no shared file writes) | Template content is fixed |
| 4p (dashboard assets present) | Script always writes them |

### Checks Kept

| Check | Reason |
|-------|--------|
| 1 (plugin structure) | Lighter confirmation — still useful as smoke test |
| 2 (YAML frontmatter) | Validates template content correctness |
| 3 (agent definitions) | Validates config-to-file mapping |
| 4a-schema (JSON Schema) | Config structure validation |
| 4a-4e (structural checks) | Config relational integrity |
| 4g (preset validation) | Preset structure |
| 4h (citation management) | Config semantics |
| 4i (VVC validation) | Config semantics — VVC agent not in tier arrays |
| 4j (provenance validation) | Config semantics |
| 4n (status protocol) | Template content verification |
| 4o (agent constraints) | Template content verification |
| 4q (pipeline status init) | Template content verification |
| 4r (output verification) | Template content verification |
| 5 (quick smoke test) | Functional test |

### Schema Updates

`engine-config-schema.json` gains a `_derived` object as a required top-level key:

```json
"_derived": {
  "type": "object",
  "description": "Pre-computed content generated by the LLM during the wizard interview. The Python generator reads these values verbatim during file generation.",
  "required": ["agentExamplesBlocks", "agentBodyBlocks", "agentFirstActionsBlocks", "scopeDisciplineBlock"],
  "additionalProperties": false,
  "properties": {
    "agentExamplesBlocks": {
      "type": "object",
      "description": "Per-agent example blocks keyed by agent ID. Each value is a complete markdown string with 3 domain-specific examples.",
      "additionalProperties": { "type": "string" }
    },
    "agentBodyBlocks": {
      "type": "object",
      "description": "Per-agent body blocks keyed by agent ID. Contains search protocol, confidence scoring, output format, and context discipline sections.",
      "additionalProperties": { "type": "string" }
    },
    "agentFirstActionsBlocks": {
      "type": "object",
      "description": "Per-agent first actions blocks keyed by agent ID. Contains the ordered list of files the agent reads on startup.",
      "additionalProperties": { "type": "string" }
    },
    "scopeDisciplineBlock": {
      "type": "string",
      "description": "Conditional scope discipline instructions containing both standalone and --extend variants with domain-specific terminology."
    },
    "operationalLessons": {
      "type": "string",
      "description": "Operational lessons section content. Defaults to placeholder text for new engines.",
      "default": "No entries yet -- update after first research run with `/post-mortem`."
    }
  }
}
```

`preset-schema.json` does NOT gain `_derived` — presets are partial configs and `_derived` content is computed per-engine during the wizard.

## Section 6: Migration and Backward Compatibility

**Existing generated engines:** Unaffected. Their files are static on disk.

**Existing `engine-config.json` without `_derived`:** Cannot be used with `generate.py` directly — validation will fail. Two migration paths:

1. **Re-run wizard.** `/create-engine` with existing config loads it, LLM computes `_derived`, saves updated config, runs script.
2. **`/update-engine` migration.** If the LLM detects a config without `_derived`, it computes the derived content and adds it before invoking the script.

**Domain presets:** No changes needed. Presets don't include `_derived`.

**Old generation path:** Removed entirely. Steps 8a-8f (LLM-driven generation) are replaced with a single script invocation. No fallback path maintained — two generation paths would inevitably diverge.

## Files Changed

**(Superseded by the Updated Files Changed table at the end of this document — see Section 7g.)**

---

## Section 7: Enhanced Observability

This section describes changes to the v1.8.0 observability system. These are template-level changes that the Python generator will pick up automatically (it reads templates as-is).

### 7a: Live Action Tracking

**Problem:** Agents only update status at research question boundaries. The `currentQuestion` field stays static for long stretches while the agent executes multiple search queries, fetches, and assessments.

**Change target:** `templates/research-protocol.md.tmpl` — Agent Status Protocol section

**Add `currentAction` field** to the status JSON schema:

```json
{
  "agentId": "[AgentID]",
  "engineId": "${ENGINE_ID}",
  "phase": 2,
  "status": "researching | writing | assessing | refining | complete | error",
  "currentQuestion": "The research question currently being worked on",
  "currentAction": "Searching 'constructive dismissal Ontario 2024 site:canlii.org'",
  "questionsCompleted": 2,
  "questionsTotal": 5,
  "activity": "searching | assessing | refining | writing | idle",
  "webFetchesUsed": 4,
  "webFetchCap": 10,
  "claimsFound": 7,
  "sourcesCollected": 4,
  "iterationPass": 2,
  "maxIterations": 3,
  "lastUpdated": "ISO-8601 timestamp"
}
```

**Update "When to Write Status" rules** — agents now update before each major action:

```
- Before each WebSearch call: update currentAction to the search query string
  (e.g., "Searching 'solid-state battery cathode patent 2024'")
- Before each WebFetch call: update currentAction to the URL being fetched
  (e.g., "Fetching https://patents.google.com/patent/US20240123456")
- During assessment: update currentAction to what is being assessed
  (e.g., "Assessing claim C-03 against 2 sources")
- During refinement: update currentAction to the refinement query
  (e.g., "Refining: searching for contradictory evidence on cathode materials")
```

The `currentAction` field is a short human-readable string (max ~120 chars) describing exactly what the agent is doing right now. It changes frequently — potentially every few seconds during active research.

### 7b: Structured Claims Tracking

**New file per agent:** `BASE_DIR/_status/[AgentID]_claims.json`

Written by the agent alongside its status JSON. Overwritten after each research question (reflects cumulative state). Contains every claim discovered so far with investigation status.

```json
[
  {
    "id": "C-01",
    "text": "Toyota filed 3 solid-state battery patents in Q1 2024",
    "confidence": "HIGH",
    "status": "investigated",
    "sourceCount": 2,
    "question": "What prior art exists for solid-state lithium battery cathode designs?"
  },
  {
    "id": "C-02",
    "text": "QuantumScape's lithium-metal anode approach shows 80% capacity retention after 800 cycles",
    "confidence": "MEDIUM",
    "status": "under_investigation",
    "sourceCount": 1,
    "question": "What prior art exists for solid-state lithium battery cathode designs?"
  },
  {
    "id": "C-03",
    "text": "Samsung SDI partnership with Solid Power announced March 2024",
    "confidence": null,
    "status": "pending",
    "sourceCount": 0,
    "question": "Are there contradictory patents in the solid-state electrolyte space?"
  }
]
```

**Claim statuses:**
- `pending` — claim identified but not yet corroborated or verified
- `under_investigation` — agent is actively looking for supporting/contradicting sources
- `investigated` — claim has been assessed and assigned a confidence level

**Field types:**
- `id`: string (e.g., "C-01")
- `text`: string (claim text, max ~200 chars)
- `confidence`: one of `"HIGH"`, `"MEDIUM"`, `"LOW"`, `"SPECULATIVE"`, or `null` (when status is `pending`)
- `status`: one of `"pending"`, `"under_investigation"`, `"investigated"`
- `sourceCount`: integer (number of supporting sources found)
- `question`: string (the research question this claim originated from)

**Write timing:** Claims JSON is overwritten after each research question (cumulative). However, individual `claim` events also appear in the action log in real-time. The dashboard shows claims from the JSON file (updated per question) — new claims discovered mid-question appear in the Activity Log tab first, then in the Claims tab after the question completes and the JSON is rewritten.

**Quick tier:** Quick-tier agents still write claims JSON and action log files. Although the dashboard is not launched for Quick tier, these files are available for post-mortem analysis and can be inspected manually.

**Change target:** `templates/research-protocol.md.tmpl` — Incremental Write Protocol section

Add to the per-question write steps:

```
6. OVERWRITE claims status to `BASE_DIR/_status/[AgentID]_claims.json` with all claims
   discovered so far (cumulative, not per-question). Each claim includes id, text,
   confidence (null if pending), status, sourceCount, and originating question.
```

### 7c: Append-Only Action Log

**New file per agent:** `BASE_DIR/_status/[AgentID]_log.json`

Append-only JSON array. Each entry is one action the agent performed. This provides a complete audit trail of agent behavior and survives agent crashes (partial logs are still valuable).

```json
[
  {
    "type": "start",
    "question": "What prior art exists for solid-state lithium battery cathode designs?",
    "questionIndex": 0,
    "timestamp": "2026-03-19T14:30:05Z"
  },
  {
    "type": "search",
    "query": "solid-state battery cathode patent landscape 2024",
    "engine": "WebSearch",
    "resultCount": 12,
    "timestamp": "2026-03-19T14:30:08Z"
  },
  {
    "type": "fetch",
    "url": "https://patents.google.com/patent/US20240123456",
    "status": "success",
    "timestamp": "2026-03-19T14:30:15Z"
  },
  {
    "type": "fetch",
    "url": "https://example.com/paywalled-article",
    "status": "403_blocked",
    "timestamp": "2026-03-19T14:30:18Z"
  },
  {
    "type": "claim",
    "claimId": "C-01",
    "text": "Toyota filed 3 solid-state battery patents in Q1 2024",
    "confidence": "HIGH",
    "timestamp": "2026-03-19T14:30:25Z"
  },
  {
    "type": "assess",
    "claimId": "C-02",
    "result": "needs_more_sources",
    "sourcesChecked": 1,
    "timestamp": "2026-03-19T14:30:30Z"
  },
  {
    "type": "write",
    "files": ["Claims_patent-search-specialist.md", "Bibliography.md"],
    "claimsAdded": 3,
    "sourcesAdded": 2,
    "timestamp": "2026-03-19T14:30:35Z"
  },
  {
    "type": "question_complete",
    "question": "What prior art exists for solid-state lithium battery cathode designs?",
    "questionIndex": 0,
    "claimsTotal": 3,
    "sourcesTotal": 2,
    "timestamp": "2026-03-19T14:30:36Z"
  }
]
```

**Action types:**
- `start` — began working on a research question
- `search` — executed a WebSearch query
- `fetch` — fetched a URL (with success/failure status)
- `claim` — identified a new claim
- `assess` — assessed a claim against sources
- `write` — wrote findings to disk
- `question_complete` — finished a research question
- `error` — encountered an error
- `abort` — aborted a research branch (with reason)

**Change target:** `templates/research-protocol.md.tmpl` — new "Action Logging Protocol" section

```markdown
## Action Logging Protocol

Maintain an append-only action log at `BASE_DIR/_status/[AgentID]_log.json`.
This file is a JSON array. Append new entries after each significant action.

Log these events:
- Before starting each research question: type "start"
- After each WebSearch call: type "search" with query and result count
- After each WebFetch call: type "fetch" with URL and status (success/403_blocked/timeout/error)
- When a new claim is identified: type "claim" with ID, text, initial confidence
- When assessing a claim: type "assess" with claim ID and result
- After writing files to disk: type "write" with file list and counts
- After completing a research question: type "question_complete" with totals
- On error or abort: type "error" or "abort" with message/reason

Each entry includes a timestamp. The log is append-only — never overwrite or truncate.
On agent start, create the file with an empty array `[]`. Append by reading the current
array, pushing the new entry, and writing back.

**Size limit:** Cap the log at 500 entries per agent. If the array exceeds 500 entries,
drop the oldest entries to stay within the limit. For a typical research session
(5 questions × ~30 actions per question = ~150 entries), this cap is never hit.
It guards against edge cases in Comprehensive tier with extensive follow-up rounds.
```

### 7d: Dashboard UI Enhancements

**Change target:** `templates/dashboard.html.tmpl`

#### Header Enhancements

**Aggregate stats bar** in the header, below the engine name/topic/tier:

```
Claims: 24 total (5 pending, 3 investigating, 16 investigated)  |  Sources: 18  |  Web Fetches: 22/40 used
```

Computed by summing across all agent status data. Updates in real-time via SSE.

**Phase duration tracking:** When a phase completes, show elapsed time next to the checkmark:

```
◇ Tier Detection ✓        ◇ Research Planning ✓ 2m 34s        ◇ Parallel Research ● 4m 12s...
```

Active phase shows a live counter. Completed phases show fixed duration. Requires the pipeline JSON to include `phaseStartedAt` timestamps (see Section 7h).

#### Agent Card — Collapsed State (Default)

Replaces the v1.8.0 compact view with a richer default:

**Question tracker** replaces the progress bar. Each assigned research question shown as a single line:

```
patent-search-specialist                                    ⚠ 1
Questions
  ✓ What prior art exists for solid-state battery cathode designs?          1m 42s
  ✓ Are there contradictory patents in the electrolyte space?               2m 08s
  ● What is the IP landscape for lithium-metal anode tech?                  0m 55s...
    └ Searching 'lithium metal anode patent holders 2024 site:patents.google.com'
  ○ Who are the key patent holders in solid-state batteries?
  ○ What freedom-to-operate risks exist?

Web Fetches  ▪▪▪▪▪▪░░░░  6/10        Claims: 12    Sources: 8        ▶ expand
```

Key elements:
- **Question status indicators:** `✓` complete (green), `●` active (cyan, pulsing), `○` pending (gray)
- **Question text:** truncated with ellipsis if longer than card width
- **Question timing:** elapsed time for completed questions; live counter for active question
- **Current action:** shown as indented sub-line under the active question, updating in real-time
- **Web Fetches:** full label, segmented meter (▪ = used, ░ = remaining), fraction `6/10`
- **Stats row:** claims count, sources count
- **Error/warning badge:** top-right corner of card, red count badge (e.g., `⚠ 1`) if the agent logged errors or aborted branches. Clicking it jumps to the error in the expanded Activity Log tab
- **Expand chevron:** `▶ expand` to reveal tabbed detail view

#### Agent Card — Expanded State

Clicking `▶ expand` reveals a tabbed detail view below the question tracker:

**Tab 1: Claims**
- Table with columns: ID, Text (truncated), Confidence, Status, Sources
- Status shown as colored pills:
  - `pending` → gray pill
  - `under_investigation` → amber pill (pulsing if agent activity is "assessing")
  - `investigated` → green pill
- Confidence shown as tier badges (HIGH/MEDIUM/LOW/SPECULATIVE) with existing accent colors
- Sortable by status (pending first, then under_investigation, then investigated)
- Count header: "12 claims (3 pending, 2 investigating, 7 investigated)"

**Tab 2: Activity Log**
- Scrollable feed, newest at top
- Each entry styled by type:
  - `search` → cyan icon, shows query in monospace
  - `fetch` → cyan icon, shows URL (truncated), status badge (success=green, blocked=rose)
  - `claim` → emerald icon, shows claim text
  - `assess` → amber icon, shows claim ID and result
  - `write` → emerald icon, shows files written and counts
  - `question_complete` → green divider with question text and duration
  - `error`/`abort` → rose icon, shows message
- Auto-scrolls to show latest entry when new events arrive via SSE
- Timestamps shown as relative ("3s ago", "1m ago")
- Full log loaded via `GET /api/agent/:id/log` on tab open (SSE only sends last 50)

**Tab 3: Sources**
- List of URLs fetched by this agent, extracted from the action log (`fetch` entries)
- Each shows: URL (linked), fetch status badge (success=green, blocked=rose, timeout=amber)
- Grouped by status (successful fetches first, then blocked/failed)
- Source count header: "8 sources (6 fetched, 1 blocked, 1 timeout)"
- Note: Credibility tier information is not available at the agent level (tiers are assigned during synthesis). The sources tab shows fetch status only.

**Data source:** The dashboard server reads `_status/[AgentID]_claims.json` and `_status/[AgentID]_log.json` alongside the existing `_status/[AgentID].json`. All three are included in the SSE push and `/api/status` response.

#### Collapsible Legend

A `?` icon in the top-right corner of the header. Clicking it expands a legend panel:

```
Legend
  Pipeline     ○ pending   ● active   ✓ complete   ✗ error
  Activity     ■ searching  ■ assessing  ■ refining  ■ writing  ■ idle
  Claims       ■ pending   ■ investigating   ■ investigated
  Questions    ○ pending   ● active   ✓ complete
  Web Fetches  ▪ used   ░ remaining
```

Each swatch uses the actual accent color from the CSS custom properties. Collapsed by default — experienced users won't need it after the first session.

### 7e: Dashboard Server Changes

**Change target:** `templates/dashboard-server.js.tmpl`

The `getStatus()` function expands to read detail files:

```javascript
function getStatus() {
  const pipeline = readJsonSafe(PIPELINE_FILE);
  const agents = {};
  try {
    for (const file of fs.readdirSync(STATUS_DIR)) {
      if (file.endsWith('.json') && !file.startsWith('_')) {
        // Agent status files: {agentId}.json
        if (!file.includes('_claims') && !file.includes('_log')) {
          const agentId = file.replace('.json', '');
          const data = readJsonSafe(path.join(STATUS_DIR, file));
          if (data) {
            // Attach claims and log if they exist
            data.claims = readJsonSafe(path.join(STATUS_DIR, `${agentId}_claims.json`)) || [];
            data.log = readJsonSafe(path.join(STATUS_DIR, `${agentId}_log.json`)) || [];
            agents[agentId] = data;
          }
        }
      }
    }
  } catch { /* directory read failed */ }
  return { pipeline, agents };
}
```

The `fs.watch` handler already triggers on any `.json` file change, so claims and log file updates automatically push to the dashboard via SSE.

**SSE payload management:** To prevent large payloads during long sessions, the SSE broadcast caps the action log to the **last 50 entries** per agent. The full log is available via a new `GET /api/agent/:id/log` endpoint for clients that need the complete history (e.g., expanding the Activity Log tab triggers a full fetch). Claims are sent in full since they are capped by the number of research questions (typically <50 claims per agent).

**Write frequency:** The `currentAction` field updates before each WebSearch/WebFetch call, which can produce dozens of status file writes per minute per agent. The existing 100ms debounce timer on `fs.watch` coalesces rapid-fire writes into a single SSE broadcast. This is sufficient — the dashboard doesn't need sub-100ms latency, and the debounce prevents SSE flooding.

### 7f: Updated File Structure

```
BASE_DIR/_status/
├── _pipeline.json                         # Pipeline state with phase timing
├── [AgentID].json                         # Agent status with questions array + currentAction
├── [AgentID]_claims.json                  # Structured claims array (new)
├── [AgentID]_log.json                     # Append-only action log (new)
├── vvc-specialist_verification.json       # VVC verdict/correction tracking (new, Phase 5-6)
├── server.js                              # Dashboard server (enhanced)
└── dashboard.html                         # Dashboard UI (enhanced)
```

### 7h: Data Model Changes for Timing and Questions

The question tracker and phase duration features require additional fields in the status and pipeline JSON files.

**Agent status JSON — new `questions` array:**

Replaces the flat `questionsCompleted`/`questionsTotal` counters with a structured array. Each entry tracks one assigned research question:

```json
{
  "agentId": "[AgentID]",
  "engineId": "${ENGINE_ID}",
  "phase": 2,
  "status": "researching",
  "currentAction": "Searching 'solid-state battery cathode 2024'",
  "activity": "searching",
  "questions": [
    {
      "text": "What prior art exists for solid-state battery cathode designs?",
      "status": "complete",
      "startedAt": "2026-03-19T14:30:05Z",
      "completedAt": "2026-03-19T14:31:47Z",
      "durationMs": 102000
    },
    {
      "text": "Are there contradictory patents in the electrolyte space?",
      "status": "complete",
      "startedAt": "2026-03-19T14:31:48Z",
      "completedAt": "2026-03-19T14:33:56Z",
      "durationMs": 128000
    },
    {
      "text": "What is the IP landscape for lithium-metal anode tech?",
      "status": "active",
      "startedAt": "2026-03-19T14:33:57Z",
      "completedAt": null,
      "durationMs": null
    },
    {
      "text": "Who are the key patent holders in solid-state batteries?",
      "status": "pending",
      "startedAt": null,
      "completedAt": null,
      "durationMs": null
    }
  ],
  "webFetchesUsed": 6,
  "webFetchCap": 10,
  "claimsFound": 12,
  "sourcesCollected": 8,
  "iterationPass": 2,
  "maxIterations": 3,
  "errors": 0,
  "aborts": 0,
  "lastUpdated": "ISO-8601 timestamp"
}
```

The `questionsCompleted` and `questionsTotal` fields are removed — the dashboard derives them from `questions.filter(q => q.status === 'complete').length` and `questions.length`. The `currentQuestion` field is also removed — the active question is `questions.find(q => q.status === 'active').text`.

New fields:
- `questions[]` — structured array replacing flat counters
- `errors` — count of error events in the action log (drives the error badge)
- `aborts` — count of abort events in the action log

**Pipeline JSON — phase timing:**

Each phase object gains `startedAt` and `completedAt` timestamps:

```json
{
  "phases": [
    {
      "phase": 0,
      "label": "Tier Detection",
      "status": "complete",
      "startedAt": "2026-03-19T14:30:00Z",
      "completedAt": "2026-03-19T14:30:02Z"
    },
    {
      "phase": 1,
      "label": "Research Planning",
      "status": "complete",
      "startedAt": "2026-03-19T14:30:02Z",
      "completedAt": "2026-03-19T14:32:36Z"
    },
    {
      "phase": 2,
      "label": "Parallel Research",
      "status": "in_progress",
      "startedAt": "2026-03-19T14:32:37Z",
      "completedAt": null
    }
  ]
}
```

The orchestrator writes `startedAt` when setting a phase to `"in_progress"` and `completedAt` when setting it to `"complete"`. The dashboard computes duration client-side. For the active phase, it shows a live counter from `startedAt` to now.

**Change target:** `templates/orchestrator-skill.md.tmpl` — Phase Transition Protocol section and `_pipeline.json` initial state.

**Change target:** `templates/research-protocol.md.tmpl` — Agent Status Protocol section (replace flat counters with `questions` array).

### 7i: VVC Verification Panel

When the pipeline reaches Phase 5 (VVC-Verify), the dashboard transitions from the Phase 2 agent cards view to a dedicated VVC Verification Panel. This panel replaces the agent cards area — Phase 2 agents are done by then and their cards are no longer updating.

**VVC panel appears only when:**
- Engine has VVC enabled (`qualityFramework.vvc.enabled: true`)
- `--no-vvc` flag was NOT passed
- Pipeline has reached Phase 5

**Data source:** The VVC agent writes `BASE_DIR/_status/vvc-specialist_verification.json`:

```json
{
  "phase": 5,
  "mode": "full",
  "totalClaims": 47,
  "verified": 34,
  "claims": [
    {
      "id": "VC-01",
      "text": "Toyota filed 3 solid-state battery patents in Q1 2024",
      "confidence": "HIGH",
      "sourceUrl": "https://patents.google.com/...",
      "sourceQuote": "Three patent applications filed January-March 2024...",
      "verdict": "CONFIRMED",
      "recommendation": "KEEP",
      "correctedText": null,
      "correctionApplied": null
    },
    {
      "id": "VC-02",
      "text": "QuantumScape achieves 80% capacity retention after 800 cycles",
      "confidence": "HIGH",
      "sourceUrl": "https://quantumscape.com/resources/...",
      "sourceQuote": "Testing showed 75% capacity retention after 700 cycles...",
      "verdict": "OVERSTATED",
      "recommendation": "REVISE",
      "correctedText": "QuantumScape achieves approximately 75% capacity retention after 700 cycles",
      "correctionApplied": null
    },
    {
      "id": "VC-03",
      "text": "Solid Power received $130M DOE grant in 2024",
      "confidence": "MEDIUM",
      "sourceUrl": "https://energy.gov/...",
      "sourceQuote": null,
      "verdict": "SOURCE_UNAVAILABLE",
      "recommendation": "REMOVE",
      "correctedText": null,
      "correctionApplied": null
    },
    {
      "id": "VC-04",
      "text": "Pending verification...",
      "confidence": "HIGH",
      "sourceUrl": null,
      "sourceQuote": null,
      "verdict": null,
      "recommendation": null,
      "correctedText": null,
      "correctionApplied": null
    }
  ],
  "lastUpdated": "ISO-8601 timestamp"
}
```

**Phase 5 verdict field values:**
- `CONFIRMED` — source supports the claim as stated
- `PARAPHRASED` — source supports but claim rewords slightly (acceptable)
- `OVERSTATED` — claim exaggerates what the source says
- `UNDERSTATED` — claim undersells what the source says
- `DISPUTED` — other credible sources contradict the claim
- `UNSUPPORTED` — cited source does not support the claim
- `SOURCE_UNAVAILABLE` — source URL returned 403/timeout/error

**Phase 5 recommendation field values:**
- `KEEP` — no changes needed (CONFIRMED, PARAPHRASED)
- `REVISE` — rewrite claim to match source accurately (OVERSTATED, UNDERSTATED)
- `DOWNGRADE` — lower confidence tier and add qualifying language
- `REMOVE` — delete claim from report (UNSUPPORTED)
- `REPLACE_SOURCE` — find alternative source for the claim

**Phase 6 `correctionApplied` field** — set by the VVC agent during Phase 6 (correction pass):
- `null` — Phase 6 has not processed this claim yet
- `"applied"` — correction was applied to the report
- `"kept"` — claim was kept unchanged (verdict was CONFIRMED/PARAPHRASED)
- `"removed"` — claim was removed from the report
- `"skipped"` — Phase 6 did not run (verify-only mode)

**`mode` field** reflects the tier behavior:
- `"full"` — Phases 5 + 6 (verify and correct)
- `"verify-only"` — Phase 5 only (verdicts rendered, no corrections applied)

#### VVC Panel Layout — Phase 5 (Verification)

```
VVC Verification                                          Phase 5 ● 2m 18s...
Mode: Full (verify + correct)

Summary: 47 claims  ██████████████████████████░░░░  34/47 verified
  38 confirmed  ·  5 paraphrased  ·  2 overstated  ·  1 disputed  ·  1 unsupported  ·  0 unavailable

┌──────┬──────────────────────────────────┬───────────┬───────────────┬──────────────┐
│ ID   │ Claim                            │ Conf.     │ Verdict       │ Recommendation│
├──────┼──────────────────────────────────┼───────────┼───────────────┼──────────────┤
│VC-01 │ Toyota filed 3 solid-state...   │ HIGH      │ ✓ CONFIRMED   │ KEEP         │
│VC-02 │ QuantumScape 80% capacity...    │ HIGH      │ ⚠ OVERSTATED  │ REVISE       │
│VC-03 │ Solid Power $130M DOE grant...  │ MEDIUM    │ ✗ UNSUPPORTED │ REMOVE       │
│VC-04 │ Samsung SDI partnership...      │ HIGH      │ ~ PARAPHRASED │ KEEP         │
│VC-05 │ Market size $6.2B by 2030...    │ MEDIUM    │ ● verifying   │              │
│VC-06 │ Pending                         │ LOW       │ ○             │              │
└──────┴──────────────────────────────────┴───────────┴───────────────┴──────────────┘
```

**Expandable rows:** Clicking a row expands to show:
- Source URL (linked)
- Source quote (the relevant passage from the cited source)
- Corrected text (if recommendation is REVISE, shows the proposed rewrite)

#### VVC Panel Layout — Phase 6 (Correction)

When Phase 6 begins, the table gains a sixth column showing the actual action taken:

```
VVC Correction                                            Phase 6 ● 1m 05s...
Mode: Full (verify + correct)

Summary: 47 claims verified → 42 kept · 3 revised · 1 removed · 1 source replaced
                               ██████████████████████████████████████████████████

┌──────┬──────────────────────────────┬───────────────┬──────────────┬──────────────┐
│ ID   │ Claim                        │ Verdict       │ Recommend.   │ Applied      │
├──────┼──────────────────────────────┼───────────────┼──────────────┼──────────────┤
│VC-01 │ Toyota filed 3 solid-state...│ ✓ CONFIRMED   │ KEEP         │ ✓ kept       │
│VC-02 │ QuantumScape 80% capacity... │ ⚠ OVERSTATED  │ REVISE       │ ✓ applied    │
│VC-03 │ Solid Power $130M DOE...     │ ✗ UNSUPPORTED │ REMOVE       │ ✗ removed    │
│VC-04 │ Samsung SDI partnership...   │ ~ PARAPHRASED │ KEEP         │ ✓ kept       │
│VC-05 │ BYD blade battery tech...    │ ✓ CONFIRMED   │ KEEP         │ ● applying   │
│VC-06 │ Pending                      │ ✓ CONFIRMED   │ KEEP         │ ○            │
└──────┴──────────────────────────────┴───────────────┴──────────────┴──────────────┘
```

**Applied column color coding:**
- `kept` → green (claim unchanged, verdict was positive)
- `applied` → amber (claim was rewritten — expandable row shows before/after diff)
- `removed` → rose (claim deleted from report)
- `applying` → cyan pulsing (Phase 6 is processing this claim now)

**Expandable rows in Phase 6:** For `applied` rows, show before/after:
```
  Before: "QuantumScape achieves 80% capacity retention after 800 cycles"
  After:  "QuantumScape achieves approximately 75% capacity retention after 700 cycles"
  Source: https://quantumscape.com/resources/...
```

#### VVC Panel — Verify-Only Mode

When the engine's tier behavior is `"verify-only"` (Standard tier default), Phase 6 does not run. The panel shows:

```
VVC Verification (verify only — no corrections applied)    Phase 5 ✓ 3m 42s

Summary: 47 claims verified
  38 confirmed  ·  5 paraphrased  ·  2 overstated  ·  1 disputed  ·  1 unsupported  ·  0 unavailable

[Same table as Phase 5, without the Recommendation and Applied columns]
```

The header explicitly states "verify only — no corrections applied" so the user understands that the verdicts are informational. The `correctionApplied` field for all claims is `"skipped"`.

#### VVC Panel Transition

- **Before Phase 5:** VVC panel is not visible. Agent cards for Phase 2 are shown.
- **Phase 3/4 transition:** Agent cards collapse (Phase 2 agents are done). Pipeline visualization shows Phase 3/4 progressing. No agent detail view during synthesis/reporting — these are single-agent phases with no parallel activity to show.
- **Phase 5 starts:** VVC panel appears, claims populate as they are verified.
- **Phase 6 starts (full mode):** Table gains the "Applied" column, corrections populate.
- **Pipeline complete:** VVC panel stays visible with final state. Completion banner appears.

#### VVC Data Flow

**Change target:** `templates/vvc-pipeline.md.tmpl`

Add instructions for the VVC agent to write `_status/vvc-specialist_verification.json`:

- After extracting claims from the draft report: write initial array with all claims, `verdict: null`
- After verifying each claim: update that claim's verdict, recommendation, sourceQuote, correctedText
- Overwrite the file after each claim verification (not batch — one claim at a time for live dashboard updates)
- In Phase 6: update `correctionApplied` for each claim as corrections are applied

**Change target:** `templates/dashboard-server.js.tmpl`

The `getStatus()` function reads `_status/vvc-specialist_verification.json` and attaches it to the response under a `vvc` key (separate from the `agents` map):

```javascript
const vvcFile = path.join(STATUS_DIR, 'vvc-specialist_verification.json');
status.vvc = readJsonSafe(vvcFile) || null;
```

### 7g: Impact on Templates and Generator

These observability changes modify five template files:

| Template | Changes |
|----------|---------|
| `templates/research-protocol.md.tmpl` | Replace flat question counters with `questions` array in status schema, add `currentAction`, `errors`, `aborts` fields, add claims JSON writing to Incremental Write Protocol, add Action Logging Protocol section |
| `templates/orchestrator-skill.md.tmpl` | Add `startedAt`/`completedAt` timestamps to phase objects in Phase Transition Protocol and `_pipeline.json` initial state |
| `templates/vvc-pipeline.md.tmpl` | Add instructions for VVC agent to write `_status/vvc-specialist_verification.json` with per-claim verdicts, recommendations, and correction status |
| `templates/dashboard-server.js.tmpl` | Update `getStatus()` to read claims, log, and VVC verification files; add `GET /api/agent/:id/log` endpoint; cap SSE log to 50 entries |
| `templates/dashboard.html.tmpl` | Question tracker, aggregate stats bar, phase duration display, expandable cards with claims/activity log/sources tabs, error badges, legend panel, labeled WebFetch meter, VVC Verification Panel with verdict/correction tracking |

The Python generator reads these templates as-is — no generator changes needed for the observability enhancements. The templates contain the protocol instructions that agents follow at runtime.

## Updated Files Changed (Complete)

| File | Change Type | Description |
|------|-------------|-------------|
| `plugin/generator/generate.py` | New | Deterministic generator script |
| `plugin/skills/engine-creator/SKILL.md` | Modified | Replace generation steps with script invocation, add _derived, bump to v1.9.0 |
| `templates/engine-config-schema.json` | Modified | Add `_derived` to required + properties |
| `templates/research-protocol.md.tmpl` | Modified | Replace flat counters with questions array, add currentAction/errors/aborts, claims JSON, Action Logging Protocol |
| `templates/orchestrator-skill.md.tmpl` | Modified | Add startedAt/completedAt timestamps to phase transitions and _pipeline.json |
| `templates/dashboard-server.js.tmpl` | Modified | Read claims + log files, add /api/agent/:id/log endpoint, cap SSE log |
| `templates/vvc-pipeline.md.tmpl` | Modified | Add VVC verification JSON writing protocol for dashboard |
| `templates/dashboard.html.tmpl` | Modified | Question tracker, stats bar, phase durations, expandable cards, legend, error badges, VVC panel |
| `plugin/commands/test-engine.md` | Modified | Remove impossible-to-fail checks |
| `plugin/examples/patent-intelligence-engine/` | Modified | Regenerate with script + updated templates |
| `plugin/.claude-plugin/plugin.json` | Modified | Version 1.9.0 |
| `.claude-plugin/marketplace.json` | Modified | Version 1.9.0 |
| `CHANGELOG.md` | Modified | v1.9.0 entry |

## Files NOT Changed

| File | Reason |
|------|--------|
| `templates/agent-template.md.tmpl` | Agent Constraints already present from v1.8.0 |
| `templates/standards.md.tmpl` | No changes |
| `templates/provenance.md.tmpl` | No changes |
| `templates/command-template.md.tmpl` | No changes |
| `templates/sources-command-template.md.tmpl` | No changes |
| `templates/plugin-json.tmpl` | No changes |
| `templates/extension-skill.md.tmpl` | No changes (extension mode inherits observability from base plugin — see note below) |
| `templates/readme-template.md.tmpl` | No changes |
| `plugin/skills/engine-creator/domain-presets/*.json` | Presets don't include `_derived` |
| `preset-schema.json` | Presets don't include `_derived` |
| `plugin-manifest-schema.json` | Used only by `/test-engine`, not by `generate.py` |

**Extension mode note:** Extension-mode engines inherit `research-protocol.md`, `dashboard-server.js`, and `dashboard.html` from the base `/deep-research` plugin. The observability enhancements in Section 7 only take effect for extension engines when the base plugin is updated to include these changes. This is a known limitation — extension mode is inherently dependent on the base plugin version.
