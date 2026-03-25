"""Markdown auto-formatting pipeline with three progressive levels.

Level 1 -- Capture: clean up raw markdown on inbox arrival.
Level 2 -- Qualification: enrich structure when entering the review queue.
Level 3 -- Publication: validate style compliance before permanent storage.

All formatting functions are pure (no side effects, no imports from beestgraph
modules) so they can be tested and used independently.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import urlparse

# Compiled regex patterns -------------------------------------------------------

_CRLF_RE = re.compile(r"\r\n?")
_TRAILING_WS_RE = re.compile(r"[ \t]+$", re.MULTILINE)
_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_HEADING_LEVEL_RE = re.compile(r"^(#{1,6})\s", re.MULTILINE)
_BARE_URL_RE = re.compile(r"(?<!\()(?<!\]\()(?<!<)(https?://[^\s\)\]>\"'`]+)(?!\))")
_MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\([^\)]*\)")
_CODE_SPAN_RE = re.compile(r"`[^`]+`")
_CODE_BLOCK_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
_LIST_MARKER_RE = re.compile(r"^([\t ]*)([*+])\s", re.MULTILINE)
_WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
_CODE_BLOCK_LANG_RE = re.compile(r"^```(\w*)\s*$", re.MULTILINE)

_MOJIBAKE_MAP: dict[str, str] = {
    "\u00e2\u0080\u0099": "\u2019",
    "\u00e2\u0080\u009c": "\u201c",
    "\u00e2\u0080\u009d": "\u201d",
    "\u00e2\u0080\u0093": "\u2013",
    "\u00e2\u0080\u0094": "\u2014",
    "\u00e2\u0080\u00a6": "\u2026",
    "\u00c2\u00a0": " ",
    "\u00ef\u00bb\u00bf": "",
}

_TAKEAWAY_TYPES = frozenset({"article", "paper", "tutorial", "video", "book"})

# Helpers -----------------------------------------------------------------------


def generate_zettelkasten_id() -> str:
    """Generate a Zettelkasten timestamp ID: YYYYMMDDHHMMSS."""
    return datetime.now(UTC).strftime("%Y%m%d%H%M%S")


def extract_domain(url: str) -> str:
    """Extract display domain from a URL (strips ``www.`` prefix)."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        return domain.removeprefix("www.") or url
    except Exception:
        return url


def has_section(content: str, heading: str) -> bool:
    """Check if a ``## heading`` exists (case-insensitive)."""
    pat = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE | re.IGNORECASE)
    return bool(pat.search(content))


def collapse_blank_lines(content: str, max_consecutive: int = 2) -> str:
    """Collapse runs of blank lines to *max_consecutive*."""
    limit = max_consecutive + 2  # N blank lines = N+1 newlines
    return re.sub(r"\n{" + str(limit) + r",}", "\n" * (max_consecutive + 1), content)


def normalize_heading_spacing(content: str) -> str:
    """Ensure one blank line before and after each heading."""
    lines = content.split("\n")
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        is_heading = bool(re.match(r"^#{1,6}\s+", stripped))
        if is_heading:
            if result and result[-1].strip() != "":
                result.append("")
            result.append(line)
        else:
            if result and re.match(r"^#{1,6}\s+", result[-1].strip()) and stripped != "":
                result.append("")
            result.append(line)
    return "\n".join(result)


def normalize_list_markers(content: str) -> str:
    """Convert ``*`` and ``+`` unordered list markers to ``-``."""
    return _LIST_MARKER_RE.sub(r"\1- ", content)


def _protected_ranges(content: str) -> list[tuple[int, int]]:
    """Return character ranges occupied by code blocks, code spans, and links."""
    ranges: list[tuple[int, int]] = []
    for pat in (_CODE_BLOCK_RE, _CODE_SPAN_RE, _MARKDOWN_LINK_RE):
        for m in pat.finditer(content):
            ranges.append((m.start(), m.end()))
    return ranges


def normalize_bare_urls(content: str) -> str:
    """Convert bare URLs to ``[domain](url)`` format, skipping protected spans."""
    protected = _protected_ranges(content)

    def _is_safe(s: int, e: int) -> bool:
        return not any(ps <= s and e <= pe for ps, pe in protected)

    parts: list[str] = []
    last = 0
    for m in _BARE_URL_RE.finditer(content):
        url, s, e = m.group(1), m.start(1), m.end(1)
        if not _is_safe(s, e) or (s > 0 and content[s - 1] == "("):
            continue
        parts.append(content[last:s])
        parts.append(f"[{extract_domain(url)}]({url})")
        last = e
    parts.append(content[last:])
    return "".join(parts)


def ensure_h1(content: str, title: str) -> str:
    """Prepend ``# {title}`` if no H1 exists."""
    if _H1_RE.search(content):
        return content
    return f"# {title}\n\n{content}"


def inject_summary_blockquote(content: str, summary: str) -> str:
    """Add ``> {summary}`` after the H1 if not already present."""
    if not summary:
        return content
    h1 = _H1_RE.search(content)
    if not h1:
        return content
    after = content[h1.end() :].lstrip("\n")
    if after.startswith(">"):
        return content
    pos = h1.end()
    return content[:pos] + f"\n\n> {summary}" + content[pos:]


def add_section_if_missing(content: str, heading: str, default_content: str) -> str:
    """Append a ``## heading`` at the end if it does not already exist."""
    if has_section(content, heading):
        return content
    if not content.endswith("\n"):
        content += "\n"
    return content + f"\n## {heading}\n\n{default_content}\n"


# Level 1: Capture formatting ---------------------------------------------------


def format_on_capture(content: str, title: str = "") -> str:
    """Clean up raw captured markdown for inbox storage.

    Applied automatically to every file entering the inbox. Normalizes line
    endings, fixes mojibake, strips trailing whitespace, collapses blank lines,
    normalizes headings/lists/URLs, and ensures an H1 exists.

    Args:
        content: Raw markdown body (without frontmatter fences).
        title: Document title from frontmatter for H1 generation.

    Returns:
        Cleaned markdown text with a single trailing newline.
    """
    content = _CRLF_RE.sub("\n", content)
    for bad, good in _MOJIBAKE_MAP.items():
        content = content.replace(bad, good)
    content = _TRAILING_WS_RE.sub("", content)
    content = collapse_blank_lines(content, max_consecutive=2)
    content = normalize_heading_spacing(content)
    content = normalize_bare_urls(content)
    content = normalize_list_markers(content)
    if title:
        content = ensure_h1(content, title)
    return content.rstrip("\n") + "\n"


# Level 2: Qualification formatting ----------------------------------------------


def format_on_qualify(content: str, frontmatter: dict[str, object]) -> str:
    """Enrich markdown structure for qualification review.

    Applied when a file moves from inbox to the qualification queue. Runs
    capture formatting first, then injects summary blockquote, structural
    sections (Key Takeaways, Sources, Connections) based on content type.

    Args:
        content: Markdown body text (without frontmatter fences).
        frontmatter: Parsed frontmatter dict.

    Returns:
        Enriched markdown text with a single trailing newline.
    """
    title = str(frontmatter.get("title", ""))
    content = format_on_capture(content, title=title)

    summary = str(frontmatter.get("summary", "") or "")
    if summary:
        content = inject_summary_blockquote(content, summary)

    ctype = str(frontmatter.get("content_type", frontmatter.get("type", "")))
    if ctype in _TAKEAWAY_TYPES:
        content = add_section_if_missing(content, "Key Takeaways", "- (to be added)")

    source_url = str(frontmatter.get("source_url", "") or "")
    if source_url:
        domain = extract_domain(source_url)
        content = add_section_if_missing(content, "Sources", f"- [{domain}]({source_url})")

    content = add_section_if_missing(content, "Connections", "- Related: (to be linked)")
    return content.rstrip("\n") + "\n"


# Level 3: Publication validation -------------------------------------------------


def validate_for_publication(content: str, frontmatter: dict[str, object]) -> list[str]:
    """Validate markdown meets the style guide for permanent storage.

    Returns a list of issues (empty = ready to publish). Does NOT modify content.

    Args:
        content: Markdown body text (without frontmatter fences).
        frontmatter: Parsed frontmatter dict.

    Returns:
        List of issue description strings.
    """
    issues: list[str] = []
    title = str(frontmatter.get("title", ""))

    # 1. H1 present and matches frontmatter title
    h1 = _H1_RE.search(content)
    if not h1:
        issues.append("Missing H1 heading")
    elif title and h1.group(1).strip() != title.strip():
        issues.append(f"H1 '{h1.group(1).strip()}' does not match title '{title}'")

    # 2. No heading level skips
    levels = [len(m.group(1)) for m in _HEADING_LEVEL_RE.finditer(content)]
    for i in range(1, len(levels)):
        if levels[i] > levels[i - 1] + 1:
            issues.append(f"Heading skip: H{levels[i - 1]} -> H{levels[i]}")

    # 3. Summary blockquote after H1
    if h1:
        after = content[h1.end() :].lstrip("\n")
        if not after.startswith(">"):
            issues.append("Missing summary blockquote after H1")

    # 4. Key Takeaways for applicable types
    ctype = str(frontmatter.get("content_type", frontmatter.get("type", "")))
    if ctype in _TAKEAWAY_TYPES and not has_section(content, "Key Takeaways"):
        issues.append(f"Missing 'Key Takeaways' section (required for '{ctype}')")

    # 5. Sources section for external captures
    if str(frontmatter.get("source_url", "") or "") and not has_section(content, "Sources"):
        issues.append("Missing 'Sources' section (source_url present)")

    # 6. No bare URLs
    protected = _protected_ranges(content)
    for m in _BARE_URL_RE.finditer(content):
        s, e = m.start(1), m.end(1)
        if not any(ps <= s and e <= pe for ps, pe in protected) and (
            s > 0 and content[s - 1] != "("
        ):
            issues.append(f"Bare URL: {m.group(1)[:60]}...")
            break

    # 7. Code blocks have language tags (warning)
    for m in _CODE_BLOCK_LANG_RE.finditer(content):
        if not m.group(1):
            issues.append("Code block without language tag (warning)")
            break

    # 8. Content not empty (> 10 words)
    body = re.sub(r"^[#>].*$", "", content, flags=re.MULTILINE)
    if len(body.split()) < 10:
        issues.append(f"Content too short ({len(body.split())} words, minimum 10)")

    # 9. Wiki-link or Connections section
    if not _WIKI_LINK_RE.search(content) and not has_section(content, "Connections"):
        issues.append("No wiki-links or Connections section (warning)")

    return issues
