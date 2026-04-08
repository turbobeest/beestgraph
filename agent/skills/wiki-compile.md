# Skill: Wiki Compile

Read raw source material and compile it into richly interlinked wiki pages in the Obsidian vault. This is the core Karpathy pattern: the AI reads sources, writes structured wiki articles, creates entity pages, cross-references everything with `[[wikilinks]]`, and updates the index.

## When to Use

- After new sources are added to `raw/`, `01-inbox/`, or `07-resources/`
- When running `bg ingest --active` or `bg ingest --agent`
- To recompile the entire wiki from scratch
- Periodically to improve cross-linking and fill gaps

## Vault Structure

```
~/vault/
├── raw/                  # Immutable source material (never modify)
├── 07-resources/         # Wiki articles organized by topic
├── entities/             # One page per person/org/tool/concept/place
├── index.md              # Content-oriented catalog (update on every compile)
└── log.md                # Chronological record (append on every compile)
```

## Steps

### 1. Scan for unprocessed sources

Read all `.md` files in `raw/articles/`, `raw/transcripts/`, `raw/pdfs/`, and `01-inbox/`. Also check `07-resources/` for articles that exist but lack cross-references.

### 2. For each source, compile a wiki article

Read the source content. Write a wiki-quality article in `07-resources/{topic}/`:

**Required structure for every wiki article:**

```markdown
---
uid: "{generated}"
title: "{descriptive title}"
type: article
tags: [{relevant tags}]
status: published
dates:
  created: {today}
  captured: {today}
  processed: {now ISO}
  modified: {today}
source:
  type: {manual|keepmd|url|clipper}
  url: "{source URL if available}"
para: resources
topics:
  - {topic/subtopic}
content_stage: literature
summary: "{2-3 sentence summary}"
entities:
  people: [{names mentioned}]
  concepts: [{concepts discussed}]
  organizations: [{orgs mentioned}]
  tools: [{tools/software mentioned}]
key_claims:
  - "{main claim 1}"
  - "{main claim 2}"
connections:
  related: [{related wiki page titles}]
version: 1
---

## Summary

{One paragraph overview with [[wikilinks]] to related concepts.}

## Key Points

- {Point 1} — relates to [[Related Concept]]
- {Point 2} — see also [[Another Topic]]
- {Point 3}

## Details

{Main body content. Use [[wikilinks]] liberally for:
- People: [[Person Name]]
- Concepts: [[Concept Name]]
- Tools: [[Tool Name]]
- Related articles: [[Article Title]]
}

## Source

- [{source title}]({source URL}) — accessed {date}

## Connections

- Related: [[Topic A]], [[Topic B]]
- Supports: [[Claim or article this supports]]
- See also: [[Broader topic]]
```

### 3. Create or update entity pages

For every `[[wikilinked]]` entity that doesn't have a page yet:

**People** → `entities/people/{slug}.md`
**Organizations** → `entities/organizations/{slug}.md`
**Tools** → `entities/tools/{slug}.md`
**Concepts** → `entities/concepts/{slug}.md`
**Places** → `entities/places/{slug}.md`

Each entity page should have:

```markdown
---
uid: "{generated}"
title: "{Entity Name}"
type: {person|organization|tool|concept|place}
tags: []
status: published
...
---

## About

{Brief description of the entity compiled from all mentions.}

## Mentioned In

- [[Article 1]] — {context of mention}
- [[Article 2]] — {context of mention}

## Connections

- [[Related Entity 1]]
- [[Related Entity 2]]
```

If the entity page already exists, **update** the "Mentioned In" section and revise the "About" section to incorporate new information.

### 4. Update index.md

Rewrite `~/vault/index.md` as a content-oriented catalog:

```markdown
# Index

## Technology
### AI & Machine Learning
- [[Article Title]] — {one-line summary}
- [[Another Article]] — {one-line summary}

### Infrastructure
- [[Article Title]] — {one-line summary}

## People
- [[Person Name]] — {role/affiliation}

## Concepts
- [[Concept Name]] — {one-line definition}
```

Group by topic. Include every wiki article and entity page. Sort alphabetically within groups.

### 5. Append to log.md

```
{ISO timestamp} COMPILED {number} articles, {number} entities updated
  Sources processed: {list}
  New pages created: {list}
  Pages updated: {list}
  New cross-references: {count}
```

## Quality Rules

1. **Every wiki article must have at least 3 `[[wikilinks]]`** to other pages
2. **Every entity mentioned must be `[[wikilinked]]`** — create the page if it doesn't exist
3. **Source URLs must be preserved** — never lose provenance
4. **Summaries are mandatory** — both in frontmatter and as the first section
5. **key_claims must be specific and falsifiable** — not vague statements
6. **Never modify files in `raw/`** — those are immutable source material
7. **Prefer updating existing pages** over creating duplicates — search first
