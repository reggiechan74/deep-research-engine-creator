#!/usr/bin/env bash
set -euo pipefail

# publish-engine.sh — Push a generated engine plugin to a marketplace repo
# Usage: publish-engine.sh <engine-path> <marketplace-repo-url> [--force]
# Options:
#   --force    Skip confirmation prompts when updating existing engines

ENGINE_PATH="${1:?Usage: publish-engine.sh <engine-path> <marketplace-repo-url> [--force]}"
MARKETPLACE_REPO="${2:?Usage: publish-engine.sh <engine-path> <marketplace-repo-url> [--force]}"
FORCE_FLAG="${3:-}"
FORCE_MODE=false
if [ "$FORCE_FLAG" = "--force" ]; then
    FORCE_MODE=true
fi

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

# Clone marketplace, update engine, commit, push
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

echo "Cloning marketplace..."
git clone --depth 1 "$MARKETPLACE_REPO" "$TMPDIR/marketplace"

# Detect the default branch
echo "Detecting default branch..."
DEFAULT_BRANCH=$(git -C "$TMPDIR/marketplace" remote show origin | grep 'HEAD branch' | awk '{print $NF}')
echo "Default branch: $DEFAULT_BRANCH"

# Handle engine directory (new or existing)
if [ -d "$TMPDIR/marketplace/$ENGINE_NAME" ]; then
    echo "Engine directory already exists. Updating with rsync..."
    if [ "$FORCE_MODE" = false ]; then
        read -p "This will update the existing engine directory. Continue? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Publish cancelled."
            exit 0
        fi
    fi
    rsync -av --delete "$ENGINE_PATH/" "$TMPDIR/marketplace/$ENGINE_NAME/"
else
    echo "Creating new engine directory..."
    cp -r "$ENGINE_PATH" "$TMPDIR/marketplace/$ENGINE_NAME"
fi

cd "$TMPDIR/marketplace"
git add "$ENGINE_NAME/"

# Check for actual changes before committing
if git diff --cached --quiet; then
    echo "No changes to publish."
    exit 0
fi

git commit -m "feat: add $ENGINE_NAME research engine v$ENGINE_VERSION"
git push origin "$DEFAULT_BRANCH"

echo ""
echo "Successfully published $ENGINE_NAME v$ENGINE_VERSION to $MARKETPLACE_REPO"
echo "Users can install with: /plugin marketplace add $ENGINE_NAME"
