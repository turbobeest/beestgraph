#!/bin/bash
# beestgraph/scripts/maintenance-cron.sh — Run graph maintenance tasks
# Scheduled: 0 2 * * * (daily at 2am)
set -euo pipefail

cd /home/turbobeest/beestgraph

LOG_DIR="/var/log/beestgraph"
mkdir -p "$LOG_DIR"

echo "$(date -Iseconds) Starting graph maintenance" >> "$LOG_DIR/maintenance.log"

/home/turbobeest/.local/bin/uv run python -c "
import asyncio
from falkordb import FalkorDB
from src.graph.maintenance import deduplicate_tags, deduplicate_entities, compute_stats

async def main():
    from falkordb.asyncio import FalkorDB as AsyncFalkorDB
    db = AsyncFalkorDB(host='localhost', port=6379)
    graph = db.select_graph('beestgraph')
    deleted_tags = await deduplicate_tags(graph)
    deleted_people, deleted_concepts = await deduplicate_entities(graph)
    stats = await compute_stats(graph)
    print(f'Tags deduplicated: {deleted_tags}')
    print(f'Entities deduplicated: people={deleted_people}, concepts={deleted_concepts}')
    for k, v in stats.items():
        print(f'  {k}: {v}')

asyncio.run(main())
" 2>&1 | tee -a "$LOG_DIR/maintenance.log"

echo "$(date -Iseconds) Maintenance complete" >> "$LOG_DIR/maintenance.log"
