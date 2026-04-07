"""bg ingest — Thin CLI wrapper around the existing v1 pipeline."""

from __future__ import annotations

from pathlib import Path

from src.cli.commands import BaseCommand, Result
from src.config import load_settings


class IngestCommand(BaseCommand):
    """Ingest a URL or file through the existing processing pipeline."""

    agent_prompt = "Enhance document classification and entity extraction."

    def run_without_agent(self, **kwargs) -> Result:
        url_or_path: str = kwargs["url_or_path"]
        title: str | None = kwargs.get("title")

        settings = load_settings()
        vault = Path(settings.vault.path)
        inbox = vault / settings.vault.inbox_dir
        inbox.mkdir(parents=True, exist_ok=True)

        source_path = Path(url_or_path)

        if source_path.exists() and source_path.suffix == ".md":
            # Local markdown file — parse, process, ingest directly
            from src.pipeline.ingester import GraphIngester
            from src.pipeline.markdown_parser import parse_file
            from src.pipeline.processor import process_document

            try:
                doc = parse_file(source_path, vault_root=vault)
                doc = process_document(doc, enable_llm=settings.enable_llm_processing)
                ingester = GraphIngester(settings.falkordb)
                ingester.ingest_parsed_document(doc)
            except Exception as exc:
                return Result(
                    success=False,
                    output="",
                    error=f"Ingest failed: {exc}",
                )
            return Result(
                success=True,
                output=f"Ingested: {source_path}",
                data={"path": str(source_path), "title": doc.title},
            )

        if url_or_path.startswith(("http://", "https://")):
            # URL — create a stub note in inbox with the URL; the watcher handles the rest
            from datetime import UTC, datetime

            from src.pipeline.zettelkasten import generate_id, generate_slug

            uid = generate_id()
            now_iso = datetime.now(tz=UTC).strftime("%Y-%m-%d")
            doc_title = title or url_or_path

            content = f"""---
uid: "{uid}"
title: "{doc_title}"
type: article
tags: []
status: inbox
dates:
  created: {now_iso}
  captured: {now_iso}
  processed: null
  modified: {now_iso}
source:
  type: url
  url: "{url_or_path}"
content_stage: fleeting
version: 1
---

Source: {url_or_path}
"""

            slug = generate_slug(doc_title)
            filename = f"{slug}.md" if slug else f"{uid}.md"
            filepath = inbox / filename
            counter = 1
            while filepath.exists():
                filepath = inbox / f"{slug}-{counter}.md"
                counter += 1

            filepath.write_text(content, encoding="utf-8")
            return Result(
                success=True,
                output=f"Created inbox stub for URL: {filepath}",
                data={"path": str(filepath), "url": url_or_path, "uid": uid},
            )

        return Result(
            success=False,
            output="",
            error=f"Cannot ingest '{url_or_path}': not a .md file or URL.",
        )
