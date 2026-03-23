"""Tests for src.pipeline.ingester — FalkorDB graph upsert operations."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.config import FalkorDBSettings
from src.pipeline.ingester import GraphIngester
from src.pipeline.markdown_parser import ParsedDocument


@pytest.fixture
def ingester(mock_falkordb_settings: FalkorDBSettings, mock_graph: MagicMock) -> GraphIngester:
    """Create a GraphIngester with a mocked FalkorDB backend."""
    ing = GraphIngester(mock_falkordb_settings)
    # Patch _graph to return our mock
    ing._graph = MagicMock(return_value=mock_graph)  # type: ignore[method-assign]
    return ing


class TestUpsertDocument:
    """Tests for GraphIngester.upsert_document."""

    def test_calls_merge_with_correct_path(
        self, ingester: GraphIngester, sample_parsed_doc: ParsedDocument, mock_graph: MagicMock
    ) -> None:
        result = ingester.upsert_document(sample_parsed_doc)
        assert result == "inbox/kg-article.md"
        mock_graph.query.assert_called_once()

    def test_params_include_title_and_content(
        self, ingester: GraphIngester, sample_parsed_doc: ParsedDocument, mock_graph: MagicMock
    ) -> None:
        ingester.upsert_document(sample_parsed_doc)
        call_args = mock_graph.query.call_args
        params = call_args[0][1]  # Second positional arg is the params dict
        assert params["title"] == "Knowledge Graphs for Fun and Profit"
        assert params["path"] == "inbox/kg-article.md"

    def test_merge_query_used(
        self, ingester: GraphIngester, sample_parsed_doc: ParsedDocument, mock_graph: MagicMock
    ) -> None:
        ingester.upsert_document(sample_parsed_doc)
        query = mock_graph.query.call_args[0][0]
        assert "MERGE" in query

    def test_status_defaults_to_inbox(self, ingester: GraphIngester, mock_graph: MagicMock) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="Body",
            metadata={},
        )
        ingester.upsert_document(doc)
        params = mock_graph.query.call_args[0][1]
        assert params["status"] == "inbox"


class TestUpsertTag:
    """Tests for GraphIngester.upsert_tag."""

    def test_normalizes_tag_name(self, ingester: GraphIngester, mock_graph: MagicMock) -> None:
        result = ingester.upsert_tag("  My-Tag  ")
        assert result == "my-tag"

    def test_calls_merge_query(self, ingester: GraphIngester, mock_graph: MagicMock) -> None:
        ingester.upsert_tag("python")
        query = mock_graph.query.call_args[0][0]
        assert "MERGE" in query
        params = mock_graph.query.call_args[0][1]
        assert params["normalized_name"] == "python"
        assert params["name"] == "python"


class TestUpsertTopic:
    """Tests for GraphIngester.upsert_topic."""

    def test_includes_level(self, ingester: GraphIngester, mock_graph: MagicMock) -> None:
        result = ingester.upsert_topic("technology/ai-ml", level=1)
        assert result == "technology/ai-ml"
        params = mock_graph.query.call_args[0][1]
        assert params["level"] == 1
        assert params["name"] == "technology/ai-ml"

    def test_default_level_zero(self, ingester: GraphIngester, mock_graph: MagicMock) -> None:
        ingester.upsert_topic("science")
        params = mock_graph.query.call_args[0][1]
        assert params["level"] == 0


class TestCreateLink:
    """Tests for GraphIngester.create_link."""

    def test_creates_links_to_edge(self, ingester: GraphIngester, mock_graph: MagicMock) -> None:
        ingester.create_link("a.md", "b.md")
        mock_graph.query.assert_called_once()
        query = mock_graph.query.call_args[0][0]
        assert "LINKS_TO" in query
        params = mock_graph.query.call_args[0][1]
        assert params["from_path"] == "a.md"
        assert params["to_path"] == "b.md"


class TestCreateMention:
    """Tests for GraphIngester.create_mention."""

    def test_person_type(self, ingester: GraphIngester, mock_graph: MagicMock) -> None:
        ingester.create_mention("doc.md", "Jane Doe", "person", confidence=0.9, context="author")
        # Should call twice: once for MERGE Person, once for MERGE MENTIONS
        assert mock_graph.query.call_count == 2

    def test_concept_type(self, ingester: GraphIngester, mock_graph: MagicMock) -> None:
        ingester.create_mention("doc.md", "Knowledge Graph", "concept")
        assert mock_graph.query.call_count == 2

    def test_invalid_type_raises(self, ingester: GraphIngester, mock_graph: MagicMock) -> None:
        with pytest.raises(ValueError, match="entity_type must be"):
            ingester.create_mention("doc.md", "Foo", "unknown")

    def test_person_normalized_name(self, ingester: GraphIngester, mock_graph: MagicMock) -> None:
        ingester.create_mention("doc.md", "  John Smith  ", "person")
        # The MERGE Person call is the first one
        person_params = mock_graph.query.call_args_list[0][0][1]
        assert person_params["normalized_name"] == "john smith"


class TestIngestParsedDocument:
    """Tests for GraphIngester.ingest_parsed_document (high-level)."""

    def test_calls_upsert_document(
        self, ingester: GraphIngester, sample_parsed_doc: ParsedDocument, mock_graph: MagicMock
    ) -> None:
        ingester.ingest_parsed_document(sample_parsed_doc)
        # At minimum, the document MERGE should have been called
        queries = [call[0][0] for call in mock_graph.query.call_args_list]
        assert any("Document" in q and "MERGE" in q for q in queries)

    def test_creates_tag_nodes_and_edges(
        self, ingester: GraphIngester, sample_parsed_doc: ParsedDocument, mock_graph: MagicMock
    ) -> None:
        ingester.ingest_parsed_document(sample_parsed_doc)
        queries = [call[0][0] for call in mock_graph.query.call_args_list]
        # Should have Tag MERGE and TAGGED_WITH MERGE queries
        assert any("Tag" in q for q in queries)
        assert any("TAGGED_WITH" in q for q in queries)

    def test_creates_topic_nodes_and_edges(
        self, ingester: GraphIngester, sample_parsed_doc: ParsedDocument, mock_graph: MagicMock
    ) -> None:
        ingester.ingest_parsed_document(sample_parsed_doc)
        queries = [call[0][0] for call in mock_graph.query.call_args_list]
        assert any("Topic" in q for q in queries)
        assert any("BELONGS_TO" in q for q in queries)

    def test_creates_wiki_link_edges(
        self, ingester: GraphIngester, sample_parsed_doc: ParsedDocument, mock_graph: MagicMock
    ) -> None:
        ingester.ingest_parsed_document(sample_parsed_doc)
        queries = [call[0][0] for call in mock_graph.query.call_args_list]
        assert any("LINKS_TO" in q for q in queries)

    def test_creates_entity_mentions(
        self, ingester: GraphIngester, sample_parsed_doc: ParsedDocument, mock_graph: MagicMock
    ) -> None:
        ingester.ingest_parsed_document(sample_parsed_doc)
        queries = [call[0][0] for call in mock_graph.query.call_args_list]
        assert any("Person" in q for q in queries)
        assert any("Concept" in q for q in queries)
        assert any("MENTIONS" in q for q in queries)

    def test_creates_source_node(
        self, ingester: GraphIngester, sample_parsed_doc: ParsedDocument, mock_graph: MagicMock
    ) -> None:
        ingester.ingest_parsed_document(sample_parsed_doc)
        queries = [call[0][0] for call in mock_graph.query.call_args_list]
        assert any("Source" in q for q in queries)
        assert any("DERIVED_FROM" in q for q in queries)

    def test_no_topics_skips_topic_queries(
        self, ingester: GraphIngester, mock_graph: MagicMock
    ) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="Body",
            metadata={},
            tags=frozenset(),
            wiki_links=frozenset(),
        )
        ingester.ingest_parsed_document(doc)
        queries = [call[0][0] for call in mock_graph.query.call_args_list]
        assert not any("Topic" in q for q in queries)

    def test_no_entities_skips_mention_queries(
        self, ingester: GraphIngester, mock_graph: MagicMock
    ) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="Body",
            metadata={},
            tags=frozenset(),
            wiki_links=frozenset(),
        )
        ingester.ingest_parsed_document(doc)
        queries = [call[0][0] for call in mock_graph.query.call_args_list]
        assert not any("MENTIONS" in q for q in queries)
