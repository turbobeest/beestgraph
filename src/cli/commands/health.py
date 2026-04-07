"""bg health — System health report with multiple modes."""

from __future__ import annotations

from pathlib import Path

from src.cli.commands import BaseCommand, Result
from src.config import load_settings

_STATUS_ICONS = {"ok": "+", "warning": "!", "error": "X"}


class HealthCommand(BaseCommand):
    """Run health checks in various modes."""

    agent_prompt = "Diagnose any failing checks and suggest fixes."

    def run_without_agent(self, **kwargs) -> Result:
        quick: bool = kwargs.get("quick", False)
        sources: bool = kwargs.get("sources", False)
        inbox: bool = kwargs.get("inbox", False)

        settings = load_settings()

        if quick:
            return self._quick_check(settings)
        if sources:
            return self._source_check(settings)
        if inbox:
            return self._inbox_check(settings)
        # Default and --full: same full report
        return self._full_check(settings)

    def _quick_check(self, settings) -> Result:
        """Quick mode: just check services are up."""
        from src.heartbeat.checks import check_docker, check_systemd_services

        checks = [check_docker(), check_systemd_services()]
        lines = ["Quick Health Check"]
        has_error = False
        for c in checks:
            icon = _STATUS_ICONS.get(c.status, "?")
            lines.append(f"  [{icon}] {c.name}: {c.message}")
            if c.status == "error":
                has_error = True

        return Result(
            success=True, output="\n".join(lines),
            data={"checks": [c.__dict__ for c in checks], "has_errors": has_error},
        )

    def _full_check(self, settings) -> Result:
        """Full mode: all checks + graph metrics."""
        from src.heartbeat.checks import run_all_checks

        checks = run_all_checks(
            vault_path=settings.vault.path,
            falkordb_host=settings.falkordb.host,
            falkordb_port=settings.falkordb.port,
        )

        extra_lines: list[str] = []
        try:
            from falkordb import FalkorDB

            db = FalkorDB(
                host=settings.falkordb.host,
                port=settings.falkordb.port,
                password=settings.falkordb.password or None,
            )
            graph = db.select_graph(settings.falkordb.graph_name)

            orphan_result = graph.query(
                "MATCH (d:Document) "
                "WHERE NOT (d)-[:TAGGED_WITH]->() AND NOT (d)-[:BELONGS_TO]->() "
                "RETURN count(d) AS cnt"
            )
            orphan_count = (
                orphan_result.result_set[0][0] if orphan_result.result_set else 0
            )
            extra_lines.append(f"  Orphan documents (no tags/topics): {orphan_count}")

            queue_result = graph.query(
                "MATCH (d:Document {status: 'queue'}) RETURN count(d) AS cnt"
            )
            queue_count = (
                queue_result.result_set[0][0] if queue_result.result_set else 0
            )
            extra_lines.append(f"  Queue backlog: {queue_count}")
        except Exception as exc:
            extra_lines.append(f"  Graph metrics unavailable: {exc}")

        lines: list[str] = ["Health Report", "=" * 40]
        has_error = False
        for check in checks:
            icon = _STATUS_ICONS.get(check.status, "?")
            lines.append(f"  [{icon}] {check.name}: {check.message}")
            if check.status == "error":
                has_error = True

        if extra_lines:
            lines.append("")
            lines.append("Graph Metrics")
            lines.append("-" * 40)
            lines.extend(extra_lines)

        return Result(
            success=True, output="\n".join(lines),
            data={"checks": [c.__dict__ for c in checks], "has_errors": has_error},
        )

    def _source_check(self, settings) -> Result:
        """Source health: verify source URLs resolve."""
        try:
            from falkordb import FalkorDB

            db = FalkorDB(
                host=settings.falkordb.host,
                port=settings.falkordb.port,
                password=settings.falkordb.password or None,
            )
            graph = db.select_graph(settings.falkordb.graph_name)
            result = graph.query(
                "MATCH (s:Source) RETURN s.url LIMIT 50"
            )
            urls = [row[0] for row in (result.result_set or []) if row[0]]
        except Exception as exc:
            return Result(success=False, output="", error=f"Graph query failed: {exc}")

        import httpx

        lines = [f"Source Health Check ({len(urls)} URLs)"]
        ok_count = 0
        fail_count = 0
        for url in urls:
            try:
                resp = httpx.head(url, timeout=10, follow_redirects=True)
                if resp.status_code < 400:
                    ok_count += 1
                else:
                    lines.append(f"  [!] {resp.status_code} {url}")
                    fail_count += 1
            except Exception:
                lines.append(f"  [X] UNREACHABLE {url}")
                fail_count += 1

        lines.insert(1, f"  OK: {ok_count}, Failed: {fail_count}")
        return Result(
            success=True, output="\n".join(lines),
            data={"ok": ok_count, "failed": fail_count},
        )

    def _inbox_check(self, settings) -> Result:
        """Inbox backlog count for cron fallback."""
        vault = Path(settings.vault.path)
        inbox = vault / settings.vault.inbox_dir
        count = len(list(inbox.glob("*.md"))) if inbox.is_dir() else 0
        return Result(
            success=True,
            output=f"Inbox: {count} items",
            data={"inbox_count": count},
        )
