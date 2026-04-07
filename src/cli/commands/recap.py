"""bg recap — Narrative summary of recent knowledge graph activity."""

from __future__ import annotations

from src.cli.commands import BaseCommand, Result
from src.config import load_settings


class RecapCommand(BaseCommand):
    """Query FalkorDB for recent documents and format a summary."""

    agent_prompt = "Turn this structured recap into a narrative briefing."

    def run_without_agent(self, **kwargs) -> Result:
        period: str = kwargs.get("period", "7d")

        settings = load_settings()

        try:
            from falkordb import FalkorDB

            db = FalkorDB(
                host=settings.falkordb.host,
                port=settings.falkordb.port,
                password=settings.falkordb.password or None,
            )
            graph = db.select_graph(settings.falkordb.graph_name)
        except Exception as exc:
            return Result(success=False, output="", error=f"FalkorDB connection failed: {exc}")

        try:
            result = graph.query(
                "MATCH (d:Document) "
                "RETURN d.title, d.type, d.status, d.created, d.summary "
                "ORDER BY d.created DESC LIMIT 20"
            )
        except Exception as exc:
            return Result(success=False, output="", error=f"Query failed: {exc}")

        docs = result.result_set or []
        lines = [f"RECAP (last {period})", "=" * 40, ""]

        if not docs:
            lines.append("No recent documents found.")
        else:
            # Group by type
            by_type: dict[str, list] = {}
            for row in docs:
                doc_type = row[1] or "untyped"
                by_type.setdefault(doc_type, []).append(row)

            for doc_type, items in sorted(by_type.items()):
                lines.append(f"## {doc_type} ({len(items)})")
                for row in items:
                    title = row[0] or "(untitled)"
                    status = row[2] or ""
                    created = row[3] or ""
                    summary = (row[4] or "")[:80]
                    lines.append(f"  - [{status}] {title} ({created})")
                    if summary:
                        lines.append(f"    {summary}")
                lines.append("")

        return Result(
            success=True,
            output="\n".join(lines),
            data={"count": len(docs), "period": period},
        )
