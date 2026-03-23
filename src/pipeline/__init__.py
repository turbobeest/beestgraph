"""beestgraph processing pipeline.

Capture -> parse -> extract -> ingest -> organize.
"""

from __future__ import annotations

__all__ = [
    "ingester",
    "keepmd_poller",
    "markdown_parser",
    "processor",
    "watcher",
]
