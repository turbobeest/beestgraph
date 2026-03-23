"""Graphiti (Zep) client for temporal knowledge graph ingestion.

Wraps the Graphiti MCP server's add_episode endpoint. Failures are logged
but never block the primary FalkorDB ingest — Graphiti enrichment is
best-effort.

Provides both async (``add_episode``) and sync (``add_episode_sync``) variants.
The sync version uses ``httpx.Client`` and is safe to call from a running event
loop without triggering ``asyncio.run()`` errors.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import structlog

from src.config import GraphitiSettings

logger = structlog.get_logger(__name__)


def _build_payload(
    name: str,
    content: str,
    source_url: str,
    source_type: str,
) -> dict[str, str]:
    """Build the JSON payload for a Graphiti add_episode request.

    Args:
        name: Episode name (typically the document title).
        content: Full text content of the document.
        source_url: Original source URL for provenance.
        source_type: Type of source (text, url, etc.).

    Returns:
        Dict suitable for JSON serialisation.
    """
    return {
        "name": name,
        "episode_body": content,
        "source_description": source_url or name,
        "source": source_type,
        "reference_time": datetime.now(tz=UTC).isoformat(),
    }


async def add_episode(
    settings: GraphitiSettings,
    *,
    name: str,
    content: str,
    source_url: str = "",
    source_type: str = "text",
) -> bool:
    """Send a document to Graphiti as an episode for temporal fact tracking.

    Args:
        settings: Graphiti connection settings.
        name: Episode name (typically the document title).
        content: Full text content of the document.
        source_url: Original source URL for provenance.
        source_type: Type of source (text, url, etc.).

    Returns:
        True if the episode was added successfully, False otherwise.
    """
    payload = _build_payload(name, content, source_url, source_type)

    try:
        async with httpx.AsyncClient(timeout=settings.timeout_seconds) as client:
            resp = await client.post(
                f"{settings.url}/api/v1/episodes",
                json=payload,
            )
            resp.raise_for_status()
            logger.info("graphiti_episode_added", name=name)
            return True
    except httpx.ConnectError:
        logger.warning("graphiti_unreachable", url=settings.url)
        return False
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "graphiti_episode_failed",
            name=name,
            status=exc.response.status_code,
            detail=exc.response.text[:200],
        )
        return False
    except httpx.TimeoutException:
        logger.warning("graphiti_timeout", name=name, timeout=settings.timeout_seconds)
        return False


def add_episode_sync(
    settings: GraphitiSettings,
    *,
    name: str,
    content: str,
    source_url: str = "",
    source_type: str = "text",
) -> bool:
    """Synchronous version of :func:`add_episode`.

    Uses ``httpx.Client`` so it is safe to call from code that may already be
    inside an ``asyncio`` event loop (e.g. the keep.md poller calling the
    sync ingester).

    Args:
        settings: Graphiti connection settings.
        name: Episode name (typically the document title).
        content: Full text content of the document.
        source_url: Original source URL for provenance.
        source_type: Type of source (text, url, etc.).

    Returns:
        True if the episode was added successfully, False otherwise.
    """
    payload = _build_payload(name, content, source_url, source_type)

    try:
        with httpx.Client(timeout=settings.timeout_seconds) as client:
            resp = client.post(
                f"{settings.url}/api/v1/episodes",
                json=payload,
            )
            resp.raise_for_status()
            logger.info("graphiti_episode_added", name=name)
            return True
    except httpx.ConnectError:
        logger.warning("graphiti_unreachable", url=settings.url)
        return False
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "graphiti_episode_failed",
            name=name,
            status=exc.response.status_code,
            detail=exc.response.text[:200],
        )
        return False
    except httpx.TimeoutException:
        logger.warning("graphiti_timeout", name=name, timeout=settings.timeout_seconds)
        return False
