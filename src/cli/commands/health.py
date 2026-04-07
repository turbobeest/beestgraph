"""bg health — System health report."""

from __future__ import annotations

from src.cli.commands import BaseCommand, Result
from src.config import load_settings
from src.heartbeat.checks import run_all_checks

_STATUS_ICONS = {"ok": "+", "warning": "!", "error": "X"}


class HealthCommand(BaseCommand):
    """Run all health checks and print a report."""

    agent_prompt = "Diagnose any failing checks and suggest fixes."

    def run_without_agent(self, **kwargs) -> Result:
        settings = load_settings()

        checks = run_all_checks(
            vault_path=settings.vault.path,
            falkordb_host=settings.falkordb.host,
            falkordb_port=settings.falkordb.port,
        )

        # Add orphan count and queue backlog
        extra_lines: list[str] = []
        try:
            from falkordb import FalkorDB

            db = FalkorDB(
                host=settings.falkordb.host,
                port=settings.falkordb.port,
                password=settings.falkordb.password or None,
            )
            graph = db.select_graph(settings.falkordb.graph_name)

            # Orphan count (documents with no tags or topics)
            orphan_result = graph.query(
                "MATCH (d:Document) "
                "WHERE NOT (d)-[:TAGGED_WITH]->() AND NOT (d)-[:BELONGS_TO]->() "
                "RETURN count(d) AS cnt"
            )
            orphan_count = (
                orphan_result.result_set[0][0] if orphan_result.result_set else 0
            )
            extra_lines.append(f"  Orphan documents (no tags/topics): {orphan_count}")

            # Queue backlog
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

        output = "\n".join(lines)
        return Result(
            success=True,
            output=output,
            data={"checks": [c.__dict__ for c in checks], "has_errors": has_error},
        )
