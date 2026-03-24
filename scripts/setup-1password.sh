#!/usr/bin/env bash
# beestgraph/scripts/setup-1password.sh
# Creates a beestgraph vault in 1Password and stores credentials.
# Run interactively: eval $(op signin) && bash scripts/setup-1password.sh
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[1password]${NC} $*"; }
warn() { echo -e "${YELLOW}[1password]${NC} $*"; }

# ── Verify signed in ──────────────────────────────────────────
if ! op vault list &>/dev/null; then
    echo "Not signed in. Run: eval \$(op signin)"
    exit 1
fi

log "Signed in to 1Password."

# ── Create beestgraph vault (idempotent) ──────────────────────
if op vault get beestgraph &>/dev/null 2>&1; then
    log "Vault 'beestgraph' already exists."
else
    op vault create beestgraph --description "beestgraph knowledge graph credentials"
    log "Created vault 'beestgraph'."
fi

# ── Store keep.md API key ─────────────────────────────────────
if op item get "keep.md" --vault beestgraph &>/dev/null 2>&1; then
    warn "Item 'keep.md' already exists. Skipping."
else
    echo ""
    read -rp "keep.md API key (leave empty to skip): " KEEPMD_KEY
    if [[ -n "$KEEPMD_KEY" ]]; then
        op item create \
            --category="API Credential" \
            --title="keep.md" \
            --vault=beestgraph \
            "credential=$KEEPMD_KEY" \
            "url=https://keep.md" \
            "notes=keep.md inbox poller API key for beestgraph"
        log "Stored keep.md API key."
    else
        warn "Skipped keep.md."
    fi
fi

# ── Store Telegram bot token ──────────────────────────────────
if op item get "Telegram Bot" --vault beestgraph &>/dev/null 2>&1; then
    warn "Item 'Telegram Bot' already exists. Skipping."
else
    echo ""
    read -rp "Telegram bot token (leave empty to skip): " TELEGRAM_TOKEN
    if [[ -n "$TELEGRAM_TOKEN" ]]; then
        op item create \
            --category="API Credential" \
            --title="Telegram Bot" \
            --vault=beestgraph \
            "credential=$TELEGRAM_TOKEN" \
            "notes=Telegram bot token from @BotFather for beestgraph"
        log "Stored Telegram bot token."
    else
        warn "Skipped Telegram."
    fi
fi

# ── Store Obsidian account ────────────────────────────────────
if op item get "Obsidian" --vault beestgraph &>/dev/null 2>&1; then
    warn "Item 'Obsidian' already exists. Skipping."
else
    echo ""
    read -rp "Obsidian account email (leave empty to skip): " OBS_EMAIL
    if [[ -n "$OBS_EMAIL" ]]; then
        read -rsp "Obsidian password: " OBS_PASS
        echo ""
        op item create \
            --category=login \
            --title="Obsidian" \
            --vault=beestgraph \
            "username=$OBS_EMAIL" \
            "password=$OBS_PASS" \
            "url=https://obsidian.md" \
            "notes=Obsidian account for Sync / CLI access"
        log "Stored Obsidian credentials."
    else
        warn "Skipped Obsidian."
    fi
fi

# ── Summary ───────────────────────────────────────────────────
echo ""
log "Done! Stored items in 'beestgraph' vault:"
op item list --vault beestgraph --format=table 2>/dev/null || true
echo ""
log "To retrieve a secret:"
echo '  op read "op://beestgraph/keep.md/credential"'
echo '  op read "op://beestgraph/Telegram Bot/credential"'
echo '  op read "op://beestgraph/Obsidian/password"'
