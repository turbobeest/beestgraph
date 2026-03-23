"""Maintenance operations for the beestgraph knowledge graph.

Provides deduplication, orphan detection, and graph statistics. All write
operations use MERGE to remain idempotent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from falkordb.asyncio import Graph

logger = structlog.get_logger(__name__)


async def deduplicate_tags(graph: Graph) -> int:
    """Merge Tag nodes sharing the same normalized_name.

    Keeps the first node and transfers all incoming relationships from
    duplicates before deleting them.

    Args:
        graph: An async FalkorDB Graph instance.

    Returns:
        Number of duplicate nodes deleted.
    """
    cypher = (
        "MATCH (t:Tag) "
        "WITH t.normalized_name AS norm, COLLECT(t) AS nodes "
        "WHERE SIZE(nodes) > 1 "
        "WITH norm, HEAD(nodes) AS keeper, TAIL(nodes) AS duplicates "
        "UNWIND duplicates AS dup "
        "OPTIONAL MATCH (src)-[r:TAGGED_WITH]->(dup) "
        "WITH keeper, dup, COLLECT(src) AS sources "
        "FOREACH (s IN sources | MERGE (s)-[:TAGGED_WITH]->(keeper)) "
        "DETACH DELETE dup "
        "RETURN COUNT(dup) AS deleted_count"
    )
    result = await graph.query(cypher)
    deleted = result.result_set[0][0] if result.result_set else 0
    logger.info("deduplicate_tags_complete", deleted=deleted)
    return deleted


async def deduplicate_entities(graph: Graph) -> dict[str, int]:
    """Merge Person and Concept nodes sharing the same normalized_name.

    Args:
        graph: An async FalkorDB Graph instance.

    Returns:
        Dict mapping label to number of duplicates deleted.
    """
    results: dict[str, int] = {}
    for label in ("Person", "Concept"):
        cypher = (
            f"MATCH (n:{label}) "
            "WITH n.normalized_name AS norm, COLLECT(n) AS nodes "
            "WHERE SIZE(nodes) > 1 "
            "WITH norm, HEAD(nodes) AS keeper, TAIL(nodes) AS duplicates "
            "UNWIND duplicates AS dup "
            "OPTIONAL MATCH (src)-[r:MENTIONS]->(dup) "
            "WITH keeper, dup, COLLECT(src) AS sources "
            "FOREACH (s IN sources | MERGE (s)-[:MENTIONS]->(keeper)) "
            "DETACH DELETE dup "
            "RETURN COUNT(dup) AS deleted_count"
        )
        result = await graph.query(cypher)
        deleted = result.result_set[0][0] if result.result_set else 0
        results[label] = deleted
        logger.info("deduplicate_entities_complete", label=label, deleted=deleted)
    return results


def find_orphan_documents() -> tuple[str, dict[str, object]]:
    """Build a query to find documents with zero edges.

    Returns:
        Tuple of (cypher_string, params_dict) with empty params.
    """
    cypher = (
        "MATCH (d:Document) "
        "WHERE NOT (d)--() "
        "RETURN d.path AS path, d.title AS title, d.created_at AS created_at "
        "ORDER BY d.created_at DESC"
    )
    return cypher, {}


async def compute_stats(graph: Graph) -> dict[str, object]:
    """Compute graph statistics: node counts, edge counts, most connected docs.

    Args:
        graph: An async FalkorDB Graph instance.

    Returns:
        Dict with keys 'node_counts', 'edge_counts', 'most_connected'.
    """
    # Node counts by label
    node_labels = ["Document", "Tag", "Topic", "Person", "Concept", "Source", "Project"]
    node_counts: dict[str, int] = {}
    for label in node_labels:
        result = await graph.query(f"MATCH (n:{label}) RETURN COUNT(n)")
        node_counts[label] = result.result_set[0][0] if result.result_set else 0

    # Edge counts by type
    edge_types = [
        "LINKS_TO",
        "TAGGED_WITH",
        "BELONGS_TO",
        "MENTIONS",
        "DERIVED_FROM",
        "SUBTOPIC_OF",
        "SUPPORTS",
        "CONTRADICTS",
        "SUPERSEDES",
    ]
    edge_counts: dict[str, int] = {}
    for etype in edge_types:
        result = await graph.query(f"MATCH ()-[r:{etype}]->() RETURN COUNT(r)")
        edge_counts[etype] = result.result_set[0][0] if result.result_set else 0

    # Most connected documents (top 10)
    result = await graph.query(
        "MATCH (d:Document)-[r]-() "
        "RETURN d.path AS path, d.title AS title, COUNT(r) AS degree "
        "ORDER BY degree DESC LIMIT 10"
    )
    most_connected = [
        {"path": row[0], "title": row[1], "degree": row[2]} for row in result.result_set
    ]

    stats: dict[str, object] = {
        "node_counts": node_counts,
        "edge_counts": edge_counts,
        "most_connected": most_connected,
    }
    logger.info("compute_stats_complete", stats=stats)
    return stats


def find_hub_documents(top_n: int = 10) -> tuple[str, dict[str, object]]:
    """Build a query for highest degree-centrality documents.

    Args:
        top_n: Number of top hub documents to return.

    Returns:
        Tuple of (cypher_string, params_dict).
    """
    cypher = (
        "MATCH (d:Document)-[r]-() "
        "RETURN d.path AS path, d.title AS title, COUNT(r) AS degree "
        "ORDER BY degree DESC "
        "LIMIT $top_n"
    )
    return cypher, {"top_n": top_n}
