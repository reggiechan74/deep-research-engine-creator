# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
