---
name: Engine Creator
description: >-
  This skill should be used when the user asks to "create a research engine",
  "build a research plugin", "customize deep research", "make a domain-specific
  research tool", "design a research pipeline", "create engine", or wants to
  create specialized deep-research engines as standalone Claude Code plugins.
version: 1.0.0
---

# Engine Creator

Create domain-specialized deep-research engine plugins through a structured wizard interview. Collects domain identity, scope, source strategy, agent pipeline, quality framework, and output preferences, then generates a complete standalone Claude Code plugin. Two output modes: self-contained (full pipeline) or extension (overlay on base /deep-research). Uses progressive disclosure with domain presets for smart defaults.

---

## Wizard Interview Protocol

Guide the user through 8 sections sequentially. Use `AskUserQuestion` for every structured choice. Pre-fill sections 3-8 when a domain preset is selected. Skip re-asking confirmed pre-filled fields.

### Section 1: Domain Identity

1. **Engine name** -- Ask for kebab-case name (e.g. `patent-intelligence`). Validate pattern `^[a-z0-9]+(-[a-z0-9]+)*$`; suggest correction if invalid.
2. **Domain description** -- "What field does this engine research?"
3. **Target audience** -- "Who uses the research output?"
4. **Domain preset** -- AskUserQuestion: Legal Research, Market Intelligence, Academic Research, OSINT Investigation, Technical Due Diligence, Custom (no preset). If preset selected, read from `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/domain-presets/{preset-name}.json` and pre-fill sections 3-8. Inform user: "Loaded the {preset} preset -- you can accept or customize defaults."
5. **Output mode** -- AskUserQuestion: Self-contained (full pipeline, no dependencies) or Extension (overlay requiring base /deep-research plugin).

### Section 2: Research Scope & Objectives

1. **Question types** -- AskUserQuestion multiSelect: Landscape Analysis, Comparative Analysis, Trend Forecasting, Risk Assessment, Literature Review, Investigative/OSINT, Due Diligence, Custom
2. **Geographic scope** -- AskUserQuestion: Global, North America, Europe, Asia-Pacific, Specific Regions (follow-up), Custom
3. **Temporal focus** -- AskUserQuestion: Current State Only, Historical + Current, Trend Forecasting, All Timeframes
4. **Primary deliverable** -- AskUserQuestion: Briefing Document, Comprehensive Report, Analytical Assessment, Literature Review, Investigative Dossier, Custom

### Section 2.5: Sample Research Questions

1. Ask for 3-5 example research questions via AskUserQuestion text prompt.
2. Analyze samples to auto-suggest: source types needed, agent specializations, search template patterns, output structure elements (e.g., comparison matrix for comparative questions).
3. Present: "Based on your sample questions, I recommend..." with categorized suggestions.
4. AskUserQuestion: Accept All, Customize, Skip.

### Section 3: Source Strategy

Show current hierarchy from preset or sample analysis; build from scratch if no preset.

1. **Credibility tiers** -- For each tier 1-5, show name and sources. AskUserQuestion per tier: Accept or Customize.
2. **Preferred sources** -- "Any additional domains to prioritize?" Free text.
3. **Excluded sources** -- "Any domains to always exclude?" Free text.
4. **Filters** -- AskUserQuestion: No Filters, Language Only (ISO 639-1 codes), Geographic Only (country codes), Both.
5. **Search templates** -- Show existing. AskUserQuestion: Accept Current, Add New, Modify, Remove.

### Section 4: Agent Pipeline Design

1. AskUserQuestion: **Basic** (recommended structure, confirm tier assignments) or **Advanced** (configure each agent individually).
2. **Basic:** Show tier structure and agent list. AskUserQuestion: Accept, Add Agent, Remove Agent, Modify Agent.
3. **Advanced:** Per agent ask: ID (kebab-case), role, sub-agent type (AskUserQuestion: general-purpose, expert-instructor, intelligence-analyst), model (AskUserQuestion: sonnet, opus, haiku), specialization instructions. Then ask tier assignments and follow-up round settings.

### Section 5: Quality Framework

Show preset values or defaults; ask to confirm or customize:

1. **Confidence scoring** -- Show HIGH/MEDIUM/LOW/SPECULATIVE. AskUserQuestion: Accept or Customize per level.
2. **Minimum evidence** -- Show threshold. Accept or customize via free text.
3. **Validation rules** -- Show numbered list. AskUserQuestion: Accept, Add Rule, Remove Rule.
4. **Citation standard** -- AskUserQuestion: APA 7th (default), Bluebook, Chicago, Custom.

### Section 6: Output Structure

1. **Report sections** -- Show ordered list. AskUserQuestion: Accept, Add, Remove, Reorder.
2. **File naming** -- Show template (e.g. `{date}_{topic_slug}_research_report.md`). Accept or customize.
3. **Special deliverables** -- "Any special artifacts? (e.g., competitive matrix, patent family tree)" Free text or "None".

### Section 7: Advanced Configuration

1. AskUserQuestion: "Configure advanced settings?" Yes or No (use defaults).
2. If yes: max iterations (1-5, default 3), token budgets (planning: 2000, research: 15000, synthesis: 8000, reporting: 10000), custom hooks, MCP server integrations.
3. If no: use all defaults.

### Section 8: Custom Prompts

1. AskUserQuestion: "Customize agent prompts?" Yes or No (use preset defaults).
2. If yes: global preamble (free text), per-agent overrides (ask per agent: "Custom instructions for {role}?"), synthesis instructions, reporting tone.
3. If no: use preset values or leave empty.

---

## Config Assembly

After all sections complete:

1. Assemble `engine-config.json` matching schema at `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/templates/engine-config-schema.json`.
2. Set `schemaVersion` to `"1.0"`.
3. Set `engineMeta.createdAt` using bash: `TZ='America/New_York' date -u '+%Y-%m-%dT%H:%M:%SZ'`. Never hardcode timestamps.
4. Set `engineMeta.createdBy` to `"deep-research-engine-creator/1.0.0"` and `version` to `"1.0.0"`.
5. Derive `displayName` from engine name: kebab-case to Title Case.
6. Fill unanswered optional fields with sensible defaults or omit.
7. Validate all required fields. If any missing, ask user before proceeding.

---

## Preview Protocol

Present to user before generating:

1. Engine identity: name, display name, domain, audience, version
2. Output mode (self-contained / extension)
3. File tree of all files to be generated
4. Agent pipeline table: Agent ID, Role, Sub-agent Type, Model, Active Tiers
5. Source hierarchy: tier names with top 3 sources each
6. Report sections list
7. Sample questions from section 2.5

Ask: "Ready to generate? Confirm or choose a section to modify." AskUserQuestion: Confirm and Generate, Modify a Section. If modifying, re-run that section, update config, re-preview.

---

## Generation Protocol

Execute sequentially after user confirms.

**Step 1 -- Output directory.** Ask where to save. Default: `./generated-engines/{{engineName}}/`. Store as `OUTPUT_DIR`.

**Step 2 -- Create directories.** Under `OUTPUT_DIR`: `.claude-plugin/`, `commands/`, `agents/`, `skills/{skillDirName}/` (skillDirName = engineMeta.name).

**Step 3 -- plugin.json.** Read `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/templates/plugin-json.tmpl`, replace placeholders from engineMeta, write to `{OUTPUT_DIR}/.claude-plugin/plugin.json`.

**Step 4 -- engine-config.json.** Write assembled config as formatted JSON to `{OUTPUT_DIR}/engine-config.json`.

**Step 5 -- /research command.** Read `command-template.md.tmpl`, replace placeholders. For `{{tierSummary}}`, generate markdown table from agentPipeline.tiers. Write to `{OUTPUT_DIR}/commands/research.md`.

**Step 6 -- /sources command.** Read `sources-command-template.md.tmpl`, replace placeholders. Format `{{sourceHierarchyTable}}` and `{{searchTemplatesTable}}` as markdown tables. Write to `{OUTPUT_DIR}/commands/sources.md`.

**Step 7 -- Agent files.** For EACH agent: read `agent-template.md.tmpl`, replace with agent-specific values. Cycle `{{color}}` through blue, magenta, yellow. Insert `{{promptOverride}}` from prompts.agentOverrides[agentId] as "## Custom Instructions" if present. Format `{{sourceHierarchy}}` and `{{searchTemplates}}` as text blocks. Write to `{OUTPUT_DIR}/agents/{agentId}.md`.

**Step 8 -- SKILL.md.** Select template by mode: self-contained reads `base-research-skill.md.tmpl`, extension reads `extension-skill.md.tmpl`. Replace ALL placeholders:
- Simple values: direct substitution
- Arrays (`{{reportSections}}`, `{{preferredSites}}`): markdown numbered list
- Objects (`{{tierConfigTable}}`): markdown table rows
- Nested (`{{agentDeploymentBlocks}}`): one block per agent with ID, role, model, specialization, tools, prompt override
- `{{subAgentList}}`: research-planning-specialist, synthesis-specialist, research-reporting-specialist, plus custom agents
- `{{fileStructure}}`: per-agent file entries (Claims, Bibliography)
- Missing optionals: sensible defaults or empty string

Write to `{OUTPUT_DIR}/skills/{skillDirName}/SKILL.md`.

**Step 9 -- README.md.** Read `readme-template.md.tmpl`, replace placeholders. Format `{{agentTable}}`, `{{sourceTable}}` as markdown tables. Format `{{sampleQuestions}}` as numbered list, `{{qualitySummary}}` as brief text. Write to `{OUTPUT_DIR}/README.md`.

---

## Post-Generation

After all files written:

1. List all generated files with paths relative to OUTPUT_DIR and approximate line counts.
2. Suggest: "Run `/test-engine {OUTPUT_DIR}` to validate against schema and check for placeholder residue."
3. Suggest: "Run `claude --plugin-dir {OUTPUT_DIR}` to test the plugin locally."
4. Ask: "Would you like to publish this engine to a marketplace or push to a Git repository?"

---

## Template Reference

Templates at `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/templates/`:

| Template | Purpose |
|---|---|
| `base-research-skill.md.tmpl` | Self-contained engine SKILL.md |
| `extension-skill.md.tmpl` | Extension engine SKILL.md |
| `command-template.md.tmpl` | /research command |
| `sources-command-template.md.tmpl` | /sources command |
| `agent-template.md.tmpl` | Per-agent definition |
| `plugin-json.tmpl` | Plugin manifest |
| `readme-template.md.tmpl` | Plugin README |
| `engine-config-schema.json` | Config validation schema |

Domain presets at `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/domain-presets/`: `legal-research.json`, `market-intelligence.json`, `academic-research.json`, `osint-investigation.json`, `technical-due-diligence.json`.
