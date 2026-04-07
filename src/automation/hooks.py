"""Session-end hooks and git integration for beestgraph."""

from __future__ import annotations

from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


def on_session_end(session_summary: str = "") -> None:
    """Called when a bg session ends or by a git hook.

    If session_summary is provided, passes it to ``bg save`` for
    extraction of action items and decisions.

    Args:
        session_summary: Optional text describing what happened in the session.
    """
    if not session_summary:
        return

    from src.cli.commands.save import SaveCommand

    result = SaveCommand().run_without_agent(text=session_summary)
    if result.success:
        logger.info("session_knowledge_saved", path=result.data.get("path"))
    else:
        logger.warning("session_save_failed", error=result.error)


def install_git_hook(repo_path: str | Path | None = None) -> Path:
    """Install a post-commit git hook that runs ``bg health --quick``.

    Args:
        repo_path: Path to the git repo. Defaults to ``~/beestgraph``.

    Returns:
        Path to the installed hook file.
    """
    repo = Path(repo_path) if repo_path else Path.home() / "beestgraph"
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_path = hooks_dir / "post-commit"
    hook_content = """#!/bin/bash
# beestgraph post-commit hook — quick health check after every commit
bg health --quick 2>/dev/null || true
"""
    hook_path.write_text(hook_content, encoding="utf-8")
    hook_path.chmod(0o755)
    logger.info("git_hook_installed", path=str(hook_path))
    return hook_path
