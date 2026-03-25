"""Vault filesystem operations for beestgraph.

Handles directory creation, file relocation, inbox listing, and vault
statistics.  All functions are synchronous since local filesystem I/O is
fast and does not benefit from async overhead.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import structlog

from src.config import VaultSettings

logger = structlog.get_logger(__name__)

# Top-level starter topics from the taxonomy.  Used by ensure_vault_structure
# to pre-create ``07-resources/<topic>/`` directories.
_DEFAULT_TOPICS: list[str] = [
    "technology",
    "technology/programming",
    "technology/ai-ml",
    "technology/infrastructure",
    "technology/security",
    "technology/web",
    "science",
    "science/physics",
    "science/biology",
    "science/mathematics",
    "business",
    "business/startups",
    "business/finance",
    "business/marketing",
    "culture",
    "culture/books",
    "culture/film",
    "culture/music",
    "culture/history",
    "health",
    "health/fitness",
    "health/nutrition",
    "health/mental-health",
    "personal",
    "personal/journal",
    "personal/goals",
    "personal/relationships",
    "meta",
    "meta/pkm",
    "meta/tools",
    "meta/workflows",
]


def ensure_vault_structure(settings: VaultSettings) -> None:
    """Create all expected vault directories if they do not already exist.

    Creates numbered lifecycle directories (``00-meta`` through
    ``09-attachments``), topic sub-trees under ``07-resources/``,
    and the MOC / template / dashboard folders under ``00-meta/``.

    Args:
        settings: Vault path configuration.
    """
    vault = Path(settings.path)

    # Numbered lifecycle directories
    for dir_attr in (
        "meta_dir",
        "inbox_dir",
        "queue_dir",
        "fleeting_dir",
        "daily_dir",
        "projects_dir",
        "areas_dir",
        "resources_dir",
        "archive_dir",
        "attachments_dir",
    ):
        (vault / getattr(settings, dir_attr)).mkdir(parents=True, exist_ok=True)

    # Meta sub-directories
    (vault / settings.templates_dir).mkdir(parents=True, exist_ok=True)
    (vault / settings.mocs_dir).mkdir(parents=True, exist_ok=True)
    (vault / settings.meta_dir / "dashboards").mkdir(parents=True, exist_ok=True)
    (vault / settings.meta_dir / "settings").mkdir(parents=True, exist_ok=True)

    # Topic tree under resources
    resources = vault / settings.resources_dir
    for topic in _DEFAULT_TOPICS:
        (resources / topic).mkdir(parents=True, exist_ok=True)

    # Archive sub-directories
    (vault / settings.archive_dir / "projects").mkdir(parents=True, exist_ok=True)
    (vault / settings.archive_dir / "rejected").mkdir(parents=True, exist_ok=True)

    logger.info("vault_structure_ensured", vault=str(vault))


def resolve_destination(
    doc_path: str,
    topic: str,
    settings: VaultSettings,
    content_type: str = "",
) -> Path:
    """Determine where a processed document should live in the vault.

    The file is placed under ``07-resources/<topic>/`` using its original
    filename.  The *topic* string may contain slashes for sub-topics
    (e.g. ``technology/ai-ml``).  It is normalised to lowercase with
    spaces replaced by hyphens.

    Args:
        doc_path: Original filename or path of the document (only the
            basename is used).
        topic: Topic slug such as ``"technology/ai-ml"``.  An empty
            string places the file directly in the resources root.
        settings: Vault path configuration.
        content_type: Optional content type (unused for now; reserved
            for future type-based sub-directories).

    Returns:
        Absolute destination ``Path`` for the file.
    """
    vault = Path(settings.path)
    topic_dir = topic.strip().replace(" ", "-").lower() if topic else ""
    dest_dir = vault / settings.resources_dir / topic_dir
    return dest_dir / Path(doc_path).name


def move_to_resources(src: Path, topic: str, settings: VaultSettings) -> Path:
    """Move a file into the resources directory under the given topic.

    Creates intermediate directories as needed.  If a file with the same
    name already exists at the destination, the move will overwrite it
    (idempotency requirement).

    Args:
        src: Absolute path to the source file.
        topic: Topic slug (e.g. ``"science/physics"``).
        settings: Vault path configuration.

    Returns:
        Absolute ``Path`` of the file at its new location.

    Raises:
        FileNotFoundError: If *src* does not exist.
        OSError: If the move fails for filesystem-level reasons.
    """
    if not src.is_file():
        raise FileNotFoundError(f"Source file not found: {src}")

    dest = resolve_destination(str(src), topic, settings)
    dest.parent.mkdir(parents=True, exist_ok=True)

    shutil.move(str(src), str(dest))
    logger.info("file_moved", src=str(src), dest=str(dest), topic=topic)
    return dest


# Keep the old name as an alias for backwards compatibility.
move_to_knowledge = move_to_resources


def list_inbox(settings: VaultSettings) -> list[Path]:
    """Return a sorted list of ``.md`` files in the vault inbox.

    Args:
        settings: Vault path configuration.

    Returns:
        List of absolute ``Path`` objects for each markdown file,
        sorted alphabetically by filename.
    """
    inbox = Path(settings.path) / settings.inbox_dir
    if not inbox.is_dir():
        logger.warning("inbox_dir_missing", path=str(inbox))
        return []
    return sorted(inbox.glob("*.md"))


def get_vault_stats(settings: VaultSettings) -> dict[str, int]:
    """Count ``.md`` files in each top-level vault section.

    Args:
        settings: Vault path configuration.

    Returns:
        Dict mapping directory names to the number of markdown files
        they contain (recursively).
    """
    vault = Path(settings.path)
    sections = [
        settings.inbox_dir,
        settings.queue_dir,
        settings.fleeting_dir,
        settings.daily_dir,
        settings.projects_dir,
        settings.areas_dir,
        settings.resources_dir,
        settings.archive_dir,
    ]

    stats: dict[str, int] = {}
    for section in sections:
        section_path = vault / section
        if section_path.is_dir():
            stats[section] = sum(1 for _ in section_path.rglob("*.md"))
        else:
            stats[section] = 0

    stats["total"] = sum(stats.values())
    logger.debug("vault_stats", **stats)
    return stats
