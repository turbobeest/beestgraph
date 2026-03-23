"""Shared pytest fixtures for pipeline tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.config import BeestgraphSettings, FalkorDBSettings, VaultSettings
from src.pipeline.markdown_parser import ParsedDocument

_SAMPLE_FRONTMATTER = """\
---
title: "Knowledge Graphs for Fun and Profit"
source_url: "https://example.com/kg-article"
source_type: keepmd
author: "Jane Doe"
date_captured: "2026-01-16T10:30:00Z"
date_processed: "2026-01-16T10:45:00Z"
summary: "An overview of knowledge graph technology and its applications."
para_category: resources
topics:
  - technology/ai-ml
  - meta/pkm
tags:
  - knowledge-graphs
  - falkordb
entities:
  people:
    - "Jane Doe"
    - "Tim Berners-Lee"
  concepts:
    - "Knowledge Graph"
    - "Semantic Web"
status: published
---

# Knowledge Graphs for Fun and Profit

Knowledge graphs represent information as nodes and edges.
They power search engines, recommendation systems, and personal knowledge management.

See also [[Semantic Web]] and [[Graph Databases]].

Related: #ai-ml #graph-theory

More info at https://example.com/kg and https://example.org/semantic-web.

Tim Berners-Lee invented the World Wide Web. Jane Doe wrote this article.
"""


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault directory with an inbox/ subdirectory."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    return tmp_path


@pytest.fixture
def sample_markdown(tmp_vault: Path) -> Path:
    """Write a sample markdown file with full frontmatter into the tmp vault inbox."""
    filepath = tmp_vault / "inbox" / "kg-article.md"
    filepath.write_text(_SAMPLE_FRONTMATTER, encoding="utf-8")
    return filepath


@pytest.fixture
def sample_parsed_doc() -> ParsedDocument:
    """Return a pre-built ParsedDocument for tests that don't need file I/O."""
    return ParsedDocument(
        path="inbox/kg-article.md",
        title="Knowledge Graphs for Fun and Profit",
        content=(
            "Knowledge graphs represent information as nodes and edges.\n"
            "They power search engines, recommendation systems, and PKM.\n"
            "\n"
            "See also [[Semantic Web]] and [[Graph Databases]].\n"
            "\n"
            "Related: #ai-ml #graph-theory\n"
            "\n"
            "More info at https://example.com/kg\n"
        ),
        metadata={
            "title": "Knowledge Graphs for Fun and Profit",
            "source_url": "https://example.com/kg-article",
            "source_type": "keepmd",
            "topics": ["technology/ai-ml", "meta/pkm"],
            "tags": ["knowledge-graphs", "falkordb"],
            "entities": {
                "people": ["Jane Doe", "Tim Berners-Lee"],
                "concepts": ["Knowledge Graph", "Semantic Web"],
            },
            "summary": "An overview of knowledge graph technology.",
            "status": "published",
        },
        wiki_links=frozenset(["Semantic Web", "Graph Databases"]),
        tags=frozenset(["knowledge-graphs", "falkordb", "ai-ml", "graph-theory"]),
        urls=frozenset(["https://example.com/kg"]),
    )


@pytest.fixture
def mock_falkordb_settings() -> FalkorDBSettings:
    """Return FalkorDBSettings with test defaults."""
    return FalkorDBSettings(
        host="localhost",
        port=9999,
        graph_name="beestgraph_test",
        password="testpass",  # noqa: S106
    )


@pytest.fixture
def mock_beestgraph_settings(tmp_vault: Path) -> BeestgraphSettings:
    """Return BeestgraphSettings pointing at the tmp_vault."""
    return BeestgraphSettings(
        log_level="DEBUG",
        enable_llm_processing=False,
        falkordb=FalkorDBSettings(
            host="localhost",
            port=9999,
            graph_name="beestgraph_test",
            password="testpass",  # noqa: S106
        ),
        vault=VaultSettings(
            path=str(tmp_vault),
            inbox_dir="inbox",
            knowledge_dir="knowledge",
        ),
    )


class FakeResultSet:
    """Minimal stand-in for a FalkorDB query result."""

    def __init__(self, rows: list[list[Any]] | None = None) -> None:
        self.result_set: list[list[Any]] = rows if rows is not None else []


@pytest.fixture
def mock_graph() -> MagicMock:
    """Synchronous mock of a FalkorDB Graph instance.

    The mock's ``query`` method returns a FakeResultSet by default.
    """
    graph = MagicMock()
    graph.name = "beestgraph_test"
    graph.query = MagicMock(return_value=FakeResultSet())
    return graph
