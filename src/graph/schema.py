"""Schema management for the beestgraph FalkorDB knowledge graph.

Creates and maintains indexes (range, full-text) and tracks schema versions
with a metadata node. All operations are idempotent.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from falkordb.asyncio import Graph

logger = structlog.get_logger(__name__)

SCHEMA_VERSION = 5

# Range indexes: (label, property)
RANGE_INDEXES: list[tuple[str, str]] = [
    ("Document", "path"),
    ("Document", "uid"),
    ("Document", "source_url"),
    ("Document", "status"),
    ("Document", "para"),
    ("Document", "source_type"),
    ("Document", "type"),
    ("Document", "content_stage"),
    ("Document", "importance"),
    ("Document", "created"),
    ("Document", "captured"),
    ("Document", "modified"),
    ("Document", "expires"),
    ("Tag", "normalized_name"),
    ("Topic", "name"),
    ("Person", "normalized_name"),
    ("Concept", "normalized_name"),
    ("Organization", "normalized_name"),
    ("Tool", "normalized_name"),
    ("Place", "normalized_name"),
    ("Source", "url"),
]

# Full-text indexes: (label, [properties])
FULLTEXT_INDEXES: list[tuple[str, list[str]]] = [
    ("Document", ["title", "summary"]),
    ("Tag", ["name"]),
    ("Concept", ["name", "description"]),
    ("MOC", ["name", "description"]),
    ("Document", ["key_claims"]),
]


def _build_range_index_queries() -> list[str]:
    """Build Cypher statements for all range indexes.

    Returns:
        List of Cypher CREATE INDEX statements.
    """
    return [f"CREATE INDEX FOR (n:{label}) ON (n.{prop})" for label, prop in RANGE_INDEXES]


def _build_fulltext_index_queries() -> list[str]:
    """Build Cypher statements for all full-text indexes.

    Returns:
        List of Cypher CALL statements for full-text index creation.
    """
    return [
        f"CALL db.idx.fulltext.createNodeIndex('{label}', {', '.join(repr(p) for p in props)})"
        for label, props in FULLTEXT_INDEXES
    ]


def _build_schema_version_query(version: int) -> tuple[str, dict[str, object]]:
    """Build a MERGE query for the schema version metadata node.

    Args:
        version: The schema version number to record.

    Returns:
        Tuple of (cypher_string, params_dict).
    """
    query = (
        "MERGE (sv:SchemaVersion {version: $version}) "
        "ON CREATE SET sv.applied_at = $applied_at "
        "ON MATCH SET sv.applied_at = $applied_at"
    )
    params: dict[str, object] = {
        "version": version,
        "applied_at": datetime.now(tz=UTC).isoformat(),
    }
    return query, params


async def ensure_schema(graph: Graph) -> int:
    """Create all indexes and record schema version. Idempotent.

    Applies range indexes, full-text indexes, and upserts the SchemaVersion
    metadata node. Safe to call multiple times -- existing indexes are silently
    skipped by FalkorDB.

    Args:
        graph: An async FalkorDB Graph instance.

    Returns:
        The current schema version number.
    """
    log = logger.bind(graph_name=graph.name)

    # Apply range indexes
    for statement in _build_range_index_queries():
        log.debug("applying_range_index", statement=statement)
        try:
            await graph.query(statement)
        except Exception:
            log.debug("range_index_exists_or_failed", statement=statement)

    # Apply full-text indexes
    for statement in _build_fulltext_index_queries():
        log.debug("applying_fulltext_index", statement=statement)
        try:
            await graph.query(statement)
        except Exception:
            log.debug("fulltext_index_exists_or_failed", statement=statement)

    # Record schema version
    version_query, version_params = _build_schema_version_query(SCHEMA_VERSION)
    await graph.query(version_query, version_params)
    log.info("schema_ensured", version=SCHEMA_VERSION)

    return SCHEMA_VERSION
