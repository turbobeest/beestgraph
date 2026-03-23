# beestgraph

> AI-augmented personal knowledge graph — self-hosted on a Raspberry Pi 5

## Project overview

beestgraph turns bookmarks, articles, notes, and feeds into a queryable knowledge graph. It runs on a Raspberry Pi 5 (16GB, NVMe SSD) behind Tailscale VPN, using FalkorDB as the graph database, Graphiti for temporal knowledge graph management, keep.md for multi-source capture, Obsidian for deep note-taking, and Claude Code as the AI processing agent.

This is an open-source project. All code must be clean, well-documented, and ready for public GitHub.

## Architecture

Four layers, each with clear boundaries:

1. **Capture** — keep.md (browser/mobile/X/RSS/YouTube/GitHub/email) + Obsidian Web Clipper + manual notes
2. **Processing** — Claude Code headless agent + cron poller + watchdog daemon + 4 MCP servers
3. **Storage** — FalkorDB (Docker) + Graphiti (Docker) + Obsidian vault (NVMe) + Syncthing
4. **Access** — FalkorDB Browser (:3000) + beestgraph Web UI (:3001) + Telegram bot + SSH+tmux

System diagram: `docs/diagrams/beestgraph-system.svg`

## Tech stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language (pipeline) | Python | 3.11+ |
| Language (web UI) | TypeScript | 5.x |
| Web framework | Next.js | 15.x |
| Graph database | FalkorDB | latest (Docker, ARM64) |
| KG framework | Graphiti (Zep) | latest |
| Graph viz | Cytoscape.js | 3.x |
| File watching | watchdog (Python) | 4.x |
| Telegram bot | aiogram | 3.x |
| Container runtime | Docker + Compose | latest |
| VPN | Tailscale | latest |
| Note sync | Syncthing | latest |

## Repository structure

```
beestgraph/
├── CLAUDE.md                  # THIS FILE — agent context
├── README.md                  # Public-facing docs
├── .claude/
│   └── agents/                # Subagent definitions
├── agent/
│   ├── skills/                # Claude Code skill files
│   └── prompts/               # Prompt templates for processing
├── src/
│   ├── pipeline/              # Capture → process → ingest
│   ├── graph/                 # Schema, queries, maintenance
│   ├── vault/                 # Obsidian vault management
│   ├── bot/                   # Telegram bot
│   └── web/                   # Next.js web UI
├── docker/                    # Compose files + configs
├── scripts/                   # Setup & automation scripts
├── config/                    # Config templates
├── tests/                     # Mirrors src/ structure
└── docs/                      # Architecture, guides, diagrams
```

## Coding standards

### Python

- **Formatter**: ruff format (line length 100)
- **Linter**: ruff check with default rules + I (isort), UP (pyupgrade), S (bandit security)
- **Type hints**: Required on all public functions and methods. Use `from __future__ import annotations`.
- **Docstrings**: Google style on all public modules, classes, and functions.
- **Async**: Prefer async/await for I/O-bound operations (FalkorDB client, HTTP calls, file I/O). Use `asyncio` event loop.
- **Error handling**: Never bare `except:`. Catch specific exceptions. Log with `structlog`.
- **Config**: Load from `config/beestgraph.yml` with env var overrides. Use pydantic `BaseSettings`.
- **Tests**: pytest + pytest-asyncio. Minimum coverage target: 80% on `src/`.
- **Imports**: Standard lib → third-party → local, each separated by a blank line.

### TypeScript / Next.js (web UI)

- **Formatter**: prettier
- **Linter**: eslint with next/core-web-vitals
- **Styling**: Tailwind CSS utility classes. No custom CSS files except for Cytoscape.js overrides.
- **Components**: Functional components with hooks. No class components.
- **State**: React hooks (useState, useReducer) for local state. Server components where possible.
- **API routes**: Next.js Route Handlers in `src/web/src/app/api/`.

### General

- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).
- **Branch naming**: `feat/description`, `fix/description`, `docs/description`.
- **No secrets in code**: All sensitive values via environment variables or `.env` files (gitignored).
- **Logging**: structlog for Python, console for TypeScript. Structured JSON in production.
- **File naming**: Python: `snake_case.py`. TypeScript: `PascalCase.tsx` for components, `camelCase.ts` for utilities.

## Graph schema

FalkorDB graph name: `beestgraph`

### Node types

```cypher
(:Document {
  path: STRING,           -- vault path relative to root
  title: STRING,
  content: STRING,        -- full markdown body (for full-text search)
  summary: STRING,        -- AI-generated 2-3 sentence summary
  status: STRING,         -- inbox | processing | published | archived
  para_category: STRING,  -- projects | areas | resources | archives
  source_type: STRING,    -- keepmd | obsidian_clipper | manual
  source_url: STRING,
  created_at: STRING,     -- ISO 8601
  updated_at: STRING,
  processed_at: STRING
})

(:Tag { name: STRING, normalized_name: STRING })
(:Topic { name: STRING, level: INT })
(:Person { name: STRING, normalized_name: STRING })
(:Concept { name: STRING, normalized_name: STRING, description: STRING })
(:Source { url: STRING, domain: STRING, name: STRING })
(:Project { name: STRING, status: STRING, description: STRING })
```

### Relationship types

```cypher
(Document)-[:LINKS_TO]->(Document)
(Document)-[:TAGGED_WITH]->(Tag)
(Document)-[:BELONGS_TO]->(Topic)
(Document)-[:MENTIONS {confidence: FLOAT, context: STRING}]->(Person|Concept)
(Document)-[:DERIVED_FROM]->(Source)
(Topic)-[:SUBTOPIC_OF]->(Topic)
(Document)-[:SUPPORTS]->(Document)
(Document)-[:CONTRADICTS]->(Document)
(Document)-[:SUPERSEDES]->(Document)
```

### Indexes

```cypher
CREATE INDEX FOR (d:Document) ON (d.path)
CREATE INDEX FOR (d:Document) ON (d.source_url)
CREATE INDEX FOR (d:Document) ON (d.status)
CREATE INDEX FOR (t:Tag) ON (t.normalized_name)
CREATE INDEX FOR (tp:Topic) ON (tp.name)
CREATE INDEX FOR (p:Person) ON (p.normalized_name)
CREATE INDEX FOR (c:Concept) ON (c.normalized_name)
CALL db.idx.fulltext.createNodeIndex('Document', 'title', 'content', 'summary')
```

## MCP servers

Four MCP servers are configured in `config/mcp.json`:

1. **keep.md** (`https://keep.md/mcp`) — Capture intake. Tools: `list_inbox`, `get_item`, `mark_done`, `search_items`, `save_item`, `update_item`, `add_source`, `remove_source`, `list_sources`, `get_stats`, `whoami`, `list_items`.
2. **Graphiti** (local SSE) — Knowledge graph operations. Tools: `add_episode`, `search_facts`, `search_nodes`, `get_episodes`.
3. **Filesystem** (local stdio) — Vault read/write. Tools: `read_file`, `write_file`, `list_directory`, `search_files`.
4. **FalkorDB** (local stdio) — Direct Cypher queries. Natural language to Cypher translation.

## Processing pipeline

### Stream 1: keep.md (cron, every 15 minutes)

```
cron → scripts/process-keepmd.sh → claude -p (headless)
  → keep.md MCP: list_inbox
  → for each item: get_item → extract → categorize → summarize
  → filesystem MCP: write_file (formal markdown to vault)
  → graphiti MCP: add_episode
  → keep.md MCP: mark_done
```

### Stream 2: Obsidian vault (real-time watchdog)

```
watchdog (inotify on ~/vault/inbox/) → triggers processor
  → filesystem MCP: read_file
  → extract → categorize → summarize
  → filesystem MCP: write_file (move to proper vault location)
  → graphiti MCP: add_episode
```

## Taxonomy (starter)

```yaml
topics:
  - technology:
    - programming
    - ai-ml
    - infrastructure
    - security
    - web
  - science:
    - physics
    - biology
    - mathematics
  - business:
    - startups
    - finance
    - marketing
  - culture:
    - books
    - film
    - music
    - history
  - health:
    - fitness
    - nutrition
    - mental-health
  - personal:
    - journal
    - goals
    - relationships
  - meta:
    - pkm
    - tools
    - workflows
```

## Vault structure

```
~/vault/
├── inbox/              ← watchdog monitors; new captures land here
├── knowledge/          ← processed articles organized by topic
│   ├── technology/
│   ├── science/
│   ├── business/
│   └── .../
├── projects/           ← PARA: active projects
├── areas/              ← PARA: ongoing responsibilities
├── resources/          ← PARA: reference material
├── archives/           ← PARA: completed/inactive
└── templates/          ← frontmatter templates
```

## Markdown frontmatter template

Every processed document gets this frontmatter:

```yaml
---
title: "Article Title"
source_url: "https://..."
source_type: keepmd | obsidian_clipper | manual
author: "Author Name"
date_published: 2026-01-15
date_captured: 2026-01-16T10:30:00Z
date_processed: 2026-01-16T10:45:00Z
summary: "Two to three sentence AI-generated summary."
para_category: resources
topics:
  - technology/ai-ml
tags:
  - knowledge-graphs
  - falkordb
entities:
  people:
    - "Name"
  concepts:
    - "Concept"
  organizations:
    - "Org"
status: published
---
```

## Key dependencies

### Python (pyproject.toml)

```
falkordb >= 1.0
graphiti-core
watchdog >= 4.0
pyyaml >= 6.0
pydantic >= 2.0
pydantic-settings >= 2.0
structlog >= 24.0
aiogram >= 3.0
httpx >= 0.27
python-frontmatter >= 1.0
obsidiantools >= 0.15
click >= 8.0
rich >= 13.0
```

### Node.js (src/web/package.json)

```
next, react, react-dom, typescript,
cytoscape, @types/cytoscape,
tailwindcss, postcss, autoprefixer
```

## Build and run commands

```bash
# Python
make install          # Install Python deps with uv
make lint             # ruff check + ruff format --check
make test             # pytest with coverage
make run-watcher      # Start vault inbox watchdog
make run-poller       # Run keep.md poller once (cron calls this)
make run-bot          # Start Telegram bot
make run-all          # Start all Python services

# Docker
make docker-up        # docker compose up -d (FalkorDB + Graphiti)
make docker-down      # docker compose down
make docker-logs      # docker compose logs -f

# Web UI
make web-dev          # cd src/web && npm run dev
make web-build        # cd src/web && npm run build

# Setup
make setup            # Full setup (Docker, deps, schema, MCP)
make init-schema      # Create FalkorDB indexes
make backup           # Snapshot FalkorDB + vault
```

## Important conventions

- **Idempotency**: All graph writes use `MERGE` not `CREATE`. Processing the same document twice must be safe.
- **Provenance**: Every Document node preserves `source_url` and `source_type`. Never lose where something came from.
- **Normalization**: Tags and entity names get `normalized_name = lower(strip(name))` for deduplication.
- **Temporal**: Use Graphiti's `add_episode` for ingestion — it handles temporal fact tracking automatically.
- **Graceful failure**: If Claude Code or any MCP server is unreachable, queue items stay unprocessed. Never lose data.
- **Logging**: Every processing step logs: item ID, source, processing time, entities extracted, graph nodes created.
