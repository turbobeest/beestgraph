#!/usr/bin/env bash
# beestgraph/scripts/setup-op-service-account.sh
#
# Sets up a 1Password service account token for headless access.
# After running this, all shells (including Claude Code) can use `op`
# without interactive signin.
#
# STEP 1: Create a service account at https://my.1password.com
#   → Settings → Developer → Service Accounts → New Service Account
#   → Name: "beestgraph-pi"
#   → Grant access to vault: "beestgraph"
#   → Copy the token (starts with ops_...)
#
# STEP 2: Run this script:
#   bash scripts/setup-op-service-account.sh
#
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[1password]${NC} $*"; }
warn() { echo -e "${YELLOW}[1password]${NC} $*"; }

TOKEN_FILE="$HOME/.config/op/service-account-token"

echo ""
echo "1Password Service Account Setup"
echo "================================"
echo ""
echo "This creates a persistent 1Password connection for this headless machine."
echo ""
echo "If you haven't created a service account yet:"
echo "  1. Go to https://my.1password.com"
echo "  2. Settings → Developer → Service Accounts → New Service Account"
echo "  3. Name: beestgraph-pi"
echo "  4. Grant access to vault: beestgraph"
echo "  5. Copy the token (starts with ops_...)"
echo ""

read -rp "Paste service account token: " SA_TOKEN

if [[ ! "$SA_TOKEN" =~ ^ops_ ]]; then
    warn "Token doesn't start with 'ops_'. Are you sure this is a service account token?"
    read -rp "Continue anyway? (y/N): " confirm
    [[ "$confirm" =~ ^[yY]$ ]] || exit 1
fi

# Store token securely
mkdir -p "$(dirname "$TOKEN_FILE")"
echo "$SA_TOKEN" > "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"
log "Token saved to $TOKEN_FILE (mode 600)"

# Add to shell profile so it's always available
PROFILE_LINE='export OP_SERVICE_ACCOUNT_TOKEN="$(cat ~/.config/op/service-account-token 2>/dev/null)"'

for rc in "$HOME/.bashrc" "$HOME/.profile"; do
    if ! grep -q "OP_SERVICE_ACCOUNT_TOKEN" "$rc" 2>/dev/null; then
        echo "" >> "$rc"
        echo "# 1Password service account for beestgraph" >> "$rc"
        echo "$PROFILE_LINE" >> "$rc"
        log "Added to $rc"
    else
        warn "Already in $rc"
    fi
done

# Export for current session
export OP_SERVICE_ACCOUNT_TOKEN="$SA_TOKEN"

# Verify
echo ""
log "Verifying access..."
if op vault list 2>&1 | grep -q beestgraph; then
    log "Success! Can access 'beestgraph' vault."
    echo ""
    op item list --vault beestgraph --format=table 2>/dev/null || true
else
    warn "Could not access beestgraph vault. Check that the service account has vault access."
    op vault list 2>&1
fi

echo ""
log "Done! 1Password is now available in all shells without signin."
echo "  Test: op item list --vault beestgraph"
