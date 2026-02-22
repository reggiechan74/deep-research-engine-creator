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

# Read engine name and version using safe argument passing
ENGINE_NAME=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1]))['engineMeta']['name'])" "$ENGINE_PATH/engine-config.json")
ENGINE_VERSION=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1]))['engineMeta']['version'])" "$ENGINE_PATH/engine-config.json")
echo "Publishing: $ENGINE_NAME v$ENGINE_VERSION"

# Clone marketplace, update engine, commit, push
WORK_DIR=$(mktemp -d)
trap "rm -rf \"$WORK_DIR\"" EXIT

echo "Cloning marketplace..."
git clone --depth 1 "$MARKETPLACE_REPO" "$WORK_DIR/marketplace"

# Detect the default branch using symbolic-ref (locale-independent)
echo "Detecting default branch..."
DEFAULT_BRANCH=$(git -C "$WORK_DIR/marketplace" symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$DEFAULT_BRANCH" ]; then
    echo "WARNING: Could not detect default branch, falling back to 'main'" >&2
    DEFAULT_BRANCH="main"
fi
echo "Default branch: $DEFAULT_BRANCH"

# Handle engine directory (new or existing)
if [ -d "$WORK_DIR/marketplace/$ENGINE_NAME" ]; then
    echo "Engine directory already exists. Updating..."
    if [ "$FORCE_MODE" = false ]; then
        read -p "This will update the existing engine directory. Continue? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Publish cancelled."
            exit 0
        fi
    fi
    # Check for rsync availability, fallback to rm+cp
    if command -v rsync >/dev/null 2>&1; then
        rsync -av --delete "$ENGINE_PATH/" "$WORK_DIR/marketplace/$ENGINE_NAME/"
    else
        echo "rsync not found, using cp fallback..."
        rm -rf "$WORK_DIR/marketplace/$ENGINE_NAME"
        cp -r "$ENGINE_PATH" "$WORK_DIR/marketplace/$ENGINE_NAME"
    fi
else
    echo "Creating new engine directory..."
    cp -r "$ENGINE_PATH" "$WORK_DIR/marketplace/$ENGINE_NAME"
fi

cd "$WORK_DIR/marketplace"
git add "$ENGINE_NAME/"

# Check for actual changes before committing
if git diff --cached --quiet; then
    echo "No changes to publish."
    exit 0
fi

git commit -m "feat: add $ENGINE_NAME research engine v$ENGINE_VERSION

Published from: $ENGINE_PATH"
git push origin "$DEFAULT_BRANCH"

echo ""
echo "Successfully published $ENGINE_NAME v$ENGINE_VERSION to $MARKETPLACE_REPO"
echo "Users can install with: /plugin marketplace add $ENGINE_NAME"
