"""Watchdog-based daemon that monitors the vault inbox for new markdown files.

On detecting a new ``.md`` file the watcher:
1. Parses the file (frontmatter, links, tags, URLs).
2. Runs the processor for entity extraction / categorisation.
3. Ingests the parsed result into FalkorDB.
4. Moves the file to its proper vault location based on topic.

CLI entry point: ``python -m src.pipeline.watcher``
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import click
import structlog
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.config import BeestgraphSettings, load_settings
from src.pipeline.ingester import GraphIngester
from src.pipeline.markdown_parser import ParsedDocument, parse_file
from src.pipeline.processor import process_document

logger = structlog.get_logger(__name__)


def _resolve_destination(doc: ParsedDocument, settings: BeestgraphSettings) -> Path:
    """Determine where to move a processed document inside the vault.

    The target directory is derived from the first topic in the frontmatter
    (e.g. ``technology/ai-ml`` -> ``knowledge/technology/ai-ml/``).  Falls
    back to the ``knowledge/`` root when no topic is present.

    Args:
        doc: The parsed document with metadata.
        settings: Application settings (for vault paths).

    Returns:
        Absolute destination path for the file.
    """
    vault = Path(settings.vault.path)
    topics = doc.metadata.get("topics", [])
    if isinstance(topics, list) and topics:
        topic_dir = str(topics[0]).replace(" ", "-").lower()
    else:
        topic_dir = ""

    dest_dir = vault / settings.vault.knowledge_dir / topic_dir
    return dest_dir / Path(doc.path).name


def _handle_new_file(filepath: Path, settings: BeestgraphSettings) -> None:
    """Parse, process, ingest, and relocate a single inbox markdown file.

    Args:
        filepath: Absolute path to the new ``.md`` file.
        settings: Loaded application settings.
    """
    start = time.monotonic()
    vault_root = Path(settings.vault.path)

    try:
        doc = parse_file(filepath, vault_root=vault_root)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("parse_failed", path=str(filepath), error=str(exc))
        return

    # Run AI / fallback processing to enrich metadata
    doc = process_document(doc, enable_llm=settings.enable_llm_processing)

    # Ingest into FalkorDB
    try:
        ingester = GraphIngester(settings.falkordb)
        ingester.ingest_parsed_document(doc)
    except ConnectionError as exc:
        logger.error("ingest_failed", path=doc.path, error=str(exc))
        return

    # Move to proper vault location
    dest = _resolve_destination(doc, settings)
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(filepath), str(dest))
        logger.info("file_moved", src=str(filepath), dest=str(dest))
    except OSError as exc:
        logger.error("file_move_failed", src=str(filepath), dest=str(dest), error=str(exc))

    elapsed_ms = (time.monotonic() - start) * 1000
    logger.info(
        "inbox_item_processed",
        path=doc.path,
        dest=str(dest),
        elapsed_ms=round(elapsed_ms, 1),
    )


class _InboxHandler(FileSystemEventHandler):
    """Watchdog handler that triggers processing on new .md files."""

    def __init__(self, settings: BeestgraphSettings) -> None:
        super().__init__()
        self._settings = settings

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events in the inbox directory."""
        if event.is_directory:
            return
        filepath = Path(str(event.src_path))
        if filepath.suffix.lower() != ".md":
            return
        logger.info("new_inbox_file", path=str(filepath))
        _handle_new_file(filepath, self._settings)


def run_watcher(settings: BeestgraphSettings) -> None:
    """Start the blocking watchdog observer loop.

    Args:
        settings: Loaded application settings.
    """
    inbox = Path(settings.vault.path) / settings.vault.inbox_dir
    inbox.mkdir(parents=True, exist_ok=True)

    handler = _InboxHandler(settings)
    observer = Observer()
    observer.schedule(handler, str(inbox), recursive=False)
    observer.start()
    logger.info("watcher_started", inbox=str(inbox))

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        logger.info("watcher_stopping")
    finally:
        observer.stop()
        observer.join()
        logger.info("watcher_stopped")


@click.command("watch")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to beestgraph.yml config file.",
)
def main(config_path: Path | None) -> None:
    """Start the vault inbox watcher daemon."""
    settings = load_settings(config_path)
    run_watcher(settings)


if __name__ == "__main__":
    main()
