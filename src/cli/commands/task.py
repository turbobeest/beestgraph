"""bg task — Add a task entry to the vault."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from src.cli.commands import BaseCommand, Result
from src.config import load_settings


class TaskCommand(BaseCommand):
    """Write a task entry as a markdown checkbox in the vault."""

    agent_prompt = "Suggest task breakdown and dependencies."

    def run_without_agent(self, **kwargs) -> Result:
        title: str = kwargs["title"]
        project: str | None = kwargs.get("project")
        priority: str = kwargs.get("priority", "medium")
        due: str | None = kwargs.get("due")

        settings = load_settings()
        vault = Path(settings.vault.path)

        if project:
            task_file = vault / settings.vault.projects_dir / project / "tasks.md"
        else:
            task_file = vault / settings.vault.meta_dir / "tasks.md"

        task_file.parent.mkdir(parents=True, exist_ok=True)

        # Create the file with header if it doesn't exist
        if not task_file.exists():
            header = f"""---
title: "Tasks{f' — {project}' if project else ''}"
type: note
status: published
---

# Tasks{f" — {project}" if project else ""}

"""
            task_file.write_text(header, encoding="utf-8")

        # Build the task line
        now = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        meta_parts = [f"priority:{priority}", f"added:{now}"]
        if due:
            meta_parts.append(f"due:{due}")
        if project:
            meta_parts.append(f"project:{project}")
        meta = " ".join(f"[{p}]" for p in meta_parts)

        task_line = f"- [ ] {title} {meta}\n"

        with task_file.open("a", encoding="utf-8") as f:
            f.write(task_line)

        return Result(
            success=True,
            output=f"Task added: {title} → {task_file}",
            data={"path": str(task_file), "title": title, "priority": priority},
        )
