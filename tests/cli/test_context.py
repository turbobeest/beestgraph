"""Tests for bg context — context engine levels 0-3."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.cli.commands.context import ContextCommand, _estimate_tokens


@pytest.fixture
def mock_settings(tmp_path: Path):
    from src.config import BeestgraphSettings, FalkorDBSettings, VaultSettings

    return BeestgraphSettings(
        log_level="DEBUG",
        enable_llm_processing=False,
        falkordb=FalkorDBSettings(host="localhost", port=9999, graph_name="test"),
        vault=VaultSettings(path=str(tmp_path)),
    )


@pytest.fixture(autouse=True)
def _patch_settings(mock_settings):
    with patch("src.cli.commands.context.load_settings", return_value=mock_settings):
        yield


@pytest.fixture
def vault_with_identity(tmp_path: Path) -> Path:
    """Create a vault with identity.md and daily notes."""
    # identity.md
    (tmp_path / "identity.md").write_text(
        "# Identity\n\n**Who I am:** A developer building beestgraph.\n\n"
        "**Current focus:** Knowledge graph integration.\n",
        encoding="utf-8",
    )
    # Daily note
    daily_dir = tmp_path / "04-daily"
    daily_dir.mkdir()
    (daily_dir / "2026-04-07.md").write_text(
        "---\ntitle: Daily 2026-04-07\n---\n\nWorked on context engine.\n",
        encoding="utf-8",
    )
    # Projects
    proj_dir = tmp_path / "05-projects" / "beestgraph"
    proj_dir.mkdir(parents=True)
    (proj_dir / "README.md").write_text(
        "---\ntitle: beestgraph\n---\n# beestgraph\n\nA knowledge graph project.\n",
        encoding="utf-8",
    )
    # Log
    (tmp_path / "log.md").write_text(
        "---\ntitle: Log\n---\n\n"
        "2026-04-07T12:00:00Z INGESTED Test Doc\n"
        "  entities updated: 2\n",
        encoding="utf-8",
    )
    return tmp_path


class TestLevel0:
    def test_returns_identity_content(self, vault_with_identity: Path) -> None:
        result = ContextCommand().run_without_agent(level=0)
        assert result.success
        assert "Who I am" in result.output
        assert "developer" in result.output
        assert result.data["level"] == 0

    def test_missing_identity(self, tmp_path: Path) -> None:
        result = ContextCommand().run_without_agent(level=0)
        assert result.success
        assert "identity.md not found" in result.output


class TestLevel1:
    def test_includes_daily_note(self, vault_with_identity: Path) -> None:
        mock_graph = MagicMock()
        mock_graph.query.return_value = MagicMock(result_set=[[5]])
        mock_db = MagicMock()
        mock_db.select_graph.return_value = mock_graph

        with patch("falkordb.FalkorDB", return_value=mock_db):
            result = ContextCommand().run_without_agent(level=1)

        assert result.success
        assert "context engine" in result.output or "Daily" in result.output

    def test_includes_graph_stats(self, vault_with_identity: Path) -> None:
        mock_graph = MagicMock()
        mock_graph.query.return_value = MagicMock(result_set=[[42]])
        mock_db = MagicMock()
        mock_db.select_graph.return_value = mock_graph

        with patch("falkordb.FalkorDB", return_value=mock_db):
            result = ContextCommand().run_without_agent(level=1)

        assert result.success
        assert "Graph Stats" in result.output

    def test_token_estimate_is_reasonable(self, vault_with_identity: Path) -> None:
        mock_graph = MagicMock()
        mock_graph.query.return_value = MagicMock(result_set=[[5]])
        mock_db = MagicMock()
        mock_db.select_graph.return_value = mock_graph

        with patch("falkordb.FalkorDB", return_value=mock_db):
            result = ContextCommand().run_without_agent(level=1)

        tokens = result.data["tokens"]
        assert tokens < 3000, f"Level 1 token count {tokens} exceeds 3000"


class TestLevel2:
    def test_includes_last_7_days(self, vault_with_identity: Path) -> None:
        mock_graph = MagicMock()
        mock_graph.query.return_value = MagicMock(result_set=[[5]])
        mock_db = MagicMock()
        mock_db.select_graph.return_value = mock_graph

        with patch("falkordb.FalkorDB", return_value=mock_db):
            result = ContextCommand().run_without_agent(level=2)

        assert result.success
        assert "2026-04-07" in result.output


class TestOutputFormat:
    def test_output_is_valid_markdown(self, vault_with_identity: Path) -> None:
        result = ContextCommand().run_without_agent(level=0)
        # Should contain markdown headings
        assert "#" in result.output
        # Should end with token count footer
        assert "Context bundle assembled" in result.output

    def test_file_output(self, vault_with_identity: Path, tmp_path: Path) -> None:
        out_file = tmp_path / "context-out.md"
        result = ContextCommand().run_without_agent(level=0, file=str(out_file))
        assert result.success
        assert out_file.exists()
        assert "Who I am" in out_file.read_text(encoding="utf-8")


class TestTokenEstimate:
    def test_estimate(self) -> None:
        assert _estimate_tokens("hello world") == 2  # 11 chars / 4
        assert _estimate_tokens("a" * 400) == 100
