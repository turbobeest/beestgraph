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
    """Return a Zettelkasten timestamp ID in ``YYYYMMDDHHMM`` format (UTC)."""
    return datetime.now(tz=UTC).strftime("%Y%m%d%H%M")


# ---------------------------------------------------------------------------
# Content types (canonical list)
# ---------------------------------------------------------------------------

CONTENT_TYPES: list[str] = [
    "article",
    "concept",
    "reference",
    "note",
    "quote",
    "project",
    "decision",
    "meeting",
    "daily",
    "journal",
    "moc",
    "person",
    "organization",
    "tool",
    "place",
    "book",
    "film",
    "podcast",
    "thread",
    "repo",
    "email",
    "recipe",
    "event",
    "health",
    "financial",
    "dream",
    "collection",
    "synthesis",
]

# ---------------------------------------------------------------------------
# URL-based classification
# ---------------------------------------------------------------------------

_URL_TYPE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"github\.com/[^/]+/[^/]+/(?:issues|pull)/\d+"), "article"),
    (re.compile(r"github\.com/[^/]+/[^/]+/?$"), "repo"),
    (re.compile(r"(x\.com|twitter\.com)/[^/]+/status/"), "thread"),
    (re.compile(r"youtube\.com/watch|youtu\.be/"), "film"),
    (re.compile(r"vimeo\.com/\d+"), "film"),
    (re.compile(r"arxiv\.org/(?:abs|pdf)/"), "article"),
    (re.compile(r"scholar\.google\.com"), "article"),
    (re.compile(r"\.pdf(?:\?|$)"), "article"),
    (re.compile(r"reddit\.com/r/"), "thread"),
    (re.compile(r"news\.ycombinator\.com/item"), "thread"),
    (re.compile(r"stackoverflow\.com/questions/"), "thread"),
    (re.compile(r"linkedin\.com/posts/"), "thread"),
    (re.compile(r"mastodon\.\w+/"), "thread"),
    (re.compile(r"podcasts?\.(apple|google)|spotify\.com/episode"), "podcast"),
    (re.compile(r"goodreads\.com/book/"), "book"),
    (re.compile(r"coursera\.org/|udemy\.com/course/|edx\.org/"), "reference"),
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
        return "reference"

    reference_hits = sum(1 for kw in _REFERENCE_KEYWORDS if kw in text)
    if reference_hits >= 2:
        return "reference"

    # Check for code-heavy content
    code_fence_count = content.count("```")
    if code_fence_count >= 4:
        return "reference"

    return "article"


# ---------------------------------------------------------------------------
# Quality assessment
# ---------------------------------------------------------------------------

_MIN_HIGH_QUALITY_LENGTH = 1500
_MIN_MEDIUM_QUALITY_LENGTH = 400


def _assess_confidence(doc: ParsedDocument) -> float:
    """Assess confidence based on length, structure, and attribution.

    Args:
        doc: Parsed markdown document.

    Returns:
        A confidence score between 0.0 and 1.0.
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
    source = doc.metadata.get("source", {})
    has_author = doc.metadata.get("author") or (isinstance(source, dict) and source.get("author"))
    has_url = doc.metadata.get("source_url") or (isinstance(source, dict) and source.get("url"))
    if has_author or has_url:
        score += 1

    # Links and references indicate depth
    if len(doc.urls) >= 3 or len(doc.wiki_links) >= 2:
        score += 1

    if score >= 4:
        return 0.85
    if score >= 2:
        return 0.5
    return 0.3


# ---------------------------------------------------------------------------
# LLM classification via Claude Code headless
# ---------------------------------------------------------------------------

_CLASSIFY_PROMPT = """Classify this document and return ONLY a JSON object (no markdown fences):
{{
  "type": "<one of: {types}>",
  "topic": "<topic/subtopic from taxonomy, e.g. technology/ai-ml>",
  "tags": ["tag1", "tag2", "tag3"],
  "confidence": <0.0-1.0 confidence score>,
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
    source = doc.metadata.get("source", {})
    source_url = doc.metadata.get("source_url", "")
    if not source_url and isinstance(source, dict):
        source_url = source.get("url", "")
    prompt = _CLASSIFY_PROMPT.format(
        types=", ".join(CONTENT_TYPES),
        title=doc.title,
        url=source_url,
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

    # Validate type (accept both old "content_type" and new "type" keys)
    ct = data.get("type", data.get("content_type", "article"))
    if ct not in CONTENT_TYPES:
        ct = "article"

    # Parse confidence: accept float directly or convert from quality string
    raw_confidence = data.get("confidence", data.get("quality", 0.5))
    if isinstance(raw_confidence, str):
        confidence = {"high": 0.85, "medium": 0.5, "low": 0.3}.get(raw_confidence, 0.5)
    else:
        confidence = float(raw_confidence) if raw_confidence else 0.5

    return {
        "type": ct,
        "topic": data.get("topic", ""),
        "tags": data.get("tags", []),
        "confidence": confidence,
        "importance": 3,
        "summary": data.get("summary", ""),
        "uid": _generate_zettelkasten_id(),
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
                type=classification["type"],
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
    source = doc.metadata.get("source", {})
    source_url = str(doc.metadata.get("source_url", ""))
    if not source_url and isinstance(source, dict):
        source_url = str(source.get("url", ""))

    # Content type: URL first, then content analysis
    content_type = _classify_by_url(source_url) or _classify_by_content(doc.content, doc.title)

    # Topic: reuse processor keyword matching
    from src.pipeline.processor import _guess_topics

    topics = _guess_topics(doc.content.lower())
    topic = topics[0] if topics else ""

    # Tags: combine frontmatter tags with inline tags
    tags = sorted(doc.tags)[:10]

    # Confidence
    confidence = _assess_confidence(doc)

    # Summary: first substantial line
    summary = str(doc.metadata.get("summary", ""))
    if not summary:
        for line in doc.content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and len(stripped) > 30:
                summary = stripped[:250].rstrip(".") + "."
                break

    classification = {
        "type": content_type,
        "topic": topic,
        "tags": tags,
        "confidence": confidence,
        "importance": 3,
        "summary": summary,
        "uid": _generate_zettelkasten_id(),
    }

    logger.info(
        "document_classified",
        path=doc.path,
        method="fallback",
        type=content_type,
    )
    return classification
