"""Tests for src/graph/maintenance.py — deduplication, stats, and orphan detection."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.graph.maintenance import (
    compute_stats,
    deduplicate_entities,
    deduplicate_tags,
    find_hub_documents,
    find_orphan_documents,
)


class FakeResultSet:
    """Minimal stand-in for a FalkorDB query result."""

    def __init__(self, rows: list[list[Any]] | None = None) -> None:
        self.result_set: list[list[Any]] = rows if rows is not None else []


class TestDeduplicateTags:
    """Tests for deduplicate_tags."""

    @pytest.mark.asyncio
    async def test_returns_deleted_count(self, mock_graph: AsyncMock) -> None:
        mock_graph.query = AsyncMock(return_value=FakeResultSet([[3]]))
        result = await deduplicate_tags(mock_graph)
        assert result == 3

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_duplicates(self, mock_graph: AsyncMock) -> None:
        mock_graph.query = AsyncMock(return_value=FakeResultSet([]))
        result = await deduplicate_tags(mock_graph)
        assert result == 0

    @pytest.mark.asyncio
    async def test_query_uses_merge(self, mock_graph: AsyncMock) -> None:
        mock_graph.query = AsyncMock(return_value=FakeResultSet([]))
        await deduplicate_tags(mock_graph)
        cypher = mock_graph.query.call_args[0][0]
        assert "MERGE" in cypher

    @pytest.mark.asyncio
    async def test_query_targets_tag_label(self, mock_graph: AsyncMock) -> None:
        mock_graph.query = AsyncMock(return_value=FakeResultSet([]))
        await deduplicate_tags(mock_graph)
        cypher = mock_graph.query.call_args[0][0]
        assert "(t:Tag)" in cypher


class TestDeduplicateEntities:
    """Tests for deduplicate_entities."""

    @pytest.mark.asyncio
    async def test_processes_person_and_concept(self, mock_graph: AsyncMock) -> None:
        mock_graph.query = AsyncMock(side_effect=[FakeResultSet([[2]]), FakeResultSet([[1]])])
        result = await deduplicate_entities(mock_graph)
        assert result == {"Person": 2, "Concept": 1}

    @pytest.mark.asyncio
    async def test_returns_zero_for_both_when_empty(self, mock_graph: AsyncMock) -> None:
        mock_graph.query = AsyncMock(return_value=FakeResultSet([]))
        result = await deduplicate_entities(mock_graph)
        assert result == {"Person": 0, "Concept": 0}

    @pytest.mark.asyncio
    async def test_queries_use_mentions_relationship(self, mock_graph: AsyncMock) -> None:
        mock_graph.query = AsyncMock(return_value=FakeResultSet([]))
        await deduplicate_entities(mock_graph)
        for c in mock_graph.query.call_args_list:
            assert "MENTIONS" in c[0][0]


class TestFindOrphanDocuments:
    """Tests for find_orphan_documents query builder."""

    def test_returns_tuple(self) -> None:
        result = find_orphan_documents()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_query_checks_no_relationships(self) -> None:
        cypher, _ = find_orphan_documents()
        assert "NOT (d)--()" in cypher

    def test_returns_empty_params(self) -> None:
        _, params = find_orphan_documents()
        assert params == {}

    def test_returns_path_and_title(self) -> None:
        cypher, _ = find_orphan_documents()
        assert "d.path" in cypher
        assert "d.title" in cypher


class TestComputeStats:
    """Tests for compute_stats."""

    @pytest.mark.asyncio
    async def test_returns_all_keys(self, mock_graph_with_results: object) -> None:
        # 7 node labels + 9 edge types + 1 most_connected = 17 queries
        results = [FakeResultSet([[i]]) for i in range(16)] + [FakeResultSet([])]
        factory = mock_graph_with_results  # type: ignore[assignment]
        graph = factory(results)  # type: ignore[operator]
        stats = await compute_stats(graph)
        assert "node_counts" in stats
        assert "edge_counts" in stats
        assert "most_connected" in stats

    @pytest.mark.asyncio
    async def test_node_counts_include_all_labels(self, mock_graph_with_results: object) -> None:
        results = [FakeResultSet([[0]]) for _ in range(16)]
        results.append(FakeResultSet([]))  # most_connected returns no rows
        factory = mock_graph_with_results  # type: ignore[assignment]
        graph = factory(results)  # type: ignore[operator]
        stats = await compute_stats(graph)
        node_counts = stats["node_counts"]
        assert isinstance(node_counts, dict)
        expected_labels = {"Document", "Tag", "Topic", "Person", "Concept", "Source", "Project"}
        assert set(node_counts.keys()) == expected_labels

    @pytest.mark.asyncio
    async def test_most_connected_format(self, mock_graph_with_results: object) -> None:
        node_edge_results = [FakeResultSet([[0]]) for _ in range(16)]
        connected_result = FakeResultSet(
            [
                ["knowledge/ai.md", "AI Article", 12],
                ["knowledge/ml.md", "ML Article", 8],
            ]
        )
        factory = mock_graph_with_results  # type: ignore[assignment]
        graph = factory([*node_edge_results, connected_result])  # type: ignore[operator]
        stats = await compute_stats(graph)
        most_connected = stats["most_connected"]
        assert isinstance(most_connected, list)
        assert len(most_connected) == 2
        assert most_connected[0]["path"] == "knowledge/ai.md"
        assert most_connected[0]["degree"] == 12


class TestFindHubDocuments:
    """Tests for find_hub_documents query builder."""

    def test_default_top_n(self) -> None:
        _, params = find_hub_documents()
        assert params["top_n"] == 10

    def test_custom_top_n(self) -> None:
        _, params = find_hub_documents(top_n=5)
        assert params["top_n"] == 5

    def test_orders_by_degree(self) -> None:
        cypher, _ = find_hub_documents()
        assert "ORDER BY degree DESC" in cypher

    def test_uses_limit_param(self) -> None:
        cypher, _ = find_hub_documents()
        assert "LIMIT $top_n" in cypher
