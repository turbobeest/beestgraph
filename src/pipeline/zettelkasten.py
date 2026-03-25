"""Zettelkasten-specific utility functions for note identification and naming.

Provides timestamp-based ID generation, slug creation, and filename formatting
following the beestgraph naming conventions:

- Fleeting notes: ``YYYYMMDDHHMMSS Title.md``
- Permanent notes: ``Title.md``
- Captured content: ``slug-from-title.md``
"""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime

_NON_SLUG_RE = re.compile(r"[^\w\s-]")
_WHITESPACE_RE = re.compile(r"[\s_]+")
_ZK_ID_RE = re.compile(r"^\d{14}$")


def generate_id() -> str:
    """Generate a Zettelkasten timestamp ID: YYYYMMDDHHMMSS.

    Returns:
        A 14-digit UTC timestamp string.
    """
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S")


def parse_id(zk_id: str) -> datetime | None:
    """Parse a Zettelkasten ID back to a datetime.

    Args:
        zk_id: A 14-digit timestamp string (YYYYMMDDHHMMSS).

    Returns:
        A timezone-aware UTC datetime, or ``None`` if parsing fails.
    """
    if not _ZK_ID_RE.match(zk_id):
        return None
    try:
        return datetime.strptime(zk_id, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    except ValueError:
        return None


def generate_slug(title: str) -> str:
    """Create a URL-safe slug from a title string.

    Normalizes unicode, lowercases, strips non-alphanumeric characters,
    and replaces whitespace with hyphens.

    Args:
        title: The human-readable title.

    Returns:
        A lowercase, hyphen-separated slug string.
    """
    # Normalize unicode to ASCII-compatible decomposed form
    normalized = unicodedata.normalize("NFKD", title)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    # Remove non-word characters (except hyphens and spaces)
    cleaned = _NON_SLUG_RE.sub("", ascii_text)
    # Replace whitespace/underscores with hyphens, lowercase, strip edges
    slug = _WHITESPACE_RE.sub("-", cleaned).strip("-").lower()
    return slug


def format_filename(title: str, zk_id: str | None = None) -> str:
    """Generate a markdown filename from title and optional Zettelkasten ID.

    For fleeting notes (with ID): ``{zk_id} {title}.md``
    For permanent notes (no ID): ``{title}.md``

    Args:
        title: The note title.
        zk_id: Optional Zettelkasten timestamp ID.

    Returns:
        A filename string with ``.md`` extension.
    """
    # Clean title for safe filesystem use (keep spaces and basic punctuation)
    safe_title = re.sub(r'[<>:"/\\|?*]', "", title).strip()
    if not safe_title:
        safe_title = "Untitled"

    if zk_id:
        return f"{zk_id} {safe_title}.md"
    return f"{safe_title}.md"
