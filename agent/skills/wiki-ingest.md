# Skill: Wiki Ingest

Ingest a single URL or file into the knowledge base. Fetch the content, save the raw source, compile a wiki article, create entity pages, update cross-references, and update the index. This is the single-source version of wiki-compile.

## When to Use

- `bg ingest <url> --agent`
- When someone shares a link worth capturing
- When you want to add a specific article to the knowledge base

## Steps

### 1. Fetch and save the raw source

If the input is a URL:
- Fetch the page content (use WebFetch or agent-browser)
- Save the raw content to `raw/articles/{slug}.md` with frontmatter:

```markdown
---
title: "{page title}"
source_url: "{original URL}"
date_fetched: {ISO timestamp}
---

{full article text, converted to markdown}
```

If the input is a local file:
- Copy it to `raw/articles/{slug}.md` (preserving the original)

**Never modify the raw file after saving it.** It's an immutable record.

### 2. Compile the wiki article

Read the raw source. Write a wiki article following the wiki-compile template in `07-resources/{topic}/{slug}.md`.

Requirements:
- Descriptive title (not just the URL)
- Full frontmatter with all Tier 1 fields
- Summary paragraph
- Key points with `[[wikilinks]]`
- Source citation with URL
- `key_claims` extracted from the content
- `entities` extracted from the content

### 3. Create/update entity pages

For every person, organization, tool, concept, or place mentioned:
- Check if an entity page exists in `entities/{type}/{slug}.md`
- If not, create it with the wiki-compile entity template
- If yes, update the "Mentioned In" section

### 4. Cross-reference existing wiki pages

Search existing wiki articles for topics related to the new article:
- Add `[[wikilinks]]` from the new article to existing relevant pages
- Add a "See also" reference in existing pages that are strongly related
- Update `connections.related` in frontmatter of both pages

### 5. Update index.md and log.md

- Add the new article to the appropriate section in `index.md`
- Append an INGESTED entry to `log.md`

### 6. Ingest into FalkorDB

Run the beestgraph pipeline to create graph nodes:

```bash
bg ingest {path-to-wiki-article} --active
```

## Example

Input: `bg ingest https://example.com/knowledge-graphs-2026 --agent`

Output:
```
Saved raw source: raw/articles/knowledge-graphs-2026.md
Compiled wiki article: 07-resources/technology/ai-ml/knowledge-graphs-2026.md
Created entity pages:
  - entities/concepts/knowledge-graph.md
  - entities/tools/neo4j.md (updated Mentioned In)
  - entities/people/tim-berners-lee.md (updated Mentioned In)
Cross-referenced with:
  - [[Introduction to Knowledge Graphs]] (added mutual link)
  - [[FalkorDB Python Tutorial]] (added see-also)
Updated: index.md, log.md
Ingested into FalkorDB: 1 document, 3 entities, 2 cross-references
```
