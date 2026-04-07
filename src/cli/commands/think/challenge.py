"""bg think challenge — Surface counter-evidence for a topic."""

from __future__ import annotations

from src.cli.commands import BaseCommand, Result
from src.cli.commands.think import _execute_queries, _format_json
from src.graph.queries import challenge_queries
from src.graph.types import ChallengeEvidence, DocRef


class ChallengeCommand(BaseCommand):
    """Find decisions, contradictions, and reversals for a topic."""

    agent_prompt = "Synthesize a counter-argument from the evidence below."

    def run_without_agent(self, **kwargs) -> Result:
        topic: str = kwargs["topic"]
        as_json: bool = kwargs.get("json", False)

        queries = challenge_queries(topic)
        raw = _execute_queries(queries)

        evidence = ChallengeEvidence(topic=topic)
        for row in raw.get("decisions", []):
            evidence.decisions.append(DocRef(
                title=row[0] or "", path=row[1] or "", uid=row[2] or "",
                status=row[3] or "", created=row[4] or "",
                confidence=float(row[5]) if row[5] else 0.0,
            ))
        for row in raw.get("contradictions", []):
            evidence.contradictions.append(DocRef(
                title=f"{row[0]} → {row[2]}",
                path=row[1] or "",
            ))
        for row in raw.get("reversed", []):
            evidence.reversed.append(DocRef(
                title=row[0] or "", path=row[1] or "", uid=row[2] or "",
                status=row[3] or "", created=row[4] or "",
            ))

        if as_json:
            return Result(success=True, output=_format_json(evidence), data=evidence)

        lines = [f'CHALLENGE: "{topic}"', ""]

        lines.append(f"DECISIONS ({len(evidence.decisions)})")
        lines.append("-" * 40)
        if evidence.decisions:
            for d in evidence.decisions:
                lines.append(f'  * "{d.title}" ({d.created}, conf: {d.confidence})')
                lines.append(f"    {d.path}")
        else:
            lines.append("  (none found)")

        lines.append("")
        lines.append(f"CONTRADICTIONS ({len(evidence.contradictions)})")
        lines.append("-" * 40)
        if evidence.contradictions:
            for c in evidence.contradictions:
                lines.append(f"  * {c.title}")
        else:
            lines.append("  (none found)")

        lines.append("")
        lines.append(f"REVERSED/ABANDONED ({len(evidence.reversed)})")
        lines.append("-" * 40)
        if evidence.reversed:
            for r in evidence.reversed:
                lines.append(f'  * "{r.title}" [{r.status}] ({r.created})')
        else:
            lines.append("  (none found)")

        return Result(success=True, output="\n".join(lines), data=evidence)
