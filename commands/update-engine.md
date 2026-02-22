---
description: "Update an existing research engine's configuration and regenerate affected files"
argument-hint: "<path-to-engine>"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Update Research Engine

You are updating an existing research engine plugin. Your job is to let the user selectively reconfigure sections of their engine and regenerate only the affected files.

## 1. Locate the Engine

Read `engine-config.json` from the path specified in `$ARGUMENTS`.

If no path is provided, use AskUserQuestion to ask the user for the path to the generated engine directory.

Validate that the path contains a valid `engine-config.json` before proceeding.

## 2. Display Current Configuration Summary

Present an overview of the engine's current state:

- **Engine name**: `engineMeta.name`
- **Display name**: `engineMeta.displayName`
- **Domain**: `engineMeta.domain`
- **Output mode**: `engineMeta.mode`
- **Version**: `engineMeta.version`
- **Agent count**: number of agents in `agentPipeline.agents`
- **Tier structure**: list tiers with agent counts per tier

## 3. Select Sections to Reconfigure

Use AskUserQuestion with **multiSelect** to ask which sections to reconfigure:

- Domain Identity
- Research Scope
- Sample Questions
- Source Strategy
- Agent Pipeline
- Quality Framework
- Output Structure
- Advanced Configuration
- Custom Prompts

## 4. Re-run Selected Section Interviews

For each selected section:

1. Read the Engine Creator skill at `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/SKILL.md` for the wizard protocol.
2. Re-run that section's wizard interview, showing the **current values as defaults**.
3. Use AskUserQuestion for all choices, pre-filling with existing config values.
4. Record all changes.

## 5. Show Change Summary

After all selected sections are re-interviewed, display a change summary:

```
### Changes Summary

| Field | Old Value | New Value |
|-------|-----------|-----------|
| ... | ... | ... |
```

Show old and new values for every modified field. If a section was re-interviewed but no values changed, note "No changes" for that section.

## 6. Confirm and Regenerate

Ask the user to confirm before regenerating. Use AskUserQuestion: **Confirm and Regenerate**, **Modify Another Section**, **Cancel**.

If confirmed, regenerate only the affected files based on what changed:

| What Changed | Files to Regenerate |
|---|---|
| Source strategy, quality framework, output structure, or custom prompts | `skills/{name}/SKILL.md` |
| Agent pipeline (agents added/removed/modified) | Agent `.md` files in `agents/` + `skills/{name}/SKILL.md` |
| Engine metadata (name, description, version, mode) | `.claude-plugin/plugin.json` + `README.md` |
| Any change at all | `README.md` (always regenerated) |

Use template files from `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/templates/` for all regeneration.

## 7. Bump Version

After regeneration, bump the **patch version** in `engine-config.json`:
- `1.0.0` becomes `1.0.1`
- `1.0.1` becomes `1.0.2`
- etc.

Also update the version in `.claude-plugin/plugin.json` to match.

## 8. Post-Update

1. List all regenerated files.
2. Show the new version number.
3. Suggest running `/test-engine` to validate the updated engine.
