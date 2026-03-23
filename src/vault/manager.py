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
# to pre-create ``knowledge/<topic>/`` directories.
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

# PARA directories that live at the vault root.
_PARA_DIRS: list[str] = ["projects", "areas", "resources", "archives"]


def ensure_vault_structure(settings: VaultSettings) -> None:
    """Create all expected vault directories if they do not already exist.

    Creates the inbox, knowledge/<topic>, PARA directories (projects, areas,
    resources, archives), and the templates directory.

    Args:
        settings: Vault path configuration.
    """
    vault = Path(settings.path)

    # Inbox
    (vault / settings.inbox_dir).mkdir(parents=True, exist_ok=True)

    # Knowledge topic tree
    knowledge = vault / settings.knowledge_dir
    for topic in _DEFAULT_TOPICS:
        (knowledge / topic).mkdir(parents=True, exist_ok=True)

    # PARA directories
    for para_dir in _PARA_DIRS:
        (vault / para_dir).mkdir(parents=True, exist_ok=True)

    # Templates
    (vault / settings.templates_dir).mkdir(parents=True, exist_ok=True)

    logger.info("vault_structure_ensured", vault=str(vault))


def resolve_destination(doc_path: str, topic: str, settings: VaultSettings) -> Path:
    """Determine where a processed document should live in the vault.

    The file is placed under ``knowledge/<topic>/`` using its original
    filename.  The *topic* string may contain slashes for sub-topics
    (e.g. ``technology/ai-ml``).  It is normalised to lowercase with
    spaces replaced by hyphens.

    Args:
        doc_path: Original filename or path of the document (only the
            basename is used).
        topic: Topic slug such as ``"technology/ai-ml"``.  An empty
            string places the file directly in the knowledge root.
        settings: Vault path configuration.

    Returns:
        Absolute destination ``Path`` for the file.
    """
    vault = Path(settings.path)
    topic_dir = topic.strip().replace(" ", "-").lower() if topic else ""
    dest_dir = vault / settings.knowledge_dir / topic_dir
    return dest_dir / Path(doc_path).name


def move_to_knowledge(src: Path, topic: str, settings: VaultSettings) -> Path:
    """Move a file into the knowledge directory under the given topic.

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
        Dict mapping directory names (``inbox``, ``knowledge``,
        ``projects``, ``areas``, ``resources``, ``archives``) to
        the number of markdown files they contain (recursively).
    """
    vault = Path(settings.path)
    sections = [
        settings.inbox_dir,
        settings.knowledge_dir,
        *_PARA_DIRS,
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
