"""bg project — Project status from vault and graph."""

from __future__ import annotations

from pathlib import Path

from src.cli.commands import BaseCommand, Result
from src.config import load_settings


class ProjectCommand(BaseCommand):
    """Show project status from the vault README and graph data."""

    agent_prompt = "Analyze project progress and suggest next actions."

    def run_without_agent(self, **kwargs) -> Result:
        project_name: str = kwargs["project_name"]
        status_filter: str | None = kwargs.get("status")

        settings = load_settings()
        vault = Path(settings.vault.path)
        project_dir = vault / settings.vault.projects_dir / project_name

        lines: list[str] = [f"Project: {project_name}"]

        # Read README if it exists
        readme = project_dir / "README.md"
        if readme.exists():
            content = readme.read_text(encoding="utf-8")
            # Extract first non-empty, non-frontmatter lines as summary
            in_frontmatter = False
            summary_lines: list[str] = []
            for line in content.splitlines():
                if line.strip() == "---":
                    in_frontmatter = not in_frontmatter
                    continue
                if in_frontmatter:
                    continue
                if line.strip() and len(summary_lines) < 3:
                    summary_lines.append(line.strip())
            if summary_lines:
                lines.append("Summary: " + " ".join(summary_lines))
        else:
            lines.append(f"No README.md found at {project_dir}")

        # Query FalkorDB for project documents
        try:
            from falkordb import FalkorDB

            db = FalkorDB(
                host=settings.falkordb.host,
                port=settings.falkordb.port,
                password=settings.falkordb.password or None,
            )
            graph = db.select_graph(settings.falkordb.graph_name)

            cypher = (
                "MATCH (d:Document)-[:BELONGS_TO]->(tp:Topic) "
                "WHERE tp.name CONTAINS $project "
                "RETURN d.title, d.status, d.path "
                "ORDER BY d.created DESC LIMIT 20"
            )
            result = graph.query(cypher, {"project": project_name})
            docs = result.result_set

            if docs:
                lines.append(f"\nGraph documents ({len(docs)}):")
                for doc in docs:
                    title = doc[0] or "(untitled)"
                    doc_status = doc[1] or "unknown"
                    if status_filter and doc_status != status_filter:
                        continue
                    lines.append(f"  - [{doc_status}] {title}")
            else:
                lines.append("\nNo documents linked to this project in the graph.")
        except Exception as exc:
            lines.append(f"\nGraph query failed: {exc}")

        output = "\n".join(lines)
        return Result(success=True, output=output, data={"project": project_name})
