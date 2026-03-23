"""Tests for src/graph/queries.py — Cypher query builder functions."""

from __future__ import annotations

from src.graph.queries import (
    documents_by_source_type,
    find_orphans,
    find_related_by_tags,
    get_document_neighborhood,
    recent_documents,
    search_documents,
    topic_tree,
)


class TestSearchDocuments:
    """Tests for search_documents."""

    def test_returns_fulltext_query(self) -> None:
        cypher, params = search_documents("knowledge graph")
        assert "db.idx.fulltext.queryNodes" in cypher
        assert params["query"] == "knowledge graph"

    def test_default_limit(self) -> None:
        _, params = search_documents("test")
        assert params["limit"] == 20

    def test_custom_limit(self) -> None:
        _, params = search_documents("test", limit=5)
        assert params["limit"] == 5

    def test_orders_by_score(self) -> None:
        cypher, _ = search_documents("test")
        assert "ORDER BY score DESC" in cypher


class TestGetDocumentNeighborhood:
    """Tests for get_document_neighborhood."""

    def test_matches_by_path(self) -> None:
        cypher, params = get_document_neighborhood("knowledge/tech/article.md")
        assert "Document {path: $path}" in cypher
        assert params["path"] == "knowledge/tech/article.md"

    def test_default_depth(self) -> None:
        _, params = get_document_neighborhood("test.md")
        assert params["depth"] == 1

    def test_custom_depth(self) -> None:
        _, params = get_document_neighborhood("test.md", depth=3)
        assert params["depth"] == 3

    def test_returns_nodes_and_edges(self) -> None:
        cypher, _ = get_document_neighborhood("test.md")
        assert "nodes" in cypher
        assert "edges" in cypher


class TestFindRelatedByTags:
    """Tests for find_related_by_tags."""

    def test_uses_tag_list_param(self) -> None:
        tags = ["python", "ai-ml"]
        cypher, params = find_related_by_tags(tags)
        assert params["tags"] == tags

    def test_matches_tagged_with_relationship(self) -> None:
        cypher, _ = find_related_by_tags(["test"])
        assert "TAGGED_WITH" in cypher

    def test_orders_by_overlap(self) -> None:
        cypher, _ = find_related_by_tags(["a", "b"])
        assert "ORDER BY tag_overlap DESC" in cypher


class TestFindOrphans:
    """Tests for find_orphans."""

    def test_returns_empty_params(self) -> None:
        _, params = find_orphans()
        assert params == {}

    def test_checks_no_relationships(self) -> None:
        cypher, _ = find_orphans()
        assert "NOT (d)--()" in cypher

    def test_returns_documents(self) -> None:
        cypher, _ = find_orphans()
        assert "RETURN d" in cypher


class TestTopicTree:
    """Tests for topic_tree."""

    def test_returns_empty_params(self) -> None:
        _, params = topic_tree()
        assert params == {}

    def test_includes_subtopic_of(self) -> None:
        cypher, _ = topic_tree()
        assert "SUBTOPIC_OF" in cypher

    def test_returns_hierarchy_fields(self) -> None:
        cypher, _ = topic_tree()
        assert "topic" in cypher
        assert "level" in cypher
        assert "parent_topic" in cypher

    def test_orders_by_level(self) -> None:
        cypher, _ = topic_tree()
        assert "ORDER BY t.level ASC" in cypher


class TestRecentDocuments:
    """Tests for recent_documents."""

    def test_default_n(self) -> None:
        _, params = recent_documents()
        assert params["n"] == 10

    def test_custom_n(self) -> None:
        _, params = recent_documents(n=50)
        assert params["n"] == 50

    def test_orders_by_created_at_desc(self) -> None:
        cypher, _ = recent_documents()
        assert "ORDER BY d.created_at DESC" in cypher


class TestDocumentsBySourceType:
    """Tests for documents_by_source_type."""

    def test_passes_source_type_param(self) -> None:
        _, params = documents_by_source_type("keepmd")
        assert params["source_type"] == "keepmd"

    def test_filters_by_source_type(self) -> None:
        cypher, _ = documents_by_source_type("manual")
        assert "d.source_type = $source_type" in cypher

    def test_returns_documents(self) -> None:
        cypher, _ = documents_by_source_type("obsidian_clipper")
        assert "RETURN d" in cypher
