"""bg save — Extract action items, decisions, and key facts from text."""

from __future__ import annotations

import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from src.cli.commands import BaseCommand, Result
from src.config import load_settings
from src.pipeline.zettelkasten import generate_id

_ACTION_RE = re.compile(r"^\s*[-*]\s+\[?\s?\]?\s*(.+)", re.MULTILINE)
_TODO_RE = re.compile(r"(?i)\bTODO\b[:\s]*(.+)")
_DECISION_RE = re.compile(
    r"(?i).*\b(decided|will use|won't|agreed|choosing|selected)\b.*", re.MULTILINE
)


class SaveCommand(BaseCommand):
    """Parse text for action items, decisions, and facts, then save to vault."""

    agent_prompt = "Categorize extracted items and suggest follow-up actions."

    def run_without_agent(self, **kwargs) -> Result:
        text: str | None = kwargs.get("text")
        from_stdin: bool = kwargs.get("from_stdin", False)

        if from_stdin:
            text = sys.stdin.read()
        if not text:
            return Result(success=False, output="", error="No text provided.")

        actions: list[str] = []
        decisions: list[str] = []
        facts: list[str] = []

        for match in _ACTION_RE.finditer(text):
            actions.append(match.group(1).strip())
        for match in _TODO_RE.finditer(text):
            item = match.group(1).strip()
            if item not in actions:
                actions.append(item)

        for match in _DECISION_RE.finditer(text):
            line = match.group(0).strip()
            if line not in decisions:
                decisions.append(line)

        # Key facts: lines that are statements (not bullets, not blank, not short)
        for line in text.splitlines():
            stripped = line.strip()
            if (
                stripped
                and not stripped.startswith(("-", "*", "#", ">"))
                and len(stripped) > 40
                and stripped not in decisions
            ):
                facts.append(stripped)

        settings = load_settings()
        vault = Path(settings.vault.path)
        fleeting_dir = vault / settings.vault.fleeting_dir
        fleeting_dir.mkdir(parents=True, exist_ok=True)

        uid = generate_id()
        now_iso = datetime.now(tz=UTC).strftime("%Y-%m-%d")

        sections: list[str] = []
        if actions:
            sections.append("## Action Items\n")
            for a in actions:
                sections.append(f"- [ ] {a}")
            sections.append("")
        if decisions:
            sections.append("## Decisions\n")
            for d in decisions:
                sections.append(f"- {d}")
            sections.append("")
        if facts:
            sections.append("## Key Facts\n")
            for f in facts[:10]:
                sections.append(f"- {f}")
            sections.append("")

        body = "\n".join(sections) if sections else "No structured items extracted.\n"

        content = f"""---
uid: "{uid}"
title: "Saved — {now_iso}"
type: note
tags: [saved-extract]
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

{body}
"""

        filepath = fleeting_dir / f"saved-{uid}.md"
        filepath.write_text(content, encoding="utf-8")

        summary = (
            f"Extracted {len(actions)} action(s), "
            f"{len(decisions)} decision(s), "
            f"{len(facts)} fact(s)"
        )
        return Result(
            success=True,
            output=f"{summary} → {filepath}",
            data={
                "path": str(filepath),
                "actions": actions,
                "decisions": decisions,
                "facts": facts,
            },
        )
