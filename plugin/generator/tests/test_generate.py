"""Tests for the deterministic engine generator."""
import json
import os
import re
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
