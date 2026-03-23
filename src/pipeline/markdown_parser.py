"""Parse markdown files into structured data for graph ingestion.

Extracts YAML frontmatter, wiki-links, inline tags, and URLs from markdown
documents, returning a ``ParsedDocument`` dataclass ready for the ingester.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter
import structlog

logger = structlog.get_logger(__name__)

# Patterns ------------------------------------------------------------------

_WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
_INLINE_TAG_RE = re.compile(r"(?:^|(?<=\s))#([A-Za-z][A-Za-z0-9_/-]*)\b")
_URL_RE = re.compile(r"https?://[^\s\)\]>\"']+")


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """Structured representation of a parsed markdown file.

    Attributes:
        path: Vault-relative path (e.g. ``inbox/article.md``).
        title: Document title from frontmatter or first H1.
        content: Full markdown body (without frontmatter).
        metadata: Raw frontmatter dict.
        wiki_links: Set of linked document names extracted from ``[[…]]``.
        tags: Set of inline ``#tag`` values (lowercased).
        urls: Set of URLs found in the body.
    """

    path: str
    title: str
    content: str
    metadata: dict[str, object] = field(default_factory=dict)
    wiki_links: frozenset[str] = field(default_factory=frozenset)
    tags: frozenset[str] = field(default_factory=frozenset)
    urls: frozenset[str] = field(default_factory=frozenset)


def _extract_title(metadata: dict[str, object], body: str, filepath: Path) -> str:
    """Derive document title from frontmatter, first H1, or filename.

    Args:
        metadata: Parsed frontmatter dict.
        body: Markdown body text.
        filepath: Filesystem path to the file.

    Returns:
        A non-empty title string.
    """
    fm_title = metadata.get("title")
    if isinstance(fm_title, str) and fm_title.strip():
        return fm_title.strip()

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            return stripped.lstrip("# ").strip()

    return filepath.stem.replace("-", " ").replace("_", " ").title()


def extract_wiki_links(text: str) -> frozenset[str]:
    """Find all ``[[wiki-link]]`` targets in markdown text.

    Args:
        text: Markdown body string.

    Returns:
        Frozenset of link target names (display aliases stripped).
    """
    return frozenset(_WIKI_LINK_RE.findall(text))


def extract_tags(text: str) -> frozenset[str]:
    """Find all inline ``#tag`` values, normalised to lowercase.

    Args:
        text: Markdown body string.

    Returns:
        Frozenset of lowercased tag strings (without the ``#`` prefix).
    """
    return frozenset(tag.lower() for tag in _INLINE_TAG_RE.findall(text))


def extract_urls(text: str) -> frozenset[str]:
    """Find all HTTP(S) URLs in text.

    Args:
        text: Markdown body string.

    Returns:
        Frozenset of URL strings.
    """
    return frozenset(_URL_RE.findall(text))


def parse_file(filepath: Path, vault_root: Path | None = None) -> ParsedDocument:
    """Parse a single markdown file into a ``ParsedDocument``.

    Args:
        filepath: Absolute or relative path to the ``.md`` file.
        vault_root: If provided, ``ParsedDocument.path`` will be relative to
            this directory.  Otherwise the full path string is used.

    Returns:
        A fully populated ``ParsedDocument``.

    Raises:
        FileNotFoundError: If *filepath* does not exist.
        ValueError: If the file cannot be decoded as UTF-8.
    """
    filepath = Path(filepath).resolve()
    if not filepath.is_file():
        raise FileNotFoundError(f"Markdown file not found: {filepath}")

    try:
        raw_text = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Cannot decode {filepath} as UTF-8: {exc}") from exc

    post = frontmatter.loads(raw_text)
    metadata: dict[str, object] = dict(post.metadata)
    body: str = post.content

    rel_path = str(filepath.relative_to(vault_root)) if vault_root else str(filepath)
    title = _extract_title(metadata, body, filepath)

    # Merge frontmatter tags with inline tags
    fm_tags = metadata.get("tags", [])
    fm_tag_set = frozenset(str(t).lower() for t in (fm_tags if isinstance(fm_tags, list) else []))

    doc = ParsedDocument(
        path=rel_path,
        title=title,
        content=body,
        metadata=metadata,
        wiki_links=extract_wiki_links(body),
        tags=extract_tags(body) | fm_tag_set,
        urls=extract_urls(body),
    )

    logger.info(
        "markdown_parsed",
        path=rel_path,
        title=title,
        wiki_links=len(doc.wiki_links),
        tags=len(doc.tags),
        urls=len(doc.urls),
    )
    return doc
