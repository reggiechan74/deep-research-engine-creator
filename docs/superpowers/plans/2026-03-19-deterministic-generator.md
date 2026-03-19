# Deterministic Python Generator — Implementation Plan (Plan A)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace LLM-driven file generation (Steps 1-9 in SKILL.md) with a deterministic Python script that reads `engine-config.json` + templates and produces identical output every time.

**Architecture:** Single-file Python generator (`plugin/generator/generate.py`) with functions for: config loading, validation, placeholder derivation (90+ rules), template substitution, file generation, and post-generation verification. The LLM wizard interview is unchanged — it produces `engine-config.json` with a new `_derived` section for creative content. The script does pure mechanical substitution.

**Tech Stack:** Python 3 stdlib only (json, os, sys, re, pathlib). Zero external dependencies.

**Spec:** `docs/superpowers/specs/2026-03-19-deterministic-generator-design.md` (Sections 1-6)

---

## File Structure

```
plugin/
├── generator/
│   └── generate.py                    # NEW — deterministic generator (~500 lines)
├── generator/tests/
│   └── test_generate.py               # NEW — unit tests for generator
├── skills/engine-creator/
│   └── SKILL.md                       # MODIFY — replace Steps 1-9 with script invocation
├── skills/engine-creator/templates/
│   └── engine-config-schema.json      # MODIFY — add _derived to schema
├── commands/
│   └── test-engine.md                 # MODIFY — drop impossible-to-fail checks
├── examples/patent-intelligence-engine/
│   └── engine-config.json             # MODIFY — add _derived section
├── .claude-plugin/plugin.json         # MODIFY — version 1.9.0
.claude-plugin/marketplace.json        # MODIFY — version 1.9.0
CHANGELOG.md                           # MODIFY — v1.9.0 entry
```

---

### Task 1: Create generator skeleton with load_config and validate

**Files:**
- Create: `plugin/generator/generate.py`
- Create: `plugin/generator/tests/test_generate.py`

- [ ] **Step 1: Create the generator directory**

```bash
mkdir -p plugin/generator/tests
```

- [ ] **Step 2: Write the test file with initial tests**

Write `plugin/generator/tests/test_generate.py`:

```python
"""Tests for the deterministic engine generator."""
import json
import os
import sys
import tempfile
import pytest

# Add generator to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import generate


def make_minimal_config():
    """Return a minimal valid engine-config.json as a dict."""
    return {
        "schemaVersion": "1.0",
        "engineMeta": {
            "name": "test-engine",
            "displayName": "Test Engine",
            "domain": "testing",
            "audience": "testers",
            "version": "1.0.0",
            "mode": "self-contained",
            "createdAt": "2026-03-19T12:00:00-04:00",
            "createdBy": "deep-research-engine-creator/1.0.0",
            "description": "A test engine",
            "author": {"name": "Test Author"},
            "keywords": ["test"]
        },
        "sampleQuestions": ["What is X?", "How does Y work?", "Why does Z matter?"],
        "scope": {
            "questionTypes": ["Landscape Analysis"],
            "geographic": ["Global"],
            "temporal": "Current State Only",
            "deliverable": "Comprehensive Report"
        },
        "sourceStrategy": {
            "credibilityTiers": {
                "tier1": {"name": "Primary", "sources": ["Government databases"]},
                "tier2": {"name": "Institutional", "sources": ["Academic journals"]},
                "tier3": {"name": "Professional", "sources": ["Industry reports"]},
                "tier4": {"name": "General", "sources": ["News outlets"]},
                "tier5": {"name": "Unverified", "sources": ["Social media"]}
            },
            "preferredSites": ["example.com"],
            "excludedSources": [],
            "searchTemplates": [{"name": "general", "pattern": "{topic} {geography}"}]
        },
        "agentPipeline": {
            "agents": [
                {
                    "id": "research-agent",
                    "role": "Research Analyst",
                    "subagentType": "general-purpose",
                    "specialization": "General research and analysis",
                    "model": "sonnet"
                }
            ],
            "tiers": {
                "quick": {"agents": ["research-agent"]},
                "standard": {"agents": ["research-agent"]},
                "deep": {"agents": ["research-agent"]},
                "comprehensive": {"agents": ["research-agent"], "followUpRound": True}
            }
        },
        "qualityFramework": {
            "confidenceScoring": {
                "HIGH": "Multiple corroborating sources",
                "MEDIUM": "Single reliable source",
                "LOW": "Limited or indirect evidence",
                "SPECULATIVE": "Inference without direct evidence"
            },
            "minimumEvidence": "At least one credible source",
            "validationRules": ["Cross-reference claims"],
            "citationStandard": "APA 7th Edition",
            "provenance": {
                "enabled": True,
                "hashAlgorithm": "sha256",
                "reverifiableDefault": False,
                "auditPhase": {"tiers": ["standard", "deep", "comprehensive"]},
                "chainFormat": "[SHA-256]|[URL]|[TIMESTAMP]|[AGENT_ID]|[PREV_HASH]"
            }
        },
        "outputStructure": {
            "reportOutputDir": "./research-reports",
            "reportSections": ["Executive Summary", "Findings", "Conclusion"],
            "fileNaming": "{date}_{topic_slug}_report.md",
            "specialDeliverables": []
        },
        "prompts": {
            "globalPreamble": "",
            "agentOverrides": {},
            "synthesisInstructions": "",
            "reportingTone": "Professional and analytical"
        },
        "advanced": {
            "maxIterationsPerQuestion": 3,
            "explorationDepth": 2,
            "maxWebFetchesPerAgent": 10,
            "comprehensiveFollowUpAgentCap": 2,
            "dashboardPort": 3847,
            "tokenBudgets": {
                "planning": 2000,
                "research": 15000,
                "synthesis": 8000,
                "reporting": 10000,
                "provenance": 5000
            }
        },
        "_derived": {
            "agentExamplesBlocks": {
                "research-agent": "## Examples\n\nExample research output."
            },
            "agentBodyBlocks": {
                "research-agent": "## Search Protocol\n\nFollow standard search protocol."
            },
            "agentFirstActionsBlocks": {
                "research-agent": "## First Actions\n\n1. Read standards.md"
            },
            "scopeDisciplineBlock": "### Scope Discipline\n\nStay on topic.",
            "operationalLessons": "No entries yet."
        }
    }


class TestLoadConfig:
    def test_loads_valid_json(self, tmp_path):
        config = make_minimal_config()
        config_path = tmp_path / "engine-config.json"
        config_path.write_text(json.dumps(config))
        result = generate.load_config(str(config_path))
        assert result["engineMeta"]["name"] == "test-engine"

    def test_raises_on_missing_file(self):
        with pytest.raises(SystemExit) as exc_info:
            generate.load_config("/nonexistent/path.json")
        assert exc_info.value.code == 1

    def test_raises_on_invalid_json(self, tmp_path):
        config_path = tmp_path / "bad.json"
        config_path.write_text("not json")
        with pytest.raises(SystemExit) as exc_info:
            generate.load_config(str(config_path))
        assert exc_info.value.code == 1


class TestValidate:
    def test_accepts_valid_config(self):
        generate.validate(make_minimal_config())  # Should not raise

    def test_rejects_missing_engine_meta(self):
        config = make_minimal_config()
        del config["engineMeta"]
        with pytest.raises(SystemExit) as exc_info:
            generate.validate(config)
        assert exc_info.value.code == 1

    def test_rejects_missing_derived(self):
        config = make_minimal_config()
        del config["_derived"]
        with pytest.raises(SystemExit) as exc_info:
            generate.validate(config)
        assert exc_info.value.code == 1

    def test_rejects_invalid_engine_name(self):
        config = make_minimal_config()
        config["engineMeta"]["name"] = "Invalid Name"
        with pytest.raises(SystemExit) as exc_info:
            generate.validate(config)
        assert exc_info.value.code == 1

    def test_rejects_dangling_agent_reference(self):
        config = make_minimal_config()
        config["agentPipeline"]["tiers"]["quick"]["agents"] = ["nonexistent-agent"]
        with pytest.raises(SystemExit) as exc_info:
            generate.validate(config)
        assert exc_info.value.code == 1
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd plugin/generator && python3 -m pytest tests/test_generate.py -v 2>&1 | head -30
```

Expected: ModuleNotFoundError or ImportError (generate.py doesn't exist yet).

- [ ] **Step 4: Write the generator skeleton**

Write `plugin/generator/generate.py`:

```python
#!/usr/bin/env python3
"""Deterministic engine generator for deep-research-engine-creator.

Reads an engine-config.json (with _derived section) and template files,
performs placeholder substitution, and writes all output files.

Usage: python3 generate.py <config-path> <output-dir>

Exit codes:
  0 — success
  1 — validation error
  2 — template error
"""
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, '..', 'skills', 'engine-creator', 'templates')


def error_exit(message, code=1):
    """Print error to stderr and exit."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def load_config(path):
    """Read and parse engine-config.json."""
    if not os.path.exists(path):
        error_exit(f"Config file not found: {path}")
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        error_exit(f"Invalid JSON in {path}: {e}")


def validate(config):
    """Check required fields, types, relational constraints."""
    required_keys = [
        "schemaVersion", "engineMeta", "sampleQuestions", "scope",
        "sourceStrategy", "agentPipeline", "qualityFramework",
        "outputStructure", "_derived"
    ]
    for key in required_keys:
        if key not in config:
            error_exit(f"Missing required key: {key}")

    meta = config.get("engineMeta", {})
    if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', meta.get("name", "")):
        error_exit(f"Invalid engine name: {meta.get('name')}. Must be kebab-case.")

    for field in ["displayName", "domain", "audience", "version", "mode", "createdAt", "createdBy"]:
        if field not in meta:
            error_exit(f"Missing engineMeta.{field}")

    # Validate agent-tier cross-references
    agent_ids = {a["id"] for a in config.get("agentPipeline", {}).get("agents", [])}
    for tier_name, tier_config in config.get("agentPipeline", {}).get("tiers", {}).items():
        for agent_id in tier_config.get("agents", []):
            if agent_id not in agent_ids:
                error_exit(f"Tier '{tier_name}' references unknown agent: {agent_id}")

    # Validate _derived has required keys
    derived = config.get("_derived", {})
    for key in ["agentExamplesBlocks", "agentBodyBlocks", "agentFirstActionsBlocks", "scopeDisciplineBlock"]:
        if key not in derived:
            error_exit(f"Missing _derived.{key}")

    # Validate source hierarchy completeness
    tiers = config.get("sourceStrategy", {}).get("credibilityTiers", {})
    for i in range(1, 6):
        tier_key = f"tier{i}"
        if tier_key not in tiers:
            error_exit(f"Missing sourceStrategy.credibilityTiers.{tier_key}")
        tier = tiers[tier_key]
        if not tier.get("name") or not tier.get("sources"):
            error_exit(f"Tier {tier_key} must have non-empty 'name' and 'sources'")

    # Validate quality framework
    qf = config.get("qualityFramework", {})
    for level in ["HIGH", "MEDIUM", "LOW", "SPECULATIVE"]:
        if level not in qf.get("confidenceScoring", {}):
            error_exit(f"Missing qualityFramework.confidenceScoring.{level}")


def substitute(template, placeholders):
    """Replace all {{key}} occurrences in template string."""
    result = template
    for key, value in placeholders.items():
        result = result.replace('{{' + key + '}}', str(value))
    remaining = re.findall(r'\{\{[a-zA-Z0-9_-]+\}\}', result)
    if remaining:
        print(f"WARNING: unresolved placeholders: {remaining}", file=sys.stderr)
    return result


def derive_placeholders(config):
    """Apply all mechanical derivation rules. Returns flat dict."""
    # Placeholder — implemented in Task 2
    return {}


def generate_files(config, placeholders, output_dir):
    """Create directories, read templates, substitute, write output files."""
    # Placeholder — implemented in Task 3
    pass


def verify_output(output_dir, config):
    """Post-generation check: all expected files exist and are non-empty."""
    # Placeholder — implemented in Task 4
    pass


def print_summary(output_dir):
    """List all generated files with sizes."""
    files = []
    for root, _, filenames in os.walk(output_dir):
        for fn in filenames:
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, output_dir)
            size = os.path.getsize(fp)
            files.append((rel, size))
    files.sort()
    print(f"\nGenerated {len(files)} files:")
    for rel, size in files:
        print(f"  {rel} ({size} bytes)")


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 generate.py <config-path> <output-dir>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]
    output_dir = sys.argv[2]

    config = load_config(config_path)
    validate(config)
    placeholders = derive_placeholders(config)
    generate_files(config, placeholders, output_dir)
    verify_output(output_dir, config)
    print_summary(output_dir)


if __name__ == '__main__':
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd plugin/generator && python3 -m pytest tests/test_generate.py -v
```

Expected: All 7 tests pass.

- [ ] **Step 6: Commit**

```bash
git add plugin/generator/generate.py plugin/generator/tests/test_generate.py
git commit -m "feat: add generator skeleton with load_config, validate, and substitute"
```

---

### Task 2: Implement derive_placeholders — all 90+ rules

**Files:**
- Modify: `plugin/generator/generate.py`
- Modify: `plugin/generator/tests/test_generate.py`

This is the largest single task. The function transforms `engine-config.json` into a flat dict of ~90 placeholder→value mappings. The spec (Section 4) groups them into: direct reads, formatted outputs, conditional blocks, computed values, and _derived passthroughs.

- [ ] **Step 1: Write derivation tests**

Append to `plugin/generator/tests/test_generate.py`:

```python
class TestDerivePlaceholders:
    def test_direct_config_reads(self):
        config = make_minimal_config()
        p = generate.derive_placeholders(config)
        assert p["engineName"] == "test-engine"
        assert p["engineDisplayName"] == "Test Engine"
        assert p["domain"] == "testing"
        assert p["audience"] == "testers"
        assert p["maxIterations"] == "3"
        assert p["explorationDepth"] == "2"
        assert p["maxWebFetches"] == "10"
        assert p["dashboardPort"] == "3847"
        assert p["citationStandard"] == "APA 7th Edition"

    def test_tier_descriptions(self):
        config = make_minimal_config()
        p = generate.derive_placeholders(config)
        assert "research-agent" in p["quickAgentId"]
        assert "Single-agent" in p["quickTierDescription"]

    def test_tier_config_table(self):
        config = make_minimal_config()
        p = generate.derive_placeholders(config)
        assert "Quick" in p["tierConfigTable"]
        assert "Standard" in p["tierConfigTable"]

    def test_vvc_disabled_produces_empty_blocks(self):
        config = make_minimal_config()
        # No VVC in config
        p = generate.derive_placeholders(config)
        assert p["vvcPhaseLines"] == ""
        assert p["vvcClaimTaggingInstructions"] == ""
        assert p["vvcVerifyPhaseBlock"] == ""
        assert p["vvcCorrectPhaseBlock"] == ""
        assert p["pipelinePhaseCount"] == "five"
        assert p["phase4Name"] == "Professional Reporting"

    def test_vvc_enabled_produces_content(self):
        config = make_minimal_config()
        config["qualityFramework"]["vvc"] = {
            "enabled": True,
            "claimTypes": [
                {"tag": "VC", "label": "Verifiable Claim", "description": "Factual", "requiresVerification": True},
                {"tag": "PO", "label": "Professional Opinion", "description": "Opinion", "requiresVerification": False},
                {"tag": "IE", "label": "Inferred", "description": "Inference", "requiresVerification": False}
            ],
            "verificationScope": {"HIGH": 100, "MEDIUM": 100, "LOW": 100, "SPECULATIVE": 100},
            "tierBehavior": {"quick": "none", "standard": "verify-only", "deep": "full", "comprehensive": "full"}
        }
        config["advanced"]["tokenBudgets"]["vvc"] = 8000
        p = generate.derive_placeholders(config)
        assert p["pipelinePhaseCount"] == "seven"
        assert p["phase4Name"] == "Draft Reporting"
        assert "VVC" in p["vvcPhaseLines"]
        assert "[VC]" in p["vvcClaimTaggingInstructions"]
        assert p["vvcWebFetchCap"] == "30"

    def test_derived_passthrough(self):
        config = make_minimal_config()
        p = generate.derive_placeholders(config)
        assert p["scopeDisciplineBlock"] == "### Scope Discipline\n\nStay on topic."
        assert p["operationalLessons"] == "No entries yet."

    def test_source_hierarchy(self):
        config = make_minimal_config()
        p = generate.derive_placeholders(config)
        assert "Primary" in p["sourceHierarchy"]
        assert "tier1Name" in p
        assert p["tier1Name"] == "Primary"

    def test_confidence_levels(self):
        config = make_minimal_config()
        p = generate.derive_placeholders(config)
        assert p["confidenceHigh"] == "Multiple corroborating sources"
        assert p["confidenceMedium"] == "Single reliable source"

    def test_agent_deployment_blocks(self):
        config = make_minimal_config()
        p = generate.derive_placeholders(config)
        assert "research-agent" in p["agentDeploymentBlocks"]
        assert "test-engine:research-agent" in p["agentDeploymentBlocks"]

    def test_sub_agent_list(self):
        config = make_minimal_config()
        p = generate.derive_placeholders(config)
        assert "research-planning-specialist" in p["subAgentList"]
        assert "synthesis-specialist" in p["subAgentList"]
        assert "test-engine:research-agent" in p["subAgentList"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd plugin/generator && python3 -m pytest tests/test_generate.py::TestDerivePlaceholders -v
```

Expected: All fail (derive_placeholders returns empty dict).

- [ ] **Step 3: Implement derive_placeholders**

Replace the stub `derive_placeholders` function in `generate.py` with the full implementation. This is a large function (~200 lines). Implement all rule groups from the spec Section 4:

**Direct config reads** — `engineName`, `domain`, `audience`, all budget fields, all confidence levels, all tier names/sources, all citation management fields, `dashboardPort`, etc.

**Formatted outputs** — `tierConfigTable` (markdown table from tiers), `agentDeploymentBlocks` (per-agent block), `subAgentList` (bullet list), `fileStructure` (per-agent file entries), `reportSections` (numbered list), `preferredSites` (bullet list), `sourceHierarchy` (formatted text), etc.

**Conditional blocks** — all `vvc*` placeholders: check `config.qualityFramework.vvc.enabled`, emit content or empty string.

**Computed values** — `pipelinePhaseCount`, `phase4Name`, `vvcWebFetchCap`, `quickAgentId`, etc.

**_derived passthroughs** — `scopeDisciplineBlock`, `operationalLessons` (with default fallback).

Key implementation notes:
- All values in the returned dict must be strings. Convert integers with `str()`.
- Use `config.get(key, default)` for optional fields.
- The complete specification for every rule is in the spec document `docs/superpowers/specs/2026-03-19-deterministic-generator-design.md` Section 4 — read the full tables there, not just this summary.
- The current SKILL.md has the same rules as prose at lines 275-340 (`plugin/skills/engine-creator/SKILL.md`) — use as cross-reference.
- For `{{filters}}`, combine `sourceStrategy.languageFilters` and `sourceStrategy.geographicFilters` into a single formatted block.
- For `{{baseSkillPath}}`, read from `config.engineMeta.get("baseSkillPath", "")` — this field is only present in extension mode configs.
- Per-agent placeholders (`agentExamplesBlock`, `agentBodyBlock`, `agentFirstActionsBlock`) are NOT in the global placeholders dict — they're built per-agent in the `generate_files` loop (see Task 3).

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd plugin/generator && python3 -m pytest tests/test_generate.py -v
```

Expected: All tests pass (both Task 1 and Task 2 tests).

- [ ] **Step 5: Commit**

```bash
git add plugin/generator/generate.py plugin/generator/tests/test_generate.py
git commit -m "feat: implement derive_placeholders with 90+ derivation rules"
```

---

### Task 3: Implement generate_files — template reading, substitution, file writing

**Files:**
- Modify: `plugin/generator/generate.py`
- Modify: `plugin/generator/tests/test_generate.py`

- [ ] **Step 1: Write generation tests**

Append to `plugin/generator/tests/test_generate.py`:

```python
class TestGenerateFiles:
    def _generate(self, tmp_path, config=None):
        """Helper: write config, run generate_files, return output dir."""
        config = config or make_minimal_config()
        config_path = tmp_path / "engine-config.json"
        config_path.write_text(json.dumps(config))
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        placeholders = generate.derive_placeholders(config)
        generate.generate_files(config, placeholders, str(output_dir))
        return output_dir

    def test_creates_directory_structure(self, tmp_path):
        out = self._generate(tmp_path)
        assert (out / ".claude-plugin").is_dir()
        assert (out / "commands").is_dir()
        assert (out / "agents").is_dir()
        assert (out / "skills" / "test-engine").is_dir()

    def test_creates_plugin_json(self, tmp_path):
        out = self._generate(tmp_path)
        pj = json.loads((out / ".claude-plugin" / "plugin.json").read_text())
        assert pj["name"] == "test-engine"

    def test_creates_research_command(self, tmp_path):
        out = self._generate(tmp_path)
        content = (out / "commands" / "research.md").read_text()
        assert "description:" in content  # YAML frontmatter

    def test_creates_agent_files(self, tmp_path):
        out = self._generate(tmp_path)
        assert (out / "agents" / "research-agent.md").exists()
        content = (out / "agents" / "research-agent.md").read_text()
        assert "Research Analyst" in content

    def test_creates_skill_files(self, tmp_path):
        out = self._generate(tmp_path)
        skill_dir = out / "skills" / "test-engine"
        assert (skill_dir / "SKILL.md").exists()
        assert (skill_dir / "standards.md").exists()
        assert (skill_dir / "research-protocol.md").exists()
        assert (skill_dir / "provenance.md").exists()
        assert (skill_dir / "dashboard-server.js").exists()
        assert (skill_dir / "dashboard.html").exists()

    def test_skips_vvc_pipeline_when_disabled(self, tmp_path):
        out = self._generate(tmp_path)
        assert not (out / "skills" / "test-engine" / "vvc-pipeline.md").exists()

    def test_creates_vvc_pipeline_when_enabled(self, tmp_path):
        config = make_minimal_config()
        config["qualityFramework"]["vvc"] = {
            "enabled": True,
            "claimTypes": [
                {"tag": "VC", "label": "Verifiable Claim", "description": "Factual", "requiresVerification": True}
            ],
            "verificationScope": {"HIGH": 100, "MEDIUM": 100, "LOW": 100, "SPECULATIVE": 100},
            "tierBehavior": {"quick": "none", "standard": "verify-only", "deep": "full", "comprehensive": "full"}
        }
        config["advanced"]["tokenBudgets"]["vvc"] = 8000
        config["agentPipeline"]["agents"].append({
            "id": "vvc-specialist", "role": "VVC Specialist",
            "subagentType": "general-purpose", "specialization": "Verify claims"
        })
        config["_derived"]["agentExamplesBlocks"]["vvc-specialist"] = "VVC examples"
        config["_derived"]["agentBodyBlocks"]["vvc-specialist"] = "VVC body"
        config["_derived"]["agentFirstActionsBlocks"]["vvc-specialist"] = "VVC first actions"
        out = self._generate(tmp_path, config)
        assert (out / "skills" / "test-engine" / "vvc-pipeline.md").exists()
        assert (out / "agents" / "vvc-specialist.md").exists()

    def test_creates_readme(self, tmp_path):
        out = self._generate(tmp_path)
        assert (out / "README.md").exists()

    def test_no_unresolved_placeholders(self, tmp_path):
        out = self._generate(tmp_path)
        for root, _, files in os.walk(str(out)):
            for fn in files:
                if fn.endswith(('.md', '.json', '.js', '.html')):
                    content = open(os.path.join(root, fn)).read()
                    remaining = re.findall(r'\{\{[a-zA-Z0-9_-]+\}\}', content)
                    assert remaining == [], f"Unresolved in {fn}: {remaining}"

    def test_plugin_json_no_empty_email(self, tmp_path):
        config = make_minimal_config()
        # No email in author
        out = self._generate(tmp_path, config)
        pj_text = (out / ".claude-plugin" / "plugin.json").read_text()
        assert '"email"' not in pj_text

    def test_dashboard_port_substituted(self, tmp_path):
        out = self._generate(tmp_path)
        content = (out / "skills" / "test-engine" / "dashboard-server.js").read_text()
        assert "3847" in content
        assert "{{dashboardPort}}" not in content
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd plugin/generator && python3 -m pytest tests/test_generate.py::TestGenerateFiles -v
```

Expected: All fail (generate_files is a stub).

- [ ] **Step 3: Implement generate_files**

Replace the stub in `generate.py`. The function:

1. Creates directory structure: `.claude-plugin/`, `commands/`, `agents/`, `skills/{name}/`
2. Reads each template from `TEMPLATE_DIR`
3. For agent files: loops through `config.agentPipeline.agents`, builds per-agent placeholders (including `_derived` blocks), substitutes, writes
4. For skill files: substitutes global placeholders, writes each file
5. For plugin.json: special handling to remove empty email line
6. For dashboard.html: copies verbatim (no substitution)
7. For VVC files: only generates when `qualityFramework.vvc.enabled` is true

Key helper:

```python
def read_template(name):
    """Read a template file from the templates directory."""
    path = os.path.join(TEMPLATE_DIR, name)
    if not os.path.exists(path):
        error_exit(f"Template not found: {path}", code=2)
    with open(path, 'r') as f:
        return f.read()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd plugin/generator && python3 -m pytest tests/test_generate.py -v
```

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugin/generator/generate.py plugin/generator/tests/test_generate.py
git commit -m "feat: implement generate_files — template reading, substitution, file writing"
```

---

### Task 4: Implement verify_output and extension mode

**Files:**
- Modify: `plugin/generator/generate.py`
- Modify: `plugin/generator/tests/test_generate.py`

- [ ] **Step 1: Write verification and extension mode tests**

Append to `plugin/generator/tests/test_generate.py`:

```python
class TestVerifyOutput:
    def test_passes_when_all_files_exist(self, tmp_path):
        config = make_minimal_config()
        config_path = tmp_path / "engine-config.json"
        config_path.write_text(json.dumps(config))
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        placeholders = generate.derive_placeholders(config)
        generate.generate_files(config, placeholders, str(output_dir))
        generate.verify_output(str(output_dir), config)  # Should not raise

    def test_fails_when_file_missing(self, tmp_path):
        config = make_minimal_config()
        config_path = tmp_path / "engine-config.json"
        config_path.write_text(json.dumps(config))
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        placeholders = generate.derive_placeholders(config)
        generate.generate_files(config, placeholders, str(output_dir))
        # Delete a required file
        os.remove(os.path.join(str(output_dir), "skills", "test-engine", "dashboard-server.js"))
        with pytest.raises(SystemExit) as exc_info:
            generate.verify_output(str(output_dir), config)
        assert exc_info.value.code == 2


class TestExtensionMode:
    def test_extension_mode_creates_single_skill_file(self, tmp_path):
        config = make_minimal_config()
        config["engineMeta"]["mode"] = "extension"
        config["engineMeta"]["baseSkillPath"] = "/path/to/base/skill"
        config_path = tmp_path / "engine-config.json"
        config_path.write_text(json.dumps(config))
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        placeholders = generate.derive_placeholders(config)
        generate.generate_files(config, placeholders, str(output_dir))
        skill_dir = output_dir / "skills" / "test-engine"
        assert (skill_dir / "SKILL.md").exists()
        # Extension mode should NOT have these files
        assert not (skill_dir / "standards.md").exists()
        assert not (skill_dir / "research-protocol.md").exists()
        assert not (skill_dir / "provenance.md").exists()
        assert not (skill_dir / "dashboard-server.js").exists()
        assert not (skill_dir / "dashboard.html").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd plugin/generator && python3 -m pytest tests/test_generate.py::TestVerifyOutput tests/test_generate.py::TestExtensionMode -v
```

- [ ] **Step 3: Implement verify_output and extension mode branching**

`verify_output` checks that all expected files exist and are non-empty. Expected files depend on mode and VVC config.

Extension mode branching: in `generate_files`, check `config["engineMeta"]["mode"]`. If `"extension"`, generate only: plugin.json, commands, agents, README, and a single SKILL.md from `extension-skill.md.tmpl`. Skip standards, research-protocol, provenance, VVC pipeline, dashboard files.

- [ ] **Step 4: Run all tests**

```bash
cd plugin/generator && python3 -m pytest tests/test_generate.py -v
```

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add plugin/generator/generate.py plugin/generator/tests/test_generate.py
git commit -m "feat: add verify_output and extension mode support"
```

---

### Task 5: End-to-end test with patent engine config

**Files:**
- Modify: `plugin/generator/tests/test_generate.py`
- Modify: `plugin/examples/patent-intelligence-engine/engine-config.json`

- [ ] **Step 1: Add `_derived` section to patent engine config**

Read `plugin/examples/patent-intelligence-engine/engine-config.json`. Add a `_derived` section with patent-domain content for all 4 agents (patent-search-specialist, prior-art-analyst, ip-landscape-mapper, vvc-specialist). Use the content from the existing agent files in `plugin/examples/patent-intelligence-engine/agents/` as the source for the `_derived` blocks.

- [ ] **Step 2: Write end-to-end test**

Append to `plugin/generator/tests/test_generate.py`:

```python
class TestEndToEnd:
    def test_generates_patent_engine(self, tmp_path):
        """Full end-to-end: load real patent config, generate, verify."""
        config_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'examples',
            'patent-intelligence-engine', 'engine-config.json'
        )
        config = generate.load_config(config_path)
        generate.validate(config)
        placeholders = generate.derive_placeholders(config)
        output_dir = str(tmp_path / "patent-output")
        os.makedirs(output_dir)
        generate.generate_files(config, placeholders, output_dir)
        generate.verify_output(output_dir, config)

        # Spot-check key files
        skill_dir = os.path.join(output_dir, "skills", "patent-intelligence-engine")
        assert os.path.exists(os.path.join(skill_dir, "SKILL.md"))
        assert os.path.exists(os.path.join(skill_dir, "vvc-pipeline.md"))
        assert os.path.exists(os.path.join(skill_dir, "dashboard-server.js"))
        assert os.path.exists(os.path.join(output_dir, "agents", "patent-search-specialist.md"))
        assert os.path.exists(os.path.join(output_dir, "agents", "vvc-specialist.md"))

        # Verify no unresolved placeholders
        for root, _, files in os.walk(output_dir):
            for fn in files:
                if fn.endswith(('.md', '.json', '.js', '.html')):
                    content = open(os.path.join(root, fn)).read()
                    remaining = re.findall(r'\{\{[a-zA-Z0-9_-]+\}\}', content)
                    assert remaining == [], f"Unresolved in {fn}: {remaining}"
```

- [ ] **Step 3: Run the end-to-end test**

```bash
cd plugin/generator && python3 -m pytest tests/test_generate.py::TestEndToEnd -v
```

Expected: PASS. This is the critical validation that the generator produces valid output from a real config.

- [ ] **Step 4: Commit**

```bash
git add plugin/generator/tests/test_generate.py plugin/examples/patent-intelligence-engine/engine-config.json
git commit -m "feat: add end-to-end test with patent engine config"
```

---

### Task 6: Add `_derived` to engine-config schema

**Files:**
- Modify: `plugin/skills/engine-creator/templates/engine-config-schema.json`

- [ ] **Step 1: Read the current schema**

Read `plugin/skills/engine-creator/templates/engine-config-schema.json` and locate:
- The top-level `required` array (~line 7)
- The top-level `properties` object (to add `_derived` alongside `advanced`)

- [ ] **Step 2: Add `_derived` to the `required` array**

Add `"_derived"` to the required array.

- [ ] **Step 3: Add `_derived` property definition**

Add to the `properties` object (after `advanced`):

```json
"_derived": {
  "type": "object",
  "description": "Pre-computed content generated by the LLM during the wizard interview. The Python generator reads these values verbatim during file generation.",
  "required": ["agentExamplesBlocks", "agentBodyBlocks", "agentFirstActionsBlocks", "scopeDisciplineBlock"],
  "additionalProperties": false,
  "properties": {
    "agentExamplesBlocks": {
      "type": "object",
      "description": "Per-agent example blocks keyed by agent ID.",
      "additionalProperties": { "type": "string" }
    },
    "agentBodyBlocks": {
      "type": "object",
      "description": "Per-agent body blocks keyed by agent ID.",
      "additionalProperties": { "type": "string" }
    },
    "agentFirstActionsBlocks": {
      "type": "object",
      "description": "Per-agent first actions blocks keyed by agent ID.",
      "additionalProperties": { "type": "string" }
    },
    "scopeDisciplineBlock": {
      "type": "string",
      "description": "Conditional scope discipline instructions with standalone and --extend variants."
    },
    "operationalLessons": {
      "type": "string",
      "description": "Operational lessons section content.",
      "default": "No entries yet -- update after first research run with `/post-mortem`."
    }
  }
}
```

- [ ] **Step 4: Verify JSON is valid**

```bash
node -e "JSON.parse(require('fs').readFileSync('plugin/skills/engine-creator/templates/engine-config-schema.json', 'utf8')); console.log('PASS')"
```

- [ ] **Step 5: Commit**

```bash
git add plugin/skills/engine-creator/templates/engine-config-schema.json
git commit -m "feat: add _derived to engine-config schema as required top-level key"
```

---

### Task 7: Update SKILL.md — replace generation steps with script invocation

**Files:**
- Modify: `plugin/skills/engine-creator/SKILL.md`

- [ ] **Step 1: Read the current SKILL.md**

Read `plugin/skills/engine-creator/SKILL.md` to identify the full extent of the Generation Protocol section (lines 224-341) and Post-Generation section (lines 345-357).

- [ ] **Step 2: Add Derived Content Generation section**

After the "Config Assembly" section (after line 204, before "Preview Protocol"), insert:

```markdown
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
```

- [ ] **Step 3: Replace Generation Protocol**

Replace the entire Generation Protocol section (Steps 1-9, Placeholder Derivation Rules) with:

```markdown
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
```

- [ ] **Step 4: Simplify Post-Generation**

Replace the Post-Generation section with:

```markdown
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
```

- [ ] **Step 5: Update Template Reference table**

Remove the Placeholder Derivation Rules section (now in generate.py). Keep the Template Reference table but update it to note the generator handles substitution.

- [ ] **Step 6: Bump version to 1.9.0**

Change `version: 1.8.0` to `version: 1.9.0` in the frontmatter.

- [ ] **Step 7: Verify the SKILL.md is under 200 lines**

The SKILL.md should be significantly shorter after removing Steps 1-9 and the derivation rules table (~150 lines removed, ~20 added).

- [ ] **Step 8: Commit**

```bash
git add plugin/skills/engine-creator/SKILL.md
git commit -m "feat: replace generation Steps 1-9 with Python generator invocation"
```

---

### Task 8: Simplify test-engine.md — remove impossible-to-fail checks

**Files:**
- Modify: `plugin/commands/test-engine.md`

- [ ] **Step 1: Read current test-engine.md**

Identify checks to remove (per spec Section 5):
- 4f (placeholder residue scan)
- 4k (SKILL.md line count)
- 4l (no per-fetch hashing)
- 4m (no shared file writes)
- 4p (dashboard assets present)

- [ ] **Step 2: Remove the 5 checks**

Delete checks 4f, 4k, 4l, 4m, 4p from the file. Renumber remaining checks to fill gaps.

- [ ] **Step 3: Verify remaining checks are intact**

Grep for the kept checks: 4a, 4b, 4c, 4d, 4e, 4g, 4h, 4i, 4j, 4n, 4o, 4q, 4r.

- [ ] **Step 4: Commit**

```bash
git add plugin/commands/test-engine.md
git commit -m "feat: remove impossible-to-fail test checks (generator guarantees them)"
```

---

### Task 9: Version bumps and CHANGELOG

**Files:**
- Modify: `plugin/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Bump plugin.json version**

In `plugin/.claude-plugin/plugin.json`, change `"version": "1.8.0"` to `"version": "1.9.0"`.

- [ ] **Step 2: Bump marketplace.json version**

In `.claude-plugin/marketplace.json`, change `"version": "1.8.0"` to `"version": "1.9.0"`.

- [ ] **Step 3: Add CHANGELOG entry**

Insert `## [1.9.0]` section before `## [1.8.0]`:

```markdown
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
```

- [ ] **Step 4: Commit**

```bash
git add plugin/.claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md
git commit -m "docs: update CHANGELOG and bump versions to 1.9.0"
```

---

### Task 10: Final verification

- [ ] **Step 1: Run full test suite**

```bash
cd plugin/generator && python3 -m pytest tests/test_generate.py -v
```

Expected: All tests pass.

- [ ] **Step 2: Run generator against patent engine config**

```bash
cd /workspaces/deep-research-engine-creator
python3 plugin/generator/generate.py plugin/examples/patent-intelligence-engine/engine-config.json /tmp/patent-gen-test
```

Expected: Exit code 0, all files generated, no warnings.

- [ ] **Step 3: Verify generated output has no placeholder residue**

```bash
grep -rn '{{[a-zA-Z0-9_-]*}}' /tmp/patent-gen-test/ || echo "PASS: no unresolved placeholders"
```

- [ ] **Step 4: Verify JSON schemas are valid**

```bash
node -e "JSON.parse(require('fs').readFileSync('plugin/skills/engine-creator/templates/engine-config-schema.json', 'utf8')); console.log('PASS')"
```

- [ ] **Step 5: Verify SKILL.md is under 200 lines**

```bash
wc -l plugin/skills/engine-creator/SKILL.md
```

Expected: Under 200 lines (was ~380, should be ~200 after removing generation steps).

- [ ] **Step 6: Clean up**

```bash
rm -rf /tmp/patent-gen-test
```
