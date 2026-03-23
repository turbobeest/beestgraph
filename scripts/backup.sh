#!/usr/bin/env bash
# beestgraph/scripts/backup.sh — Snapshot FalkorDB + rsync vault to backup directory
# Keeps last 7 daily backups with automatic rotation.
#
# Usage:
#   ./scripts/backup.sh                    # Uses defaults
#   BACKUP_DIR=/mnt/usb/backups ./scripts/backup.sh
set -euo pipefail

# ── Color log helpers ────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[backup]${NC} $*"; }
warn() { echo -e "${YELLOW}[backup]${NC} $*"; }
err()  { echo -e "${RED}[backup]${NC} $*" >&2; }

# ── Configuration ────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT_PATH="${VAULT_PATH:-$HOME/vault}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/beestgraph}"
BACKUP_RETENTION="${BACKUP_RETENTION:-7}"
FALKORDB_CONTAINER="${FALKORDB_CONTAINER:-beestgraph-falkordb}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
CURRENT_BACKUP="${BACKUP_DIR}/${TIMESTAMP}"

# ── Pre-flight checks ───────────────────────────────────────
if [[ ! -d "$VAULT_PATH" ]]; then
    err "Vault directory not found: ${VAULT_PATH}"
    err "Set VAULT_PATH to your Obsidian vault location."
    exit 1
fi

mkdir -p "${CURRENT_BACKUP}/falkordb" "${CURRENT_BACKUP}/vault"

log "Starting backup: ${TIMESTAMP}"
log "  Vault:   ${VAULT_PATH}"
log "  Dest:    ${CURRENT_BACKUP}"
log "  Retain:  ${BACKUP_RETENTION} backups"

# ── 1. FalkorDB RDB snapshot ────────────────────────────────
log "Triggering FalkorDB RDB snapshot..."

if docker exec "$FALKORDB_CONTAINER" redis-cli BGSAVE &>/dev/null; then
    # Wait for background save to complete (max 60 seconds)
    for i in $(seq 1 60); do
        if docker exec "$FALKORDB_CONTAINER" redis-cli LASTSAVE 2>/dev/null | grep -q "^[0-9]"; then
            SAVE_IN_PROGRESS=$(docker exec "$FALKORDB_CONTAINER" redis-cli INFO persistence 2>/dev/null | grep "rdb_bgsave_in_progress:1" || true)
            if [[ -z "$SAVE_IN_PROGRESS" ]]; then
                break
            fi
        fi
        sleep 1
    done

    # Copy the RDB file from the container
    if docker cp "${FALKORDB_CONTAINER}:/data/dump.rdb" "${CURRENT_BACKUP}/falkordb/dump.rdb" 2>/dev/null; then
        RDB_SIZE=$(du -sh "${CURRENT_BACKUP}/falkordb/dump.rdb" | cut -f1)
        log "FalkorDB snapshot saved (${RDB_SIZE})"
    else
        warn "Could not copy RDB file. FalkorDB data may use a different path."
    fi

    # Also copy appendonly file if it exists
    docker cp "${FALKORDB_CONTAINER}:/data/appendonly.aof" "${CURRENT_BACKUP}/falkordb/appendonly.aof" 2>/dev/null || true
else
    warn "FalkorDB container '${FALKORDB_CONTAINER}' not reachable. Skipping database backup."
    warn "Is the container running? Try: docker compose -f docker/docker-compose.yml up -d"
fi

# ── 2. Vault rsync ──────────────────────────────────────────
log "Syncing vault to backup..."
rsync -a --delete \
    --exclude='.obsidian/workspace*.json' \
    --exclude='.trash/' \
    "${VAULT_PATH}/" "${CURRENT_BACKUP}/vault/"

VAULT_SIZE=$(du -sh "${CURRENT_BACKUP}/vault" | cut -f1)
log "Vault backup complete (${VAULT_SIZE})"

# ── 3. Config backup ────────────────────────────────────────
if [[ -d "${PROJECT_DIR}/config" ]]; then
    log "Backing up config files..."
    mkdir -p "${CURRENT_BACKUP}/config"
    rsync -a \
        --exclude='*.example' \
        "${PROJECT_DIR}/config/" "${CURRENT_BACKUP}/config/" 2>/dev/null || true
fi

# ── 4. Rotate old backups ───────────────────────────────────
log "Rotating backups (keeping last ${BACKUP_RETENTION})..."
BACKUP_COUNT=0
# List backup dirs sorted oldest-first, skip the most recent $BACKUP_RETENTION
while IFS= read -r old_backup; do
    if [[ -d "$old_backup" ]]; then
        rm -rf "$old_backup"
        BACKUP_COUNT=$((BACKUP_COUNT + 1))
        log "  Removed: $(basename "$old_backup")"
    fi
done < <(
    find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d \
        | sort \
        | head -n -"${BACKUP_RETENTION}"
)

if (( BACKUP_COUNT > 0 )); then
    log "Removed ${BACKUP_COUNT} old backup(s)"
fi

# ── Summary ──────────────────────────────────────────────────
TOTAL_SIZE=$(du -sh "${CURRENT_BACKUP}" | cut -f1)
REMAINING=$(find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)

echo ""
log "Backup complete!"
echo "  Location:   ${CURRENT_BACKUP}"
echo "  Total size: ${TOTAL_SIZE}"
echo "  Backups:    ${REMAINING} of ${BACKUP_RETENTION} max"
echo ""
