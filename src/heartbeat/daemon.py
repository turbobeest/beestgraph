"""Heartbeat daemon — runs health checks on a schedule and publishes results.

Can be invoked as ``python -m src.heartbeat.daemon`` for systemd or cron, or
imported and called directly from other modules.
"""

from __future__ import annotations

import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import click
import structlog

from src.config import BeestgraphSettings, load_settings
from src.heartbeat.calendar import BeestgraphCalendar
from src.heartbeat.checks import CheckResult, run_all_checks

logger = structlog.get_logger(__name__)


def generate_heartbeat_md(checks: list[CheckResult]) -> str:
    """Generate the ``heartbeat.md`` content from check results.

    Produces a Markdown document with YAML frontmatter suitable for both
    human reading and machine parsing by Claude Code.

    Args:
        checks: Completed health-check results.

    Returns:
        Full Markdown string including frontmatter.
    """
    now = datetime.now(UTC)
    ok_count = sum(1 for c in checks if c.status == "ok")
    total = len(checks)
    worst = "ok"
    if any(c.status == "error" for c in checks):
        worst = "error"
    elif any(c.status == "warning" for c in checks):
        worst = "warning"

    lines: list[str] = []

    # Frontmatter
    lines.append("---")
    lines.append("title: beestgraph heartbeat")
    lines.append(f"updated: {now.isoformat()}")
    lines.append(f"status: {worst}")
    lines.append("---")
    lines.append("")
    lines.append("# System Heartbeat")
    lines.append("")
    lines.append(f"**Last check:** {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append(f"**Overall status:** {worst.upper()} ({ok_count}/{total} checks passing)")
    lines.append("")

    # Services table
    service_checks = [c for c in checks if c.name in ("docker", "systemd", "falkordb", "radicale")]
    if service_checks:
        lines.append("## Services")
        lines.append("")
        lines.append("| Service | Status | Detail |")
        lines.append("|---------|--------|--------|")
        for c in service_checks:
            lines.append(f"| {c.name.title()} | {c.status.upper()} | {c.message} |")
        lines.append("")

    # Resources table
    resource_checks = [c for c in checks if c.name in ("disk", "memory", "vault")]
    if resource_checks:
        lines.append("## Resources")
        lines.append("")
        lines.append("| Resource | Value | Status |")
        lines.append("|----------|-------|--------|")
        for c in resource_checks:
            lines.append(f"| {c.name.title()} | {c.message} | {c.status.upper()} |")
        lines.append("")

    # Graph metrics (from falkordb check)
    falkordb_check = next((c for c in checks if c.name == "falkordb"), None)
    if falkordb_check and falkordb_check.metrics:
        lines.append("## Graph")
        lines.append("")
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        for key, val in falkordb_check.metrics.items():
            lines.append(f"| {key.title()} | {val} |")
        lines.append("")

    return "\n".join(lines)


def run_heartbeat(
    settings: BeestgraphSettings,
    calendar: BeestgraphCalendar | None = None,
) -> list[CheckResult]:
    """Run one heartbeat cycle: checks, write heartbeat.md, publish to calendar.

    Args:
        settings: Application settings.
        calendar: Optional CalDAV client.  If ``None``, calendar publishing
            is skipped.

    Returns:
        The list of check results.
    """
    logger.info("heartbeat_running")

    checks = run_all_checks(
        vault_path=settings.vault.path,
        falkordb_host=settings.falkordb.host,
        falkordb_port=settings.falkordb.port,
    )

    md_content = generate_heartbeat_md(checks)

    # Write to vault.
    vault_heartbeat = Path(settings.vault.path) / "heartbeat.md"
    try:
        vault_heartbeat.write_text(md_content, encoding="utf-8")
        logger.info("heartbeat_md_written", path=str(vault_heartbeat))
    except OSError as exc:
        logger.error("heartbeat_md_write_failed", path=str(vault_heartbeat), error=str(exc))

    # Write to .claude/ for Claude Code.
    claude_heartbeat = Path.home() / ".claude" / "heartbeat.md"
    try:
        claude_heartbeat.parent.mkdir(parents=True, exist_ok=True)
        claude_heartbeat.write_text(md_content, encoding="utf-8")
        logger.info("heartbeat_md_written", path=str(claude_heartbeat))
    except OSError as exc:
        logger.error("heartbeat_md_write_failed", path=str(claude_heartbeat), error=str(exc))

    # Publish to calendar.
    if calendar:
        try:
            calendar.add_heartbeat_event(checks)
        except Exception as exc:
            logger.error("heartbeat_calendar_failed", error=str(exc))

    ok_count = sum(1 for c in checks if c.status == "ok")
    logger.info(
        "heartbeat_complete",
        ok=ok_count,
        total=len(checks),
        worst=max((c.status for c in checks), key=lambda s: ["ok", "warning", "error"].index(s)),
    )
    return checks


def _build_calendar(settings: BeestgraphSettings) -> BeestgraphCalendar | None:
    """Create and initialise a CalDAV calendar client from settings.

    Args:
        settings: Application settings containing calendar configuration.

    Returns:
        A connected ``BeestgraphCalendar``, or ``None`` if connection fails.
    """
    try:
        cal = BeestgraphCalendar(
            url=settings.calendar.url,
            username=settings.calendar.username,
            password=settings.calendar.password,
            calendar_name=settings.calendar.calendar_name,
        )
        cal.ensure_calendar()
        return cal
    except Exception as exc:
        logger.warning("calendar_unavailable", error=str(exc))
        return None


@click.command("heartbeat")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True),
    default=None,
    help="Path to beestgraph.yml config file.",
)
@click.option("--once", is_flag=True, help="Run once and exit (for cron).")
@click.option(
    "--interval",
    default=300,
    type=int,
    show_default=True,
    help="Seconds between heartbeats.",
)
@click.option("--no-calendar", is_flag=True, help="Skip CalDAV publishing.")
def main(
    config_path: str | None,
    once: bool,
    interval: int,
    no_calendar: bool,
) -> None:
    """Run the beestgraph heartbeat monitor."""
    settings = load_settings(Path(config_path) if config_path else None)

    calendar: BeestgraphCalendar | None = None
    if not no_calendar and settings.heartbeat.enabled:
        calendar = _build_calendar(settings)

    if once:
        run_heartbeat(settings, calendar)
        return

    logger.info("heartbeat_daemon_starting", interval=interval)
    try:
        while True:
            run_heartbeat(settings, calendar)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("heartbeat_daemon_stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
