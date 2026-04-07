#!/bin/bash
# mesh-daily-report.sh — Daily mesh health check with Telegram report
# Runs mesh-health-check.sh, formats results, sends via Telegram bot API.
# Usage: bash scripts/mesh-daily-report.sh
# Cron:  0 8 * * * bash /home/turbobeest/beestgraph/scripts/mesh-daily-report.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HEALTH_SCRIPT="$HOME/mesh-health-check.sh"

# Load 1Password token for op CLI
export OP_SERVICE_ACCOUNT_TOKEN="$(cat "$HOME/.config/op/service-account-token" 2>/dev/null || true)"

# Get bot token and chat ID from 1Password
BOT_TOKEN="$(op read 'op://AI-BEESTGRAPH/beestgraph-access-keys/Telegram/bot_token' 2>/dev/null || true)"
if [[ -z "$BOT_TOKEN" ]]; then
    echo "ERROR: Could not read Telegram bot token from 1Password" >&2
    exit 1
fi

# Chat ID from config (allowed_users)
CHAT_ID="8397896711"

# Run health check and strip ANSI color codes
REPORT="$(bash "$HEALTH_SCRIPT" 2>&1 | sed 's/\x1b\[[0-9;]*m//g')"

# Count OK and FAIL
OK_COUNT=$(echo "$REPORT" | grep -c "OK:" || true)
FAIL_COUNT=$(echo "$REPORT" | grep -c "FAIL:" || true)

# Build status emoji
if [[ "$FAIL_COUNT" -eq 0 ]]; then
    STATUS_LINE="All systems operational ($OK_COUNT checks passed)"
    EMOJI="✅"
else
    STATUS_LINE="$FAIL_COUNT issue(s) detected ($OK_COUNT/$((OK_COUNT + FAIL_COUNT)) passed)"
    EMOJI="⚠️"
fi

# Get FalkorDB node count
NODE_COUNT=""
if command -v redis-cli &>/dev/null; then
    NODE_COUNT=$(redis-cli -p 6379 GRAPH.QUERY beestgraph "MATCH (n) RETURN count(n)" 2>/dev/null | grep -E "^\d+$" | head -1 || true)
fi

# Build Telegram message (plain text, no markdown)
MESSAGE="$EMOJI Mesh Daily Report — $(date '+%Y-%m-%d %H:%M')

$STATUS_LINE"

if [[ -n "$NODE_COUNT" ]]; then
    MESSAGE="$MESSAGE
Graph: $NODE_COUNT nodes"
fi

# Add failure details if any
if [[ "$FAIL_COUNT" -gt 0 ]]; then
    FAILURES=$(echo "$REPORT" | grep "FAIL:" | sed 's/.*FAIL: /  ❌ /')
    MESSAGE="$MESSAGE

Failures:
$FAILURES"
fi

# Add connectivity summary (compact)
ONLINE=$(echo "$REPORT" | grep "OK:" | grep -oP '(?<=OK: )\S+' | tr '\n' ', ' | sed 's/,$//')
MESSAGE="$MESSAGE

Online: $ONLINE"

# Send via Telegram Bot API
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d chat_id="$CHAT_ID" \
    -d text="$MESSAGE" \
    > /dev/null 2>&1

echo "Report sent to Telegram (OK=$OK_COUNT, FAIL=$FAIL_COUNT)"
