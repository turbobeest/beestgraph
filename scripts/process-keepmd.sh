#!/usr/bin/env bash
# beestgraph/scripts/process-keepmd.sh — Cron wrapper for keep.md inbox processing
# Runs the keep.md poller via Claude Code headless agent.
# Uses a lockfile to prevent overlapping runs.
#
# Cron example (every 15 minutes):
#   */15 * * * * $HOME/beestgraph/scripts/process-keepmd.sh >> /var/log/beestgraph/keepmd.log 2>&1
set -euo pipefail

# ── Color log helpers ────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[keepmd]${NC} $(date '+%Y-%m-%d %H:%M:%S') $*"; }
warn() { echo -e "${YELLOW}[keepmd]${NC} $(date '+%Y-%m-%d %H:%M:%S') $*"; }
err()  { echo -e "${RED}[keepmd]${NC} $(date '+%Y-%m-%d %H:%M:%S') $*" >&2; }

# ── Configuration ────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCKFILE="/tmp/beestgraph-keepmd.lock"
LOCK_TIMEOUT="${LOCK_TIMEOUT:-900}"  # 15 minutes, matches cron interval

# ── Source environment ───────────────────────────────────────
if [[ -f "${PROJECT_DIR}/docker/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "${PROJECT_DIR}/docker/.env"
    set +a
fi

if [[ -f "${PROJECT_DIR}/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "${PROJECT_DIR}/.env"
    set +a
fi

# ── Lockfile management ─────────────────────────────────────
acquire_lock() {
    if [[ -f "$LOCKFILE" ]]; then
        LOCK_PID=$(cat "$LOCKFILE" 2>/dev/null || echo "")

        # Check if the lock-holding process is still running
        if [[ -n "$LOCK_PID" ]] && kill -0 "$LOCK_PID" 2>/dev/null; then
            # Check if the lock is stale (older than LOCK_TIMEOUT seconds)
            LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCKFILE" 2>/dev/null || echo 0) ))
            if (( LOCK_AGE > LOCK_TIMEOUT )); then
                warn "Stale lock detected (PID ${LOCK_PID}, age ${LOCK_AGE}s). Removing."
                rm -f "$LOCKFILE"
            else
                warn "Another instance is running (PID ${LOCK_PID}, age ${LOCK_AGE}s). Exiting."
                exit 0
            fi
        else
            # PID no longer running — stale lock
            warn "Removing stale lockfile (PID ${LOCK_PID} not running)."
            rm -f "$LOCKFILE"
        fi
    fi

    echo $$ > "$LOCKFILE"
}

release_lock() {
    rm -f "$LOCKFILE"
}

# Clean up lockfile on exit (normal or error)
trap release_lock EXIT

# ── Acquire lock ─────────────────────────────────────────────
acquire_lock

# ── Load secrets from 1Password ────────────────────────────────
if [[ -f "${PROJECT_DIR}/scripts/load-secrets.sh" ]]; then
    source <(bash "${PROJECT_DIR}/scripts/load-secrets.sh")
fi

# ── Run poller ───────────────────────────────────────────────
log "Starting keep.md inbox processing..."
START_TIME=$(date +%s)

cd "$PROJECT_DIR"
uv run python -m src.pipeline.keepmd_poller

END_TIME=$(date +%s)
DURATION=$(( END_TIME - START_TIME ))
log "Processing complete in ${DURATION}s"
