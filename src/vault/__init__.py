"""Vault filesystem management for beestgraph.

Provides utilities for maintaining the Obsidian vault directory structure,
moving processed documents to their proper locations, and querying vault state.
"""

from __future__ import annotations

from src.vault.manager import (
    ensure_vault_structure,
    get_vault_stats,
    list_inbox,
    move_to_knowledge,
    resolve_destination,
)

__all__ = [
    "ensure_vault_structure",
    "get_vault_stats",
    "list_inbox",
    "move_to_knowledge",
    "resolve_destination",
]
