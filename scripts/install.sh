#!/usr/bin/env bash
# install.sh — Install Hermes Chinese Skill System
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PLUGIN_DIR="$HERMES_HOME/plugins/cn-skill-loader"

echo "🔌 Installing cn-skill-loader plugin..."
mkdir -p "$HERMES_HOME/plugins"
cp -r "$REPO_DIR/plugin/cn-skill-loader" "$PLUGIN_DIR"
echo "✅ Plugin installed to: $PLUGIN_DIR"

# Check if plugin is enabled in config
CONFIG_FILE="$HERMES_HOME/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    if grep -q "cn-skill-loader" "$CONFIG_FILE" 2>/dev/null; then
        echo "✅ Plugin already enabled in config.yaml"
    else
        echo "⚠️  Add 'cn-skill-loader' to plugins.enabled in $CONFIG_FILE"
        echo "   Example:"
        echo "     plugins:"
        echo "       enabled:"
        echo "         - cn-skill-loader"
    fi
else
    echo "⚠️  No config.yaml found. After creating it, add:"
    echo "     plugins:"
    echo "       enabled:"
    echo "         - cn-skill-loader"
fi

# Symlink skill index for easy access
SKILL_INDEX_TARGET="$HERMES_HOME/skills/chinese-skill-index.json"
if [ ! -f "$SKILL_INDEX_TARGET" ]; then
    mkdir -p "$HERMES_HOME/skills"
    cp "$REPO_DIR/skills/chinese-skill-index.json" "$SKILL_INDEX_TARGET"
    echo "✅ Skill index copied to: $SKILL_INDEX_TARGET"
fi

echo ""
echo "🎉 Hermes Chinese Skill System installed!"
echo "   Restart your Hermes session to activate."
echo ""
echo "   After upgrading hermes-agent, run:"
echo "     python $REPO_DIR/scripts/hermes-cn-patches.py"
