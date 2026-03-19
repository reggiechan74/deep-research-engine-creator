# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.9.0] - 2026-03-19

### Added
- **Deterministic Python generator** (`plugin/generator/generate.py`) -- replaces LLM-driven file generation with a deterministic script. Zero dependencies (Python 3 stdlib only). Validates config, applies 90+ placeholder derivation rules, reads templates, writes all output files
- **`_derived` config section** -- LLM pre-computes creative content (agent examples, body blocks, first actions, scope discipline) during wizard, stores in engine-config.json for deterministic substitution
- **Generator test suite** (`plugin/generator/tests/test_generate.py`) -- unit tests for config loading, validation, placeholder derivation, file generation, extension mode, and end-to-end patent engine generation
- **Extension mode support** in generator -- single-SKILL.md output from extension template

### Changed
- SKILL.md Generation Protocol reduced from 9 steps + 74 derivation rules to 3 steps (output dir, write config, run script)
- `/test-engine` simplified: removed 5 checks made impossible by deterministic generation (placeholder residue, line count, per-fetch hashing, shared file writes, dashboard assets)
- `engine-config-schema.json` now requires `_derived` top-level key

### Removed
- LLM-driven file generation (Steps 1-9 with manual placeholder substitution) -- replaced by `generate.py`
- Placeholder Derivation Rules prose table in SKILL.md -- rules now implemented as Python code

## [1.8.0] - 2026-03-19

### Added
- **Incremental Write Protocol** -- agents now write findings to disk after each research question instead of accumulating all findings for a single write at the end. Prevents silent data loss when output exceeds the model's token limit
- **Agent Status Protocol** -- agents maintain structured JSON status files (`_status/[AgentID].json`) with real-time progress: questions completed, activity state, WebFetch budget usage, claims/sources counts
- **Live Research Dashboard** -- real-time web dashboard ("Dark Ops Console" aesthetic) showing pipeline phases, agent progress, and activity states. Node.js SSE server with `fs.watch` for instant updates. Launched automatically for Standard/Deep/Comprehensive tiers
- **Phase 2 Output Verification** -- orchestrator verifies agent output files exist and are non-empty before proceeding to synthesis. Classifies agents as HEALTHY/PARTIAL/FAILED/EMPTY and halts pipeline if all agents failed
- **Agent Constraints** -- explicit no-spawn rule prevents Phase 2 agents from creating sub-agents or background tasks, closing an uncontrolled recursion path
- **Pipeline state tracking** -- `_pipeline.json` tracks all phase transitions with tier-aware phase inclusion (VVC phases, comprehensive follow-up, provenance audit)
- `dashboardPort` advanced config option (default: 3847)
- Dashboard template files: `dashboard-server.js.tmpl`, `dashboard.html.tmpl`
- Test checks 4n-4r for observability validation

### Fixed
- Duplicate test check IDs (4h/4i/4j appeared twice) renumbered to 4k/4l/4m

### Changed
- Template count increased from 11 to 13 `.tmpl` files
- Patent Intelligence Engine example regenerated with observability features

## [1.7.0] - 2026-03-18

### Fixed
- **VVC specialist agent was a carbon copy of research agent** (C-1, C-2) -- VVC agent now receives verification-specific instructions, examples, and First Actions instead of inheriting research protocol content. Pre-computed placeholder blocks (`{{agentExamplesBlock}}`, `{{agentBodyBlock}}`, `{{agentFirstActionsBlock}}`) differentiate VVC from research agents at generation time
- **Recursive exploration exceeded WebFetch budget** (C-3) -- replaced "Recursive web exploration up to N levels deep" with "Follow-on link exploration" and budget reservation language ("Reserve at least 6 WebFetch calls for primary research queries"). Default exploration depth changed from 5 to 2
- **`--no-vvc` missing from command argument-hint** (C-4) -- added `{{vvcArgumentHint}}` placeholder that conditionally appends `[--no-vvc]` when VVC is enabled
- **Hardcoded research examples in VVC agent YAML** (H-1) -- replaced with `{{agentExamplesBlock}}` placeholder that generates verification-specific examples for VVC agents
- **Probe-on-discovery lacked budget guidance** (H-2) -- added budget note: reserve 4 WebFetch calls for content retrieval, limit probes to top 6 candidate URLs, skip Tier 1 government domains
- **Citation verification protocol unorchestrated** (H-3) -- Phase 4.5 updated to "Provenance Audit & Citation Verification" with explicit steps for URL liveness, source freshness, and dead link handling
- **VVC WebFetch cap insufficient** (H-4) -- VVC agent now gets `{{vvcWebFetchCap}}` (default: 30, formula: `min(maxWebFetchesPerAgent * 3, 50)`) instead of sharing the research agent cap (default: 10)
- **Comprehensive follow-up undefined** (H-5) -- added Phase 3.5: Comprehensive Follow-Up with scoped gap closure, max `{{comprehensiveFollowUpAgentCap}}` agents (default: 2), one round only
- **Trailing "Now executing research deployment" text** (H-6) -- removed from orchestrator template
- **Provenance budget not parameterized** (M-1) -- replaced hardcoded "5K tokens" with `{{provenanceBudget}}` (default: 5000)
- **Token limit mismatch** (M-2) -- aligned chat response limit from 500 to 450 tokens in research-protocol template
- **Claim taxonomy duplicated** (M-3) -- standards.md now contains a brief `### Claim Taxonomy (VVC)` cross-reference pointing to `vvc-pipeline.md` instead of duplicating the full table
- **Redundant Domain Context section** (M-4) -- removed from agent template; domain context already provided via `{{promptOverride}}`

### Added
- **Phase 3.5: Comprehensive Follow-Up** -- post-synthesis gap closure for Comprehensive tier only. Reviews synthesis report gaps, re-deploys up to 2 agents for targeted follow-up, merges findings. One round, no recursion
- **Split template architecture** -- monolithic `base-research-skill.md.tmpl` replaced with 5 focused templates: `orchestrator-skill.md.tmpl`, `research-protocol.md.tmpl`, `standards.md.tmpl`, `provenance.md.tmpl`, `vvc-pipeline.md.tmpl`
- 9 new placeholder derivation rules in SKILL.md generation logic
- `comprehensiveFollowUpAgentCap` and `tokenBudgets.provenance` fields in engine-config schema
- `.claude/commands/` directory with `install-local-plugin.md` custom command

### Changed
- Template count increased from 6 to 11 `.tmpl` files (plus 3 JSON schemas)
- VVC-aware Step 7 agent generation loop with `isVvcAgent` conditional logic
- Section 8 wizard defaults updated: exploration depth 2 (was 5), provenance budget 5000, comprehensive follow-up cap 2
- Patent Intelligence Engine example updated to match new template structure

## [1.6.0] - 2026-03-15

### Added
- **Cryptographic provenance system** — SHA-256 hash chains for tamper-evident source audit trails
  - Source Hashing Protocol: every WebFetch hashed and chained in Hash_Manifest.md
  - Phase 4.5 Provenance Audit: chain integrity verification, methodology cross-reference
  - `--reverifiable` flag: opt-in source snapshot retention for independent re-verification
  - Always on for all tiers; audit phase runs on Standard/Deep/Comprehensive
- New `qualityFramework.provenance` config section in engine-config schema
- Provenance validation in `/test-engine` suite (check 4j)
- `Bash` added to generated engine allowed-tools for sha256sum operations
- 4 new placeholder derivation rules: `{{agentPrefix}}`, `{{auditTierBehavior}}`, `{{provenanceTierColumn}}`, `{{reverifiableDefault}}`

## [1.5.0] - 2026-02-24

### Changed
- **All VVC verification scope defaults set to 100%** -- HIGH, MEDIUM, LOW, and SPECULATIVE confidence levels now all default to 100% verification. Previously HIGH was fixed at 100%, MEDIUM defaulted to 75%, LOW to 0%, and SPECULATIVE was fixed at 0%. Every verifiable claim is now checked by default regardless of confidence tier
- **All confidence levels are now configurable** -- removed `const` constraints on HIGH and SPECULATIVE. All four levels accept any value from 0-100, giving users full control over the verification depth-vs-cost tradeoff
- **All 21 domain presets updated** -- every preset now defaults to 100% verification across all confidence levels (previously varied: e.g., Legal had 100/100/25/0, Market Intelligence had 100/75/0/0)
- **Wizard prompts updated** -- MEDIUM, LOW, and SPECULATIVE now recommend 100% as the default option. SPECULATIVE added as a separate wizard question
- **Test validation relaxed** -- `/test-engine` check 4i no longer enforces fixed values for HIGH or SPECULATIVE
- **Schema files updated** -- `engine-config-schema.json` and `preset-schema.json` use `default` instead of `const` for all levels

## [1.4.0] - 2026-02-23

### Added
- **Context isolation (`--extend` flag)** -- research engines now default to standalone mode, scoping research strictly to the user's stated topic. Prior behavior (inheriting ambient project context from CLAUDE.md, observation history, and prior research files) caused Phase 1 planning agents to expand scope beyond the stated topic. Users who want to build on prior research must now explicitly opt in with `--extend`
- **`--no-approve` flag** -- skip the outline approval gate for automation or fast iteration
- **Scope discipline block** -- new `{{scopeDisciplineBlock}}` placeholder injects conditional instructions into Phase 1 planning agent prompts, with standalone and extend variants
- **Context contamination issue documentation** -- `ISSUE_context-contamination.md` with root cause analysis, evidence trail, and resolution

### Changed
- **Approval gate now defaults to ON for Standard/Deep/Comprehensive tiers** -- previously only `--comprehensive` and explicit `--approve` paused for user review. Now all non-quick tiers present the outline for approval before Phase 2 agents execute. This catches scope bloat before spending tokens on research
- `--approve` flag annotation updated to note it is the default behavior for Standard+ tiers
- Command template `argument-hint` updated with new flags

## [1.3.0] - 2026-02-22

### Added
- **`/install-local-plugin` command** -- registers a generated engine as a permanently installed Claude Code plugin. Creates a temporary marketplace, registers it, and installs via `claude plugin marketplace add` + `claude plugin install`. The installed plugin persists across sessions and projects without needing `--plugin-dir` flags
- **Automatic install command deployment** -- post-generation step now copies `install-local-plugin.md` to the user's `.claude/commands/` directory so it's immediately available after engine creation
- `AskUserQuestion` added to `install-local-plugin` allowed tools (used for reinstall confirmation)

### Changed
- Post-generation workflow updated in both `create-engine.md` and `SKILL.md` to suggest `/install-local-plugin` as the primary installation path (with `--plugin-dir` as a quick-test alternative)
- Quick Start in README updated to 5-step flow: create → validate → install → restart → use
- Commands table updated with `/install-local-plugin` entry
- File Reference updated with `install-local-plugin.md` in commands listing

## [1.2.0] - 2026-02-22

### Added
- **Verification, Validation & Correction (VVC) system** -- goes beyond simple citations (which can still hallucinate). Two-pass post-reporting pipeline that extracts every factual claim, re-fetches the cited source, and verifies both source credibility and accurate representation. Failed claims are auto-corrected or flagged
  - Phase 4 renamed to "Draft Reporting" with mandatory `[VC]`/`[PO]`/`[IE]` claim tagging
  - Phase 5 (VVC-Verify): extracts verifiable claims, fetches sources, classifies alignment (CONFIRMED/PARAPHRASED/OVERSTATED/UNDERSTATED/DISPUTED/UNSUPPORTED/SOURCE_UNAVAILABLE), produces verification report
  - Phase 6 (VVC-Correct): implements corrections, produces final Comprehensive Report + correction log
- **Claim type taxonomy**: `[VC]` Verifiable Claim, `[PO]` Professional Opinion, `[IE]` Inferred/Extrapolated -- extensible via wizard
- **Tier-aware VVC behavior**: Quick: none, Standard: verify-only, Deep: full, Comprehensive: full
- **Configurable verification scope**: HIGH% (default 100), MEDIUM% (default 100), LOW% (default 100), SPECULATIVE% (default 100)
- **VVC specialist agent** (`vvc-specialist`) -- pipeline agent using `general-purpose` subagent type for WebFetch source verification
- **High-accuracy presets**: Legal, OSINT, Financial DD, AML, Academic get 100% MEDIUM / 25-50% LOW verification rates
- VVC configuration in wizard Section 6 with customizable claim types, verification scope, and per-tier behavior
- VVC token budget (default 8000) in advanced configuration
- Check 4i in `/test-engine` for VVC configuration validation including negative check that vvc-specialist is NOT in tier agent arrays
- 18 new VVC placeholder derivation rules in engine creator wizard
- VVC sections in base-research-skill, extension-skill, command, and readme templates

### Changed
- Pipeline architecture expanded from 5-phase to 7-phase when VVC enabled (backward-compatible: 5-phase when VVC disabled/absent)
- Patent Intelligence Engine example updated with VVC configuration, vvc-specialist agent, and regenerated 7-phase SKILL.md
- All 20 domain presets updated with VVC configuration blocks
- Schema files (engine-config-schema.json, preset-schema.json) extended with VVC object and claimTypeDefinition

## [1.1.0] - 2026-02-22

### Added
- **20 domain presets** covering all major research sectors (up from 5):
  - Real Estate & CRE (`--preset cre`)
  - Cybersecurity & Threat Intel (`--preset cyber`)
  - Healthcare & Medical (`--preset medical`)
  - Financial Due Diligence (`--preset findd`)
  - Energy & Utilities (`--preset energy`)
  - Infrastructure & Development (`--preset infra`)
  - ESG & Climate Risk (`--preset esg`)
  - Government & Public Policy (`--preset policy`)
  - Supply Chain & Logistics (`--preset supply`)
  - Geopolitical & Political Risk (`--preset geopolit`)
  - Insurance & Actuarial (`--preset insurance`)
  - Biotechnology & Life Sciences (`--preset biotech`)
  - Aerospace & Defense (`--preset defense`)
  - Investigative Journalism (`--preset investigate`)
  - AML & Regulatory Compliance (`--preset aml`)
- "Why I Built This" section in README explaining the motivation and positioning
- Clear installation instructions with `claude plugin add` and manual clone methods
- Expanded wizard interview documentation showing full customization depth across all 9 sections

### Fixed
- Template `{{maxIterations}}` placeholder was hardcoded to "3" in agent template
- Template phase count corrected from "four-phase" to "five-phase" in base research skill
- Sources command template missing `argument-hint` frontmatter field
- README template using `{{version}}` instead of `{{engineVersion}}`
- Extension skill template missing advanced configuration override section
- Empty `"email": ""` field generated in plugin.json when email not provided
- Edit tool missing from all 15 preset agent configurations across original 5 presets
- Spot-check verification mode definition inconsistency in SKILL.md
- Exploration depth parameter missing from wizard Section 8
- SKILL.md frontmatter: removed unsupported `version` field, fixed `name` format to kebab-case
- Repository URLs updated from `cc-plugins` to `deep-research-engine-creator` across all files
- Publish script now warns instead of silently falling back when branch detection fails

### Changed
- Regenerated all 8 patent-intelligence-engine example files from fixed templates
- File reference in README now lists all 20 domain presets (was showing 5)
- Self-contained mode description corrected to "5-phase research pipeline" in output modes table

## [1.0.1] - 2026-02-22

### Added
- Citation management system with verification modes (none, spot-check, comprehensive)
- Source freshness checking with configurable thresholds
- Dead link handling with archive fallback
- URL liveness checking and content-claim matching options
- Verification reporting with configurable scope
- `.gitignore` for `generated-engines/` directory

### Fixed
- 13 findings from GPT-5.3 Codex cross-model code review remediated
- 5 quality gaps patched: URL input handling, exploration depth defaults, absence tracking in reports, post-mortem skill reference, contrarian sweep integration

## [1.0.0] - 2026-02-22

### Added
- **Engine Creator wizard** with 9-section structured interview for building domain-specific research engines
- **Two output modes**: self-contained (full 5-phase pipeline embedded) and extension (lightweight overlay on base `/deep-research` skill)
- **5 slash commands**: `/create-engine`, `/update-engine`, `/test-engine`, `/preview-engine`, `/list-engines`
- **5 initial domain presets**: Legal Research, Market Intelligence, Academic Research, OSINT Investigation, Technical Due Diligence
- **Template system** for generating all plugin files: SKILL.md, commands, agents, plugin.json, README
- **JSON Schema validation** for engine configs, domain presets, and plugin manifests
- **Patent Intelligence Engine** as complete reference example with 3 specialized agents, 5-tier source hierarchy, and 12-section report structure
- **Publish script** for pushing generated engines to marketplace repositories
- **engine-config.json** as the pivot point -- editable, versionable, re-processable configuration format
