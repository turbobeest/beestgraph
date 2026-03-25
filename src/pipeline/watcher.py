"""Watchdog-based daemon that monitors the vault inbox for new markdown files.

On detecting a new ``.md`` file the watcher:
1. Parses the file (frontmatter, links, tags, URLs).
2. AI pre-classifies the content (type, topic, tags, quality, summary).
3. Moves the file to the qualification queue for user review.
4. Writes a notification JSON for the Telegram bot to pick up.

When qualification is disabled, falls back to the legacy direct-ingest path.

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
from src.pipeline.classifier import classify_document
from src.pipeline.formatter import format_on_capture
from src.pipeline.markdown_parser import ParsedDocument, parse_file
from src.pipeline.qualification import QualificationQueue

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Legacy direct-ingest path (used when qualification is disabled)
# ---------------------------------------------------------------------------


def _resolve_destination(doc: ParsedDocument, settings: BeestgraphSettings) -> Path:
    """Determine where to move a processed document inside the vault.

    The target directory is derived from the first topic in the frontmatter
    (e.g. ``technology/ai-ml`` -> ``07-resources/technology/ai-ml/``).  Falls
    back to the ``07-resources/`` root when no topic is present.

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

    dest_dir = vault / settings.vault.resources_dir / topic_dir
    return dest_dir / Path(doc.path).name


def _handle_new_file_legacy(filepath: Path, settings: BeestgraphSettings) -> None:
    """Legacy path: parse, process, ingest, and relocate directly.

    Used when qualification is disabled.

    Args:
        filepath: Absolute path to the new ``.md`` file.
        settings: Loaded application settings.
    """
    from src.pipeline.ingester import GraphIngester
    from src.pipeline.processor import process_document

    start = time.monotonic()
    vault_root = Path(settings.vault.path)

    try:
        doc = parse_file(filepath, vault_root=vault_root)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("parse_failed", path=str(filepath), error=str(exc))
        return

    # Apply capture formatting and write back
    formatted_body = format_on_capture(doc.content, title=doc.title)
    if formatted_body != doc.content:
        import frontmatter as fm

        raw = filepath.read_text(encoding="utf-8")
        post = fm.loads(raw)
        post.content = formatted_body
        filepath.write_text(fm.dumps(post), encoding="utf-8")
        logger.info("capture_formatted", path=str(filepath))
        doc = parse_file(filepath, vault_root=vault_root)

    doc = process_document(doc, enable_llm=settings.enable_llm_processing)

    try:
        ingester = GraphIngester(settings.falkordb)
        ingester.ingest_parsed_document(doc)
    except ConnectionError as exc:
        logger.error("ingest_failed", path=doc.path, error=str(exc))
        return

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


# ---------------------------------------------------------------------------
# Qualification queue path (default)
# ---------------------------------------------------------------------------


def _handle_new_file(filepath: Path, settings: BeestgraphSettings) -> None:
    """Parse, classify, and route a new inbox file to the qualification queue.

    Steps:
    1. Parse the markdown file.
    2. AI pre-classify (content type, topic, tags, quality, summary).
    3. Add to the qualification queue.
    4. Write a notification JSON for the Telegram bot.

    Args:
        filepath: Absolute path to the new ``.md`` file.
        settings: Loaded application settings.
    """
    # Fall back to legacy path when qualification is disabled
    if not settings.qualification.enabled:
        _handle_new_file_legacy(filepath, settings)
        return

    start = time.monotonic()
    vault_root = Path(settings.vault.path)

    # 1. Parse the file
    try:
        doc = parse_file(filepath, vault_root=vault_root)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("parse_failed", path=str(filepath), error=str(exc))
        return

    # 1b. Apply capture formatting and write back
    formatted_body = format_on_capture(doc.content, title=doc.title)
    if formatted_body != doc.content:
        import frontmatter as fm

        raw = filepath.read_text(encoding="utf-8")
        post = fm.loads(raw)
        post.content = formatted_body
        filepath.write_text(fm.dumps(post), encoding="utf-8")
        logger.info("capture_formatted", path=str(filepath))
        # Re-parse to pick up any changes
        doc = parse_file(filepath, vault_root=vault_root)

    # 1c. Security scan — detect PII, API keys, financial data
    from src.pipeline.security_scanner import scan_content

    scan_result = scan_content(doc.content)
    force_private = scan_result.forced_private
    if scan_result.has_findings:
        logger.warning(
            "security_scan_alert",
            path=str(filepath),
            findings=len(scan_result.findings),
            forced_private=force_private,
            summary=scan_result.summary,
        )

    # 2. AI pre-classify
    try:
        recommendation = classify_document(doc, enable_llm=settings.enable_llm_processing)
    except Exception as exc:
        logger.error("classification_failed", path=str(filepath), error=str(exc))
        # Use safe defaults so we never lose a file
        recommendation = {
            "content_type": "article",
            "topic": "",
            "tags": sorted(doc.tags)[:10],
            "quality": "medium",
            "summary": "",
        }

    # Override visibility if security scan found sensitive data
    if force_private:
        recommendation["visibility"] = "private"
        recommendation["security_findings"] = scan_result.summary

    # 3. Add to qualification queue
    queue = QualificationQueue(
        vault_path=vault_root,
        queue_dir=settings.vault.queue_dir,
    )
    try:
        item = queue.add_item(filepath, recommendation)
    except (FileNotFoundError, OSError) as exc:
        logger.error("queue_add_failed", path=str(filepath), error=str(exc))
        return

    # 4. Write notification for Telegram bot
    if settings.qualification.notify_telegram:
        try:
            queue.write_notification(item)
        except OSError as exc:
            logger.warning("notification_write_failed", path=str(filepath), error=str(exc))

    elapsed_ms = (time.monotonic() - start) * 1000
    logger.info(
        "inbox_item_queued",
        path=doc.path,
        queue_path=str(item.path),
        content_type=recommendation.get("content_type"),
        topic=recommendation.get("topic"),
        elapsed_ms=round(elapsed_ms, 1),
    )


# ---------------------------------------------------------------------------
# Watchdog handler and runner
# ---------------------------------------------------------------------------


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

    # Ensure queue directory exists at startup
    if settings.qualification.enabled:
        queue_path = Path(settings.vault.path) / settings.vault.queue_dir
        queue_path.mkdir(parents=True, exist_ok=True)
        logger.info("qualification_queue_ready", path=str(queue_path))

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
