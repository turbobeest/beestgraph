"""Tests for src.pipeline.watcher — inbox file monitoring and processing."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.config import BeestgraphSettings
from src.pipeline.markdown_parser import ParsedDocument
from src.pipeline.watcher import _handle_new_file, _InboxHandler, _resolve_destination

# ---------------------------------------------------------------------------
# _resolve_destination
# ---------------------------------------------------------------------------


class TestResolveDestination:
    """Tests for vault destination resolution based on topic metadata."""

    def test_uses_first_topic_as_subdirectory(
        self, mock_beestgraph_settings: BeestgraphSettings
    ) -> None:
        doc = ParsedDocument(
            path="inbox/article.md",
            title="Test",
            content="Body",
            metadata={"topics": ["technology/ai-ml", "meta/pkm"]},
        )
        dest = _resolve_destination(doc, mock_beestgraph_settings)
        vault = Path(mock_beestgraph_settings.vault.path)
        expected = vault / "knowledge" / "technology/ai-ml" / "article.md"
        assert dest == expected

    def test_falls_back_to_knowledge_root(
        self, mock_beestgraph_settings: BeestgraphSettings
    ) -> None:
        doc = ParsedDocument(
            path="inbox/article.md",
            title="Test",
            content="Body",
            metadata={},
        )
        dest = _resolve_destination(doc, mock_beestgraph_settings)
        vault = Path(mock_beestgraph_settings.vault.path)
        expected = vault / "knowledge" / "article.md"
        assert dest == expected

    def test_empty_topics_list_falls_back(
        self, mock_beestgraph_settings: BeestgraphSettings
    ) -> None:
        doc = ParsedDocument(
            path="inbox/article.md",
            title="Test",
            content="Body",
            metadata={"topics": []},
        )
        dest = _resolve_destination(doc, mock_beestgraph_settings)
        vault = Path(mock_beestgraph_settings.vault.path)
        expected = vault / "knowledge" / "article.md"
        assert dest == expected

    def test_topic_normalized_lowercase(self, mock_beestgraph_settings: BeestgraphSettings) -> None:
        doc = ParsedDocument(
            path="inbox/article.md",
            title="Test",
            content="Body",
            metadata={"topics": ["Science/Physics"]},
        )
        dest = _resolve_destination(doc, mock_beestgraph_settings)
        assert "science/physics" in str(dest)


# ---------------------------------------------------------------------------
# _handle_new_file
# ---------------------------------------------------------------------------


class TestHandleNewFile:
    """Tests for the single-file processing pipeline."""

    def test_calls_parse_process_ingest_in_sequence(
        self,
        tmp_vault: Path,
        mock_beestgraph_settings: BeestgraphSettings,
    ) -> None:
        # Write a markdown file
        filepath = tmp_vault / "inbox" / "test-article.md"
        filepath.write_text(
            "---\ntitle: Test Article\ntopics:\n  - meta/pkm\n---\n\nSome content here.\n",
            encoding="utf-8",
        )

        call_order: list[str] = []

        def mock_parse(fp, vault_root=None):
            call_order.append("parse")
            # Use real parse
            from src.pipeline.markdown_parser import parse_file

            return parse_file(fp, vault_root=vault_root)

        def mock_process(doc, enable_llm=False):
            call_order.append("process")
            return doc

        mock_ingester = MagicMock()

        def mock_ingest(doc):
            call_order.append("ingest")

        mock_ingester.ingest_parsed_document = mock_ingest

        with (
            patch("src.pipeline.watcher.parse_file", side_effect=mock_parse),
            patch("src.pipeline.watcher.process_document", side_effect=mock_process),
            patch("src.pipeline.watcher.GraphIngester", return_value=mock_ingester),
        ):
            _handle_new_file(filepath, mock_beestgraph_settings)

        assert call_order == ["parse", "process", "ingest"]

    def test_handles_parse_failure_gracefully(
        self,
        tmp_vault: Path,
        mock_beestgraph_settings: BeestgraphSettings,
    ) -> None:
        filepath = tmp_vault / "inbox" / "missing.md"
        # File doesn't exist — parse should fail
        with patch("src.pipeline.watcher.GraphIngester") as mock_cls:
            _handle_new_file(filepath, mock_beestgraph_settings)
            # Ingester should never be called
            mock_cls.return_value.ingest_parsed_document.assert_not_called()

    def test_handles_ingest_connection_error(
        self,
        tmp_vault: Path,
        mock_beestgraph_settings: BeestgraphSettings,
    ) -> None:
        filepath = tmp_vault / "inbox" / "test.md"
        filepath.write_text("---\ntitle: Test\n---\n\nContent.\n", encoding="utf-8")

        mock_ingester = MagicMock()
        mock_ingester.ingest_parsed_document.side_effect = ConnectionError("db down")

        with (
            patch("src.pipeline.watcher.process_document", side_effect=lambda d, **kw: d),
            patch("src.pipeline.watcher.GraphIngester", return_value=mock_ingester),
        ):
            # Should not raise — handled gracefully
            _handle_new_file(filepath, mock_beestgraph_settings)

    def test_moves_file_to_destination(
        self,
        tmp_vault: Path,
        mock_beestgraph_settings: BeestgraphSettings,
    ) -> None:
        filepath = tmp_vault / "inbox" / "moveme.md"
        filepath.write_text(
            "---\ntitle: Move Me\ntopics:\n  - technology/web\n---\n\nWeb content.\n",
            encoding="utf-8",
        )

        mock_ingester = MagicMock()

        with (
            patch("src.pipeline.watcher.process_document", side_effect=lambda d, **kw: d),
            patch("src.pipeline.watcher.GraphIngester", return_value=mock_ingester),
        ):
            _handle_new_file(filepath, mock_beestgraph_settings)

        # File should have been moved out of inbox
        assert not filepath.exists()
        dest = tmp_vault / "knowledge" / "technology/web" / "moveme.md"
        assert dest.exists()


# ---------------------------------------------------------------------------
# _InboxHandler (watchdog integration)
# ---------------------------------------------------------------------------


class TestInboxHandler:
    """Tests for the watchdog event handler."""

    def test_ignores_directory_events(self, mock_beestgraph_settings: BeestgraphSettings) -> None:
        handler = _InboxHandler(mock_beestgraph_settings)
        event = MagicMock()
        event.is_directory = True
        event.src_path = "/some/dir"
        with patch("src.pipeline.watcher._handle_new_file") as mock_handle:
            handler.on_created(event)
            mock_handle.assert_not_called()

    def test_ignores_non_markdown_files(self, mock_beestgraph_settings: BeestgraphSettings) -> None:
        handler = _InboxHandler(mock_beestgraph_settings)
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/some/file.txt"
        with patch("src.pipeline.watcher._handle_new_file") as mock_handle:
            handler.on_created(event)
            mock_handle.assert_not_called()

    def test_processes_markdown_files(self, mock_beestgraph_settings: BeestgraphSettings) -> None:
        handler = _InboxHandler(mock_beestgraph_settings)
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/vault/inbox/article.md"
        with patch("src.pipeline.watcher._handle_new_file") as mock_handle:
            handler.on_created(event)
            mock_handle.assert_called_once()
            call_path = mock_handle.call_args[0][0]
            assert str(call_path).endswith("article.md")
