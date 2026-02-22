# Deep Research Engine Creator

Create domain-specialized deep-research engines as standalone Claude Code plugins.

This meta-plugin interviews you about your research domain, then generates a complete Claude Code plugin with a custom multi-agent research pipeline, domain-specific source hierarchies, quality frameworks, and output templates. You describe what you research; it builds the tooling.

## Quick Start

```bash
# 1. Install the plugin
claude --plugin-dir ./deep-research-engine-creator

# 2. Run the wizard (with an optional preset)
/create-engine --preset market

# 3. Answer the wizard questions — domain, sources, agents, quality, output
#    The wizard walks you through 9 sections with smart defaults.

# 4. Validate the generated engine
/test-engine ./generated-engines/your-engine/

# 5. Use the generated engine
claude --plugin-dir ./generated-engines/your-engine/
/research "your topic"
```

## Commands

| Command | Description |
|---------|-------------|
| `/create-engine [--preset name]` | Main wizard -- interviews you and generates a complete engine plugin |
| `/update-engine <path>` | Re-configure specific sections of an existing engine |
| `/test-engine <path> [topic]` | Validate structure and run smoke test on a generated engine |
| `/preview-engine <path>` | Preview what an engine config would generate (read-only) |
| `/list-engines [dir]` | Scan a directory for generated engines and display a summary table |

## Domain Presets

Presets pre-fill the wizard with domain-specific defaults for source hierarchies, agent configurations, quality rules, and output structure. You can accept them as-is or customize any section.

| Preset Flag | Domain | Key Features |
|-------------|--------|--------------|
| `--preset legal` | Legal Research | Bluebook citations, case law databases, statutory analysis |
| `--preset market` | Market Intelligence | SEC filings, competitive analysis, market sizing |
| `--preset academic` | Academic Research | Peer-reviewed sources, systematic review methodology |
| `--preset osint` | OSINT Investigation | Multi-source correlation, digital footprint analysis |
| `--preset techdd` | Technical Due Diligence | Patent databases, standards compliance, IP landscape |

Or choose **Custom** during the wizard to build a configuration from scratch.

## What Gets Generated

A generated engine is a fully self-contained Claude Code plugin:

```
your-engine-name/
├── .claude-plugin/plugin.json     # Plugin manifest
├── engine-config.json             # Full configuration (editable, re-processable)
├── commands/
│   ├── research.md                # /research <topic> [--quick|--deep|--comprehensive]
│   └── sources.md                 # /sources — view configured source hierarchy
├── agents/
│   ├── agent-1.md                 # Domain-specialized research agent
│   ├── agent-2.md                 # Domain-specialized analysis agent
│   └── agent-3.md                 # Domain-specialized mapping agent
├── skills/
│   └── your-domain/
│       └── SKILL.md               # Complete research engine (~500-700 lines)
└── README.md                      # Auto-generated documentation
```

Every generated engine includes:

- A tiered research command (`/research`) with quick, standard, deep, and comprehensive modes
- A sources command (`/sources`) for inspecting the configured credibility hierarchy
- Domain-specialized agents with their own search strategies and citation prefixes
- A quality framework with confidence scoring, evidence thresholds, and validation rules
- Structured report output with configurable sections

## Two Output Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| **Self-contained** | Full 4-phase research pipeline embedded. No dependencies. | Sharing, portability, standalone use |
| **Extension** | Overlays customizations on the base `/deep-research` skill. Lighter weight. | When you already have `/deep-research` installed |

Self-contained engines include the complete research orchestration logic (planning, research, synthesis, reporting) in their SKILL.md. Extension engines inherit the base pipeline and only override domain-specific configuration (sources, agents, quality rules, output structure).

## The Wizard Interview

The wizard uses progressive disclosure across 9 sections. When a domain preset is loaded, sections 4-9 are pre-filled with smart defaults that you can accept or customize.

| Section | What It Covers |
|---------|----------------|
| 1. Domain Identity | Engine name, field, target audience, preset selection, output mode |
| 2. Research Scope | Question types, geographic scope, temporal focus, primary deliverable |
| 3. Sample Questions | 3-5 example queries -- used to auto-suggest source types, agent roles, and output structure |
| 4. Source Strategy | 5-tier credibility hierarchy, preferred/excluded sites, search templates |
| 5. Agent Pipeline | Basic (recommended defaults) or advanced (per-agent configuration of roles, models, tools) |
| 6. Quality Framework | Confidence scoring levels, minimum evidence thresholds, validation rules, citation standard |
| 7. Output Structure | Report sections, file naming templates, special deliverables (matrices, maps, etc.) |
| 8. Advanced Configuration | Optional: iteration limits, token budgets, custom hooks, MCP integrations |
| 9. Custom Prompts | Global preamble, per-agent prompt overrides, synthesis instructions, reporting tone |

After all sections are complete, the wizard shows a full preview of the engine configuration and asks for confirmation before generating any files.

## Example: Patent Intelligence Engine

A complete reference implementation is included:

```
See examples/patent-intelligence-engine/ for a working patent research engine.
```

This engine demonstrates the full capabilities of a generated plugin:

- **3 specialized agents:**
  - `patent-search-specialist` -- searches USPTO, EPO, WIPO, and other patent offices
  - `prior-art-analyst` -- applies TSM/KSR frameworks for novelty and obviousness analysis
  - `ip-landscape-mapper` -- builds competitive portfolio matrices and identifies whitespace
- **5-tier source hierarchy** from official patent databases (Tier 1) down to unverified claims (Tier 5)
- **Patent-specific quality rules** including patent number verification, assignee currency checks, and claim-element FTO requirements
- **12-section report structure** covering landscape overview, claims analysis, FTO assessment, IP risk matrix, and more

## Architecture

The Engine Creator uses an **A+C hybrid architecture** (Ask + Configure):

```
Wizard Interview  -->  engine-config.json  -->  Plugin Generation
    (ask)                  (config)                (generate)
```

1. **Wizard interview** collects domain requirements through structured questions
2. **engine-config.json** serves as the pivot point -- a complete, editable, versionable specification of the engine
3. **Templates + config** are combined to generate all plugin files (commands, agents, skills, README)

The config file is the source of truth. You can:
- Edit it directly and re-run generation
- Use `/update-engine` to re-interview specific sections
- Use `/preview-engine` to inspect what a config would produce without writing files
- Version-control it alongside your generated engine

## Publishing

Push a generated engine to a marketplace repository:

```bash
./scripts/publish-engine.sh ./generated-engines/your-engine/ https://github.com/user/marketplace-repo
```

The script validates the engine structure, reads the name and version from `engine-config.json`, clones the marketplace repo, copies the engine, commits, and pushes.

## Requirements

- **Claude Code** with plugin support
- **For extension mode only:** the base `/deep-research` skill must be installed as a separate plugin

## File Reference

```
deep-research-engine-creator/
├── .claude-plugin/plugin.json                          # This plugin's manifest
├── commands/
│   ├── create-engine.md                                # /create-engine wizard
│   ├── update-engine.md                                # /update-engine reconfiguration
│   ├── test-engine.md                                  # /test-engine validation suite
│   ├── preview-engine.md                               # /preview-engine read-only preview
│   └── list-engines.md                                 # /list-engines directory scanner
├── skills/engine-creator/
│   ├── SKILL.md                                        # Core wizard + generation logic
│   ├── domain-presets/
│   │   ├── legal-research.json                         # Legal research preset
│   │   ├── market-intelligence.json                    # Market intelligence preset
│   │   ├── academic-research.json                      # Academic research preset
│   │   ├── osint-investigation.json                    # OSINT investigation preset
│   │   └── technical-due-diligence.json                # Technical due diligence preset
│   └── templates/
│       ├── base-research-skill.md.tmpl                 # Self-contained SKILL.md template
│       ├── extension-skill.md.tmpl                     # Extension SKILL.md template
│       ├── command-template.md.tmpl                    # /research command template
│       ├── sources-command-template.md.tmpl            # /sources command template
│       ├── agent-template.md.tmpl                      # Per-agent definition template
│       ├── plugin-json.tmpl                            # plugin.json template
│       ├── readme-template.md.tmpl                     # Generated README template
│       └── engine-config-schema.json                   # Config validation schema
├── scripts/
│   └── publish-engine.sh                               # Marketplace publishing script
├── examples/
│   └── patent-intelligence-engine/                     # Complete reference implementation
└── README.md                                           # This file
```

## License

MIT
