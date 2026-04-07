"""Cypher query builders for the beestgraph knowledge graph.

Each function returns a (cypher_string, params_dict) tuple. Query execution
is handled separately by the caller, keeping query construction pure and testable.

Thinking-tool query builders (``challenge_queries``, ``emerge_queries``, etc.)
return a list of named query tuples: ``[(name, cypher, params), ...]``.
The caller executes each and assembles the typed result dataclass.
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


def get_document_neighborhood(path: str, depth: int = 1) -> tuple[str, dict[str, object]]:
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
        "CALL subgraph.neighbors(d, {}, {maxDepth: $depth}) "
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
    cypher = "MATCH (d:Document) WHERE NOT (d)--() RETURN d ORDER BY d.created_at DESC"
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
    cypher = "MATCH (d:Document) RETURN d ORDER BY d.created_at DESC LIMIT $n"
    return cypher, {"n": n}


def documents_by_source_type(source_type: str) -> tuple[str, dict[str, object]]:
    """Filter documents by their source type.

    Args:
        source_type: One of 'keepmd', 'obsidian_clipper', or 'manual'.

    Returns:
        Tuple of (cypher_string, params_dict).
    """
    cypher = (
        "MATCH (d:Document) WHERE d.source_type = $source_type RETURN d ORDER BY d.created_at DESC"
    )
    return cypher, {"source_type": source_type}


# ---------------------------------------------------------------------------
# Thinking-tool query builders
# ---------------------------------------------------------------------------

NamedQuery = tuple[str, str, dict[str, object]]
"""(query_name, cypher_string, params_dict)."""


def challenge_queries(topic: str) -> list[NamedQuery]:
    """Build queries for ``bg think challenge``.

    Returns three named queries:
    - decisions: documents of type decision/adr/journal related to the topic
    - contradictions: existing CONTRADICTS edges touching the topic
    - reversed: archived/superseded decisions in this topic

    Args:
        topic: Topic string to challenge.
    """
    return [
        (
            "decisions",
            "MATCH (d:Document)-[:BELONGS_TO]->(tp:Topic) "
            "WHERE tp.name CONTAINS $topic "
            "AND d.type IN ['decision', 'adr', 'journal'] "
            "RETURN d.title AS title, d.path AS path, d.uid AS uid, "
            "d.status AS status, d.created AS created, d.confidence AS confidence "
            "ORDER BY d.created DESC",
            {"topic": topic},
        ),
        (
            "contradictions",
            "MATCH (a:Document)-[:CONTRADICTS]->(b:Document), "
            "(a)-[:BELONGS_TO]->(tp:Topic) "
            "WHERE tp.name CONTAINS $topic "
            "RETURN a.title AS from_title, a.path AS from_path, "
            "b.title AS to_title, b.path AS to_path",
            {"topic": topic},
        ),
        (
            "reversed",
            "MATCH (d:Document)-[:BELONGS_TO]->(tp:Topic) "
            "WHERE tp.name CONTAINS $topic "
            "AND (d.status = 'archived' OR (d)-[:SUPERSEDES]->()) "
            "AND d.type IN ['decision', 'adr'] "
            "RETURN d.title AS title, d.path AS path, d.uid AS uid, "
            "d.status AS status, d.created AS created "
            "ORDER BY d.created DESC",
            {"topic": topic},
        ),
    ]


def emerge_queries(period_days: int = 30) -> list[NamedQuery]:
    """Build queries for ``bg think emerge``.

    Returns three named queries:
    - trending_tags: tag frequency in the period, ordered by count
    - entity_clusters: entity pairs co-occurring across documents (>= 3)
    - topic_density: document count per topic

    Args:
        period_days: Number of days to look back.
    """
    return [
        (
            "trending_tags",
            "MATCH (d:Document)-[:TAGGED_WITH]->(t:Tag) "
            "RETURN t.name AS tag, count(d) AS cnt "
            "ORDER BY cnt DESC LIMIT 20",
            {},
        ),
        (
            "entity_clusters",
            "MATCH (d:Document)-[:MENTIONS]->(e1), (d)-[:MENTIONS]->(e2) "
            "WHERE id(e1) < id(e2) "
            "WITH labels(e1)[0] + ':' + e1.name AS a, "
            "labels(e2)[0] + ':' + e2.name AS b, count(d) AS cnt "
            "WHERE cnt >= 3 "
            "RETURN a, b, cnt ORDER BY cnt DESC LIMIT 20",
            {},
        ),
        (
            "topic_density",
            "MATCH (d:Document)-[:BELONGS_TO]->(tp:Topic) "
            "RETURN tp.name AS topic, count(d) AS cnt "
            "ORDER BY cnt DESC",
            {},
        ),
    ]


def connect_queries(a: str, b: str) -> list[NamedQuery]:
    """Build queries for ``bg think connect``.

    Returns three named queries:
    - shortest_path: shortest path between two concepts (max depth 5)
    - shared_nodes: nodes connected to both concepts
    - bridging_docs: documents mentioning both concepts

    Args:
        a: First concept name.
        b: Second concept name.
    """
    return [
        (
            "shortest_path",
            "MATCH (c1 {name: $a}), (c2 {name: $b}), "
            "p = shortestPath((c1)-[*..5]-(c2)) "
            "UNWIND nodes(p) AS n "
            "RETURN DISTINCT coalesce(n.title, n.name, 'unknown') AS node_name",
            {"a": a, "b": b},
        ),
        (
            "shared_nodes",
            "MATCH (c1 {name: $a})--(shared)--(c2 {name: $b}) "
            "WHERE c1 <> c2 AND shared <> c1 AND shared <> c2 "
            "RETURN DISTINCT coalesce(shared.title, shared.name) AS name "
            "LIMIT 20",
            {"a": a, "b": b},
        ),
        (
            "bridging_docs",
            "MATCH (d:Document)-[:MENTIONS]->(c1 {name: $a}), "
            "(d)-[:MENTIONS]->(c2 {name: $b}) "
            "WHERE c1 <> c2 "
            "RETURN d.title AS title, d.path AS path, d.uid AS uid "
            "ORDER BY d.created DESC",
            {"a": a, "b": b},
        ),
    ]


def graduate_queries(idea_slug: str) -> list[NamedQuery]:
    """Build queries for ``bg think graduate``.

    Returns three named queries:
    - source_doc: find the document by slug, uid, or path substring
    - related_docs: documents sharing tags or topics with the source
    - nearby_projects: project-type documents sharing entities

    Args:
        idea_slug: Document slug, uid, or partial path.
    """
    return [
        (
            "source_doc",
            "MATCH (d:Document) "
            "WHERE d.uid = $slug OR d.path CONTAINS $slug OR d.title CONTAINS $slug "
            "RETURN d.title AS title, d.path AS path, d.uid AS uid, "
            "d.status AS status, d.created AS created "
            "LIMIT 1",
            {"slug": idea_slug},
        ),
        (
            "related_docs",
            "MATCH (src:Document)-[:TAGGED_WITH]->(t:Tag)<-[:TAGGED_WITH]-(rel:Document) "
            "WHERE (src.uid = $slug OR src.path CONTAINS $slug "
            "OR src.title CONTAINS $slug) AND src <> rel "
            "RETURN DISTINCT rel.title AS title, rel.path AS path, rel.uid AS uid, "
            "count(t) AS shared_tags "
            "ORDER BY shared_tags DESC LIMIT 10",
            {"slug": idea_slug},
        ),
        (
            "nearby_projects",
            "MATCH (src:Document)-[:MENTIONS]->(e)<-[:MENTIONS]-(proj:Document) "
            "WHERE (src.uid = $slug OR src.path CONTAINS $slug "
            "OR src.title CONTAINS $slug) "
            "AND proj.type IN ['project', 'moc'] AND src <> proj "
            "RETURN DISTINCT proj.title AS title, proj.path AS path, proj.uid AS uid "
            "LIMIT 10",
            {"slug": idea_slug},
        ),
    ]


def forecast_queries(topic: str) -> list[NamedQuery]:
    """Build queries for ``bg think forecast``.

    Returns two named queries:
    - monthly_counts: documents per month for this topic (last 12 months)
    - related_trends: mention counts for related concepts

    Args:
        topic: Topic to forecast.
    """
    return [
        (
            "monthly_counts",
            "MATCH (d:Document)-[:BELONGS_TO]->(tp:Topic) "
            "WHERE tp.name CONTAINS $topic AND d.created IS NOT NULL "
            "RETURN substring(d.created, 0, 7) AS month, count(d) AS cnt "
            "ORDER BY month ASC",
            {"topic": topic},
        ),
        (
            "related_trends",
            "MATCH (d:Document)-[:BELONGS_TO]->(tp:Topic), "
            "(d)-[:MENTIONS]->(e) "
            "WHERE tp.name CONTAINS $topic AND d.created IS NOT NULL "
            "RETURN coalesce(e.name, 'unknown') AS entity, "
            "substring(d.created, 0, 7) AS month, count(d) AS cnt "
            "ORDER BY entity, month",
            {"topic": topic},
        ),
    ]


def audit_queries(claim: str) -> list[NamedQuery]:
    """Build queries for ``bg think audit``.

    Returns three named queries:
    - matching: full-text search on key_claims for the claim text
    - supporting: documents with SUPPORTS edges from matches
    - contradicting: documents with CONTRADICTS edges from matches

    Args:
        claim: The claim text to audit.
    """
    return [
        (
            "matching",
            "CALL db.idx.fulltext.queryNodes('Document', $claim) "
            "YIELD node, score "
            "RETURN node.title AS title, node.path AS path, node.uid AS uid, "
            "node.created AS created, node.confidence AS confidence, "
            "node.key_claims AS key_claims, score "
            "ORDER BY score DESC LIMIT 20",
            {"claim": claim},
        ),
        (
            "supporting",
            "CALL db.idx.fulltext.queryNodes('Document', $claim) "
            "YIELD node "
            "MATCH (node)-[:SUPPORTS]->(s:Document) "
            "RETURN s.title AS title, s.path AS path, s.uid AS uid, "
            "s.created AS created, s.confidence AS confidence",
            {"claim": claim},
        ),
        (
            "contradicting",
            "CALL db.idx.fulltext.queryNodes('Document', $claim) "
            "YIELD node "
            "MATCH (node)-[:CONTRADICTS]->(c:Document) "
            "RETURN c.title AS title, c.path AS path, c.uid AS uid, "
            "c.created AS created, c.confidence AS confidence",
            {"claim": claim},
        ),
    ]
