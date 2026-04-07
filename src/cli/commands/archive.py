"""bg archive — Move a document to archived status."""

from __future__ import annotations

import shutil
from pathlib import Path

import frontmatter as fm

from src.cli.commands import BaseCommand, Result
from src.config import load_settings


class ArchiveCommand(BaseCommand):
    """Set a document's status to archived and move it to the archive directory."""

    def run_without_agent(self, **kwargs) -> Result:
        slug_or_path: str = kwargs["slug_or_path"]
        reason: str | None = kwargs.get("reason")

        settings = load_settings()
        vault = Path(settings.vault.path)
        archive_dir = vault / settings.vault.archive_dir

        # Resolve the file
        filepath = Path(slug_or_path)
        if not filepath.is_absolute():
            filepath = vault / slug_or_path
        if not filepath.exists():
            # Try searching by filename
            matches = list(vault.rglob(f"*{slug_or_path}*"))
            md_matches = [m for m in matches if m.suffix == ".md"]
            if len(md_matches) == 1:
                filepath = md_matches[0]
            elif len(md_matches) > 1:
                names = "\n".join(f"  - {m.relative_to(vault)}" for m in md_matches[:10])
                return Result(
                    success=False,
                    output="",
                    error=f"Multiple matches for '{slug_or_path}':\n{names}",
                )
            else:
                return Result(
                    success=False,
                    output="",
                    error=f"Document not found: {slug_or_path}",
                )

        # Update frontmatter
        raw = filepath.read_text(encoding="utf-8")
        post = fm.loads(raw)
        post.metadata["status"] = "archived"
        if reason:
            post.metadata["archive_reason"] = reason
        filepath.write_text(fm.dumps(post), encoding="utf-8")

        # Move to archive
        archive_dir.mkdir(parents=True, exist_ok=True)
        dest = archive_dir / filepath.name
        counter = 1
        while dest.exists():
            dest = archive_dir / f"{filepath.stem}-{counter}{filepath.suffix}"
            counter += 1
        shutil.move(str(filepath), str(dest))

        # Update FalkorDB node
        try:
            from falkordb import FalkorDB

            db = FalkorDB(
                host=settings.falkordb.host,
                port=settings.falkordb.port,
                password=settings.falkordb.password or None,
            )
            graph = db.select_graph(settings.falkordb.graph_name)
            old_path = str(filepath.relative_to(vault))
            new_path = str(dest.relative_to(vault))
            graph.query(
                "MATCH (d:Document {path: $old_path}) "
                "SET d.status = 'archived', d.path = $new_path",
                {"old_path": old_path, "new_path": new_path},
            )
        except Exception as exc:
            import structlog
            structlog.get_logger(__name__).debug("graph_update_skipped", error=str(exc))

        return Result(
            success=True,
            output=f"Archived: {filepath.name} → {dest}",
            data={"source": str(filepath), "dest": str(dest)},
        )
