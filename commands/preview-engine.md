---
description: "Preview what a research engine plugin would look like from an engine-config.json"
argument-hint: "<path-to-engine-or-config>"
allowed-tools: ["Read", "Glob"]
---

# Preview Research Engine

You are generating a read-only preview of a research engine configuration. Do NOT write any files.

## 1. Locate Configuration

Read `engine-config.json` from the path specified in `$ARGUMENTS`.

- If the path points to a directory, look for `engine-config.json` inside it.
- If the path points directly to a `.json` file, read it directly.
- If the file is not found, report an error and exit.

## 2. Display Preview

Present the engine configuration in this order:

### Engine Identity

| Field | Value |
|-------|-------|
| Name | `engineMeta.name` |
| Display Name | `engineMeta.displayName` |
| Domain | `engineMeta.domain` |
| Audience | `engineMeta.audience` |
| Version | `engineMeta.version` |
| Mode | `engineMeta.mode` |

### File Tree

Show what files exist (if previewing an existing engine) or would be generated (if previewing a config only):

```
{engineName}/
  .claude-plugin/
    plugin.json
  commands/
    research.md
    sources.md
  agents/
    {agent-1-id}.md
    {agent-2-id}.md
    ...
  skills/{engineName}/
    SKILL.md
  engine-config.json
  README.md
```

If the engine directory exists, use Glob to show the actual file tree. Otherwise, construct the expected tree from the config.

### Agent Pipeline

| Agent | Role | Sub-Agent Type | Tiers |
|-------|------|---------------|-------|
| {agentId} | {role} | {subAgentType} | {comma-separated tier names} |

For each agent in `agentPipeline.agents`, look up which tiers include that agent by checking `agentPipeline.tiers[*].agents`.

### Source Hierarchy

For each of the 5 tiers in `sourceStrategy.credibilityTiers`:

**Tier {N}: {tierName}**
- {source 1}
- {source 2}
- {source 3}
- ... (show all sources)

### Report Sections

Numbered list of sections from `outputStructure.reportSections` in order.

### Sample Questions

Numbered list from `sampleQuestions`.

### Quality Framework

- **Confidence levels**: List each level from `qualityFramework.confidenceScoring` with name and threshold
- **Minimum evidence**: `qualityFramework.minimumEvidence`
- **Citation standard**: `qualityFramework.citationStandard`
- **Validation rules**: Count of rules defined

## Important

This command is **read-only**. Do not create, modify, or delete any files.
