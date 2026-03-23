"""Graphiti (Zep) client for temporal knowledge graph ingestion.

Wraps the Graphiti MCP server's add_episode endpoint. Failures are logged
but never block the primary FalkorDB ingest — Graphiti enrichment is
best-effort.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import structlog

from src.config import GraphitiSettings

logger = structlog.get_logger(__name__)


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
    payload = {
        "name": name,
        "episode_body": content,
        "source_description": source_url or name,
        "source": source_type,
        "reference_time": datetime.now(tz=UTC).isoformat(),
    }

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
