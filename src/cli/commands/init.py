"""bg init — Bootstrap new vault directories."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from src.cli.commands import BaseCommand, Result
from src.config import load_settings
from src.pipeline.zettelkasten import generate_id

_NEW_DIRS = [
    "entities/people",
    "entities/organizations",
    "entities/tools",
    "entities/concepts",
    "entities/places",
    "raw/articles",
    "raw/transcripts",
    "raw/pdfs",
]

_INDEX_FRONTMATTER = """---
uid: "{uid}"
title: "Index"
type: moc
tags: [meta-index]
status: published
dates:
  created: {date}
  captured: {date}
  processed: null
  modified: {date}
source:
  type: manual
para: resources
version: 1
---

"""

_LOG_FRONTMATTER = """---
uid: "{uid}"
title: "Log"
type: note
tags: [meta-log]
status: published
dates:
  created: {date}
  captured: {date}
  processed: null
  modified: {date}
source:
  type: manual
para: resources
version: 1
---

"""


class InitCommand(BaseCommand):
    """Create new vault directories and root files."""

    def run_without_agent(self, **kwargs) -> Result:
        settings = load_settings()
        vault = Path(settings.vault.path)

        created: list[str] = []
        existed: list[str] = []

        for d in _NEW_DIRS:
            target = vault / d
            if target.exists():
                existed.append(d)
            else:
                target.mkdir(parents=True, exist_ok=True)
                created.append(d)

        now = datetime.now(tz=UTC).strftime("%Y-%m-%d")

        # index.md
        index_path = vault / "index.md"
        if index_path.exists():
            existed.append("index.md")
        else:
            index_path.write_text(
                _INDEX_FRONTMATTER.format(uid=generate_id(), date=now),
                encoding="utf-8",
            )
            created.append("index.md")

        # log.md
        log_path = vault / "log.md"
        if log_path.exists():
            existed.append("log.md")
        else:
            log_path.write_text(
                _LOG_FRONTMATTER.format(uid=generate_id(), date=now),
                encoding="utf-8",
            )
            created.append("log.md")

        lines: list[str] = []
        if created:
            lines.append(f"Created ({len(created)}):")
            for c in created:
                lines.append(f"  + {c}")
        if existed:
            lines.append(f"Already existed ({len(existed)}):")
            for e in existed:
                lines.append(f"  = {e}")
        if not created:
            lines.append("Nothing new to create — vault is already initialized.")

        return Result(
            success=True,
            output="\n".join(lines),
            data={"created": created, "existed": existed},
        )
