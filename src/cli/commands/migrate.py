"""bg migrate — Vault document migration tool.

Upgrades document frontmatter to the current template spec. Idempotent:
running twice produces the same result as running once. Read-only by
default — requires ``--write`` to modify files.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import frontmatter as fm
import structlog

from src.cli.commands import BaseCommand, Result
from src.config import load_settings
from src.pipeline.zettelkasten import generate_id

logger = structlog.get_logger(__name__)

_QUALITY_MAP = {"low": 0.3, "medium": 0.6, "high": 0.9}

# Flat kebab-case keys that should be nested under a parent
_FLAT_TO_NESTED = {
    "source-url": ("source", "url"),
    "source-type": ("source", "type"),
    "source-author": ("source", "author"),
    "source-context": ("source", "context"),
    "source_url": ("source", "url"),
    "source_type": ("source", "type"),
    "date-created": ("dates", "created"),
    "date-captured": ("dates", "captured"),
    "date-processed": ("dates", "processed"),
    "date-modified": ("dates", "modified"),
    "date_created": ("dates", "created"),
    "date_captured": ("dates", "captured"),
    "date_processed": ("dates", "processed"),
    "date_modified": ("dates", "modified"),
    "created_at": ("dates", "created"),
    "modified_at": ("dates", "modified"),
}


def _migrate_one(
    filepath: Path,
    uid_only: bool = False,
    do_frontmatter: bool = False,
) -> dict:
    """Migrate a single file's frontmatter. Returns a change report.

    Does NOT write to disk — caller decides based on --write flag.
    """
    raw = filepath.read_text(encoding="utf-8")
    post = fm.loads(raw)
    meta = dict(post.metadata)
    changes: list[str] = []

    # --- UID backfill ---
    if not meta.get("uid"):
        # Use file mtime for past documents
        try:
            mtime = os.path.getmtime(filepath)
            mtime_dt = datetime.fromtimestamp(mtime, tz=UTC)
            uid = mtime_dt.strftime("%Y%m%d%H%M%S")
        except OSError:
            uid = generate_id()
        meta["uid"] = uid
        changes.append(f"uid: generated {uid}")

    if uid_only:
        return {"path": str(filepath), "changes": changes, "meta": meta, "post": post}

    if not do_frontmatter:
        return {"path": str(filepath), "changes": changes, "meta": meta, "post": post}

    # --- quality → confidence ---
    quality = meta.pop("quality", None)
    if quality and not meta.get("confidence"):
        conf = _QUALITY_MAP.get(str(quality).lower(), 0.5)
        meta["confidence"] = conf
        changes.append(f"quality:{quality} → confidence:{conf}")

    # --- Flat kebab-case → nested ---
    for flat_key, (parent, child) in _FLAT_TO_NESTED.items():
        if flat_key in meta:
            value = meta.pop(flat_key)
            if parent not in meta:
                meta[parent] = {}
            if isinstance(meta[parent], dict) and child not in meta[parent]:
                meta[parent][child] = value
                changes.append(f"{flat_key} → {parent}.{child}")

    # --- Missing dates.created → from file mtime ---
    dates = meta.get("dates", {})
    if isinstance(dates, dict) and not dates.get("created"):
        try:
            mtime = os.path.getmtime(filepath)
            mtime_dt = datetime.fromtimestamp(mtime, tz=UTC)
            dates["created"] = mtime_dt.strftime("%Y-%m-%d")
            meta["dates"] = dates
            changes.append("dates.created: inferred from mtime")
        except OSError:
            pass

    # --- Missing status → default to published ---
    if not meta.get("status"):
        meta["status"] = "published"
        changes.append("status: set to 'published' (default for existing docs)")

    # --- Missing version ---
    if "version" not in meta:
        meta["version"] = 1
        changes.append("version: set to 1")

    # --- Maturity → content_stage ---
    maturity = meta.pop("maturity", None)
    if maturity and not meta.get("content_stage"):
        stage_map = {"raw": "fleeting", "permanent": "evergreen"}
        stage = stage_map.get(str(maturity).lower(), str(maturity).lower())
        meta["content_stage"] = stage
        changes.append(f"maturity:{maturity} → content_stage:{stage}")

    # --- para_category → para ---
    para_cat = meta.pop("para_category", None)
    if para_cat and not meta.get("para"):
        meta["para"] = para_cat
        changes.append(f"para_category → para:{para_cat}")

    # --- content_type → type ---
    content_type = meta.pop("content_type", None)
    if content_type and not meta.get("type"):
        meta["type"] = content_type
        changes.append(f"content_type → type:{content_type}")

    return {"path": str(filepath), "changes": changes, "meta": meta, "post": post}


class MigrateCommand(BaseCommand):
    """Migrate vault documents to the current frontmatter spec."""

    def run_without_agent(self, **kwargs) -> Result:
        dry_run: bool = kwargs.get("dry_run", False)
        uid_only: bool = kwargs.get("uid_only", False)
        do_frontmatter: bool = kwargs.get("frontmatter", False)
        do_all: bool = kwargs.get("all", False)
        write: bool = kwargs.get("write", False)
        single_path: str | None = kwargs.get("path")

        if do_all:
            uid_only = True
            do_frontmatter = True

        # Safety: read-only unless --write is explicitly passed
        if not write:
            dry_run = True

        settings = load_settings()
        vault = Path(settings.vault.path)

        # Collect files
        if single_path:
            target = Path(single_path)
            if not target.is_absolute():
                target = vault / single_path
            if not target.exists():
                return Result(success=False, output="", error=f"File not found: {target}")
            files = [target]
        else:
            files = sorted(vault.rglob("*.md"))
            # Skip hidden dirs
            files = [
                f for f in files
                if not any(p.startswith(".") for p in f.relative_to(vault).parts)
            ]

        total = len(files)
        changed = 0
        unchanged = 0
        report_lines: list[str] = []

        for filepath in files:
            try:
                result = _migrate_one(filepath, uid_only=uid_only, do_frontmatter=do_frontmatter)
            except Exception as exc:
                report_lines.append(f"ERROR {filepath}: {exc}")
                continue

            if result["changes"]:
                changed += 1
                rel = filepath.relative_to(vault) if filepath.is_relative_to(vault) else filepath
                report_lines.append(f"  {rel}")
                for c in result["changes"]:
                    report_lines.append(f"    + {c}")

                if not dry_run:
                    post = result["post"]
                    post.metadata = result["meta"]
                    filepath.write_text(fm.dumps(post), encoding="utf-8")
            else:
                unchanged += 1

        mode = "DRY RUN" if dry_run else "APPLIED"
        summary = (
            f"Migration [{mode}]: {total} files scanned, "
            f"{changed} changed, {unchanged} unchanged"
        )
        lines = [summary, ""]
        if report_lines:
            lines.extend(report_lines)
        else:
            lines.append("No changes needed.")

        return Result(
            success=True,
            output="\n".join(lines),
            data={"total": total, "changed": changed, "unchanged": unchanged, "dry_run": dry_run},
        )
