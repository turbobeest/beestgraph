"""beestgraph.bot — Telegram bot for querying and managing the knowledge graph.

Provides a Telegram interface for searching documents, viewing stats,
adding URLs, and browsing topics via aiogram 3.x.
"""

from __future__ import annotations

__all__ = [
    "create_bot",
    "router",
]

from src.bot.telegram_bot import create_bot, router
