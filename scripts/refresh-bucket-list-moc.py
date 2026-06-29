#!/usr/bin/env python3
"""Re-aggregate the Bucket List MOC from per-item pages.

Scans every .md under 07-resources/bucket-list/<section>/, reads each
item's `bucket_status` from frontmatter, and rewrites Bucket List.md
with a fresh sectioned checklist that reflects current state.

Run on a cron, after editing item statuses, or whenever the per-item
truth has drifted from the parent index.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
import re

VAULT = Path("/home/turbobeest/vault/07-resources/bucket-list")
TODAY = date.today().isoformat()

SECTION_ORDER = [
    ("adventure", "Adventure"),
    ("exotic-food-drink", "Exotic Food & Drink"),
    ("food-drink-experiences", "Food & Drink Experiences"),
    ("creative", "Creative"),
    ("style-wellness", "Style & Wellness"),
    ("nature-wildlife", "Nature & Wildlife"),
    ("finance-luxury", "Finance & Luxury"),
    ("entertainment", "Entertainment"),
    ("personal-growth", "Personal Growth"),
]

STATUS_RE = re.compile(r"^bucket_status:\s*(\S+)\s*$", re.MULTILINE)


def read_status(path: Path) -> str:
    text = path.read_text()
    m = STATUS_RE.search(text)
    return m.group(1).strip() if m else "pending"


def main() -> None:
    by_section: dict[str, list[tuple[str, str]]] = {s: [] for s, _ in SECTION_ORDER}
    for sec_slug, _ in SECTION_ORDER:
        sec_dir = VAULT / sec_slug
        if not sec_dir.exists():
            continue
        for fp in sorted(sec_dir.glob("*.md")):
            by_section[sec_slug].append((fp.stem, read_status(fp)))

    sections_md: list[str] = []
    total = 0
    completed = 0
    for sec_slug, sec_label in SECTION_ORDER:
        items = sorted(by_section[sec_slug], key=lambda x: x[0])
        total += len(items)
        completed += sum(1 for _, s in items if s == "completed")
        lines = [f"## {sec_label} ({len(items)})"]
        for title, status in items:
            check = "x" if status == "completed" else " "
            lines.append(f"- [{check}] [[{title}]]")
        sections_md.append("\n".join(lines))

    moc = f"""---
aliases:
- life-goals
- things-to-do
created: 2023-11-22
status: published
summary: Index of personal bucket-list goals across 9 categories. Each item is a separate wiki entry under 07-resources/bucket-list/<section>/.
tags:
- personal
- goals
- bucket-list
- moc
title: Bucket List
topics:
- personal/bucket-list
- personal/goals
type: moc
uid: '20260325004606'
updated: {TODAY}
version: 3
---

# Bucket List

Top-level personal bucket list, organized by category. Each item below is its own wiki entry — click through for "how to accomplish" notes, status, and topical context. Item-level status (the `bucket_status` field on each page) is the source of truth; this index reflects it.

**{total} items across 9 categories. Completed: {completed}.**

{(chr(10) + chr(10)).join(sections_md)}

## Related
- [[Entertainment Index]]
- [[Food & Nutrition List]]
- [[Reading List]]
- [[Drinks List]]
- [[Camping List]]
- [[Restaurants - RI]]
"""
    (VAULT / "Bucket List.md").write_text(moc)
    print(f"Refreshed MOC: {total} items, {completed} completed.")


if __name__ == "__main__":
    main()
