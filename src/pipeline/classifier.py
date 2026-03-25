"""AI content classifier for the qualification pipeline.

Pre-classifies captured content by recommending a content_type, topic, tags,
quality score, and summary.  Tries Claude Code headless first, then falls back
to URL-pattern and keyword heuristics.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime

import structlog

from src.pipeline.markdown_parser import ParsedDocument

logger = structlog.get_logger(__name__)


def _generate_zettelkasten_id() -> str:
    """Return a Zettelkasten timestamp ID in ``YYYYMMDDHHMMSS`` format (UTC)."""
    return datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")


# ---------------------------------------------------------------------------
# Content types (canonical list)
# ---------------------------------------------------------------------------

CONTENT_TYPES: list[str] = [
    "article",
    "paper",
    "tutorial",
    "reference",
    "thought",
    "note",
    "video",
    "podcast",
    "image",
    "pdf",
    "tweet",
    "social-post",
    "discussion",
    "url",
    "github-repo",
    "github-issue",
    "code-snippet",
    "tool",
    "recipe",
    "product",
    "place",
    "event",
    "person",
    "book",
    "course",
]

# ---------------------------------------------------------------------------
# URL-based classification
# ---------------------------------------------------------------------------

_URL_TYPE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"github\.com/[^/]+/[^/]+/(?:issues|pull)/\d+"), "github-issue"),
    (re.compile(r"github\.com/[^/]+/[^/]+/?$"), "github-repo"),
    (re.compile(r"(x\.com|twitter\.com)/[^/]+/status/"), "tweet"),
    (re.compile(r"youtube\.com/watch|youtu\.be/"), "video"),
    (re.compile(r"vimeo\.com/\d+"), "video"),
    (re.compile(r"arxiv\.org/(?:abs|pdf)/"), "paper"),
    (re.compile(r"scholar\.google\.com"), "paper"),
    (re.compile(r"\.pdf(?:\?|$)"), "pdf"),
    (re.compile(r"reddit\.com/r/"), "discussion"),
    (re.compile(r"news\.ycombinator\.com/item"), "discussion"),
    (re.compile(r"stackoverflow\.com/questions/"), "discussion"),
    (re.compile(r"linkedin\.com/posts/"), "social-post"),
    (re.compile(r"mastodon\.\w+/"), "social-post"),
    (re.compile(r"podcasts?\.(apple|google)|spotify\.com/episode"), "podcast"),
    (re.compile(r"goodreads\.com/book/"), "book"),
    (re.compile(r"coursera\.org/|udemy\.com/course/|edx\.org/"), "course"),
]


def _classify_by_url(url: str) -> str | None:
    """Guess content_type from URL domain/pattern.

    Args:
        url: Source URL string.

    Returns:
        A content_type string, or ``None`` if no pattern matched.
    """
    if not url:
        return None
    for pattern, content_type in _URL_TYPE_PATTERNS:
        if pattern.search(url):
            return content_type
    return None


# ---------------------------------------------------------------------------
# Content-based classification
# ---------------------------------------------------------------------------

_RECIPE_KEYWORDS = [
    "ingredients",
    "servings",
    "prep time",
    "cook time",
    "tablespoon",
    "teaspoon",
    "preheat",
    "bake",
]

_TUTORIAL_KEYWORDS = [
    "step 1",
    "step 2",
    "how to",
    "getting started",
    "walkthrough",
    "tutorial",
    "guide",
    "set up",
    "install",
]

_REFERENCE_KEYWORDS = [
    "api reference",
    "documentation",
    "specification",
    "man page",
    "cheat sheet",
    "syntax",
]


def _classify_by_content(content: str, title: str) -> str:
    """Guess content_type from content keywords.

    Args:
        content: Document body text.
        title: Document title.

    Returns:
        Best-guess content_type string.
    """
    text = (title + " " + content).lower()

    recipe_hits = sum(1 for kw in _RECIPE_KEYWORDS if kw in text)
    if recipe_hits >= 3:
        return "recipe"

    tutorial_hits = sum(1 for kw in _TUTORIAL_KEYWORDS if kw in text)
    if tutorial_hits >= 2:
        return "tutorial"

    reference_hits = sum(1 for kw in _REFERENCE_KEYWORDS if kw in text)
    if reference_hits >= 2:
        return "reference"

    # Check for code-heavy content
    code_fence_count = content.count("```")
    if code_fence_count >= 4:
        return "code-snippet"

    return "article"


# ---------------------------------------------------------------------------
# Quality assessment
# ---------------------------------------------------------------------------

_MIN_HIGH_QUALITY_LENGTH = 1500
_MIN_MEDIUM_QUALITY_LENGTH = 400


def _assess_quality(doc: ParsedDocument) -> str:
    """Assess quality based on length, structure, and attribution.

    Args:
        doc: Parsed markdown document.

    Returns:
        One of ``"high"``, ``"medium"``, or ``"low"``.
    """
    score = 0
    content_len = len(doc.content)

    # Length scoring
    if content_len >= _MIN_HIGH_QUALITY_LENGTH:
        score += 2
    elif content_len >= _MIN_MEDIUM_QUALITY_LENGTH:
        score += 1

    # Structure: headings indicate organized content
    heading_count = doc.content.count("\n#")
    if heading_count >= 3:
        score += 1

    # Attribution: has an author or source URL
    if doc.metadata.get("author") or doc.metadata.get("source_url"):
        score += 1

    # Links and references indicate depth
    if len(doc.urls) >= 3 or len(doc.wiki_links) >= 2:
        score += 1

    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# LLM classification via Claude Code headless
# ---------------------------------------------------------------------------

_CLASSIFY_PROMPT = """Classify this document and return ONLY a JSON object (no markdown fences):
{{
  "content_type": "<one of: {types}>",
  "topic": "<topic/subtopic from taxonomy, e.g. technology/ai-ml>",
  "tags": ["tag1", "tag2", "tag3"],
  "quality": "<high|medium|low>",
  "summary": "<2-3 sentence summary>"
}}

Document title: {title}
Source URL: {url}
Document content (first 4000 chars):
{content}"""

_CLASSIFY_TIMEOUT_SECONDS = 45


def _llm_classify(doc: ParsedDocument) -> dict[str, object]:
    """Classify a document using Claude Code headless.

    Args:
        doc: Parsed markdown document.

    Returns:
        Dict with keys: content_type, topic, tags, quality, summary.

    Raises:
        RuntimeError: If the Claude Code subprocess fails.
    """
    prompt = _CLASSIFY_PROMPT.format(
        types=", ".join(CONTENT_TYPES),
        title=doc.title,
        url=doc.metadata.get("source_url", ""),
        content=doc.content[:4000],
    )

    result = subprocess.run(  # noqa: S603
        ["claude", "-p", prompt],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=_CLASSIFY_TIMEOUT_SECONDS,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude Code exited {result.returncode}: {result.stderr}")

    raw = result.stdout.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        lines = [ln for ln in lines if not ln.startswith("```")]
        raw = "\n".join(lines)

    data = json.loads(raw)

    # Validate content_type
    ct = data.get("content_type", "article")
    if ct not in CONTENT_TYPES:
        ct = "article"

    quality = data.get("quality", "medium")
    if quality not in ("high", "medium", "low"):
        quality = "medium"

    return {
        "content_type": ct,
        "topic": data.get("topic", ""),
        "tags": data.get("tags", []),
        "quality": quality,
        "summary": data.get("summary", ""),
        "visibility": "private",
        "id": _generate_zettelkasten_id(),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_document(doc: ParsedDocument, enable_llm: bool = True) -> dict[str, object]:
    """Classify a document using Claude Code headless or fallback heuristics.

    Args:
        doc: Parsed markdown document.
        enable_llm: Whether to attempt LLM classification first.

    Returns:
        Dict with keys: content_type, topic, tags, quality, summary.
    """
    if enable_llm:
        try:
            classification = _llm_classify(doc)
            logger.info(
                "document_classified",
                path=doc.path,
                method="llm",
                content_type=classification["content_type"],
            )
            return classification
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            json.JSONDecodeError,
            RuntimeError,
            FileNotFoundError,
            KeyError,
        ) as exc:
            logger.warning(
                "llm_classification_failed_using_fallback",
                path=doc.path,
                error=str(exc),
            )

    # Fallback heuristic classification
    source_url = str(doc.metadata.get("source_url", ""))

    # Content type: URL first, then content analysis
    content_type = _classify_by_url(source_url) or _classify_by_content(doc.content, doc.title)

    # Topic: reuse processor keyword matching
    from src.pipeline.processor import _guess_topics

    topics = _guess_topics(doc.content.lower())
    topic = topics[0] if topics else ""

    # Tags: combine frontmatter tags with inline tags
    tags = sorted(doc.tags)[:10]

    # Quality
    quality = _assess_quality(doc)

    # Summary: first substantial line
    summary = str(doc.metadata.get("summary", ""))
    if not summary:
        for line in doc.content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and len(stripped) > 30:
                summary = stripped[:250].rstrip(".") + "."
                break

    classification = {
        "content_type": content_type,
        "topic": topic,
        "tags": tags,
        "quality": quality,
        "summary": summary,
        "visibility": "private",
        "id": _generate_zettelkasten_id(),
    }

    logger.info(
        "document_classified",
        path=doc.path,
        method="fallback",
        content_type=content_type,
    )
    return classification
