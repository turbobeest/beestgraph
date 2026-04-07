"""bg think emerge — Detect emerging patterns in the knowledge graph."""

from __future__ import annotations

from src.cli.commands import BaseCommand, Result
from src.cli.commands.think import _execute_queries, _format_json
from src.graph.queries import emerge_queries
from src.graph.types import EmergenceReport, EntityPair, TagCount, TopicCount


class EmergeCommand(BaseCommand):
    """Identify trending tags, entity clusters, and topic density."""

    agent_prompt = "Identify the most significant emerging patterns and explain why."

    def run_without_agent(self, **kwargs) -> Result:
        period_days: int = kwargs.get("period", 30)
        as_json: bool = kwargs.get("json", False)

        queries = emerge_queries(period_days)
        raw = _execute_queries(queries)

        report = EmergenceReport(period_days=period_days)
        for row in raw.get("trending_tags", []):
            report.trending_tags.append(TagCount(tag=row[0] or "", count=int(row[1] or 0)))
        for row in raw.get("entity_clusters", []):
            report.entity_clusters.append(EntityPair(
                entity_a=row[0] or "", entity_b=row[1] or "",
                co_occurrence_count=int(row[2] or 0),
            ))
        for row in raw.get("topic_density", []):
            report.topic_density.append(TopicCount(topic=row[0] or "", count=int(row[1] or 0)))

        if as_json:
            return Result(success=True, output=_format_json(report), data=report)

        lines = [f"EMERGENCE REPORT (last {period_days} days)", ""]

        lines.append(f"TRENDING TAGS ({len(report.trending_tags)})")
        lines.append("-" * 40)
        for tc in report.trending_tags[:15]:
            bar = "#" * min(tc.count, 30)
            lines.append(f"  {tc.tag:<30} {tc.count:>3}  {bar}")

        lines.append("")
        lines.append(f"ENTITY CLUSTERS ({len(report.entity_clusters)})")
        lines.append("-" * 40)
        if report.entity_clusters:
            for ep in report.entity_clusters:
                lines.append(f"  {ep.entity_a} <-> {ep.entity_b}  ({ep.co_occurrence_count}x)")
        else:
            lines.append("  (no co-occurring entity pairs found)")

        lines.append("")
        lines.append(f"TOPIC DENSITY ({len(report.topic_density)})")
        lines.append("-" * 40)
        for td in report.topic_density:
            bar = "#" * min(td.count, 30)
            lines.append(f"  {td.topic:<30} {td.count:>3}  {bar}")

        return Result(success=True, output="\n".join(lines), data=report)
