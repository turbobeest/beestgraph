"""Qualification queue for content review before permanent storage.

Manages the lifecycle of captured items as they move from inbox through
user review to permanent vault residency.  Items sit in ``~/vault/02-queue/``
with enriched frontmatter until approved, rejected, or auto-classified
after a configurable timeout.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import frontmatter
import structlog

from src.pipeline.formatter import format_on_qualify, validate_for_publication

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class QualificationItem:
    """An item in the qualification queue."""

    path: Path
    original_path: Path
    title: str
    source_url: str
    source_type: str
    captured_at: datetime

    # AI recommendation
    recommended_type: str
    recommended_topic: str
    recommended_tags: list[str]
    recommended_quality: str
    recommended_summary: str

    # User modifications
    user_type: str | None = None
    user_topic: str | None = None
    user_tags: list[str] | None = None
    user_quality: str | None = None
    user_notes: str = ""

    # Status
    status: str = "qualifying"
    deferred_until: datetime | None = None
    telegram_message_id: int | None = None

    @property
    def final_type(self) -> str:
        """Return the user-overridden or AI-recommended content type."""
        return self.user_type or self.recommended_type

    @property
    def final_topic(self) -> str:
        """Return the user-overridden or AI-recommended topic."""
        return self.user_topic or self.recommended_topic

    @property
    def final_tags(self) -> list[str]:
        """Return the user-overridden or AI-recommended tags."""
        return self.user_tags if self.user_tags is not None else self.recommended_tags

    @property
    def final_quality(self) -> str:
        """Return the user-overridden or AI-recommended quality."""
        return self.user_quality or self.recommended_quality


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(tz=UTC).isoformat()


def _parse_datetime(value: object) -> datetime:
    """Parse a datetime from frontmatter value.

    Args:
        value: An ISO string, datetime, or date object.

    Returns:
        A timezone-aware datetime (UTC if naive).
    """
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if hasattr(value, "isoformat"):
        # date object
        return datetime.combine(value, datetime.min.time(), tzinfo=UTC)  # type: ignore[arg-type]
    return datetime.fromisoformat(str(value))


def _item_from_post(post: frontmatter.Post, filepath: Path) -> QualificationItem:
    """Build a QualificationItem from a frontmatter Post object.

    Args:
        post: Parsed frontmatter post.
        filepath: Absolute path to the queue file.

    Returns:
        A populated QualificationItem.
    """
    meta = post.metadata

    captured_raw = meta.get("date_captured") or meta.get("created_at") or _now_iso()
    captured_at = _parse_datetime(captured_raw)

    deferred_raw = meta.get("deferred_until")
    deferred_until = _parse_datetime(deferred_raw) if deferred_raw else None

    return QualificationItem(
        path=filepath,
        original_path=Path(meta.get("original_path", str(filepath))),
        title=str(meta.get("title", filepath.stem)),
        source_url=str(meta.get("source_url", "")),
        source_type=str(meta.get("source_type", "")),
        captured_at=captured_at,
        recommended_type=str(meta.get("recommended_type", "article")),
        recommended_topic=str(meta.get("recommended_topic", "")),
        recommended_tags=list(meta.get("recommended_tags", [])),
        recommended_quality=str(meta.get("recommended_quality", "medium")),
        recommended_summary=str(meta.get("recommended_summary", "")),
        user_type=meta.get("user_type"),
        user_topic=meta.get("user_topic"),
        user_tags=meta.get("user_tags"),
        user_quality=meta.get("user_quality"),
        user_notes=str(meta.get("qualification_notes", "")),
        status=str(meta.get("status", "qualifying")),
        deferred_until=deferred_until,
        telegram_message_id=meta.get("telegram_message_id"),
    )


def _update_frontmatter(filepath: Path, updates: dict[str, object]) -> frontmatter.Post:
    """Read a markdown file, update its frontmatter, and write it back.

    Args:
        filepath: Path to the markdown file.
        updates: Key-value pairs to merge into the frontmatter.

    Returns:
        The updated frontmatter Post object.
    """
    raw = filepath.read_text(encoding="utf-8")
    post = frontmatter.loads(raw)
    for key, value in updates.items():
        post.metadata[key] = value
    filepath.write_text(frontmatter.dumps(post), encoding="utf-8")
    return post


# ---------------------------------------------------------------------------
# Queue manager
# ---------------------------------------------------------------------------


class QualificationQueue:
    """Manages the qualification queue directory and item lifecycle.

    Args:
        vault_path: Absolute path to the vault root.
        queue_dir: Subdirectory name within vault for the queue.
        notifications_dir: Subdirectory for notification JSON files.
    """

    def __init__(
        self,
        vault_path: Path,
        queue_dir: str = "02-queue",
        notifications_dir: str | None = None,
    ) -> None:
        self._vault_path = Path(vault_path)
        self._queue_path = self._vault_path / queue_dir
        self._queue_path.mkdir(parents=True, exist_ok=True)
        # Notifications live inside the queue directory itself.
        notif_dir = notifications_dir or f"{queue_dir}/.notifications"
        self._notifications_path = self._vault_path / notif_dir
        self._notifications_path.mkdir(parents=True, exist_ok=True)

    @property
    def queue_path(self) -> Path:
        """Return the absolute path to the queue directory."""
        return self._queue_path

    # -- add ----------------------------------------------------------------

    def add_item(self, source_path: Path, recommendation: dict[str, object]) -> QualificationItem:
        """Move a file from inbox to queue and create a QualificationItem.

        Reads the file's frontmatter, merges with AI recommendation,
        updates frontmatter with qualification metadata, and moves the file
        to the queue directory.

        Args:
            source_path: Absolute path to the markdown file (typically in inbox/).
            recommendation: Dict from ``classify_document`` with keys:
                content_type, topic, tags, quality, summary.

        Returns:
            The created QualificationItem.

        Raises:
            FileNotFoundError: If *source_path* does not exist.
        """
        source_path = Path(source_path).resolve()
        if not source_path.is_file():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Read existing frontmatter
        raw = source_path.read_text(encoding="utf-8")
        post = frontmatter.loads(raw)

        now = _now_iso()

        # Merge qualification metadata into frontmatter
        post.metadata["status"] = "qualifying"
        post.metadata["original_path"] = str(source_path)
        post.metadata["date_captured"] = post.metadata.get("date_captured", now)
        post.metadata["content_type"] = recommendation.get("content_type", "article")
        post.metadata["recommended_type"] = recommendation.get("content_type", "article")
        post.metadata["recommended_topic"] = recommendation.get("topic", "")
        post.metadata["recommended_tags"] = list(recommendation.get("tags", []))
        post.metadata["recommended_quality"] = recommendation.get("quality", "medium")
        post.metadata["recommended_summary"] = recommendation.get("summary", "")

        # Preserve existing topics/tags alongside recommendations
        if not post.metadata.get("topics") and recommendation.get("topic"):
            post.metadata["topics"] = [recommendation["topic"]]
        if not post.metadata.get("tags"):
            post.metadata["tags"] = list(recommendation.get("tags", []))
        if not post.metadata.get("summary") and recommendation.get("summary"):
            post.metadata["summary"] = recommendation["summary"]
        if not post.metadata.get("quality"):
            post.metadata["quality"] = recommendation.get("quality", "medium")

        # Apply qualification formatting to the body
        post.content = format_on_qualify(post.content, post.metadata)

        # Write updated frontmatter to source before moving
        updated_content = frontmatter.dumps(post)
        source_path.write_text(updated_content, encoding="utf-8")

        # Move file to queue directory
        dest_path = self._queue_path / source_path.name
        # Handle name collision
        if dest_path.exists():
            stem = source_path.stem
            suffix = source_path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = self._queue_path / f"{stem}-{counter}{suffix}"
                counter += 1

        shutil.move(str(source_path), str(dest_path))
        logger.info("item_added_to_queue", source=str(source_path), dest=str(dest_path))

        return _item_from_post(post, dest_path)

    # -- get / list ---------------------------------------------------------

    def get_item(self, filename: str) -> QualificationItem | None:
        """Load a QualificationItem from its queue file.

        Args:
            filename: The filename (not full path) in the queue directory.

        Returns:
            A QualificationItem, or ``None`` if the file does not exist.
        """
        filepath = self._queue_path / filename
        if not filepath.is_file():
            return None
        try:
            raw = filepath.read_text(encoding="utf-8")
            post = frontmatter.loads(raw)
            return _item_from_post(post, filepath)
        except (OSError, ValueError) as exc:
            logger.error("queue_item_read_failed", path=str(filepath), error=str(exc))
            return None

    def list_pending(self) -> list[QualificationItem]:
        """List all items with status=qualifying.

        Returns:
            List of QualificationItems sorted by capture date (oldest first).
        """
        items: list[QualificationItem] = []
        for filepath in sorted(self._queue_path.glob("*.md")):
            try:
                raw = filepath.read_text(encoding="utf-8")
                post = frontmatter.loads(raw)
                if post.metadata.get("status") == "qualifying":
                    items.append(_item_from_post(post, filepath))
            except (OSError, ValueError) as exc:
                logger.warning("queue_item_skip", path=str(filepath), error=str(exc))
        return sorted(items, key=lambda i: i.captured_at)

    def list_deferred(self) -> list[QualificationItem]:
        """List deferred items whose deferred_until has passed.

        Returns:
            List of QualificationItems ready to be re-presented.
        """
        now = datetime.now(tz=UTC)
        items: list[QualificationItem] = []
        for filepath in sorted(self._queue_path.glob("*.md")):
            try:
                raw = filepath.read_text(encoding="utf-8")
                post = frontmatter.loads(raw)
                if post.metadata.get("status") != "qualifying":
                    continue
                deferred_raw = post.metadata.get("deferred_until")
                if deferred_raw:
                    deferred_dt = _parse_datetime(deferred_raw)
                    if deferred_dt <= now:
                        items.append(_item_from_post(post, filepath))
            except (OSError, ValueError) as exc:
                logger.warning("queue_deferred_skip", path=str(filepath), error=str(exc))
        return sorted(items, key=lambda i: i.captured_at)

    # -- approve / reject / defer -------------------------------------------

    def approve_item(self, item: QualificationItem) -> Path:
        """Move approved item from queue to permanent vault location.

        Updates frontmatter with final classification, sets status=published,
        and moves to ``~/vault/07-resources/<topic>/``.

        Args:
            item: The QualificationItem to approve.

        Returns:
            The new permanent path.
        """
        # Build destination: 07-resources/<topic>/
        topic_dir = item.final_topic.replace(" ", "-").lower() if item.final_topic else ""

        dest_dir = self._vault_path / "07-resources"
        if topic_dir:
            dest_dir = dest_dir / topic_dir
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / item.path.name

        # Handle collision
        if dest_path.exists():
            stem = item.path.stem
            suffix = item.path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{stem}-{counter}{suffix}"
                counter += 1

        now = _now_iso()
        _update_frontmatter(
            item.path,
            {
                "status": "published",
                "content_type": item.final_type,
                "topics": [item.final_topic] if item.final_topic else [],
                "tags": item.final_tags,
                "quality": item.final_quality,
                "summary": item.recommended_summary,
                "qualified_by": "user" if item.user_type or item.user_topic else "auto",
                "qualification_notes": item.user_notes,
                "date_qualified": now,
                "date_processed": now,
            },
        )

        # Validate for publication — log warnings but don't block
        raw = item.path.read_text(encoding="utf-8")
        post = frontmatter.loads(raw)
        pub_issues = validate_for_publication(post.content, post.metadata)
        if pub_issues:
            for issue in pub_issues:
                logger.warning("publication_issue", path=str(item.path), issue=issue)

        shutil.move(str(item.path), str(dest_path))
        logger.info(
            "item_approved",
            source=str(item.path),
            dest=str(dest_path),
            content_type=item.final_type,
            topic=item.final_topic,
            publication_issues=len(pub_issues),
        )
        return dest_path

    def reject_item(self, item: QualificationItem) -> Path:
        """Move rejected item to 08-archive/rejected/.

        Args:
            item: The QualificationItem to reject.

        Returns:
            The new path in the archive.
        """
        reject_dir = self._vault_path / "08-archive" / "rejected"
        reject_dir.mkdir(parents=True, exist_ok=True)

        dest_path = reject_dir / item.path.name
        if dest_path.exists():
            stem = item.path.stem
            suffix = item.path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = reject_dir / f"{stem}-{counter}{suffix}"
                counter += 1

        _update_frontmatter(item.path, {"status": "rejected", "date_qualified": _now_iso()})
        shutil.move(str(item.path), str(dest_path))
        logger.info("item_rejected", source=str(item.path), dest=str(dest_path))
        return dest_path

    def defer_item(self, item: QualificationItem, until: datetime) -> None:
        """Set deferred_until in frontmatter, keep in queue.

        Args:
            item: The QualificationItem to defer.
            until: When to re-present the item for review.
        """
        _update_frontmatter(item.path, {"deferred_until": until.isoformat()})
        logger.info("item_deferred", path=str(item.path), until=until.isoformat())

    def update_item(self, item: QualificationItem, **changes: object) -> QualificationItem:
        """Apply user modifications to frontmatter and return updated item.

        Supported change keys: ``user_type``, ``user_topic``, ``user_tags``,
        ``user_quality``, ``qualification_notes``, ``telegram_message_id``.

        Args:
            item: The QualificationItem to update.
            **changes: Key-value pairs to apply.

        Returns:
            A fresh QualificationItem loaded from the updated file.
        """
        fm_updates: dict[str, object] = {}
        for key, value in changes.items():
            if key == "qualification_notes":
                fm_updates["qualification_notes"] = value
            elif key.startswith("user_") or key == "telegram_message_id":
                fm_updates[key] = value
            else:
                logger.warning("unknown_update_key", key=key)

        if fm_updates:
            _update_frontmatter(item.path, fm_updates)
            logger.info("item_updated", path=str(item.path), keys=list(fm_updates.keys()))

        # Reload and return
        raw = item.path.read_text(encoding="utf-8")
        post = frontmatter.loads(raw)
        return _item_from_post(post, item.path)

    # -- notifications ------------------------------------------------------

    def write_notification(self, item: QualificationItem) -> Path:
        """Write a JSON notification file for the Telegram bot to pick up.

        Args:
            item: The QualificationItem to notify about.

        Returns:
            Path to the created notification file.
        """
        notification = {
            "type": "new_qualification",
            "filename": item.path.name,
            "title": item.title,
            "source_url": item.source_url,
            "source_type": item.source_type,
            "recommended_type": item.recommended_type,
            "recommended_topic": item.recommended_topic,
            "recommended_tags": item.recommended_tags,
            "recommended_quality": item.recommended_quality,
            "recommended_summary": item.recommended_summary,
            "created_at": _now_iso(),
        }

        timestamp = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S%f")
        notif_path = self._notifications_path / f"{timestamp}-{item.path.stem}.json"
        notif_path.write_text(json.dumps(notification, indent=2), encoding="utf-8")
        logger.info("notification_written", path=str(notif_path))
        return notif_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TYPE_PLURALS: dict[str, str] = {
    "article": "articles",
    "paper": "papers",
    "tutorial": "tutorials",
    "reference": "reference",
    "thought": "thoughts",
    "note": "notes",
    "video": "videos",
    "podcast": "podcasts",
    "image": "images",
    "pdf": "pdfs",
    "tweet": "tweets",
    "social-post": "social-posts",
    "discussion": "discussions",
    "url": "urls",
    "github-repo": "github-repos",
    "github-issue": "github-issues",
    "code-snippet": "code-snippets",
    "tool": "tools",
    "recipe": "recipes",
    "product": "products",
    "place": "places",
    "event": "events",
    "person": "people",
    "book": "books",
    "course": "courses",
}


def _pluralize_type(content_type: str) -> str:
    """Return the plural form of a content type for directory naming.

    Args:
        content_type: Singular content type string.

    Returns:
        Plural directory name.
    """
    return _TYPE_PLURALS.get(content_type, f"{content_type}s")
