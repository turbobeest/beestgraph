"""Tests for src/graph/schema.py — schema creation and idempotency."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.graph.schema import (
    RANGE_INDEXES,
    SCHEMA_VERSION,
    _build_fulltext_index_queries,
    _build_range_index_queries,
    _build_schema_version_query,
    ensure_schema,
)


class TestBuildRangeIndexQueries:
    """Tests for _build_range_index_queries."""

    def test_returns_one_statement_per_index(self) -> None:
        queries = _build_range_index_queries()
        assert len(queries) == len(RANGE_INDEXES)

    def test_statements_are_create_index(self) -> None:
        for query in _build_range_index_queries():
            assert query.startswith("CREATE INDEX FOR")

    def test_includes_document_path_index(self) -> None:
        queries = _build_range_index_queries()
        assert "CREATE INDEX FOR (n:Document) ON (n.path)" in queries

    def test_includes_tag_normalized_name_index(self) -> None:
        queries = _build_range_index_queries()
        assert "CREATE INDEX FOR (n:Tag) ON (n.normalized_name)" in queries


class TestBuildFulltextIndexQueries:
    """Tests for _build_fulltext_index_queries."""

    def test_returns_correct_count(self) -> None:
        queries = _build_fulltext_index_queries()
        assert len(queries) == 4

    def test_includes_document_fields(self) -> None:
        query = _build_fulltext_index_queries()[0]
        assert "Document" in query
        assert "'title'" in query
        assert "'summary'" in query


class TestBuildSchemaVersionQuery:
    """Tests for _build_schema_version_query."""

    def test_returns_merge_query(self) -> None:
        cypher, _params = _build_schema_version_query(1)
        assert "MERGE" in cypher
        assert "SchemaVersion" in cypher

    def test_params_contain_version(self) -> None:
        _, params = _build_schema_version_query(42)
        assert params["version"] == 42

    def test_params_contain_applied_at(self) -> None:
        _, params = _build_schema_version_query(1)
        assert "applied_at" in params
        assert isinstance(params["applied_at"], str)


class TestEnsureSchema:
    """Tests for ensure_schema — integration with mock graph."""

    @pytest.mark.asyncio
    async def test_calls_query_for_each_index(self, mock_graph: AsyncMock) -> None:
        await ensure_schema(mock_graph)
        from src.graph.schema import FULLTEXT_INDEXES

        range_count = len(RANGE_INDEXES)
        fulltext_count = len(FULLTEXT_INDEXES)
        version_count = 1
        assert mock_graph.query.call_count == range_count + fulltext_count + version_count

    @pytest.mark.asyncio
    async def test_returns_schema_version(self, mock_graph: AsyncMock) -> None:
        result = await ensure_schema(mock_graph)
        assert result == SCHEMA_VERSION

    @pytest.mark.asyncio
    async def test_idempotent_on_second_call(self, mock_graph: AsyncMock) -> None:
        """Calling ensure_schema twice should succeed without errors."""
        await ensure_schema(mock_graph)
        mock_graph.query.reset_mock()
        result = await ensure_schema(mock_graph)
        assert result == SCHEMA_VERSION

    @pytest.mark.asyncio
    async def test_tolerates_existing_index_error(self, mock_graph: AsyncMock) -> None:
        """If an index already exists, FalkorDB raises — ensure_schema handles it."""
        from src.graph.schema import FULLTEXT_INDEXES

        mock_graph.query = AsyncMock(
            side_effect=[Exception("Index already exists")] * len(RANGE_INDEXES)
            + [Exception("Index already exists")] * len(FULLTEXT_INDEXES)
            + [None]  # schema version succeeds
        )
        # Should not raise
        result = await ensure_schema(mock_graph)
        assert result == SCHEMA_VERSION
