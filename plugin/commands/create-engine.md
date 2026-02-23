---
description: "Create a domain-specialized deep-research engine as a standalone Claude Code plugin"
argument-hint: "[--preset legal|market|academic|osint|techdd]"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Create Research Engine

You are running the **Deep Research Engine Creator** wizard. Your job is to interview the user about their research domain and generate a complete, standalone Claude Code plugin.

## 1. Parse Arguments

Check `$ARGUMENTS` for a `--preset` flag. Map short names to preset files:

| Short Name | Preset File |
|------------|-------------|
| `legal` | `legal-research.json` |
| `market` | `market-intelligence.json` |
| `academic` | `academic-research.json` |
| `osint` | `osint-investigation.json` |
| `techdd` | `technical-due-diligence.json` |
| `ai` | `ai-agentic-engineering.json` |

If a preset is specified, read it from:
`${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/domain-presets/{preset-file}`

This will pre-fill sections 4-9 of the wizard interview with smart defaults. Inform the user which preset was loaded.

## 2. Load the Skill

Read the Engine Creator skill at:
`${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/SKILL.md`

This is your complete reference for the wizard interview protocol, config assembly, preview protocol, generation protocol, and post-generation steps.

## 3. Execute the Wizard

Follow the **Wizard Interview Protocol** from the skill exactly:

- **Section 1**: Domain Identity (name, description, audience, preset, output mode)
- **Section 2**: Research Scope & Objectives (question types, geographic scope, temporal focus, deliverable)
- **Section 3**: Sample Research Questions (collect 3-5 examples, auto-suggest configuration)
- **Section 4**: Source Strategy (credibility tiers, preferred/excluded sources, filters, search templates)
- **Section 5**: Agent Pipeline Design (basic or advanced agent configuration)
- **Section 6**: Quality Framework (confidence scoring, evidence thresholds, validation rules, citation standard)
- **Section 7**: Output Structure (report sections, file naming, special deliverables)
- **Section 8**: Advanced Configuration (iterations, token budgets, hooks, MCP integrations)
- **Section 9**: Custom Prompts (global preamble, per-agent overrides, synthesis instructions, tone)

## Key Rules

- **Use AskUserQuestion for ALL interview questions.** Never assume answers.
- **One section at a time.** Complete each section before moving to the next.
- **Show preset defaults.** When a preset is loaded, display pre-filled values and ask the user to accept or customize.
- **Skip confirmed pre-filled fields.** If the user accepts a preset section, do not re-ask each sub-question.
- **Always preview before generating.** Follow the Preview Protocol from the skill to show the full engine summary.
- **Always confirm before writing files.** The user must explicitly approve before any files are generated.
- **Use templates for generation.** All generated files must use the templates in `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/templates/`.
- **Never hardcode timestamps.** Use bash to get the current date/time for `createdAt` fields.

## 4. Post-Generation

After generating all files:

1. List all generated files with paths and approximate line counts.
2. Suggest running `/test-engine` to validate the generated engine.
3. **Copy the install command to the user's project** so they can install the generated engine immediately:
   ```bash
   mkdir -p .claude/commands
   ```
   Then use the Write tool to copy the contents of `${CLAUDE_PLUGIN_ROOT}/commands/install-local-plugin.md` to `.claude/commands/install-local-plugin.md` in the user's project.
   Inform the user: "Copied `/install-local-plugin` command to your project. You can now run:"
   ```
   /install-local-plugin {OUTPUT_DIR}
   ```
4. Suggest running `claude --plugin-dir {OUTPUT_DIR}` as an alternative for quick local testing without formal installation.
5. Ask if the user wants to publish or push to a Git repository.
