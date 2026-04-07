"""bg think graduate — Context for promoting an idea to permanent status."""

from __future__ import annotations

from src.cli.commands import BaseCommand, Result
from src.cli.commands.think import _execute_queries, _format_json
from src.graph.queries import graduate_queries
from src.graph.types import DocRef, GraduateContext


class GraduateCommand(BaseCommand):
    """Find related context to graduate a fleeting idea into a permanent note."""

    agent_prompt = "Suggest how to structure this idea as a permanent note with connections."

    def run_without_agent(self, **kwargs) -> Result:
        idea: str = kwargs["idea"]
        as_json: bool = kwargs.get("json", False)

        queries = graduate_queries(idea)
        raw = _execute_queries(queries)

        ctx = GraduateContext(idea=idea)
        src_rows = raw.get("source_doc", [])
        if src_rows:
            row = src_rows[0]
            ctx.source_doc = DocRef(
                title=row[0] or "", path=row[1] or "", uid=row[2] or "",
                status=row[3] or "", created=row[4] or "",
            )
        for row in raw.get("related_docs", []):
            ctx.related_docs.append(DocRef(
                title=row[0] or "", path=row[1] or "", uid=row[2] or "",
            ))
        for row in raw.get("nearby_projects", []):
            ctx.nearby_projects.append(DocRef(
                title=row[0] or "", path=row[1] or "", uid=row[2] or "",
            ))

        if as_json:
            return Result(success=True, output=_format_json(ctx), data=ctx)

        lines = [f'GRADUATE: "{idea}"', ""]

        lines.append("SOURCE DOCUMENT")
        lines.append("-" * 40)
        if ctx.source_doc:
            lines.append(f'  "{ctx.source_doc.title}" [{ctx.source_doc.status}]')
            lines.append(f"  {ctx.source_doc.path}")
        else:
            lines.append(f'  (no document found matching "{idea}")')

        lines.append("")
        lines.append(f"RELATED DOCUMENTS ({len(ctx.related_docs)})")
        lines.append("-" * 40)
        if ctx.related_docs:
            for d in ctx.related_docs:
                lines.append(f'  * "{d.title}"  {d.path}')
        else:
            lines.append("  (none)")

        lines.append("")
        lines.append(f"NEARBY PROJECTS ({len(ctx.nearby_projects)})")
        lines.append("-" * 40)
        if ctx.nearby_projects:
            for p in ctx.nearby_projects:
                lines.append(f'  * "{p.title}"  {p.path}')
        else:
            lines.append("  (none)")

        return Result(success=True, output="\n".join(lines), data=ctx)
