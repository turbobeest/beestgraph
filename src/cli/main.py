"""``bg`` CLI entry point — Typer application with all Phase 1 commands."""

from __future__ import annotations

from typing import Annotated

import typer

from src.cli.commands import Result

app = typer.Typer(
    name="bg",
    help="beestgraph — AI-augmented personal knowledge graph CLI.",
    no_args_is_help=True,
)

# Global state for --agent flag (no-op in Phase 1)
_agent_enabled = False


def _version_callback(value: bool) -> None:
    if value:
        typer.echo("bg 0.1.0 (beestgraph)")
        raise typer.Exit()


def _print_result(result: Result) -> None:
    """Print a command result and exit with appropriate code."""
    if result.success:
        if result.output:
            typer.echo(result.output)
    else:
        typer.echo(f"Error: {result.error}", err=True)
        raise typer.Exit(1)


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = None,
    agent: Annotated[
        bool,
        typer.Option("--agent", help="Enable LLM agent enhancement (Phase 2+, no-op for now)."),
    ] = False,
) -> None:
    """beestgraph knowledge graph CLI."""
    global _agent_enabled
    _agent_enabled = agent


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def daily() -> None:
    """Create or open today's daily note."""
    from src.cli.commands.daily import DailyCommand

    _print_result(DailyCommand().run_without_agent())


@app.command()
def task(
    title: Annotated[str, typer.Argument(help="Task title.")],
    project: Annotated[str | None, typer.Option(help="Project name.")] = None,
    priority: Annotated[str, typer.Option(help="Priority: high/medium/low.")] = "medium",
    due: Annotated[str | None, typer.Option(help="Due date (YYYY-MM-DD).")] = None,
) -> None:
    """Add a task to the vault."""
    from src.cli.commands.task import TaskCommand

    _print_result(TaskCommand().run_without_agent(
        title=title, project=project, priority=priority, due=due,
    ))


@app.command()
def find(
    query: Annotated[str, typer.Argument(help="Search query.")],
    type: Annotated[str | None, typer.Option("--type", help="Filter by document type.")] = None,
    limit: Annotated[int, typer.Option(help="Max results.")] = 10,
    json: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """Search the knowledge graph."""
    from src.cli.commands.find import FindCommand

    _print_result(FindCommand().run_without_agent(
        query=query, type=type, limit=limit, json=json,
    ))


@app.command()
def project(
    project_name: Annotated[str, typer.Argument(help="Project name.")],
    status: Annotated[
        str | None, typer.Option(help="Filter documents by status.")
    ] = None,
) -> None:
    """Show project status from vault and graph."""
    from src.cli.commands.project import ProjectCommand

    _print_result(ProjectCommand().run_without_agent(
        project_name=project_name, status=status,
    ))


@app.command()
def health() -> None:
    """Run system health checks."""
    from src.cli.commands.health import HealthCommand

    _print_result(HealthCommand().run_without_agent())


@app.command(name="init")
def init_cmd() -> None:
    """Bootstrap new vault directories (entities/, raw/)."""
    from src.cli.commands.init import InitCommand

    _print_result(InitCommand().run_without_agent())


@app.command()
def capture(
    text: Annotated[str, typer.Argument(help="Text to capture.")],
    title: Annotated[str | None, typer.Option(help="Note title.")] = None,
    tags: Annotated[str | None, typer.Option(help="Comma-separated tags.")] = None,
) -> None:
    """Quick-capture a note to the inbox."""
    from src.cli.commands.capture import CaptureCommand

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    _print_result(CaptureCommand().run_without_agent(
        text=text, title=title, tags=tag_list,
    ))


@app.command()
def save(
    text: Annotated[str | None, typer.Argument(help="Text to parse.")] = None,
    from_stdin: Annotated[
        bool, typer.Option("--from-stdin", help="Read from stdin.")
    ] = False,
) -> None:
    """Extract action items, decisions, and key facts from text."""
    from src.cli.commands.save import SaveCommand

    _print_result(SaveCommand().run_without_agent(text=text, from_stdin=from_stdin))


@app.command()
def export(
    flat: Annotated[bool, typer.Option("--flat", help="Flatten nested frontmatter.")] = False,
    output: Annotated[
        str | None, typer.Option("--output", help="Output file path.")
    ] = None,
) -> None:
    """Export vault documents as JSON."""
    from src.cli.commands.export import ExportCommand

    _print_result(ExportCommand().run_without_agent(flat=flat, output=output))


@app.command()
def archive(
    slug_or_path: Annotated[str, typer.Argument(help="Document slug or path.")],
    reason: Annotated[str | None, typer.Option(help="Archival reason.")] = None,
) -> None:
    """Archive a document."""
    from src.cli.commands.archive import ArchiveCommand

    _print_result(ArchiveCommand().run_without_agent(
        slug_or_path=slug_or_path, reason=reason,
    ))


@app.command()
def ingest(
    url_or_path: Annotated[str, typer.Argument(help="URL or file path to ingest.")],
    title: Annotated[str | None, typer.Option(help="Override title.")] = None,
) -> None:
    """Ingest a URL or file through the pipeline."""
    from src.cli.commands.ingest import IngestCommand

    _print_result(IngestCommand().run_without_agent(
        url_or_path=url_or_path, title=title,
    ))


if __name__ == "__main__":
    app()
