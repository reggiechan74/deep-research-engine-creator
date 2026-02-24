---
description: "Smoke-test a generated research engine plugin for structural validity and basic functionality"
argument-hint: "<path-to-engine> [test-topic]"
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "WebSearch", "WebFetch"]
---

# Test Research Engine

You are running a 5-point validation suite against a generated research engine plugin.

## 1. Parse Arguments

Parse `$ARGUMENTS`:
- **First argument** (required): path to the engine directory
- **Second argument** (optional): test topic for the smoke test

If no engine path is provided, report an error and exit.

Read `engine-config.json` from the specified path. If no test topic is provided, use the first entry from `sampleQuestions` in the config.

## 2. Run 5-Point Validation

### Check 1: Plugin Structure

Verify these files exist in the engine directory:

- `.claude-plugin/plugin.json`
- `engine-config.json`
- `commands/research.md`
- `commands/sources.md`
- `skills/*/SKILL.md` (at least one skill directory with a SKILL.md)
- `README.md`
- One `.md` file in `agents/` for each agent defined in `agentPipeline.agents`

Record PASS if all files exist, FAIL with a list of missing files otherwise.

### Check 2: YAML Frontmatter

Read each `.md` file in `commands/` and `agents/`. For each file:

- Verify the file starts with `---` (YAML frontmatter opening)
- Verify there is a closing `---` after the frontmatter block
- Verify the frontmatter contains at least a `description` field

Record PASS if all files have valid frontmatter, FAIL with the list of files that failed.

### Check 3: Agent Definitions

For each agent defined in `agentPipeline.agents` in the config:

- Verify a corresponding `.md` file exists in the `agents/` directory
- The file should be named `{agentId}.md` where `agentId` matches the agent's `id` field
- This includes the `vvc-specialist` agent when VVC is enabled — it should have an agent file even though it does not appear in tier agent arrays

Record PASS if all agents have matching files, FAIL with the list of missing agent files.

### Check 4: Config Validity

Perform multi-level structural validation on `engine-config.json`:

**4a-schema: JSON Schema validation.** Validate the engine config against the schema at `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/templates/engine-config-schema.json` (or the bundled schema if running outside the creator context). Report any schema violations including type mismatches, missing required fields, pattern failures, and enum violations. If schema validation passes, proceed with relational checks below that cannot be expressed in JSON Schema.

**4a: Required top-level keys.** Verify these keys exist:
- `schemaVersion`, `engineMeta`, `sampleQuestions`, `scope`, `sourceStrategy`, `agentPipeline`, `qualityFramework`, `outputStructure`

**4b: engineMeta structure.** Verify `engineMeta` contains:
- `name` (matches pattern `^[a-z0-9]+(-[a-z0-9]+)*$`)
- `displayName`, `domain`, `audience`, `version`, `mode`, `createdAt`, `createdBy`

**4c: Agent-tier cross-reference.** For each tier in `agentPipeline.tiers` (quick, standard, deep, comprehensive):
- Extract the agent IDs listed in `tier.agents`
- Verify each ID exists in `agentPipeline.agents[].id`
- Record FAIL with list of dangling references if any ID doesn't match

**4d: Quality framework structure.** Verify `qualityFramework` contains:
- `confidenceScoring` with keys: HIGH, MEDIUM, LOW, SPECULATIVE
- `minimumEvidence` (non-empty string)
- `validationRules` (non-empty array)
- `citationStandard` (non-empty string)

**4e: Source hierarchy completeness.** Verify `sourceStrategy.credibilityTiers` contains:
- All 5 tiers (tier1 through tier5)
- Each tier has non-empty `name` and `sources` array

**4f: Unresolved placeholder scan.** Scan ALL `.md` and `.json` files in the engine directory (excluding `engine-config-schema.json` and `preset-schema.json`):
- Search for pattern `\{\{[a-zA-Z0-9_-]+\}\}` (double-brace placeholders with letters, digits, underscores, hyphens)
- Record FAIL with list of files and unresolved placeholders if any found
- This catches generation failures where template substitution was incomplete

**4g: Domain preset validation (if presets used).** If the engine was generated from a domain preset, validate the preset file against `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/templates/preset-schema.json`. Report any structural violations.

**4h: Citation management validation (if present).** If `qualityFramework.citationManagement` exists:
- Verify `verificationMode` is one of: "none", "spot-check", "comprehensive"
- Verify `deadLinkHandling` is one of: "flag-only", "archive-fallback", "exclude-from-high"
- If `sourceFreshnessThreshold` is "custom", verify `sourceFreshnessCustomYears` is present and valid

**4i: VVC configuration validation (if present).** If `qualityFramework.vvc` exists:
- Verify `enabled` is a boolean
- If `enabled` is true:
  - Verify `claimTypes` is a non-empty array where each element has `tag` (2-4 uppercase letters), `label`, `description`, and `requiresVerification` (boolean)
  - Verify `verificationScope` exists with `HIGH` in 0-100, `MEDIUM` in 0-100, `LOW` in 0-100, `SPECULATIVE` in 0-100
  - Verify `tierBehavior` exists with `quick` = "none" and `standard`, `deep`, `comprehensive` each one of: "none", "verify-only", "full"
  - Verify `vvc-specialist.md` exists in the `agents/` directory
  - Verify `vvc-specialist` is listed in `agentPipeline.agents[].id`
  - **CRITICAL:** Verify `vvc-specialist` does NOT appear in any tier's `agents` array (`agentPipeline.tiers.{quick,standard,deep,comprehensive}.agents`). The VVC agent is a pipeline agent (Phases 5-6), NOT a Phase 2 research agent.
  - If `advanced.tokenBudgets` exists, verify `vvc` field is present with a positive integer value

Record PASS if all sub-checks pass, FAIL with details of which sub-checks failed.

### Check 5: Quick Smoke Test

Perform a lightweight functional test:

1. Take the test topic (from arguments or the first sample question).
2. Deploy a single general-purpose sub-agent in `--quick` mode.
3. The sub-agent should use the engine's configured source hierarchy (top tier sources) to perform 2-3 web searches on the test topic.
4. Verify the sub-agent can: execute web searches successfully, find relevant results, produce a short structured summary (3-5 bullet points with at least one source citation).

This is NOT a full research run. It is a lightweight check that the engine's source configuration is functional and produces usable results.

Record PASS if the sub-agent produces structured output with citations, FAIL with details of what went wrong.

## 3. Generate Report

Output the test report in this format:

```markdown
## Engine Test Report: {engineName}

| Check | Status | Details |
|-------|--------|---------|
| Plugin structure | PASS/FAIL | {details} |
| YAML frontmatter | PASS/FAIL | {details} |
| Agent definitions | PASS/FAIL | {details} |
| Config validity | PASS/FAIL | {details} |
| Quick smoke test | PASS/FAIL | {details} |

**Overall: {PASS/FAIL}** -- {summary}
```

- Overall is PASS only if all 5 checks pass.
- If any check fails, overall is FAIL with a summary of what needs fixing.
- Include the engine name and version in the report header.
