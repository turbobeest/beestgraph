"""System health checks for the beestgraph heartbeat monitor.

Each check function returns a structured ``CheckResult`` with status, message,
and optional numeric metrics.  All checks catch their own exceptions so one
failing check never takes down the rest.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

_SYSTEMD_SERVICES = [
    "beestgraph-watcher",
    "beestgraph-bot",
    "beestgraph-web",
    "beestgraph-heartbeat",
]


@dataclass
class CheckResult:
    """Structured result from a single health check.

    Attributes:
        name: Short identifier, e.g. ``"falkordb"``, ``"disk"``.
        status: One of ``"ok"``, ``"warning"``, ``"error"``.
        message: Human-readable detail string.
        metrics: Optional dict of numeric metrics for reporting.
        checked_at: UTC timestamp when the check ran.
    """

    name: str
    status: str
    message: str
    metrics: dict[str, object] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def _run_cmd(cmd: list[str], *, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with a timeout and return the result.

    Args:
        cmd: Command and arguments to execute.
        timeout: Maximum seconds to wait.

    Returns:
        Completed process result.
    """
    return subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def check_docker() -> CheckResult:
    """Check that beestgraph Docker containers are running and healthy.

    Returns:
        CheckResult with per-container status details.
    """
    try:
        result = _run_cmd(["docker", "ps", "--format", "{{json .}}", "--filter", "name=beestgraph"])
        if result.returncode != 0:
            return CheckResult(
                name="docker",
                status="error",
                message=f"docker ps failed: {result.stderr.strip()}",
            )

        containers: dict[str, str] = {}
        for line in result.stdout.strip().splitlines():
            info = json.loads(line)
            name = info.get("Names", "unknown")
            status = info.get("Status", "unknown")
            containers[name] = status

        if not containers:
            return CheckResult(
                name="docker",
                status="error",
                message="No beestgraph containers found",
            )

        unhealthy = [
            n for n, s in containers.items() if "unhealthy" in s.lower() or "exited" in s.lower()
        ]
        if unhealthy:
            return CheckResult(
                name="docker",
                status="warning",
                message=f"Unhealthy containers: {', '.join(unhealthy)}",
                metrics={"total": len(containers), "unhealthy": len(unhealthy)},
            )

        return CheckResult(
            name="docker",
            status="ok",
            message=f"{len(containers)} container(s) running",
            metrics={"total": len(containers)},
        )
    except Exception as exc:
        logger.error("check_docker_failed", error=str(exc))
        return CheckResult(name="docker", status="error", message=str(exc))


def check_systemd_services() -> CheckResult:
    """Check beestgraph systemd service units.

    Returns:
        CheckResult listing active vs inactive services.
    """
    try:
        active: list[str] = []
        inactive: list[str] = []

        for svc in _SYSTEMD_SERVICES:
            result = _run_cmd(["systemctl", "is-active", f"{svc}.service"])
            state = result.stdout.strip()
            if state == "active":
                active.append(svc)
            else:
                inactive.append(svc)

        if inactive:
            status = "warning" if active else "error"
            return CheckResult(
                name="systemd",
                status=status,
                message=f"Inactive: {', '.join(inactive)}",
                metrics={"active": len(active), "inactive": len(inactive)},
            )

        return CheckResult(
            name="systemd",
            status="ok",
            message=f"All {len(active)} services active",
            metrics={"active": len(active), "inactive": 0},
        )
    except Exception as exc:
        logger.error("check_systemd_failed", error=str(exc))
        return CheckResult(name="systemd", status="error", message=str(exc))


def check_falkordb(host: str = "localhost", port: int = 6379) -> CheckResult:
    """Ping FalkorDB and query node counts.

    Args:
        host: FalkorDB/Redis host.
        port: FalkorDB/Redis port.

    Returns:
        CheckResult with connectivity status and graph metrics.
    """
    try:
        ping = _run_cmd(["docker", "exec", "beestgraph-falkordb", "redis-cli", "PING"])
        if ping.stdout.strip() != "PONG":
            return CheckResult(
                name="falkordb",
                status="error",
                message=f"PING failed: {ping.stdout.strip() or ping.stderr.strip()}",
            )

        # Query document count.
        query = "MATCH (d:Document) RETURN count(d) AS cnt"
        graph_result = _run_cmd(
            [
                "docker",
                "exec",
                "beestgraph-falkordb",
                "redis-cli",
                "GRAPH.QUERY",
                "beestgraph",
                query,
            ]
        )
        doc_count = _parse_graph_count(graph_result.stdout)

        return CheckResult(
            name="falkordb",
            status="ok",
            message=f"Healthy, {doc_count} documents",
            metrics={"documents": doc_count},
        )
    except Exception as exc:
        logger.error("check_falkordb_failed", error=str(exc))
        return CheckResult(name="falkordb", status="error", message=str(exc))


def _parse_graph_count(output: str) -> int:
    """Extract an integer count from ``GRAPH.QUERY`` text output.

    Args:
        output: Raw redis-cli stdout from a count query.

    Returns:
        Parsed integer, or ``-1`` on failure.
    """
    for line in output.splitlines():
        line = line.strip()
        # redis-cli returns the count as a bare integer line.
        if line.isdigit():
            return int(line)
    return -1


def check_vault(vault_path: str | None = None) -> CheckResult:
    """Check the Obsidian vault for note counts and inbox status.

    Args:
        vault_path: Absolute path to the vault root.  Defaults to ``~/vault``.

    Returns:
        CheckResult with note and inbox metrics.
    """
    try:
        root = Path(vault_path) if vault_path else Path.home() / "vault"
        if not root.is_dir():
            return CheckResult(
                name="vault",
                status="error",
                message=f"Vault not found: {root}",
            )

        inbox = root / "inbox"
        inbox_count = len(list(inbox.glob("*.md"))) if inbox.is_dir() else 0
        total_notes = len(list(root.rglob("*.md")))

        status = "warning" if inbox_count > 50 else "ok"
        return CheckResult(
            name="vault",
            status=status,
            message=f"{total_notes} notes, {inbox_count} in inbox",
            metrics={"total_notes": total_notes, "inbox_count": inbox_count},
        )
    except Exception as exc:
        logger.error("check_vault_failed", error=str(exc))
        return CheckResult(name="vault", status="error", message=str(exc))


def check_disk(paths: list[str] | None = None) -> CheckResult:
    """Check disk usage on key mount points.

    Args:
        paths: Filesystem paths to check.  Defaults to ``["/"]``.

    Returns:
        CheckResult with usage percentages.
    """
    try:
        targets = paths or ["/"]
        metrics: dict[str, object] = {}
        worst_pct = 0.0

        for p in targets:
            usage = shutil.disk_usage(p)
            pct = (usage.used / usage.total) * 100
            total_gb = round(usage.total / (1024**3), 1)
            used_gb = round(usage.used / (1024**3), 1)
            metrics[p] = {"used_gb": used_gb, "total_gb": total_gb, "percent": round(pct, 1)}
            worst_pct = max(worst_pct, pct)

        if worst_pct > 90:
            status = "error"
        elif worst_pct > 80:
            status = "warning"
        else:
            status = "ok"

        detail = ", ".join(
            f"{p}: {m['used_gb']}GB/{m['total_gb']}GB ({m['percent']}%)"  # type: ignore[index]
            for p, m in metrics.items()
        )
        return CheckResult(name="disk", status=status, message=detail, metrics=metrics)
    except Exception as exc:
        logger.error("check_disk_failed", error=str(exc))
        return CheckResult(name="disk", status="error", message=str(exc))


def check_memory() -> CheckResult:
    """Check system memory usage via ``/proc/meminfo``.

    Returns:
        CheckResult with total, available, and used memory in GB.
    """
    try:
        meminfo: dict[str, int] = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    meminfo[key] = int(parts[1])  # kB

        total_kb = meminfo.get("MemTotal", 0)
        available_kb = meminfo.get("MemAvailable", 0)
        used_kb = total_kb - available_kb
        total_gb = round(total_kb / (1024**2), 1)
        used_gb = round(used_kb / (1024**2), 1)
        pct = round((used_kb / total_kb) * 100, 1) if total_kb else 0.0

        if pct > 90:
            status = "error"
        elif pct > 80:
            status = "warning"
        else:
            status = "ok"

        return CheckResult(
            name="memory",
            status=status,
            message=f"{used_gb}GB / {total_gb}GB ({pct}%)",
            metrics={"total_gb": total_gb, "used_gb": used_gb, "percent": pct},
        )
    except Exception as exc:
        logger.error("check_memory_failed", error=str(exc))
        return CheckResult(name="memory", status="error", message=str(exc))


def check_radicale(url: str = "http://localhost:5232") -> CheckResult:
    """Check that the Radicale CalDAV server is reachable.

    Args:
        url: Base URL of the Radicale instance.

    Returns:
        CheckResult with connectivity status.
    """
    try:
        import httpx

        resp = httpx.get(f"{url}/.web/", timeout=5)
        if resp.status_code < 400:
            return CheckResult(
                name="radicale",
                status="ok",
                message=f"Healthy, port {url.split(':')[-1]}",
            )
        return CheckResult(
            name="radicale",
            status="warning",
            message=f"HTTP {resp.status_code}",
        )
    except Exception as exc:
        logger.error("check_radicale_failed", error=str(exc))
        return CheckResult(name="radicale", status="error", message=str(exc))


def run_all_checks(
    vault_path: str | None = None,
    falkordb_host: str = "localhost",
    falkordb_port: int = 6379,
    radicale_url: str = "http://localhost:5232",
) -> list[CheckResult]:
    """Run every health check and return the collected results.

    Each check is run independently; a failure in one does not affect the others.

    Args:
        vault_path: Path to the Obsidian vault root.
        falkordb_host: FalkorDB/Redis host.
        falkordb_port: FalkorDB/Redis port.
        radicale_url: Base URL of the Radicale CalDAV server.

    Returns:
        List of ``CheckResult`` objects, one per check.
    """
    results: list[CheckResult] = []
    for check_fn in [
        lambda: check_docker(),
        lambda: check_systemd_services(),
        lambda: check_falkordb(falkordb_host, falkordb_port),
        lambda: check_vault(vault_path),
        lambda: check_disk(["/", vault_path] if vault_path else ["/"]),
        lambda: check_memory(),
        lambda: check_radicale(radicale_url),
    ]:
        try:
            results.append(check_fn())
        except Exception as exc:
            logger.error("check_unexpected_error", error=str(exc))
            results.append(CheckResult(name="unknown", status="error", message=str(exc)))
    return results
