# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
