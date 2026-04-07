"""bg think audit — Verify a claim against the knowledge graph."""

from __future__ import annotations

from src.cli.commands import BaseCommand, Result
from src.cli.commands.think import _execute_queries, _format_json
from src.graph.queries import audit_queries
from src.graph.types import AuditEvidence, DocRef


class AuditCommand(BaseCommand):
    """Search for supporting and contradicting evidence for a claim."""

    agent_prompt = "Evaluate the strength of evidence and assign a confidence score."

    def run_without_agent(self, **kwargs) -> Result:
        claim: str = kwargs["claim"]
        as_json: bool = kwargs.get("json", False)

        queries = audit_queries(claim)
        raw = _execute_queries(queries)

        evidence = AuditEvidence(claim=claim)

        # Gather paths from supporting/contradicting to distinguish from unverified
        supported_paths: set[str] = set()
        for row in raw.get("supporting", []):
            path = row[1] or ""
            supported_paths.add(path)
            evidence.supporting.append(DocRef(
                title=row[0] or "", path=path, uid=row[2] or "",
                created=row[3] or "",
                confidence=float(row[4]) if row[4] else 0.0,
            ))

        contradicted_paths: set[str] = set()
        for row in raw.get("contradicting", []):
            path = row[1] or ""
            contradicted_paths.add(path)
            evidence.contradicting.append(DocRef(
                title=row[0] or "", path=path, uid=row[2] or "",
                created=row[3] or "",
                confidence=float(row[4]) if row[4] else 0.0,
            ))

        # Matching docs that aren't in supporting/contradicting are unverified
        for row in raw.get("matching", []):
            path = row[1] or ""
            if path not in supported_paths and path not in contradicted_paths:
                evidence.unverified.append(DocRef(
                    title=row[0] or "", path=path, uid=row[2] or "",
                    created=row[3] or "",
                    confidence=float(row[4]) if row[4] else 0.0,
                    claim=row[5] or "",
                ))

        if as_json:
            return Result(success=True, output=_format_json(evidence), data=evidence)

        lines = [f'CLAIM: "{claim}"', ""]

        lines.append(f"SUPPORTING EVIDENCE ({len(evidence.supporting)} documents)")
        lines.append("-" * 40)
        if evidence.supporting:
            for d in evidence.supporting:
                lines.append(f'  * "{d.title}" ({d.created}, confidence: {d.confidence})')
                if d.claim:
                    lines.append(f"    Claim: \"{d.claim}\"")
        else:
            lines.append("  (none)")

        lines.append("")
        lines.append(f"CONTRADICTING EVIDENCE ({len(evidence.contradicting)} documents)")
        lines.append("-" * 40)
        if evidence.contradicting:
            for d in evidence.contradicting:
                lines.append(f'  * "{d.title}" ({d.created}, confidence: {d.confidence})')
                if d.claim:
                    lines.append(f"    Claim: \"{d.claim}\"")
        else:
            lines.append("  (none)")

        lines.append("")
        lines.append(f"UNVERIFIED MENTIONS ({len(evidence.unverified)} documents)")
        lines.append("-" * 40)
        if evidence.unverified:
            for d in evidence.unverified:
                desc = f" — {d.claim}" if d.claim else ""
                lines.append(f'  * "{d.title}"{desc}')
        else:
            lines.append("  (none)")

        return Result(success=True, output="\n".join(lines), data=evidence)
