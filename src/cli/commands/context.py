"""bg context — Progressive context bundle for LLM sessions.

Assembles a structured markdown document from vault files and graph data
at four levels of detail. No LLM required — pure file-and-graph reading.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.cli.commands import BaseCommand, Result
from src.config import load_settings


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English text."""
    return len(text) // 4


def _read_if_exists(path: Path) -> str:
    """Read a file's content, returning empty string if missing."""
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ""


def _graph_stats(settings) -> str:
    """Query FalkorDB for node and edge counts by type."""
    try:
        from falkordb import FalkorDB

        db = FalkorDB(
            host=settings.falkordb.host,
            port=settings.falkordb.port,
            password=settings.falkordb.password or None,
        )
        graph = db.select_graph(settings.falkordb.graph_name)

        labels = [
            "Document", "Tag", "Topic", "Person", "Concept",
            "Organization", "Tool", "Place", "Source",
        ]
        lines = ["### Graph Stats\n"]
        for label in labels:
            try:
                r = graph.query(f"MATCH (n:{label}) RETURN count(n)")
                count = r.result_set[0][0] if r.result_set else 0
                lines.append(f"- {label}: {count}")
            except Exception:
                lines.append(f"- {label}: (query failed)")

        # Edge count
        try:
            r = graph.query("MATCH ()-[r]->() RETURN count(r)")
            edge_count = r.result_set[0][0] if r.result_set else 0
            lines.append(f"- Total relationships: {edge_count}")
        except Exception:  # noqa: S110
            pass

        return "\n".join(lines)
    except Exception as exc:
        return f"### Graph Stats\n\n(unavailable: {exc})\n"


def _active_projects(settings, full: bool = False) -> str:
    """List active projects from the vault."""
    vault = Path(settings.vault.path)
    projects_dir = vault / settings.vault.projects_dir
    if not projects_dir.is_dir():
        return ""

    lines = ["### Active Projects\n"]
    count = 0
    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir():
            continue
        readme = proj_dir / "README.md"
        if full and readme.exists():
            lines.append(f"#### {proj_dir.name}\n")
            lines.append(readme.read_text(encoding="utf-8"))
            lines.append("")
        else:
            status = ""
            if readme.exists():
                for line in readme.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith(("#", "---")):
                        status = stripped[:80]
                        break
            lines.append(f"- **{proj_dir.name}** — {status}")
        count += 1
        if not full and count >= 3:
            break

    return "\n".join(lines) if count > 0 else ""


def _daily_notes(settings, count: int = 1) -> str:
    """Read the most recent daily notes."""
    vault = Path(settings.vault.path)
    daily_dir = vault / settings.vault.daily_dir
    if not daily_dir.is_dir():
        return ""

    notes = sorted(daily_dir.glob("????-??-??.md"), reverse=True)[:count]
    if not notes:
        return ""

    lines = ["### Daily Notes\n"]
    for note in notes:
        content = note.read_text(encoding="utf-8")
        if count == 1:
            lines.append(f"#### {note.stem}\n")
            lines.append(content)
        else:
            # Summary only for multiple notes
            summary_lines = []
            in_fm = False
            for line in content.splitlines():
                if line.strip() == "---":
                    in_fm = not in_fm
                    continue
                if in_fm:
                    continue
                if line.strip() and not line.startswith("#") and len(summary_lines) < 2:
                    summary_lines.append(line.strip())
            summary = " ".join(summary_lines)[:120] if summary_lines else "(empty)"
            lines.append(f"- **{note.stem}**: {summary}")

    return "\n".join(lines)


def _task_board(settings) -> str:
    """Summarize tasks by project and priority."""
    vault = Path(settings.vault.path)
    task_files = list(vault.rglob("tasks.md"))
    if not task_files:
        return ""

    lines = ["### Task Board\n"]
    for tf in task_files:
        content = tf.read_text(encoding="utf-8")
        open_count = content.count("- [ ]")
        done_count = content.count("- [x]") + content.count("- [X]")
        parent = tf.parent.name
        lines.append(f"- **{parent}**: {open_count} open, {done_count} done")

    return "\n".join(lines)


def _recent_log(settings, entries: int = 20) -> str:
    """Read the last N entries from log.md."""
    vault = Path(settings.vault.path)
    log_path = vault / "log.md"
    if not log_path.is_file():
        return ""

    content = log_path.read_text(encoding="utf-8")
    # Find INGESTED lines
    log_lines = [
        line for line in content.splitlines()
        if line.strip().startswith("20") and "INGESTED" in line
    ]
    recent = log_lines[-entries:]
    if not recent:
        return ""

    lines = ["### Recent Activity\n"]
    lines.extend(f"- {entry}" for entry in recent)
    return "\n".join(lines)


def _full_graph_stats(settings) -> str:
    """Extended graph stats for level 3."""
    try:
        from falkordb import FalkorDB

        db = FalkorDB(
            host=settings.falkordb.host,
            port=settings.falkordb.port,
            password=settings.falkordb.password or None,
        )
        graph = db.select_graph(settings.falkordb.graph_name)

        lines = ["### Full Graph Stats\n"]

        # Node counts
        base = _graph_stats(settings)
        lines.append(base)

        # Edge type counts
        edge_types = [
            "TAGGED_WITH", "BELONGS_TO", "MENTIONS", "LINKS_TO",
            "DERIVED_FROM", "SUPPORTS", "CONTRADICTS", "EXTENDS",
            "SUPERSEDES", "RELATED_TO", "CHILD_OF",
        ]
        lines.append("\n### Edge Type Counts\n")
        for et in edge_types:
            try:
                r = graph.query(f"MATCH ()-[r:{et}]->() RETURN count(r)")
                count = r.result_set[0][0] if r.result_set else 0
                if count > 0:
                    lines.append(f"- {et}: {count}")
            except Exception:  # noqa: S110
                pass

        # Recent queue items
        try:
            r = graph.query(
                "MATCH (d:Document) WHERE d.status IN ['queue', 'inbox'] "
                "RETURN d.title, d.status ORDER BY d.created DESC LIMIT 30"
            )
            if r.result_set:
                lines.append("\n### Recent Queue Items\n")
                for row in r.result_set:
                    lines.append(f"- [{row[1]}] {row[0]}")
        except Exception:  # noqa: S110
            pass

        return "\n".join(lines)
    except Exception as exc:
        return f"### Full Graph Stats\n\n(unavailable: {exc})\n"


class ContextCommand(BaseCommand):
    """Assemble a context bundle for LLM sessions."""

    def run_without_agent(self, **kwargs) -> Result:
        level: int = kwargs.get("level", 1)
        to_clipboard: bool = kwargs.get("clipboard", False)
        to_file: str | None = kwargs.get("file")

        settings = load_settings()
        vault = Path(settings.vault.path)
        sections: list[str] = []

        # Level 0: identity only
        identity = _read_if_exists(vault / "identity.md")
        if identity:
            sections.append(identity)
        else:
            sections.append("(identity.md not found — run `bg init --identity`)\n")

        if level >= 1:
            # Daily note
            daily = _daily_notes(settings, count=1)
            if daily:
                sections.append(daily)

            # Top 3 projects
            projects = _active_projects(settings)
            if projects:
                sections.append(projects)

            # Graph stats summary
            stats = _graph_stats(settings)
            if stats:
                sections.append(stats)

        if level >= 2:
            # Last 7 daily notes (titles + summaries)
            weekly = _daily_notes(settings, count=7)
            if weekly:
                sections.append(weekly)

            # Task board
            board = _task_board(settings)
            if board:
                sections.append(board)

            # Recent log
            log = _recent_log(settings, entries=20)
            if log:
                sections.append(log)

        if level >= 3:
            # Full project READMEs
            full_projects = _active_projects(settings, full=True)
            if full_projects:
                sections.append(full_projects)

            # Full graph stats
            full_stats = _full_graph_stats(settings)
            if full_stats:
                sections.append(full_stats)

        output = "\n\n---\n\n".join(sections)
        tokens = _estimate_tokens(output)

        footer = f"\n\n---\nContext bundle assembled: Level {level} (~{tokens:,} tokens)\n"
        output += footer

        if to_clipboard:
            import contextlib

            try:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],  # noqa: S607
                    input=output.encode(),
                    check=True,
                )
            except (FileNotFoundError, subprocess.SubprocessError):
                with contextlib.suppress(FileNotFoundError, subprocess.SubprocessError):
                    subprocess.run(
                        ["pbcopy"],  # noqa: S607
                        input=output.encode(),
                        check=True,
                    )

        if to_file:
            Path(to_file).write_text(output, encoding="utf-8")
            return Result(
                success=True,
                output=f"Context written to {to_file} (~{tokens:,} tokens)",
                data={"level": level, "tokens": tokens, "file": to_file},
            )

        return Result(
            success=True,
            output=output,
            data={"level": level, "tokens": tokens},
        )
