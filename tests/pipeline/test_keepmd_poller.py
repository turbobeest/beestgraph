"""Tests for src.pipeline.keepmd_poller — keep.md inbox polling and processing."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.config import BeestgraphSettings, KeepMDSettings
from src.pipeline.keepmd_poller import (
    _fetch_inbox,
    _slugify,
    _write_markdown,
    poll_once,
)

# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------


class TestSlugify:
    """Tests for the filename slug generator."""

    def test_basic_title(self) -> None:
        assert _slugify("Hello World") == "hello-world"

    def test_strips_special_chars(self) -> None:
        assert _slugify("What's New? (2026)") == "whats-new-2026"

    def test_max_length(self) -> None:
        long_title = "A" * 100
        assert len(_slugify(long_title, max_len=60)) <= 60

    def test_collapses_multiple_hyphens(self) -> None:
        assert _slugify("foo---bar") == "foo-bar"

    def test_empty_string(self) -> None:
        assert _slugify("") == ""

    def test_preserves_numbers(self) -> None:
        assert _slugify("Article 42 Redux") == "article-42-redux"


# ---------------------------------------------------------------------------
# _fetch_inbox
# ---------------------------------------------------------------------------


class TestFetchInbox:
    """Tests for the keep.md inbox API call."""

    @pytest.mark.asyncio
    async def test_returns_items_list(self) -> None:
        items = [{"id": "1", "title": "Item 1"}, {"id": "2", "title": "Item 2"}]
        mock_response = MagicMock()
        mock_response.json.return_value = items
        mock_response.raise_for_status = MagicMock()

        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)

        settings = KeepMDSettings(api_url="https://keep.md/api", api_key="test-key")
        result = await _fetch_inbox(client, settings)
        assert len(result) == 2
        assert result[0]["id"] == "1"

    @pytest.mark.asyncio
    async def test_handles_dict_response_with_items_key(self) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": [{"id": "1"}], "total": 1}
        mock_response.raise_for_status = MagicMock()

        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)

        settings = KeepMDSettings(api_url="https://keep.md/api", api_key="")
        result = await _fetch_inbox(client, settings)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_sends_auth_header_when_api_key_set(self) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)

        settings = KeepMDSettings(api_url="https://keep.md/api", api_key="secret")
        await _fetch_inbox(client, settings)

        call_kwargs = client.get.call_args
        headers = call_kwargs.kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer secret"

    @pytest.mark.asyncio
    async def test_no_auth_header_without_api_key(self) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)

        settings = KeepMDSettings(api_url="https://keep.md/api", api_key="")
        await _fetch_inbox(client, settings)

        call_kwargs = client.get.call_args
        headers = call_kwargs.kwargs.get("headers", {})
        assert "Authorization" not in headers


# ---------------------------------------------------------------------------
# _write_markdown
# ---------------------------------------------------------------------------


class TestWriteMarkdown:
    """Tests for writing keep.md items as vault markdown files."""

    def test_creates_file_with_frontmatter(self, tmp_vault: Path) -> None:
        item = {
            "title": "Test Article",
            "url": "https://example.com/test",
            "content": "Article body text.",
        }
        filepath = _write_markdown(item, tmp_vault / "inbox")
        assert filepath.exists()
        text = filepath.read_text(encoding="utf-8")
        assert "title:" in text
        assert "source_url:" in text
        assert "source_type: keepmd" in text
        assert "Article body text." in text

    def test_filename_is_slugified(self, tmp_vault: Path) -> None:
        item = {"title": "My Great Article!", "content": "Body."}
        filepath = _write_markdown(item, tmp_vault / "inbox")
        assert filepath.name == "my-great-article.md"

    def test_avoids_overwriting_existing(self, tmp_vault: Path) -> None:
        inbox = tmp_vault / "inbox"
        item = {"title": "Duplicate", "content": "First."}
        first = _write_markdown(item, inbox)

        item2 = {"title": "Duplicate", "content": "Second."}
        second = _write_markdown(item2, inbox)

        assert first != second
        assert first.exists()
        assert second.exists()
        assert "duplicate-1.md" in second.name

    def test_untitled_item(self, tmp_vault: Path) -> None:
        item = {"content": "No title here."}
        filepath = _write_markdown(item, tmp_vault / "inbox")
        assert filepath.exists()
        text = filepath.read_text(encoding="utf-8")
        assert 'title: "Untitled"' in text

    def test_creates_inbox_dir_if_missing(self, tmp_path: Path) -> None:
        inbox = tmp_path / "new-inbox"
        item = {"title": "Test", "content": "Body."}
        filepath = _write_markdown(item, inbox)
        assert inbox.is_dir()
        assert filepath.exists()


# ---------------------------------------------------------------------------
# poll_once (end-to-end with mocks)
# ---------------------------------------------------------------------------


class TestPollOnce:
    """Tests for the full polling cycle."""

    @pytest.mark.asyncio
    async def test_processes_items_end_to_end(
        self, mock_beestgraph_settings: BeestgraphSettings, tmp_vault: Path
    ) -> None:
        inbox_items = [{"id": "item-1", "title": "Test Item"}]
        full_item = {
            "id": "item-1",
            "title": "Test Item",
            "url": "https://example.com/item-1",
            "content": "Full item content for processing.",
        }

        mock_response_inbox = MagicMock()
        mock_response_inbox.json.return_value = inbox_items
        mock_response_inbox.raise_for_status = MagicMock()

        mock_response_item = MagicMock()
        mock_response_item.json.return_value = full_item
        mock_response_item.raise_for_status = MagicMock()

        mock_response_done = MagicMock()
        mock_response_done.raise_for_status = MagicMock()

        async def mock_get(url, **kwargs):
            if "items/" in url and "item-1" in url:
                return mock_response_item
            return mock_response_inbox

        async def mock_patch(url, **kwargs):
            return mock_response_done

        mock_ingester = MagicMock()

        with (
            patch("src.pipeline.keepmd_poller.httpx.AsyncClient") as mock_client_cls,
            patch("src.pipeline.keepmd_poller.GraphIngester", return_value=mock_ingester),
            patch("src.pipeline.keepmd_poller.process_document", side_effect=lambda d, **kw: d),
        ):
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(side_effect=mock_get)
            client_instance.patch = AsyncMock(side_effect=mock_patch)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            count = await poll_once(mock_beestgraph_settings)

        assert count == 1
        mock_ingester.ingest_parsed_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_items_without_id(
        self, mock_beestgraph_settings: BeestgraphSettings
    ) -> None:
        inbox_items = [{"title": "No ID Item"}]  # Missing "id" key

        mock_response = MagicMock()
        mock_response.json.return_value = inbox_items
        mock_response.raise_for_status = MagicMock()

        mock_ingester = MagicMock()

        with (
            patch("src.pipeline.keepmd_poller.httpx.AsyncClient") as mock_client_cls,
            patch("src.pipeline.keepmd_poller.GraphIngester", return_value=mock_ingester),
        ):
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            count = await poll_once(mock_beestgraph_settings)

        assert count == 0
        mock_ingester.ingest_parsed_document.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_zero_on_fetch_failure(
        self, mock_beestgraph_settings: BeestgraphSettings
    ) -> None:
        mock_ingester = MagicMock()

        with (
            patch("src.pipeline.keepmd_poller.httpx.AsyncClient") as mock_client_cls,
            patch("src.pipeline.keepmd_poller.GraphIngester", return_value=mock_ingester),
        ):
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Server Error",
                    request=MagicMock(),
                    response=MagicMock(status_code=500),
                )
            )
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            count = await poll_once(mock_beestgraph_settings)

        assert count == 0
