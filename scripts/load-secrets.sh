#!/usr/bin/env bash
# beestgraph/scripts/load-secrets.sh
# Loads secrets from 1Password and exports them as environment variables.
# Used by systemd services and scripts at startup.
#
# Usage:
#   eval $(bash scripts/load-secrets.sh)
#   # or source it:
#   source <(bash scripts/load-secrets.sh)
set -euo pipefail

export OP_SERVICE_ACCOUNT_TOKEN="$(cat "$HOME/.config/op/service-account-token" 2>/dev/null || true)"

if [[ -z "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]]; then
    echo "# WARNING: No 1Password service account token found" >&2
    exit 0
fi

# Telegram bot token
TOKEN="$(op read 'op://AI-BEESTGRAPH/beestgraph-access-keys/Telegram/bot_token' 2>/dev/null || true)"
if [[ -n "$TOKEN" ]]; then
    echo "export BEESTGRAPH_TELEGRAM_BOT_TOKEN='$TOKEN'"
fi

# keep.md API key
KEY="$(op read 'op://AI-BEESTGRAPH/beestgraph-access-keys/Keep/api_key' 2>/dev/null || true)"
if [[ -n "$KEY" ]]; then
    echo "export KEEPMD_API_KEY='$KEY'"
    echo "export BEESTGRAPH_KEEPMD_API_KEY='$KEY'"
fi
