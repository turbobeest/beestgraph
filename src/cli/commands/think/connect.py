"""bg think connect — Find paths between two concepts."""

from __future__ import annotations

from src.cli.commands import BaseCommand, Result
from src.cli.commands.think import _execute_queries, _format_json
from src.graph.queries import connect_queries
from src.graph.types import ConnectionPaths, DocRef


class ConnectCommand(BaseCommand):
    """Find shortest paths, shared neighbors, and bridging documents."""

    agent_prompt = "Explain the connection between these concepts and suggest synthesis."

    def run_without_agent(self, **kwargs) -> Result:
        a: str = kwargs["a"]
        b: str = kwargs["b"]
        as_json: bool = kwargs.get("json", False)

        queries = connect_queries(a, b)
        raw = _execute_queries(queries)

        paths = ConnectionPaths(concept_a=a, concept_b=b)
        for row in raw.get("shortest_path", []):
            paths.shortest_path.append(str(row[0]) if row[0] else "")
        for row in raw.get("shared_nodes", []):
            paths.shared_nodes.append(str(row[0]) if row[0] else "")
        for row in raw.get("bridging_docs", []):
            paths.bridging_docs.append(DocRef(
                title=row[0] or "", path=row[1] or "", uid=row[2] or "",
            ))

        if as_json:
            return Result(success=True, output=_format_json(paths), data=paths)

        lines = [f'CONNECTION: "{a}" <-> "{b}"', ""]

        lines.append("SHORTEST PATH")
        lines.append("-" * 40)
        if paths.shortest_path:
            lines.append("  " + " → ".join(paths.shortest_path))
        else:
            lines.append("  (no path found)")

        lines.append("")
        lines.append(f"SHARED NEIGHBORS ({len(paths.shared_nodes)})")
        lines.append("-" * 40)
        if paths.shared_nodes:
            for n in paths.shared_nodes:
                lines.append(f"  * {n}")
        else:
            lines.append("  (none)")

        lines.append("")
        lines.append(f"BRIDGING DOCUMENTS ({len(paths.bridging_docs)})")
        lines.append("-" * 40)
        if paths.bridging_docs:
            for d in paths.bridging_docs:
                lines.append(f'  * "{d.title}"')
                lines.append(f"    {d.path}")
        else:
            lines.append("  (no documents mention both)")

        return Result(success=True, output="\n".join(lines), data=paths)
