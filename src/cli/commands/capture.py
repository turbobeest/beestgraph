"""bg capture — Quick idea capture to inbox."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from src.cli.commands import BaseCommand, Result
from src.config import load_settings
from src.pipeline.zettelkasten import generate_id, generate_slug


class CaptureCommand(BaseCommand):
    """Create a new note in the vault inbox with a generated uid."""

    agent_prompt = "Classify and suggest tags for this captured note."

    def run_without_agent(self, **kwargs) -> Result:
        text: str = kwargs["text"]
        title: str | None = kwargs.get("title")
        tags: list[str] = kwargs.get("tags") or []

        settings = load_settings()
        vault = Path(settings.vault.path)
        inbox = vault / settings.vault.inbox_dir
        inbox.mkdir(parents=True, exist_ok=True)

        uid = generate_id()
        now_iso = datetime.now(tz=UTC).strftime("%Y-%m-%d")

        if not title:
            # Use first line of text, truncated
            first_line = text.split("\n", 1)[0].strip()
            title = first_line[:80] if first_line else "Untitled capture"

        tags_yaml = ", ".join(tags) if tags else ""

        content = f"""---
uid: "{uid}"
title: "{title}"
type: note
tags: [{tags_yaml}]
status: inbox
dates:
  created: {now_iso}
  captured: {now_iso}
  processed: null
  modified: {now_iso}
source:
  type: manual
content_stage: fleeting
version: 1
---

{text}
"""

        slug = generate_slug(title)
        filename = f"{slug}.md" if slug else f"{uid}.md"
        filepath = inbox / filename

        # Avoid overwriting
        counter = 1
        while filepath.exists():
            filepath = inbox / f"{slug}-{counter}.md"
            counter += 1

        filepath.write_text(content, encoding="utf-8")

        return Result(
            success=True,
            output=f"Captured: {filepath}",
            data={"path": str(filepath), "uid": uid, "title": title},
        )
