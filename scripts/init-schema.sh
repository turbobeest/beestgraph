#!/usr/bin/env bash
# beestgraph/scripts/init-schema.sh — Create FalkorDB indexes and constraints
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[beestgraph]${NC} $*"; }
err() { echo -e "${RED}[beestgraph]${NC} $*" >&2; }

FALKORDB_HOST="${FALKORDB_HOST:-localhost}"
FALKORDB_PORT="${FALKORDB_PORT:-6379}"

log "Initializing beestgraph schema on FalkorDB at ${FALKORDB_HOST}:${FALKORDB_PORT}..."

# Check FalkorDB is reachable
if ! redis-cli -h "$FALKORDB_HOST" -p "$FALKORDB_PORT" ping &>/dev/null; then
    # Try with docker
    if docker exec beestgraph-falkordb redis-cli ping &>/dev/null; then
        REDIS_CMD="docker exec beestgraph-falkordb redis-cli"
    else
        err "Cannot reach FalkorDB. Is it running?"
        err "  Try: cd docker && docker compose up -d"
        exit 1
    fi
else
    REDIS_CMD="redis-cli -h $FALKORDB_HOST -p $FALKORDB_PORT"
fi

run_cypher() {
    local query="$1"
    $REDIS_CMD GRAPH.QUERY beestgraph "$query" 2>/dev/null
}

# ── Range indexes ────────────────────────────────────────────
log "Creating range indexes..."
run_cypher "CREATE INDEX FOR (d:Document) ON (d.path)"
run_cypher "CREATE INDEX FOR (d:Document) ON (d.source_url)"
run_cypher "CREATE INDEX FOR (d:Document) ON (d.status)"
run_cypher "CREATE INDEX FOR (d:Document) ON (d.para_category)"
run_cypher "CREATE INDEX FOR (d:Document) ON (d.source_type)"
run_cypher "CREATE INDEX FOR (t:Tag) ON (t.normalized_name)"
run_cypher "CREATE INDEX FOR (tp:Topic) ON (tp.name)"
run_cypher "CREATE INDEX FOR (p:Person) ON (p.normalized_name)"
run_cypher "CREATE INDEX FOR (c:Concept) ON (c.normalized_name)"
run_cypher "CREATE INDEX FOR (s:Source) ON (s.url)"
run_cypher "CREATE INDEX FOR (pr:Project) ON (pr.name)"

# ── Full-text indexes ────────────────────────────────────────
log "Creating full-text search indexes..."
run_cypher "CALL db.idx.fulltext.createNodeIndex('Document', 'title', 'content', 'summary')"
run_cypher "CALL db.idx.fulltext.createNodeIndex('Tag', 'name')"
run_cypher "CALL db.idx.fulltext.createNodeIndex('Concept', 'name', 'description')"

# ── Seed the starter taxonomy as Topic nodes ─────────────────
log "Seeding starter taxonomy..."
TOPICS=(
    "technology,0"
    "technology/programming,1"
    "technology/ai-ml,1"
    "technology/infrastructure,1"
    "technology/security,1"
    "technology/web,1"
    "science,0"
    "science/physics,1"
    "science/biology,1"
    "science/mathematics,1"
    "business,0"
    "business/startups,1"
    "business/finance,1"
    "business/marketing,1"
    "culture,0"
    "culture/books,1"
    "culture/film,1"
    "culture/music,1"
    "culture/history,1"
    "health,0"
    "health/fitness,1"
    "health/nutrition,1"
    "health/mental-health,1"
    "personal,0"
    "personal/journal,1"
    "personal/goals,1"
    "personal/relationships,1"
    "meta,0"
    "meta/pkm,1"
    "meta/tools,1"
    "meta/workflows,1"
)

for entry in "${TOPICS[@]}"; do
    IFS=',' read -r name level <<< "$entry"
    run_cypher "MERGE (t:Topic {name: '${name}', level: ${level}})"

    # Create SUBTOPIC_OF edges for level > 0
    if (( level > 0 )); then
        parent="${name%/*}"
        run_cypher "MATCH (child:Topic {name: '${name}'}), (parent:Topic {name: '${parent}'}) MERGE (child)-[:SUBTOPIC_OF]->(parent)"
    fi
done

# ── Verify ───────────────────────────────────────────────────
log "Verifying schema..."
TOPIC_COUNT=$($REDIS_CMD GRAPH.QUERY beestgraph "MATCH (t:Topic) RETURN count(t)" 2>/dev/null | grep -oP '\d+' | head -1)
log "Topics created: ${TOPIC_COUNT:-unknown}"

echo ""
log "Schema initialization complete!"
echo ""
echo "  View in FalkorDB Browser: http://localhost:3000"
echo "  Test query: MATCH (t:Topic)-[:SUBTOPIC_OF]->(p:Topic) RETURN t.name, p.name"
echo ""
