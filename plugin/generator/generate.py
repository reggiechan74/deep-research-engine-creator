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
    p = {}
    meta = config["engineMeta"]
    advanced = config.get("advanced", {})
    budgets = advanced.get("tokenBudgets", {})
    qf = config.get("qualityFramework", {})
    ss = config.get("sourceStrategy", {})
    tiers_cfg = ss.get("credibilityTiers", {})
    pipeline = config.get("agentPipeline", {})
    agents = pipeline.get("agents", [])
    tiers = pipeline.get("tiers", {})
    output = config.get("outputStructure", {})
    prompts = config.get("prompts", {})
    derived = config.get("_derived", {})
    cm = qf.get("citationManagement", {})
    prov = qf.get("provenance", {})
    vvc = qf.get("vvc", {})
    vvc_enabled = vvc.get("enabled", False)
    engine_name = meta["name"]

    # --- Direct config reads ---
    p["engineName"] = engine_name
    p["engineDisplayName"] = meta["displayName"]
    p["domain"] = meta["domain"]
    p["audience"] = meta["audience"]
    p["engineVersion"] = meta.get("version", "1.0.0")
    p["engineDescription"] = meta.get("description", "")
    p["authorName"] = meta.get("author", {}).get("name", "")
    p["authorEmail"] = meta.get("author", {}).get("email", "")
    p["skillDirName"] = engine_name
    p["mode"] = meta.get("mode", "self-contained")
    p["createdAt"] = meta.get("createdAt", "")
    p["baseSkillPath"] = meta.get("baseSkillPath", "")

    p["maxIterations"] = str(advanced.get("maxIterationsPerQuestion", 3))
    p["explorationDepth"] = str(advanced.get("explorationDepth", 2))
    p["maxWebFetches"] = str(advanced.get("maxWebFetchesPerAgent", 10))
    p["dashboardPort"] = str(advanced.get("dashboardPort", 3847))
    p["comprehensiveFollowUpAgentCap"] = str(advanced.get("comprehensiveFollowUpAgentCap", 2))

    p["planningBudget"] = str(budgets.get("planning", 2000))
    p["researchBudget"] = str(budgets.get("research", 15000))
    p["synthesisBudget"] = str(budgets.get("synthesis", 8000))
    p["reportingBudget"] = str(budgets.get("reporting", 10000))
    p["provenanceBudget"] = str(budgets.get("provenance", 5000))

    p["citationStandard"] = qf.get("citationStandard", "APA 7th Edition")
    p["confidenceHigh"] = qf.get("confidenceScoring", {}).get("HIGH", "")
    p["confidenceMedium"] = qf.get("confidenceScoring", {}).get("MEDIUM", "")
    p["confidenceLow"] = qf.get("confidenceScoring", {}).get("LOW", "")
    p["confidenceSpeculative"] = qf.get("confidenceScoring", {}).get("SPECULATIVE", "")
    p["minimumEvidence"] = qf.get("minimumEvidence", "")

    p["reportOutputDir"] = output.get("reportOutputDir", "./research-reports")
    p["fileNaming"] = output.get("fileNaming", "{date}_{topic_slug}_report.md")

    p["reportingTone"] = prompts.get("reportingTone", "Professional and analytical")
    p["globalPreamble"] = prompts.get("globalPreamble", "")
    p["synthesisInstructions"] = prompts.get("synthesisInstructions", "")

    # Citation management fields
    p["verificationMode"] = cm.get("verificationMode", "none")
    p["urlLivenessCheck"] = str(cm.get("urlLivenessCheck", False))
    p["contentClaimMatching"] = str(cm.get("contentClaimMatching", False))
    p["sourceFreshnessThreshold"] = cm.get("sourceFreshnessThreshold", "")
    p["deadLinkHandling"] = cm.get("deadLinkHandling", "flag-only")
    p["probeOnDiscovery"] = str(cm.get("probeOnDiscovery", False))

    # Source tier names and sources
    for i in range(1, 6):
        tier_key = f"tier{i}"
        tier = tiers_cfg.get(tier_key, {})
        p[f"tier{i}Name"] = tier.get("name", "")
        sources = tier.get("sources", [])
        p[f"tier{i}Sources"] = ", ".join(sources) if sources else ""

    # Provenance
    p["reverifiableDefault"] = str(prov.get("reverifiableDefault", False))
    audit_tiers = prov.get("auditPhase", {}).get("tiers", [])
    audit_parts = []
    for t in audit_tiers:
        audit_parts.append(f"{t.capitalize()}: run")
    p["auditTierBehavior"] = " | ".join(audit_parts) if audit_parts else ""

    # Provenance tier column
    provenance_columns = []
    for tier_name in ["Quick", "Standard", "Deep", "Comprehensive"]:
        if tier_name.lower() in audit_tiers:
            provenance_columns.append("Hash + Audit")
        else:
            provenance_columns.append("Hash-only")
    p["provenanceTierColumn"] = ", ".join(provenance_columns)

    # --- Formatted outputs ---

    # Keywords
    keywords = meta.get("keywords", [])
    p["keywords"] = ", ".join(f'"{k}"' for k in keywords)

    # Source hierarchy
    hierarchy_lines = []
    for i in range(1, 6):
        name = p[f"tier{i}Name"]
        sources = p[f"tier{i}Sources"]
        hierarchy_lines.append(f"**Tier {i} ({name}):** {sources}")
    p["sourceHierarchy"] = "\n".join(hierarchy_lines)

    # Sample questions
    sq = config.get("sampleQuestions", [])
    p["sampleQuestions"] = "\n".join(f"{i+1}. {q}" for i, q in enumerate(sq))

    # Report sections
    sections = output.get("reportSections", [])
    p["reportSections"] = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sections))

    # Preferred sites
    preferred = ss.get("preferredSites", ss.get("preferredSources", []))
    p["preferredSites"] = "\n".join(f"- {s}" for s in preferred) if preferred else ""

    # Excluded sources
    excluded = ss.get("excludedSources", [])
    p["excludedSources"] = "\n".join(f"- {s}" for s in excluded) if excluded else "None"

    # Search templates
    templates = ss.get("searchTemplates", [])
    p["additionalSearchTemplates"] = "\n".join(
        f"{i+1}. **{t.get('name', '')}**: `{t.get('pattern', '')}`"
        for i, t in enumerate(templates)
    )

    # Validation rules
    rules = qf.get("validationRules", [])
    p["validationRules"] = "\n".join(f"{i+1}. {r}" for i, r in enumerate(rules))

    # Special deliverables
    deliverables = output.get("specialDeliverables", [])
    p["specialDeliverables"] = "\n".join(f"- {d}" for d in deliverables) if deliverables else ""

    # Filters
    filters_parts = []
    lang_filters = ss.get("languageFilters", ss.get("filters", {}).get("language", []))
    if isinstance(lang_filters, list) and lang_filters:
        filters_parts.append("**Language:** " + ", ".join(lang_filters))
    geo_filters = ss.get("geographicFilters", ss.get("filters", {}).get("geographic", []))
    if isinstance(geo_filters, list) and geo_filters:
        filters_parts.append("**Geographic:** " + ", ".join(geo_filters))
    p["filters"] = "\n".join(filters_parts) if filters_parts else ""

    # Agent specialization (all agents joined)
    p["agentSpecialization"] = "; ".join(a.get("specialization", "") for a in agents)

    # Agent overrides
    overrides = prompts.get("agentOverrides", {})
    if overrides:
        override_lines = []
        for aid, text in overrides.items():
            override_lines.append(f"**{aid}:** {text}")
        p["agentOverrides"] = "\n\n".join(override_lines)
    else:
        p["agentOverrides"] = ""

    # --- Tier descriptions ---
    agent_map = {a["id"]: a for a in agents}

    def _agent_roles(tier_name):
        tier_agents = tiers.get(tier_name, {}).get("agents", [])
        return [agent_map[aid]["role"] for aid in tier_agents if aid in agent_map]

    quick_roles = _agent_roles("quick")
    p["quickTierDescription"] = f"Single-agent lookup using {quick_roles[0]}" if quick_roles else "Single-agent lookup"

    standard_roles = _agent_roles("standard")
    n_std = len(standard_roles)
    p["standardTierDescription"] = f"{n_std} agents: {', '.join(standard_roles)}"

    deep_roles = _agent_roles("deep")
    n_deep = len(deep_roles)
    p["deepTierDescription"] = f"Full pipeline with {n_deep} agents: {', '.join(deep_roles)}"

    comp_roles = _agent_roles("comprehensive")
    n_comp = len(comp_roles)
    p["comprehensiveTierDescription"] = f"All {n_comp} agents + follow-up round"

    # Quick agent ID
    quick_agents = tiers.get("quick", {}).get("agents", [])
    p["quickAgentId"] = f"{engine_name}:{quick_agents[0]}" if quick_agents else ""

    # Tier summary (for command template)
    summary_rows = []
    for tier_name in ["Quick", "Standard", "Deep", "Comprehensive"]:
        desc_key = f"{tier_name.lower()}TierDescription"
        summary_rows.append(f"| `--{tier_name.lower()}` | {p.get(desc_key, '')} |")
    p["tierSummary"] = "\n".join(summary_rows)

    # Tier config table
    def _tier_row(tier_name):
        tc = tiers.get(tier_name.lower(), {})
        tier_agents = tc.get("agents", [])
        qualified = [f"{engine_name}:{aid}" for aid in tier_agents]
        has_follow_up = tc.get("followUpRound", False)

        planning = "Yes" if tier_name.lower() != "quick" else "No"
        synthesis = "Yes" if tier_name.lower() != "quick" else "No"
        report = "Inline" if tier_name.lower() == "quick" else "Full"
        prov_col = "Hash + Audit" if tier_name.lower() in audit_tiers else "Hash-only"
        gate = "No" if tier_name.lower() == "quick" else "Yes"

        agent_str = ", ".join(qualified)
        if has_follow_up:
            agent_str += " + gap follow-up"
        return f"| {tier_name} | {planning} | {agent_str} | {synthesis} | {report} | {prov_col} | {gate} |"

    tier_rows = [_tier_row(t) for t in ["Quick", "Standard", "Deep", "Comprehensive"]]
    p["tierConfigTable"] = "\n".join(tier_rows)

    # Agent deployment blocks
    deploy_blocks = []
    for agent in agents:
        aid = agent["id"]
        role = agent["role"]
        model = agent.get("model", "sonnet")
        spec = agent.get("specialization", "")
        fq_name = f"{engine_name}:{aid}"
        block = f"#### Agent: {role}\n\nDeploy **{fq_name}** (model: {model}, type: {fq_name}) with specialization:\n\n{spec}"
        override = overrides.get(aid, "")
        if override:
            block += f"\n\n**Custom Instructions:** {override}"
        deploy_blocks.append(block)
    p["agentDeploymentBlocks"] = "\n\n".join(deploy_blocks)

    # Sub-agent list
    sub_lines = [
        "- research-planning-specialist",
        "- synthesis-specialist",
        "- research-reporting-specialist",
    ]
    for agent in agents:
        aid = agent["id"]
        role = agent["role"]
        if aid != "vvc-specialist":
            sub_lines.append(f"- {engine_name}:{aid} ({role})")
    if vvc_enabled:
        sub_lines.append("- vvc-specialist (Verification, Validation & Correction Specialist)")
    p["subAgentList"] = "\n".join(sub_lines)

    # File structure (per-agent)
    file_lines = []
    for agent in agents:
        aid = agent["id"]
        if aid != "vvc-specialist":
            file_lines.append(f"├── [TOPIC_SLUG]_Claims_{aid}.md")
            file_lines.append(f"├── [TOPIC_SLUG]_{aid}_Bibliography.md")
    p["fileStructure"] = "\n".join(file_lines)

    # Source hierarchy table (for sources command)
    sh_rows = []
    for i in range(1, 6):
        name = p[f"tier{i}Name"]
        sources = p[f"tier{i}Sources"]
        sh_rows.append(f"| Tier {i} | {name} | {sources} |")
    p["sourceHierarchyTable"] = "\n".join(sh_rows)

    # Search templates table
    st_rows = []
    for t in templates:
        st_rows.append(f"| {t.get('name', '')} | `{t.get('pattern', '')}` |")
    p["searchTemplatesTable"] = "\n".join(st_rows)

    # Agent table (for README)
    agent_table_lines = ["| Agent | Role | Model | Specialization |", "|-------|------|-------|----------------|"]
    for agent in agents:
        agent_table_lines.append(
            f"| {agent['id']} | {agent['role']} | {agent.get('model', 'sonnet')} | {agent.get('specialization', '')} |"
        )
    p["agentTable"] = "\n".join(agent_table_lines)

    # Source table (for README)
    source_table_lines = ["| Tier | Name | Sources |", "|------|------|---------|"]
    for i in range(1, 6):
        source_table_lines.append(f"| {i} | {p[f'tier{i}Name']} | {p[f'tier{i}Sources']} |")
    p["sourceTable"] = "\n".join(source_table_lines)

    # Quality summary (for README)
    p["qualitySummary"] = (
        f"- **Confidence scoring:** HIGH / MEDIUM / LOW / SPECULATIVE on every claim\n"
        f"- **Citation standard:** {p['citationStandard']}\n"
        f"- **Minimum evidence:** {p['minimumEvidence']}\n"
        f"- **Source credibility:** 5-tier hierarchy from {p['tier1Name']} to {p['tier5Name']}"
    )

    # Verification mode instructions
    vm = p["verificationMode"]
    if vm == "none":
        p["verificationModeInstructions"] = "Source verification is disabled. Trust agent-reported citations without independent verification."
    elif vm == "spot-check":
        p["verificationModeInstructions"] = "Verify a random sample of HIGH-confidence citations (minimum 3 or 20% of HIGH citations, whichever is greater). Record verification results in Methodology_Log.md."
    elif vm == "comprehensive":
        p["verificationModeInstructions"] = "Verify every cited source. Check URL accessibility, confirm source content supports the claim, and record all results in a dedicated verification pass."
    else:
        p["verificationModeInstructions"] = ""

    # Dead link instructions
    dl = p["deadLinkHandling"]
    if dl == "flag-only":
        p["deadLinkInstructions"] = "Mark dead links with [DEAD LINK] tag in the bibliography. Do not attempt recovery."
    elif dl == "archive-fallback":
        p["deadLinkInstructions"] = "Attempt Wayback Machine retrieval at https://web.archive.org/web/*/[URL]. If archived version found, use it and note [ARCHIVED: date] in bibliography. If not found, mark as [DEAD LINK]."
    elif dl == "exclude-from-high":
        p["deadLinkInstructions"] = "Downgrade any claim that relies solely on unreachable sources from HIGH to MEDIUM confidence. Note the downgrade reason in the claims table."
    else:
        p["deadLinkInstructions"] = ""

    # Verification report config
    vr = cm.get("verificationReport", {})
    if vr.get("enabled", False):
        scope = vr.get("scope", "all citations")
        p["verificationReportConfig"] = f"Generate a standalone Citation Verification Report. Scope: {scope}. Include summary statistics, per-citation verification table, issues found, and remediation recommendations."
    else:
        p["verificationReportConfig"] = "Verification report generation is disabled."

    # Output files (for README)
    output_files_lines = [
        "| File | Description |",
        "|------|-------------|",
        "| `_Research_Outline.md` | Strategic research framework |",
        "| `_Claims_[AgentID].md` | Per-agent claims with confidence |",
        "| `_[AgentID]_Bibliography.md` | Per-agent source bibliography |",
        "| `_Synthesis_Report.md` | Integrated findings |",
    ]
    if vvc_enabled:
        output_files_lines.append("| `_Draft_Report.md` | Draft report with claim tagging |")
        output_files_lines.append("| `_VVC_Verification_Report.md` | Claim verification results |")
        output_files_lines.append("| `_VVC_Correction_Log.md` | Applied corrections |")
    output_files_lines.append("| `_Comprehensive_Report.md` | Final professional report |")
    output_files_lines.append("| `_Master_Bibliography.md` | Consolidated bibliography |")
    p["outputFiles"] = "\n".join(output_files_lines)

    # --- Computed values ---
    p["pipelinePhaseCount"] = "seven" if vvc_enabled else "five"
    p["pipelinePhaseDescription"] = "seven-phase" if vvc_enabled else "five-phase"
    p["phase4Name"] = "Draft Reporting" if vvc_enabled else "Professional Reporting"
    p["phase4Description"] = (
        "Draft report generation with claim tagging for VVC verification" if vvc_enabled
        else "Comprehensive report generation with consolidated bibliography"
    )
    p["phase4ReportType"] = "draft" if vvc_enabled else "final"
    p["phase4OutputFile"] = "Draft_Report.md" if vvc_enabled else "Comprehensive_Report.md"

    max_web = advanced.get("maxWebFetchesPerAgent", 10)
    p["vvcWebFetchCap"] = str(min(max_web * 3, 50))

    # --- Conditional VVC blocks ---
    if vvc_enabled:
        claim_types = vvc.get("claimTypes", [])
        scope = vvc.get("verificationScope", {})
        tier_behavior = vvc.get("tierBehavior", {})
        vvc_budget = budgets.get("vvc", 8000)

        # vvcPhaseLines
        p["vvcPhaseLines"] = (
            "| 5 | VVC-Verify | Verify draft report claims against cited sources, produce verification report |\n"
            "| 6 | VVC-Correct | Implement corrections, produce final Comprehensive Report + correction log |"
        )

        # vvcClaimTaggingInstructions
        tag_examples = " ".join(f"`[{ct['tag']}]`" for ct in claim_types)
        p["vvcClaimTaggingInstructions"] = (
            f"\n- **CLAIM TAGGING (REQUIRED):** Tag every factual assertion with its claim type: "
            f"`[VC]` for verifiable claims with cited sources, `[PO]` for professional opinions/analytical judgments, "
            f"`[IE]` for inferences/extrapolations. Place tags at the end of each claim sentence before the citation. "
            f"Example: 'Toyota invested $142M in solid-state battery research [VC][^3]'. "
            f"This tagging is essential for the VVC verification phase."
        )

        # vvcClaimTaxonomyBlock
        taxonomy_lines = ["### Claim Type Taxonomy\n"]
        taxonomy_lines.append("| Tag | Label | Description | Requires Verification |")
        taxonomy_lines.append("|-----|-------|-------------|----------------------|")
        for ct in claim_types:
            taxonomy_lines.append(f"| [{ct['tag']}] | {ct['label']} | {ct['description']} | {'Yes' if ct.get('requiresVerification', False) else 'No'} |")
        taxonomy_lines.append("\n### VVC Verification Scope\n")
        taxonomy_lines.append("| Confidence Level | Verification % |")
        taxonomy_lines.append("|-----------------|----------------|")
        for level in ["HIGH", "MEDIUM", "LOW", "SPECULATIVE"]:
            pct = scope.get(level, 0)
            taxonomy_lines.append(f"| {level} | {pct}% |")
        p["vvcClaimTaxonomyBlock"] = "\n".join(taxonomy_lines)

        # vvcClaimTaxonomySummary
        p["vvcClaimTaxonomySummary"] = (
            "### Claim Taxonomy (VVC)\n\n"
            "When VVC is active, tag every factual claim in reports. See `${CLAUDE_SKILL_DIR}/vvc-pipeline.md` "
            "for the full claim taxonomy, verification scope, and verification process.\n\n"
            "Claim types: `[VC]` Verifiable Claim (requires verification), `[PO]` Professional Opinion (no verification), "
            "`[IE]` Inferred/Extrapolated (no verification)."
        )

        # vvcVerifyPhaseBlock
        p["vvcVerifyPhaseBlock"] = (
            f"### Phase 5: VVC-Verify\n\n"
            f"Deploy **vvc-specialist** to verify draft report claims:\n\n"
            f"1. Read draft report and all bibliographies\n"
            f"2. Extract all [VC]-tagged claims with cited sources and confidence tiers\n"
            f"3. Apply verification scope: {scope.get('HIGH', 100)}% HIGH, {scope.get('MEDIUM', 100)}% MEDIUM, "
            f"{scope.get('LOW', 0)}% LOW, {scope.get('SPECULATIVE', 0)}% SPECULATIVE\n"
            f"4. Per-claim: locate source → extract quote → analyze alignment → classify "
            f"(CONFIRMED/PARAPHRASED/OVERSTATED/UNDERSTATED/DISPUTED/UNSUPPORTED/SOURCE_UNAVAILABLE) → "
            f"recommend (KEEP/REVISE/DOWNGRADE/REMOVE/REPLACE_SOURCE) → write corrected text\n"
            f"5. Output: `_VVC_Verification_Report.md` with summary stats + per-claim table"
        )

        # vvcCorrectPhaseBlock
        tb_deep = tier_behavior.get("deep", "full")
        tb_comp = tier_behavior.get("comprehensive", "full")
        if tb_deep == "full" or tb_comp == "full":
            p["vvcCorrectPhaseBlock"] = (
                "### Phase 6: VVC-Correct\n\n"
                "Deploy **vvc-specialist** (second pass):\n\n"
                "1. Read verification report per-claim table\n"
                "2. Apply corrections mechanically into draft report:\n"
                "   - REVISE/DOWNGRADE: substitute Corrected Text verbatim\n"
                "   - REMOVE: delete claim and adjust surrounding narrative\n"
                "   - REPLACE_SOURCE: substitute Corrected Text and update bibliography\n"
                "3. Preserve all KEEP/CONFIRMED claims unchanged\n"
                "4. Output: `_Comprehensive_Report.md` (final) + `_VVC_Correction_Log.md` + Verification Statement + Provenance Appendix"
            )
        else:
            p["vvcCorrectPhaseBlock"] = ""

        # vvcFileStructure
        p["vvcFileStructure"] = (
            "├── [TOPIC_SLUG]_Draft_Report.md\n"
            "├── [TOPIC_SLUG]_VVC_Verification_Report.md\n"
            "├── [TOPIC_SLUG]_VVC_Correction_Log.md  # When tier behavior is 'full'"
        )

        # vvcFeatureBullets
        p["vvcFeatureBullets"] = (
            "- **Claim verification, not just citations (VVC)** -- citations are URLs; they don't prove the AI read the source correctly. "
            "VVC extracts every [VC]-tagged claim, re-fetches the cited source, and checks: (1) Is the source credible? "
            "(2) Was it accurately represented? Failed claims are auto-corrected or flagged. Citations can hallucinate. Verified claims can't.\n"
            "- **Claim type taxonomy** -- claims tagged as [VC] (verifiable), [PO] (professional opinion), or [IE] (inferred) to focus verification effort\n"
            "- **Tier-aware VVC** -- Quick: no VVC, Standard: verify-only, Deep/Comprehensive: full verify+correct"
        )

        # vvcBudgetLine
        p["vvcBudgetLine"] = f"VVC:            {vvc_budget} tokens output max (verification + correction combined)"

        # vvcSubAgentNote
        p["vvcSubAgentNote"] = "The vvc-specialist is a pipeline agent that runs in Phases 5-6 (post-reporting). It does NOT participate in Phase 2 research."

        # vvcExtensionOverride
        ext_lines = ["#### VVC Configuration Override\n"]
        ext_lines.append(f"- **Enabled:** true")
        ct_strs = [f"[{ct['tag']}] {ct['label']}" for ct in claim_types]
        ext_lines.append(f"- **Claim types:** {', '.join(ct_strs)}")
        ext_lines.append(f"- **Verification scope:** HIGH {scope.get('HIGH', 100)}%, MEDIUM {scope.get('MEDIUM', 100)}%, LOW {scope.get('LOW', 0)}%, SPECULATIVE {scope.get('SPECULATIVE', 0)}%")
        for tn, tb in tier_behavior.items():
            ext_lines.append(f"- **{tn.capitalize()}:** {tb}")
        p["vvcExtensionOverride"] = "\n".join(ext_lines)

        # vvcTierNote
        tb_parts = [f"{tn.capitalize()}: {tb}" for tn, tb in tier_behavior.items()]
        p["vvcTierNote"] = "**VVC:** " + " | ".join(tb_parts)

        # vvcReadmeSection
        p["vvcReadmeSection"] = (
            "## Verification, Validation & Correction (VVC)\n\n"
            "Every research tool cites sources, but a citation is just a URL — it doesn't mean the AI read the source correctly. "
            "VVC goes further by extracting claims, re-fetching sources, and verifying both source credibility and accurate representation.\n\n"
            "**Claim types:** " + ", ".join(f"`[{ct['tag']}]` {ct['label']}" for ct in claim_types) + "\n\n"
            "**Verification scope:** " + ", ".join(f"{level} {scope.get(level, 0)}%" for level in ["HIGH", "MEDIUM", "LOW", "SPECULATIVE"]) + "\n\n"
            "**Tier behavior:** " + " | ".join(f"{tn.capitalize()}: {tb}" for tn, tb in tier_behavior.items())
        )

        # vvcArgumentHint
        p["vvcArgumentHint"] = " [--no-vvc]"

    else:
        # VVC disabled — all empty strings
        for key in [
            "vvcPhaseLines", "vvcClaimTaggingInstructions", "vvcVerifyPhaseBlock",
            "vvcCorrectPhaseBlock", "vvcFileStructure", "vvcFeatureBullets",
            "vvcBudgetLine", "vvcSubAgentNote", "vvcExtensionOverride",
            "vvcTierNote", "vvcReadmeSection", "vvcArgumentHint",
            "vvcClaimTaxonomyBlock", "vvcClaimTaxonomySummary",
        ]:
            p[key] = ""

    # --- _derived passthroughs ---
    p["scopeDisciplineBlock"] = derived.get("scopeDisciplineBlock", "")
    p["operationalLessons"] = derived.get(
        "operationalLessons",
        "No entries yet -- update after first research run with `/post-mortem`."
    )

    return p


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
