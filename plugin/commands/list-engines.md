---
description: "List research engines found in a directory"
argument-hint: "[directory-path]"
allowed-tools: ["Read", "Glob", "Bash"]
---

# List Research Engines

You are scanning a directory for research engine plugins and displaying a summary table.

## 1. Determine Search Directory

Use the directory specified in `$ARGUMENTS`. If no directory is provided, use the current working directory.

## 2. Scan for Engines

Use Glob to find all `engine-config.json` files within subdirectories of the search directory:

- Pattern: `{search-directory}/*/engine-config.json`
- Also check one level deeper: `{search-directory}/*/*/engine-config.json`

## 3. Read Engine Metadata

For each `engine-config.json` found, read the file and extract:

- **name**: `engineMeta.name`
- **displayName**: `engineMeta.displayName`
- **domain**: `engineMeta.domain`
- **version**: `engineMeta.version`
- **mode**: `engineMeta.mode`
- **agent count**: length of `agentPipeline.agents` array

## 4. Display Results

If engines were found, display as a table:

```markdown
## Research Engines in {search-directory}

| Engine | Domain | Version | Mode | Agents |
|--------|--------|---------|------|--------|
| {displayName} ({name}) | {domain} | {version} | {mode} | {agentCount} |
```

Sort by engine name alphabetically.

If no engines were found, inform the user:

> No research engines found in `{search-directory}`. Research engines are identified by the presence of an `engine-config.json` file in a subdirectory.

## Important

This command is **read-only**. Do not create, modify, or delete any files.
