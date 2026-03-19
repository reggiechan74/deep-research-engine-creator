---
name: Engine Creator
description: >-
  This skill should be used when the user asks to "create a research engine",
  "build a research plugin", "customize deep research", "make a domain-specific
  research tool", "design a research pipeline", "create engine", or wants to
  create specialized deep-research engines as standalone Claude Code plugins.
version: 1.9.0
---

# Engine Creator

Create domain-specialized deep-research engine plugins through a structured wizard interview. Collects domain identity, scope, source strategy, agent pipeline, quality framework, and output preferences, then generates a complete standalone Claude Code plugin. Two output modes: self-contained (full pipeline) or extension (overlay on base /deep-research). Uses progressive disclosure with domain presets for smart defaults.

---

## Wizard Interview Protocol

Guide the user through 9 sections sequentially. Use `AskUserQuestion` for every structured choice. Pre-fill sections 4-9 when a domain preset is selected. Skip re-asking confirmed pre-filled fields.

### Section 1: Domain Identity

1. **Engine name** -- Ask for kebab-case name (e.g. `patent-intelligence`). Validate pattern `^[a-z0-9]+(-[a-z0-9]+)*$`; suggest correction if invalid.
2. **Domain description** -- "What field does this engine research?"
3. **Target audience** -- "Who uses the research output?"
4. **Engine description** -- Auto-derive default: "A domain-specialized research engine for {domain}". Show to user: "Engine description for plugin manifest: [default]. Accept or customize?" via AskUserQuestion.
5. **Author** -- Attempt to read from git config: `git config user.name` and `git config user.email`. Show: "Author: {name} <{email}>. Accept or customize?" If git config unavailable, ask for name and email. These are optional — user can skip.
6. **Keywords** -- Auto-derive from domain + question types. Show: "Suggested keywords: [list]. Accept or customize?" via AskUserQuestion.
7. **Domain preset** -- AskUserQuestion: Legal Research, Market Intelligence, Academic Research, OSINT Investigation, Technical Due Diligence, Custom (no preset). If preset selected, read from `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/domain-presets/{preset-name}.json` and pre-fill sections 4-9. Inform user: "Loaded the {preset} preset -- you can accept or customize defaults."
8. **Output mode** -- AskUserQuestion: Self-contained (full pipeline, no dependencies) or Extension (overlay requiring base /deep-research plugin).

### Section 2: Research Scope & Objectives

1. **Question types** -- AskUserQuestion multiSelect: Landscape Analysis, Comparative Analysis, Trend Forecasting, Risk Assessment, Literature Review, Investigative/OSINT, Due Diligence, Custom
2. **Geographic scope** -- AskUserQuestion: Global, North America, Europe, Asia-Pacific, Specific Regions (follow-up), Custom
3. **Temporal focus** -- AskUserQuestion: Current State Only, Historical + Current, Trend Forecasting, All Timeframes
4. **Primary deliverable** -- AskUserQuestion: Briefing Document, Comprehensive Report, Analytical Assessment, Literature Review, Investigative Dossier, Custom

### Section 3: Sample Research Questions

1. Ask for 3-5 example research questions via AskUserQuestion text prompt.
2. Analyze samples to auto-suggest: source types needed, agent specializations, search template patterns, output structure elements (e.g., comparison matrix for comparative questions).
3. Present: "Based on your sample questions, I recommend..." with categorized suggestions.
4. AskUserQuestion: Accept All, Customize, Skip.

### Section 4: Source Strategy

Show current hierarchy from preset or sample analysis; build from scratch if no preset.

1. **Credibility tiers** -- For each tier 1-5, show name and sources. AskUserQuestion per tier: Accept or Customize.
2. **Preferred sources** -- "Any additional domains to prioritize?" Free text.
3. **Excluded sources** -- "Any domains to always exclude?" Free text.
4. **Filters** -- AskUserQuestion: No Filters, Language Only (ISO 639-1 codes), Geographic Only (country codes), Both.
5. **Search templates** -- Show existing. AskUserQuestion: Accept Current, Add New, Modify, Remove.

### Section 5: Agent Pipeline Design

1. AskUserQuestion: **Basic** (recommended structure, confirm tier assignments) or **Advanced** (configure each agent individually).
2. **Basic:** Show tier structure and agent list. AskUserQuestion: Accept, Add Agent, Remove Agent, Modify Agent.
3. **Advanced:** Per agent ask: ID (kebab-case), role, sub-agent type (AskUserQuestion: general-purpose, expert-instructor, intelligence-analyst), model (AskUserQuestion: sonnet, opus, haiku), specialization instructions. Then ask tier assignments and follow-up round settings.
4. **VVC agent:** When VVC is enabled (Section 6), automatically include `vvc-specialist` as a pipeline agent. This agent is NOT added to any tier's `agents` array — it runs in Phases 5-6, not Phase 2. Include it in `agentPipeline.agents` for file generation but do not assign it to tiers. The VVC agent definition uses `subagentType: "general-purpose"` (needs WebFetch for source verification, Read/Write/Edit for reports). Auto-derive specialization from the engine's domain.

### Section 6: Quality Framework

Show preset values or defaults; ask to confirm or customize:

1. **Confidence scoring** -- Show HIGH/MEDIUM/LOW/SPECULATIVE. AskUserQuestion: Accept or Customize per level.
2. **Minimum evidence** -- Show threshold. Accept or customize via free text.
3. **Validation rules** -- Show numbered list. AskUserQuestion: Accept, Add Rule, Remove Rule.
4. **Citation standard** -- AskUserQuestion: APA 7th (default), Bluebook, Chicago, Custom.

#### Citation Management

After configuring the citation standard, ask about source verification:

Use AskUserQuestion: "How should this engine verify cited sources?"
- Options:
  - "Spot-check (Recommended)" -- verify a random sample of HIGH-confidence citations
  - "Comprehensive" -- verify every cited source (thorough but slower)
  - "None" -- trust agent-reported citations without verification

Use AskUserQuestion: "Should sources be verified immediately when discovered, or in a batch after research?"
- Options:
  - "Probe on discovery (Recommended)" -- verify source accessibility when found (prevents wasted analysis on dead sources)
  - "Batch verification after research" -- verify all sources in a post-research pass

Use AskUserQuestion: "How should the engine handle dead links?"
- Options:
  - "Archive.org fallback (Recommended)" -- attempt Wayback Machine retrieval for dead URLs
  - "Flag only" -- mark dead links in the report but don't attempt recovery
  - "Exclude from HIGH claims" -- downgrade claims that rely solely on unreachable sources

Use AskUserQuestion: "What source freshness threshold should be enforced?"
- Options:
  - "2 years (Recommended)" -- flag sources older than 2 years
  - "5 years" -- more lenient for slower-moving domains
  - "1 year" -- strict for fast-moving domains
  - "No limit" -- no freshness requirement

Use AskUserQuestion: "Generate a standalone Citation Verification Report?"
- Options:
  - "Yes, for HIGH-confidence sources (Recommended)" -- audit HIGH-confidence citations
  - "Yes, for all sources" -- comprehensive audit
  - "No" -- skip verification report

#### Verification, Validation & Correction (VVC)

After citation management, configure the VVC pipeline:

Use AskUserQuestion: "Enable Verification, Validation & Correction (VVC)? Every deep research tool cites sources, but citations alone don't prevent hallucinations — the AI can cite a URL without accurately representing what it says. VVC goes further: it extracts every factual claim, re-fetches the cited source, and checks two things: (1) Is the source credible for this claim? (2) Was the source accurately represented? Failed claims are auto-corrected or flagged."
- Options:
  - "Yes, enable VVC (Recommended)" -- adds Phase 5 (verification) and Phase 6 (correction)
  - "No, skip VVC" -- Phase 4 produces the final report directly

If VVC enabled:

Use AskUserQuestion: "What percentage of MEDIUM-confidence claims should be verified? (HIGH is always 100%)"
- Options:
  - "100% (Recommended)" -- verify all MEDIUM claims (highest accuracy)
  - "75%" -- balanced verification depth
  - "50%" -- lighter verification
  - Custom (free text, 0-100)

Use AskUserQuestion: "What percentage of LOW-confidence claims should be verified?"
- Options:
  - "100% (Recommended)" -- verify all LOW confidence claims
  - "50%" -- moderate LOW claim verification
  - "25%" -- spot-check LOW claims
  - Custom (free text, 0-100)

Use AskUserQuestion: "What percentage of SPECULATIVE-confidence claims should be verified?"
- Options:
  - "100% (Recommended)" -- verify all SPECULATIVE claims
  - "50%" -- moderate SPECULATIVE claim verification
  - "0%" -- skip SPECULATIVE claim verification
  - Custom (free text, 0-100)

Use AskUserQuestion: "Customize claim type taxonomy? Default types: [VC] Verifiable Claim, [PO] Professional Opinion, [IE] Inferred/Extrapolated"
- Options:
  - "Accept defaults (Recommended)" -- use VC/PO/IE taxonomy
  - "Add domain-specific types" -- add custom types (e.g., [LH] Legal Holding, [SD] Statistical Data)

If adding custom types: ask for tag (2-4 uppercase letters), label, description, and whether it requires verification.

Use AskUserQuestion: "VVC tier behavior?"
- Options:
  - "Standard defaults (Recommended)" -- Quick: none, Standard: verify-only, Deep: full, Comprehensive: full
  - "Customize per tier" -- configure each tier individually

If customizing per tier: for each of Standard, Deep, Comprehensive, ask: none / verify-only / full. Quick is always "none".

#### Provenance (always on)

Inform the user — this is NOT a question:

- SHA-256 source hashing is enabled for all tiers
- Phase 4.5 provenance audit runs on Standard/Deep/Comprehensive tiers
- `--reverifiable` flag available to retain source snapshots
- No configuration needed — provenance is baked into every generated engine

### Section 7: Output Structure

1. **Report output directory** -- AskUserQuestion: "Where should research reports be saved? Each run creates a timestamped subdirectory under this path." Default: `./research-reports`. Common alternatives: `./output/reports`, `docs/research`, or a project-specific path. Accept or customize.
2. **Report sections** -- Show ordered list. AskUserQuestion: Accept, Add, Remove, Reorder.
3. **File naming** -- Show template (e.g. `{date}_{topic_slug}_research_report.md`). Accept or customize.
4. **Special deliverables** -- "Any special artifacts? (e.g., competitive matrix, patent family tree)" Free text or "None".

### Section 8: Advanced Configuration

1. AskUserQuestion: "Configure advanced settings?" Yes or No (use defaults).
2. If yes: max iterations (1-5, default 3), exploration depth (1-10, default 2), max WebFetch calls per agent (1-50, default 10), max follow-up agents for Comprehensive tier (1-5, default 2), token budgets (planning: 2000, research: 15000, synthesis: 8000, reporting: 10000, vvc: 8000, provenance: 5000), dashboard port (1024-65535, default 3847), custom hooks, MCP server integrations.
3. If no: use all defaults.

### Section 9: Custom Prompts

1. AskUserQuestion: "Customize agent prompts?" Yes or No (use preset defaults).
2. If yes: global preamble (free text), per-agent overrides (ask per agent: "Custom instructions for {role}?"), synthesis instructions, reporting tone.
3. If no: use preset values or leave empty.

---

## Config Assembly

After all sections complete:

1. Assemble `engine-config.json` matching schema at `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/templates/engine-config-schema.json`.
2. Set `schemaVersion` to `"1.0"`.
3. Set `engineMeta.createdAt` using bash: `TZ='America/New_York' date '+%Y-%m-%dT%H:%M:%S%:z'`. Never hardcode timestamps.
4. Set `engineMeta.createdBy` to `"deep-research-engine-creator/1.0.0"` and `version` to `"1.0.0"`.
5. Derive `displayName` from engine name: kebab-case to Title Case.
6. Always include `qualityFramework.provenance` with these defaults:
   ```json
   "provenance": {
     "enabled": true,
     "hashAlgorithm": "sha256",
     "reverifiableDefault": false,
     "auditPhase": {
       "tiers": ["standard", "deep", "comprehensive"]
     },
     "chainFormat": "[SHA-256]|[URL]|[TIMESTAMP]|[AGENT_ID]|[PREV_HASH]"
   }
   ```
7. Fill unanswered optional fields with sensible defaults or omit.
8. Validate all required fields. If any missing, ask user before proceeding.

---

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
3. Set operationalLessons: "No entries yet -- update after first research run with `/post-mortem`."

Store all values in engine-config.json under "_derived" key.

---

## Preview Protocol

Present to user before generating:

1. Engine identity: name, display name, domain, audience, version
2. Output mode (self-contained / extension)
3. File tree of all files to be generated
4. Agent pipeline table: Agent ID, Role, Sub-agent Type, Model, Active Tiers
5. Source hierarchy: tier names with top 3 sources each
6. Report sections list
7. Sample questions from section 3

Ask: "Ready to generate? Confirm or choose a section to modify." AskUserQuestion: Confirm and Generate, Modify a Section. If modifying, re-run that section, update config, re-preview.

---

## Generation Protocol

Execute after user confirms.

**Step 1 -- Output directory.** Ask where to save. Default: `./generated-engines/{{engineName}}/`. Store as `OUTPUT_DIR`.

**Step 2 -- Write engine-config.json.** Write the assembled config (including `_derived` section) as formatted JSON to `{OUTPUT_DIR}/engine-config.json`.

**Step 3 -- Generate engine files.** Run the generator script:

    python3 ${CLAUDE_PLUGIN_ROOT}/generator/generate.py {OUTPUT_DIR}/engine-config.json {OUTPUT_DIR}

The script reads engine-config.json (including _derived content), loads all templates,
performs placeholder substitution, and writes every output file deterministically.

If the script exits with error code 1 (validation), review the error message and fix
the config. Re-run the script.
If exit code 2 (template error), report the error to the user.
If exit code 0, proceed to Post-Generation.

---

## Post-Generation

After the generator script completes successfully:

1. The script has already verified all files exist and printed a summary.
2. Suggest: "Run `/test-engine {OUTPUT_DIR}` to validate config semantics."
3. Copy the install command to the user's project for immediate use:
   - Create `.claude/commands/` directory in the user's project if it doesn't exist.
   - Copy `${CLAUDE_PLUGIN_ROOT}/commands/install-local-plugin.md` to `.claude/commands/install-local-plugin.md`.
   - Inform the user: "Run `/install-local-plugin {OUTPUT_DIR}` to register the engine as an installed plugin."
4. Suggest: "Alternatively, run `claude --plugin-dir {OUTPUT_DIR}` for quick local testing without installation."
5. Ask: "Would you like to publish this engine to a marketplace or push to a Git repository?"

---

## Template Reference

Templates at `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/templates/`. The generator script (`generate.py`) handles all placeholder substitution automatically:

| Template | Purpose |
|---|---|
| `orchestrator-skill.md.tmpl` | Self-contained engine orchestrator SKILL.md (~150-200 lines) |
| `standards.md.tmpl` | Confidence scoring, source credibility, citation rules |
| `research-protocol.md.tmpl` | Search protocol, iterative refinement, file isolation, WebFetch cap |
| `provenance.md.tmpl` | Phase 2.5 batch hashing, Phase 4.5 provenance audit |
| `vvc-pipeline.md.tmpl` | VVC Phases 5-6 instructions (conditional on VVC enabled) |
| `extension-skill.md.tmpl` | Extension engine SKILL.md |
| `command-template.md.tmpl` | /research command |
| `sources-command-template.md.tmpl` | /sources command |
| `agent-template.md.tmpl` | Per-agent definition |
| `plugin-json.tmpl` | Plugin manifest |
| `readme-template.md.tmpl` | Plugin README |
| `dashboard-server.js.tmpl` | Dashboard SSE server (Node.js, zero dependencies) |
| `dashboard.html.tmpl` | Live research dashboard (self-contained HTML) |
| `engine-config-schema.json` | Config validation schema |
| `preset-schema.json` | Domain preset validation schema |
| `plugin-manifest-schema.json` | Plugin manifest validation schema |

Domain presets at `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/domain-presets/`: `legal-research.json`, `market-intelligence.json`, `academic-research.json`, `osint-investigation.json`, `technical-due-diligence.json`.
