"""Tests for bg think commands — Phase 2 thinking tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.graph.types import (
    AuditEvidence,
    ChallengeEvidence,
    ConnectionPaths,
    EmergenceReport,
    FrequencyTimeline,
    GraduateContext,
)


@pytest.fixture
def mock_execute_queries():
    """Patch _execute_queries in all think command modules."""
    targets = [
        "src.cli.commands.think.challenge._execute_queries",
        "src.cli.commands.think.emerge._execute_queries",
        "src.cli.commands.think.connect._execute_queries",
        "src.cli.commands.think.graduate._execute_queries",
        "src.cli.commands.think.forecast._execute_queries",
        "src.cli.commands.think.audit._execute_queries",
    ]
    mock = MagicMock()
    patches = [patch(t, mock) for t in targets]
    for p in patches:
        p.start()
    yield mock
    for p in patches:
        p.stop()


# ---------------------------------------------------------------------------
# bg think challenge
# ---------------------------------------------------------------------------


class TestChallenge:
    def test_returns_evidence(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "decisions": [
                ["Use FalkorDB", "path/adr.md", "20260101", "published", "2026-01-01", 0.85],
            ],
            "contradictions": [
                ["Doc A", "path/a.md", "Doc B", "path/b.md"],
            ],
            "reversed": [],
        }
        from src.cli.commands.think.challenge import ChallengeCommand

        result = ChallengeCommand().run_without_agent(topic="database")
        assert result.success
        evidence = result.data
        assert isinstance(evidence, ChallengeEvidence)
        assert len(evidence.decisions) == 1
        assert evidence.decisions[0].title == "Use FalkorDB"
        assert len(evidence.contradictions) == 1
        assert len(evidence.reversed) == 0

    def test_empty_results(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "decisions": [], "contradictions": [], "reversed": [],
        }
        from src.cli.commands.think.challenge import ChallengeCommand

        result = ChallengeCommand().run_without_agent(topic="nonexistent")
        assert result.success
        assert "(none found)" in result.output

    def test_json_output(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "decisions": [], "contradictions": [], "reversed": [],
        }
        from src.cli.commands.think.challenge import ChallengeCommand

        result = ChallengeCommand().run_without_agent(topic="test", json=True)
        assert result.success
        assert '"topic": "test"' in result.output


# ---------------------------------------------------------------------------
# bg think emerge
# ---------------------------------------------------------------------------


class TestEmerge:
    def test_returns_trends(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "trending_tags": [
                ["python", 15],
                ["ai-ml", 12],
            ],
            "entity_clusters": [
                ["Person:Jane", "Concept:ML", 5],
            ],
            "topic_density": [
                ["technology/ai-ml", 8],
            ],
        }
        from src.cli.commands.think.emerge import EmergeCommand

        result = EmergeCommand().run_without_agent(period=30)
        assert result.success
        report = result.data
        assert isinstance(report, EmergenceReport)
        assert len(report.trending_tags) == 2
        assert report.trending_tags[0].tag == "python"
        assert len(report.entity_clusters) == 1
        assert len(report.topic_density) == 1

    def test_empty_results(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "trending_tags": [], "entity_clusters": [], "topic_density": [],
        }
        from src.cli.commands.think.emerge import EmergeCommand

        result = EmergeCommand().run_without_agent()
        assert result.success
        assert "no co-occurring" in result.output


# ---------------------------------------------------------------------------
# bg think connect
# ---------------------------------------------------------------------------


class TestConnect:
    def test_returns_paths(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "shortest_path": [["FalkorDB"], ["Graph DB"], ["Neo4j"]],
            "shared_nodes": [["Database Article"]],
            "bridging_docs": [
                ["Graph DB Comparison", "path/comparison.md", "2026"],
            ],
        }
        from src.cli.commands.think.connect import ConnectCommand

        result = ConnectCommand().run_without_agent(a="FalkorDB", b="Neo4j")
        assert result.success
        paths = result.data
        assert isinstance(paths, ConnectionPaths)
        assert len(paths.shortest_path) == 3
        assert len(paths.shared_nodes) == 1
        assert len(paths.bridging_docs) == 1

    def test_no_path_found(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "shortest_path": [], "shared_nodes": [], "bridging_docs": [],
        }
        from src.cli.commands.think.connect import ConnectCommand

        result = ConnectCommand().run_without_agent(a="A", b="Z")
        assert result.success
        assert "no path found" in result.output


# ---------------------------------------------------------------------------
# bg think audit
# ---------------------------------------------------------------------------


class TestAudit:
    def test_returns_evidence(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "matching": [
                ["Benchmark Doc", "path/bench.md", "uid1", "2026-01-15", 0.85, "fast", 6.5],
                ["Overview", "path/overview.md", "uid2", "2026-02-01", 0.6, "", 3.2],
            ],
            "supporting": [
                ["Support Doc", "path/support.md", "uid3", "2026-01-20", 0.9],
            ],
            "contradicting": [
                ["Counter Doc", "path/counter.md", "uid4", "2025-11-02", 0.6],
            ],
        }
        from src.cli.commands.think.audit import AuditCommand

        result = AuditCommand().run_without_agent(claim="FalkorDB is fast")
        assert result.success
        evidence = result.data
        assert isinstance(evidence, AuditEvidence)
        assert len(evidence.supporting) == 1
        assert len(evidence.contradicting) == 1
        # The two matching docs that aren't in supporting/contradicting
        assert len(evidence.unverified) == 2

    def test_no_evidence(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "matching": [], "supporting": [], "contradicting": [],
        }
        from src.cli.commands.think.audit import AuditCommand

        result = AuditCommand().run_without_agent(claim="unknown claim")
        assert result.success
        assert "(none)" in result.output


# ---------------------------------------------------------------------------
# bg think graduate
# ---------------------------------------------------------------------------


class TestGraduate:
    def test_finds_source_and_related(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "source_doc": [
                ["My Idea", "path/idea.md", "20260301", "inbox", "2026-03-01"],
            ],
            "related_docs": [
                ["Related Note", "path/related.md", "20260215"],
            ],
            "nearby_projects": [],
        }
        from src.cli.commands.think.graduate import GraduateCommand

        result = GraduateCommand().run_without_agent(idea="idea")
        assert result.success
        ctx = result.data
        assert isinstance(ctx, GraduateContext)
        assert ctx.source_doc is not None
        assert ctx.source_doc.title == "My Idea"
        assert len(ctx.related_docs) == 1


# ---------------------------------------------------------------------------
# bg think forecast
# ---------------------------------------------------------------------------


class TestForecast:
    def test_returns_timeline(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "monthly_counts": [
                ["2025-12", 3],
                ["2026-01", 5],
                ["2026-02", 8],
            ],
            "related_trends": [
                ["FalkorDB", "2026-01", 2],
                ["FalkorDB", "2026-02", 4],
            ],
        }
        from src.cli.commands.think.forecast import ForecastCommand

        result = ForecastCommand().run_without_agent(topic="ai-ml")
        assert result.success
        timeline = result.data
        assert isinstance(timeline, FrequencyTimeline)
        assert len(timeline.monthly_counts) == 3
        assert timeline.trend_direction == "rising"
        assert len(timeline.related_trends) == 1

    def test_falling_trend(self, mock_execute_queries: MagicMock) -> None:
        mock_execute_queries.return_value = {
            "monthly_counts": [["2026-01", 10], ["2026-02", 3]],
            "related_trends": [],
        }
        from src.cli.commands.think.forecast import ForecastCommand

        result = ForecastCommand().run_without_agent(topic="old-topic")
        assert result.success
        assert result.data.trend_direction == "falling"
