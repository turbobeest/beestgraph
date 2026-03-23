"""beestgraph.graph — Graph database layer for the beestgraph knowledge graph.

Provides schema management, query builders, and maintenance operations
for the FalkorDB-backed knowledge graph.
"""

from __future__ import annotations

__all__ = [
    "ensure_schema",
    "compute_stats",
    "deduplicate_entities",
    "deduplicate_tags",
    "documents_by_source_type",
    "find_hub_documents",
    "find_orphan_documents",
    "find_orphans",
    "find_related_by_tags",
    "get_document_neighborhood",
    "recent_documents",
    "search_documents",
    "topic_tree",
]

from src.graph.maintenance import (
    compute_stats,
    deduplicate_entities,
    deduplicate_tags,
    find_hub_documents,
    find_orphan_documents,
)
from src.graph.queries import (
    documents_by_source_type,
    find_orphans,
    find_related_by_tags,
    get_document_neighborhood,
    recent_documents,
    search_documents,
    topic_tree,
)
from src.graph.schema import ensure_schema
