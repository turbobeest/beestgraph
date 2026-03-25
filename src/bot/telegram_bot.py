"""Telegram bot for the beestgraph knowledge graph.

Provides commands for searching documents, viewing recent entries,
browsing topics, inspecting graph stats, and quick-adding URLs to
the inbox. Also supports free-form conversational queries powered
by Claude Code headless mode.

Usage::

    python -m src.bot.telegram_bot          # default config
    python -m src.bot.telegram_bot --config config/beestgraph.yml
"""

from __future__ import annotations

import asyncio
import contextlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import click
import structlog
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from falkordb import FalkorDB

from src.bot.qualification_handler import (
    handle_qualification_response,
    is_qualification_response,
    qualification_router,
    register_chat_id,
    start_notification_poller,
)
from src.config import BeestgraphSettings, FalkorDBSettings, load_settings
from src.graph.queries import (
    recent_documents,
    search_documents,
    topic_tree,
)

if TYPE_CHECKING:
    from falkordb.graph import Graph

logger = structlog.get_logger(__name__)

router = Router(name="beestgraph")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_graph(settings: FalkorDBSettings) -> Graph:
    """Create a FalkorDB graph handle from settings.

    Args:
        settings: FalkorDB connection settings.

    Returns:
        A FalkorDB Graph instance for the configured graph name.
    """
    db = FalkorDB(
        host=settings.host,
        port=settings.port,
        password=settings.password or None,
    )
    return db.select_graph(settings.graph_name)


def _truncate(text: str, length: int = 200) -> str:
    """Truncate text to *length* characters, appending an ellipsis if needed."""
    if len(text) <= length:
        return text
    return text[: length - 1] + "\u2026"


def _escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters for Telegram."""
    specials = r"_*[]()~`>#+-=|{}.!\\"
    out: list[str] = []
    for ch in text:
        if ch in specials:
            out.append("\\")
        out.append(ch)
    return "".join(out)


# ---------------------------------------------------------------------------
# Access control filter
# ---------------------------------------------------------------------------


class _AllowedUsers:
    """Callable filter that restricts commands to allowed Telegram user IDs."""

    def __init__(self, allowed_ids: list[int]) -> None:
        self._allowed = set(allowed_ids)

    def __call__(self, message: Message) -> bool:
        if not self._allowed:
            # Empty allowlist = allow everyone (dev/testing convenience).
            return True
        user_id = message.from_user.id if message.from_user else None
        return user_id is not None and user_id in self._allowed


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start — welcome message with available commands."""
    register_chat_id(message.chat.id)
    text = (
        "Welcome to *beestgraph* \\- your personal knowledge graph bot\\!\n\n"
        "You can chat with me naturally about your knowledge graph, "
        "or use these commands:\n\n"
        "*Search \\& browse:*\n"
        "/search \\<query\\> \\- full\\-text search documents\n"
        "/recent \\- show 5 most recent documents\n"
        "/stats \\- graph statistics\n"
        "/topics \\- list top\\-level topics\n\n"
        "*Capture:*\n"
        "/add \\<url\\> \\[title\\] \\- quick\\-add a URL to inbox\n\n"
        "*Qualification queue:*\n"
        "/queue \\- list items awaiting review\n"
        "/approve \\[name\\] \\- approve to fleeting\n"
        "/approve permanent \\- approve to permanent\n"
        "/reject \\[name\\] \\- reject an item\n"
        "/later \\[time\\] \\- defer review \\(e\\.g\\. `later 9pm`\\)\n\n"
        "*Inline responses \\(when reviewing an item\\):*\n"
        "`ok` \\- approve as fleeting \\| `publish` \\- approve as permanent\n"
        "`public`/`shared`/`private` \\- set visibility\n"
        "`type X` \\| `topic X` \\| `add tag X` \\| `quality high`\n\n"
        "I'll also notify you when new items are captured\\. "
        "You can reply inline to classify, tag, and approve them\\.\n\n"
        "Or just type a question like:\n"
        "_What do I know about knowledge graphs?_\n"
        "_Who are the people in my graph?_\n"
    )
    await message.answer(text, parse_mode="MarkdownV2")


@router.message(Command("search"))
async def cmd_search(message: Message, graph: Graph, **_kwargs: object) -> None:
    """Handle /search <query> — full-text search across documents.

    Args:
        message: Incoming Telegram message.
        graph: FalkorDB graph handle (injected via middleware).
    """
    if not message.text:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Usage: /search <query>")
        return

    query_text = parts[1].strip()
    cypher, params = search_documents(query_text, limit=5)

    user_id = message.from_user.id if message.from_user else None
    logger.info("search_command", query=query_text, user_id=user_id)

    try:
        result = await asyncio.to_thread(graph.query, cypher, params)
    except Exception as exc:
        logger.error("search_query_failed", error=str(exc))
        await message.answer("Search failed. Please try again later.")
        return

    if not result.result_set:
        await message.answer("No documents found.")
        return

    lines: list[str] = []
    for row in result.result_set:
        node = row[0]
        score = row[1]
        title = node.properties.get("title", "Untitled")
        summary = node.properties.get("summary", "")
        source_url = node.properties.get("source_url", "")
        header = _escape_md(title)
        body = _escape_md(_truncate(summary)) if summary else "No summary"
        score_str = _escape_md(f"({score:.2f})")
        line = f"*{header}* {score_str}\n{body}"
        if source_url:
            line += f"\n[Link]({source_url})"
        lines.append(line)

    await message.answer("\n\n".join(lines), parse_mode="MarkdownV2", disable_web_page_preview=True)


@router.message(Command("recent"))
async def cmd_recent(message: Message, graph: Graph, **_kwargs: object) -> None:
    """Handle /recent — show 5 most recent documents.

    Args:
        message: Incoming Telegram message.
        graph: FalkorDB graph handle (injected via middleware).
    """
    cypher, params = recent_documents(n=5)
    logger.info("recent_command", user_id=message.from_user.id if message.from_user else None)

    try:
        result = await asyncio.to_thread(graph.query, cypher, params)
    except Exception as exc:
        logger.error("recent_query_failed", error=str(exc))
        await message.answer("Failed to fetch recent documents.")
        return

    if not result.result_set:
        await message.answer("No documents in the graph yet.")
        return

    lines: list[str] = []
    for row in result.result_set:
        node = row[0]
        title = node.properties.get("title", "Untitled")
        created = node.properties.get("created_at", "unknown date")
        source_url = node.properties.get("source_url", "")
        summary = node.properties.get("summary", "")
        header = _escape_md(title)
        date_str = _escape_md(str(created))
        line = f"*{header}*\n{date_str}"
        if summary:
            line += f"\n{_escape_md(_truncate(summary, 120))}"
        if source_url:
            line += f"\n[Link]({source_url})"
        lines.append(line)

    await message.answer("\n\n".join(lines), parse_mode="MarkdownV2", disable_web_page_preview=True)


@router.message(Command("stats"))
async def cmd_stats(message: Message, graph: Graph, **_kwargs: object) -> None:
    """Handle /stats — display graph statistics.

    Args:
        message: Incoming Telegram message.
        graph: FalkorDB graph handle (injected via middleware).
    """
    logger.info("stats_command", user_id=message.from_user.id if message.from_user else None)

    node_labels = ["Document", "Tag", "Topic", "Person", "Concept", "Source", "Project"]
    counts: dict[str, int] = {}

    try:
        for label in node_labels:
            result = await asyncio.to_thread(graph.query, f"MATCH (n:{label}) RETURN COUNT(n)")
            counts[label] = result.result_set[0][0] if result.result_set else 0
    except Exception as exc:
        logger.error("stats_query_failed", error=str(exc))
        await message.answer("Failed to fetch stats.")
        return

    lines = ["*Graph Statistics*\n"]
    total = 0
    for label in node_labels:
        count = counts[label]
        total += count
        lines.append(f"{_escape_md(label)}: {count}")
    lines.append(f"\nTotal nodes: {total}")

    await message.answer("\n".join(lines), parse_mode="MarkdownV2")


@router.message(Command("add"))
async def cmd_add(message: Message, graph: Graph, **_kwargs: object) -> None:
    """Handle /add <url> [title] — quick-add a URL to inbox.

    Creates a Document node with ``status=inbox`` in the graph.

    Args:
        message: Incoming Telegram message.
        graph: FalkorDB graph handle (injected via middleware).
    """
    if not message.text:
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("Usage: /add <url> [title]")
        return

    url = parts[1].strip()
    title = parts[2].strip() if len(parts) > 2 else url

    now = datetime.now(UTC).isoformat()
    user_id = message.from_user.id if message.from_user else 0

    logger.info("add_command", url=url, title=title, user_id=user_id)

    cypher = (
        "MERGE (d:Document {source_url: $url}) "
        "ON CREATE SET d.title = $title, d.status = 'inbox', "
        "d.source_type = 'manual', d.created_at = $now, d.updated_at = $now "
        "ON MATCH SET d.updated_at = $now "
        "RETURN d"
    )
    params = {"url": url, "title": title, "now": now}

    try:
        await asyncio.to_thread(graph.query, cypher, params)
    except Exception as exc:
        logger.error("add_query_failed", error=str(exc))
        await message.answer("Failed to add URL. Please try again.")
        return

    safe_title = _escape_md(title)
    await message.answer(
        f"Added to inbox: *{safe_title}*",
        parse_mode="MarkdownV2",
    )


@router.message(Command("topics"))
async def cmd_topics(message: Message, graph: Graph, **_kwargs: object) -> None:
    """Handle /topics — list top-level topics.

    Args:
        message: Incoming Telegram message.
        graph: FalkorDB graph handle (injected via middleware).
    """
    logger.info("topics_command", user_id=message.from_user.id if message.from_user else None)

    cypher, params = topic_tree()

    try:
        result = await asyncio.to_thread(graph.query, cypher, params)
    except Exception as exc:
        logger.error("topics_query_failed", error=str(exc))
        await message.answer("Failed to fetch topics.")
        return

    if not result.result_set:
        await message.answer("No topics in the graph yet.")
        return

    # Build a simple indented topic tree.
    lines: list[str] = []
    for row in result.result_set:
        topic_name = row[0]
        level = row[1] if row[1] is not None else 0
        indent = "  " * level
        lines.append(f"{indent}\\- {_escape_md(topic_name)}")

    header = "*Topics*\n\n"
    await message.answer(header + "\n".join(lines), parse_mode="MarkdownV2")


# ---------------------------------------------------------------------------
# Conversational handler — Claude-powered free-form queries
# ---------------------------------------------------------------------------

_CHAT_TIMEOUT_SECONDS = 120

_CHAT_SYSTEM_PROMPT = """\
You are beestgraph, a personal knowledge graph assistant available via Telegram.
You help the user explore, search, and understand their knowledge graph.

The user's graph contains documents, tags, topics, people, concepts, and sources.
Below is context from the graph to help you answer.

RULES:
- Be concise — Telegram messages should be short and readable.
- Use plain text, not markdown (Telegram formatting is limited).
- If the graph context doesn't contain relevant info, say so honestly.
- Suggest /search or /add commands when appropriate.
- Never make up documents or facts that aren't in the context.
"""


async def _build_graph_context(graph: Graph) -> str:
    """Query the graph for recent docs, stats, and topics to give Claude context.

    Args:
        graph: FalkorDB graph handle.

    Returns:
        A text summary of the graph state for inclusion in the prompt.
    """
    sections: list[str] = []

    # Stats
    try:
        labels = ["Document", "Tag", "Topic", "Person", "Concept", "Source"]
        counts: dict[str, int] = {}
        for label in labels:
            result = await asyncio.to_thread(graph.query, f"MATCH (n:{label}) RETURN COUNT(n)")
            counts[label] = result.result_set[0][0] if result.result_set else 0
        stats_lines = [f"  {k}: {v}" for k, v in counts.items()]
        sections.append("GRAPH STATS:\n" + "\n".join(stats_lines))
    except Exception:  # noqa: S110
        pass

    # Recent documents (last 10)
    try:
        cypher, params = recent_documents(n=10)
        result = await asyncio.to_thread(graph.query, cypher, params)
        if result.result_set:
            doc_lines: list[str] = []
            for row in result.result_set:
                node = row[0]
                title = node.properties.get("title", "Untitled")
                summary = node.properties.get("summary", "")
                line = f"  - {title}"
                if summary:
                    line += f": {summary[:150]}"
                doc_lines.append(line)
            sections.append("RECENT DOCUMENTS:\n" + "\n".join(doc_lines))
    except Exception:  # noqa: S110
        pass

    # Topics
    try:
        cypher, params = topic_tree()
        result = await asyncio.to_thread(graph.query, cypher, params)
        if result.result_set:
            topic_names = [row[0] for row in result.result_set]
            sections.append("TOPICS: " + ", ".join(topic_names))
    except Exception:  # noqa: S110
        pass

    return "\n\n".join(sections) if sections else "Graph is empty."


async def _ask_claude(question: str, graph_context: str, claude_binary: str = "claude") -> str:
    """Send a question to Claude Code headless with graph context.

    Args:
        question: The user's free-form message.
        graph_context: Summary of the graph state.
        claude_binary: Path to the claude CLI binary.

    Returns:
        Claude's response text, or an error message.
    """
    prompt = f"{_CHAT_SYSTEM_PROMPT}\n\n{graph_context}\n\nUSER QUESTION: {question}"

    try:
        result = await asyncio.to_thread(
            subprocess.run,
            [claude_binary, "-p", prompt],
            capture_output=True,
            text=True,
            timeout=_CHAT_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            logger.warning(
                "claude_chat_failed", returncode=result.returncode, stderr=result.stderr[:200]
            )
            return "Sorry, I couldn't process that right now. Try a /search command instead."
        response = result.stdout.strip()
        if not response:
            return "I didn't get a response. Try rephrasing your question."
        return response
    except FileNotFoundError:
        logger.warning("claude_binary_not_found")
        return (
            "Claude Code CLI is not available on this machine. "
            "You can still use commands like /search, /recent, /stats."
        )
    except subprocess.TimeoutExpired:
        logger.warning("claude_chat_timeout", timeout=_CHAT_TIMEOUT_SECONDS)
        return "That took too long. Try a simpler question or use /search."


@router.message()
async def chat_handler(message: Message, graph: Graph, bot: Bot, **_kwargs: object) -> None:
    """Handle any non-command message as a conversational query.

    First checks if the message is a qualification response (e.g. "ok",
    "type paper", "topic science/cs"). If so, delegates to the qualification
    handler. Otherwise sends the message to Claude Code with graph context.

    Args:
        message: Incoming Telegram message.
        graph: FalkorDB graph handle (injected via middleware).
        bot: The aiogram Bot instance (injected by dispatcher).
    """
    if not message.text or message.text.startswith("/"):
        return

    user_text = message.text.strip()
    if not user_text:
        return

    user_id = message.from_user.id if message.from_user else None
    register_chat_id(message.chat.id)
    logger.info("chat_message", text=user_text[:100], user_id=user_id)

    # Check if this is a qualification response before falling through to Claude
    chat_id = message.chat.id
    if is_qualification_response(chat_id, user_text):
        settings: BeestgraphSettings | None = _kwargs.get("settings")
        if settings is not None:
            handled = await handle_qualification_response(message, bot, settings)
            if handled:
                return

    # Send typing indicator while Claude thinks
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Build context from the graph + targeted search results
    graph_context = await _build_graph_context(graph)

    # Also run a search for the user's query to find specifically relevant docs
    try:
        cypher, params = search_documents(user_text, limit=5)
        result = await asyncio.to_thread(graph.query, cypher, params)
        if result.result_set:
            search_lines: list[str] = []
            for row in result.result_set:
                node = row[0]
                title = node.properties.get("title", "Untitled")
                summary = node.properties.get("summary", "")
                content = node.properties.get("content", "")[:500]
                line = f"  - {title}"
                if summary:
                    line += f"\n    Summary: {summary}"
                if content:
                    line += f"\n    Content preview: {content[:300]}"
                search_lines.append(line)
            graph_context += "\n\nSEARCH RESULTS FOR USER QUERY:\n" + "\n".join(search_lines)
    except Exception:  # noqa: S110
        pass  # Search may fail on short queries, that's fine

    # Ask Claude
    # Get claude binary path from settings if available
    settings: BeestgraphSettings | None = _kwargs.get("settings")
    claude_bin = settings.claude_code_binary if settings else "claude"
    response = await _ask_claude(user_text, graph_context, claude_binary=claude_bin)

    # Telegram has a 4096 char limit
    if len(response) > 4000:
        response = response[:3997] + "..."

    await message.answer(response)


# ---------------------------------------------------------------------------
# Middleware — injects graph handle and enforces access control
# ---------------------------------------------------------------------------


class _GraphMiddleware:
    """Outer middleware that injects a FalkorDB graph handle into handler kwargs.

    Also enforces the user allowlist before dispatching to handlers.
    """

    def __init__(
        self,
        graph: Graph,
        allowed_filter: _AllowedUsers,
        settings: BeestgraphSettings,
    ) -> None:
        self._graph = graph
        self._allowed = allowed_filter
        self._settings = settings

    async def __call__(self, handler, event: Message, data: dict) -> object:
        """Intercept messages, check access, and inject *graph* + *settings* into data."""
        if isinstance(event, Message) and not self._allowed(event):
            logger.warning(
                "unauthorized_access",
                user_id=event.from_user.id if event.from_user else None,
            )
            return None  # silently drop
        data["graph"] = self._graph
        data["settings"] = self._settings
        return await handler(event, data)


# ---------------------------------------------------------------------------
# Bot factory
# ---------------------------------------------------------------------------


def create_bot(settings: BeestgraphSettings) -> tuple[Bot, Dispatcher]:
    """Build and configure the aiogram Bot and Dispatcher.

    Args:
        settings: Fully resolved beestgraph settings.

    Returns:
        Tuple of (Bot, Dispatcher) ready for polling.
    """
    if not settings.telegram.bot_token:
        raise ValueError("BEESTGRAPH_TELEGRAM_BOT_TOKEN is required to run the Telegram bot.")

    bot = Bot(token=settings.telegram.bot_token)
    dp = Dispatcher()

    graph = _get_graph(settings.falkordb)
    allowed_filter = _AllowedUsers(settings.telegram.allowed_user_ids)

    middleware = _GraphMiddleware(graph, allowed_filter, settings)
    router.message.outer_middleware(middleware)
    qualification_router.message.outer_middleware(middleware)
    dp.include_router(qualification_router)
    dp.include_router(router)

    logger.info(
        "telegram_bot_created",
        allowed_users=settings.telegram.allowed_user_ids,
        falkordb_host=settings.falkordb.host,
    )
    return bot, dp


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


@click.command("telegram-bot")
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to beestgraph.yml config file.",
)
def main(config_path: Path | None) -> None:
    """Start the beestgraph Telegram bot."""
    settings = load_settings(config_path)
    import logging

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
    )
    bot, dp = create_bot(settings)
    logger.info("telegram_bot_starting")

    async def _run() -> None:
        """Run the bot with the notification poller as a background task."""
        poller_task: asyncio.Task | None = None  # type: ignore[type-arg]
        if settings.qualification.enabled and settings.qualification.notify_telegram:
            poller_task = asyncio.create_task(start_notification_poller(bot, settings))
            logger.info("notification_poller_scheduled")
        try:
            await dp.start_polling(bot)
        finally:
            if poller_task is not None:
                poller_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await poller_task

    asyncio.run(_run())


if __name__ == "__main__":
    main()
