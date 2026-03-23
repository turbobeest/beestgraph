# Graph schema

Reference documentation for the beestgraph knowledge graph schema in FalkorDB.

Graph name: `beestgraph`

## Table of contents

- [Node types](#node-types)
- [Relationship types](#relationship-types)
- [Indexes](#indexes)
- [Query examples](#query-examples)
- [Conventions](#conventions)

---

## Node types

### Document

The central node type. Every captured and processed piece of content becomes a Document.

```cypher
(:Document {
  path: STRING,           -- vault path relative to root (e.g., "knowledge/technology/ai-ml/article.md")
  title: STRING,
  content: STRING,        -- full markdown body (for full-text search)
  summary: STRING,        -- AI-generated 2-3 sentence summary
  status: STRING,         -- inbox | processing | published | archived
  para_category: STRING,  -- projects | areas | resources | archives
  source_type: STRING,    -- keepmd | obsidian_clipper | manual
  source_url: STRING,
  created_at: STRING,     -- ISO 8601 (e.g., "2026-03-22T10:30:00Z")
  updated_at: STRING,
  processed_at: STRING
})
```

Create a Document:

```cypher
MERGE (d:Document {path: "knowledge/technology/ai-ml/knowledge-graphs-overview.md"})
SET d.title = "Knowledge Graphs Overview",
    d.summary = "An introduction to knowledge graph architectures and their applications in personal knowledge management.",
    d.status = "published",
    d.para_category = "resources",
    d.source_type = "keepmd",
    d.source_url = "https://example.com/knowledge-graphs",
    d.created_at = "2026-03-22T10:30:00Z",
    d.updated_at = "2026-03-22T10:30:00Z",
    d.processed_at = "2026-03-22T10:45:00Z"
```

### Tag

Flat labels for categorizing documents. Tags use `normalized_name` for deduplication.

```cypher
(:Tag {
  name: STRING,             -- display name (e.g., "Knowledge Graphs")
  normalized_name: STRING   -- lowercase, stripped (e.g., "knowledge graphs")
})
```

Create a Tag and link it:

```cypher
MERGE (t:Tag {normalized_name: "knowledge graphs"})
SET t.name = "Knowledge Graphs"

MATCH (d:Document {path: "knowledge/technology/ai-ml/knowledge-graphs-overview.md"})
MERGE (d)-[:TAGGED_WITH]->(t)
```

### Topic

Hierarchical categories from the taxonomy. Topics have levels indicating depth (0 = root, 1 = subtopic, etc.).

```cypher
(:Topic {
  name: STRING,   -- topic name using path-style (e.g., "technology/ai-ml")
  level: INT      -- depth in taxonomy tree (0 = top-level)
})
```

Create a Topic hierarchy:

```cypher
MERGE (tech:Topic {name: "technology"})
SET tech.level = 0

MERGE (aiml:Topic {name: "technology/ai-ml"})
SET aiml.level = 1

MERGE (aiml)-[:SUBTOPIC_OF]->(tech)
```

### Person

Named individuals mentioned in documents.

```cypher
(:Person {
  name: STRING,             -- display name (e.g., "Geoffrey Hinton")
  normalized_name: STRING   -- lowercase, stripped (e.g., "geoffrey hinton")
})
```

Create a Person and link:

```cypher
MERGE (p:Person {normalized_name: "geoffrey hinton"})
SET p.name = "Geoffrey Hinton"

MATCH (d:Document {path: "knowledge/technology/ai-ml/knowledge-graphs-overview.md"})
MERGE (d)-[:MENTIONS {confidence: 0.95, context: "Referenced as pioneer of deep learning"}]->(p)
```

### Concept

Abstract ideas, techniques, or terms extracted from documents.

```cypher
(:Concept {
  name: STRING,             -- display name (e.g., "Graph Neural Networks")
  normalized_name: STRING,  -- lowercase, stripped
  description: STRING       -- brief definition
})
```

Create a Concept:

```cypher
MERGE (c:Concept {normalized_name: "graph neural networks"})
SET c.name = "Graph Neural Networks",
    c.description = "Neural network architectures designed to operate on graph-structured data"

MATCH (d:Document {path: "knowledge/technology/ai-ml/knowledge-graphs-overview.md"})
MERGE (d)-[:MENTIONS {confidence: 0.88, context: "Discussed as method for graph embedding"}]->(c)
```

### Source

Origin websites or platforms where content was captured from.

```cypher
(:Source {
  url: STRING,      -- full URL (e.g., "https://example.com/article")
  domain: STRING,   -- domain only (e.g., "example.com")
  name: STRING      -- display name (e.g., "Example Blog")
})
```

Create a Source:

```cypher
MERGE (s:Source {url: "https://example.com/knowledge-graphs"})
SET s.domain = "example.com",
    s.name = "Example Blog"

MATCH (d:Document {path: "knowledge/technology/ai-ml/knowledge-graphs-overview.md"})
MERGE (d)-[:DERIVED_FROM]->(s)
```

### Project

Active projects tracked in the PARA system.

```cypher
(:Project {
  name: STRING,         -- project name
  status: STRING,       -- active | paused | completed | archived
  description: STRING   -- brief description
})
```

Create a Project:

```cypher
MERGE (p:Project {name: "beestgraph"})
SET p.status = "active",
    p.description = "AI-augmented personal knowledge graph on Raspberry Pi 5"
```

---

## Relationship types

### Document-to-Document

| Relationship | Description |
|-------------|-------------|
| `LINKS_TO` | Wiki-style link between documents |
| `SUPPORTS` | This document provides evidence for the target |
| `CONTRADICTS` | This document disagrees with the target |
| `SUPERSEDES` | This document replaces the target (newer version) |

```cypher
-- Link two documents
MATCH (a:Document {path: "knowledge/technology/ai-ml/article-a.md"})
MATCH (b:Document {path: "knowledge/technology/ai-ml/article-b.md"})
MERGE (a)-[:LINKS_TO]->(b)

-- Mark a document as superseding another
MERGE (a)-[:SUPERSEDES]->(b)
```

### Document-to-Entity

| Relationship | Properties | Description |
|-------------|-----------|-------------|
| `TAGGED_WITH` | (none) | Document has this tag |
| `BELONGS_TO` | (none) | Document is categorized under this topic |
| `MENTIONS` | `confidence: FLOAT, context: STRING` | Document references this person or concept |
| `DERIVED_FROM` | (none) | Document was captured from this source |

```cypher
-- Tag a document
MATCH (d:Document {path: "knowledge/technology/ai-ml/article.md"})
MERGE (t:Tag {normalized_name: "falkordb"})
SET t.name = "FalkorDB"
MERGE (d)-[:TAGGED_WITH]->(t)

-- Categorize under a topic
MATCH (d:Document {path: "knowledge/technology/ai-ml/article.md"})
MATCH (tp:Topic {name: "technology/ai-ml"})
MERGE (d)-[:BELONGS_TO]->(tp)

-- Mention with confidence
MATCH (d:Document {path: "knowledge/technology/ai-ml/article.md"})
MERGE (c:Concept {normalized_name: "vector similarity"})
SET c.name = "Vector Similarity"
MERGE (d)-[:MENTIONS {confidence: 0.82, context: "Used for semantic search over embeddings"}]->(c)
```

### Topic-to-Topic

| Relationship | Description |
|-------------|-------------|
| `SUBTOPIC_OF` | Child topic belongs to parent topic |

```cypher
MATCH (child:Topic {name: "technology/programming"})
MATCH (parent:Topic {name: "technology"})
MERGE (child)-[:SUBTOPIC_OF]->(parent)
```

---

## Indexes

These indexes are created by `scripts/init-schema.sh` (or `make init-schema`):

```cypher
-- Property indexes for fast lookups
CREATE INDEX FOR (d:Document) ON (d.path)
CREATE INDEX FOR (d:Document) ON (d.source_url)
CREATE INDEX FOR (d:Document) ON (d.status)
CREATE INDEX FOR (t:Tag) ON (t.normalized_name)
CREATE INDEX FOR (tp:Topic) ON (tp.name)
CREATE INDEX FOR (p:Person) ON (p.normalized_name)
CREATE INDEX FOR (c:Concept) ON (c.normalized_name)

-- Full-text search index
CALL db.idx.fulltext.createNodeIndex('Document', 'title', 'content', 'summary')
```

---

## Query examples

### Find all documents about a topic

```cypher
MATCH (d:Document)-[:BELONGS_TO]->(t:Topic {name: "technology/ai-ml"})
RETURN d.title, d.summary, d.source_url
ORDER BY d.created_at DESC
```

### Find documents mentioning a person

```cypher
MATCH (d:Document)-[m:MENTIONS]->(p:Person {normalized_name: "geoffrey hinton"})
WHERE m.confidence > 0.8
RETURN d.title, m.context, m.confidence
ORDER BY m.confidence DESC
```

### Full-text search

```cypher
CALL db.idx.fulltext.queryNodes('Document', 'knowledge graph raspberry pi')
YIELD node, score
RETURN node.title, node.summary, score
ORDER BY score DESC
LIMIT 10
```

### Find related documents (shared tags)

```cypher
MATCH (d:Document {path: "knowledge/technology/ai-ml/article.md"})-[:TAGGED_WITH]->(t:Tag)<-[:TAGGED_WITH]-(related:Document)
WHERE d <> related
RETURN related.title, related.path, COUNT(t) AS shared_tags
ORDER BY shared_tags DESC
LIMIT 10
```

### Get the full topic tree

```cypher
MATCH (child:Topic)-[:SUBTOPIC_OF]->(parent:Topic)
RETURN parent.name AS parent, child.name AS child, child.level
ORDER BY parent.name, child.name
```

### Find unprocessed inbox items

```cypher
MATCH (d:Document {status: "inbox"})
RETURN d.path, d.title, d.created_at
ORDER BY d.created_at ASC
```

### Count entities by type

```cypher
MATCH (n)
WHERE n:Document OR n:Tag OR n:Topic OR n:Person OR n:Concept OR n:Source OR n:Project
RETURN labels(n)[0] AS type, COUNT(n) AS count
ORDER BY count DESC
```

### Find contradicting documents

```cypher
MATCH (a:Document)-[:CONTRADICTS]->(b:Document)
RETURN a.title AS document, b.title AS contradicts
```

---

## Conventions

- **Idempotency**: All writes use `MERGE`, not `CREATE`. Processing the same document twice produces no duplicates.
- **Normalization**: Tags, Person, and Concept nodes store a `normalized_name` field computed as `lower(strip(name))`. Always match on `normalized_name`.
- **Provenance**: Every Document preserves `source_url` and `source_type`. Never lose where content came from.
- **Temporal tracking**: Use Graphiti's `add_episode` for ingestion. It handles temporal fact management automatically on top of the FalkorDB graph.
- **Status lifecycle**: Documents follow the lifecycle `inbox` -> `processing` -> `published` -> `archived`.
