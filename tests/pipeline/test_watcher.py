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
    """Tests for vault destination routing based on topics."""

    def test_uses_first_topic_as_subdirectory(
        self, mock_beestgraph_settings: BeestgraphSettings
    ) -> None:
        doc = ParsedDocument(
            path="inbox/article.md",
            title="Test",
            content="Body",
            metadata={"topics": ["technology/ai-ml"]},
        )
        dest = _resolve_destination(doc, mock_beestgraph_settings)
        assert "technology/ai-ml" in str(dest)
        assert dest.name == "article.md"

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
        expected = vault / "07-resources" / "article.md"
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
        expected = vault / "07-resources" / "article.md"
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
# _handle_new_file (qualification-enabled path)
# ---------------------------------------------------------------------------


class TestHandleNewFile:
    """Tests for the new file handler with qualification queue."""

    def test_routes_through_qualification_when_enabled(
        self,
        tmp_vault: Path,
        mock_beestgraph_settings: BeestgraphSettings,
    ) -> None:
        """When qualification is enabled, file goes to queue, not permanent storage."""
        filepath = tmp_vault / "01-inbox" / "test-article.md"
        filepath.write_text(
            "---\ntitle: Test Article\ntopics:\n  - meta/pkm\n---\n\nSome content.\n",
            encoding="utf-8",
        )
        queue_dir = tmp_vault / mock_beestgraph_settings.vault.queue_dir
        queue_dir.mkdir(parents=True, exist_ok=True)

        mock_queue = MagicMock()
        mock_queue.add_item.return_value = MagicMock(title="Test Article")

        with (
            patch(
                "src.pipeline.watcher.classify_document",
                return_value={
                    "type": "article",
                    "topic": "meta/pkm",
                    "tags": ["test"],
                    "confidence": 0.5,
                    "summary": "Test summary.",
                },
            ),
            patch("src.pipeline.watcher.QualificationQueue", return_value=mock_queue),
        ):
            _handle_new_file(filepath, mock_beestgraph_settings)

        mock_queue.add_item.assert_called_once()

    def test_handles_parse_failure_gracefully(
        self,
        tmp_vault: Path,
        mock_beestgraph_settings: BeestgraphSettings,
    ) -> None:
        """Parse failure should not crash — file stays in inbox."""
        filepath = tmp_vault / "01-inbox" / "missing.md"
        # File doesn't exist
        _handle_new_file(filepath, mock_beestgraph_settings)
        # Should not raise

    def test_handles_classification_failure(
        self,
        tmp_vault: Path,
        mock_beestgraph_settings: BeestgraphSettings,
    ) -> None:
        """Classification failure should use safe defaults."""
        filepath = tmp_vault / "01-inbox" / "test.md"
        filepath.write_text("---\ntitle: Test\n---\nContent.\n", encoding="utf-8")
        queue_dir = tmp_vault / mock_beestgraph_settings.vault.queue_dir
        queue_dir.mkdir(parents=True, exist_ok=True)

        mock_queue = MagicMock()
        mock_queue.add_item.return_value = MagicMock(title="Test")

        with (
            patch("src.pipeline.watcher.classify_document", side_effect=RuntimeError("fail")),
            patch("src.pipeline.watcher.QualificationQueue", return_value=mock_queue),
        ):
            _handle_new_file(filepath, mock_beestgraph_settings)

        # Should still add to queue with fallback classification
        mock_queue.add_item.assert_called_once()

    def test_falls_back_to_legacy_when_qualification_disabled(
        self,
        tmp_vault: Path,
        mock_beestgraph_settings: BeestgraphSettings,
    ) -> None:
        """When qualification is disabled, uses legacy direct-ingest path."""
        mock_beestgraph_settings.qualification.enabled = False
        filepath = tmp_vault / "01-inbox" / "test.md"
        filepath.write_text(
            "---\ntitle: Test\ntopics:\n  - meta/pkm\n---\nContent.\n",
            encoding="utf-8",
        )

        with (
            patch(
                "src.pipeline.processor.process_document",
                return_value=ParsedDocument(
                    path="test.md",
                    title="Test",
                    content="Content.",
                    metadata={"topics": ["meta/pkm"]},
                ),
            ),
            patch("src.pipeline.ingester.GraphIngester") as mock_ingester_cls,
        ):
            mock_ingester_cls.return_value = MagicMock()
            _handle_new_file(filepath, mock_beestgraph_settings)
            mock_ingester_cls.return_value.ingest_parsed_document.assert_called_once()


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
