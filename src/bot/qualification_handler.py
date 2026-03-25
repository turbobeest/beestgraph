"""Telegram qualification conversation handler for beestgraph.

Manages the interactive review of items in the qualification queue.
Watches for notification JSON files written by the pipeline watcher,
sends Telegram messages with AI recommendations, and handles user
responses to approve, modify, reject, or defer queue items.

Supports visibility (private/shared/public) and maturity (fleeting/permanent)
controls. Default approval ("ok") sends items to fleeting; "approve permanent"
or "publish" sends directly to the resources tree.

Usage::

    # Integrated via telegram_bot.py — not invoked directly.
    from src.bot.qualification_handler import (
        qualification_router,
        start_notification_poller,
    )
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import structlog
import yaml
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from src.config import BeestgraphSettings

logger = structlog.get_logger(__name__)

qualification_router = Router(name="qualification")

# ---------------------------------------------------------------------------
# State — active qualification conversation per chat_id
# ---------------------------------------------------------------------------

# chat_id -> notification data dict (includes "filename" key)
_active_qualifications: dict[int, dict] = {}

# Track chat IDs of users who have interacted with the bot
_known_chat_ids: set[int] = set()

# chat_id -> asyncio.Task for deferred reminders
_deferred_tasks: dict[int, asyncio.Task] = {}  # type: ignore[type-arg]

# Valid visibility values
_VALID_VISIBILITIES = {"private", "shared", "public"}

# Valid maturity values
_VALID_MATURITIES = {"raw", "fleeting", "permanent"}


# ---------------------------------------------------------------------------
# MarkdownV2 helper
# ---------------------------------------------------------------------------


def _escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters for Telegram.

    Args:
        text: Raw text string.

    Returns:
        Escaped string safe for MarkdownV2 parse mode.
    """
    specials = r"_*[]()~`>#+-=|{}.!\\"
    out: list[str] = []
    for ch in text:
        if ch in specials:
            out.append("\\")
        out.append(ch)
    return "".join(out)


# ---------------------------------------------------------------------------
# Message formatting
# ---------------------------------------------------------------------------


def _format_qualification_message(notification: dict) -> str:
    """Format a qualification Telegram message from notification data.

    Includes visibility and maturity recommendations alongside type, topic,
    tags, quality, and summary.

    Args:
        notification: Parsed notification JSON with recommended fields.

    Returns:
        MarkdownV2-formatted message string.
    """
    title = _escape_md(notification.get("title", "Untitled"))
    source_url = notification.get("source_url", "")
    source_type = _escape_md(notification.get("source_type", "unknown"))
    recommended_type = _escape_md(notification.get("recommended_type", "article"))
    recommended_topic = _escape_md(notification.get("recommended_topic", ""))
    tags = notification.get("recommended_tags", [])
    tag_list = ", ".join(_escape_md(t) for t in tags) if tags else "none"
    quality = _escape_md(notification.get("recommended_quality", "medium"))
    visibility = _escape_md(notification.get("recommended_visibility", "private"))
    summary = _escape_md(notification.get("recommended_summary", ""))

    source_line = f"[Link]({source_url})" if source_url else "no URL"

    # Security scan indicator
    security_findings = notification.get("security_findings", "")
    scan_passed = not security_findings
    if scan_passed:
        security_line = "\U0001f50d Security scan: PASSED"
    else:
        security_line = f"\u26a0\ufe0f Security: {_escape_md(security_findings[:80])}"

    # Visibility icon
    vis_icon = "\U0001f513" if visibility == "public" else "\U0001f512"

    return (
        f"\U0001f4e5 *New item captured:*\n\n"
        f"*{title}*\n"
        f"Source: {source_line}\n"
        f"Via: {source_type}\n\n"
        f"  Type: `{recommended_type}` \\| Topic: `{recommended_topic}`\n"
        f"  Tags: {tag_list}\n"
        f"  Quality: {quality} \\| Summary: {summary}\n\n"
        f"{vis_icon} *Visibility: {visibility}*\n"
        f"{security_line}\n\n"
        f"Reply:\n"
        f"  `ok` \\— fleeting \\(private\\)\n"
        f"  `ok public` \\— fleeting \\(public\\)\n"
        f"  `publish` \\— permanent \\(private\\)\n"
        f"  `publish public` \\— permanent \\(public\\)\n"
        f"  `type X` \\| `topic X` \\| `add tag X`\n"
        f"  `later` \\| `reject`"
    )


def _format_updated_message(notification: dict) -> str:
    """Format an updated classification for re-presentation after edits.

    Args:
        notification: Updated notification data dict.

    Returns:
        MarkdownV2-formatted message string.
    """
    title = _escape_md(notification.get("title", "Untitled"))
    recommended_type = _escape_md(notification.get("recommended_type", "article"))
    recommended_topic = _escape_md(notification.get("recommended_topic", ""))
    tags = notification.get("recommended_tags", [])
    tag_list = ", ".join(_escape_md(t) for t in tags) if tags else "none"
    quality = _escape_md(notification.get("recommended_quality", "medium"))
    visibility = _escape_md(notification.get("recommended_visibility", "private"))
    maturity = _escape_md(notification.get("recommended_maturity", "fleeting"))
    summary = _escape_md(notification.get("recommended_summary", ""))

    return (
        f"\u270f\ufe0f *Updated classification for:* {title}\n\n"
        f"  Type: `{recommended_type}`\n"
        f"  Topic: `{recommended_topic}`\n"
        f"  Tags: {tag_list}\n"
        f"  Quality: {quality}\n"
        f"  Visibility: {visibility}\n"
        f"  Maturity: {maturity}\n"
        f"  Summary: {summary}\n\n"
        f"Approve? Reply `ok` \\(fleeting\\) or `publish` \\(permanent\\) or keep editing\\."
    )


# ---------------------------------------------------------------------------
# Queue file operations
# ---------------------------------------------------------------------------


def _read_queue_frontmatter(vault_path: str, queue_dir: str, filename: str) -> dict:
    """Read the YAML frontmatter from a queue file.

    Args:
        vault_path: Absolute path to the vault root.
        queue_dir: Queue subdirectory name.
        filename: Markdown filename in the queue.

    Returns:
        Parsed frontmatter dict, or empty dict on failure.
    """
    queue_file = Path(vault_path) / queue_dir / filename
    if not queue_file.exists():
        return {}
    try:
        content = queue_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return yaml.safe_load(parts[1]) or {}
    except Exception as exc:
        logger.warning("read_queue_frontmatter_failed", file=str(queue_file), error=str(exc))
    return {}


def _update_queue_frontmatter(
    vault_path: str, queue_dir: str, filename: str, updates: dict
) -> bool:
    """Update specific frontmatter fields in a queue file.

    Args:
        vault_path: Absolute path to the vault root.
        queue_dir: Queue subdirectory name.
        filename: Markdown filename in the queue.
        updates: Dict of frontmatter keys to update.

    Returns:
        True if the file was updated, False on failure.
    """
    queue_file = Path(vault_path) / queue_dir / filename
    if not queue_file.exists():
        return False
    try:
        content = queue_file.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return False
        parts = content.split("---", 2)
        if len(parts) < 3:
            return False
        frontmatter = yaml.safe_load(parts[1]) or {}
        frontmatter.update(updates)
        new_yaml = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        new_content = f"---\n{new_yaml}---{parts[2]}"
        queue_file.write_text(new_content, encoding="utf-8")
        logger.info("queue_frontmatter_updated", file=filename, updates=list(updates.keys()))
        return True
    except Exception as exc:
        logger.error("update_queue_frontmatter_failed", file=str(queue_file), error=str(exc))
        return False


def _move_to_fleeting(
    vault_path: str, queue_dir: str, fleeting_dir: str, filename: str, data: dict
) -> str | None:
    """Move a queue file to the fleeting directory.

    Updates frontmatter status to 'fleeting' and maturity to 'fleeting'.

    Args:
        vault_path: Absolute path to the vault root.
        queue_dir: Queue subdirectory name.
        fleeting_dir: Fleeting subdirectory name (e.g. ``03-fleeting``).
        filename: Markdown filename in the queue.
        data: Current notification/classification data.

    Returns:
        The new file path relative to vault, or None on failure.
    """
    source = Path(vault_path) / queue_dir / filename
    if not source.exists():
        return None

    dest_dir = Path(vault_path) / fleeting_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename

    try:
        now = datetime.now(UTC).isoformat()
        content = source.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = yaml.safe_load(parts[1]) or {}
                fm["status"] = "fleeting"
                fm["maturity"] = "fleeting"
                fm["modified"] = now
                fm["qualified_by"] = "user"
                # Apply any recommended fields from data
                if data.get("recommended_type"):
                    fm["type"] = data["recommended_type"]
                if data.get("recommended_topic"):
                    fm["topics"] = [data["recommended_topic"]]
                if data.get("recommended_tags"):
                    fm["tags"] = data["recommended_tags"]
                if data.get("recommended_quality"):
                    fm["quality"] = data["recommended_quality"]
                if data.get("recommended_visibility"):
                    fm["visibility"] = data["recommended_visibility"]
                if data.get("recommended_summary"):
                    fm["summary"] = data["recommended_summary"]
                new_yaml = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
                content = f"---\n{new_yaml}---{parts[2]}"

        dest.write_text(content, encoding="utf-8")
        source.unlink()
        rel_path = str(dest.relative_to(vault_path))
        logger.info("item_fleeting", source=filename, destination=rel_path)
        return rel_path
    except Exception as exc:
        logger.error("move_to_fleeting_failed", file=filename, error=str(exc))
        return None


def _move_to_published(
    vault_path: str,
    queue_dir: str,
    resources_dir: str,
    filename: str,
    data: dict,
) -> str | None:
    """Move a queue file to its permanent location in the resources tree.

    Updates frontmatter status to 'published', maturity to 'permanent',
    and sets timestamps.

    Args:
        vault_path: Absolute path to the vault root.
        queue_dir: Queue subdirectory name.
        resources_dir: Resources subdirectory name (e.g. ``07-resources``).
        filename: Markdown filename in the queue.
        data: Current notification/classification data.

    Returns:
        The new file path relative to vault, or None on failure.
    """
    source = Path(vault_path) / queue_dir / filename
    if not source.exists():
        return None

    content_type = data.get("recommended_type", "article")
    topic = data.get("recommended_topic", "uncategorized")

    # Build destination: resources/<topic>/
    dest_dir = Path(vault_path) / resources_dir / topic.replace("/", "/")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename

    try:
        now = datetime.now(UTC).isoformat()
        content = source.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = yaml.safe_load(parts[1]) or {}
                fm["status"] = "published"
                fm["maturity"] = "permanent"
                fm["published"] = now
                fm["modified"] = now
                fm["qualified_by"] = "user"
                fm["type"] = content_type
                if data.get("recommended_topic"):
                    fm["topics"] = [data["recommended_topic"]]
                if data.get("recommended_tags"):
                    fm["tags"] = data["recommended_tags"]
                if data.get("recommended_quality"):
                    fm["quality"] = data["recommended_quality"]
                if data.get("recommended_visibility"):
                    fm["visibility"] = data["recommended_visibility"]
                if data.get("recommended_summary"):
                    fm["summary"] = data["recommended_summary"]
                new_yaml = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
                content = f"---\n{new_yaml}---{parts[2]}"

        dest.write_text(content, encoding="utf-8")
        source.unlink()
        rel_path = str(dest.relative_to(vault_path))
        logger.info("item_published", source=filename, destination=rel_path)
        return rel_path
    except Exception as exc:
        logger.error("move_to_published_failed", file=filename, error=str(exc))
        return None


def _move_to_rejected(vault_path: str, queue_dir: str, archive_dir: str, filename: str) -> bool:
    """Move a queue file to the rejected archive.

    Args:
        vault_path: Absolute path to the vault root.
        queue_dir: Queue subdirectory name.
        archive_dir: Archive subdirectory name.
        filename: Markdown filename in the queue.

    Returns:
        True if the file was moved successfully.
    """
    source = Path(vault_path) / queue_dir / filename
    if not source.exists():
        return False
    try:
        rejected_dir = Path(vault_path) / archive_dir / "rejected"
        rejected_dir.mkdir(parents=True, exist_ok=True)
        dest = rejected_dir / filename

        content = source.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = yaml.safe_load(parts[1]) or {}
                fm["status"] = "rejected"
                fm["modified"] = datetime.now(UTC).isoformat()
                fm["qualified_by"] = "user"
                new_yaml = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
                content = f"---\n{new_yaml}---{parts[2]}"

        dest.write_text(content, encoding="utf-8")
        source.unlink()
        logger.info("item_rejected", file=filename)
        return True
    except Exception as exc:
        logger.error("move_to_rejected_failed", file=filename, error=str(exc))
        return False


def _pluralize_type(content_type: str) -> str:
    """Convert a content type to its plural directory name.

    Args:
        content_type: Singular content type string.

    Returns:
        Pluralized directory name.
    """
    plurals = {
        "article": "articles",
        "paper": "papers",
        "tutorial": "tutorials",
        "reference": "references",
        "thought": "thoughts",
        "note": "notes",
        "video": "videos",
        "podcast": "podcasts",
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
        "image": "images",
        "pdf": "pdfs",
    }
    return plurals.get(content_type, f"{content_type}s")


# ---------------------------------------------------------------------------
# Queue listing
# ---------------------------------------------------------------------------


def _list_queue_items(vault_path: str, queue_dir: str) -> list[dict]:
    """List all items currently in the qualification queue.

    Args:
        vault_path: Absolute path to the vault root.
        queue_dir: Queue subdirectory name.

    Returns:
        List of dicts with filename, title, and status from frontmatter.
    """
    queue_path = Path(vault_path) / queue_dir
    if not queue_path.exists():
        return []
    items: list[dict] = []
    for f in sorted(queue_path.glob("*.md")):
        fm = _read_queue_frontmatter(vault_path, queue_dir, f.name)
        items.append(
            {
                "filename": f.name,
                "title": fm.get("title", f.stem),
                "content_type": fm.get("type", fm.get("content_type", "unknown")),
                "topics": fm.get("topics", []),
                "status": fm.get("status", "qualifying"),
                "visibility": fm.get("visibility", "private"),
                "maturity": fm.get("maturity", "raw"),
            }
        )
    return items


# ---------------------------------------------------------------------------
# Time parsing for /later command
# ---------------------------------------------------------------------------

_TIME_PATTERN = re.compile(
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?",
    re.IGNORECASE,
)


def _parse_defer_time(text: str, default_hours: int = 4) -> timedelta:
    """Parse a deferral time expression into a timedelta from now.

    Supports:
        - "later" -> default_hours
        - "later 4h" / "later 4 hours" -> N hours
        - "later 9pm" / "later 9:30pm" -> next occurrence of that time
        - "later tomorrow" -> 24 hours

    Args:
        text: The deferral text (everything after "later" or the /later command).
        default_hours: Default hours to defer if no time specified.

    Returns:
        A timedelta representing how long to wait.
    """
    text = text.strip().lower()

    if not text:
        return timedelta(hours=default_hours)

    if text == "tomorrow":
        return timedelta(hours=24)

    # Match "Nh" or "N hours"
    hour_match = re.match(r"(\d+)\s*h(?:ours?)?$", text)
    if hour_match:
        return timedelta(hours=int(hour_match.group(1)))

    # Match time like "9pm", "9:30pm", "21:00"
    time_match = _TIME_PATTERN.match(text)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        ampm = time_match.group(3)

        if ampm:
            if ampm.lower() == "pm" and hour != 12:
                hour += 12
            elif ampm.lower() == "am" and hour == 12:
                hour = 0

        now = datetime.now(UTC)
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target - now

    # Fallback
    return timedelta(hours=default_hours)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


@qualification_router.message(Command("queue"))
async def cmd_queue(message: Message, settings: BeestgraphSettings, **_kwargs: object) -> None:
    """List items in the qualification queue.

    Args:
        message: Incoming Telegram message.
        settings: Application settings.
    """
    logger.info("queue_command", user_id=message.from_user.id if message.from_user else None)

    items = _list_queue_items(settings.vault.path, settings.vault.queue_dir)

    if not items:
        await message.answer("No items in the qualification queue\\.", parse_mode="MarkdownV2")
        return

    lines: list[str] = [f"*Qualification Queue* \\({len(items)} items\\)\n"]
    for i, item in enumerate(items, 1):
        title = _escape_md(item["title"])
        ctype = _escape_md(item["content_type"])
        topics = item.get("topics", [])
        topic_str = _escape_md(topics[0]) if topics else "uncategorized"
        vis = _escape_md(item.get("visibility", "private"))
        lines.append(
            f"{i}\\. *{title}*\n   Type: `{ctype}` \\| Topic: `{topic_str}` \\| Visibility: {vis}"
        )

    lines.append("\nUse /approve or /reject with an item name\\.")
    await message.answer("\n".join(lines), parse_mode="MarkdownV2")


@qualification_router.message(Command("approve"))
async def cmd_approve(message: Message, settings: BeestgraphSettings, **_kwargs: object) -> None:
    """Approve the most recent or specified queue item.

    Usage:
        /approve — approve last presented item (fleeting)
        /approve permanent — approve as permanent
        /approve knowledge-graphs-intro — approve by name (fleeting)

    Args:
        message: Incoming Telegram message.
        settings: Application settings.
    """
    if not message.text:
        return

    chat_id = message.chat.id
    parts = message.text.split(maxsplit=1)
    arg = parts[1].strip() if len(parts) > 1 else None

    # Check if "permanent" or "publish" is the argument
    permanent = False
    target_name = arg
    if arg and arg.lower() in ("permanent", "publish"):
        permanent = True
        target_name = None

    logger.info(
        "approve_command",
        user_id=message.from_user.id if message.from_user else None,
        target=target_name,
        permanent=permanent,
    )

    # Resolve which item to approve
    data = _resolve_target(chat_id, target_name, settings)
    if data is None:
        await message.answer(
            "No item to approve\\. Use /queue to see pending items\\.",
            parse_mode="MarkdownV2",
        )
        return

    filename = data["filename"]

    if permanent:
        dest = _move_to_published(
            settings.vault.path,
            settings.vault.queue_dir,
            settings.vault.resources_dir,
            filename,
            data,
        )
        if dest:
            title = _escape_md(data.get("title", filename))
            safe_dest = _escape_md(dest)
            await message.answer(
                f"\u2705 *Published \\(permanent\\):* {title}\n`{safe_dest}`",
                parse_mode="MarkdownV2",
            )
        else:
            await message.answer("Failed to publish item\\. Check logs\\.", parse_mode="MarkdownV2")
    else:
        dest = _move_to_fleeting(
            settings.vault.path,
            settings.vault.queue_dir,
            settings.vault.fleeting_dir,
            filename,
            data,
        )
        if dest:
            title = _escape_md(data.get("title", filename))
            safe_dest = _escape_md(dest)
            await message.answer(
                f"\u2705 *Approved \\(fleeting\\):* {title}\n`{safe_dest}`",
                parse_mode="MarkdownV2",
            )
        else:
            await message.answer("Failed to approve item\\. Check logs\\.", parse_mode="MarkdownV2")

    _active_qualifications.pop(chat_id, None)


@qualification_router.message(Command("reject"))
async def cmd_reject(message: Message, settings: BeestgraphSettings, **_kwargs: object) -> None:
    """Reject a queue item.

    Args:
        message: Incoming Telegram message.
        settings: Application settings.
    """
    if not message.text:
        return

    chat_id = message.chat.id
    parts = message.text.split(maxsplit=1)
    target_name = parts[1].strip() if len(parts) > 1 else None

    logger.info(
        "reject_command",
        user_id=message.from_user.id if message.from_user else None,
        target=target_name,
    )

    data = _resolve_target(chat_id, target_name, settings)
    if data is None:
        await message.answer(
            "No item to reject\\. Use /queue to see pending items\\.",
            parse_mode="MarkdownV2",
        )
        return

    filename = data["filename"]
    success = _move_to_rejected(
        settings.vault.path,
        settings.vault.queue_dir,
        settings.vault.archive_dir,
        filename,
    )

    if success:
        title = _escape_md(data.get("title", filename))
        await message.answer(
            f"\u274c *Rejected:* {title}\nMoved to archive/rejected\\.",
            parse_mode="MarkdownV2",
        )
        _active_qualifications.pop(chat_id, None)
    else:
        await message.answer("Failed to reject item\\. Check logs\\.", parse_mode="MarkdownV2")


@qualification_router.message(Command("later"))
async def cmd_later(
    message: Message, bot: Bot, settings: BeestgraphSettings, **_kwargs: object
) -> None:
    """Defer a queue item for later review.

    Usage:
        /later — defer 4 hours
        /later 9pm — defer until specific time
        /later tomorrow — defer 24 hours

    Args:
        message: Incoming Telegram message.
        bot: The aiogram Bot instance.
        settings: Application settings.
    """
    if not message.text:
        return

    chat_id = message.chat.id
    parts = message.text.split(maxsplit=1)
    time_text = parts[1].strip() if len(parts) > 1 else ""

    logger.info(
        "later_command",
        user_id=message.from_user.id if message.from_user else None,
        time_text=time_text,
    )

    data = _active_qualifications.get(chat_id)
    if data is None:
        await message.answer(
            "No active item to defer\\. Use /queue to see pending items\\.",
            parse_mode="MarkdownV2",
        )
        return

    delay = _parse_defer_time(time_text, settings.qualification.default_defer_hours)
    remind_at = datetime.now(UTC) + delay
    hours = delay.total_seconds() / 3600

    title = _escape_md(data.get("title", "item"))
    time_str = _escape_md(f"{hours:.1f} hours")
    await message.answer(
        f"\u23f0 *Deferred:* {title}\nI'll remind you in {time_str}\\.",
        parse_mode="MarkdownV2",
    )

    # Cancel any existing deferred task for this chat
    if chat_id in _deferred_tasks:
        _deferred_tasks[chat_id].cancel()

    # Schedule a reminder
    task = asyncio.create_task(_send_deferred_reminder(bot, chat_id, data, delay))
    _deferred_tasks[chat_id] = task

    # Try to create a calendar event for the reminder
    _schedule_calendar_reminder(settings, data, remind_at)


# ---------------------------------------------------------------------------
# Inline qualification response handling
# ---------------------------------------------------------------------------

_QUALIFICATION_KEYWORDS = {
    "ok",
    "approve",
    "approve permanent",
    "publish",
    "yes",
    "y",
    "\U0001f44d",
    "reject",
    "no",
    "n",
    "\U0001f44e",
    "later",
    "public",
    "private",
    "shared",
}


def register_chat_id(chat_id: int) -> None:
    """Register a chat ID as a known user for notification delivery."""
    _known_chat_ids.add(chat_id)


def is_qualification_response(chat_id: int, text: str) -> bool:
    """Check if a message looks like a qualification response.

    Args:
        chat_id: The Telegram chat ID.
        text: The message text.

    Returns:
        True if this chat has an active qualification and the text
        looks like a qualification action.
    """
    if chat_id not in _active_qualifications:
        return False

    text_lower = text.strip().lower()

    # Direct keywords
    if text_lower in _QUALIFICATION_KEYWORDS:
        return True

    # Prefixed commands
    prefixes = (
        "type ",
        "topic ",
        "add tag ",
        "remove tag ",
        "quality ",
        "visibility ",
        "maturity ",
        "later ",
        "approve ",
    )
    return any(text_lower.startswith(p) for p in prefixes)


async def handle_qualification_response(
    message: Message, bot: Bot, settings: BeestgraphSettings
) -> bool:
    """Process an inline qualification response from the user.

    Called from the main chat_handler when a qualification response is detected.
    Handles visibility (public/private/shared), maturity (fleeting/permanent),
    and the existing type/topic/tag/quality commands.

    Args:
        message: Incoming Telegram message.
        bot: The aiogram Bot instance.
        settings: Application settings.

    Returns:
        True if the message was handled as a qualification response.
    """
    if not message.text:
        return False

    chat_id = message.chat.id
    data = _active_qualifications.get(chat_id)
    if data is None:
        return False

    text = message.text.strip()
    text_lower = text.lower()

    logger.info(
        "qualification_response",
        chat_id=chat_id,
        text=text[:80],
        filename=data.get("filename"),
    )

    # --- Determine visibility modifier ---
    wants_public = text_lower.endswith(" public")
    wants_shared = text_lower.endswith(" shared")
    base_command = text_lower.replace(" public", "").replace(" shared", "").strip()
    target_visibility = "public" if wants_public else ("shared" if wants_shared else "private")

    # Validate public eligibility
    if wants_public:
        from src.pipeline.privacy import validate_can_be_public

        issues = validate_can_be_public(
            content_type=data.get("recommended_type", ""),
            para=data.get("para", "resources"),
            title=data.get("title", ""),
            content="",
            security_scan_passed=not data.get("security_findings"),
        )
        if issues:
            issue_text = _escape_md("; ".join(issues))
            await message.answer(
                f"\U0001f512 Cannot make public: {issue_text}\nApproving as *private* instead\\.",
                parse_mode="MarkdownV2",
            )
            target_visibility = "private"

    # --- ok / approve (-> fleeting) ---
    if base_command in ("ok", "approve", "yes", "y", "\U0001f44d"):
        filename = data["filename"]
        data["_target_visibility"] = target_visibility
        dest = _move_to_fleeting(
            settings.vault.path,
            settings.vault.queue_dir,
            settings.vault.fleeting_dir,
            filename,
            data,
        )
        if dest:
            vis_icon = "\U0001f513" if target_visibility == "public" else "\U0001f512"
            title = _escape_md(data.get("title", filename))
            safe_dest = _escape_md(dest)
            await message.answer(
                f"\u2705 *Approved \\(fleeting\\):* {title}\n"
                f"{vis_icon} {_escape_md(target_visibility)}\n`{safe_dest}`",
                parse_mode="MarkdownV2",
            )
        else:
            await message.answer("Failed to approve\\. Check logs\\.", parse_mode="MarkdownV2")
        _active_qualifications.pop(chat_id, None)
        return True

    # --- approve permanent / publish (-> permanent in resources) ---
    if base_command in ("approve permanent", "publish"):
        filename = data["filename"]
        dest = _move_to_published(
            settings.vault.path,
            settings.vault.queue_dir,
            settings.vault.resources_dir,
            filename,
            data,
        )
        if dest:
            title = _escape_md(data.get("title", filename))
            safe_dest = _escape_md(dest)
            await message.answer(
                f"\u2705 *Published \\(permanent\\):* {title}\n`{safe_dest}`",
                parse_mode="MarkdownV2",
            )
        else:
            await message.answer("Failed to publish\\. Check logs\\.", parse_mode="MarkdownV2")
        _active_qualifications.pop(chat_id, None)
        return True

    # --- reject ---
    if text_lower in ("reject", "no", "n", "\U0001f44e"):
        filename = data["filename"]
        success = _move_to_rejected(
            settings.vault.path,
            settings.vault.queue_dir,
            settings.vault.archive_dir,
            filename,
        )
        if success:
            title = _escape_md(data.get("title", filename))
            await message.answer(f"\u274c *Rejected:* {title}", parse_mode="MarkdownV2")
        else:
            await message.answer("Failed to reject\\. Check logs\\.", parse_mode="MarkdownV2")
        _active_qualifications.pop(chat_id, None)
        return True

    # --- later ---
    if text_lower.startswith("later"):
        time_text = text_lower[5:].strip()
        delay = _parse_defer_time(time_text, settings.qualification.default_defer_hours)
        hours = delay.total_seconds() / 3600

        title = _escape_md(data.get("title", "item"))
        time_str = _escape_md(f"{hours:.1f} hours")
        await message.answer(
            f"\u23f0 *Deferred:* {title}\nReminder in {time_str}\\.",
            parse_mode="MarkdownV2",
        )

        if chat_id in _deferred_tasks:
            _deferred_tasks[chat_id].cancel()

        task = asyncio.create_task(_send_deferred_reminder(bot, chat_id, data, delay))
        _deferred_tasks[chat_id] = task
        return True

    # --- visibility: public / private / shared (bare keyword) ---
    if text_lower in _VALID_VISIBILITIES:
        data["recommended_visibility"] = text_lower
        _active_qualifications[chat_id] = data
        _update_queue_frontmatter(
            settings.vault.path,
            settings.vault.queue_dir,
            data["filename"],
            {"visibility": text_lower},
        )
        msg = _format_updated_message(data)
        await message.answer(msg, parse_mode="MarkdownV2")
        return True

    # --- visibility <level> (explicit prefix) ---
    if text_lower.startswith("visibility "):
        new_vis = text[11:].strip().lower()
        if new_vis in _VALID_VISIBILITIES:
            data["recommended_visibility"] = new_vis
            _active_qualifications[chat_id] = data
            _update_queue_frontmatter(
                settings.vault.path,
                settings.vault.queue_dir,
                data["filename"],
                {"visibility": new_vis},
            )
            msg = _format_updated_message(data)
            await message.answer(msg, parse_mode="MarkdownV2")
            return True

    # --- maturity <level> ---
    if text_lower.startswith("maturity "):
        new_mat = text[9:].strip().lower()
        if new_mat in _VALID_MATURITIES:
            data["recommended_maturity"] = new_mat
            _active_qualifications[chat_id] = data
            _update_queue_frontmatter(
                settings.vault.path,
                settings.vault.queue_dir,
                data["filename"],
                {"maturity": new_mat},
            )
            msg = _format_updated_message(data)
            await message.answer(msg, parse_mode="MarkdownV2")
            return True

    # --- type <new_type> ---
    if text_lower.startswith("type "):
        new_type = text[5:].strip()
        data["recommended_type"] = new_type
        _active_qualifications[chat_id] = data
        _update_queue_frontmatter(
            settings.vault.path,
            settings.vault.queue_dir,
            data["filename"],
            {"type": new_type},
        )
        msg = _format_updated_message(data)
        await message.answer(msg, parse_mode="MarkdownV2")
        return True

    # --- topic <new_topic> ---
    if text_lower.startswith("topic "):
        new_topic = text[6:].strip()
        data["recommended_topic"] = new_topic
        _active_qualifications[chat_id] = data
        _update_queue_frontmatter(
            settings.vault.path,
            settings.vault.queue_dir,
            data["filename"],
            {"topics": [new_topic]},
        )
        msg = _format_updated_message(data)
        await message.answer(msg, parse_mode="MarkdownV2")
        return True

    # --- add tag <tag> ---
    if text_lower.startswith("add tag "):
        new_tag = text[8:].strip()
        tags = data.get("recommended_tags", [])
        if new_tag not in tags:
            tags.append(new_tag)
        data["recommended_tags"] = tags
        _active_qualifications[chat_id] = data
        _update_queue_frontmatter(
            settings.vault.path,
            settings.vault.queue_dir,
            data["filename"],
            {"tags": tags},
        )
        msg = _format_updated_message(data)
        await message.answer(msg, parse_mode="MarkdownV2")
        return True

    # --- remove tag <tag> ---
    if text_lower.startswith("remove tag "):
        rm_tag = text[11:].strip()
        tags = data.get("recommended_tags", [])
        tags = [t for t in tags if t.lower() != rm_tag.lower()]
        data["recommended_tags"] = tags
        _active_qualifications[chat_id] = data
        _update_queue_frontmatter(
            settings.vault.path,
            settings.vault.queue_dir,
            data["filename"],
            {"tags": tags},
        )
        msg = _format_updated_message(data)
        await message.answer(msg, parse_mode="MarkdownV2")
        return True

    # --- quality <level> ---
    if text_lower.startswith("quality "):
        new_quality = text[8:].strip().lower()
        if new_quality in ("high", "medium", "low"):
            data["recommended_quality"] = new_quality
            _active_qualifications[chat_id] = data
            _update_queue_frontmatter(
                settings.vault.path,
                settings.vault.queue_dir,
                data["filename"],
                {"quality": new_quality},
            )
            msg = _format_updated_message(data)
            await message.answer(msg, parse_mode="MarkdownV2")
            return True

    # Not recognized as a qualification command
    return False


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------


def _resolve_target(
    chat_id: int, target_name: str | None, settings: BeestgraphSettings
) -> dict | None:
    """Resolve a queue item by name or from the active qualification.

    Args:
        chat_id: The Telegram chat ID.
        target_name: Optional filename stem to look up.
        settings: Application settings.

    Returns:
        Notification-like dict with at least a "filename" key, or None.
    """
    # If no target specified, use active qualification
    if not target_name:
        return _active_qualifications.get(chat_id)

    # Search by name in the queue
    queue_path = Path(settings.vault.path) / settings.vault.queue_dir
    if not queue_path.exists():
        return None

    # Try exact filename match first
    for suffix in ("", ".md"):
        candidate = queue_path / f"{target_name}{suffix}"
        if candidate.exists():
            fm = _read_queue_frontmatter(
                settings.vault.path, settings.vault.queue_dir, candidate.name
            )
            return {
                "id": fm.get("id", ""),
                "filename": candidate.name,
                "title": fm.get("title", candidate.stem),
                "recommended_type": fm.get("type", fm.get("content_type", "article")),
                "recommended_topic": (fm.get("topics", [None]) or [None])[0] or "",
                "recommended_tags": fm.get("tags", []),
                "recommended_quality": fm.get("quality", "medium"),
                "recommended_visibility": fm.get("visibility", "private"),
                "recommended_maturity": fm.get("maturity", "raw"),
                "recommended_summary": fm.get("summary", ""),
                "source_url": fm.get("source_url", ""),
                "source_type": fm.get("source_type", ""),
            }

    # Try partial match
    for f in queue_path.glob("*.md"):
        if target_name.lower() in f.stem.lower():
            fm = _read_queue_frontmatter(settings.vault.path, settings.vault.queue_dir, f.name)
            return {
                "id": fm.get("id", ""),
                "filename": f.name,
                "title": fm.get("title", f.stem),
                "recommended_type": fm.get("type", fm.get("content_type", "article")),
                "recommended_topic": (fm.get("topics", [None]) or [None])[0] or "",
                "recommended_tags": fm.get("tags", []),
                "recommended_quality": fm.get("quality", "medium"),
                "recommended_visibility": fm.get("visibility", "private"),
                "recommended_maturity": fm.get("maturity", "raw"),
                "recommended_summary": fm.get("summary", ""),
                "source_url": fm.get("source_url", ""),
                "source_type": fm.get("source_type", ""),
            }

    return None


# ---------------------------------------------------------------------------
# Background notification poller
# ---------------------------------------------------------------------------


async def _send_deferred_reminder(bot: Bot, chat_id: int, data: dict, delay: timedelta) -> None:
    """Wait for *delay*, then re-send the qualification message.

    Args:
        bot: The aiogram Bot instance.
        chat_id: The Telegram chat ID to send to.
        data: The notification data dict.
        delay: How long to wait before sending.
    """
    try:
        await asyncio.sleep(delay.total_seconds())
        msg = _format_qualification_message(data)
        await bot.send_message(chat_id, msg, parse_mode="MarkdownV2")
        _active_qualifications[chat_id] = data
        logger.info("deferred_reminder_sent", chat_id=chat_id, filename=data.get("filename"))
    except asyncio.CancelledError:
        logger.debug("deferred_reminder_cancelled", chat_id=chat_id)
    except Exception as exc:
        logger.warning("deferred_reminder_failed", chat_id=chat_id, error=str(exc))


def _schedule_calendar_reminder(
    settings: BeestgraphSettings, data: dict, remind_at: datetime
) -> None:
    """Attempt to create a calendar event for a deferred qualification reminder.

    Fails silently if the calendar service is unavailable.

    Args:
        settings: Application settings.
        data: The notification data dict.
        remind_at: When to trigger the reminder.
    """
    try:
        from src.heartbeat.calendar import BeestgraphCalendar

        cal = BeestgraphCalendar(
            url=settings.calendar.url,
            username=settings.calendar.username,
            password=settings.calendar.password,
            calendar_name=settings.calendar.calendar_name,
        )
        title = data.get("title", "Untitled")
        cal.add_scheduled_event(
            title=f"Review: {title}",
            start=remind_at,
            end=remind_at + timedelta(minutes=15),
            description=f"Qualification reminder for: {title}\nFile: {data.get('filename', '')}",
        )
        logger.info("calendar_reminder_created", title=title, remind_at=remind_at.isoformat())
    except Exception as exc:
        logger.debug("calendar_reminder_skipped", error=str(exc))


async def start_notification_poller(bot: Bot, settings: BeestgraphSettings) -> None:
    """Poll for new qualification notifications and send Telegram messages.

    Watches ``~/vault/queue/.notifications/`` for JSON files written by
    the pipeline watcher. Each file triggers a Telegram notification to
    the first allowed user.

    The notification JSON should include::

        {
            "id": "20260325013335",
            "filename": "docker-networking.md",
            "title": "Understanding Docker Networking",
            "source_url": "https://docs.docker.com/network/",
            "source_type": "manual",
            "recommended_type": "tutorial",
            "recommended_topic": "technology/infrastructure",
            "recommended_tags": ["docker", "networking"],
            "recommended_quality": "high",
            "recommended_visibility": "private",
            "recommended_maturity": "fleeting",
            "recommended_summary": "Guide to Docker container networking..."
        }

    This runs as a long-lived background task.

    Args:
        bot: The aiogram Bot instance.
        settings: Application settings.
    """
    notifications_dir = Path(settings.vault.path) / settings.vault.queue_dir / ".notifications"
    poll_interval = settings.qualification.poll_interval_seconds

    # Determine the chat ID to send to
    allowed_ids = settings.telegram.get_allowed_ids()

    logger.info(
        "notification_poller_started",
        notifications_dir=str(notifications_dir),
        poll_interval=poll_interval,
        allowed_users=allowed_ids,
    )

    while True:
        await asyncio.sleep(poll_interval)

        if not notifications_dir.exists():
            continue

        for f in sorted(notifications_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))

                # Ensure new fields have defaults for backward compat
                data.setdefault("recommended_visibility", "private")
                data.setdefault("recommended_maturity", "fleeting")

                msg = _format_qualification_message(data)

                # Send to allowed users, or known users if no allowlist
                recipients = allowed_ids or list(_known_chat_ids)
                sent = False
                for user_id in recipients:
                    try:
                        await bot.send_message(
                            user_id, msg, parse_mode="MarkdownV2", disable_web_page_preview=True
                        )
                        _active_qualifications[user_id] = data
                        sent = True
                        logger.info(
                            "notification_sent",
                            file=f.name,
                            user_id=user_id,
                            filename=data.get("filename"),
                        )
                    except Exception as exc:
                        logger.warning(
                            "notification_send_to_user_failed",
                            user_id=user_id,
                            error=str(exc),
                        )

                if sent:
                    f.unlink()
                else:
                    logger.warning("notification_no_recipients", file=f.name)

            except json.JSONDecodeError as exc:
                logger.warning("notification_json_invalid", file=str(f), error=str(exc))
                f.unlink()  # Remove malformed files
            except Exception as exc:
                logger.warning("notification_send_failed", file=str(f), error=str(exc))
