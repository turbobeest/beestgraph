"""beestgraph heartbeat — system health monitoring and CalDAV calendar integration.

Monitors Docker containers, systemd services, FalkorDB, vault, disk, and memory.
Publishes status to heartbeat.md and optionally to a Radicale CalDAV calendar.
"""

from __future__ import annotations

__all__ = [
    "BeestgraphCalendar",
    "CheckResult",
    "generate_heartbeat_md",
    "run_all_checks",
    "run_heartbeat",
]


def __getattr__(name: str) -> object:
    """Lazy-load public symbols to avoid circular import issues with ``__main__``."""
    if name in ("CheckResult", "run_all_checks"):
        from src.heartbeat.checks import CheckResult, run_all_checks

        return {"CheckResult": CheckResult, "run_all_checks": run_all_checks}[name]
    if name == "BeestgraphCalendar":
        from src.heartbeat.calendar import BeestgraphCalendar

        return BeestgraphCalendar
    if name in ("generate_heartbeat_md", "run_heartbeat"):
        from src.heartbeat.daemon import generate_heartbeat_md, run_heartbeat

        return {"generate_heartbeat_md": generate_heartbeat_md, "run_heartbeat": run_heartbeat}[
            name
        ]
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
