"""bg think forecast — Topic frequency timeline and trend detection."""

from __future__ import annotations

from src.cli.commands import BaseCommand, Result
from src.cli.commands.think import _execute_queries, _format_json
from src.graph.queries import forecast_queries
from src.graph.types import FrequencyTimeline, MonthlyCount, TrendItem


class ForecastCommand(BaseCommand):
    """Show document frequency over time for a topic and detect trends."""

    agent_prompt = "Interpret these trends and forecast future activity."

    def run_without_agent(self, **kwargs) -> Result:
        topic: str = kwargs["topic"]
        as_json: bool = kwargs.get("json", False)

        queries = forecast_queries(topic)
        raw = _execute_queries(queries)

        timeline = FrequencyTimeline(topic=topic)
        for row in raw.get("monthly_counts", []):
            timeline.monthly_counts.append(
                MonthlyCount(month=row[0] or "", count=int(row[1] or 0))
            )

        # Build related trends from entity mention data
        entity_data: dict[str, list[MonthlyCount]] = {}
        for row in raw.get("related_trends", []):
            entity = row[0] or ""
            month = row[1] or ""
            cnt = int(row[2] or 0)
            entity_data.setdefault(entity, []).append(MonthlyCount(month=month, count=cnt))
        for name, counts in entity_data.items():
            timeline.related_trends.append(TrendItem(name=name, counts=counts))

        # Determine trend direction
        if len(timeline.monthly_counts) >= 2:
            recent = timeline.monthly_counts[-1].count
            earlier = timeline.monthly_counts[0].count
            if recent > earlier:
                timeline.trend_direction = "rising"
            elif recent < earlier:
                timeline.trend_direction = "falling"
            else:
                timeline.trend_direction = "stable"
        else:
            timeline.trend_direction = "insufficient data"

        if as_json:
            return Result(success=True, output=_format_json(timeline), data=timeline)

        lines = [f'FORECAST: "{topic}"', ""]

        lines.append("MONTHLY DOCUMENT COUNT")
        lines.append("-" * 40)
        if timeline.monthly_counts:
            max_count = max(mc.count for mc in timeline.monthly_counts) or 1
            for mc in timeline.monthly_counts:
                bar = "#" * max(1, int(mc.count / max_count * 20))
                lines.append(f"  {mc.month}  {mc.count:>3}  {bar}")
        else:
            lines.append("  (no data)")

        lines.append("")
        lines.append(f"TREND: {timeline.trend_direction}")

        if timeline.related_trends:
            lines.append("")
            lines.append(f"RELATED ENTITY TRENDS ({len(timeline.related_trends)})")
            lines.append("-" * 40)
            for trend in timeline.related_trends[:10]:
                total = sum(c.count for c in trend.counts)
                lines.append(f"  {trend.name}: {total} mentions across {len(trend.counts)} months")

        return Result(success=True, output="\n".join(lines), data=timeline)
