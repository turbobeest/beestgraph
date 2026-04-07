"""FalkorDB ingester — writes parsed documents into the knowledge graph.

Every write uses ``MERGE`` for idempotency so reprocessing a document is always
safe.  The five-phase pipeline extends basic ingestion (Phase 1) with entity
page updates, contradiction detection, synthesis, and navigation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
from falkordb import FalkorDB

from src.config import FalkorDBSettings
from src.pipeline.markdown_parser import ParsedDocument
from src.pipeline.zettelkasten import generate_id, generate_slug

logger = structlog.get_logger(__name__)


@dataclass
class PhaseResult:
    """Result from a single ingest phase."""

    phase: int
    success: bool = True
    items: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class IngestResult:
    """Aggregated result from the multi-phase ingest pipeline."""

    phase1: PhaseResult | None = None
    phase2: PhaseResult | None = None
    phase3: PhaseResult | None = None
    phase4: PhaseResult | None = None
    phase5: PhaseResult | None = None

    @property
    def entities_updated(self) -> int:
        return len(self.phase2.items) if self.phase2 else 0

    @property
    def contradictions_flagged(self) -> int:
        return len(self.phase3.items) if self.phase3 else 0

    @property
    def synthesis_created(self) -> bool:
        return bool(self.phase4 and self.phase4.items)


# Entity type → vault subdirectory mapping
_ENTITY_TYPE_MAP = {
    "people": ("person", "people"),
    "organizations": ("organization", "organizations"),
    "tools": ("tool", "tools"),
    "concepts": ("concept", "concepts"),
    "places": ("place", "places"),
}

_QUALITY_TO_CONFIDENCE = {"low": 0.3, "medium": 0.5, "high": 0.85}
_MATURITY_TO_STAGE = {"raw": "fleeting", "permanent": "evergreen"}


def _to_confidence(value: object) -> float:
    """Convert a confidence value to float, handling legacy quality strings."""
    if isinstance(value, (int, float)):
        return float(value)
    return _QUALITY_TO_CONFIDENCE.get(str(value).lower(), 0.5)


def _to_content_stage(value: object) -> str:
    """Convert a content_stage or legacy maturity value to new spec values."""
    s = str(value).lower()
    return _MATURITY_TO_STAGE.get(s, s)


# ---------------------------------------------------------------------------
# Cypher templates (all use MERGE for idempotency)
# ---------------------------------------------------------------------------

_MERGE_DOCUMENT_BY_UID = """
MERGE (d:Document {uid: $uid})
ON CREATE SET d.path            = $path,
              d.created_at      = $created
ON MATCH  SET d.path            = $path,
              d.updated_at      = $processed
SET d.title             = $title,
    d.content           = $content,
    d.summary           = $summary,
    d.status            = $status,
    d.para              = $para,
    d.source_type       = $source_type,
    d.source_url        = $source_url,
    d.author            = $author,
    d.type              = $type,
    d.content_stage     = $content_stage,
    d.importance        = $importance,
    d.confidence        = $confidence,
    d.engagement_status = $engagement_status,
    d.created           = $created,
    d.processed         = $processed,
    d.modified          = $modified,
    d.published         = $published,
    d.captured          = $captured
RETURN d.path AS path
"""

_MERGE_DOCUMENT_BY_PATH = """
MERGE (d:Document {path: $path})
SET d.title             = $title,
    d.content           = $content,
    d.summary           = $summary,
    d.status            = $status,
    d.para              = $para,
    d.source_type       = $source_type,
    d.source_url        = $source_url,
    d.author            = $author,
    d.uid               = $uid,
    d.type              = $type,
    d.content_stage     = $content_stage,
    d.importance        = $importance,
    d.confidence        = $confidence,
    d.engagement_status = $engagement_status,
    d.created           = $created,
    d.processed         = $processed,
    d.modified          = $modified,
    d.published         = $published,
    d.captured          = $captured
RETURN d.path AS path
"""

_MERGE_TAG = """
MERGE (t:Tag {normalized_name: $normalized_name})
SET t.name = $name
RETURN t.normalized_name AS normalized_name
"""

_MERGE_TOPIC = """
MERGE (tp:Topic {name: $name})
SET tp.level = $level
RETURN tp.name AS name
"""

_MERGE_DOC_TAG_REL = """
MERGE (d:Document {path: $doc_path})
MERGE (t:Tag {normalized_name: $tag_normalized})
MERGE (d)-[:TAGGED_WITH]->(t)
"""

_MERGE_DOC_TOPIC_REL = """
MERGE (d:Document {path: $doc_path})
MERGE (tp:Topic {name: $topic_name})
MERGE (d)-[:BELONGS_TO]->(tp)
"""

_MERGE_DOC_LINK_REL = """
MERGE (a:Document {path: $from_path})
MERGE (b:Document {path: $to_path})
MERGE (a)-[:LINKS_TO]->(b)
"""

_MERGE_PERSON = """
MERGE (p:Person {normalized_name: $normalized_name})
SET p.name = $name
RETURN p.normalized_name AS normalized_name
"""

_MERGE_CONCEPT = """
MERGE (c:Concept {normalized_name: $normalized_name})
SET c.name = $name, c.description = $description
RETURN c.normalized_name AS normalized_name
"""

_MERGE_DOC_MENTIONS_PERSON = """
MERGE (d:Document {path: $doc_path})
MERGE (p:Person {normalized_name: $normalized_name})
MERGE (d)-[r:MENTIONS]->(p)
SET r.confidence = $confidence, r.context = $context
"""

_MERGE_DOC_MENTIONS_CONCEPT = """
MERGE (d:Document {path: $doc_path})
MERGE (c:Concept {normalized_name: $normalized_name})
MERGE (d)-[r:MENTIONS]->(c)
SET r.confidence = $confidence, r.context = $context
"""

_MERGE_SOURCE = """
MERGE (s:Source {url: $url})
SET s.domain = $domain, s.name = $name
RETURN s.url AS url
"""

_MERGE_DOC_SOURCE_REL = """
MERGE (d:Document {path: $doc_path})
MERGE (s:Source {url: $source_url})
MERGE (d)-[:DERIVED_FROM]->(s)
"""

_MERGE_ORGANIZATION = """
MERGE (o:Organization {normalized_name: $normalized_name})
SET o.name = $name
RETURN o.normalized_name AS normalized_name
"""

_MERGE_TOOL = """
MERGE (tl:Tool {normalized_name: $normalized_name})
SET tl.name = $name, tl.url = $url
RETURN tl.normalized_name AS normalized_name
"""

_MERGE_PLACE = """
MERGE (pl:Place {normalized_name: $normalized_name})
SET pl.name = $name
RETURN pl.normalized_name AS normalized_name
"""

_MERGE_DOC_MENTIONS_ORGANIZATION = """
MERGE (d:Document {path: $doc_path})
MERGE (o:Organization {normalized_name: $normalized_name})
MERGE (d)-[r:MENTIONS]->(o)
SET r.confidence = $confidence, r.context = $context
"""

_MERGE_DOC_MENTIONS_TOOL = """
MERGE (d:Document {path: $doc_path})
MERGE (tl:Tool {normalized_name: $normalized_name})
MERGE (d)-[r:MENTIONS]->(tl)
SET r.confidence = $confidence, r.context = $context
"""

_MERGE_DOC_MENTIONS_PLACE = """
MERGE (d:Document {path: $doc_path})
MERGE (pl:Place {normalized_name: $normalized_name})
MERGE (d)-[r:MENTIONS]->(pl)
SET r.confidence = $confidence, r.context = $context
"""

_MERGE_DOC_EXTENDS = """
MERGE (a:Document {path: $from_path})
MERGE (b:Document {path: $to_path})
MERGE (a)-[:EXTENDS]->(b)
"""

_MERGE_DOC_INSPIRED_BY = """
MERGE (a:Document {path: $from_path})
MERGE (b:Document {path: $to_path})
MERGE (a)-[:INSPIRED_BY]->(b)
"""

_MERGE_DOC_RELATED_TO = """
MERGE (a:Document {path: $from_path})
MERGE (b:Document {path: $to_path})
MERGE (a)-[r:RELATED_TO]->(b)
SET r.weight = $weight
"""

_MERGE_DOC_SUPPORTS = """
MERGE (a:Document {path: $from_path})
MERGE (b:Document {path: $to_path})
MERGE (a)-[r:SUPPORTS]->(b)
SET r.weight = $weight
"""

_MERGE_DOC_CONTRADICTS = """
MERGE (a:Document {path: $from_path})
MERGE (b:Document {path: $to_path})
MERGE (a)-[r:CONTRADICTS]->(b)
SET r.weight = $weight
"""

_MERGE_DOC_SUPERSEDES = """
MERGE (a:Document {path: $from_path})
MERGE (b:Document {path: $to_path})
MERGE (a)-[:SUPERSEDES]->(b)
"""

_MERGE_DOC_CHILD_OF = """
MERGE (a:Document {path: $from_path})
MERGE (b:Document {path: $to_path})
MERGE (a)-[:CHILD_OF]->(b)
"""


class GraphIngester:
    """Manages a FalkorDB connection and exposes idempotent upsert methods.

    Args:
        settings: FalkorDB connection settings.
    """

    def __init__(
        self,
        settings: FalkorDBSettings,
    ) -> None:
        self._settings = settings
        self._db: FalkorDB | None = None

    # -- connection helpers --------------------------------------------------

    def _connect(self) -> FalkorDB:
        """Return a connected FalkorDB client, creating one if needed."""
        if self._db is None:
            self._db = FalkorDB(
                host=self._settings.host,
                port=self._settings.port,
                password=self._settings.password or None,
            )
            logger.info(
                "falkordb_connected",
                host=self._settings.host,
                port=self._settings.port,
            )
        return self._db

    def _graph(self):
        """Return the named graph handle."""
        return self._connect().select_graph(self._settings.graph_name)

    # -- public upsert methods -----------------------------------------------

    def upsert_document(self, doc: ParsedDocument) -> str:
        """Create or update a Document node from a parsed document.

        Args:
            doc: The parsed markdown document.

        Returns:
            The vault-relative path used as the node key.
        """
        now = datetime.now(tz=UTC).isoformat()
        meta = doc.metadata
        dates = meta.get("dates", {}) if isinstance(meta.get("dates"), dict) else {}
        source = meta.get("source", {}) if isinstance(meta.get("source"), dict) else {}
        params = {
            "path": doc.path,
            "title": doc.title,
            "content": doc.content,
            "summary": str(meta.get("summary", "")),
            "status": str(meta.get("status", "inbox")),
            "para": str(meta.get("para", meta.get("para_category", ""))),
            "source_type": str(meta.get("source_type", source.get("type", ""))),
            "source_url": str(meta.get("source_url", source.get("url", ""))),
            "author": str(meta.get("author", source.get("author", ""))),
            "uid": str(meta.get("uid", meta.get("id", ""))),
            "type": str(meta.get("type", meta.get("content_type", ""))),
            "content_stage": _to_content_stage(
                meta.get("content_stage", meta.get("maturity", "fleeting"))
            ),
            "importance": meta.get("importance", 3),
            "confidence": _to_confidence(meta.get("confidence", meta.get("quality", 0.5))),
            "engagement_status": str(meta.get("engagement_status", "unread")),
            "created": str(dates.get("created", meta.get("created_at", now))),
            "processed": now,
            "modified": str(dates.get("modified", meta.get("modified_at", now))),
            "published": str(dates.get("published", meta.get("published_at", ""))),
            "captured": str(dates.get("captured", meta.get("date_captured", now))),
        }
        if params["uid"]:
            self._graph().query(_MERGE_DOCUMENT_BY_UID, params)
        else:
            logger.warning(
                "legacy_document_no_uid",
                path=doc.path,
                msg="Document has no uid — falling back to MERGE on path. "
                "Add a uid field to this document's frontmatter.",
            )
            self._graph().query(_MERGE_DOCUMENT_BY_PATH, params)
        logger.debug("upserted_document", path=doc.path, uid=params["uid"] or "(none)")
        return doc.path

    def upsert_tag(self, name: str) -> str:
        """Create or update a Tag node.

        Args:
            name: Human-readable tag name.

        Returns:
            The normalized tag name used as the node key.
        """
        normalized = name.strip().lower()
        self._graph().query(_MERGE_TAG, {"name": name, "normalized_name": normalized})
        return normalized

    def upsert_topic(self, name: str, level: int = 0) -> str:
        """Create or update a Topic node.

        Args:
            name: Topic name (e.g. ``technology/ai-ml``).
            level: Depth in the topic hierarchy (0 = root).

        Returns:
            The topic name used as the node key.
        """
        self._graph().query(_MERGE_TOPIC, {"name": name, "level": level})
        return name

    def create_link(self, from_path: str, to_path: str) -> None:
        """Ensure a LINKS_TO relationship exists between two documents.

        Args:
            from_path: Source document vault path.
            to_path: Target document vault path.
        """
        self._graph().query(_MERGE_DOC_LINK_REL, {"from_path": from_path, "to_path": to_path})

    def create_mention(
        self,
        doc_path: str,
        entity_name: str,
        entity_type: str,
        confidence: float = 1.0,
        context: str = "",
        description: str = "",
    ) -> None:
        """Create a MENTIONS edge from a document to an entity node.

        Args:
            doc_path: Document vault path.
            entity_name: Display name of the entity.
            entity_type: One of ``"person"``, ``"concept"``, ``"organization"``,
                ``"tool"``, or ``"place"``.
            confidence: Extraction confidence score (0.0-1.0).
            context: Short text snippet where the mention was found.
            description: Optional description for Concept entities.

        Raises:
            ValueError: If *entity_type* is not a recognized entity type.
        """
        normalized = entity_name.strip().lower()
        params = {
            "doc_path": doc_path,
            "name": entity_name,
            "normalized_name": normalized,
            "confidence": confidence,
            "context": context,
        }

        if entity_type == "person":
            self._graph().query(_MERGE_PERSON, {"name": entity_name, "normalized_name": normalized})
            self._graph().query(_MERGE_DOC_MENTIONS_PERSON, params)
        elif entity_type == "concept":
            self._graph().query(
                _MERGE_CONCEPT,
                {"name": entity_name, "normalized_name": normalized, "description": description},
            )
            self._graph().query(_MERGE_DOC_MENTIONS_CONCEPT, params)
        elif entity_type == "organization":
            self._graph().query(
                _MERGE_ORGANIZATION, {"name": entity_name, "normalized_name": normalized}
            )
            self._graph().query(_MERGE_DOC_MENTIONS_ORGANIZATION, params)
        elif entity_type == "tool":
            self._graph().query(
                _MERGE_TOOL, {"name": entity_name, "normalized_name": normalized, "url": ""}
            )
            self._graph().query(_MERGE_DOC_MENTIONS_TOOL, params)
        elif entity_type == "place":
            self._graph().query(
                _MERGE_PLACE, {"name": entity_name, "normalized_name": normalized}
            )
            self._graph().query(_MERGE_DOC_MENTIONS_PLACE, params)
        else:
            raise ValueError(
                f"entity_type must be 'person', 'concept', 'organization', 'tool', or 'place', "
                f"got '{entity_type}'"
            )

    def _upsert_source(self, url: str) -> None:
        """Create or update a Source node and link it to a document.

        Args:
            url: The source URL.
        """
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc or url
        self._graph().query(_MERGE_SOURCE, {"url": url, "domain": domain, "name": domain})

    # -- high-level ingest ---------------------------------------------------

    def ingest_parsed_document(self, doc: ParsedDocument) -> None:
        """Write the full subgraph for a single parsed document.

        Upserts the Document node, all tags, topics, wiki-link edges, source
        node, and any entities present in the frontmatter.

        Args:
            doc: A fully parsed markdown document.
        """
        start = time.monotonic()

        self.upsert_document(doc)

        # Tags
        for tag in doc.tags:
            self.upsert_tag(tag)
            self._graph().query(
                _MERGE_DOC_TAG_REL,
                {"doc_path": doc.path, "tag_normalized": tag.strip().lower()},
            )

        # Topics from frontmatter
        topics = doc.metadata.get("topics", [])
        if isinstance(topics, list):
            for topic in topics:
                topic_str = str(topic)
                level = topic_str.count("/")
                self.upsert_topic(topic_str, level=level)
                self._graph().query(
                    _MERGE_DOC_TOPIC_REL,
                    {"doc_path": doc.path, "topic_name": topic_str},
                )

        # Wiki-link edges (target docs get placeholder nodes via MERGE)
        for link_target in doc.wiki_links:
            target_path = f"{link_target}.md"
            self.create_link(doc.path, target_path)

        # Source URL (check both flat and nested frontmatter)
        source_nested = doc.metadata.get("source", {})
        if isinstance(source_nested, dict):
            source_url = source_nested.get("url", "") or doc.metadata.get("source_url", "")
        else:
            source_url = doc.metadata.get("source_url", "")
        if isinstance(source_url, str) and source_url:
            self._upsert_source(source_url)
            self._graph().query(
                _MERGE_DOC_SOURCE_REL,
                {"doc_path": doc.path, "source_url": source_url},
            )

        # Entities from frontmatter
        entities = doc.metadata.get("entities", {})
        if isinstance(entities, dict):
            for person in entities.get("people", []) or []:
                self.create_mention(doc.path, str(person), "person")
            for concept in entities.get("concepts", []) or []:
                self.create_mention(doc.path, str(concept), "concept")
            for org in entities.get("organizations", []) or []:
                self.create_mention(doc.path, str(org), "organization")
            for tool in entities.get("tools", []) or []:
                self.create_mention(doc.path, str(tool), "tool")
            for place in entities.get("places", []) or []:
                self.create_mention(doc.path, str(place), "place")

        # Connections from frontmatter (connections.* nested fields)
        connections = doc.metadata.get("connections", {})
        if isinstance(connections, dict):
            rel_map = {
                "supports": (_MERGE_DOC_SUPPORTS, True),
                "contradicts": (_MERGE_DOC_CONTRADICTS, True),
                "extends": (_MERGE_DOC_EXTENDS, False),
                "supersedes": (_MERGE_DOC_SUPERSEDES, False),
                "inspired_by": (_MERGE_DOC_INSPIRED_BY, False),
                "related": (_MERGE_DOC_RELATED_TO, True),
            }
            for rel_key, (template, has_weight) in rel_map.items():
                targets = connections.get(rel_key, [])
                if isinstance(targets, list):
                    for target in targets:
                        t = str(target)
                        target_path = t if t.endswith(".md") else f"{t}.md"
                        params = {"from_path": doc.path, "to_path": target_path}
                        if has_weight:
                            params["weight"] = 1.0
                        self._graph().query(template, params)

        # CHILD_OF from up field
        up_targets = doc.metadata.get("up", [])
        if isinstance(up_targets, str):
            up_targets = [up_targets]
        if isinstance(up_targets, list):
            for parent in up_targets:
                parent_path = f"{parent}.md" if not str(parent).endswith(".md") else str(parent)
                self._graph().query(
                    _MERGE_DOC_CHILD_OF,
                    {"from_path": doc.path, "to_path": parent_path},
                )

        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "document_ingested",
            path=doc.path,
            tags=len(doc.tags),
            topics=len(topics) if isinstance(topics, list) else 0,
            wiki_links=len(doc.wiki_links),
            elapsed_ms=round(elapsed_ms, 1),
        )

    # -- five-phase pipeline ---------------------------------------------------

    def ingest(
        self,
        doc: ParsedDocument,
        vault_path: str | Path | None = None,
        agent: Any | None = None,
        phases: list[int] | None = None,
    ) -> IngestResult:
        """Run the multi-phase ingest pipeline.

        Args:
            doc: Parsed document to ingest.
            vault_path: Vault root path (needed for phases 2-5).
            agent: Optional LLMAgent for enhanced processing.
            phases: Which phases to run (default: [1] only).

        Returns:
            IngestResult with per-phase outcomes.
        """
        if phases is None:
            phases = [1]

        vault = Path(vault_path) if vault_path else Path.home() / "vault"
        result = IngestResult()

        if 1 in phases:
            result.phase1 = self._phase1_upsert_document(doc)

        if 2 in phases:
            result.phase2 = self._phase2_update_entities(doc, vault, agent)

        if 3 in phases:
            result.phase3 = self._phase3_detect_contradictions(doc, vault, agent)

        if 4 in phases and agent:
            result.phase4 = self._phase4_synthesize(doc, vault, agent)

        if 5 in phases:
            result.phase5 = self._phase5_update_navigation(doc, vault, result)

        return result

    def _phase1_upsert_document(self, doc: ParsedDocument) -> PhaseResult:
        """Phase 1: Create/update document node and subgraph (existing behavior)."""
        try:
            self.ingest_parsed_document(doc)
            return PhaseResult(phase=1, success=True, items=[doc.path])
        except Exception as exc:
            logger.error("phase1_failed", path=doc.path, error=str(exc))
            return PhaseResult(phase=1, success=False, error=str(exc))

    def _phase2_update_entities(
        self, doc: ParsedDocument, vault: Path, agent: Any | None,
    ) -> PhaseResult:
        """Phase 2: Create/update entity pages in the vault."""
        entities = doc.metadata.get("entities", {})
        if not isinstance(entities, dict):
            return PhaseResult(phase=2, items=[])

        updated: list[str] = []
        now_iso = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        summary = str(doc.metadata.get("summary", ""))[:100]

        for category, (entity_type, subdir) in _ENTITY_TYPE_MAP.items():
            names = entities.get(category, [])
            if not isinstance(names, list):
                continue
            for name in names:
                name = str(name).strip()
                if not name:
                    continue

                slug = generate_slug(name)
                entity_dir = vault / "entities" / subdir
                entity_dir.mkdir(parents=True, exist_ok=True)
                entity_path = entity_dir / f"{slug}.md"

                if not entity_path.exists():
                    # Create from template or minimal frontmatter
                    self._create_entity_page(entity_path, name, entity_type, now_iso)

                # Append mention reference
                mention_line = (
                    f"- [[{doc.title}]] ({now_iso})"
                    f"{' — ' + summary if summary else ''}\n"
                )

                if agent:
                    self._agent_rewrite_entity(
                        entity_path, name, doc, agent,
                    )
                else:
                    self._append_mention(entity_path, mention_line)

                updated.append(f"{subdir}/{slug}")

        return PhaseResult(phase=2, items=updated)

    def _create_entity_page(
        self, path: Path, name: str, entity_type: str, date: str,
    ) -> None:
        """Create a new entity page with minimal frontmatter."""
        uid = generate_id()
        content = f"""---
uid: "{uid}"
title: "{name}"
type: {entity_type}
tags: []
status: published
dates:
  created: {date}
  captured: {date}
  processed: null
  modified: {date}
source:
  type: auto
para: resources
version: 1
---

## About

## Mentioned In

"""
        path.write_text(content, encoding="utf-8")
        logger.info("entity_page_created", path=str(path), entity=name)

    def _append_mention(self, entity_path: Path, mention_line: str) -> None:
        """Append a mention to an entity page's Mentioned In section."""
        content = entity_path.read_text(encoding="utf-8")
        # Check if this mention is already present (idempotent)
        if mention_line.strip() in content:
            return
        if "## Mentioned In" in content:
            content = content.replace(
                "## Mentioned In\n", f"## Mentioned In\n{mention_line}", 1,
            )
        else:
            content += f"\n## Mentioned In\n{mention_line}"
        entity_path.write_text(content, encoding="utf-8")

    def _agent_rewrite_entity(
        self, entity_path: Path, name: str, doc: ParsedDocument, agent: Any,
    ) -> None:
        """Use the agent to rewrite an entity page with full context."""
        try:
            # Query for all docs mentioning this entity
            normalized = name.strip().lower()
            result = self._graph().query(
                "MATCH (d:Document)-[:MENTIONS]->(e {normalized_name: $name}) "
                "RETURN d.title, d.summary, d.created "
                "ORDER BY d.created DESC LIMIT 20",
                {"name": normalized},
            )
            mentions = [
                f"- {row[0]} ({row[2]}): {row[1]}"
                for row in (result.result_set or [])
            ]

            existing = entity_path.read_text(encoding="utf-8")
            context = (
                f"New document: {doc.title}\n"
                f"Summary: {doc.metadata.get('summary', '')}\n\n"
                f"All mentions:\n" + "\n".join(mentions)
            )
            rewritten = agent.rewrite(
                existing=existing,
                context=context,
                prompt=(
                    f"Update this entity page for '{name}' incorporating "
                    f"the new document and all known mentions. "
                    f"Preserve the YAML frontmatter exactly. "
                    f"Only update the markdown body sections."
                ),
            )
            if rewritten and len(rewritten) > 50:
                entity_path.write_text(rewritten, encoding="utf-8")
                logger.info("entity_page_rewritten", path=str(entity_path))
        except Exception as exc:
            logger.warning("agent_rewrite_failed", entity=name, error=str(exc))
            # Fall back to simple append
            now_iso = datetime.now(tz=UTC).strftime("%Y-%m-%d")
            summary = str(doc.metadata.get("summary", ""))[:100]
            mention = f"- [[{doc.title}]] ({now_iso}) — {summary}\n"
            self._append_mention(entity_path, mention)

    def _phase3_detect_contradictions(
        self, doc: ParsedDocument, vault: Path, agent: Any | None,
    ) -> PhaseResult:
        """Phase 3: Detect contradiction candidates via key_claims index."""
        claims = doc.metadata.get("key_claims", [])
        if not isinstance(claims, list) or not claims:
            return PhaseResult(phase=3, items=[])

        flagged: list[str] = []
        review_path = vault / "00-meta" / "contradictions-review.md"
        review_path.parent.mkdir(parents=True, exist_ok=True)

        for claim_text in claims:
            claim_text = str(claim_text).strip()
            if not claim_text:
                continue

            try:
                result = self._graph().query(
                    "CALL db.idx.fulltext.queryNodes('Document', $claim) "
                    "YIELD node, score "
                    "WHERE score > 0.5 AND node.path <> $path "
                    "RETURN node.title, node.path, node.key_claims, score "
                    "ORDER BY score DESC LIMIT 5",
                    {"claim": claim_text, "path": doc.path},
                )
            except Exception as exc:
                logger.warning("contradiction_query_failed", error=str(exc))
                continue

            for row in result.result_set or []:
                match_title = row[0] or "(untitled)"
                match_path = row[1] or ""
                score = row[3] if len(row) > 3 else 0

                if agent:
                    self._agent_evaluate_contradiction(
                        doc, match_path, claim_text, agent,
                    )
                else:
                    entry = (
                        f"| {doc.title} | {match_title} "
                        f"| {claim_text[:80]} | {score:.2f} |\n"
                    )
                    self._append_to_review(review_path, entry)

                flagged.append(f"{doc.title} ↔ {match_title}")

        return PhaseResult(phase=3, items=flagged)

    def _append_to_review(self, review_path: Path, entry: str) -> None:
        """Append a contradiction candidate to the review file."""
        if not review_path.exists():
            header = (
                "# Contradiction Review\n\n"
                "| New Document | Conflicting Document | Claim | Score |\n"
                "|---|---|---|---|\n"
            )
            review_path.write_text(header, encoding="utf-8")
        with review_path.open("a", encoding="utf-8") as f:
            f.write(entry)

    def _agent_evaluate_contradiction(
        self, doc: ParsedDocument, match_path: str, claim: str, agent: Any,
    ) -> None:
        """Use agent to evaluate if a contradiction is genuine."""
        try:
            synthesis = agent.synthesize(
                documents=[
                    f"Document 1: {doc.title}\nClaim: {claim}",
                    f"Document 2: {match_path}",
                ],
                prompt=(
                    "Evaluate whether these two documents genuinely contradict "
                    "each other on this claim. Return 'CONTRADICTION' or "
                    "'NOT A CONTRADICTION' followed by a brief explanation."
                ),
            )
            if "CONTRADICTION" in synthesis.upper() and "NOT" not in synthesis.upper()[:20]:
                self._graph().query(
                    _MERGE_DOC_CONTRADICTS,
                    {"from_path": doc.path, "to_path": match_path, "weight": 1.0},
                )
                logger.info(
                    "contradiction_detected",
                    from_doc=doc.path, to_doc=match_path, claim=claim[:80],
                )
        except Exception as exc:
            logger.warning("agent_contradiction_eval_failed", error=str(exc))

    def _phase4_synthesize(
        self, doc: ParsedDocument, vault: Path, agent: Any,
    ) -> PhaseResult:
        """Phase 4: Agent-only synthesis of cross-document patterns."""
        uid = str(doc.metadata.get("uid", ""))
        try:
            result = self._graph().query(
                "MATCH (d:Document)-[:TAGGED_WITH]->(t:Tag)"
                "<-[:TAGGED_WITH]-(other:Document) "
                "WHERE d.uid = $uid AND other.uid <> $uid "
                "RETURN other.title, other.summary, other.path, "
                "count(t) AS shared "
                "ORDER BY shared DESC LIMIT 5",
                {"uid": uid},
            )
        except Exception as exc:
            logger.warning("phase4_query_failed", error=str(exc))
            return PhaseResult(phase=4, items=[], error=str(exc))

        related = result.result_set or []
        if not related:
            return PhaseResult(phase=4, items=[])

        doc_summaries = [
            f"- {row[0]}: {row[1]}" for row in related
        ]
        prompt = (
            "Identify any unnamed patterns or novel connections between "
            "these documents that would justify a new synthesis note. "
            "If you find one, return a complete markdown document with "
            "frontmatter (type: synthesis). If not, return 'NO_SYNTHESIS'."
        )
        try:
            synthesis_text = agent.synthesize(
                documents=[
                    f"New: {doc.title}\n{doc.metadata.get('summary', '')}",
                    *doc_summaries,
                ],
                prompt=prompt,
            )
        except Exception as exc:
            logger.warning("phase4_synthesis_failed", error=str(exc))
            return PhaseResult(phase=4, items=[], error=str(exc))

        if "NO_SYNTHESIS" in synthesis_text:
            return PhaseResult(phase=4, items=[])

        # Write synthesis to vault and queue for review
        synthesis_dir = vault / "synthesis"
        synthesis_dir.mkdir(parents=True, exist_ok=True)
        slug = generate_slug(doc.title)
        synth_path = synthesis_dir / f"synthesis-{slug}.md"
        synth_path.write_text(synthesis_text, encoding="utf-8")

        # Route through qualification queue
        try:
            from src.pipeline.qualification import QualificationQueue

            queue = QualificationQueue(
                vault_path=vault,
                queue_dir="02-queue",
            )
            queue.add_item(synth_path, {"type": "synthesis", "topic": "", "tags": []})
        except Exception as exc:
            logger.warning("synthesis_queue_failed", error=str(exc))

        return PhaseResult(phase=4, items=[str(synth_path)])

    def _phase5_update_navigation(
        self, doc: ParsedDocument, vault: Path, result: IngestResult,
    ) -> PhaseResult:
        """Phase 5: Update index.md and log.md."""
        updated: list[str] = []
        now = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        summary = str(doc.metadata.get("summary", ""))[:80]
        topics = doc.metadata.get("topics", [])
        topic_str = topics[0] if isinstance(topics, list) and topics else "general"

        # Update index.md
        index_path = vault / "index.md"
        if index_path.exists():
            index_line = f"- [[{doc.title}]] — {summary}\n"
            content = index_path.read_text(encoding="utf-8")
            if doc.title not in content:
                # Try to find topic section, else append
                section_header = f"## {topic_str}"
                if section_header in content:
                    content = content.replace(
                        section_header + "\n",
                        section_header + "\n" + index_line,
                        1,
                    )
                else:
                    content += f"\n{section_header}\n{index_line}"
                index_path.write_text(content, encoding="utf-8")
                updated.append("index.md")

        # Update log.md
        log_path = vault / "log.md"
        if log_path.exists():
            log_entry = (
                f"{now} INGESTED {doc.title}\n"
                f"  entities updated: {result.entities_updated}\n"
                f"  contradictions: {result.contradictions_flagged}\n"
                f"  synthesis: "
                f"{'created' if result.synthesis_created else 'skipped'}\n\n"
            )
            with log_path.open("a", encoding="utf-8") as f:
                f.write(log_entry)
            updated.append("log.md")

        return PhaseResult(phase=5, items=updated)
