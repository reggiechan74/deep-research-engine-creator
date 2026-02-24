---
name: Engine Creator
description: >-
  This skill should be used when the user asks to "create a research engine",
  "build a research plugin", "customize deep research", "make a domain-specific
  research tool", "design a research pipeline", "create engine", or wants to
  create specialized deep-research engines as standalone Claude Code plugins.
version: 1.3.0
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

### Section 7: Output Structure

1. **Report output directory** -- AskUserQuestion: "Where should research reports be saved? Each run creates a timestamped subdirectory under this path." Default: `./research-reports`. Common alternatives: `./output/reports`, `docs/research`, or a project-specific path. Accept or customize.
2. **Report sections** -- Show ordered list. AskUserQuestion: Accept, Add, Remove, Reorder.
3. **File naming** -- Show template (e.g. `{date}_{topic_slug}_research_report.md`). Accept or customize.
4. **Special deliverables** -- "Any special artifacts? (e.g., competitive matrix, patent family tree)" Free text or "None".

### Section 8: Advanced Configuration

1. AskUserQuestion: "Configure advanced settings?" Yes or No (use defaults).
2. If yes: max iterations (1-5, default 3), exploration depth (1-10, default 5), token budgets (planning: 2000, research: 15000, synthesis: 8000, reporting: 10000, vvc: 8000), custom hooks, MCP server integrations.
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
7. Sample questions from section 3

Ask: "Ready to generate? Confirm or choose a section to modify." AskUserQuestion: Confirm and Generate, Modify a Section. If modifying, re-run that section, update config, re-preview.

---

## Generation Protocol

Execute sequentially after user confirms.

**Step 1 -- Output directory.** Ask where to save. Default: `./generated-engines/{{engineName}}/`. Store as `OUTPUT_DIR`.

**Step 2 -- Create directories.** Under `OUTPUT_DIR`: `.claude-plugin/`, `commands/`, `agents/`, `skills/{skillDirName}/` (skillDirName = engineMeta.name).

**Step 3 -- plugin.json.** Read `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/templates/plugin-json.tmpl`, replace placeholders from engineMeta, write to `{OUTPUT_DIR}/.claude-plugin/plugin.json`.
Replace `{{engineDescription}}` with `engineMeta.description` (default: "A domain-specialized research engine for {domain}").
Replace `{{authorName}}` with `engineMeta.author.name` (default: empty string).
Replace `{{authorEmail}}` with `engineMeta.author.email`. **If the email value is empty or `engineMeta.author.email` is absent, remove the entire `"email": "{{authorEmail}}"` line from the generated plugin.json output** (including the trailing comma if it becomes the last property in the author object). Do not emit `"email": ""` — an empty string fails email format validation.
Replace `{{keywords}}` with `engineMeta.keywords` formatted as `"keyword1", "keyword2", "keyword3"` (quoted, comma-separated).

**Step 4 -- engine-config.json.** Write assembled config as formatted JSON to `{OUTPUT_DIR}/engine-config.json`.

**Step 5 -- /research command.** Read `command-template.md.tmpl`, replace placeholders. For `{{tierSummary}}`, generate markdown table from agentPipeline.tiers. Write to `{OUTPUT_DIR}/commands/research.md`.

**Step 6 -- /sources command.** Read `sources-command-template.md.tmpl`, replace placeholders. Format `{{sourceHierarchyTable}}` and `{{searchTemplatesTable}}` as markdown tables. Write to `{OUTPUT_DIR}/commands/sources.md`.

**Step 7 -- Agent files.** For EACH agent: read `agent-template.md.tmpl`, replace with agent-specific values. Cycle `{{color}}` through blue, magenta, yellow. Insert `{{promptOverride}}` from prompts.agentOverrides[agentId] as "## Custom Instructions" if present. Format `{{sourceHierarchy}}` and `{{searchTemplates}}` as text blocks. Write to `{OUTPUT_DIR}/agents/{agentId}.md`.

**Step 8 -- SKILL.md.** Select template by mode: self-contained reads `base-research-skill.md.tmpl`, extension reads `extension-skill.md.tmpl`. For extension mode: before template substitution, verify the base `/deep-research` skill exists. Check `.claude/commands/deep-research.md` first, then `skills/*/SKILL.md` containing "deep-research". If found, set `{{baseSkillPath}}` to the discovered path. If not found, warn user: "Base /deep-research skill not found. Extension mode requires it. Generate as self-contained instead?" and offer AskUserQuestion. Replace ALL placeholders:
- Simple values: direct substitution
- Arrays (`{{reportSections}}`, `{{preferredSites}}`): markdown numbered list
- Objects (`{{tierConfigTable}}`): markdown table rows
- Nested (`{{agentDeploymentBlocks}}`): one block per agent with ID, role, model, specialization, tools, prompt override
- `{{subAgentList}}`: research-planning-specialist, synthesis-specialist, research-reporting-specialist, plus custom agents
- `{{fileStructure}}`: per-agent file entries (Claims, Bibliography)
- Missing optionals: sensible defaults or empty string

#### Placeholder Derivation Rules

Some placeholders are not direct config fields but are derived from config values. Apply these rules:

| Placeholder | Derivation Rule |
|---|---|
| `{{quickTierDescription}}` | Build from `tiers.quick.agents`: "Single-agent lookup using [first agent's role]" |
| `{{standardTierDescription}}` | Build from `tiers.standard.agents`: "[N] agents: [role1], [role2]" |
| `{{deepTierDescription}}` | Build from `tiers.deep.agents`: "Full pipeline with [N] agents: [role1], [role2], [role3]" |
| `{{comprehensiveTierDescription}}` | Build from `tiers.comprehensive.agents` + followUpRound: "All [N] agents + follow-up round" |
| `{{agentSpecialization}}` | Concatenate all agent `specialization` strings, joined by "; " |
| `{{quickAgentId}}` | Fully qualified agent name: `{{engineName}}:[first agent ID from tiers.quick.agents]`. Example: `patent-intelligence-engine:patent-search-specialist` |
| `{{tierConfigTable}}` | Build markdown table rows from `tiers` config, one row per tier, columns: Tier, Planning (Yes/No), Research Agents (fully qualified: `{{engineName}}:[agentId]`), Synthesis (Yes/No), Report (Inline/Full), User Gate |
| `{{agentDeploymentBlocks}}` | For each agent in `agents` array, generate a deployment block: "#### Agent: [role]\n\nDeploy **{{engineName}}:[id]** (model: [model], type: {{engineName}}:[id]) with specialization:\n\n[specialization]\n\n[promptOverride if present]". **Important:** Custom agents defined in the plugin's `agents/` directory MUST use the fully qualified `{{engineName}}:[agentId]` format. Built-in pipeline agents (research-planning-specialist, synthesis-specialist, research-reporting-specialist) do NOT get the prefix. |
| `{{subAgentList}}` | "- research-planning-specialist\n- synthesis-specialist\n- research-reporting-specialist\n" + one line per custom agent: "- {{engineName}}:[id] ([role])". If VVC enabled, also append: "- vvc-specialist (Verification, Validation & Correction Specialist)" |
| `{{fileStructure}}` | For each agent, generate two lines: "├── [TOPIC_SLUG]_Claims_[agentId].md\n├── [TOPIC_SLUG]_[agentId]_Bibliography.md" |
| `{{verificationModeInstructions}}` | Expand from `citationManagement.verificationMode`: "none" → "Source verification is disabled. Trust agent-reported citations without independent verification."; "spot-check" → "Verify a random sample of HIGH-confidence citations (minimum 3 or 20% of HIGH citations, whichever is greater). Record verification results in Methodology_Log.md."; "comprehensive" → "Verify every cited source. Check URL accessibility, confirm source content supports the claim, and record all results in a dedicated verification pass." |
| `{{deadLinkInstructions}}` | Expand from `citationManagement.deadLinkHandling`: "flag-only" → "Mark dead links with [DEAD LINK] tag in the bibliography. Do not attempt recovery."; "archive-fallback" → "Attempt Wayback Machine retrieval at https://web.archive.org/web/*/[URL]. If archived version found, use it and note [ARCHIVED: date] in bibliography. If not found, mark as [DEAD LINK]."; "exclude-from-high" → "Downgrade any claim that relies solely on unreachable sources from HIGH to MEDIUM confidence. Note the downgrade reason in the claims table." |
| `{{verificationReportConfig}}` | If `verificationReport.enabled` is true: "Generate a standalone Citation Verification Report. Scope: [scope value]. Include summary statistics, per-citation verification table, issues found, and remediation recommendations." If false: "Verification report generation is disabled." |
| `{{operationalLessons}}` | Default: "No entries yet — update after first research run with `/post-mortem`." |
| `{{maxIterations}}` | From `advanced.maxIterationsPerQuestion` (default: 3) |
| `{{explorationDepth}}` | From `advanced.explorationDepth` (default: 5) |
| `{{planningBudget}}` | From `advanced.tokenBudgets.planning` (default: 2000) |
| `{{researchBudget}}` | From `advanced.tokenBudgets.research` (default: 15000) |
| `{{synthesisBudget}}` | From `advanced.tokenBudgets.synthesis` (default: 8000) |
| `{{reportingBudget}}` | From `advanced.tokenBudgets.reporting` (default: 10000) |
| `{{pipelinePhaseCount}}` | If `qualityFramework.vvc.enabled` is true: "seven"; otherwise: "five" |
| `{{pipelinePhaseDescription}}` | If VVC enabled: "seven-phase"; otherwise: "five-phase" |
| `{{phase4Name}}` | If VVC enabled: "Draft Reporting"; otherwise: "Professional Reporting" |
| `{{phase4Description}}` | If VVC enabled: "Draft report generation with claim tagging for VVC verification"; otherwise: "Comprehensive report generation with consolidated bibliography" |
| `{{phase4ReportType}}` | If VVC enabled: "draft"; otherwise: "final" |
| `{{phase4OutputFile}}` | If VVC enabled: "Draft_Report.md"; otherwise: "Comprehensive_Report.md" |
| `{{vvcPhaseLines}}` | If VVC enabled: "6. **Phase 5: VVC-Verify** -- Verify draft report claims against cited sources, produce verification report\n7. **Phase 6: VVC-Correct** -- Implement corrections, produce final Comprehensive Report + correction log"; otherwise: empty string |
| `{{vvcClaimTaxonomyBlock}}` | If VVC enabled: generate "### Claim Type Taxonomy" section listing each claimType from config (tag, label, description, requiresVerification) plus "### VVC Verification Scope" table showing HIGH/MEDIUM/LOW/SPECULATIVE percentages; otherwise: empty string |
| `{{vvcClaimTaggingInstructions}}` | If VVC enabled: "- **CLAIM TAGGING (REQUIRED):** Tag every factual assertion with its claim type: `[VC]` for verifiable claims with cited sources, `[PO]` for professional opinions/analytical judgments, `[IE]` for inferences/extrapolations. Place tags at the end of each claim sentence before the citation. Example: 'Toyota invested $142M in solid-state battery research [VC][^3]'. This tagging is essential for the VVC verification phase."; otherwise: empty string |
| `{{vvcVerifyPhaseBlock}}` | If VVC enabled AND tier behavior is "verify-only" or "full": generate complete Phase 5 VVC-Verify section with instructions to deploy **vvc-specialist** to: read draft report + all bibliographies, extract all [VC] claims with cited sources and confidence tiers, apply verification scope ({HIGH}% HIGH, {MEDIUM}% MEDIUM, {LOW}% LOW, {SPECULATIVE}% SPECULATIVE), per-claim protocol (locate source → extract quote → analyze alignment → classify as CONFIRMED/PARAPHRASED/OVERSTATED/UNDERSTATED/DISPUTED/UNSUPPORTED/SOURCE_UNAVAILABLE → recommend KEEP/REVISE/DOWNGRADE/REMOVE/REPLACE_SOURCE → write corrected text per recommendation rules), corrected text rules (KEEP: "---", REVISE: rewritten claim reflecting accurate source content, DOWNGRADE: claim with qualifying language and lowered confidence tier, REMOVE: "[REMOVE]", REPLACE_SOURCE: corrected claim text citing new source + replacement source URL found during verification), output `_VVC_Verification_Report.md` with summary stats + per-claim table including Corrected Text and New Source columns; otherwise: empty string |
| `{{vvcCorrectPhaseBlock}}` | If VVC enabled AND tier behavior is "full": generate complete Phase 6 VVC-Correct section with instructions to deploy **vvc-specialist** (second pass) to: read verification report per-claim table, apply corrected text mechanically into draft report (REVISE/DOWNGRADE: substitute Corrected Text verbatim, REMOVE: delete claim and adjust surrounding narrative for coherence, REPLACE_SOURCE: substitute Corrected Text and update bibliography with New Source), preserve all KEEP/CONFIRMED claims unchanged, NO independent rewriting or source searching — all corrections come from the Phase 5 verification table, output `_Comprehensive_Report.md` (final) + `_VVC_Correction_Log.md` + Verification Statement appendix; if tier behavior is "verify-only": empty string (Phase 4 draft becomes final with verification report alongside) |
| `{{vvcFileStructure}}` | If VVC enabled: "├── [TOPIC_SLUG]_Draft_Report.md\n├── [TOPIC_SLUG]_VVC_Verification_Report.md\n├── [TOPIC_SLUG]_VVC_Correction_Log.md  # When tier behavior is 'full'"; otherwise: empty string |
| `{{vvcFeatureBullets}}` | If VVC enabled: "- **Claim verification, not just citations (VVC)** -- citations are URLs; they don't prove the AI read the source correctly. VVC extracts every [VC]-tagged claim, re-fetches the cited source, and checks: (1) Is the source credible? (2) Was it accurately represented? Failed claims are auto-corrected or flagged. Citations can hallucinate. Verified claims can't.\n- **Claim type taxonomy** -- claims tagged as [VC] (verifiable), [PO] (professional opinion), or [IE] (inferred) to focus verification effort\n- **Tier-aware VVC** -- Quick: no VVC, Standard: verify-only, Deep/Comprehensive: full verify+correct"; otherwise: empty string |
| `{{vvcBudgetLine}}` | If VVC enabled: "VVC:            {vvcBudget} tokens output max (verification + correction combined)"; otherwise: empty string. Default vvcBudget: from `advanced.tokenBudgets.vvc` (default: 8000) |
| `{{vvcSubAgentNote}}` | If VVC enabled: "The vvc-specialist is a pipeline agent that runs in Phases 5-6 (post-reporting). It does NOT participate in Phase 2 research."; otherwise: empty string |
| `{{vvcExtensionOverride}}` | If VVC enabled: generate "#### VVC Configuration Override" section listing: enabled, claim types, verification scope (HIGH%, MEDIUM%, LOW%, SPECULATIVE%), tier behavior per tier; otherwise: empty string |
| `{{vvcTierNote}}` | If VVC enabled: "**VVC:** Quick: none | Standard: verify-only | Deep: full | Comprehensive: full"; otherwise: empty string |
| `{{vvcReadmeSection}}` | If VVC enabled: generate "## Verification, Validation & Correction (VVC)" section. Lead with the key distinction: every research tool cites sources, but a citation is just a URL -- it doesn't mean the AI read the source correctly. VVC goes further by extracting claims, re-fetching sources, and verifying both source credibility and accurate representation. Then describe claim types, verification scope, and tier behavior; otherwise: empty string |
| `{{scopeDisciplineBlock}}` | Always generate the following conditional block (both modes included in template output): "**If CONTEXT_MODE is standalone (default -- no `--extend` flag):**\n\n### Scope Discipline\n\nYour research scope is LIMITED to the user's stated topic.\n\n- Do NOT read files outside BASE_DIR\n- Do NOT reference prior research runs, their files, or their findings\n- Do NOT incorporate project context from CLAUDE.md into research scope\n- Do NOT use observation history or session context to expand the topic\n- Generate ALL research questions strictly from the user's topic string and your domain expertise in {domain}\n- If the topic is ambiguous, interpret it as a general domain question -- do not assume it relates to any specific project or prior work\n- Every section in the outline must map directly to the stated topic. Remove any section that requires project-specific knowledge to justify.\n\n**If CONTEXT_MODE is extend (`--extend` flag present):**\n\n### Scope Discipline\n\nThis research EXTENDS prior work in this project. You may:\n\n- Read prior research files in the working directory for context\n- Reference project context from CLAUDE.md to inform research scope\n- Build on findings from previous research runs\n- Frame new research questions that deepen or broaden prior findings\n\nClearly mark which sections build on prior work vs. new investigation." |

Write to `{OUTPUT_DIR}/skills/{skillDirName}/SKILL.md`.

**Step 9 -- README.md.** Read `readme-template.md.tmpl`, replace placeholders. Format `{{agentTable}}`, `{{sourceTable}}` as markdown tables. Format `{{sampleQuestions}}` as numbered list, `{{qualitySummary}}` as brief text. Write to `{OUTPUT_DIR}/README.md`.

---

## Post-Generation

After all files written:

1. List all generated files with paths relative to OUTPUT_DIR and approximate line counts.
2. Suggest: "Run `/test-engine {OUTPUT_DIR}` to validate against schema and check for placeholder residue."
3. Copy the install command to the user's project for immediate use:
   - Create `.claude/commands/` directory in the user's project if it doesn't exist.
   - Copy `${CLAUDE_PLUGIN_ROOT}/commands/install-local-plugin.md` to `.claude/commands/install-local-plugin.md`.
   - Inform the user: "Run `/install-local-plugin {OUTPUT_DIR}` to register the engine as an installed plugin."
4. Suggest: "Alternatively, run `claude --plugin-dir {OUTPUT_DIR}` for quick local testing without installation."
5. Ask: "Would you like to publish this engine to a marketplace or push to a Git repository?"

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
| `preset-schema.json` | Domain preset validation schema |
| `plugin-manifest-schema.json` | Plugin manifest validation schema |

Domain presets at `${CLAUDE_PLUGIN_ROOT}/skills/engine-creator/domain-presets/`: `legal-research.json`, `market-intelligence.json`, `academic-research.json`, `osint-investigation.json`, `technical-due-diligence.json`.
