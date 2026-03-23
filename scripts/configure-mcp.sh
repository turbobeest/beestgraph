#!/usr/bin/env bash
# beestgraph/scripts/configure-mcp.sh — Wire up all 3 MCP servers for Claude Code
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[beestgraph]${NC} $*"; }
warn() { echo -e "${YELLOW}[beestgraph]${NC} $*"; }

VAULT_PATH="${VAULT_PATH:-$HOME/vault}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log "Configuring MCP servers for beestgraph..."
log "Vault path: ${VAULT_PATH}"
log "Project dir: ${PROJECT_DIR}"

# ── 1. keep.md MCP (HTTP transport, cloud-hosted) ───────────
log "Adding keep.md MCP server..."
claude mcp add --transport http keep https://keep.md/mcp 2>/dev/null || \
    warn "keep.md MCP may already be configured or claude not authenticated yet."

# ── 2. Filesystem MCP (stdio, local) ────────────────────────
log "Adding Filesystem MCP server..."
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem "$VAULT_PATH" 2>/dev/null || \
    warn "Filesystem MCP may already be configured."

# ── 3. FalkorDB MCP (stdio, local) ──────────────────────────
log "Adding FalkorDB MCP server..."
claude mcp add falkordb \
    -e FALKORDB_HOST=localhost \
    -e FALKORDB_PORT=6379 \
    -- npx -y @falkordb/falkordb-mcp-server 2>/dev/null || \
    warn "FalkorDB MCP may already be configured."

# ── Verify ───────────────────────────────────────────────────
log "Current MCP servers:"
claude mcp list 2>/dev/null || warn "Could not list MCP servers. Authenticate first."

echo ""
log "MCP configuration complete!"
echo ""
echo "  Test with:"
echo "    claude -p 'List my keep.md inbox items'"
echo "    claude -p 'How many nodes are in the FalkorDB graph?'"
echo ""
