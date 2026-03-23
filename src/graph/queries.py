"""Cypher query builders for the beestgraph knowledge graph.

Each function returns a (cypher_string, params_dict) tuple. Query execution
is handled separately by the caller, keeping query construction pure and testable.
"""

from __future__ import annotations


def search_documents(query: str, limit: int = 20) -> tuple[str, dict[str, object]]:
    """Full-text search across Document title, content, and summary.

    Args:
        query: The search text to match against the full-text index.
        limit: Maximum number of results to return.

    Returns:
        Tuple of (cypher_string, params_dict).
    """
    cypher = (
        "CALL db.idx.fulltext.queryNodes('Document', $query) "
        "YIELD node, score "
        "RETURN node, score "
        "ORDER BY score DESC "
        "LIMIT $limit"
    )
    return cypher, {"query": query, "limit": limit}


def get_document_neighborhood(
    path: str, depth: int = 1
) -> tuple[str, dict[str, object]]:
    """Retrieve the subgraph around a document up to a given depth.

    Follows all relationship types outward from the document matched by path.

    Args:
        path: The vault-relative path of the document.
        depth: How many hops to traverse (1-3 recommended).

    Returns:
        Tuple of (cypher_string, params_dict).
    """
    cypher = (
        "MATCH (d:Document {path: $path}) "
        f"CALL subgraph.neighbors(d, {{}}, {{maxDepth: $depth}}) "
        "YIELD nodes, edges "
        "RETURN nodes, edges"
    )
    return cypher, {"path": path, "depth": depth}


def find_related_by_tags(tags: list[str]) -> tuple[str, dict[str, object]]:
    """Find documents sharing any of the given tags.

    Args:
        tags: List of normalized tag names to match.

    Returns:
        Tuple of (cypher_string, params_dict).
    """
    cypher = (
        "MATCH (d:Document)-[:TAGGED_WITH]->(t:Tag) "
        "WHERE t.normalized_name IN $tags "
        "RETURN d, COLLECT(DISTINCT t.normalized_name) AS matched_tags, "
        "COUNT(DISTINCT t) AS tag_overlap "
        "ORDER BY tag_overlap DESC"
    )
    return cypher, {"tags": tags}


def find_orphans() -> tuple[str, dict[str, object]]:
    """Find documents with no relationships of any kind.

    Returns:
        Tuple of (cypher_string, params_dict) with empty params.
    """
    cypher = (
        "MATCH (d:Document) "
        "WHERE NOT (d)--() "
        "RETURN d "
        "ORDER BY d.created_at DESC"
    )
    return cypher, {}


def topic_tree() -> tuple[str, dict[str, object]]:
    """Retrieve the hierarchical topic structure.

    Returns topics with their parent relationships, ordered by level
    for tree reconstruction.

    Returns:
        Tuple of (cypher_string, params_dict) with empty params.
    """
    cypher = (
        "MATCH (t:Topic) "
        "OPTIONAL MATCH (t)-[:SUBTOPIC_OF]->(parent:Topic) "
        "RETURN t.name AS topic, t.level AS level, "
        "parent.name AS parent_topic "
        "ORDER BY t.level ASC, t.name ASC"
    )
    return cypher, {}


def recent_documents(n: int = 10) -> tuple[str, dict[str, object]]:
    """Retrieve the most recently created documents.

    Args:
        n: Number of documents to return.

    Returns:
        Tuple of (cypher_string, params_dict).
    """
    cypher = (
        "MATCH (d:Document) "
        "RETURN d "
        "ORDER BY d.created_at DESC "
        "LIMIT $n"
    )
    return cypher, {"n": n}


def documents_by_source_type(source_type: str) -> tuple[str, dict[str, object]]:
    """Filter documents by their source type.

    Args:
        source_type: One of 'keepmd', 'obsidian_clipper', or 'manual'.

    Returns:
        Tuple of (cypher_string, params_dict).
    """
    cypher = (
        "MATCH (d:Document) "
        "WHERE d.source_type = $source_type "
        "RETURN d "
        "ORDER BY d.created_at DESC"
    )
    return cypher, {"source_type": source_type}
