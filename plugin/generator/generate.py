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
