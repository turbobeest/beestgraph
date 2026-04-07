"""bg review — Structured daily or weekly review."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from src.cli.commands import BaseCommand, Result
from src.config import load_settings
from src.pipeline.zettelkasten import generate_id


class ReviewCommand(BaseCommand):
    """Create structured review notes (daily or weekly)."""

    agent_prompt = "Synthesize the review data into actionable insights."

    def run_without_agent(self, **kwargs) -> Result:
        weekly: bool = kwargs.get("weekly", False)

        if weekly:
            return self._weekly_review()
        # Default to daily
        return self._daily_review()

    def _daily_review(self) -> Result:
        """Create/open a daily review note."""
        settings = load_settings()
        vault = Path(settings.vault.path)
        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")

        review_dir = vault / settings.vault.daily_dir
        review_dir.mkdir(parents=True, exist_ok=True)
        review_path = review_dir / f"review-{today}.md"

        if review_path.exists():
            return Result(
                success=True,
                output=f"Daily review exists: {review_path}",
                data={"path": str(review_path), "created": False},
            )

        uid = generate_id()
        content = f"""---
uid: "{uid}"
title: "Daily Review — {today}"
type: note
tags: [review, daily]
status: inbox
dates:
  created: {today}
  captured: {today}
  processed: null
  modified: {today}
source:
  type: manual
para: areas
content_stage: fleeting
version: 1
---

## What I accomplished today

## What I learned

## What needs attention tomorrow

## Decisions made

## Open questions

"""
        review_path.write_text(content, encoding="utf-8")
        return Result(
            success=True,
            output=f"Created daily review: {review_path}",
            data={"path": str(review_path), "created": True},
        )

    def _weekly_review(self) -> Result:
        """Run bg think emerge + recap and format a weekly review."""
        from src.cli.commands.recap import RecapCommand
        from src.cli.commands.think.emerge import EmergeCommand

        settings = load_settings()
        vault = Path(settings.vault.path)
        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")

        emerge_result = EmergeCommand().run_without_agent(period=7)
        recap_result = RecapCommand().run_without_agent(period="7d")

        review_dir = vault / settings.vault.daily_dir
        review_dir.mkdir(parents=True, exist_ok=True)
        review_path = review_dir / f"weekly-review-{today}.md"

        uid = generate_id()
        content = f"""---
uid: "{uid}"
title: "Weekly Review — {today}"
type: note
tags: [review, weekly]
status: inbox
dates:
  created: {today}
  captured: {today}
  processed: null
  modified: {today}
source:
  type: manual
para: areas
content_stage: fleeting
version: 1
---

## Emerging Patterns

{emerge_result.output}

## Activity Recap

{recap_result.output}

## Reflections

## Next week's focus

"""
        review_path.write_text(content, encoding="utf-8")
        return Result(
            success=True,
            output=f"Created weekly review: {review_path}",
            data={"path": str(review_path), "created": True},
        )
