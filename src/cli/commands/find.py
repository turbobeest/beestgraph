"""bg find — Graph-powered document search."""

from __future__ import annotations

import json

from src.cli.commands import BaseCommand, Result
from src.config import load_settings
from src.graph.queries import search_documents


class FindCommand(BaseCommand):
    """Search the knowledge graph for documents matching a query."""

    agent_prompt = "Summarize search results and suggest related topics."

    def run_without_agent(self, **kwargs) -> Result:
        query: str = kwargs["query"]
        limit: int = kwargs.get("limit", 10)
        doc_type: str | None = kwargs.get("type")
        as_json: bool = kwargs.get("json", False)

        settings = load_settings()

        from falkordb import FalkorDB

        try:
            db = FalkorDB(
                host=settings.falkordb.host,
                port=settings.falkordb.port,
                password=settings.falkordb.password or None,
            )
            graph = db.select_graph(settings.falkordb.graph_name)
        except Exception as exc:
            return Result(success=False, output="", error=f"FalkorDB connection failed: {exc}")

        cypher, params = search_documents(query, limit=limit)
        try:
            result = graph.query(cypher, params)
        except Exception as exc:
            return Result(success=False, output="", error=f"Query failed: {exc}")

        rows: list[dict] = []
        for record in result.result_set:
            node = record[0]
            score = record[1] if len(record) > 1 else 0
            props = node.properties if hasattr(node, "properties") else {}
            node_type = props.get("type", "")
            if doc_type and node_type != doc_type:
                continue
            rows.append({
                "title": props.get("title", "(untitled)"),
                "path": props.get("path", ""),
                "type": node_type,
                "score": round(float(score), 3) if score else 0,
            })

        if as_json:
            output = json.dumps(rows, indent=2)
        else:
            if not rows:
                output = f"No results for '{query}'"
            else:
                lines = []
                for i, r in enumerate(rows, 1):
                    lines.append(
                        f"  {i}. [{r['score']:.2f}] {r['title']}\n"
                        f"     {r['path']}  ({r['type'] or 'untyped'})"
                    )
                output = f"Found {len(rows)} result(s) for '{query}':\n" + "\n".join(lines)

        return Result(success=True, output=output, data=rows)
