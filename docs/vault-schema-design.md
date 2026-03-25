# Vault Schema Design — Unified Organizational Framework

> Combining PARA, Zettelkasten, and Topic Trees with a graph-native backbone.

**Status:** DESIGN — requires review before implementation.

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Folder Structure](#folder-structure)
3. [Note Lifecycle](#note-lifecycle)
4. [Frontmatter Schema](#frontmatter-schema)
5. [Note Types](#note-types)
6. [MOCs (Maps of Content)](#mocs-maps-of-content)
7. [FalkorDB Schema Updates](#falkordb-schema-updates)
8. [Naming Conventions](#naming-conventions)
9. [Migration Plan](#migration-plan)

---

## Design Philosophy

Three systems, one vault, one graph:

### PARA — The Action Layer
> "What needs my attention?"

Projects, Areas, Resources, Archives organize notes by **actionability**. A note moves through these stages as its relevance changes. This answers: "What am I working on?" and "What can I ignore?"

### Zettelkasten — The Connection Layer
> "How does this idea relate to everything else?"

Every note is **atomic** (one idea), heavily linked, and graduates through maturity levels. Fleeting → literature → permanent. This answers: "What connects to what?" and "What patterns am I seeing?"

### Topic Tree — The Navigation Layer
> "Where do I find things about X?"

Hierarchical topics (`technology/ai-ml/knowledge-graphs`) provide familiar drill-down navigation. MOCs (Maps of Content) serve as curated entry points. This answers: "Show me everything about machine learning."

### The beestgraph advantage

Unlike a pure Obsidian setup, we have:
- **FalkorDB** — the graph database tracks all relationships, not just `[[wiki-links]]`
- **AI classification** — Claude assigns type, topic, tags, and maturity at capture time
- **Qualification pipeline** — enforces frontmatter completeness before permanent storage
- **Telegram bot** — interactive refinement of metadata
- **Full-text + graph search** — find notes by content, relationship, or metadata

This means we can be **more aggressive with metadata** (the pipeline enforces it) and **less dependent on folder hierarchy** (the graph handles discovery). Folders become a convenience, not the primary organizational tool.

---

## Folder Structure

```
~/vault/
├── 00-meta/                    # System notes
│   ├── templates/              # Frontmatter templates per note type
│   ├── mocs/                   # Maps of Content (curated indexes)
│   ├── dashboards/             # Dataview-powered overview notes
│   └── settings/               # Vault config notes
│
├── 01-inbox/                   # Raw captures — empty daily
│   └── (files land here from keep.md, clipper, telegram, manual)
│
├── 02-queue/                   # Qualification queue — awaiting review
│   └── (files here have AI recommendations, awaiting approval)
│
├── 03-fleeting/                # Quick thoughts, rough ideas
│   └── (graduated from inbox, not yet fully processed)
│
├── 04-daily/                   # Daily notes, journals, logs
│   ├── 2026-03-24.md
│   └── ...
│
├── 05-projects/                # PARA: Active projects with deadlines
│   ├── beestgraph/
│   ├── home-renovation/
│   └── ...
│
├── 06-areas/                   # PARA: Ongoing responsibilities
│   ├── health/
│   ├── career/
│   ├── finance/
│   └── ...
│
├── 07-resources/               # PARA: Reference knowledge (permanent notes)
│   ├── technology/
│   │   ├── ai-ml/
│   │   ├── programming/
│   │   ├── infrastructure/
│   │   └── ...
│   ├── science/
│   ├── business/
│   ├── culture/
│   └── ...
│
├── 08-archive/                 # PARA: Completed/inactive
│   ├── projects/
│   ├── rejected/               # Items rejected during qualification
│   └── ...
│
├── 09-attachments/             # Binary files (images, PDFs, etc.)
│   └── ...
│
└── heartbeat.md                # System health (auto-generated)
```

### Key changes from current structure

| Current | New | Why |
|---------|-----|-----|
| `inbox/` | `01-inbox/` | Numbered for sort order |
| `queue/` | `02-queue/` | Part of the visible lifecycle |
| (none) | `03-fleeting/` | New: Zettelkasten fleeting notes |
| `daily/` | `04-daily/` | Numbered |
| `projects/` | `05-projects/` | Numbered |
| `areas/` | `06-areas/` | Numbered |
| `knowledge/` | `07-resources/` | Renamed to PARA terminology |
| `archives/` | `08-archive/` | Numbered, singular |
| `templates/` | `00-meta/templates/` | Templates are meta, not content |

---

## Note Lifecycle

Every note progresses through maturity stages tracked in frontmatter:

```
┌─────────────┐
│   CAPTURE   │  Source: keep.md, clipper, telegram, manual
│  status:    │  Location: 01-inbox/
│  inbox      │  Maturity: raw
└──────┬──────┘
       ▼
┌─────────────┐
│   QUALIFY   │  AI classifies, Telegram notification
│  status:    │  Location: 02-queue/
│  qualifying │  Maturity: raw
└──────┬──────┘
       ▼
┌─────────────┐
│  FLEETING   │  Quick capture approved but not fully processed
│  status:    │  Location: 03-fleeting/
│  fleeting   │  Maturity: fleeting
└──────┬──────┘
       ▼
┌─────────────┐
│  PERMANENT  │  Fully processed, atomic, linked
│  status:    │  Location: 07-resources/<topic>/ or 05-projects/ etc.
│  published  │  Maturity: permanent
└──────┬──────┘
       ▼
┌─────────────┐
│  ARCHIVED   │  No longer active/relevant
│  status:    │  Location: 08-archive/
│  archived   │  Maturity: permanent
└─────────────┘
```

### Graduation rules

- **inbox → qualifying**: Automatic (watcher detects, AI classifies)
- **qualifying → fleeting**: User approves via Telegram with basic metadata
- **qualifying → permanent**: User approves with full metadata (type, topic, tags, summary)
- **fleeting → permanent**: User enriches with atomic note writing, links, full frontmatter
- **permanent → archived**: User marks as inactive/completed
- **any → rejected**: User rejects during qualification

---

## Frontmatter Schema

### Universal fields (every note, always)

```yaml
---
# ── Identity ──────────────────────────────────────
id: "20260324213500"              # Zettelkasten timestamp ID (YYYYMMDDHHMMSS)
title: "Knowledge Graphs for Personal Knowledge Management"
aliases: []                        # Alternative names for linking

# ── Timestamps ────────────────────────────────────
created: 2026-03-24T21:35:00Z     # When first captured/created
modified: 2026-03-24T22:10:00Z    # Last edit
published: ""                      # When approved to permanent
source_date: 2026-03-20            # Original publication date (if external)

# ── Classification ────────────────────────────────
type: article                      # Content type (see Note Types)
status: published                  # inbox | qualifying | fleeting | published | archived
maturity: permanent                # raw | fleeting | permanent
para: resources                    # projects | areas | resources | archive

# ── Topic & Tags ──────────────────────────────────
topics:
  - technology/ai-ml
  - technology/programming
tags:
  - knowledge-graphs
  - falkordb
  - obsidian
mocs:                              # Maps of Content this note belongs to
  - "[[Knowledge Graphs MOC]]"
  - "[[PKM MOC]]"

# ── Summary ───────────────────────────────────────
summary: "Overview of how knowledge graphs can power personal knowledge management systems, with practical examples using FalkorDB and Obsidian."

# ── Source ────────────────────────────────────────
source_url: "https://example.com/article"
source_type: keepmd                # keepmd | obsidian_clipper | telegram | manual | web_ui
source_domain: "example.com"
author: "Author Name"

# ── Quality & Qualification ──────────────────────
quality: high                      # high | medium | low
qualified_by: user                 # user | auto
qualification_notes: ""

# ── Entities (AI-extracted) ──────────────────────
entities:
  people: []
  concepts: []
  organizations: []
  tools: []

# ── Relationships ────────────────────────────────
related:                           # Explicit related notes
  - "[[Other Note]]"
supersedes: ""                     # If this replaces an older note
---
```

### Type-specific fields (appended for certain content types)

```yaml
# ── article/tutorial ──────────────────────────────
key_points:
  - "First key takeaway"
  - "Second key takeaway"
difficulty: intermediate           # beginner | intermediate | advanced (tutorials)
estimated_time: "15 min"           # Reading/completion time

# ── paper ─────────────────────────────────────────
doi: "10.1234/..."
arxiv_id: ""
journal: ""
year: 2026
abstract: ""

# ── tweet ─────────────────────────────────────────
tweet_author: "@handle"
tweet_url: "https://x.com/..."
tweet_thread: false

# ── github-repo ──────────────────────────────────
github_repo: "owner/repo"
github_stars: 1234
language: "Python"
license: "MIT"

# ── video ─────────────────────────────────────────
duration: "45:00"
channel: "Channel Name"
platform: youtube

# ── book ──────────────────────────────────────────
isbn: ""
publisher: ""
pages: 0
genre: ""
rating: 0

# ── recipe ────────────────────────────────────────
servings: 4
prep_time: "15 min"
cook_time: "30 min"
cuisine: ""
ingredients: []

# ── person ────────────────────────────────────────
role: ""
affiliation: ""
contact: ""

# ── project (PARA) ───────────────────────────────
project_status: active             # active | on-hold | completed
deadline: ""
outcomes: []

# ── area (PARA) ──────────────────────────────────
area_type: ""                      # health, career, finance, etc.
review_cycle: monthly              # weekly | monthly | quarterly
```

---

## Note Types

### Content types (external captures)

| Type | Folder | Description |
|------|--------|-------------|
| `article` | `07-resources/<topic>/` | Blog post, news, essay |
| `paper` | `07-resources/<topic>/` | Academic paper, research |
| `tutorial` | `07-resources/<topic>/` | How-to guide, walkthrough |
| `reference` | `07-resources/<topic>/` | Documentation, API reference |
| `video` | `07-resources/<topic>/` | YouTube, conference talk |
| `podcast` | `07-resources/<topic>/` | Audio content |
| `tweet` | `07-resources/<topic>/` | X/Twitter post or thread |
| `github-repo` | `07-resources/<topic>/` | GitHub repository |
| `book` | `07-resources/<topic>/` | Book notes, review |
| `recipe` | `07-resources/<topic>/` | Food recipe |
| `product` | `07-resources/<topic>/` | Product page, review |
| `url` | `07-resources/<topic>/` | Generic web page |
| `pdf` | `07-resources/<topic>/` | PDF document |

### Knowledge types (internal creation)

| Type | Folder | Description |
|------|--------|-------------|
| `fleeting` | `03-fleeting/` | Quick thought, rough idea |
| `note` | `07-resources/<topic>/` | Permanent atomic note (one idea) |
| `moc` | `00-meta/mocs/` | Map of Content (curated index) |
| `daily` | `04-daily/` | Daily note / journal |
| `project` | `05-projects/<name>/` | Project tracking note |
| `area` | `06-areas/<name>/` | Area of responsibility |
| `dashboard` | `00-meta/dashboards/` | Dataview-powered overview |
| `meeting` | `04-daily/` or `05-projects/` | Meeting notes |
| `person` | `07-resources/people/` | Person profile |
| `thought` | `03-fleeting/` or `07-resources/` | Personal reflection |

---

## MOCs (Maps of Content)

MOCs are curated index notes that link to related notes. They live in `00-meta/mocs/` and serve as the **primary navigation tool** — more important than folders.

### Structure of a MOC

```markdown
---
id: "20260324000000"
title: "Knowledge Graphs MOC"
type: moc
status: published
maturity: permanent
para: resources
tags:
  - moc
  - knowledge-graphs
summary: "Everything I know about knowledge graphs — tools, concepts, articles, and projects."
---

# Knowledge Graphs MOC

## Core Concepts
- [[What is a Knowledge Graph]]
- [[Graph Database vs Relational Database]]
- [[Property Graph Model]]

## Tools & Platforms
- [[FalkorDB]] — the graph database powering beestgraph
- [[Neo4j]] — the most popular graph database
- [[Obsidian]] — our vault and note-taking tool

## Articles & Papers
- [[Introduction to Knowledge Graphs]]
- [[Building Knowledge Graphs at Scale]]

## Projects
- [[beestgraph]] — my personal knowledge graph system

## Open Questions
- How to handle temporal facts without Graphiti?
- Best approach for entity resolution across sources?
```

### Starter MOCs to create

- **Home** — the root MOC, links to all others
- **Technology MOC** → sub-MOCs: AI/ML, Programming, Infrastructure, Security, Web
- **Science MOC** → Physics, Biology, Mathematics
- **Business MOC** → Startups, Finance, Marketing
- **Culture MOC** → Books, Film, Music, History
- **Health MOC** → Fitness, Nutrition, Mental Health
- **Projects MOC** → All active projects
- **People MOC** → Notable people across all domains
- **PKM MOC** — meta: how this system works

---

## FalkorDB Schema Updates

The graph schema needs to evolve to support the new organizational model.

### New node properties

```cypher
(:Document {
  id: STRING,                 -- Zettelkasten timestamp ID (new)
  path: STRING,
  title: STRING,
  content: STRING,
  summary: STRING,
  status: STRING,             -- inbox | qualifying | fleeting | published | archived
  maturity: STRING,           -- raw | fleeting | permanent (new)
  para: STRING,               -- projects | areas | resources | archive (renamed from para_category)
  content_type: STRING,       -- article | paper | tweet | etc. (new, was source_type)
  source_type: STRING,        -- keepmd | obsidian_clipper | telegram | manual
  source_url: STRING,
  source_domain: STRING,      -- (new)
  quality: STRING,            -- high | medium | low (new)
  author: STRING,
  created_at: STRING,
  modified_at: STRING,        -- (new)
  published_at: STRING,       -- (new)
  source_date: STRING         -- (new)
})
```

### New node type

```cypher
(:MOC {
  name: STRING,               -- e.g. "Knowledge Graphs MOC"
  normalized_name: STRING,
  path: STRING,               -- vault path
  description: STRING
})
```

### New relationships

```cypher
(Document)-[:IN_MOC]->(MOC)           -- note belongs to a MOC
(MOC)-[:CHILD_OF]->(MOC)              -- MOC hierarchy
(Document)-[:SUPERSEDES]->(Document)  -- note replaces an older note
(Document)-[:GRADUATED_FROM]->(Document) -- fleeting → permanent lineage
```

### New indexes

```cypher
CREATE INDEX FOR (d:Document) ON (d.id)
CREATE INDEX FOR (d:Document) ON (d.maturity)
CREATE INDEX FOR (d:Document) ON (d.content_type)
CREATE INDEX FOR (m:MOC) ON (m.normalized_name)
```

---

## Naming Conventions

### Files

| Type | Pattern | Example |
|------|---------|---------|
| Permanent notes | `Title Case.md` | `Knowledge Graphs for PKM.md` |
| Fleeting notes | `YYYYMMDDHHMMSS Title.md` | `20260324213500 Quick thought on graphs.md` |
| Daily notes | `YYYY-MM-DD.md` | `2026-03-24.md` |
| MOCs | `Topic MOC.md` | `Knowledge Graphs MOC.md` |
| Projects | `Project Name.md` | `beestgraph.md` |
| Captured content | `Slug from title.md` | `building-knowledge-graphs-at-scale.md` |

### Tags

- Lowercase, hyphenated: `knowledge-graphs`, `ai-ml`
- Prefixed for categories: `type/article`, `status/active`, `project/beestgraph`
- No spaces, no special characters

### Links

- Always use `[[Title]]` format, not file paths
- For disambiguation: `[[Title|Display Text]]`
- Link to MOCs explicitly in frontmatter `mocs:` field

---

## Migration Plan

### Phase 1: Schema update (non-breaking)
- Add new frontmatter fields to templates
- Update FalkorDB schema with new properties and indexes
- Update classifier to populate new fields
- Update qualification pipeline to enforce new schema

### Phase 2: Folder restructure
- Rename folders (add number prefixes)
- Move templates to `00-meta/templates/`
- Create `03-fleeting/` directory
- Update watcher, vault manager, and all path references

### Phase 3: MOC creation
- Create starter MOCs
- Add MOC node type to FalkorDB
- Update ingester to create MOC relationships
- Backfill existing notes with MOC links

### Phase 4: Existing note migration
- Backfill frontmatter on existing notes
- Re-classify existing documents with new schema
- Update FalkorDB with new properties
- Verify all notes have Zettelkasten IDs

---

## Open Questions

1. **Should fleeting notes auto-expire?** If a fleeting note isn't graduated in 30 days, should it auto-archive?
2. **MOC auto-generation?** Should beestgraph auto-create/update MOCs based on topic clustering in the graph?
3. **Dataview compatibility?** The frontmatter schema should work with Obsidian's Dataview plugin — verify field types.
4. **Attachment handling?** Should PDFs and images go in `09-attachments/` or alongside their note?
5. **Multi-vault?** Should work and personal be separate vaults or same vault with PARA separation?
