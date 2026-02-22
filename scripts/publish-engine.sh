#!/usr/bin/env bash
set -euo pipefail

# publish-engine.sh — Push a generated engine plugin to a marketplace repo
# Usage: publish-engine.sh <engine-path> <marketplace-repo-url>

ENGINE_PATH="${1:?Usage: publish-engine.sh <engine-path> <marketplace-repo-url>}"
MARKETPLACE_REPO="${2:?Usage: publish-engine.sh <engine-path> <marketplace-repo-url>}"

# Validate engine structure
if [ ! -f "$ENGINE_PATH/engine-config.json" ]; then
    echo "ERROR: No engine-config.json found at $ENGINE_PATH" >&2
    exit 1
fi
if [ ! -f "$ENGINE_PATH/.claude-plugin/plugin.json" ]; then
    echo "ERROR: No .claude-plugin/plugin.json found at $ENGINE_PATH" >&2
    exit 1
fi

# Read engine name and version
ENGINE_NAME=$(python3 -c "import json; print(json.load(open('$ENGINE_PATH/engine-config.json'))['engineMeta']['name'])")
ENGINE_VERSION=$(python3 -c "import json; print(json.load(open('$ENGINE_PATH/engine-config.json'))['engineMeta']['version'])")
echo "Publishing: $ENGINE_NAME v$ENGINE_VERSION"

# Clone marketplace, copy engine, commit, push
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

echo "Cloning marketplace..."
git clone --depth 1 "$MARKETPLACE_REPO" "$TMPDIR/marketplace"

# Copy engine to marketplace
echo "Copying engine files..."
cp -r "$ENGINE_PATH" "$TMPDIR/marketplace/$ENGINE_NAME"

cd "$TMPDIR/marketplace"
git add "$ENGINE_NAME/"
git commit -m "feat: add $ENGINE_NAME research engine v$ENGINE_VERSION"
git push origin main

echo ""
echo "Successfully published $ENGINE_NAME v$ENGINE_VERSION to $MARKETPLACE_REPO"
echo "Users can install with: /plugin marketplace add $ENGINE_NAME"
