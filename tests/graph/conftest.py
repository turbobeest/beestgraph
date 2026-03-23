"""Shared pytest fixtures for graph layer tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


class FakeResultSet:
    """Minimal stand-in for a FalkorDB query result."""

    def __init__(self, rows: list[list[Any]] | None = None) -> None:
        self.result_set: list[list[Any]] = rows if rows is not None else []


@pytest.fixture
def mock_graph() -> AsyncMock:
    """Async mock of a FalkorDB Graph instance.

    The mock's ``query`` method returns a FakeResultSet by default.
    Tests can override ``graph.query.return_value`` or use ``side_effect``
    for specific scenarios.
    """
    graph = AsyncMock()
    graph.name = "beestgraph_test"
    graph.query = AsyncMock(return_value=FakeResultSet())
    return graph


@pytest.fixture
def mock_graph_with_results() -> Any:
    """Factory fixture that creates a mock graph pre-loaded with query results.

    Usage::

        def test_something(mock_graph_with_results):
            graph = mock_graph_with_results([
                FakeResultSet([[5]]),         # first query call
                FakeResultSet([[3]]),         # second query call
            ])
    """

    def _factory(results: list[FakeResultSet]) -> AsyncMock:
        graph = AsyncMock()
        graph.name = "beestgraph_test"
        graph.query = AsyncMock(side_effect=results)
        return graph

    return _factory
