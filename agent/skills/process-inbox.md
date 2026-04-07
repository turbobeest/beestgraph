# Skill: Process Inbox

Process unread items from the Obsidian vault inbox directory. For each item, extract metadata, categorize by topic, generate a summary, ingest into the knowledge graph, and move the file to its proper vault location.

## When to Use

- When new files appear in `~/vault/inbox/`
- When the vault watchdog triggers processing
- When manually invoked to clear the inbox backlog

## Prerequisites

- FalkorDB is running (Docker, port 6379)
- MCP servers are configured in `config/mcp.json`
- The Obsidian vault is mounted at `~/vault/`

## Steps

### 1. List inbox files

Use the Filesystem MCP server to list files in the inbox:

```
Tool: filesystem.list_directory
Path: ~/vault/inbox/
```

If the inbox is empty, log "No items to process" and exit.

### 2. For each file in the inbox

#### 2a. Read the file

```
Tool: filesystem.read_file
Path: ~/vault/inbox/<filename>
```

#### 2b. Parse existing frontmatter

If the file already has YAML frontmatter (between `---` delimiters), parse it to extract any pre-existing metadata such as `source_url`, `source_type`, `title`, `author`, `tags`.

If no frontmatter exists, treat the entire file as content.

#### 2c. Extract entities

Apply the entity extraction prompt template from `agent/prompts/extract-entities.md`.

Input: the document content (body text, excluding frontmatter).

Expected output: structured list of people, concepts, and organizations.

#### 2d. Categorize by topic

Apply the categorization prompt template from `agent/prompts/categorize.md`.

Input: the document title and content.

Expected output: a topic path from the taxonomy (e.g., `technology/ai-ml`).

#### 2e. Generate summary

Apply the summarization prompt template from `agent/prompts/summarize.md`.

Input: the document content.

Expected output: a 2-3 sentence summary.

#### 2f. Build complete frontmatter

Construct the full YAML frontmatter block using the template from `CONTEXT.md`. Merge any pre-existing frontmatter values with newly extracted ones. Set:

- `date_processed`: current ISO 8601 timestamp
- `status`: `published`
- `para_category`: infer from topic (default `resources`)
- `topics`: result from step 2d
- `tags`: merge existing tags with any extracted from content
- `entities`: result from step 2c
- `summary`: result from step 2e

#### 2g. Determine destination path

Based on the topic and PARA category:

- `resources` -> `~/vault/knowledge/<topic>/`
- `projects` -> `~/vault/projects/`
- `areas` -> `~/vault/areas/`
- `archives` -> `~/vault/archives/`

Filename: slugified title with `.md` extension.

#### 2h. Write processed file

```
Tool: filesystem.write_file
Path: ~/vault/knowledge/<topic>/<slug>.md
Content: frontmatter + processed body
```

#### 2i. Ingest into knowledge graph

Ingest the document into FalkorDB by creating nodes and relationships:

1. **MERGE Document node** with all properties from frontmatter
2. **MERGE Tag nodes** and create `TAGGED_WITH` relationships
3. **MERGE Topic nodes** and create `BELONGS_TO` relationships
4. **MERGE Person/Concept nodes** and create `MENTIONS` relationships with confidence scores
5. **MERGE Source node** (if `source_url` exists) and create `DERIVED_FROM` relationship

All graph writes MUST use `MERGE`, never `CREATE`, to ensure idempotency.

#### 2j. Remove or archive the inbox file

```
Tool: filesystem.write_file
Path: ~/vault/inbox/<filename>
```

Delete the original inbox file (or move to a `.processed/` subdirectory if archival is preferred).

### 3. Log results

For each processed item, log:

- Item filename
- Source type
- Processing duration
- Number of entities extracted
- Topic assigned
- Destination path
- Graph nodes created/updated

## Error Handling

- If entity extraction fails, continue with empty entities. Do not block processing.
- If categorization fails, default to `resources` category and `meta/uncategorized` topic.
- If graph ingestion fails, still write the processed file to the vault. Log the error and mark for retry.
- If file write fails, do NOT mark the inbox item as processed. Leave it for retry.
- Never lose data. If any step fails, the original inbox file must remain intact.

## Example Log Output

```
[2026-03-22T10:30:00Z] Processing inbox: 3 items found
[2026-03-22T10:30:01Z] Processing: falkordb-introduction.md
  Source: keepmd | Duration: 2.3s
  Entities: 2 people, 3 concepts, 1 org
  Topic: technology/infrastructure
  Destination: ~/vault/knowledge/technology/falkordb-introduction.md
  Graph: 1 Document, 3 Tags, 1 Topic, 6 relationships
[2026-03-22T10:30:03Z] Processing complete: 3/3 succeeded
```
