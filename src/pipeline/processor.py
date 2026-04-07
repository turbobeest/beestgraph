"""Document processor — AI-powered or fallback entity extraction and categorisation.

When ``enable_llm=True``, invokes Claude Code headless to extract entities,
assign topics, and generate a summary.  When LLM processing is disabled (or
fails), a rule-based fallback extracts keywords, basic entities, and a
topic guess from the document content.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import replace

import structlog

from src.pipeline.markdown_parser import ParsedDocument

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants for fallback processing
# ---------------------------------------------------------------------------

_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "technology/programming": [
        "python",
        "javascript",
        "typescript",
        "rust",
        "golang",
        "api",
        "sdk",
        "framework",
        "library",
        "git",
        "code",
        "software",
        "developer",
    ],
    "technology/ai-ml": [
        "machine learning",
        "deep learning",
        "neural",
        "llm",
        "gpt",
        "transformer",
        "ai",
        "artificial intelligence",
        "model",
        "training",
        "inference",
    ],
    "technology/infrastructure": [
        "docker",
        "kubernetes",
        "linux",
        "server",
        "cloud",
        "aws",
        "deploy",
        "ci/cd",
        "terraform",
        "ansible",
        "raspberry pi",
    ],
    "technology/security": [
        "security",
        "vulnerability",
        "encryption",
        "auth",
        "oauth",
        "firewall",
        "vpn",
        "tailscale",
        "zero trust",
    ],
    "technology/web": [
        "react",
        "next.js",
        "html",
        "css",
        "frontend",
        "backend",
        "browser",
        "web",
        "http",
        "rest",
    ],
    "science/mathematics": ["math", "algebra", "calculus", "statistics", "theorem"],
    "science/physics": ["physics", "quantum", "relativity", "particle"],
    "science/biology": ["biology", "gene", "cell", "evolution", "dna"],
    "business/startups": ["startup", "founder", "venture", "fundraise", "pitch"],
    "business/finance": ["finance", "investment", "stock", "portfolio", "trading"],
    "culture/books": ["book", "novel", "author", "reading", "literature"],
    "meta/pkm": [
        "knowledge graph",
        "obsidian",
        "zettelkasten",
        "note-taking",
        "pkm",
        "second brain",
        "knowledge management",
    ],
}

_CAPITALIZED_WORD_RE = re.compile(r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})+)\b")


# ---------------------------------------------------------------------------
# Fallback (no-LLM) processing
# ---------------------------------------------------------------------------


def _guess_topics(text: str) -> list[str]:
    """Match document text against keyword lists to guess topics.

    Args:
        text: Lowercased document body.

    Returns:
        List of matched topic paths, sorted by match count descending.
    """
    scores: dict[str, int] = {}
    for topic, keywords in _TOPIC_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            scores[topic] = count
    return sorted(scores, key=scores.__getitem__, reverse=True)[:3]


def _extract_capitalized_names(text: str) -> list[str]:
    """Extract potential person/org names as consecutive capitalised words.

    Args:
        text: Raw document body (original casing).

    Returns:
        Deduplicated list of candidate names.
    """
    seen: set[str] = set()
    names: list[str] = []
    for match in _CAPITALIZED_WORD_RE.finditer(text):
        name = match.group(1).strip()
        if name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)
    return names[:20]


def _fallback_process(doc: ParsedDocument) -> ParsedDocument:
    """Enrich a document using rule-based heuristics (no LLM).

    Args:
        doc: Parsed markdown document.

    Returns:
        A new ``ParsedDocument`` with enriched metadata (topics, entities).
    """
    text_lower = doc.content.lower()
    meta = dict(doc.metadata)

    # Guess topics
    if not meta.get("topics"):
        topics = _guess_topics(text_lower)
        if topics:
            meta["topics"] = topics

    # Extract candidate entities
    if not meta.get("entities"):
        names = _extract_capitalized_names(doc.content)
        if names:
            meta["entities"] = {"people": names[:10], "concepts": [], "organizations": []}

    # Generate a basic summary (first non-empty, non-heading line)
    if not meta.get("summary"):
        for line in doc.content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and len(stripped) > 30:
                summary = stripped[:250].rstrip(".") + "."
                meta["summary"] = summary
                break

    return replace(doc, metadata=meta)


# ---------------------------------------------------------------------------
# LLM-powered processing via Claude Code headless
# ---------------------------------------------------------------------------

_CLAUDE_PROMPT = """Analyze this document and return ONLY a JSON object (no markdown fences):
{{
  "summary": "2-3 sentence summary",
  "topics": ["topic/subtopic"],
  "entities": {{
    "people": ["Name"],
    "concepts": ["Concept"],
    "organizations": ["Org"]
  }},
  "para": "resources|projects|areas|archives"
}}

Document title: {title}
Document content:
{content}"""

_CLAUDE_TIMEOUT_SECONDS = 60


def _llm_process(doc: ParsedDocument) -> ParsedDocument:
    """Enrich a document using Claude Code headless for AI extraction.

    Args:
        doc: Parsed markdown document.

    Returns:
        A new ``ParsedDocument`` with AI-enriched metadata.

    Raises:
        RuntimeError: If the Claude Code subprocess fails.
    """
    prompt = _CLAUDE_PROMPT.format(
        title=doc.title,
        content=doc.content[:8000],  # Limit content length for the prompt
    )

    result = subprocess.run(  # noqa: S603
        ["claude", "-p", prompt],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=_CLAUDE_TIMEOUT_SECONDS,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude Code exited with code {result.returncode}: {result.stderr}")

    raw_output = result.stdout.strip()

    # Strip markdown code fences if present
    if raw_output.startswith("```"):
        lines = raw_output.splitlines()
        lines = [ln for ln in lines if not ln.startswith("```")]
        raw_output = "\n".join(lines)

    extraction = json.loads(raw_output)
    meta = dict(doc.metadata)

    if extraction.get("summary"):
        meta["summary"] = extraction["summary"]
    if extraction.get("topics"):
        meta["topics"] = extraction["topics"]
    if extraction.get("entities"):
        meta["entities"] = extraction["entities"]
    if extraction.get("para"):
        meta["para"] = extraction["para"]
    elif extraction.get("para_category"):
        meta["para"] = extraction["para_category"]

    return replace(doc, metadata=meta)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def process_document(doc: ParsedDocument, enable_llm: bool = True) -> ParsedDocument:
    """Run entity extraction and categorisation on a parsed document.

    Tries LLM-powered processing first (when enabled).  Falls back to
    rule-based heuristics on any failure.

    Args:
        doc: A parsed markdown document.
        enable_llm: Whether to attempt Claude Code headless processing.

    Returns:
        An enriched ``ParsedDocument`` with topics, entities, and summary.
    """
    start = time.monotonic()
    method = "fallback"

    if enable_llm:
        try:
            enriched = _llm_process(doc)
            method = "llm"
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.info(
                "document_processed",
                path=doc.path,
                method=method,
                elapsed_ms=round(elapsed_ms, 1),
            )
            return enriched
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            json.JSONDecodeError,
            RuntimeError,
            FileNotFoundError,
            KeyError,
        ) as exc:
            logger.warning(
                "llm_processing_failed_using_fallback",
                path=doc.path,
                error=str(exc),
            )

    enriched = _fallback_process(doc)
    elapsed_ms = (time.monotonic() - start) * 1000
    logger.info(
        "document_processed",
        path=doc.path,
        method=method,
        elapsed_ms=round(elapsed_ms, 1),
    )
    return enriched
