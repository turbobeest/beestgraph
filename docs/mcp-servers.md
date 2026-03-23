# MCP servers

beestgraph uses three Model Context Protocol (MCP) servers to give Claude Code access to external tools and data. This document describes each server, its tools, and usage examples.

## Table of contents

- [Overview](#overview)
- [Configuration](#configuration)
- [keep.md server](#keepmd-server)
- [Filesystem server](#filesystem-server)
- [FalkorDB server](#falkordb-server)

---

## Overview

| Server | Transport | Endpoint | Purpose |
|--------|-----------|----------|---------|
| keep.md | HTTP | `https://keep.md/mcp` | Capture inbox intake |
| Filesystem | stdio (local) | N/A | Vault file read/write |
| FalkorDB | stdio (local) | N/A | Direct Cypher queries |

All three servers are configured in `config/mcp.json` and loaded by Claude Code at startup. The processing pipeline uses them in sequence: read from keep.md or filesystem, process with Claude, write to filesystem, ingest into FalkorDB, and query the graph directly.

---

## Configuration

The MCP configuration file is `config/mcp.json`. Copy the template and edit:

```bash
cp config/mcp.json.example config/mcp.json
```

Full configuration:

```json
{
  "mcpServers": {
    "keep": {
      "transport": "http",
      "url": "https://keep.md/mcp"
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/vault"]
    },
    "falkordb": {
      "command": "npx",
      "args": ["-y", "@falkordb/falkordb-mcp-server"],
      "env": {
        "FALKORDB_HOST": "localhost",
        "FALKORDB_PORT": "6379"
      }
    }
  }
}
```

Replace `~/vault` with your actual vault path (e.g., `$HOME/vault` or `/mnt/nvme/vault`).

To apply the configuration to Claude Code's global settings:

```bash
./scripts/configure-mcp.sh
```

---

## keep.md server

**Transport**: HTTP (remote)
**URL**: `https://keep.md/mcp`
**Authentication**: Via keep.md session

The keep.md MCP server provides read/write access to your keep.md inbox and saved items.

### Tools

#### `list_inbox`

List unprocessed items in the inbox.

```
list_inbox()
```

Returns a list of items with ID, title, URL, and creation date. Use this as the starting point for the processing pipeline.

#### `get_item`

Get the full content and metadata for a specific item.

```
get_item(id: "item-id-here")
```

Returns the item's title, URL, full markdown content, source type, and metadata. This is what the AI agent reads to extract entities and categorize.

#### `mark_done`

Mark an item as processed (removes it from the inbox).

```
mark_done(id: "item-id-here")
```

Called after the item has been successfully written to the vault and ingested into the graph.

#### `search_items`

Search across all saved items.

```
search_items(query: "knowledge graphs")
```

Useful for finding previously saved items related to a topic.

#### `save_item`

Save a new item to keep.md.

```
save_item(url: "https://example.com/article", title: "Article Title")
```

#### `update_item`

Update an existing item's metadata or content.

```
update_item(id: "item-id-here", title: "Updated Title")
```

#### `add_source`

Add a new content source (RSS feed, etc.).

```
add_source(type: "rss", url: "https://example.com/feed.xml")
```

#### `remove_source`

Remove a content source.

```
remove_source(id: "source-id-here")
```

#### `list_sources`

List all configured content sources.

```
list_sources()
```

#### `get_stats`

Get statistics about your inbox and sources.

```
get_stats()
```

#### `whoami`

Get information about the current authenticated user.

```
whoami()
```

#### `list_items`

List all items with optional filters.

```
list_items(status: "done", limit: 50)
```

---

## Filesystem server

**Transport**: stdio (local process)
**Package**: `@modelcontextprotocol/server-filesystem`

The Filesystem MCP server provides sandboxed read/write access to the Obsidian vault directory. It only allows access to the path specified in the configuration.

### Tools

#### `read_file`

Read the contents of a file in the vault.

```
read_file(path: "inbox/2026-03-22-article-title.md")
```

Paths are relative to the vault root. Returns the full file contents including frontmatter.

#### `write_file`

Write content to a file in the vault. Creates parent directories if needed.

```
write_file(
  path: "knowledge/technology/ai-ml/knowledge-graphs-overview.md",
  content: "---\ntitle: Knowledge Graphs Overview\n---\n\nArticle content..."
)
```

Used by the pipeline to write processed documents to their final location in the vault.

#### `list_directory`

List files and subdirectories in a vault directory.

```
list_directory(path: "inbox")
```

Returns file and directory names in the specified path.

#### `search_files`

Search for files matching a pattern.

```
search_files(pattern: "*.md", path: "knowledge/technology")
```

Returns file paths matching the glob pattern within the specified directory.

---

## FalkorDB server

**Transport**: stdio (local process)
**Package**: `@falkordb/falkordb-mcp-server`
**Requires**: FalkorDB running on localhost:6379

The FalkorDB MCP server provides direct access to the graph database. It supports both natural language queries (translated to Cypher) and raw Cypher queries.

### Usage

The FalkorDB MCP server accepts natural language questions and translates them to Cypher queries against the `beestgraph` graph. It also supports raw Cypher for precise queries.

### Example queries

Natural language:

```
"How many documents are in the graph?"
"Show me all documents tagged with 'ai-ml'"
"What topics have the most documents?"
"Find people mentioned in more than 3 documents"
```

These are translated internally to Cypher queries like:

```cypher
MATCH (d:Document) RETURN COUNT(d) AS document_count

MATCH (d:Document)-[:TAGGED_WITH]->(t:Tag {normalized_name: "ai-ml"})
RETURN d.title, d.path

MATCH (d:Document)-[:BELONGS_TO]->(t:Topic)
RETURN t.name, COUNT(d) AS doc_count
ORDER BY doc_count DESC

MATCH (d:Document)-[:MENTIONS]->(p:Person)
WITH p, COUNT(d) AS mentions
WHERE mentions > 3
RETURN p.name, mentions
ORDER BY mentions DESC
```

### When to use which server

| Task | Server |
|------|--------|
| Read/write vault files | Filesystem |
| Read keep.md inbox | keep.md |
| Ingest content into the graph | FalkorDB |
| Run specific Cypher queries | FalkorDB |
| Get graph statistics | FalkorDB |
| Natural language graph exploration | FalkorDB |
