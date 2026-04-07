# beestgraph: The Universal Template

> Canonical specification for knowledge documents in beestgraph
>
> **Version:** Final (supersedes v1 four-template system and v2 universal template)
> **Status:** Authoritative — this is the single source of truth for the template
> **Last updated:** April 2026

---

## What this document is

This is the complete, final specification for the markdown frontmatter template used by every document in a beestgraph vault. It replaces and consolidates four prior documents:

- The original v1 four-template system (`article.md`, `concept.md`, `project.md`, `person.md`)
- The v2 `universal.md` YAML file
- The v2 `beestgraph-universal-template.md` design document
- The Unified PKM Frontmatter Schema (practitioner-tested specification)
- The research synthesis document that reconciled all of the above

Where those documents disagreed, this spec resolves the disagreements explicitly. Where they agreed, this spec adopts the consensus. Where none of them addressed a concern that surfaced during the merge, this spec makes a decision and explains the reasoning.

If you are an AI agent reading this document during a beestgraph processing session: this is your authoritative reference. The frontmatter rules in this document override any conflicting guidance you may find in older documentation.

If you are a human setting up a vault: read sections 1–4 for the philosophy, jump to section 11 for the complete template, and use sections 12–18 as reference.

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [The Tier System](#2-the-tier-system)
3. [The Minimum Viable Document](#3-the-minimum-viable-document)
4. [Canonical Format: Nested YAML with Flat Export](#4-canonical-format-nested-yaml-with-flat-export)
5. [Tier 1: Universal Fields](#5-tier-1-universal-fields)
6. [Tier 2: Type-Conditional Fields](#6-tier-2-type-conditional-fields)
7. [Tier 3: Advanced Fields](#7-tier-3-advanced-fields)
8. [The Type Registry](#8-the-type-registry)
9. [The Temporal Model](#9-the-temporal-model)
10. [The Inline Wikilink Mirroring Rule](#10-the-inline-wikilink-mirroring-rule)
11. [The Complete Template](#11-the-complete-template)
12. [FalkorDB Mapping](#12-falkordb-mapping)
13. [3D Visualization Mapping](#13-3d-visualization-mapping)
14. [Dataview Query Patterns](#14-dataview-query-patterns)
15. [Agent Instructions](#15-agent-instructions)
16. [Migration from v1 and v2](#16-migration-from-v1-and-v2)
17. [Anti-Patterns](#17-anti-patterns)
18. [Complete Field Reference](#18-complete-field-reference)
19. [Appendix: Worked Examples](#19-appendix-worked-examples)

---

## 1. Design Principles

Five principles govern every decision in this specification. When extending or modifying the template in the future, these principles take precedence over field-level conventions.

### Principle 1: Tiered, not flat

Fields are organized into three tiers by how universally they apply, not by topical category. Tier 1 fields appear on every document. Tier 2 fields appear when the document type warrants them. Tier 3 fields appear only when there is a demonstrated, recurring need. This prevents the "blank field proliferation" problem that kills flat schemas: when every document carries every possible field, the unused ones become metadata debt within months.

### Principle 2: Frontmatter for structure, body for prose

The frontmatter is the machine-readable layer that feeds FalkorDB, Dataview queries, and 3D visualization. The body is freeform markdown for human reading. There are no prescribed H2 sections in the body — write whatever makes sense for that specific piece of knowledge. The single exception is the auto-generated "Connections" section at the end of the body, which mirrors frontmatter relationship fields as inline wikilinks (see Section 10).

### Principle 3: Every field must justify its existence

Each field either feeds a graph node or edge, drives a visualization property, enables a query pattern, or preserves irreplaceable context. No decorative metadata. If you cannot point to a Dataview query, a Cypher pattern, a 3D rendering rule, or a workflow that uses a field, it does not belong in the template.

### Principle 4: Graceful degradation

The minimum viable document is three lines of frontmatter plus a body. Every other field is optional and can be enriched later by an AI agent or by manual editing. A document with only `title` and `type` is valid. A document with all 40+ fields populated is also valid. The agent treats missing fields as "not yet known" rather than "not applicable."

### Principle 5: Tool-agnostic at the edges, opinionated at the core

The canonical format is nested YAML because nesting communicates structure programmatically and reads cleanly in plain text. But the ecosystem of PKM tools (Obsidian Properties UI, Notion import, Tana, Logseq) handles flat key-value pairs more reliably than nested objects. So the spec defines a standard flattening convention (Section 4) and the ingester handles both formats. Internal storage is nested. External export is flat-kebab. The vault is portable in either direction.

---

## 2. The Tier System

The tier system is the most important structural decision in this spec. It is borrowed from the Unified PKM Frontmatter Schema, which evolved it from field reports across vaults of 1,000–10,000+ notes. The pattern is empirically grounded: practitioners who started with flat schemas added complexity over time and abandoned it; practitioners who started with tiered schemas added fields incrementally and kept them.

### Tier 1: Universal (every document)

Eight fields that appear on every document in the vault. They are the minimum viable frontmatter, the universal contract, and the fields you can rely on in any query without checking for existence. All Tier 1 fields are auto-populated by templates or by the ingester — the human never needs to type them.

### Tier 2: Type-conditional (template-driven)

Fields that appear only on documents of specific types. A `person` document has `aliases` and `role`; an `article` document has `source.url` and `source.author`; a `meeting` document has `dates.event_date` and `attendees`. The `type` field (Tier 1) acts as the master key that determines which Tier 2 fields are relevant. Templates include only the Tier 2 fields appropriate to their type, preventing blank field proliferation.

### Tier 3: Advanced (add when earned)

Fields that exist in the spec but should only be populated when there is a demonstrated, recurring need. Examples: `dates.reviewed` for evergreen notes that warrant maintenance, `confidence` for research vaults, `location.*` for travel notes. The agent does not populate Tier 3 fields by default — they are added by humans or by specialized agent workflows when the need arises.

### How the tiers map to agent behavior

- **Tier 1**: The agent must populate every Tier 1 field on every document. Failure to do so is a processing error.
- **Tier 2**: The agent populates Tier 2 fields when the document type warrants them, using the type registry (Section 8) as the lookup table.
- **Tier 3**: The agent populates Tier 3 fields only when explicitly instructed (e.g., by a thinking-tool command that needs `confidence`) or when the source content makes the need obvious (e.g., a travel article naturally yields `location.*`).

---

## 3. The Minimum Viable Document

The absolute minimum a human needs to create:

```markdown
---
title: "Quick thought about X"
type: note
---
The content goes here.
```

The agent expands this on first processing to:

```markdown
---
uid: "202604061430"
title: "Quick thought about X"
type: note
tags: [meta-pkm]
status: published
dates:
  created: 2026-04-06
  captured: 2026-04-06
  processed: 2026-04-06T14:31:00Z
  modified: 2026-04-06
---
The content goes here.

## Connections

(none identified)
```

That is eight Tier 1 fields populated from a two-field input. Everything else is added later by the agent or by the human as the document earns more metadata.

---

## 4. Canonical Format: Nested YAML with Flat Export

### The canonical format is nested

```yaml
source:
  url: "https://example.com/article"
  author: "Jane Doe"
  publisher: "Example Publishing"
```

Nested YAML is the canonical format because it groups related fields, communicates structure to readers, and maps cleanly to programmatic access (`doc['source']['url']` in Python, `frontmatter.source.url` in TypeScript). The ingester reads and writes nested YAML by default. FalkorDB stores the flattened equivalent internally because graph databases do not support nested properties, but the markdown file itself uses nesting.

### The flat-export format

For tools that handle flat key-value pairs better than nested objects (Obsidian Properties UI, Notion import, Tana import), the spec defines a standard flattening convention:

```yaml
source-url: "https://example.com/article"
source-author: "Jane Doe"
source-publisher: "Example Publishing"
```

The flattening rule is: replace `.` nesting with `-` and use kebab-case throughout. This matches the convention used by the Unified PKM Frontmatter Schema and the Obsidian community more broadly.

### The flattening table

| Nested (canonical) | Flat-export |
|---|---|
| `source.url` | `source-url` |
| `source.author` | `source-author` |
| `dates.created` | `date-created` |
| `dates.captured` | `date-captured` |
| `dates.published` | `date-published` |
| `dates.processed` | `date-processed` |
| `dates.modified` | `date-modified` |
| `dates.reviewed` | `date-reviewed` |
| `dates.event_date` | `event-date` |
| `entities.people` | `entities-people` |
| `entities.concepts` | `entities-concepts` |
| `connections.supports` | `connections-supports` |
| `connections.contradicts` | `connections-contradicts` |
| `engagement.status` | `engagement-status` |
| `engagement.rating` | `engagement-rating` |
| `location.lat` | `location-lat` |
| `location.lon` | `location-lon` |

Note that some flat-export field names match conventions established by the Unified PKM Schema (`date-captured`, `event-date`) rather than mechanical transformations (`dates-captured`). When the Unified PKM Schema has an established name for a field, the flat-export uses that name.

### Ingester behavior

The pipeline ingester (`src/pipeline/markdown_parser.py`) accepts both nested and flat-export formats on input. When the ingester writes a document back to the vault, it always writes the canonical nested format. To export a vault to a flat-format-preferring tool, run `bg export --flat <output-dir>` which produces a copy of the vault with all frontmatter flattened.

---

## 5. Tier 1: Universal Fields

These eight fields appear on every document in the vault. The agent must populate all of them on every document it processes. They are auto-populated by templates and the ingester — the human creating a document never needs to type any of them except `title` and `type`.

### `uid` (text)

A timestamp-based unique identifier in `YYYYMMDDHHMM` format. Generated by the ingester at first processing time. This decouples document identity from filename and path — files can be renamed or moved without breaking external references (scripts, API integrations, citations, AI agent state).

```yaml
uid: "202604061430"
```

The UID is immutable after creation. If a document is moved or renamed, the UID stays the same. The ingester uses the UID as the primary key in FalkorDB so that path changes do not create duplicate nodes.

### `title` (text)

The human-readable title of the document. This is the only Tier 1 field a human typically types when creating a document manually. If the document is created from an inbox capture, the agent extracts the title from the source content during processing.

```yaml
title: "Building Knowledge Graphs from Markdown"
```

Do not store the filename here — Obsidian's `file.name` and FalkorDB's `path` property already serve that role. The `title` is the *display* title, which may differ from the filename.

### `type` (text)

The document type. This is the master key that determines which Tier 2 fields apply. The full registry of valid types is in Section 8. The default is `note` if no type is specified.

```yaml
type: article
```

The agent assigns the type during processing based on content analysis. Humans creating documents manually should set the type explicitly when they know it; otherwise the agent will infer it on first processing.

### `tags` (list)

A flat folksonomy of topical tags. Lowercase, hyphenated, no hierarchy. Two to five tags per document is the practical sweet spot — more than five and the tags lose discriminating power. Tags are for *topics*, not for type or status (those have their own fields).

```yaml
tags:
  - knowledge-graphs
  - falkordb
  - raspberry-pi
```

Obsidian indexes the `tags` key as a reserved property. Use array notation, not space-separated strings. Do not encode the document type in tags (`evergreen`, `literature`) — that goes in `type` and `content_stage`.

### `status` (text)

The lifecycle status of the document. Five values, but only four are commonly seen in mature vaults — `processing` is a transient machine state.

| Value | Meaning |
|---|---|
| `inbox` | New, unprocessed (in the inbox folder or just captured by keep.md) |
| `processing` | Currently being processed by the agent (transient, rarely seen) |
| `published` | Processed, complete, in the active vault |
| `archived` | No longer maintained, kept for historical reference |
| `draft` | Human work-in-progress, not yet ready for processing |

The agent transitions documents from `inbox` → `processing` → `published` automatically during ingest. Humans can manually transition documents to `archived` or `draft`. The status drives the 3D visualization opacity (archived = faded, draft = dim, published = bright).

### `dates.created` (date)

When the markdown file was created on disk. ISO 8601 date (`YYYY-MM-DD`) is the standard, but ISO 8601 datetime (`YYYY-MM-DDTHH:MM:SSZ`) is acceptable when minute-level precision matters. Auto-populated by the template or the ingester. Never rely on filesystem `ctime` — it resets on sync, git operations, and device transfers.

```yaml
dates:
  created: 2026-04-06
```

This field is *not* the same as `dates.captured` (when you encountered the information) or `dates.published` (when the source was published). See Section 9 for the full temporal model.

### `dates.captured` (date)

When you first encountered or ingested the information. For documents created from a keep.md capture, this is the date the URL was saved. For documents created from a manual note, this is usually the same as `dates.created`. The distinction matters when you batch-process a reading queue: you might capture an article on March 1st but not create the formal note until March 20th.

```yaml
dates:
  created: 2026-03-20
  captured: 2026-03-01
```

This is the field that answers "what was I reading last month?" — the answer requires `dates.captured`, not `dates.created`.

### `dates.processed` (datetime)

When the AI agent last processed this document. ISO 8601 datetime with timezone. Auto-populated by the agent on every processing pass. Used by maintenance jobs to identify stale processing and by the agent itself to determine whether to re-evaluate a document.

```yaml
dates:
  processed: 2026-04-06T14:31:00Z
```

### `dates.modified` (date)

The last date the document was edited. Auto-updated by a file watcher or by the ingester when it writes changes. This is the field Dataview queries sort by when looking for "recently changed" — `SORT dates.modified DESC`.

```yaml
dates:
  modified: 2026-04-06
```

If the file watcher is not running, this field rots quickly. Either run the watcher (recommended) or accept that this field is unreliable and rely on `file.mtime` instead.

---

## 6. Tier 2: Type-Conditional Fields

These fields appear when the document type warrants them. The type registry in Section 8 lists which Tier 2 fields are appropriate for each type. The agent populates these fields during processing based on the document type and the source content.

### Identity extensions

#### `aliases` (list)

Alternative names, acronyms, or alternate spellings. Used by Obsidian's link autocomplete to surface the document under multiple names. Especially valuable for `person` documents (first name, nickname, full name) and `concept` documents (acronym, full term).

```yaml
aliases:
  - "JD"
  - "Jane D. Doe"
  - "Janie"
```

Applies to types: `person`, `concept`, `tool`, `organization`, `place`.

### Provenance (source attribution)

The `source` object groups all provenance metadata. The `source.type` field (Tier 1, but stored under `source` for grouping) is universal because every document has a source — even a manual note has `source.type: manual`.

#### `source.type` (text — Tier 1)

How the document entered the vault. One of:

- `keepmd` — saved via keep.md (browser, mobile, RSS, X, YouTube, GitHub, email)
- `obsidian_clipper` — saved via the Obsidian Web Clipper extension
- `manual` — written directly in Obsidian or another editor
- `api` — created via the `bg` CLI or another programmatic interface
- `agent` — created by the AI agent itself (synthesis notes, MOCs)

```yaml
source:
  type: keepmd
```

#### `source.url` (text)

The original URL the content came from. Immutable after creation — even if the source moves or disappears, the original URL is preserved as historical record. Applies to types: `article`, `repo`, `thread`, `podcast`, `film`, `email`, `reference`.

```yaml
source:
  url: "https://example.com/article"
```

#### `source.author` (text or list)

Creator of the source material. For multi-author works, use a list. Drives `(:Person)` node creation in FalkorDB and enables author-index queries.

```yaml
source:
  author: "Jane Doe"
# or
source:
  author:
    - "Jane Doe"
    - "John Smith"
```

#### `source.publisher` (text)

Publishing entity — site name, publication, organization, studio. Used by `(:Organization)` queries and by attribution displays.

```yaml
source:
  publisher: "Example Publishing"
```

#### `source.via` (text)

How you found this content. The referral chain. Could be a person ("recommended by Alice"), a feed ("RSS: Hacker News"), a search ("Google: knowledge graph databases"), or a context ("found while researching FalkorDB"). This field is high-signal for understanding *why* a particular piece of content entered your knowledge base.

```yaml
source:
  via: "Alice's newsletter, March 2026 issue"
```

#### `source.context` (text)

Why you saved it — your intent at capture time. This is the field most likely to be valuable in retrospect: six months from now, you will not remember why you bookmarked something, but the `source.context` will tell you. The agent should encourage the human to fill this in at capture time, and should never guess at it.

```yaml
source:
  context: "Looking for ARM64 graph database options for the Pi 5 build"
```

### Classification

#### `para` (text)

The PARA category from Tiago Forte's PARA method. One of:

- `projects` — active, time-bound initiatives with specific goals
- `areas` — ongoing responsibilities and standards to maintain
- `resources` — reference material on topics of interest
- `archives` — completed projects and inactive material

```yaml
para: resources
```

This is the workflow/lifecycle dimension of classification, distinct from `topics` (the knowledge dimension) and `tags` (the cross-cutting dimension). Most processed knowledge documents land in `resources`. Active work goes in `projects`. Completed work moves to `archives`.

#### `topics` (list)

Hierarchical topic assignment. The first entry is the primary topic; additional entries enable cross-domain classification. Topics use slash-delimited hierarchy (`technology/ai-ml`) which the ingester converts into `(:Topic)-[:SUBTOPIC_OF]->(:Topic)` relationships in FalkorDB.

```yaml
topics:
  - technology/ai-ml
  - technology/infrastructure
```

The starter taxonomy is in the beestgraph whitepaper (Section 13). Topics are explicitly designed to evolve — the agent suggests new topics during processing and the weekly report job recommends taxonomy changes.

#### `importance` (integer 1–5)

Personal importance scale. Drives 3D visualization sphere size and prioritization in queries.

| Value | Meaning |
|---|---|
| 1 | Passing interest, low-priority reference |
| 2 | Useful reference, worth keeping |
| 3 | Important knowledge, regularly relevant |
| 4 | Key insight, foundational to a topic area |
| 5 | Life-critical, central to active work or core values |

```yaml
importance: 3
```

The agent assigns an initial importance based on content analysis (a tutorial on a tool you use heavily gets 4; a passing news article gets 1). Humans can override.

#### `confidence` (float 0.0–1.0)

How reliable is the information in this document? Drives source quality filtering and visual emphasis.

| Range | Label | Meaning |
|---|---|---|
| 0.0–0.3 | speculative | Early thinking, unverified claims, opinion |
| 0.4–0.7 | likely | Researched and reasoned, could revise |
| 0.8–1.0 | established | Well-supported, multiple sources, high trust |

```yaml
confidence: 0.9
```

The numeric value enables thresholding and sorting; the agent computes the human-readable label as `confidence_label` if needed for display.

#### `content_stage` (text)

Where this document is in your thinking process. Borrowed from the Zettelkasten tradition.

| Value | Meaning |
|---|---|
| `fleeting` | Quick capture, raw thought, unprocessed |
| `literature` | Notes on external sources, rewritten in your own words |
| `evergreen` | Self-contained insight, written for longevity |
| `reference` | Stable documentation, API specs, lookup material |

```yaml
content_stage: literature
```

This is distinct from `type`. A document of `type: article` is almost always `content_stage: literature`. A document of `type: note` could be `fleeting` or `evergreen` depending on how processed it is. A document of `type: reference` is always `content_stage: reference`.

### Entities

The `entities` object groups all entity extraction. Each subcategory is a list of strings. The agent extracts entities during processing and creates corresponding nodes in FalkorDB.

```yaml
entities:
  people:
    - "Andrej Karpathy"
    - "Tiago Forte"
  concepts:
    - "knowledge graph"
    - "PARA method"
  organizations:
    - "Anthropic"
    - "Obsidian"
  tools:
    - "FalkorDB"
    - "Claude Code"
  places:
    - "San Francisco"
```

Each entity name is normalized for graph deduplication (`normalized_name = lower(strip(name))`). The agent attempts to match against existing entities in the graph before creating new ones.

### Engagement (simplified from v2)

The v2 template had five engagement statuses (`unread`, `reading`, `read`, `reviewed`, `reference`). The Unified PKM Schema warns explicitly that more than three status values are abandoned by practitioners within months. This spec reduces engagement to three statuses.

#### `engagement.status` (text)

| Value | Meaning |
|---|---|
| `unread` | Not yet read, or only skimmed |
| `read` | Actively read at least once |
| `reference` | Used as a lookup; never read linearly |

```yaml
engagement:
  status: read
```

#### `engagement.rating` (integer 1–5, optional)

Personal quality rating. Optional — only populate if you actually rate things. An unused `rating` field on 200 documents is pure metadata debt.

```yaml
engagement:
  rating: 4
```

#### `engagement.last_visited` (date, optional)

Last time you opened this document. Auto-updated by a file watcher if you run one; otherwise omit.

### Synthesis (AI-extracted)

These fields are populated by the agent during processing. They are the agent's structured interpretation of the document content.

#### `summary` (text)

A 2–3 sentence summary in the agent's words. The most-used field in the entire spec — appears in graph displays, search results, the morning brief, and any LLM context that references the document.

```yaml
summary: "Karpathy's LLM Wiki gist proposes a three-layer architecture where an LLM incrementally builds and maintains a persistent knowledge base. The pattern emphasizes compiling knowledge once and keeping it current rather than re-deriving via RAG on every query."
```

#### `key_claims` (list)

The core assertions made in the document. Each claim is a single sentence. Used by `bg think audit` to find supporting and contradicting evidence across the graph.

```yaml
key_claims:
  - "Knowledge should be compiled once and maintained, not re-derived per query."
  - "LLMs are well-suited to incremental wiki maintenance."
```

#### `questions` (list)

Questions the document raises for you. These become entry points for future research and `bg think emerge` can surface unanswered questions across the vault.

```yaml
questions:
  - "How does the wiki pattern scale beyond a single user?"
  - "What's the right granularity for individual wiki pages?"
```

#### `action_items` (list)

Things to do based on this document. These can be promoted to tasks via `bg task` or surfaced in the morning brief.

```yaml
action_items:
  - "Try the index.md/log.md pattern in beestgraph"
  - "Read the comment thread for federated indexing details"
```

### Connections (typed relationships)

The `connections` object groups all typed relationships to other documents. Each subcategory is a list of wiki-link strings. The agent creates corresponding edges in FalkorDB during processing.

```yaml
connections:
  supports:
    - "[[Karpathy LLM Wiki Gist]]"
    - "[[Active Vault Pattern]]"
  contradicts:
    - "[[RAG-First Architecture Notes]]"
  extends:
    - "[[beestgraph v1 Whitepaper]]"
  supersedes: []
  inspired_by:
    - "[[obsidian-second-brain Repo]]"
  related:
    - "[[FalkorDB Selection Notes]]"
```

| Relationship | Edge type in FalkorDB | Semantic |
|---|---|---|
| `supports` | `(:Document)-[:SUPPORTS]->(:Document)` | This provides evidence for the target |
| `contradicts` | `(:Document)-[:CONTRADICTS]->(:Document)` | This conflicts with the target |
| `extends` | `(:Document)-[:EXTENDS]->(:Document)` | This builds on the target |
| `supersedes` | `(:Document)-[:SUPERSEDES]->(:Document)` | This replaces or updates the target |
| `inspired_by` | `(:Document)-[:INSPIRED_BY]->(:Document)` | The target led to this |
| `related` | `(:Document)-[:RELATED_TO]->(:Document)` | Loose association |

**Critical rule:** Every entry in `connections.*` must also appear as an inline wikilink in the document body's "## Connections" section. See Section 10 for the rationale and the agent's responsibility.

### Type-specific Tier 2 fields

These fields appear only on documents of specific types.

#### For `project` documents

```yaml
area: "professional"        # the PARA area this project rolls up to
dates:
  due: 2026-06-30           # target completion date
```

#### For `person` documents

```yaml
role: "Senior Engineer at Example Corp"
```

(Person documents also use `aliases` heavily.)

#### For `meeting` documents

```yaml
dates:
  event_date: 2026-04-06    # when the meeting actually happened
attendees:
  - "[[Alice Smith]]"
  - "[[Bob Jones]]"
project: "[[Project Alpha]]"
```

#### For `moc` documents (Maps of Content)

```yaml
scope: "Knowledge graphs, graph databases, and graph-native AI"
```

#### For `book`, `film`, `podcast` documents

```yaml
source:
  author: "Author or Director or Host"
  publisher: "Publisher or Studio or Network"
engagement:
  rating: 4
```

#### For `tool` documents

```yaml
entities:
  tools:
    - "Tool Name"
engagement:
  rating: 4
key_claims:
  - "Pro: handles ARM64 natively"
  - "Con: requires JVM, high memory overhead"
```

---

## 7. Tier 3: Advanced Fields

These fields are supported by the spec but should only be populated when there is a demonstrated, recurring need. The agent does not populate Tier 3 fields by default — they are added by humans, by specialized agent workflows (thinking tools), or by content that obviously warrants them (a travel article naturally yields `location.*`).

### Structural hierarchy

#### `up` (list)

The single structural frontmatter link field worth keeping. Points to this document's parent MOC or structural hub. Used by the Breadcrumbs plugin in Obsidian and by the `bg think connect` command for hierarchical traversal.

```yaml
up:
  - "[[AI-ML MOC]]"
  - "[[PKM MOC]]"
```

This is the single exception to the "relationships in the body" principle (Section 10) because structural hierarchy is *scalar* (one or two parents) rather than associative (many sibling links). The agent populates `up` during processing based on the primary topic — for a document with `topics: [technology/ai-ml]`, the agent sets `up: ["[[AI-ML MOC]]"]`.

### Advanced temporal

#### `dates.published` (date)

When the original source was published. For articles, this is the publication date from the byline. For books, the publication year (use `YYYY-01-01` if only the year is known). For undated content, omit rather than guess.

```yaml
dates:
  published: 2025-01-15
```

#### `dates.reviewed` (date)

The last date a human re-evaluated the document for accuracy and relevance. Distinct from `dates.modified` (which fires on any edit) and from `dates.processed` (which fires on every agent pass). This is the temporal field most practitioners wish they had added earlier — it powers the single most valuable maintenance query in a mature vault: "show me active evergreen notes not reviewed in 90 days."

```yaml
dates:
  reviewed: 2026-03-15
```

Manual by nature. The act of reviewing is a judgment, not an edit event. Update the date when you have genuinely re-evaluated the content.

#### `dates.last_synthesis` (datetime)

The last time the agent evaluated this document against the rest of the graph for connection updates. Distinct from `dates.processed` (initial processing) and `dates.modified` (any edit). When the maintenance job runs the rewrite-on-ingest synthesis pass, it updates `dates.last_synthesis`. The weekly report uses this field to identify documents that need re-synthesis.

```yaml
dates:
  last_synthesis: 2026-04-01T02:15:00Z
```

#### `dates.expires` (date)

When this knowledge may become stale. The agent suggests an expiration date during processing for time-sensitive content (a "current state of X" article gets a 6-month expiration; a fundamental theorem gets none). After the expiration date, the document is flagged for review by the maintenance job.

```yaml
dates:
  expires: 2026-10-15
```

#### `dates.archived` (date)

When the document's status changed to `archived`. Auto-populated by the `bg archive` command or by the agent when it transitions a document to archived status. Pairs with `dates.created` to compute document lifespan.

```yaml
dates:
  archived: 2026-04-01
```

### Provenance integrity

#### `source.content_hash` (text)

SHA-256 hash of the source content at ingest time. Computed by the agent during processing. Enables the source health job to detect when a source URL has been modified or taken down since you ingested it.

```yaml
source:
  content_hash: "a3f2c9d8e7b6..."
```

#### `source.archived_locally` (boolean)

Whether a local copy of the source content exists in the vault's `raw/` directory. The agent sets this to `true` when it archives a copy of the original source (for important documents or content from sources likely to disappear).

```yaml
source:
  archived_locally: true
```

### Epistemic metadata

#### `epistemic_effort` (text)

How much work went into this note. Three values:

- `casual` — quick capture, minimal processing
- `moderate` — researched and reasoned
- `thorough` — extensive investigation, multiple sources

```yaml
epistemic_effort: thorough
```

This complements `confidence`: a note can be low-effort but high-confidence (obvious truths) or high-effort but speculative (complex research). Both fields together give a more complete picture of the note's epistemic status than either alone.

### Geospatial

```yaml
location:
  name: "Narragansett, Rhode Island"
  lat: 41.4321
  lon: -71.4495
  region: "Rhode Island, USA"
```

Applies to types: `place`, `event`, `meeting` (when the meeting was in person), `journal`, and any document where the geographic context matters. Drives map views and proximity queries.

### Media attachments

```yaml
media:
  images:
    - "attachments/diagram.png"
    - "https://example.com/photo.jpg"
  attachments:
    - "attachments/paper.pdf"
  audio:
    - "attachments/voice-memo.m4a"
  video:
    - "https://youtube.com/watch?v=..."
```

### Graph rendering hints

```yaml
graph:
  cluster: 7                # community detection result, auto-computed
  pinned: false             # pin this node's position in 3D space
  hidden: false             # exclude from default graph view
  color_override: "#E91E63" # override the type-based color
```

`graph.cluster` is auto-computed by the maintenance job's community detection pass. `graph.pinned`, `graph.hidden`, and `graph.color_override` are manual overrides for special cases.

### Versioning

#### `version` (integer)

Incremented on significant edits to the document. Distinct from filesystem versioning (git) and from `dates.modified`. The agent increments `version` when it does a substantive rewrite (e.g., during rewrite-on-ingest when an entity page gets meaningful new content).

```yaml
version: 3
```

---

## 8. The Type Registry

The `type` field is the master key that determines which Tier 2 fields apply. This registry lists all currently recognized types, the Tier 2 fields the agent should prioritize for each, and a brief description.

New types can be added at any time without breaking the schema — all fields remain optional.

### Knowledge types

| Type | Description | Priority Tier 2 fields |
|---|---|---|
| `article` | Web article, blog post, news story | `source.url`, `source.author`, `source.publisher`, `summary` |
| `concept` | Idea, framework, theory, definition | `aliases`, `key_claims`, `confidence`, `connections.related` |
| `reference` | Documentation, API spec, lookup material | `entities.tools`, `content_stage: reference`, `source.url` |
| `note` | Quick thought, observation, reflection | `source.context`, `content_stage: fleeting` |
| `quote` | Notable quote or passage | `source.author`, `source.url`, `connections.inspired_by` |

### Workflow types

| Type | Description | Priority Tier 2 fields |
|---|---|---|
| `project` | Active initiative with goals/timeline | `area`, `dates.due`, `action_items`, `status` |
| `decision` | A choice made with reasoning | `key_claims` (options), `connections.supports` (evidence) |
| `meeting` | Notes from a meeting or conversation | `dates.event_date`, `attendees`, `project`, `action_items` |
| `daily` | Daily journal entry, daily log | `dates.event_date`, `engagement.status: read`, `location` |
| `journal` | Personal diary entry | `dates.event_date`, `location` |
| `moc` | Map of Content — navigational hub | `scope`, `up` (parent MOC) |

### Entity types

| Type | Description | Priority Tier 2 fields |
|---|---|---|
| `person` | Individual referenced across the graph | `aliases`, `role`, `entities.organizations`, `location` |
| `organization` | Company, institution, group | `aliases`, `location`, `source.url` (website) |
| `tool` | Software, framework, service, hardware | `aliases`, `engagement.rating`, `key_claims` (pros/cons) |
| `place` | Location, restaurant, venue, destination | `location.*`, `engagement.rating`, `media.images` |

### Source types

| Type | Description | Priority Tier 2 fields |
|---|---|---|
| `book` | Book notes, review, summary | `source.author`, `engagement.rating`, `key_claims`, `dates.published` |
| `film` | Movie or TV show notes | `source.publisher` (studio), `engagement.rating`, `dates.published` |
| `podcast` | Podcast episode notes | `media.audio`, `source.author` (host), `entities.people` (guests) |
| `thread` | X/Twitter thread or discussion | `source.url`, `entities.people`, `key_claims` |
| `repo` | GitHub repository notes | `source.url`, `entities.tools`, `tags` |
| `email` | Saved newsletter or email | `source.author`, `source.publisher` |

### Specialized types

| Type | Description | Priority Tier 2 fields |
|---|---|---|
| `recipe` | Cooking recipe or procedure | `tags`, `media.images`, `engagement.rating` |
| `event` | Conference, meetup, occasion | `dates.event_date`, `location`, `entities.people` |
| `health` | Health observation, symptom, treatment | `dates.event_date`, `tags` (symptoms), `action_items` |
| `financial` | Financial decision, analysis, record | `entities.organizations`, `tags`, `importance` |
| `dream` | Dream journal entry | `dates.event_date`, `tags` (themes) |
| `collection` | Curated list of related items | `connections.related`, `tags` |
| `synthesis` | Agent-generated cross-document synthesis | `connections.*` (heavy use), `source.type: agent` |

### Default type

If no type is specified, the default is `note`. The agent should always assign a more specific type during processing if it can determine one from the content.

---

## 9. The Temporal Model

The temporal model is the area where the v2 template, the Unified PKM Schema, and the temporal KG research most strongly converged. The core insight: **collapsing time into a single date field loses information that powers the most valuable queries in a mature knowledge base.**

### Why one date is not enough

You read an article on March 10th. The article was published January 5th. You write the formal note on March 20th. The agent processes the note on March 21st. You re-read and update your interpretation on April 15th. You archive the note on August 1st.

That is six distinct moments in time, each answering a different question:

| Question | Field |
|---|---|
| "When did I create this file?" | `dates.created` (March 20) |
| "When did I encounter this information?" | `dates.captured` (March 10) |
| "When was the source published?" | `dates.published` (January 5) |
| "When did the AI process it?" | `dates.processed` (March 21) |
| "When did I last update it?" | `dates.modified` (April 15) |
| "When did I archive it?" | `dates.archived` (August 1) |

A single `date` field cannot answer "what was I reading last month?" because the answer depends on when you encountered the information, not when you created the file. A single `date` field cannot answer "show me sources from 2024" because the answer depends on the source publication date, not the file creation date.

### The eleven temporal dimensions

| Field | Tier | Auto? | Question it answers |
|---|---|---|---|
| `dates.created` | 1 | Yes (template/ingester) | When was the markdown file created? |
| `dates.captured` | 1 | Yes (capture timestamp) | When did I encounter the information? |
| `dates.processed` | 1 | Yes (agent) | When did the AI last process this? |
| `dates.modified` | 1 | Yes (file watcher) | When did I last edit this? |
| `dates.published` | 2 | Sometimes (from source) | When was the source published? |
| `dates.event_date` | 2 | No | When did the event occur? |
| `dates.due` | 2 | No | When does this need to be done? |
| `dates.reviewed` | 3 | No | When did I last re-evaluate this? |
| `dates.last_synthesis` | 3 | Yes (maintenance job) | When did the agent last check graph coherence? |
| `dates.expires` | 3 | Sometimes (agent suggestion) | When does this knowledge become stale? |
| `dates.archived` | 3 | Yes (archive command) | When did this become archived? |

### The minimum viable temporal model

A document that exists has, at minimum, four populated temporal fields (all Tier 1, all auto-populated):

```yaml
dates:
  created: 2026-04-06
  captured: 2026-04-06
  processed: 2026-04-06T14:31:00Z
  modified: 2026-04-06
```

For a fresh capture where everything happens at once, `created`, `captured`, and `modified` will all be the same date. The distinction matters only when they diverge — and they will diverge as soon as you start batch-processing, archiving, or revisiting.

---

## 10. The Inline Wikilink Mirroring Rule

This is the most important convention in the entire spec, and the one most likely to be forgotten by agents that have not been explicitly told.

### The rule

**Every entry in any `connections.*` frontmatter field must also appear as an inline wikilink in the document body's "## Connections" section.**

### Why this matters

Obsidian's backlink graph indexes inline `[[wikilinks]]` *but does not index frontmatter link fields*. If you put `connections.supports: ["[[Doc B]]"]` in the frontmatter and stop there, the link does not appear in Doc B's backlinks panel. Doc B has no idea Doc A links to it.

This is a long-standing Obsidian limitation that has not been fixed and is unlikely to change. The fix is simple: every connection in the frontmatter must be mirrored as an inline wikilink in the body.

### How the agent implements it

When the agent processes a document and writes any `connections.*` field, it must also write (or update) a "## Connections" section at the end of the document body containing all those links as inline wikilinks. The format is:

```markdown
## Connections

**Supports:**
- [[Doc B]]
- [[Doc C]]

**Contradicts:**
- [[Doc D]]

**Extends:**
- [[Doc E]]

**Related:**
- [[Doc F]]
- [[Doc G]]
```

If a connections category is empty, omit the subheading. If all categories are empty, write `(none identified)` as the section body.

### What this gives you

Once the rule is followed consistently, Obsidian's backlink graph and FalkorDB stay in sync. The frontmatter is the machine layer (the agent reads and writes it programmatically). The body wikilinks are the human layer (Obsidian's graph view shows them, the backlinks panel surfaces them, the user can navigate them by clicking).

### What about the `up` field?

The `up` field in Tier 3 is the single exception. It is intentionally a frontmatter-only relationship because it is *scalar* (one or two parents) and *structural* (used by Breadcrumbs plugin and Dataview, not by Obsidian's associative backlink graph). You do not mirror `up` as an inline wikilink because that would create a cycle with the parent MOC's content list.

---

## 11. The Complete Template

This is the canonical template file. It lives at `config/templates/universal.md` in the beestgraph repository. Type-specific templates are convenience shortcuts that pre-populate `type` and omit irrelevant fields, but they are all derived from this universal template.

```yaml
---
# ═══════════════════════════════════════════════════════════════
# TIER 1 — UNIVERSAL FIELDS (every document)
# ═══════════════════════════════════════════════════════════════
uid: ""                            # YYYYMMDDHHMM, auto-generated
title: ""
type: note                         # see Type Registry (Section 8)
tags: []                           # 2-5 lowercase hyphenated tags
status: inbox                      # inbox | draft | published | archived
dates:
  created: null                    # when the file was created
  captured: null                   # when you encountered the info
  processed: null                  # when the agent last processed
  modified: null                   # last human edit

# ═══════════════════════════════════════════════════════════════
# TIER 2 — TYPE-CONDITIONAL FIELDS
# ═══════════════════════════════════════════════════════════════

# Identity extensions
aliases: []                        # alternative names (person, concept, tool)

# Provenance
source:
  type: manual                     # keepmd | obsidian_clipper | manual | api | agent
  url: ""                          # original URL (article, repo, thread, etc.)
  author: ""                       # creator of the source
  publisher: ""                    # site, publication, organization
  via: ""                          # how you found it
  context: ""                      # why you saved it

# Classification
para: resources                    # projects | areas | resources | archives
topics: []                         # hierarchical: ["technology/ai-ml"]
importance: 3                      # 1-5
confidence: 0.8                    # 0.0-1.0
content_stage: literature          # fleeting | literature | evergreen | reference

# Entities
entities:
  people: []
  concepts: []
  organizations: []
  tools: []
  places: []

# Engagement
engagement:
  status: unread                   # unread | read | reference
  rating: null                     # 1-5, optional
  last_visited: null

# Synthesis (AI-extracted)
summary: ""                        # 2-3 sentences
key_claims: []
questions: []
action_items: []

# Connections (mirror in body "## Connections" section!)
connections:
  supports: []
  contradicts: []
  extends: []
  supersedes: []
  inspired_by: []
  related: []

# Type-specific extensions
area: ""                           # for type: project
role: ""                           # for type: person
attendees: []                      # for type: meeting
project: ""                        # for type: meeting
scope: ""                          # for type: moc

# ═══════════════════════════════════════════════════════════════
# TIER 3 — ADVANCED FIELDS (add when earned)
# ═══════════════════════════════════════════════════════════════

# Structural hierarchy
up: []                             # ["[[Parent MOC]]"]

# Advanced temporal
# dates.published: null            # source publication date
# dates.event_date: null           # for events
# dates.due: null                  # for projects
# dates.reviewed: null             # last human re-evaluation
# dates.last_synthesis: null       # last AI graph-coherence check
# dates.expires: null              # knowledge expiration
# dates.archived: null             # archival timestamp

# Provenance integrity
# source.content_hash: ""          # SHA-256 at ingest
# source.archived_locally: false   # local copy in raw/?

# Epistemic
epistemic_effort: null             # casual | moderate | thorough

# Geospatial
location:
  name: ""
  lat: null
  lon: null
  region: ""

# Media
media:
  images: []
  attachments: []
  audio: []
  video: []

# Graph rendering hints
graph:
  cluster: null                    # auto-computed
  pinned: false
  hidden: false
  color_override: null

# Versioning
version: 1
---

(freeform markdown body)

## Connections

(none identified)
```

---

## 12. FalkorDB Mapping

Every field in the template maps to a node property, an edge, or both in FalkorDB. This section documents the canonical mapping.

### Document node creation

```cypher
MERGE (d:Document {uid: $uid})
SET d.title = $title,
    d.type = $type,
    d.path = $path,
    d.status = $status,
    d.para = $para,
    d.importance = $importance,
    d.confidence = $confidence,
    d.content_stage = $content_stage,
    d.summary = $summary,
    d.created = $dates_created,
    d.captured = $dates_captured,
    d.processed = $dates_processed,
    d.modified = $dates_modified,
    d.published = $dates_published,
    d.event_date = $dates_event_date,
    d.due = $dates_due,
    d.reviewed = $dates_reviewed,
    d.last_synthesis = $dates_last_synthesis,
    d.expires = $dates_expires,
    d.archived = $dates_archived,
    d.source_type = $source_type,
    d.source_url = $source_url,
    d.source_via = $source_via,
    d.source_context = $source_context,
    d.source_content_hash = $source_content_hash,
    d.engagement_status = $engagement_status,
    d.rating = $engagement_rating,
    d.epistemic_effort = $epistemic_effort,
    d.lat = $location_lat,
    d.lon = $location_lon,
    d.location_name = $location_name,
    d.has_media = $has_media,
    d.cluster = $graph_cluster,
    d.pinned = $graph_pinned,
    d.hidden = $graph_hidden,
    d.color_override = $graph_color_override,
    d.version = $version
```

Note that nested YAML fields are flattened with underscores when stored in FalkorDB (FalkorDB does not support nested properties). The frontmatter file keeps nesting; the graph storage does not.

### Auxiliary node types

```cypher
(:Tag {name, normalized_name})
(:Topic {name, level})
(:Person {name, normalized_name})
(:Concept {name, normalized_name, description})
(:Organization {name, normalized_name})
(:Tool {name, normalized_name, url})
(:Place {name, normalized_name, lat, lon})
(:Source {url, domain, name})
```

### Relationship types

```cypher
-- Document relationships
(Document)-[:LINKS_TO]->(Document)              -- inline wikilinks
(Document)-[:TAGGED_WITH]->(Tag)
(Document)-[:BELONGS_TO]->(Topic)
(Document)-[:MENTIONS {confidence}]->(Person|Concept|Organization|Tool|Place)
(Document)-[:DERIVED_FROM]->(Source)

-- Typed connections (from connections.* frontmatter)
(Document)-[:SUPPORTS {weight}]->(Document)
(Document)-[:CONTRADICTS {weight}]->(Document)
(Document)-[:EXTENDS]->(Document)
(Document)-[:SUPERSEDES]->(Document)
(Document)-[:INSPIRED_BY]->(Document)
(Document)-[:RELATED_TO {weight}]->(Document)

-- Hierarchy
(Topic)-[:SUBTOPIC_OF]->(Topic)
(Document)-[:CHILD_OF]->(Document)              -- from up: field

-- Entity relationships
(Person)-[:AFFILIATED_WITH]->(Organization)
(Tool)-[:USED_BY]->(Project:Document)
(Place)-[:LOCATED_IN]->(Place)                  -- city → country
```

### Indexes

```cypher
-- Range indexes
CREATE INDEX FOR (d:Document) ON (d.uid)
CREATE INDEX FOR (d:Document) ON (d.path)
CREATE INDEX FOR (d:Document) ON (d.type)
CREATE INDEX FOR (d:Document) ON (d.status)
CREATE INDEX FOR (d:Document) ON (d.para)
CREATE INDEX FOR (d:Document) ON (d.importance)
CREATE INDEX FOR (d:Document) ON (d.created)
CREATE INDEX FOR (d:Document) ON (d.captured)
CREATE INDEX FOR (d:Document) ON (d.modified)
CREATE INDEX FOR (d:Document) ON (d.expires)
CREATE INDEX FOR (t:Tag) ON (t.normalized_name)
CREATE INDEX FOR (tp:Topic) ON (tp.name)
CREATE INDEX FOR (p:Person) ON (p.normalized_name)
CREATE INDEX FOR (c:Concept) ON (c.normalized_name)
CREATE INDEX FOR (o:Organization) ON (o.normalized_name)
CREATE INDEX FOR (tl:Tool) ON (tl.normalized_name)
CREATE INDEX FOR (pl:Place) ON (pl.normalized_name)

-- Full-text indexes
CALL db.idx.fulltext.createNodeIndex('Document', 'title', 'summary')
CALL db.idx.fulltext.createNodeIndex('Tag', 'name')
CALL db.idx.fulltext.createNodeIndex('Concept', 'name', 'description')
```

---

## 13. 3D Visualization Mapping

The template is designed to feed `3d-force-graph` (the recommended Phase 4 upgrade from Cytoscape.js) without post-processing. Eight visual dimensions map directly from frontmatter fields.

### Node dimensions

| Visual property | Field | Mapping |
|---|---|---|
| **Sphere size** | `importance` | val = importance × 2 |
| **Color (hue)** | `type` | type → TYPE_COLORS lookup |
| **Spatial cluster** | `topics[0]` | community detection on primary topic |
| **Opacity** | `status` | published=1.0, draft=0.6, archived=0.3 |
| **Glow / emissive** | `engagement.rating` | rating × 0.2 |
| **Border** | `confidence` | confidence × 3 px |
| **Pinned position** | `graph.pinned` | boolean lock |
| **Hidden** | `graph.hidden` | exclude from view |

### Edge dimensions

| Visual property | Field | Mapping |
|---|---|---|
| **Color** | relationship type | EDGE_COLORS lookup |
| **Width** | edge weight | weight × 2 |
| **Animated particles** | `CONTRADICTS` type | 3 particles, red |
| **Curvature** | edge type | hierarchical = curved, associative = straight |

### Type color palette

```javascript
const TYPE_COLORS = {
  // Knowledge
  article:      '#4A90D9',  // blue
  concept:      '#9B59B6',  // purple
  reference:    '#34495E',  // slate
  note:         '#95A5A6',  // grey
  quote:        '#16A085',  // dark teal
  // Workflow
  project:      '#E67E22',  // orange
  decision:     '#E91E63',  // pink
  meeting:      '#F39C12',  // amber
  daily:        '#FFC107',  // yellow
  journal:      '#FF9800',  // dark amber
  moc:          '#6366F1',  // indigo
  // Entities
  person:       '#2ECC71',  // green
  organization: '#27AE60',  // dark green
  tool:         '#1ABC9C',  // teal
  place:        '#E74C3C',  // red
  // Sources
  book:         '#8B4513',  // brown
  film:         '#7F8C8D',  // grey
  podcast:      '#9C27B0',  // dark purple
  thread:       '#1DA1F2',  // twitter blue
  repo:         '#181717',  // github black
  email:        '#D44638',  // gmail red
  // Specialized
  recipe:       '#FF6B6B',  // coral
  event:        '#FFD700',  // gold
  health:       '#10B981',  // emerald
  financial:    '#059669',  // dark emerald
  dream:        '#A78BFA',  // lavender
  collection:   '#64748B',  // cool grey
  synthesis:    '#EC4899',  // hot pink
};
```

### Edge color palette

```javascript
const EDGE_COLORS = {
  SUPPORTS:    '#2ECC71',  // green
  CONTRADICTS: '#E74C3C',  // red
  EXTENDS:     '#3498DB',  // blue
  SUPERSEDES:  '#F39C12',  // amber
  INSPIRED_BY: '#9B59B6',  // purple
  RELATED_TO:  '#95A5A6',  // grey
  LINKS_TO:    '#BDC3C7',  // light grey
  MENTIONS:    '#ECF0F1',  // very light grey
  BELONGS_TO:  '#7F8C8D',  // medium grey
  CHILD_OF:    '#34495E',  // slate (hierarchical)
};
```

### Transformation function

```javascript
async function buildGraphData(falkorClient) {
  const result = await falkorClient.query(`
    MATCH (d:Document)
    WHERE d.status <> 'archived' AND NOT d.hidden
    OPTIONAL MATCH (d)-[r]->(other:Document)
    RETURN d, type(r) AS rel_type, other
  `);

  const nodes = result.documents.map(d => ({
    id: d.uid,
    name: d.title,
    val: (d.importance || 2) * 2,
    group: d.type,
    community: d.topics?.[0]?.split('/')[0] || 'misc',
    color: d.color_override || TYPE_COLORS[d.type] || TYPE_COLORS.note,
    opacity: d.status === 'archived' ? 0.3 : d.status === 'draft' ? 0.6 : 1.0,
    rating: d.rating || 0,
    confidence: d.confidence || 0.5,
    summary: d.summary,
    tags: d.tags,
    captured: d.captured,
  }));

  const links = result.relationships.map(r => ({
    source: r.source_uid,
    target: r.target_uid,
    type: r.rel_type,
    color: EDGE_COLORS[r.rel_type] || EDGE_COLORS.RELATED_TO,
    width: (r.weight || 1) * 2,
    particles: r.rel_type === 'CONTRADICTS' ? 3 : 0,
    particleColor: r.rel_type === 'CONTRADICTS' ? '#E74C3C' : null,
  }));

  return { nodes, links };
}
```

---

## 14. Dataview Query Patterns

These query patterns work in Obsidian with the Dataview plugin. They are the human-facing equivalent of the FalkorDB Cypher queries — the same questions answered against the local vault rather than the graph database. Both should work; they should agree.

### Recently captured

```dataview
TABLE dates.captured AS "Captured", source.author AS "Author", summary
WHERE dates.captured >= date(today) - dur(30 days)
SORT dates.captured DESC
```

### Sources from a specific year

```dataview
TABLE dates.published AS "Published", source.author AS "Author", source.url AS "URL"
WHERE type = "article" 
  AND dates.published >= date(2025-01-01) 
  AND dates.published < date(2026-01-01)
SORT dates.published ASC
```

### Evergreen notes needing review

```dataview
LIST
WHERE content_stage = "evergreen" 
  AND status = "published"
  AND (!dates.reviewed OR dates.reviewed < date(today) - dur(90 days))
SORT dates.modified ASC
```

This is the single most valuable maintenance query in a mature vault.

### Active projects with deadlines this week

```dataview
TABLE dates.due AS "Due", area AS "Area"
WHERE type = "project" 
  AND status = "published" 
  AND dates.due <= date(today) + dur(7 days)
SORT dates.due ASC
```

### High-importance, high-confidence knowledge

```dataview
TABLE importance, confidence, summary
WHERE importance >= 4 AND confidence >= 0.8
SORT importance DESC, confidence DESC
```

### Knowledge bridges (documents in multiple top-level topics)

```dataview
TABLE topics, summary
WHERE length(topics) >= 2 
  AND length(unique(topics.map(t => split(t, "/")[0]))) >= 2
SORT importance DESC
```

### Stale processing (agent hasn't touched in 30 days)

```dataview
LIST
WHERE dates.processed < date(today) - dur(30 days)
SORT dates.processed ASC
```

### People mentioned across multiple domains

```dataview
TABLE length(file.inlinks) AS "References"
FROM "entities/people"
WHERE length(file.inlinks) >= 3
SORT length(file.inlinks) DESC
```

### Documents that may be expiring

```dataview
TABLE dates.expires AS "Expires", summary
WHERE dates.expires AND dates.expires <= date(today) + dur(30 days)
SORT dates.expires ASC
```

### Co-occurring tags (potential MOC opportunities)

```dataview
TABLE length(rows) AS "Count", rows.file.link AS "Documents"
FROM #knowledge-graphs AND #falkordb
GROUP BY tags
SORT length(rows) DESC
```

### Recently archived

```dataview
TABLE dates.created AS "Created", dates.archived AS "Archived", 
      (dates.archived - dates.created).days AS "Lifespan (days)"
WHERE status = "archived" AND dates.archived
SORT dates.archived DESC
LIMIT 20
```

---

## 15. Agent Instructions

This section is the canonical text for the agent processing instructions. It should be referenced from `CLAUDE.md` (or `CONTEXT.md` in the agent-agnostic naming) and from the prompts used by `bg ingest` and the OpenClaw cron jobs.

### Core processing rules

When processing a document, the agent must follow these rules in order:

**1. Tier 1 fields are mandatory.** Every document must have all eight Tier 1 fields populated after processing. Missing Tier 1 fields are a processing error.

**2. The `uid` field is immutable.** If the document already has a `uid`, preserve it. Generate a new `uid` only for documents that have never been processed before. Use the format `YYYYMMDDHHMM` based on the current time.

**3. `dates.captured` is preserved across re-processing.** Once set, never overwrite. The capture date is the moment the information entered the vault, regardless of how many times the agent re-processes the document afterward.

**4. `dates.processed` is updated on every pass.** Set to the current ISO 8601 datetime with timezone (`Z` for UTC).

**5. `dates.modified` reflects the latest substantive change.** If processing makes meaningful changes to the document content or frontmatter, update `dates.modified`. If processing is a no-op or only updates `dates.processed`, do not update `dates.modified`.

**6. Type assignment uses the Type Registry.** Look up the document type in Section 8 to determine which Tier 2 fields to prioritize. If the document has no `type`, infer one from content. Default to `note` if unsure.

**7. Importance is 1–5; confidence is 0.0–1.0.** Use the rubrics in Section 6. Default to `importance: 3` and `confidence: 0.8` if uncertain.

**8. Content stage reflects processing depth.** Quick captures are `fleeting`. Articles you've rewritten in your own words are `literature`. Self-contained insights are `evergreen`. Documentation and specs are `reference`.

**9. Topics use slash-delimited hierarchy.** Always use the format `top-level/sub-level` (e.g., `technology/ai-ml`). The first topic in the list is the primary topic and drives spatial clustering in the 3D view.

**10. Tags are lowercase and hyphenated.** Two to five tags per document. Tags are for *topics*, never for type or status.

### The connections mirroring rule

**Whenever you populate any `connections.*` field, you must also write a "## Connections" section at the end of the document body containing the same links as inline wikilinks.** Format:

```markdown
## Connections

**Supports:**
- [[Doc A]]
- [[Doc B]]

**Contradicts:**
- [[Doc C]]
```

Omit subheadings for empty categories. If all categories are empty, write `(none identified)`.

This rule exists because Obsidian does not generate backlinks from frontmatter link fields. If you skip the body mirror, the target documents will not show this document in their backlinks panel.

### Entity extraction guidelines

When extracting entities, populate all five subcategories that apply:

- `entities.people` — humans named in the content (authors are in `source.author`, not here, unless they're also discussed)
- `entities.concepts` — ideas, frameworks, theories, methods
- `entities.organizations` — companies, institutions, groups
- `entities.tools` — software, frameworks, services, hardware
- `entities.places` — locations relevant to the content

Normalize entity names for graph deduplication: lowercase, strip whitespace, no titles or honorifics. Match against existing entities in the graph before creating new ones.

### Tier 2 vs Tier 3

Populate Tier 2 fields when the document type warrants them. Do not populate Tier 3 fields by default — leave them absent. Only populate Tier 3 when:

- The source content makes the need obvious (a travel article naturally yields `location.*`)
- A specialized command requested it (the `bg think audit` command needs `confidence` set)
- The human explicitly added the field and the agent should preserve it

### Status transitions

- New documents from inbox: `status: inbox` → `processing` → `published`
- Human-created drafts: `status: draft` → `published` (when the human signals completion)
- Archived documents: `status: published` → `archived` (set `dates.archived`)
- Never set `status: processing` and leave it — that is a transient machine state

### Idempotency

Every graph write must use `MERGE`, never `CREATE`. Re-processing the same document must be safe and produce no duplicate nodes or edges. Entity matching uses `normalized_name` as the merge key.

### When in doubt

Prefer to omit a field rather than guess. A missing field means "not yet known"; an incorrect field is metadata pollution. The agent's job is to enrich what it can confidently determine, not to fill every blank.

---

## 16. Migration from v1 and v2

The spec is designed so existing documents continue to work without modification. The pipeline ingester accepts v1, v2, and final-spec frontmatter and transparently upgrades documents on processing.

### v1 → final-spec field mapping

The v1 templates used flat YAML with fields like `source_url`, `date_published`, `para_category`. These map cleanly to the final spec:

| v1 field | Final-spec field |
|---|---|
| `source_url` | `source.url` |
| `source_type` | `source.type` |
| `author` | `source.author` |
| `date_published` | `dates.published` |
| `date_captured` | `dates.captured` |
| `date_processed` | `dates.processed` |
| `para_category` | `para` |
| `entities.people` | `entities.people` (unchanged) |
| `entities.concepts` | `entities.concepts` (unchanged) |
| `entities.organizations` | `entities.organizations` (unchanged) |
| `summary` | `summary` (unchanged) |
| `topics` | `topics` (unchanged) |
| `tags` | `tags` (unchanged) |
| `status` | `status` (unchanged) |

The ingester reads v1 documents, computes the missing Tier 1 fields (`uid`, `dates.created`, `dates.modified`), and writes them back in nested format.

### v2 → final-spec changes

The v2 universal template was already very close to the final spec. The differences:

- **`dates.captured` is split.** v2 used `dates.captured` to mean both file creation and information encounter. Final spec splits these into `dates.created` (file) and `dates.captured` (information). On migration, the ingester sets both to the v2 `dates.captured` value as a starting point.
- **`uid` is added.** Generated from the v2 `dates.captured` timestamp on first re-processing.
- **`engagement.status` is reduced from 5 values to 3.** Migration mapping: `unread` → `unread`, `reading` → `read`, `read` → `read`, `reviewed` → `read`, `reference` → `reference`.
- **New Tier 3 fields are added but not populated.** `dates.reviewed`, `dates.last_synthesis`, `source.content_hash`, `epistemic_effort` — these are added to the schema but left absent on migrated documents until they earn population.
- **Inline wikilink mirroring is enforced.** On first re-processing, the agent writes the "## Connections" section to any document with non-empty `connections.*` fields that does not already have one.

### The `bg migrate` command

```bash
bg migrate --dry-run            # show what would change
bg migrate                      # migrate all documents
bg migrate --path knowledge/    # migrate a subdirectory
bg migrate --type article       # migrate documents of a specific type
```

The command is idempotent — running it twice has no additional effect after the first run completes.

### Backward compatibility window

The pipeline ingester supports v1 and v2 frontmatter indefinitely. There is no deadline for migration. Documents are upgraded opportunistically as they are re-processed. The `bg migrate` command is provided for users who want to upgrade in bulk rather than waiting for organic re-processing.

---

## 17. Anti-Patterns

These are mistakes practitioners consistently report making, organized by category. The spec is designed to make these difficult, but the agent and the human should both be aware of them.

### Schema anti-patterns

**Adding fields speculatively.** If you cannot point to a Dataview query, a Cypher pattern, or a workflow that uses a field, do not add it. The cost of adding a field later is near-zero. The cost of maintaining an unused field across hundreds of documents is real.

**Encoding type or status in tags.** `tags: [evergreen, active]` duplicates `type` and `status`, creates ambiguity, and pollutes tag search. Tags are for topics only.

**More than three engagement statuses.** Every practitioner report converges on this. Five-value reading-status ladders (unread → reading → read → reviewed → reference) get abandoned within months.

**Storing relationship links exclusively in frontmatter.** Frontmatter links do not generate backlinks in Obsidian. Always mirror connection fields as inline wikilinks in the body (Section 10).

### Temporal anti-patterns

**Conflating file creation with information encounter.** `dates.created` is when the file was made; `dates.captured` is when you encountered the information. They are often the same but they can diverge by weeks when you batch-process a reading queue.

**Manually maintaining `dates.modified`.** Either run a file watcher that updates it automatically, or omit the field and rely on `file.mtime`. Manual maintenance fails within weeks.

**Updating `dates.reviewed` on every edit.** That is what `dates.modified` is for. `dates.reviewed` is for genuine re-evaluation events — when you read the document with intent to verify it's still accurate.

### Format anti-patterns

**Deeply nested YAML objects.** The spec uses one level of nesting (`source.url`, `dates.created`). Do not nest further (`source.metadata.url`). Obsidian Properties UI handles one level of nesting acceptably and deeper nesting poorly.

**Mixing flat and nested in the same file.** Pick one. The canonical format is nested. The flat-export format is flat. Files in the vault use nested. Files exported for other tools use flat. Never mix.

**Storing computed fields manually.** `confidence_label`, `graph.cluster`, `has_media` are all derived from other fields. Do not set them by hand — let the agent or the ingester compute them.

### Content anti-patterns

**Empty fields as placeholders.** A field with an empty string or empty list is metadata noise. Omit the field entirely if it has no value. The ingester treats missing fields as "not yet known."

**Guessing at `source.context`.** If the human did not record why they saved something, the agent should leave `source.context` blank. Inventing context six months after capture is worse than admitting you don't remember.

**Over-categorizing with topics.** The first topic is the primary topic and drives spatial clustering. Adding many secondary topics dilutes that signal. Two or three topics is a reasonable maximum.

---

## 18. Complete Field Reference

| Field | Type | Tier | Auto? | Applies to | Notes |
|---|---|---|---|---|---|
| `uid` | text | 1 | Ingester | all | YYYYMMDDHHMM, immutable |
| `title` | text | 1 | Manual/agent | all | display title |
| `type` | text | 1 | Manual/agent | all | see Type Registry |
| `tags` | list | 1 | Agent | all | flat, lowercase, 2-5 |
| `status` | text | 1 | Agent/manual | all | inbox/draft/published/archived |
| `dates.created` | date | 1 | Template/ingester | all | file creation |
| `dates.captured` | date | 1 | Capture | all | info encounter |
| `dates.processed` | datetime | 1 | Agent | all | last agent pass |
| `dates.modified` | date | 1 | File watcher | all | last edit |
| `aliases` | list | 2 | Manual/agent | person, concept, tool | alt names |
| `source.type` | text | 1* | Auto | all | *technically Tier 1 but stored under source |
| `source.url` | text | 2 | Capture | article, repo, thread, etc. | immutable |
| `source.author` | text/list | 2 | Agent | article, book, podcast | creator |
| `source.publisher` | text | 2 | Agent | article, book, film | publishing entity |
| `source.via` | text | 2 | Manual | all | how you found it |
| `source.context` | text | 2 | Manual | all | why you saved it |
| `para` | text | 2 | Agent | all | projects/areas/resources/archives |
| `topics` | list | 2 | Agent | all | hierarchical |
| `importance` | int | 2 | Agent | all | 1-5 |
| `confidence` | float | 2 | Agent | all | 0.0-1.0 |
| `content_stage` | text | 2 | Agent | all | fleeting/literature/evergreen/reference |
| `entities.people` | list | 2 | Agent | most types | normalized for dedup |
| `entities.concepts` | list | 2 | Agent | most types | |
| `entities.organizations` | list | 2 | Agent | most types | |
| `entities.tools` | list | 2 | Agent | most types | |
| `entities.places` | list | 2 | Agent | most types | |
| `engagement.status` | text | 2 | Manual | all | unread/read/reference |
| `engagement.rating` | int | 2 | Manual | all | 1-5, optional |
| `engagement.last_visited` | date | 2 | File watcher | all | optional |
| `summary` | text | 2 | Agent | all | 2-3 sentences |
| `key_claims` | list | 2 | Agent | all | core assertions |
| `questions` | list | 2 | Agent | all | open questions |
| `action_items` | list | 2 | Agent | all | derived TODOs |
| `connections.supports` | list | 2 | Agent | all | mirror in body! |
| `connections.contradicts` | list | 2 | Agent | all | mirror in body! |
| `connections.extends` | list | 2 | Agent | all | mirror in body! |
| `connections.supersedes` | list | 2 | Agent | all | mirror in body! |
| `connections.inspired_by` | list | 2 | Agent | all | mirror in body! |
| `connections.related` | list | 2 | Agent | all | mirror in body! |
| `area` | text | 2 | Manual | project | PARA area rollup |
| `role` | text | 2 | Manual | person | current role |
| `attendees` | list | 2 | Manual | meeting | wikilinks to people |
| `project` | text | 2 | Manual | meeting | wikilink to project |
| `scope` | text | 2 | Manual | moc | what this MOC covers |
| `up` | list | 3 | Agent | any | parent MOC link |
| `dates.published` | date | 3 | Agent | source-bearing | source publication |
| `dates.event_date` | date | 3 | Manual | meeting, event, journal | when it happened |
| `dates.due` | date | 3 | Manual | project | deadline |
| `dates.reviewed` | date | 3 | Manual | evergreen, literature | last re-evaluation |
| `dates.last_synthesis` | datetime | 3 | Maintenance job | all | last graph coherence check |
| `dates.expires` | date | 3 | Agent | time-sensitive | knowledge expiration |
| `dates.archived` | date | 3 | Archive command | archived | when archived |
| `source.content_hash` | text | 3 | Ingester | source-bearing | SHA-256 |
| `source.archived_locally` | bool | 3 | Agent | source-bearing | local copy in raw/ |
| `epistemic_effort` | text | 3 | Manual | research-heavy | casual/moderate/thorough |
| `location.name` | text | 3 | Agent/manual | place, event, journal | human-readable |
| `location.lat` | float | 3 | Agent | place, event | decimal degrees |
| `location.lon` | float | 3 | Agent | place, event | decimal degrees |
| `location.region` | text | 3 | Agent | place, event | city/state/country |
| `media.images` | list | 3 | Agent | any with images | paths or URLs |
| `media.attachments` | list | 3 | Agent | any with files | paths |
| `media.audio` | list | 3 | Agent | podcast, voice memos | paths or URLs |
| `media.video` | list | 3 | Agent | film, lectures | paths or URLs |
| `graph.cluster` | int | 3 | Maintenance job | all | community ID |
| `graph.pinned` | bool | 3 | Manual | all | lock 3D position |
| `graph.hidden` | bool | 3 | Manual | all | exclude from view |
| `graph.color_override` | text | 3 | Manual | all | hex color |
| `version` | int | 1 | Agent | all | incremented on rewrite |

---

## 19. Appendix: Worked Examples

### Example 1: An article captured via keep.md

```yaml
---
uid: "202604061030"
title: "Building Knowledge Graphs from Markdown"
type: article
tags:
  - knowledge-graphs
  - markdown
  - obsidian
status: published
dates:
  created: 2026-04-06
  captured: 2026-04-06
  processed: 2026-04-06T10:35:00Z
  modified: 2026-04-06
  published: 2026-03-28
source:
  type: keepmd
  url: "https://example.com/knowledge-graphs-markdown"
  author: "James Croft"
  publisher: "Example Tech Blog"
  via: "RSS: PKM weekly digest"
  context: "Researching how others bridge markdown vaults to graph databases"
  content_hash: "a3f2c9d8e7b6a5c4d3e2f1b0a9c8d7e6f5b4a3c2d1e0f9b8a7c6d5e4f3b2a1c0"
para: resources
topics:
  - technology/ai-ml
  - meta/pkm
importance: 4
confidence: 0.85
content_stage: literature
entities:
  people:
    - "James Croft"
  concepts:
    - "knowledge graph"
    - "frontmatter"
    - "wikilinks"
  tools:
    - "Obsidian"
    - "Dataview"
engagement:
  status: read
  rating: 4
summary: "Croft proposes a dual-strategy approach to knowledge graphs in markdown: typed relationships in frontmatter for machine-readable structure, and inline wikilinks in the body for human navigation and Obsidian backlink generation. The two layers serve complementary purposes."
key_claims:
  - "Frontmatter relationships are the machine layer; inline wikilinks are the human layer."
  - "Obsidian's backlink graph does not index frontmatter link fields."
  - "Both layers should be kept in sync, neither is the sole source of truth."
questions:
  - "How does this approach scale beyond a few thousand notes?"
  - "What's the right granularity for typed relationships?"
action_items:
  - "Apply the dual-strategy pattern to beestgraph's connections fields"
connections:
  supports:
    - "[[beestgraph Universal Template]]"
  related:
    - "[[Karpathy LLM Wiki Pattern]]"
    - "[[Unified PKM Frontmatter Schema]]"
up:
  - "[[PKM MOC]]"
version: 1
---

The article opens by acknowledging the central tension in markdown-based knowledge management: markdown is excellent for human reading but the relationships between documents — the part that makes a "knowledge graph" valuable — need machine-readable structure that pure markdown lacks.

[... article body continues ...]

## Connections

**Supports:**
- [[beestgraph Universal Template]]

**Related:**
- [[Karpathy LLM Wiki Pattern]]
- [[Unified PKM Frontmatter Schema]]
```

### Example 2: A meeting note

```yaml
---
uid: "202604051430"
title: "beestgraph architecture review with Alice"
type: meeting
tags:
  - beestgraph
  - architecture-review
status: published
dates:
  created: 2026-04-05
  captured: 2026-04-05
  processed: 2026-04-05T15:00:00Z
  modified: 2026-04-05
  event_date: 2026-04-05
source:
  type: manual
  context: "Walking through the v2 template design and 3D viz mapping"
para: projects
topics:
  - meta/projects
importance: 4
content_stage: literature
attendees:
  - "[[Alice Smith]]"
project: "[[beestgraph]]"
entities:
  people:
    - "Alice Smith"
  concepts:
    - "tier system"
    - "type registry"
  tools:
    - "FalkorDB"
    - "3d-force-graph"
summary: "Alice and I walked through the v2 template design. She pushed back on the 5-value engagement status, agreeing it should reduce to 3. We aligned on the inline wikilink mirroring rule as the most important convention. Action items: write up the final spec, update CLAUDE.md."
action_items:
  - "Write the final template spec consolidating all four source documents"
  - "Update CLAUDE.md with the new agent instructions"
  - "Add bg migrate command for v1/v2 → final-spec migration"
connections:
  related:
    - "[[beestgraph v2 Template Design]]"
version: 1
---

## Discussion

Walked Alice through the four source documents (v1 templates, v2 universal template, Unified PKM Schema, research synthesis) and the open questions about how to consolidate them.

[... meeting notes continue ...]

## Connections

**Related:**
- [[beestgraph v2 Template Design]]
```

### Example 3: A minimum-viable note

```yaml
---
uid: "202604061500"
title: "Idea: use uid as FalkorDB primary key"
type: note
tags:
  - beestgraph
  - graph-design
status: published
dates:
  created: 2026-04-06
  captured: 2026-04-06
  processed: 2026-04-06T15:01:00Z
  modified: 2026-04-06
para: resources
topics:
  - meta/pkm
content_stage: fleeting
summary: "Using uid as the FalkorDB primary key instead of path means renaming or moving files doesn't create duplicate nodes."
version: 1
---

If we MERGE on `path`, then renaming `knowledge/ai/foo.md` to `knowledge/ai-ml/foo.md` creates a new node. If we MERGE on `uid`, the same node persists across path changes. Worth it.

## Connections

(none identified)
```

This is a fleeting note with the bare minimum populated. The agent expanded the human's two-line input (`title` and `type`) into the full Tier 1 plus enough Tier 2 (`para`, `topics`, `content_stage`, `summary`) to make the note queryable.

---

*This document is the canonical specification for the beestgraph universal template. It supersedes all prior template documentation. Future revisions should be made by amending this document directly rather than creating parallel specifications.*
