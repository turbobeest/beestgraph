"""FalkorDB ingester — writes parsed documents into the knowledge graph.

Every write uses ``MERGE`` for idempotency so reprocessing a document is always
safe.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import structlog
from falkordb import FalkorDB

from src.config import FalkorDBSettings
from src.pipeline.markdown_parser import ParsedDocument

logger = structlog.get_logger(__name__)

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

_MERGE_DOCUMENT = """
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
        self._graph().query(_MERGE_DOCUMENT, params)
        logger.debug("upserted_document", path=doc.path)
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
                        target_path = f"{target}.md" if not str(target).endswith(".md") else str(target)
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
