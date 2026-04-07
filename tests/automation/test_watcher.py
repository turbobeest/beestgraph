"""Tests for src/automation/watcher.py — vault-sync incremental watcher."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.automation.watcher import _DebouncedSyncHandler, _IGNORE_DIRS
from src.config import BeestgraphSettings, FalkorDBSettings, VaultSettings


@pytest.fixture
def mock_settings(tmp_path: Path) -> BeestgraphSettings:
    return BeestgraphSettings(
        log_level="DEBUG",
        enable_llm_processing=False,
        falkordb=FalkorDBSettings(host="localhost", port=9999, graph_name="test"),
        vault=VaultSettings(path=str(tmp_path)),
    )


@pytest.fixture
def handler(mock_settings: BeestgraphSettings) -> _DebouncedSyncHandler:
    return _DebouncedSyncHandler(mock_settings)


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    """Create vault structure for testing."""
    for d in ["00-meta", "01-inbox", "04-daily", "07-resources", "09-attachments"]:
        (tmp_path / d).mkdir()
    return tmp_path


class TestVaultWatcherIgnoresInbox:
    def test_ignores_inbox_files(self, handler: _DebouncedSyncHandler, tmp_vault: Path) -> None:
        inbox_file = tmp_vault / "01-inbox" / "new.md"
        assert handler._should_ignore(inbox_file) is True

    def test_ignores_attachments(self, handler: _DebouncedSyncHandler, tmp_vault: Path) -> None:
        attach = tmp_vault / "09-attachments" / "image.md"
        assert handler._should_ignore(attach) is True

    def test_ignores_git_dir(self, handler: _DebouncedSyncHandler, tmp_vault: Path) -> None:
        git_file = tmp_vault / ".git" / "config.md"
        assert handler._should_ignore(git_file) is True

    def test_ignores_obsidian_dir(self, handler: _DebouncedSyncHandler, tmp_vault: Path) -> None:
        obs = tmp_vault / ".obsidian" / "workspace.md"
        assert handler._should_ignore(obs) is True

    def test_accepts_resources(self, handler: _DebouncedSyncHandler, tmp_vault: Path) -> None:
        resource = tmp_vault / "07-resources" / "article.md"
        assert handler._should_ignore(resource) is False

    def test_accepts_daily(self, handler: _DebouncedSyncHandler, tmp_vault: Path) -> None:
        daily = tmp_vault / "04-daily" / "2026-04-07.md"
        assert handler._should_ignore(daily) is False


class TestVaultWatcherSync:
    def test_syncs_frontmatter_on_change(
        self, handler: _DebouncedSyncHandler, tmp_vault: Path,
    ) -> None:
        # Create a file in the vault
        doc = tmp_vault / "07-resources" / "test.md"
        doc.write_text(
            '---\nuid: "20260407"\ntitle: "Test"\nstatus: published\n---\nContent.\n',
            encoding="utf-8",
        )

        mock_graph = MagicMock()
        mock_db = MagicMock()
        mock_db.select_graph.return_value = mock_graph

        with patch("falkordb.FalkorDB", return_value=mock_db):
            handler._sync_file(doc)

        mock_graph.query.assert_called_once()
        call_args = mock_graph.query.call_args
        assert "uid" in call_args[0][0]
        assert call_args[0][1]["uid"] == "20260407"


class TestDebounce:
    def test_coalesces_rapid_changes(
        self, handler: _DebouncedSyncHandler, tmp_vault: Path,
    ) -> None:
        doc = tmp_vault / "04-daily" / "test.md"
        doc.write_text("---\ntitle: Test\n---\n", encoding="utf-8")

        event = MagicMock()
        event.is_directory = False
        event.src_path = str(doc)

        # Simulate rapid changes
        handler.on_modified(event)
        handler.on_modified(event)
        handler.on_modified(event)

        # Only one path should be pending
        assert len(handler._pending) == 1

        # Cancel the timer to prevent it from firing during cleanup
        if handler._timer:
            handler._timer.cancel()
