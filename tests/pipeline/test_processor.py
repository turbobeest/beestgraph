"""Tests for src.pipeline.processor — AI and fallback document enrichment."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

from src.pipeline.markdown_parser import ParsedDocument
from src.pipeline.processor import (
    _extract_capitalized_names,
    _fallback_process,
    _guess_topics,
    process_document,
)

# ---------------------------------------------------------------------------
# _guess_topics
# ---------------------------------------------------------------------------


class TestGuessTopics:
    """Tests for the keyword-based topic guesser."""

    def test_matches_programming_keywords(self) -> None:
        text = "python framework library code developer"
        topics = _guess_topics(text)
        assert "technology/programming" in topics

    def test_matches_ai_keywords(self) -> None:
        text = "machine learning deep learning neural llm transformer"
        topics = _guess_topics(text)
        assert "technology/ai-ml" in topics

    def test_returns_top_three(self) -> None:
        # Long text with keywords from many categories
        text = (
            "python code framework "
            "machine learning llm ai "
            "docker kubernetes linux server "
            "security vpn encryption "
            "react next.js web frontend "
        )
        topics = _guess_topics(text)
        assert len(topics) <= 3

    def test_no_match_returns_empty(self) -> None:
        text = "completely unrelated content about nothing specific"
        topics = _guess_topics(text)
        assert topics == []

    def test_sorted_by_score_descending(self) -> None:
        # AI keywords heavily weighted
        text = "machine learning deep learning neural llm transformer ai python code"
        topics = _guess_topics(text)
        assert topics[0] == "technology/ai-ml"

    def test_pkm_keywords(self) -> None:
        text = "knowledge graph obsidian zettelkasten pkm second brain"
        topics = _guess_topics(text)
        assert "meta/pkm" in topics


# ---------------------------------------------------------------------------
# _extract_capitalized_names
# ---------------------------------------------------------------------------


class TestExtractCapitalizedNames:
    """Tests for the regex-based name extractor."""

    def test_extracts_two_word_name(self) -> None:
        text = "The author Tim Berners invented something."
        # "Tim Berners" is two consecutive capitalized words
        names = _extract_capitalized_names(text)
        assert any("Tim Berners" in n for n in names)

    def test_extracts_multi_word_name(self) -> None:
        text = "John Stuart Mill wrote extensively."
        names = _extract_capitalized_names(text)
        assert "John Stuart Mill" in names

    def test_deduplicates_names(self) -> None:
        text = "Jane Doe said hello. Then Jane Doe said goodbye."
        names = _extract_capitalized_names(text)
        count = sum(1 for n in names if n == "Jane Doe")
        assert count == 1

    def test_skips_single_capitalized_words(self) -> None:
        text = "Python is great."
        names = _extract_capitalized_names(text)
        assert "Python" not in names

    def test_limits_to_20(self) -> None:
        text = " ".join(f"Name{i} Person{i}" for i in range(30))
        names = _extract_capitalized_names(text)
        assert len(names) <= 20

    def test_empty_text(self) -> None:
        assert _extract_capitalized_names("") == []


# ---------------------------------------------------------------------------
# _fallback_process
# ---------------------------------------------------------------------------


class TestFallbackProcess:
    """Tests for the rule-based fallback enrichment."""

    def test_adds_topics_from_keywords(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="ML Article",
            content="This is about machine learning and deep learning with neural networks.",
            metadata={},
        )
        enriched = _fallback_process(doc)
        assert "technology/ai-ml" in enriched.metadata.get("topics", [])

    def test_extracts_names_as_entities(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="People",
            content="I met John Smith and Jane Doe at the conference. They were great.",
            metadata={},
        )
        enriched = _fallback_process(doc)
        entities = enriched.metadata.get("entities", {})
        people = entities.get("people", [])
        assert any("John Smith" in p for p in people)

    def test_generates_summary_from_first_lines(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content=(
                "# Heading\n"
                "\n"
                "This is the first substantial paragraph of content"
                " that should be used as a summary.\n"
                "More content follows.\n"
            ),
            metadata={},
        )
        enriched = _fallback_process(doc)
        summary = enriched.metadata.get("summary", "")
        assert "first substantial paragraph" in summary

    def test_preserves_existing_topics(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="python code framework",
            metadata={"topics": ["culture/books"]},
        )
        enriched = _fallback_process(doc)
        # Should not overwrite existing topics
        assert enriched.metadata["topics"] == ["culture/books"]

    def test_preserves_existing_entities(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="John Smith was here.",
            metadata={"entities": {"people": ["Existing Person"]}},
        )
        enriched = _fallback_process(doc)
        assert enriched.metadata["entities"]["people"] == ["Existing Person"]

    def test_preserves_existing_summary(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="Some content here that is long enough to qualify as a summary line.",
            metadata={"summary": "Existing summary."},
        )
        enriched = _fallback_process(doc)
        assert enriched.metadata["summary"] == "Existing summary."


# ---------------------------------------------------------------------------
# process_document (public API)
# ---------------------------------------------------------------------------


class TestProcessDocument:
    """Tests for the public process_document function."""

    def test_fallback_mode_when_llm_disabled(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="AI Article",
            content="Discussion about machine learning and deep learning research.",
            metadata={},
        )
        enriched = process_document(doc, enable_llm=False)
        # Should still enrich via fallback
        assert enriched.metadata.get("topics") is not None

    def test_returns_parsed_document(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="Some long content body that has enough text for processing purposes.",
            metadata={},
        )
        enriched = process_document(doc, enable_llm=False)
        assert isinstance(enriched, ParsedDocument)
        assert enriched.path == "test.md"

    def test_falls_back_when_llm_fails(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="About machine learning and python code development.",
            metadata={},
        )
        with patch(
            "src.pipeline.processor.subprocess.run",
            side_effect=FileNotFoundError("claude not found"),
        ):
            enriched = process_document(doc, enable_llm=True)
        # Should still produce enriched output via fallback
        assert isinstance(enriched, ParsedDocument)

    def test_falls_back_on_timeout(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="About python programming and code libraries.",
            metadata={},
        )
        with patch(
            "src.pipeline.processor.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=60),
        ):
            enriched = process_document(doc, enable_llm=True)
        assert isinstance(enriched, ParsedDocument)

    def test_falls_back_on_bad_json(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="About python and machine learning topics.",
            metadata={},
        )
        mock_result = subprocess.CompletedProcess(
            args=["claude"],
            returncode=0,
            stdout="not valid json at all",
            stderr="",
        )
        with patch("src.pipeline.processor.subprocess.run", return_value=mock_result):
            enriched = process_document(doc, enable_llm=True)
        assert isinstance(enriched, ParsedDocument)

    def test_llm_success_uses_extracted_data(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="Some content.",
            metadata={},
        )
        llm_output = json.dumps(
            {
                "summary": "AI-generated summary.",
                "topics": ["technology/ai-ml"],
                "entities": {
                    "people": ["Ada Lovelace"],
                    "concepts": ["Neural Network"],
                    "organizations": ["OpenAI"],
                },
                "para_category": "resources",
            }
        )
        mock_result = subprocess.CompletedProcess(
            args=["claude"],
            returncode=0,
            stdout=llm_output,
            stderr="",
        )
        with patch("src.pipeline.processor.subprocess.run", return_value=mock_result):
            enriched = process_document(doc, enable_llm=True)
        assert enriched.metadata["summary"] == "AI-generated summary."
        assert enriched.metadata["topics"] == ["technology/ai-ml"]
        assert enriched.metadata["para_category"] == "resources"

    def test_llm_strips_markdown_fences(self) -> None:
        doc = ParsedDocument(
            path="test.md",
            title="Test",
            content="Content.",
            metadata={},
        )
        fenced = "```json\n" + json.dumps({"summary": "Fenced output."}) + "\n```"
        mock_result = subprocess.CompletedProcess(
            args=["claude"],
            returncode=0,
            stdout=fenced,
            stderr="",
        )
        with patch("src.pipeline.processor.subprocess.run", return_value=mock_result):
            enriched = process_document(doc, enable_llm=True)
        assert enriched.metadata["summary"] == "Fenced output."
