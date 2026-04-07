# beestgraph

> AI-augmented personal knowledge graph — self-hosted on a Raspberry Pi 5

## Project overview

beestgraph turns bookmarks, articles, notes, and feeds into a queryable knowledge graph. It runs on a Raspberry Pi 5 (16GB, NVMe SSD) behind Tailscale VPN, using FalkorDB as the graph database, keep.md for multi-source capture, Obsidian for deep note-taking, and Claude Code as the AI processing agent.

This is an open-source project. All code must be clean, well-documented, and ready for public GitHub.

## Engineering standards (non-negotiable)

This project follows strict professional software engineering practices. Every file, directory, and line of code should reflect the discipline of a well-run engineering organization.

### Code quality

- **No dead code.** Remove unused imports, variables, functions, and files immediately. Do not comment out code "for later."
- **No placeholder or stub implementations** unless explicitly marked with `# TODO(username): reason` and tracked in an issue.
- **Single responsibility.** Every module, class, and function does one thing. If a docstring needs "and" to describe what it does, split it.
- **Explicit over implicit.** No magic strings, no hardcoded values, no hidden coupling between modules. Constants go in a dedicated module or config.
- **Defensive at boundaries, trusting internally.** Validate all external input (user input, API responses, file contents). Internal function calls between trusted modules do not need redundant validation.
- **Error messages are actionable.** Every raised exception or logged error must tell the reader what happened, why, and what to do about it.

### Directory and file organization

- **Mirror the architecture.** The directory tree must reflect the system's logical layers. A new contributor should understand the architecture just by reading `tree -L 3`.
- **No orphan files.** Every file belongs in a purposeful directory. No loose scripts, configs, or modules at the repo root unless they are standard (Makefile, pyproject.toml, etc.).
- **No god modules.** If a file exceeds ~300 lines, it likely needs to be split. If a directory has more than ~10 files, it likely needs subdirectories.
- **`__init__.py` files are intentional.** They define the public API of a package via explicit `__all__` exports. They are not empty placeholders.
- **Test structure mirrors source.** `tests/` replicates the `src/` directory tree exactly. `src/pipeline/ingester.py` → `tests/pipeline/test_ingester.py`.

### Process discipline

- **Every PR must be reviewable.** Small, focused changes with clear commit messages. No 1000-line "initial implementation" dumps.
- **Dependencies are justified.** Do not add a package for something achievable in <20 lines of standard library code. Pin versions.
- **Configuration has one source of truth.** `config/beestgraph.yml` with env var overrides. No scattered `.env` files or inline defaults that diverge.
- **Logging is structured and leveled.** DEBUG for development tracing, INFO for operational events, WARNING for recoverable issues, ERROR for failures requiring attention.

## Architecture

Four layers, each with clear boundaries:

1. **Capture** — keep.md (browser/mobile/X/RSS/YouTube/GitHub/email) + Obsidian Web Clipper + manual notes
2. **Processing** — Claude Code headless agent + cron poller + watchdog daemon + 3 MCP servers
3. **Storage** — FalkorDB (Docker) + Obsidian vault (NVMe) + Syncthing
4. **Access** — FalkorDB Browser (:3000) + beestgraph Web UI (:3001) + Telegram bot + SSH+tmux

System diagram: `docs/diagrams/beestgraph-system.svg`

## Tech stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language (pipeline) | Python | 3.11+ |
| Language (web UI) | TypeScript | 5.x |
| Web framework | Next.js | 15.x |
| Graph database | FalkorDB | latest (Docker, ARM64) |
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

Full specification: `docs/beestgraph-template-spec.md` (Sections 12–13)

### Node types

```cypher
(:Document {
  uid: STRING,            -- YYYYMMDDHHMM, primary key (immutable)
  path: STRING,           -- vault path relative to root
  title: STRING,
  type: STRING,           -- see Type Registry (spec §8)
  status: STRING,         -- inbox | processing | published | archived | draft
  para: STRING,           -- projects | areas | resources | archives
  importance: INT,        -- 1-5
  confidence: FLOAT,      -- 0.0-1.0
  content_stage: STRING,  -- fleeting | literature | evergreen | reference
  summary: STRING,        -- AI-generated 2-3 sentence summary
  source_type: STRING,    -- keepmd | obsidian_clipper | manual | api | agent
  source_url: STRING,
  source_via: STRING,
  source_context: STRING,
  source_content_hash: STRING,
  created: STRING,        -- ISO 8601 date
  captured: STRING,       -- when info was encountered
  processed: STRING,      -- ISO 8601 datetime (last agent pass)
  modified: STRING,       -- last human edit
  published: STRING,      -- source publication date
  event_date: STRING,     -- for meetings/events
  due: STRING,            -- for projects
  reviewed: STRING,       -- last human re-evaluation
  last_synthesis: STRING, -- last graph coherence check
  expires: STRING,        -- knowledge expiration
  archived: STRING,       -- archival timestamp
  engagement_status: STRING, -- unread | read | reference
  rating: INT,            -- 1-5
  epistemic_effort: STRING, -- casual | moderate | thorough
  lat: FLOAT,
  lon: FLOAT,
  location_name: STRING,
  has_media: BOOLEAN,
  cluster: INT,           -- community detection (auto-computed)
  pinned: BOOLEAN,
  hidden: BOOLEAN,
  color_override: STRING,
  version: INT
})

(:Tag { name: STRING, normalized_name: STRING })
(:Topic { name: STRING, level: INT })
(:Person { name: STRING, normalized_name: STRING })
(:Concept { name: STRING, normalized_name: STRING, description: STRING })
(:Organization { name: STRING, normalized_name: STRING })
(:Tool { name: STRING, normalized_name: STRING, url: STRING })
(:Place { name: STRING, normalized_name: STRING, lat: FLOAT, lon: FLOAT })
(:Source { url: STRING, domain: STRING, name: STRING })
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
(Place)-[:LOCATED_IN]->(Place)
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

## MCP servers

Three MCP servers are configured in `config/mcp.json`:

1. **keep.md** (`https://keep.md/mcp`) — Capture intake. Tools: `list_inbox`, `get_item`, `mark_done`, `search_items`, `save_item`, `update_item`, `add_source`, `remove_source`, `list_sources`, `get_stats`, `whoami`, `list_items`.
2. **Filesystem** (local stdio) — Vault read/write. Tools: `read_file`, `write_file`, `list_directory`, `search_files`.
3. **FalkorDB** (local stdio) — Direct Cypher queries. Natural language to Cypher translation.

## Processing pipeline

### Stream 1: keep.md (cron, every 15 minutes)

```
cron → scripts/process-keepmd.sh → python -m src.pipeline.keepmd_poller
  → keep.md MCP: list_inbox
  → for each item: get_item → extract → categorize → summarize
  → filesystem MCP: write_file (formal markdown to vault)
  → FalkorDB: ingest document subgraph
  → keep.md MCP: mark_done
```

### Stream 2: Obsidian vault (real-time watchdog)

```
watchdog (inotify on ~/vault/inbox/) → triggers processor
  → filesystem MCP: read_file
  → extract → categorize → summarize
  → filesystem MCP: write_file (move to proper vault location)
  → FalkorDB: ingest document subgraph
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

Full specification: `docs/beestgraph-template-spec.md`
Canonical template: `config/templates/universal.md`

The template uses a **3-tier system**: Tier 1 (universal, mandatory on every document), Tier 2 (type-conditional), Tier 3 (advanced, add when earned). The `type` field is the master key that determines which Tier 2 fields apply — see the Type Registry in the spec (§8).

### Tier 1 fields (every document, all mandatory)

`uid`, `title`, `type`, `tags`, `status`, `dates.created`, `dates.captured`, `dates.processed`, `dates.modified`, `source.type`

### Minimum viable document (human creates this)

```yaml
---
title: "Quick thought about X"
type: note
---
The content goes here.
```

### Agent-expanded result (after processing)

```yaml
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
source:
  type: manual
para: resources
topics:
  - meta/pkm
content_stage: fleeting
summary: "..."
version: 1
---
The content goes here.

## Connections

(none identified)
```

### Critical convention: wikilink mirroring

Every entry in `connections.*` frontmatter fields **must** also appear as an inline wikilink in a `## Connections` section at the end of the body. Obsidian does not index frontmatter link fields for backlinks — the body mirror is what makes connections visible in the graph view.

### Agent processing rules

1. **Tier 1 fields are mandatory** — missing Tier 1 after processing is a bug
2. **`uid` is immutable** — never overwrite an existing uid
3. **`dates.captured` is preserved** — never overwrite once set
4. **`dates.processed` updates every pass** — ISO 8601 datetime with Z
5. **Use MERGE not CREATE** — all graph writes are idempotent
6. **Prefer omit over guess** — missing = "not yet known", wrong = metadata pollution
7. **Entity names are normalized** — `lower(strip(name))` for dedup, match existing before creating

## Key dependencies

### Python (pyproject.toml)

```
falkordb >= 1.0
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
make docker-up        # docker compose up -d (FalkorDB)
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
- **Graceful failure**: If Claude Code or any MCP server is unreachable, queue items stay unprocessed. Never lose data.
- **Logging**: Every processing step logs: item ID, source, processing time, entities extracted, graph nodes created.
