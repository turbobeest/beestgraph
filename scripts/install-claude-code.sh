#!/usr/bin/env bash
# beestgraph/scripts/install-claude-code.sh — Install Claude Code on ARM64
# Handles known aarch64 bugs (issues #3569, #27405)
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[beestgraph]${NC} $*"; }
warn() { echo -e "${YELLOW}[beestgraph]${NC} $*"; }
err()  { echo -e "${RED}[beestgraph]${NC} $*" >&2; }

# ── Check architecture ───────────────────────────────────────
ARCH=$(uname -m)
log "Detected architecture: ${ARCH}"

if [[ "$ARCH" != "aarch64" && "$ARCH" != "arm64" ]]; then
    warn "This script is optimized for ARM64 (Raspberry Pi 5)."
    warn "On x86_64, you can use: curl -fsSL https://claude.ai/install.sh | sh"
fi

# ── Check Node.js ────────────────────────────────────────────
if ! command -v node &>/dev/null; then
    err "Node.js is required. Run scripts/setup.sh first."
    exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//')
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)

if (( NODE_MAJOR < 18 )); then
    err "Node.js 18+ required. Found: v${NODE_VERSION}"
    exit 1
fi

log "Node.js version: v${NODE_VERSION}"

# ── Install Claude Code via npm ──────────────────────────────
# The native installer (claude.ai/install.sh) has a bug rejecting
# aarch64 as "Unsupported architecture: arm" (GitHub issue #3569).
# npm install works correctly on ARM64.

log "Installing Claude Code via npm (bypasses ARM64 installer bug)..."
npm install -g @anthropic-ai/claude-code

if command -v claude &>/dev/null; then
    log "Claude Code installed: $(claude --version 2>/dev/null || echo 'installed')"
else
    err "Claude Code installation failed."
    exit 1
fi

# ── Authentication guidance ──────────────────────────────────
echo ""
log "Claude Code installed successfully!"
echo ""
echo "  Authentication options:"
echo ""
echo "  Option A — API key (recommended for headless/server use):"
echo "    export ANTHROPIC_API_KEY=sk-ant-..."
echo "    echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc"
echo ""
echo "  Option B — OAuth (interactive, may need workaround on ARM64):"
echo "    If 'claude login' fails on ARM64 (issue #27405):"
echo "    1. Run 'claude login' on an x86_64 machine"
echo "    2. Copy credentials to the Pi:"
echo "       scp ~/.claude/.credentials.json pi@beestgraph:~/.claude/"
echo ""
echo "  Option C — Claude Max subscription:"
echo "    claude login  (follow browser-based OAuth flow)"
echo ""
echo "  After authentication, verify with:"
echo "    claude -p 'Hello, confirm you are working on beestgraph'"
echo ""
