"""Async poller for keep.md inbox items.

Fetches unprocessed items from keep.md via its REST API, writes each as a
markdown file with proper frontmatter into the vault inbox, ingests into
FalkorDB, and marks the item as done.

CLI entry point: ``python -m src.pipeline.keepmd_poller``
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import click
import httpx
import structlog

from src.config import BeestgraphSettings, KeepMDSettings, load_settings
from src.pipeline.ingester import GraphIngester
from src.pipeline.markdown_parser import parse_file
from src.pipeline.processor import process_document

logger = structlog.get_logger(__name__)

_FRONTMATTER_TEMPLATE = """---
title: "{title}"
source_url: "{source_url}"
source_type: keepmd
date_captured: {date_captured}
date_processed: {date_processed}
status: inbox
---

{content}
"""


def _slugify(text: str, max_len: int = 60) -> str:
    """Convert text to a filesystem-safe slug.

    Args:
        text: Arbitrary title text.
        max_len: Maximum slug length.

    Returns:
        Lowercased, hyphen-separated slug string.
    """
    slug = text.lower().strip()
    safe_chars: list[str] = []
    for ch in slug:
        if ch.isalnum():
            safe_chars.append(ch)
        elif ch in (" ", "-", "_"):
            safe_chars.append("-")
    result = "-".join(part for part in "".join(safe_chars).split("-") if part)
    return result[:max_len]


async def _fetch_inbox(client: httpx.AsyncClient, settings: KeepMDSettings) -> list[dict]:
    """Retrieve the list of inbox items from keep.md.

    Args:
        client: Configured async HTTP client.
        settings: keep.md API configuration.

    Returns:
        List of item dicts from the API response.

    Raises:
        httpx.HTTPStatusError: On non-2xx response.
    """
    headers = {"Authorization": f"Bearer {settings.api_key}"} if settings.api_key else {}
    url = f"{settings.api_url}/items"
    resp = await client.get(url, params={"status": "inbox"}, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    items: list[dict] = data if isinstance(data, list) else data.get("items", [])
    logger.info("keepmd_inbox_fetched", count=len(items))
    return items


async def _get_item_content(
    client: httpx.AsyncClient, settings: KeepMDSettings, item_id: str
) -> dict:
    """Fetch the full content of a single keep.md item.

    Args:
        client: Configured async HTTP client.
        settings: keep.md API configuration.
        item_id: Unique keep.md item identifier.

    Returns:
        Full item dict including content.
    """
    headers = {"Authorization": f"Bearer {settings.api_key}"} if settings.api_key else {}
    resp = await client.get(f"{settings.api_url}/items/{item_id}", headers=headers)
    resp.raise_for_status()
    return resp.json()


async def _mark_done(client: httpx.AsyncClient, settings: KeepMDSettings, item_id: str) -> None:
    """Mark a keep.md item as processed / done.

    Args:
        client: Configured async HTTP client.
        settings: keep.md API configuration.
        item_id: Unique keep.md item identifier.
    """
    headers = {"Authorization": f"Bearer {settings.api_key}"} if settings.api_key else {}
    resp = await client.patch(
        f"{settings.api_url}/items/{item_id}",
        json={"status": "done"},
        headers=headers,
    )
    resp.raise_for_status()
    logger.debug("keepmd_item_marked_done", item_id=item_id)


def _write_markdown(item: dict, vault_inbox: Path) -> Path:
    """Write a keep.md item as a markdown file in the vault inbox.

    Args:
        item: Full item dict from keep.md API.
        vault_inbox: Absolute path to the vault inbox directory.

    Returns:
        Path to the newly written markdown file.
    """
    now = datetime.now(tz=UTC).isoformat()
    title = item.get("title", "Untitled")
    source_url = item.get("url", item.get("source_url", ""))
    content = item.get("content", item.get("body", ""))

    md_content = _FRONTMATTER_TEMPLATE.format(
        title=title.replace('"', '\\"'),
        source_url=source_url,
        date_captured=now,
        date_processed=now,
        content=content,
    )

    slug = _slugify(title) or _slugify(urlparse(source_url).path) or "untitled"
    filename = f"{slug}.md"
    filepath = vault_inbox / filename

    # Avoid overwriting existing files
    counter = 1
    while filepath.exists():
        filepath = vault_inbox / f"{slug}-{counter}.md"
        counter += 1

    vault_inbox.mkdir(parents=True, exist_ok=True)
    filepath.write_text(md_content, encoding="utf-8")
    logger.info("keepmd_item_written", path=str(filepath), title=title)
    return filepath


async def poll_once(settings: BeestgraphSettings) -> int:
    """Run a single polling cycle: fetch inbox, process, ingest, mark done.

    Args:
        settings: Loaded application settings.

    Returns:
        Number of items successfully processed.
    """
    vault_inbox = Path(settings.vault.path) / settings.vault.inbox_dir
    ingester = GraphIngester(settings.falkordb)
    processed_count = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            inbox_items = await _fetch_inbox(client, settings.keepmd)
        except httpx.HTTPError as exc:
            logger.error("keepmd_fetch_failed", error=str(exc))
            return 0

        for item_summary in inbox_items:
            item_id = str(item_summary.get("id", ""))
            if not item_id:
                logger.warning("keepmd_item_missing_id", item=item_summary)
                continue

            start = time.monotonic()
            try:
                item = await _get_item_content(client, settings.keepmd, item_id)
            except httpx.HTTPError as exc:
                logger.error("keepmd_get_item_failed", item_id=item_id, error=str(exc))
                continue

            # Write to vault
            filepath = _write_markdown(item, vault_inbox)

            # Parse and process
            try:
                vault_root = Path(settings.vault.path)
                doc = parse_file(filepath, vault_root=vault_root)
                doc = process_document(doc, enable_llm=settings.enable_llm_processing)
                ingester.ingest_parsed_document(doc)
            except (FileNotFoundError, ValueError, ConnectionError) as exc:
                logger.error(
                    "keepmd_process_failed", item_id=item_id, path=str(filepath), error=str(exc)
                )
                continue

            # Mark done in keep.md
            try:
                await _mark_done(client, settings.keepmd, item_id)
            except httpx.HTTPError as exc:
                logger.error("keepmd_mark_done_failed", item_id=item_id, error=str(exc))
                continue

            elapsed_ms = (time.monotonic() - start) * 1000
            processed_count += 1
            logger.info(
                "keepmd_item_processed",
                item_id=item_id,
                title=item.get("title", ""),
                elapsed_ms=round(elapsed_ms, 1),
            )

    logger.info("keepmd_poll_complete", processed=processed_count, total=len(inbox_items))
    return processed_count


@click.command("poll-keepmd")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to beestgraph.yml config file.",
)
def main(config_path: Path | None) -> None:
    """Run a single keep.md polling cycle."""
    settings = load_settings(config_path)
    count = asyncio.run(poll_once(settings))
    click.echo(f"Processed {count} items from keep.md inbox.")


if __name__ == "__main__":
    main()
