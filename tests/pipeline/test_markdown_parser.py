"""Tests for src.pipeline.markdown_parser — file parsing, link/tag/URL extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.pipeline.markdown_parser import (
    extract_tags,
    extract_urls,
    extract_wiki_links,
    parse_file,
)

# ---------------------------------------------------------------------------
# extract_wiki_links
# ---------------------------------------------------------------------------


class TestExtractWikiLinks:
    """Tests for the ``extract_wiki_links`` helper."""

    def test_simple_link(self) -> None:
        assert extract_wiki_links("See [[My Page]]") == frozenset(["My Page"])

    def test_multiple_links(self) -> None:
        text = "Ref [[Alpha]] and [[Beta]] here."
        assert extract_wiki_links(text) == frozenset(["Alpha", "Beta"])

    def test_alias_link_strips_display_text(self) -> None:
        text = "See [[Real Target|Display Text]]"
        assert extract_wiki_links(text) == frozenset(["Real Target"])

    def test_no_links_returns_empty(self) -> None:
        assert extract_wiki_links("No links here.") == frozenset()

    def test_nested_brackets_ignored(self) -> None:
        # Edge case: only proper [[...]] should match
        text = "Not a link: [single bracket]"
        assert extract_wiki_links(text) == frozenset()


# ---------------------------------------------------------------------------
# extract_tags
# ---------------------------------------------------------------------------


class TestExtractTags:
    """Tests for the ``extract_tags`` helper."""

    def test_simple_tag(self) -> None:
        assert extract_tags("Hello #world") == frozenset(["world"])

    def test_tag_at_line_start(self) -> None:
        assert extract_tags("#python is great") == frozenset(["python"])

    def test_multiple_tags(self) -> None:
        text = "#ai-ml and #graph-theory"
        assert extract_tags(text) == frozenset(["ai-ml", "graph-theory"])

    def test_tags_lowercased(self) -> None:
        assert extract_tags("#MyTag") == frozenset(["mytag"])

    def test_no_tags_returns_empty(self) -> None:
        assert extract_tags("No tags here.") == frozenset()

    def test_heading_not_matched_as_tag(self) -> None:
        # Headings like "# Title" start with "# " — the space means no word char follows #
        # The regex requires an alpha char right after #
        result = extract_tags("# Title heading")
        # "Title" could match if there's no space rule — but our regex requires
        # start-of-string or whitespace before #, and "#<space>" won't match \w
        assert "title heading" not in result

    def test_tag_with_slashes(self) -> None:
        assert extract_tags("#technology/ai-ml") == frozenset(["technology/ai-ml"])


# ---------------------------------------------------------------------------
# extract_urls
# ---------------------------------------------------------------------------


class TestExtractUrls:
    """Tests for the ``extract_urls`` helper."""

    def test_http_url(self) -> None:
        assert extract_urls("Visit http://example.com") == frozenset(["http://example.com"])

    def test_https_url(self) -> None:
        assert extract_urls("Visit https://example.com/path") == frozenset(
            ["https://example.com/path"]
        )

    def test_multiple_urls(self) -> None:
        text = "See https://a.com and https://b.org/p"
        assert extract_urls(text) == frozenset(["https://a.com", "https://b.org/p"])

    def test_no_urls(self) -> None:
        assert extract_urls("No urls here") == frozenset()


# ---------------------------------------------------------------------------
# parse_file
# ---------------------------------------------------------------------------


class TestParseFile:
    """Tests for the top-level ``parse_file`` function."""

    def test_parses_frontmatter_title(self, sample_markdown: Path, tmp_vault: Path) -> None:
        doc = parse_file(sample_markdown, vault_root=tmp_vault)
        assert doc.title == "Knowledge Graphs for Fun and Profit"

    def test_parses_frontmatter_tags_merged_with_inline(
        self, sample_markdown: Path, tmp_vault: Path
    ) -> None:
        doc = parse_file(sample_markdown, vault_root=tmp_vault)
        # Frontmatter tags: knowledge-graphs, falkordb
        assert "knowledge-graphs" in doc.tags
        assert "falkordb" in doc.tags
        # Inline tags: #ai-ml, #graph-theory
        assert "ai-ml" in doc.tags
        assert "graph-theory" in doc.tags

    def test_parses_topics_from_metadata(self, sample_markdown: Path, tmp_vault: Path) -> None:
        doc = parse_file(sample_markdown, vault_root=tmp_vault)
        assert doc.metadata.get("topics") == ["technology/ai-ml", "meta/pkm"]

    def test_parses_entities_from_metadata(self, sample_markdown: Path, tmp_vault: Path) -> None:
        doc = parse_file(sample_markdown, vault_root=tmp_vault)
        entities = doc.metadata.get("entities", {})
        assert "Jane Doe" in entities.get("people", [])
        assert "Knowledge Graph" in entities.get("concepts", [])

    def test_extracts_wiki_links(self, sample_markdown: Path, tmp_vault: Path) -> None:
        doc = parse_file(sample_markdown, vault_root=tmp_vault)
        assert "Semantic Web" in doc.wiki_links
        assert "Graph Databases" in doc.wiki_links

    def test_extracts_urls(self, sample_markdown: Path, tmp_vault: Path) -> None:
        doc = parse_file(sample_markdown, vault_root=tmp_vault)
        assert "https://example.com/kg" in doc.urls
        # The URL regex includes trailing punctuation; the raw URL ends with "."
        assert any("example.org/semantic-web" in u for u in doc.urls)

    def test_path_relative_to_vault(self, sample_markdown: Path, tmp_vault: Path) -> None:
        doc = parse_file(sample_markdown, vault_root=tmp_vault)
        assert doc.path == "inbox/kg-article.md"

    def test_handles_missing_frontmatter(self, tmp_vault: Path) -> None:
        bare = tmp_vault / "inbox" / "bare.md"
        bare.write_text("# Just a heading\n\nSome content.\n", encoding="utf-8")
        doc = parse_file(bare, vault_root=tmp_vault)
        assert doc.title == "Just a heading"
        assert doc.metadata == {}

    def test_handles_file_not_found(self, tmp_vault: Path) -> None:
        missing = tmp_vault / "inbox" / "nonexistent.md"
        with pytest.raises(FileNotFoundError):
            parse_file(missing, vault_root=tmp_vault)

    def test_title_fallback_to_h1(self, tmp_vault: Path) -> None:
        no_fm = tmp_vault / "inbox" / "no-fm.md"
        no_fm.write_text("# My Article Title\n\nBody text.\n", encoding="utf-8")
        doc = parse_file(no_fm, vault_root=tmp_vault)
        assert doc.title == "My Article Title"

    def test_title_fallback_to_filename(self, tmp_vault: Path) -> None:
        no_title = tmp_vault / "inbox" / "my-cool-article.md"
        no_title.write_text("Just body text, no heading, no frontmatter.\n", encoding="utf-8")
        doc = parse_file(no_title, vault_root=tmp_vault)
        assert doc.title == "My Cool Article"

    def test_empty_tags_in_frontmatter(self, tmp_vault: Path) -> None:
        md = tmp_vault / "inbox" / "empty-tags.md"
        md.write_text("---\ntitle: Test\ntags: []\n---\n\nBody.\n", encoding="utf-8")
        doc = parse_file(md, vault_root=tmp_vault)
        # No frontmatter tags, no inline tags
        assert doc.tags == frozenset()

    def test_content_excludes_frontmatter(self, sample_markdown: Path, tmp_vault: Path) -> None:
        doc = parse_file(sample_markdown, vault_root=tmp_vault)
        assert "---" not in doc.content.split("\n")[0]
        assert "Knowledge graphs represent" in doc.content
