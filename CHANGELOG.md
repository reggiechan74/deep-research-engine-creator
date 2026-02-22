# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-02-22

### Added
- **Verification, Validation & Correction (VVC) system** -- goes beyond simple citations (which can still hallucinate). Two-pass post-reporting pipeline that extracts every factual claim, re-fetches the cited source, and verifies both source credibility and accurate representation. Failed claims are auto-corrected or flagged
  - Phase 4 renamed to "Draft Reporting" with mandatory `[VC]`/`[PO]`/`[IE]` claim tagging
  - Phase 5 (VVC-Verify): extracts verifiable claims, fetches sources, classifies alignment (CONFIRMED/PARAPHRASED/OVERSTATED/UNDERSTATED/DISPUTED/UNSUPPORTED/SOURCE_UNAVAILABLE), produces verification report
  - Phase 6 (VVC-Correct): implements corrections, produces final Comprehensive Report + correction log
- **Claim type taxonomy**: `[VC]` Verifiable Claim, `[PO]` Professional Opinion, `[IE]` Inferred/Extrapolated -- extensible via wizard
- **Tier-aware VVC behavior**: Quick: none, Standard: verify-only, Deep: full, Comprehensive: full
- **Configurable verification scope**: 100% HIGH (fixed), MEDIUM% (default 75), LOW% (default 0), 0% SPECULATIVE (fixed)
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
