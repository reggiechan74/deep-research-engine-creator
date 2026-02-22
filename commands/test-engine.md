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

Record PASS if all agents have matching files, FAIL with the list of missing agent files.

### Check 4: Config Validity

Verify `engine-config.json` contains all required top-level keys:

- `schemaVersion`
- `engineMeta`
- `sampleQuestions`
- `scope`
- `sourceStrategy`
- `agentPipeline`
- `qualityFramework`
- `outputStructure`

Record PASS if all keys are present, FAIL with the list of missing keys.

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
