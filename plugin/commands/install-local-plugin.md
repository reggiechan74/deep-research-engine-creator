---
description: "Install a generated research engine plugin locally via Claude Code's plugin system"
argument-hint: "<path-to-engine-plugin>"
allowed-tools: ["Read", "Write", "Bash", "Glob", "AskUserQuestion"]
---

# Install Local Plugin

Install a generated research engine plugin into Claude Code's local plugin system so its `/research` and `/sources` commands become available as slash commands.

## 1. Parse Arguments

Parse `$ARGUMENTS`:
- **First argument** (required): path to the engine plugin directory (must contain `engine-config.json` and `.claude-plugin/plugin.json`)

If no path is provided, check the current working directory. If no engine found, report an error and exit.

## 2. Validate Plugin

Run `claude plugin validate {path}` via Bash. If validation fails, report the errors and exit.

## 3. Read Engine Metadata

Read `{path}/engine-config.json` and extract:
- `engineMeta.name` — the plugin name (kebab-case)
- `engineMeta.displayName` — human-readable name
- `engineMeta.version` — semver version
- `engineMeta.description` — engine description

Read `{path}/.claude-plugin/plugin.json` and verify it exists and contains a `name` field matching `engineMeta.name`.

## 4. Check for Existing Installation

Read `~/.claude/plugins/installed_plugins.json` via Bash (`cat ~/.claude/plugins/installed_plugins.json`).

Search for any key starting with `{engineMeta.name}@`. If found:
- Inform the user: "Plugin `{name}` is already installed (version {existing_version} from {marketplace})."
- Use AskUserQuestion: "Reinstall/update?" with options:
  - "Yes, reinstall" — continue with installation (will overwrite)
  - "No, cancel" — exit

## 5. Create Temporary Marketplace

The Claude Code plugin system installs from **marketplaces** — directories with a `.claude-plugin/marketplace.json` manifest listing available plugins. Create a temporary one:

```
MARKETPLACE_DIR = /tmp/{engineMeta.name}-marketplace
MARKETPLACE_NAME = {engineMeta.name}-local
```

1. Create directory: `mkdir -p {MARKETPLACE_DIR}/.claude-plugin`
2. Create directory: `mkdir -p {MARKETPLACE_DIR}/{engineMeta.name}`
3. Write `{MARKETPLACE_DIR}/.claude-plugin/marketplace.json`:

```json
{
  "name": "{MARKETPLACE_NAME}",
  "owner": {
    "name": "{author_name_from_plugin_json_or_empty}"
  },
  "plugins": [
    {
      "name": "{engineMeta.name}",
      "source": "./{engineMeta.name}",
      "description": "{engineMeta.description}",
      "version": "{engineMeta.version}"
    }
  ]
}
```

4. Copy ALL plugin files into the marketplace plugin subdirectory:
   ```bash
   cp -r {path}/* {MARKETPLACE_DIR}/{engineMeta.name}/
   cp -r {path}/.claude-plugin {MARKETPLACE_DIR}/{engineMeta.name}/
   ```

## 6. Register Marketplace and Install

Run these commands sequentially via Bash:

```bash
# Register the temporary marketplace
claude plugin marketplace add {MARKETPLACE_DIR}

# Install the plugin from the marketplace
claude plugin install {engineMeta.name}@{MARKETPLACE_NAME}
```

If either command fails, report the error with the full command output and suggest manual troubleshooting.

## 7. Verify Installation

Read `~/.claude/plugins/installed_plugins.json` again and verify `{engineMeta.name}@{MARKETPLACE_NAME}` exists with the correct version and installPath.

Also verify the installed files exist:
```bash
ls {installPath}/.claude-plugin/plugin.json
ls {installPath}/commands/
ls {installPath}/skills/
```

## 8. Report Results

If successful, display:

```markdown
## Plugin Installed Successfully

| Field | Value |
|-------|-------|
| Plugin | {engineMeta.displayName} |
| Version | {engineMeta.version} |
| Installed as | {engineMeta.name}@{MARKETPLACE_NAME} |
| Install path | {installPath} |

### Available Commands (after restart)

- `/{engineMeta.name}:research [topic] [--quick|--deep|--comprehensive]`
- `/{engineMeta.name}:sources`

### Next Step

**Restart Claude Code** to load the new plugin. Run `/exit` and relaunch.
```

Also suggest:
- "Run `/{engineMeta.name}:research [topic] --quick` after restart for a quick functional test."

## Important Notes

- This command creates a temporary marketplace at `/tmp/`. The marketplace registration persists in `~/.claude/plugins/known_marketplaces.json` but the actual files are ephemeral. If `/tmp/` is cleaned, the marketplace entry will be stale but the **installed plugin in the cache remains functional**.
- To uninstall: `claude plugin uninstall {engineMeta.name}@{MARKETPLACE_NAME}`
- To update after modifying engine files: re-run this command (it will detect the existing install and offer to reinstall).
- The plugin is installed at **user scope** (available across all projects). Use `claude plugin install {name}@{marketplace} --scope project` for project-scoped installation.
