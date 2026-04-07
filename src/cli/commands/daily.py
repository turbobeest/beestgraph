"""bg daily — Create or open today's daily note."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from src.cli.commands import BaseCommand, Result
from src.config import load_settings
from src.pipeline.zettelkasten import generate_id


class DailyCommand(BaseCommand):
    """Create or open today's daily note in the vault."""

    agent_prompt = "Summarize today's agenda and suggest focus areas."

    def run_without_agent(self, **kwargs) -> Result:
        settings = load_settings()
        vault = Path(settings.vault.path)
        daily_dir = vault / settings.vault.daily_dir

        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        filepath = daily_dir / f"{today}.md"

        if filepath.exists():
            return Result(
                success=True,
                output=f"Daily note exists: {filepath}",
                data={"path": str(filepath), "created": False},
            )

        daily_dir.mkdir(parents=True, exist_ok=True)

        # Try to load the note template
        template_path = vault / settings.vault.templates_dir / "note.md"
        template = template_path.read_text(encoding="utf-8") if template_path.exists() else None

        uid = generate_id()
        now_iso = datetime.now(tz=UTC).strftime("%Y-%m-%d")

        if template:
            content = template.replace("{{ title }}", f"Daily — {today}")
            content = content.replace("{{ created }}", now_iso)
            content = content.replace("{{ captured }}", now_iso)
            content = content.replace("{{ content }}", "")
            # Fill in the uid
            content = content.replace('uid: ""', f'uid: "{uid}"')
        else:
            content = f"""---
uid: "{uid}"
title: "Daily — {today}"
type: note
tags: [daily]
status: inbox
dates:
  created: {now_iso}
  captured: {now_iso}
  processed: null
  modified: {now_iso}
source:
  type: manual
para: areas
content_stage: fleeting
version: 1
---

"""

        filepath.write_text(content, encoding="utf-8")
        return Result(
            success=True,
            output=f"Created daily note: {filepath}",
            data={"path": str(filepath), "created": True},
        )
