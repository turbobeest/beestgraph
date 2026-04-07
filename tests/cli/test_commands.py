"""Tests for bg CLI commands — Phase 1."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.cli.commands import BaseCommand, Result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings(tmp_path: Path) -> MagicMock:
    """Build a mock BeestgraphSettings pointing at tmp_path as the vault."""
    from src.config import (
        BeestgraphSettings,
        FalkorDBSettings,
        VaultSettings,
    )

    return BeestgraphSettings(
        log_level="DEBUG",
        enable_llm_processing=False,
        falkordb=FalkorDBSettings(
            host="localhost",
            port=9999,
            graph_name="beestgraph_test",
            password="testpass",
        ),
        vault=VaultSettings(path=str(tmp_path)),
    )


@pytest.fixture(autouse=True)
def _patch_load_settings(mock_settings: MagicMock) -> None:
    """Patch load_settings globally for all CLI tests."""
    with patch("src.config.load_settings", return_value=mock_settings):
        # Also patch it in each command module that imports it
        modules = [
            "src.cli.commands.daily",
            "src.cli.commands.task",
            "src.cli.commands.find",
            "src.cli.commands.project",
            "src.cli.commands.health",
            "src.cli.commands.init",
            "src.cli.commands.capture",
            "src.cli.commands.save",
            "src.cli.commands.export",
            "src.cli.commands.archive",
            "src.cli.commands.ingest",
        ]
        patches = [patch(f"{m}.load_settings", return_value=mock_settings) for m in modules]
        for p in patches:
            p.start()
        yield
        for p in patches:
            p.stop()


# ---------------------------------------------------------------------------
# BaseCommand contract
# ---------------------------------------------------------------------------


class TestBaseCommand:
    """Verify the two-path contract."""

    def test_result_dataclass(self) -> None:
        r = Result(success=True, output="ok")
        assert r.success is True
        assert r.output == "ok"
        assert r.data is None
        assert r.error is None

    def test_result_with_error(self) -> None:
        r = Result(success=False, output="", error="fail")
        assert not r.success

    def test_run_with_agent_falls_back(self) -> None:
        class Cmd(BaseCommand):
            def run_without_agent(self, **kwargs) -> Result:
                return Result(success=True, output="base")

        result = Cmd().run_with_agent(agent=None)
        assert result.output == "base"


# ---------------------------------------------------------------------------
# bg daily
# ---------------------------------------------------------------------------


class TestDaily:
    def test_creates_daily_note(self, tmp_path: Path) -> None:
        from src.cli.commands.daily import DailyCommand

        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        daily_dir = tmp_path / "04-daily"
        daily_dir.mkdir(parents=True)

        result = DailyCommand().run_without_agent()

        assert result.success
        assert result.data["created"] is True
        filepath = Path(result.data["path"])
        assert filepath.exists()
        assert today in filepath.name

    def test_existing_daily_returns_path(self, tmp_path: Path) -> None:
        from src.cli.commands.daily import DailyCommand

        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        daily_dir = tmp_path / "04-daily"
        daily_dir.mkdir(parents=True)
        existing = daily_dir / f"{today}.md"
        existing.write_text("existing", encoding="utf-8")

        result = DailyCommand().run_without_agent()
        assert result.success
        assert result.data["created"] is False


# ---------------------------------------------------------------------------
# bg find
# ---------------------------------------------------------------------------


class TestFind:
    def test_calls_search_documents(self, tmp_path: Path) -> None:
        from src.cli.commands.find import FindCommand

        mock_graph = MagicMock()
        mock_node = MagicMock()
        mock_node.properties = {"title": "Test Doc", "path": "test.md", "type": "article"}
        mock_graph.query.return_value = MagicMock(result_set=[[mock_node, 0.95]])

        mock_db = MagicMock()
        mock_db.select_graph.return_value = mock_graph

        with patch("falkordb.FalkorDB", return_value=mock_db):
            result = FindCommand().run_without_agent(query="test", limit=5)

        assert result.success
        assert len(result.data) == 1
        assert result.data[0]["title"] == "Test Doc"

    def test_empty_results(self, tmp_path: Path) -> None:
        from src.cli.commands.find import FindCommand

        mock_graph = MagicMock()
        mock_graph.query.return_value = MagicMock(result_set=[])
        mock_db = MagicMock()
        mock_db.select_graph.return_value = mock_graph

        with patch("falkordb.FalkorDB", return_value=mock_db):
            result = FindCommand().run_without_agent(query="nonexistent")

        assert result.success
        assert "No results" in result.output


# ---------------------------------------------------------------------------
# bg health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_returns_success(self, tmp_path: Path) -> None:
        from src.cli.commands.health import HealthCommand

        with patch("src.cli.commands.health.run_all_checks", return_value=[]):
            result = HealthCommand().run_without_agent()

        assert result.success
        assert "Health Report" in result.output


# ---------------------------------------------------------------------------
# bg init
# ---------------------------------------------------------------------------


class TestInit:
    def test_creates_directories(self, tmp_path: Path) -> None:
        from src.cli.commands.init import InitCommand

        result = InitCommand().run_without_agent()

        assert result.success
        assert (tmp_path / "entities" / "people").is_dir()
        assert (tmp_path / "entities" / "organizations").is_dir()
        assert (tmp_path / "entities" / "tools").is_dir()
        assert (tmp_path / "entities" / "concepts").is_dir()
        assert (tmp_path / "entities" / "places").is_dir()
        assert (tmp_path / "raw" / "articles").is_dir()
        assert (tmp_path / "raw" / "transcripts").is_dir()
        assert (tmp_path / "raw" / "pdfs").is_dir()
        assert (tmp_path / "index.md").exists()
        assert (tmp_path / "log.md").exists()

    def test_idempotent(self, tmp_path: Path) -> None:
        from src.cli.commands.init import InitCommand

        cmd = InitCommand()
        r1 = cmd.run_without_agent()
        r2 = cmd.run_without_agent()

        assert r1.success and r2.success
        assert len(r2.data["created"]) == 0
        assert len(r2.data["existed"]) > 0


# ---------------------------------------------------------------------------
# bg capture
# ---------------------------------------------------------------------------


class TestCapture:
    def test_creates_file_in_inbox(self, tmp_path: Path) -> None:
        from src.cli.commands.capture import CaptureCommand

        inbox = tmp_path / "01-inbox"
        inbox.mkdir()

        result = CaptureCommand().run_without_agent(
            text="This is a test idea",
            title="Test Idea",
            tags=["test", "idea"],
        )

        assert result.success
        filepath = Path(result.data["path"])
        assert filepath.exists()
        assert filepath.parent == inbox
        content = filepath.read_text(encoding="utf-8")
        assert "Test Idea" in content
        assert 'uid: "' in content

    def test_auto_title_from_text(self, tmp_path: Path) -> None:
        from src.cli.commands.capture import CaptureCommand

        (tmp_path / "01-inbox").mkdir()
        result = CaptureCommand().run_without_agent(text="My quick thought about graphs")
        assert result.success
        assert result.data["title"] == "My quick thought about graphs"


# ---------------------------------------------------------------------------
# bg task
# ---------------------------------------------------------------------------


class TestTask:
    def test_adds_task_line(self, tmp_path: Path) -> None:
        from src.cli.commands.task import TaskCommand

        (tmp_path / "00-meta").mkdir()
        result = TaskCommand().run_without_agent(title="Fix the tests")
        assert result.success

        task_file = tmp_path / "00-meta" / "tasks.md"
        assert task_file.exists()
        content = task_file.read_text(encoding="utf-8")
        assert "- [ ] Fix the tests" in content

    def test_project_task(self, tmp_path: Path) -> None:
        from src.cli.commands.task import TaskCommand

        result = TaskCommand().run_without_agent(
            title="Deploy v2", project="beestgraph", priority="high",
        )
        assert result.success
        task_file = tmp_path / "05-projects" / "beestgraph" / "tasks.md"
        assert task_file.exists()
        content = task_file.read_text(encoding="utf-8")
        assert "priority:high" in content


# ---------------------------------------------------------------------------
# bg save
# ---------------------------------------------------------------------------


class TestSave:
    def test_extracts_action_items(self, tmp_path: Path) -> None:
        from src.cli.commands.save import SaveCommand

        (tmp_path / "03-fleeting").mkdir()
        text = "- [ ] Ship the feature\n- Fix the bug\nTODO: write tests\n"
        result = SaveCommand().run_without_agent(text=text)

        assert result.success
        assert len(result.data["actions"]) >= 2

    def test_extracts_decisions(self, tmp_path: Path) -> None:
        from src.cli.commands.save import SaveCommand

        (tmp_path / "03-fleeting").mkdir()
        text = "We decided to use FalkorDB instead of Neo4j for the graph layer.\n"
        result = SaveCommand().run_without_agent(text=text)

        assert result.success
        assert len(result.data["decisions"]) >= 1


# ---------------------------------------------------------------------------
# bg archive
# ---------------------------------------------------------------------------


class TestArchive:
    def test_moves_to_archive(self, tmp_path: Path) -> None:
        from src.cli.commands.archive import ArchiveCommand

        inbox = tmp_path / "01-inbox"
        inbox.mkdir()
        filepath = inbox / "old-note.md"
        filepath.write_text("---\ntitle: Old\nstatus: published\n---\nContent\n")
        archive_dir = tmp_path / "08-archive"

        result = ArchiveCommand().run_without_agent(
            slug_or_path=str(filepath), reason="outdated",
        )

        assert result.success
        assert not filepath.exists()
        assert (archive_dir / "old-note.md").exists()


# ---------------------------------------------------------------------------
# bg ingest
# ---------------------------------------------------------------------------


class TestIngest:
    def test_url_creates_inbox_stub(self, tmp_path: Path) -> None:
        from src.cli.commands.ingest import IngestCommand

        (tmp_path / "01-inbox").mkdir()
        result = IngestCommand().run_without_agent(
            url_or_path="https://example.com/article",
        )

        assert result.success
        filepath = Path(result.data["path"])
        assert filepath.exists()
        content = filepath.read_text(encoding="utf-8")
        assert "https://example.com/article" in content

    def test_invalid_input(self, tmp_path: Path) -> None:
        from src.cli.commands.ingest import IngestCommand

        result = IngestCommand().run_without_agent(url_or_path="not-a-file-or-url")
        assert not result.success


# ---------------------------------------------------------------------------
# bg export
# ---------------------------------------------------------------------------


class TestExport:
    def test_exports_documents(self, tmp_path: Path) -> None:
        from src.cli.commands.export import ExportCommand

        (tmp_path / "test.md").write_text(
            "---\ntitle: Test\ntags: [a]\n---\nBody\n"
        )
        result = ExportCommand().run_without_agent()
        assert result.success
        assert result.data["count"] >= 1


# ---------------------------------------------------------------------------
# bg project
# ---------------------------------------------------------------------------


class TestProject:
    def test_shows_project_info(self, tmp_path: Path) -> None:
        from src.cli.commands.project import ProjectCommand

        proj_dir = tmp_path / "05-projects" / "beestgraph"
        proj_dir.mkdir(parents=True)
        (proj_dir / "README.md").write_text(
            "---\ntitle: beestgraph\n---\n# beestgraph\n\nA knowledge graph.\n"
        )

        result = ProjectCommand().run_without_agent(project_name="beestgraph")
        assert result.success
        assert "beestgraph" in result.output
