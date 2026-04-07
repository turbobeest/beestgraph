"""Tests for bg migrate command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.cli.commands.migrate import MigrateCommand, _migrate_one


@pytest.fixture
def mock_settings(tmp_path: Path):
    from src.config import BeestgraphSettings, FalkorDBSettings, VaultSettings

    return BeestgraphSettings(
        log_level="DEBUG",
        enable_llm_processing=False,
        falkordb=FalkorDBSettings(host="localhost", port=9999, graph_name="test"),
        vault=VaultSettings(path=str(tmp_path)),
    )


@pytest.fixture(autouse=True)
def _patch_settings(mock_settings):
    with patch("src.cli.commands.migrate.load_settings", return_value=mock_settings):
        yield


def _write_doc(path: Path, frontmatter: str, body: str = "Content.") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n\n{body}\n", encoding="utf-8")
    return path


class TestDryRun:
    def test_produces_no_changes(self, tmp_path: Path) -> None:
        _write_doc(tmp_path / "test.md", 'title: "Test"\nstatus: published\n')
        result = MigrateCommand().run_without_agent(uid_only=True)
        assert result.success
        assert "DRY RUN" in result.output
        # File should be unchanged
        content = (tmp_path / "test.md").read_text(encoding="utf-8")
        assert "uid:" not in content  # Not written in dry run


class TestUidBackfill:
    def test_generates_uid(self, tmp_path: Path) -> None:
        doc = _write_doc(tmp_path / "test.md", 'title: "Test"\n')
        result = _migrate_one(doc, uid_only=True)
        assert any("uid:" in c for c in result["changes"])
        assert result["meta"]["uid"]

    def test_preserves_existing_uid(self, tmp_path: Path) -> None:
        doc = _write_doc(tmp_path / "test.md", 'title: "Test"\nuid: "20260101120000"\n')
        result = _migrate_one(doc, uid_only=True)
        assert len(result["changes"]) == 0
        assert result["meta"]["uid"] == "20260101120000"


class TestQualityToConfidence:
    @pytest.mark.parametrize("quality,expected", [
        ("low", 0.3), ("medium", 0.6), ("high", 0.9),
    ])
    def test_conversion(self, tmp_path: Path, quality: str, expected: float) -> None:
        doc = _write_doc(tmp_path / "test.md", f'title: "Test"\nquality: {quality}\n')
        result = _migrate_one(doc, do_frontmatter=True)
        assert result["meta"]["confidence"] == expected
        assert "quality" not in result["meta"]

    def test_does_not_overwrite_existing_confidence(self, tmp_path: Path) -> None:
        doc = _write_doc(
            tmp_path / "test.md",
            'title: "Test"\nquality: high\nconfidence: 0.5\n',
        )
        result = _migrate_one(doc, do_frontmatter=True)
        assert result["meta"]["confidence"] == 0.5


class TestFlatToNested:
    def test_source_url_nests(self, tmp_path: Path) -> None:
        doc = _write_doc(tmp_path / "test.md", 'title: "Test"\nsource_url: "https://example.com"\n')
        result = _migrate_one(doc, do_frontmatter=True)
        assert result["meta"]["source"]["url"] == "https://example.com"
        assert "source_url" not in result["meta"]

    def test_date_captured_nests(self, tmp_path: Path) -> None:
        doc = _write_doc(tmp_path / "test.md", 'title: "Test"\ndate_captured: "2026-01-01"\n')
        result = _migrate_one(doc, do_frontmatter=True)
        assert result["meta"]["dates"]["captured"] == "2026-01-01"


class TestIdempotent:
    def test_double_run(self, tmp_path: Path) -> None:
        doc = _write_doc(
            tmp_path / "test.md",
            'title: "Test"\nquality: high\nsource_url: "https://example.com"\n',
        )
        r1 = _migrate_one(doc, uid_only=True, do_frontmatter=True)
        assert len(r1["changes"]) > 0

        # Write the migrated version
        import frontmatter as fm
        post = r1["post"]
        post.metadata = r1["meta"]
        doc.write_text(fm.dumps(post), encoding="utf-8")

        # Run again
        r2 = _migrate_one(doc, uid_only=True, do_frontmatter=True)
        assert len(r2["changes"]) == 0


class TestSingleFile:
    def test_single_file_migration(self, tmp_path: Path) -> None:
        target = _write_doc(tmp_path / "target.md", 'title: "Target"\n')
        _write_doc(tmp_path / "other.md", 'title: "Other"\n')

        result = MigrateCommand().run_without_agent(
            uid_only=True, write=True, path=str(target),
        )
        assert result.success
        assert result.data["total"] == 1

        # target should have uid
        content = target.read_text(encoding="utf-8")
        assert "uid:" in content

        # other should be untouched
        other_content = (tmp_path / "other.md").read_text(encoding="utf-8")
        assert "uid:" not in other_content


class TestWriteFlag:
    def test_write_applies_changes(self, tmp_path: Path) -> None:
        doc = _write_doc(tmp_path / "test.md", 'title: "Test"\n')
        result = MigrateCommand().run_without_agent(uid_only=True, write=True)
        assert result.success
        assert "APPLIED" in result.output
        content = doc.read_text(encoding="utf-8")
        assert "uid:" in content
