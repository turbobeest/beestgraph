"""Full-vault incremental graph sync daemon.

Monitors ``~/vault/**/*.md`` (excluding ``01-inbox/``, ``09-attachments/``,
``.git/``, ``.obsidian/``) and syncs frontmatter changes to FalkorDB on
every file modification.  Uses a 2-second debounce to coalesce rapid saves
from Obsidian autosave.

This is distinct from ``src/pipeline/watcher.py`` which monitors only
``01-inbox/`` and runs the full capture pipeline.

CLI entry point: ``python -m src.automation.watcher``
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import click
import structlog
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.config import BeestgraphSettings, load_settings

logger = structlog.get_logger(__name__)

_IGNORE_DIRS = {"01-inbox", "09-attachments", ".git", ".obsidian", ".trash"}
_DEBOUNCE_SECONDS = 2.0


class _DebouncedSyncHandler(FileSystemEventHandler):
    """Watchdog handler that debounces rapid file changes before syncing."""

    def __init__(self, settings: BeestgraphSettings) -> None:
        super().__init__()
        self._settings = settings
        self._pending: dict[str, float] = {}
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    def _should_ignore(self, path: Path) -> bool:
        """Check if the path is in an ignored directory."""
        vault = Path(self._settings.vault.path)
        try:
            rel = path.relative_to(vault)
        except ValueError:
            return True
        return any(part in _IGNORE_DIRS for part in rel.parts)

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        filepath = Path(str(event.src_path))
        if filepath.suffix.lower() != ".md":
            return
        if self._should_ignore(filepath):
            return

        with self._lock:
            self._pending[str(filepath)] = time.monotonic()
            # Reset debounce timer
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(_DEBOUNCE_SECONDS, self._flush)
            self._timer.daemon = True
            self._timer.start()

    def on_created(self, event: FileSystemEvent) -> None:
        self.on_modified(event)

    def _flush(self) -> None:
        """Process all pending file changes after debounce period."""
        with self._lock:
            paths = list(self._pending.keys())
            self._pending.clear()

        for filepath in paths:
            self._sync_file(Path(filepath))

    def _sync_file(self, filepath: Path) -> None:
        """Parse frontmatter and sync changed fields to FalkorDB."""
        from src.pipeline.markdown_parser import parse_file

        vault_root = Path(self._settings.vault.path)
        try:
            doc = parse_file(filepath, vault_root=vault_root)
        except (FileNotFoundError, ValueError) as exc:
            logger.debug("vault_sync_parse_skip", path=str(filepath), error=str(exc))
            return

        meta = doc.metadata
        uid = str(meta.get("uid", ""))
        path = doc.path

        if not uid and not path:
            return

        try:
            from falkordb import FalkorDB

            db = FalkorDB(
                host=self._settings.falkordb.host,
                port=self._settings.falkordb.port,
                password=self._settings.falkordb.password or None,
            )
            graph = db.select_graph(self._settings.falkordb.graph_name)

            params: dict = {
                "title": doc.title,
                "status": str(meta.get("status", "")),
                "importance": meta.get("importance", 3),
                "version": meta.get("version", 1),
                "modified": str(meta.get("dates", {}).get("modified", ""))
                if isinstance(meta.get("dates"), dict)
                else "",
            }

            if uid:
                graph.query(
                    "MATCH (d:Document {uid: $uid}) "
                    "SET d.title = $title, d.status = $status, "
                    "d.importance = $importance, d.version = $version, "
                    "d.modified = $modified",
                    {"uid": uid, **params},
                )
            else:
                graph.query(
                    "MATCH (d:Document {path: $path}) "
                    "SET d.title = $title, d.status = $status, "
                    "d.importance = $importance, d.version = $version, "
                    "d.modified = $modified",
                    {"path": path, **params},
                )

            logger.info("vault_synced", path=str(filepath), uid=uid or "(path)")
        except Exception as exc:
            logger.error("vault_sync_failed", path=str(filepath), error=str(exc))


def run_vault_watcher(settings: BeestgraphSettings) -> None:
    """Start the blocking vault sync observer loop."""
    vault = Path(settings.vault.path)
    if not vault.is_dir():
        logger.error("vault_not_found", path=str(vault))
        return

    handler = _DebouncedSyncHandler(settings)
    observer = Observer()
    observer.schedule(handler, str(vault), recursive=True)
    observer.start()
    logger.info("vault_sync_started", vault=str(vault), debounce=_DEBOUNCE_SECONDS)

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        logger.info("vault_sync_stopping")
    finally:
        observer.stop()
        observer.join()
        logger.info("vault_sync_stopped")


@click.command("vault-sync")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to beestgraph.yml config file.",
)
def main(config_path: Path | None) -> None:
    """Start the vault → FalkorDB incremental sync daemon."""
    settings = load_settings(config_path)
    run_vault_watcher(settings)


if __name__ == "__main__":
    main()
