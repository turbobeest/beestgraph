# Skill: Search Graph

Search the beestgraph knowledge graph using natural language queries. Translate the user's intent into Cypher queries, execute against FalkorDB, and return formatted results.

## When to Use

- When the user asks a question about their saved knowledge
- When looking up documents by topic, tag, person, or concept
- When exploring relationships between entities in the graph
- When retrieving recent or filtered documents

## Prerequisites

- FalkorDB is running (Docker, port 6379)
- The graph `beestgraph` exists with indexed data
- MCP server `falkordb` is configured in `config/mcp.json`

## Steps

### 1. Parse the user query

Analyze the natural language query to determine the intent:

| Intent | Example Query |
|--------|--------------|
| Find by topic | "What do I have about AI?" |
| Find by tag | "Show me everything tagged with rust" |
| Find by person | "Articles mentioning Yann LeCun" |
| Find by concept | "What do I know about knowledge graphs?" |
| Find by source | "What came from Hacker News?" |
| Find recent | "What did I save this week?" |
| Find relationships | "How are RAG and knowledge graphs related?" |
| Full-text search | "Search for transformer architecture" |

### 2. Translate to Cypher

Based on the intent, construct the appropriate Cypher query.

#### Find by topic

```cypher
MATCH (d:Document)-[:BELONGS_TO]->(t:Topic)
WHERE t.name CONTAINS $query
RETURN d.title, d.summary, d.source_url, d.created_at, t.name
ORDER BY d.created_at DESC
LIMIT $limit
```

#### Find by tag

```cypher
MATCH (d:Document)-[:TAGGED_WITH]->(tag:Tag)
WHERE tag.normalized_name = $normalizedQuery
RETURN d.title, d.summary, d.source_url, d.created_at, tag.name
ORDER BY d.created_at DESC
LIMIT $limit
```

#### Find by person

```cypher
MATCH (d:Document)-[m:MENTIONS]->(p:Person)
WHERE p.normalized_name CONTAINS $normalizedQuery
RETURN d.title, d.summary, p.name, m.confidence, m.context
ORDER BY m.confidence DESC
LIMIT $limit
```

#### Find by concept

```cypher
MATCH (d:Document)-[m:MENTIONS]->(c:Concept)
WHERE c.normalized_name CONTAINS $normalizedQuery
RETURN d.title, d.summary, c.name, c.description, m.confidence
ORDER BY m.confidence DESC
LIMIT $limit
```

#### Find by source domain

```cypher
MATCH (d:Document)-[:DERIVED_FROM]->(s:Source)
WHERE s.domain CONTAINS $query OR s.name CONTAINS $query
RETURN d.title, d.summary, s.url, d.created_at
ORDER BY d.created_at DESC
LIMIT $limit
```

#### Find recent (time-based)

```cypher
MATCH (d:Document)
WHERE d.created_at >= $sinceDate
RETURN d.title, d.summary, d.source_type, d.created_at
ORDER BY d.created_at DESC
LIMIT $limit
```

Calculate `$sinceDate` from the query:
- "today" -> start of current day (ISO 8601)
- "this week" -> 7 days ago
- "this month" -> 30 days ago
- "recently" -> 7 days ago

#### Find relationships between concepts

```cypher
MATCH (d1:Document)-[:MENTIONS]->(c1:Concept),
      (d1)-[:MENTIONS]->(c2:Concept)
WHERE c1.normalized_name CONTAINS $concept1
  AND c2.normalized_name CONTAINS $concept2
RETURN d1.title, d1.summary, c1.name, c2.name
LIMIT $limit
```

#### Full-text search

```cypher
CALL db.idx.fulltext.queryNodes('Document', $query)
YIELD node
RETURN node.title, node.summary, node.source_url, node.created_at
LIMIT $limit
```

### 3. Execute the query

Use the FalkorDB MCP server to run the Cypher query:

```
Tool: falkordb.query
Graph: beestgraph
Query: <constructed Cypher>
```

Default limit: 20 results unless the user specifies otherwise.

### 4. Format results

Present results in a clear, readable format:

```
Found N results for "<query>":

1. **Article Title**
   Summary snippet here...
   Topic: technology/ai-ml | Tags: #rag, #llm
   Source: https://example.com | Saved: 2026-03-15

2. **Another Article**
   ...
```

If no results are found, suggest:
- Alternative search terms
- Broader topic categories
- Checking if the data has been ingested

### 5. Offer follow-up actions

After presenting results, suggest relevant follow-ups:

- "Would you like to see the full content of any of these?"
- "Want to explore related topics?"
- "Should I search with different terms?"

## Query Normalization

Before executing queries, normalize input:

- Convert to lowercase for `normalized_name` fields
- Strip leading/trailing whitespace
- Remove special characters for tag matching
- Handle plurals (basic: strip trailing 's')

## Error Handling

- If FalkorDB is unreachable, inform the user and suggest checking Docker status
- If the query returns no results, try a broader full-text search as fallback
- If the Cypher syntax is invalid, log the error and attempt a simpler query
- Never expose raw error messages to the user; provide helpful context

## Performance Notes

- Always include `LIMIT` to prevent unbounded result sets
- Use indexed properties (`path`, `normalized_name`, `status`) in WHERE clauses
- Prefer `CONTAINS` over regex for simple substring matching
- For complex multi-hop queries, consider breaking into multiple simpler queries
