"""Tests for the five-phase ingest pipeline in src/pipeline/ingester.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.config import FalkorDBSettings
from src.pipeline.ingester import GraphIngester, IngestResult, PhaseResult
from src.pipeline.markdown_parser import ParsedDocument


@pytest.fixture
def ingester(mock_falkordb_settings: FalkorDBSettings, mock_graph: MagicMock) -> GraphIngester:
    """Create a GraphIngester with a mocked FalkorDB backend."""
    ing = GraphIngester(mock_falkordb_settings)
    ing._graph = MagicMock(return_value=mock_graph)
    return ing


@pytest.fixture
def sample_doc() -> ParsedDocument:
    """Document with entities for multi-phase testing."""
    return ParsedDocument(
        path="inbox/test-article.md",
        title="Test Article About AI",
        content="This article discusses AI and knowledge graphs.",
        metadata={
            "title": "Test Article About AI",
            "uid": "20260407120000",
            "summary": "An article about AI and knowledge graphs.",
            "topics": ["technology/ai-ml"],
            "entities": {
                "people": ["Alan Turing"],
                "concepts": ["Knowledge Graph", "Machine Learning"],
                "organizations": ["DeepMind"],
            },
            "key_claims": ["AI will transform knowledge management"],
            "status": "published",
        },
        tags=frozenset(["ai", "knowledge-graphs"]),
        wiki_links=frozenset(),
    )


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    """Create a temporary vault with required directories."""
    for d in [
        "00-meta", "01-inbox", "02-queue",
        "entities/people", "entities/organizations",
        "entities/tools", "entities/concepts", "entities/places",
    ]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    # Create index.md and log.md
    (tmp_path / "index.md").write_text("---\ntitle: Index\n---\n\n", encoding="utf-8")
    (tmp_path / "log.md").write_text("---\ntitle: Log\n---\n\n", encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# Phase 1 regression
# ---------------------------------------------------------------------------


class TestPhase1Regression:
    """Ensure Phase 1 behavior is exactly the existing ingester logic."""

    def test_phase1_only_is_default(
        self, ingester: GraphIngester, sample_doc: ParsedDocument,
        tmp_vault: Path, mock_graph: MagicMock,
    ) -> None:
        result = ingester.ingest(sample_doc, vault_path=tmp_vault)
        assert result.phase1 is not None
        assert result.phase1.success
        assert result.phase2 is None
        assert result.phase3 is None
        assert result.phase4 is None
        assert result.phase5 is None

    def test_phase1_calls_ingest_parsed_document(
        self, ingester: GraphIngester, sample_doc: ParsedDocument,
        tmp_vault: Path, mock_graph: MagicMock,
    ) -> None:
        result = ingester.ingest(sample_doc, vault_path=tmp_vault, phases=[1])
        assert result.phase1.success
        # Should have called graph queries for document + tags + topics + entities
        assert mock_graph.query.call_count > 0


# ---------------------------------------------------------------------------
# Phase 2: Entity updates
# ---------------------------------------------------------------------------


class TestPhase2Entities:
    def test_creates_entity_file_when_missing(
        self, ingester: GraphIngester, sample_doc: ParsedDocument,
        tmp_vault: Path, mock_graph: MagicMock,
    ) -> None:
        result = ingester.ingest(sample_doc, vault_path=tmp_vault, phases=[2])
        assert result.phase2 is not None
        assert result.phase2.success

        # Check entity files were created
        assert (tmp_vault / "entities" / "people" / "alan-turing.md").exists()
        assert (tmp_vault / "entities" / "concepts" / "knowledge-graph.md").exists()
        assert (tmp_vault / "entities" / "concepts" / "machine-learning.md").exists()
        assert (tmp_vault / "entities" / "organizations" / "deepmind.md").exists()

    def test_appends_to_existing_entity_file(
        self, ingester: GraphIngester, sample_doc: ParsedDocument,
        tmp_vault: Path, mock_graph: MagicMock,
    ) -> None:
        # Pre-create entity file
        entity_path = tmp_vault / "entities" / "people" / "alan-turing.md"
        entity_path.write_text(
            "---\ntitle: Alan Turing\n---\n\n## About\n\n## Mentioned In\n\n",
            encoding="utf-8",
        )

        result = ingester.ingest(sample_doc, vault_path=tmp_vault, phases=[2])
        content = entity_path.read_text(encoding="utf-8")
        assert "Test Article About AI" in content
        assert "## Mentioned In" in content

    def test_entity_mention_is_idempotent(
        self, ingester: GraphIngester, sample_doc: ParsedDocument,
        tmp_vault: Path, mock_graph: MagicMock,
    ) -> None:
        ingester.ingest(sample_doc, vault_path=tmp_vault, phases=[2])
        ingester.ingest(sample_doc, vault_path=tmp_vault, phases=[2])

        entity_path = tmp_vault / "entities" / "people" / "alan-turing.md"
        content = entity_path.read_text(encoding="utf-8")
        # Should appear exactly once
        assert content.count("Test Article About AI") == 1


# ---------------------------------------------------------------------------
# Phase 3: Contradiction detection
# ---------------------------------------------------------------------------


class TestPhase3Contradictions:
    def test_detects_contradiction_candidate(
        self, ingester: GraphIngester, sample_doc: ParsedDocument,
        tmp_vault: Path, mock_graph: MagicMock,
    ) -> None:
        # Mock fulltext search returning a matching document
        mock_graph.query.return_value = MagicMock(
            result_set=[
                ["Conflicting Doc", "path/conflict.md", "some claims", 0.8],
            ]
        )
        result = ingester.ingest(sample_doc, vault_path=tmp_vault, phases=[3])
        assert result.phase3 is not None
        assert len(result.phase3.items) >= 1

        # Check review file was created
        review = tmp_vault / "00-meta" / "contradictions-review.md"
        assert review.exists()
        content = review.read_text(encoding="utf-8")
        assert "Conflicting Doc" in content

    def test_no_false_positive_on_unrelated_content(
        self, ingester: GraphIngester, tmp_vault: Path, mock_graph: MagicMock,
    ) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="Simple note.",
            metadata={"key_claims": []},  # No claims
        )
        result = ingester.ingest(doc, vault_path=tmp_vault, phases=[3])
        assert result.phase3 is not None
        assert len(result.phase3.items) == 0


# ---------------------------------------------------------------------------
# Phase 5: Navigation updates
# ---------------------------------------------------------------------------


class TestPhase5Navigation:
    def test_updates_index_md(
        self, ingester: GraphIngester, sample_doc: ParsedDocument,
        tmp_vault: Path, mock_graph: MagicMock,
    ) -> None:
        result = ingester.ingest(sample_doc, vault_path=tmp_vault, phases=[5])
        assert result.phase5 is not None
        assert "index.md" in result.phase5.items

        content = (tmp_vault / "index.md").read_text(encoding="utf-8")
        assert "Test Article About AI" in content

    def test_updates_log_md(
        self, ingester: GraphIngester, sample_doc: ParsedDocument,
        tmp_vault: Path, mock_graph: MagicMock,
    ) -> None:
        result = ingester.ingest(sample_doc, vault_path=tmp_vault, phases=[5])
        assert "log.md" in result.phase5.items

        content = (tmp_vault / "log.md").read_text(encoding="utf-8")
        assert "INGESTED Test Article About AI" in content
        assert "entities updated: 0" in content  # Phase 2 wasn't run


# ---------------------------------------------------------------------------
# IngestResult dataclass
# ---------------------------------------------------------------------------


class TestIngestResult:
    def test_entities_updated_count(self) -> None:
        r = IngestResult(phase2=PhaseResult(phase=2, items=["a", "b"]))
        assert r.entities_updated == 2

    def test_contradictions_flagged_count(self) -> None:
        r = IngestResult(phase3=PhaseResult(phase=3, items=["x"]))
        assert r.contradictions_flagged == 1

    def test_synthesis_created(self) -> None:
        r = IngestResult(phase4=PhaseResult(phase=4, items=["synth.md"]))
        assert r.synthesis_created is True

    def test_no_synthesis(self) -> None:
        r = IngestResult()
        assert r.synthesis_created is False

    def test_default_phases_is_one(
        self, ingester: GraphIngester, tmp_vault: Path, mock_graph: MagicMock,
    ) -> None:
        doc = ParsedDocument(
            path="test.md", title="Test", content="Body", metadata={},
        )
        result = ingester.ingest(doc, vault_path=tmp_vault)
        assert result.phase1 is not None
        assert result.phase2 is None
