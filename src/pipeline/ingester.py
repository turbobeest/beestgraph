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

# ---------------------------------------------------------------------------
# Cypher templates (all use MERGE for idempotency)
# ---------------------------------------------------------------------------

_MERGE_DOCUMENT = """
MERGE (d:Document {path: $path})
SET d.title         = $title,
    d.content       = $content,
    d.summary       = $summary,
    d.status        = $status,
    d.para_category = $para_category,
    d.source_type   = $source_type,
    d.source_url    = $source_url,
    d.author        = $author,
    d.created_at    = $created_at,
    d.updated_at    = $updated_at,
    d.processed_at  = $processed_at,
    d.id            = $id,
    d.maturity      = $maturity,
    d.content_type  = $content_type,
    d.visibility    = $visibility,
    d.quality       = $quality,
    d.modified_at   = $modified_at,
    d.published_at  = $published_at,
    d.source_domain = $source_domain
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
        params = {
            "path": doc.path,
            "title": doc.title,
            "content": doc.content,
            "summary": str(meta.get("summary", "")),
            "status": str(meta.get("status", "inbox")),
            "para_category": str(meta.get("para_category", "")),
            "source_type": str(meta.get("source_type", "")),
            "source_url": str(meta.get("source_url", "")),
            "author": str(meta.get("author", "")),
            "created_at": str(meta.get("date_captured", now)),
            "updated_at": now,
            "processed_at": now,
            # New v3 fields
            "id": str(meta.get("id", "")),
            "maturity": str(meta.get("maturity", "raw")),
            "content_type": str(meta.get("content_type", "")),
            "visibility": str(meta.get("visibility", "private")),
            "quality": str(meta.get("quality", "")),
            "modified_at": str(meta.get("modified", now)),
            "published_at": str(meta.get("published", "")),
            "source_domain": str(meta.get("source_domain", "")),
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
        """Create a MENTIONS edge from a document to a Person or Concept.

        Args:
            doc_path: Document vault path.
            entity_name: Display name of the entity.
            entity_type: Either ``"person"`` or ``"concept"``.
            confidence: Extraction confidence score (0.0-1.0).
            context: Short text snippet where the mention was found.
            description: Optional description for Concept entities.

        Raises:
            ValueError: If *entity_type* is not ``person`` or ``concept``.
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
        else:
            raise ValueError(f"entity_type must be 'person' or 'concept', got '{entity_type}'")

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

        # Source URL
        source_url = doc.metadata.get("source_url")
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

        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "document_ingested",
            path=doc.path,
            tags=len(doc.tags),
            topics=len(topics) if isinstance(topics, list) else 0,
            wiki_links=len(doc.wiki_links),
            elapsed_ms=round(elapsed_ms, 1),
        )
