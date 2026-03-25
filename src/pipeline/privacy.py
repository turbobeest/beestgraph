"""Deterministic privacy classification for vault notes.

Computes visibility based on hard rules — not AI judgment. Nothing is
public unless explicitly approved by a human AND passing all automated checks.

The three barriers:
    1. **Deterministic classification** — rules-based private-by-default
    2. **LLM content boundaries** — private content never sent to LLMs in full
    3. **Publish gate** — public requires explicit human action + scan pass
"""

from __future__ import annotations

import re

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Private-by-default rules
# ---------------------------------------------------------------------------

# Content types that are ALWAYS private (personal/work content)
_ALWAYS_PRIVATE_TYPES: frozenset[str] = frozenset(
    {
        "project",
        "area",
        "daily",
        "fleeting",
        "meeting",
        "thought",
        "person",
    }
)

# PARA categories that are ALWAYS private
_ALWAYS_PRIVATE_PARA: frozenset[str] = frozenset(
    {
        "projects",
        "areas",
    }
)

# Source types that default to private (user-created content)
_PRIVATE_SOURCE_TYPES: frozenset[str] = frozenset(
    {
        "manual",
        "telegram",
    }
)

# Content types eligible for public visibility
_PUBLIC_ELIGIBLE_TYPES: frozenset[str] = frozenset(
    {
        "article",
        "paper",
        "tutorial",
        "reference",
        "video",
        "podcast",
        "tweet",
        "social-post",
        "discussion",
        "url",
        "github-repo",
        "github-issue",
        "code-snippet",
        "tool",
        "book",
        "course",
        "recipe",
        "product",
    }
)

# Keywords in title or content that force private
_PRIVATE_KEYWORDS: re.Pattern[str] = re.compile(
    r"(?i)\b("
    r"salary|compensation|pay\s*stub|w-?2|1099|tax\s*return|"
    r"medical|diagnosis|prescription|hipaa|"
    r"legal|attorney|nda|confidential|"
    r"password|credential|secret|private\s*key|"
    r"ssn|social\s*security|"
    r"bank\s*account|routing\s*number|"
    r"contract|agreement|offer\s*letter"
    r")\b"
)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def classify_visibility(
    *,
    content_type: str = "",
    para: str = "",
    source_type: str = "",
    title: str = "",
    content: str = "",
    security_scan_passed: bool = True,
    user_set_visibility: str = "",
) -> str:
    """Determine visibility using deterministic rules.

    Args:
        content_type: The note's content type (article, project, etc.).
        para: The PARA category (projects, areas, resources, archive).
        source_type: How the note was captured.
        title: The note title.
        content: The note body text.
        security_scan_passed: Whether the security scanner found no high-severity items.
        user_set_visibility: Explicit visibility set by the user (overrides if valid).

    Returns:
        One of: "private", "public", "shared".
    """
    # User explicitly set visibility — respect it, but validate
    if user_set_visibility == "public":
        # Public requires passing all checks
        issues = validate_can_be_public(
            content_type=content_type,
            para=para,
            title=title,
            content=content,
            security_scan_passed=security_scan_passed,
        )
        if issues:
            logger.warning(
                "public_visibility_denied",
                issues=issues,
                title=title[:50],
            )
            return "private"
        return "public"

    if user_set_visibility == "shared":
        # Shared is allowed for anything except security-flagged content
        if not security_scan_passed:
            return "private"
        return "shared"

    if user_set_visibility == "private":
        return "private"

    # No explicit user choice — apply rules
    # Rule 1: Security scan failure = always private
    if not security_scan_passed:
        return "private"

    # Rule 2: Always-private content types
    if content_type in _ALWAYS_PRIVATE_TYPES:
        return "private"

    # Rule 3: Always-private PARA categories
    if para in _ALWAYS_PRIVATE_PARA:
        return "private"

    # Rule 4: User-created content defaults to private
    if source_type in _PRIVATE_SOURCE_TYPES:
        return "private"

    # Rule 5: Private keywords in title or content
    if _PRIVATE_KEYWORDS.search(title) or _PRIVATE_KEYWORDS.search(content[:2000]):
        return "private"

    # Default: private (nothing is public without explicit human action)
    return "private"


def validate_can_be_public(
    *,
    content_type: str = "",
    para: str = "",
    title: str = "",
    content: str = "",
    security_scan_passed: bool = True,
) -> list[str]:
    """Check if a note is eligible to be made public.

    Args:
        content_type: The note's content type.
        para: The PARA category.
        title: The note title.
        content: The note body text.
        security_scan_passed: Whether the security scanner passed.

    Returns:
        List of reasons the note cannot be public. Empty = eligible.
    """
    issues: list[str] = []

    if not security_scan_passed:
        issues.append("Security scan detected sensitive data")

    if content_type in _ALWAYS_PRIVATE_TYPES:
        issues.append(f"Content type '{content_type}' is always private")

    if para in _ALWAYS_PRIVATE_PARA:
        issues.append(f"PARA category '{para}' is always private")

    if content_type and content_type not in _PUBLIC_ELIGIBLE_TYPES:
        issues.append(f"Content type '{content_type}' is not eligible for public")

    if _PRIVATE_KEYWORDS.search(title):
        issues.append("Title contains private keywords")

    if _PRIVATE_KEYWORDS.search(content[:2000]):
        issues.append("Content contains private keywords")

    return issues


# ---------------------------------------------------------------------------
# LLM content boundary
# ---------------------------------------------------------------------------


def filter_for_llm(
    title: str,
    content: str,
    summary: str,
    visibility: str,
) -> str:
    """Return content appropriate for LLM context based on visibility.

    This is the boundary that prevents private content from leaking
    through LLM responses.

    Args:
        title: Note title.
        content: Full note body.
        summary: Note summary.
        visibility: The note's visibility level.

    Returns:
        Filtered content string safe for LLM consumption.
    """
    if visibility == "public":
        return f"[PUBLIC] {title}\n{content}"

    if visibility == "shared":
        safe_summary = summary or "(no summary)"
        return f"[SHARED] {title}: {safe_summary}"

    # Private — title only, no content
    return f"[PRIVATE] {title} (content restricted)"
