"""bg ingest — CLI wrapper around the ingest pipeline.

Without flags: Phase 1 only (existing behavior, safe).
With --active: Phases 1-3 (script-level, no LLM).
With --agent:  Phases 1-5 (full active ingest, requires LLM config).
"""

from __future__ import annotations

from pathlib import Path

from src.cli.commands import BaseCommand, Result
from src.config import load_settings


class IngestCommand(BaseCommand):
    """Ingest a URL or file through the processing pipeline."""

    agent_prompt = "Enhance document classification and entity extraction."

    def run_without_agent(self, **kwargs) -> Result:
        url_or_path: str = kwargs["url_or_path"]
        title: str | None = kwargs.get("title")
        active: bool = kwargs.get("active", False)
        use_agent: bool = kwargs.get("use_agent", False)

        settings = load_settings()
        vault = Path(settings.vault.path)
        inbox = vault / settings.vault.inbox_dir
        inbox.mkdir(parents=True, exist_ok=True)

        # Determine phases
        if use_agent:
            phases = [1, 2, 3, 4, 5]
        elif active:
            phases = [1, 2, 3, 5]
        else:
            phases = [1]

        # Load agent if needed
        agent = None
        if use_agent:
            try:
                from src.cli.agent import load_agent
                agent = load_agent()
            except Exception as exc:
                return Result(
                    success=False, output="",
                    error=f"Agent load failed: {exc}",
                )

        source_path = Path(url_or_path)

        if source_path.exists() and source_path.suffix == ".md":
            return self._ingest_file(source_path, vault, settings, phases, agent)

        if url_or_path.startswith(("http://", "https://")):
            return self._ingest_url(
                url_or_path, title, vault, inbox, settings, phases, agent,
            )

        return Result(
            success=False, output="",
            error=f"Cannot ingest '{url_or_path}': not a .md file or URL.",
        )

    def _ingest_file(
        self, source_path, vault, settings, phases, agent,
    ) -> Result:
        """Ingest a local markdown file."""
        from src.pipeline.ingester import GraphIngester
        from src.pipeline.markdown_parser import parse_file
        from src.pipeline.processor import process_document

        try:
            doc = parse_file(source_path, vault_root=vault)
            doc = process_document(doc, enable_llm=settings.enable_llm_processing)
            ingester = GraphIngester(settings.falkordb)

            if phases == [1]:
                ingester.ingest_parsed_document(doc)
            else:
                result = ingester.ingest(
                    doc, vault_path=vault, agent=agent, phases=phases,
                )
                lines = [f"Ingested: {source_path}"]
                if result.phase2 and result.phase2.items:
                    lines.append(f"  Entities updated: {len(result.phase2.items)}")
                if result.phase3 and result.phase3.items:
                    lines.append(f"  Contradictions flagged: {len(result.phase3.items)}")
                if result.phase4 and result.phase4.items:
                    lines.append(f"  Synthesis created: {len(result.phase4.items)}")
                if result.phase5 and result.phase5.items:
                    lines.append(f"  Navigation updated: {', '.join(result.phase5.items)}")
                return Result(
                    success=True,
                    output="\n".join(lines),
                    data={"path": str(source_path), "title": doc.title, "phases": phases},
                )
        except Exception as exc:
            return Result(success=False, output="", error=f"Ingest failed: {exc}")

        return Result(
            success=True,
            output=f"Ingested: {source_path}",
            data={"path": str(source_path), "title": doc.title},
        )

    def _ingest_url(
        self, url, title, vault, inbox, settings, phases, agent,
    ) -> Result:
        """Ingest a URL by creating an inbox stub, then optionally running phases."""
        from datetime import UTC, datetime

        from src.pipeline.zettelkasten import generate_id, generate_slug

        uid = generate_id()
        now_iso = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        doc_title = title or url

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
  url: "{url}"
content_stage: fleeting
version: 1
---

Source: {url}
"""

        slug = generate_slug(doc_title)
        filename = f"{slug}.md" if slug else f"{uid}.md"
        filepath = inbox / filename
        counter = 1
        while filepath.exists():
            filepath = inbox / f"{slug}-{counter}.md"
            counter += 1

        filepath.write_text(content, encoding="utf-8")

        # If active/agent phases requested, run them on the new file
        if phases != [1]:
            from src.pipeline.ingester import GraphIngester
            from src.pipeline.markdown_parser import parse_file
            from src.pipeline.processor import process_document

            try:
                doc = parse_file(filepath, vault_root=vault)
                doc = process_document(doc, enable_llm=settings.enable_llm_processing)
                ingester = GraphIngester(settings.falkordb)
                result = ingester.ingest(
                    doc, vault_path=vault, agent=agent, phases=phases,
                )
                lines = [f"Ingested URL: {filepath}"]
                if result.phase2 and result.phase2.items:
                    lines.append(f"  Entities updated: {len(result.phase2.items)}")
                if result.phase3 and result.phase3.items:
                    lines.append(f"  Contradictions flagged: {len(result.phase3.items)}")
                if result.phase5 and result.phase5.items:
                    lines.append(f"  Navigation updated: {', '.join(result.phase5.items)}")
                return Result(
                    success=True,
                    output="\n".join(lines),
                    data={"path": str(filepath), "url": url, "uid": uid, "phases": phases},
                )
            except Exception as exc:
                return Result(
                    success=True,
                    output=f"Created inbox stub (active ingest failed: {exc}): {filepath}",
                    data={"path": str(filepath), "url": url, "uid": uid},
                )

        return Result(
            success=True,
            output=f"Created inbox stub for URL: {filepath}",
            data={"path": str(filepath), "url": url, "uid": uid},
        )
