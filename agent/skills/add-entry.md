# Skill: Add Entry

Accept a URL or raw text from the user, create a properly formatted markdown file with YAML frontmatter, and save it to the Obsidian vault inbox for processing.

## When to Use

- When the user wants to save a URL (article, blog post, video, etc.)
- When the user provides raw text or notes to capture
- When the user shares content via the Telegram bot
- When programmatically adding items from keep.md or other sources

## Prerequisites

- Obsidian vault is accessible at `~/vault/`
- Filesystem MCP server is configured in `config/mcp.json`

## Steps

### 1. Determine input type

Evaluate what the user provided:

| Input | Action |
|-------|--------|
| URL only | Fetch page title and content if possible; create stub entry |
| URL + notes | Use notes as content, URL as source |
| Raw text only | Use text as content, no source URL |
| Text + metadata (title, tags) | Use provided metadata directly |

### 2. Extract or infer title

Priority order for title:
1. Explicitly provided title
2. First `# heading` in the content
3. Page title from URL (if fetchable)
4. First 60 characters of content, truncated at word boundary
5. Fallback: `untitled-<timestamp>`

### 3. Generate slug

Convert the title to a URL-safe filename slug:

```
"FalkorDB: A Graph Database for AI" -> "falkordb-a-graph-database-for-ai"
```

Rules:
- Lowercase
- Replace non-alphanumeric characters with hyphens
- Collapse consecutive hyphens
- Strip leading/trailing hyphens
- Maximum 80 characters

### 4. Build minimal frontmatter

Create the YAML frontmatter for an inbox item. Use only fields that are known at capture time:

```yaml
---
title: "FalkorDB: A Graph Database for AI"
source_url: "https://example.com/article"
source_type: manual
date_captured: 2026-03-22T10:30:00Z
status: inbox
tags:
  - user-provided-tag
---
```

Field rules:
- `title`: always required (see step 2)
- `source_url`: include only if a URL was provided
- `source_type`: `manual` for user-provided content, `keepmd` for keep.md imports
- `date_captured`: current UTC timestamp in ISO 8601 format
- `status`: always `inbox` for new entries
- `tags`: include only if the user provided tags; do not auto-generate at this stage

Do NOT include fields that require AI processing (`summary`, `topics`, `entities`, `para_category`). Those are populated by the `process-inbox` skill.

### 5. Compose the markdown file

Structure:

```markdown
---
<frontmatter>
---

<content body>
```

If the user provided notes or text, use that as the content body. If only a URL was provided, include a minimal body:

```markdown
---
<frontmatter>
---

Source: <url>

<!-- Content will be extracted during processing -->
```

### 6. Write to vault inbox

```
Tool: filesystem.write_file
Path: ~/vault/inbox/<slug>.md
Content: <composed markdown>
```

If a file with the same slug already exists, append a short numeric suffix: `<slug>-2.md`, `<slug>-3.md`, etc.

### 7. Optionally create a graph stub

If FalkorDB is available, create a minimal Document node so the entry appears in the timeline immediately:

```cypher
MERGE (d:Document {path: $path})
SET d.title = $title,
    d.source_url = $sourceUrl,
    d.source_type = $sourceType,
    d.status = 'inbox',
    d.created_at = $now,
    d.updated_at = $now
```

This is optional and non-blocking. If FalkorDB is unreachable, skip this step silently.

### 8. Confirm to user

Report back:
- File saved to: `~/vault/inbox/<slug>.md`
- Status: inbox (pending processing)
- Title: `<title>`

## Input Validation

- URLs must be valid HTTP or HTTPS URLs
- Title must not be empty after trimming
- Content must not exceed 500KB (reject with helpful message)
- Tags must be non-empty strings, max 50 characters each, max 20 tags

## Error Handling

- If the vault directory is not writable, report the error clearly
- If file creation fails, do not leave partial files behind
- If the slug generation produces an empty string, use `untitled-<timestamp>`
- Never overwrite an existing file without the numeric suffix strategy

## Example

User input:
```
URL: https://zep.ai/blog/graphiti
Tags: knowledge-graphs, temporal
```

Result file at `~/vault/inbox/graphiti.md`:
```markdown
---
title: "graphiti"
source_url: "https://zep.ai/blog/graphiti"
source_type: manual
date_captured: 2026-03-22T10:30:00Z
status: inbox
tags:
  - knowledge-graphs
  - temporal
---

Source: https://zep.ai/blog/graphiti

<!-- Content will be extracted during processing -->
```
