"""bg export — Flat YAML export of vault documents."""

from __future__ import annotations

import json
from pathlib import Path

import frontmatter as fm

from src.cli.commands import BaseCommand, Result
from src.config import load_settings


def _flatten(d: dict, prefix: str = "") -> dict:
    """Flatten nested dict to kebab-case keys.

    Example: ``{"dates": {"created": "2026-01-01"}}`` becomes
    ``{"dates-created": "2026-01-01"}``.
    """
    items: dict = {}
    for k, v in d.items():
        key = f"{prefix}-{k}" if prefix else k
        if isinstance(v, dict):
            items.update(_flatten(v, key))
        else:
            items[key] = v
    return items


class ExportCommand(BaseCommand):
    """Export vault documents as flat YAML/JSON."""

    def run_without_agent(self, **kwargs) -> Result:
        flat: bool = kwargs.get("flat", False)
        output_path: str | None = kwargs.get("output")

        settings = load_settings()
        vault = Path(settings.vault.path)

        docs: list[dict] = []
        for md_file in sorted(vault.rglob("*.md")):
            # Skip hidden dirs and templates
            rel = md_file.relative_to(vault)
            if any(p.startswith(".") for p in rel.parts):
                continue

            try:
                post = fm.load(str(md_file))
            except Exception:  # noqa: S112
                continue

            meta = dict(post.metadata)
            if flat:
                meta = _flatten(meta)
            meta["_path"] = str(rel)
            docs.append(meta)

        output = json.dumps(docs, indent=2, default=str)

        if output_path:
            Path(output_path).write_text(output, encoding="utf-8")
            return Result(
                success=True,
                output=f"Exported {len(docs)} documents to {output_path}",
                data={"count": len(docs), "output_path": output_path},
            )

        return Result(
            success=True,
            output=output,
            data={"count": len(docs)},
        )
