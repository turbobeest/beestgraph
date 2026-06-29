#!/usr/bin/env python3
"""Re-aggregate the three entertainment sub-MOCs from per-item pages.

Scans every .md under 07-resources/entertainment/{reading,movies,tv}/, reads
each item's `consumption_status` from frontmatter, and rewrites the parent
MOC in each subfolder with a fresh checklist that reflects current state.

Run on a cron, after editing item statuses, or whenever the per-item truth
has drifted from the index.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
import re

VAULT = Path("/home/turbobeest/vault/07-resources/entertainment")
TODAY = date.today().isoformat()

SECTIONS = {
    "reading": {
        "moc_title": "Reading List",
        "section_label": "Reading List",
        "type_label": "book",
        "extra_tag": "books",
        "topic": "entertainment/reading",
    },
    "movies": {
        "moc_title": "Watchlist - Movies",
        "section_label": "Movies",
        "type_label": "movie",
        "extra_tag": "movies",
        "topic": "entertainment/film",
    },
    "tv": {
        "moc_title": "Watchlist - TV Shows",
        "section_label": "TV Shows",
        "type_label": "TV series",
        "extra_tag": "tv",
        "topic": "entertainment/television",
    },
}

STATUS_RE = re.compile(r"^consumption_status:\s*(\S+)\s*$", re.MULTILINE)


def read_status(path: Path) -> str:
    m = STATUS_RE.search(path.read_text())
    return m.group(1).strip() if m else "queued"


def refresh_section(slug: str) -> tuple[int, int]:
    meta = SECTIONS[slug]
    folder = VAULT / slug
    if not folder.exists():
        return 0, 0
    items = sorted(p for p in folder.glob("*.md") if p.stem != meta["moc_title"])
    rows = [(p.stem, read_status(p)) for p in items]
    finished = sum(1 for _, s in rows if s == "finished")

    lines = [f"## {meta['section_label']} ({len(rows)})"]
    for stem, st in rows:
        check = "x" if st == "finished" else " "
        lines.append(f"- [{check}] [[{stem}]]")
    body = "\n".join(lines)

    moc = f"""---
aliases:
- {slug}-list
created: 2023-11-22
status: published
summary: {meta['moc_title']} — index of per-{meta['type_label']} pages under 07-resources/entertainment/{slug}/.
tags:
- entertainment
- {meta['extra_tag']}
- moc
title: {meta['moc_title']}
topics:
- {meta['topic']}
type: moc
uid: '20260503160000'
updated: {TODAY}
version: 1
---

# {meta['moc_title']}

Per-{meta['type_label']} entries live in `07-resources/entertainment/{slug}/`. Per-item `consumption_status` is the source of truth (values: `queued | in-progress | finished | dropped`); this index reflects it.

**{len(rows)} {meta['type_label']}s. Finished: {finished}.**

{body}

## Related
- [[Reading List]]
- [[Watchlist - Movies]]
- [[Watchlist - TV Shows]]
- [[Bucket List]]
"""
    (folder / f"{meta['moc_title']}.md").write_text(moc)
    return len(rows), finished


def main() -> None:
    for slug in SECTIONS:
        n, fin = refresh_section(slug)
        print(f"  {SECTIONS[slug]['moc_title']}: {n} entries, {fin} finished.")


if __name__ == "__main__":
    main()
