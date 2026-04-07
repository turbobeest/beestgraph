# beestgraph — System Documentation

> LLM-agnostic documentation for the beestgraph knowledge graph system.
> Any language model reading this file should understand the system
> completely without additional context.

---

## 1. What beestgraph Is

beestgraph is a self-hosted, AI-augmented personal knowledge graph. It
runs on a Raspberry Pi 5 (16 GB RAM, NVMe SSD) behind a Tailscale VPN
and turns bookmarks, articles, notes, and feeds into a queryable graph.

**Core components:**

- **FalkorDB** — graph database (Docker, ARM64, port 6379)
- **Obsidian vault** — markdown notes with structured frontmatter
- **keep.md** — multi-source capture (browser, mobile, RSS, X, YouTube,
  GitHub, email)
- **`bg` CLI** — unified command-line interface for all operations
- **Telegram bot** — mobile notification and review interface
- **Web UI** — Next.js graph visualisation (port 3001)

**Design principle:** The vault and graph are fully functional with zero
AI running. Every feature works at three levels: manual (human edits
files and runs Cypher), script (`bg` commands do the mechanical work),
and agent (an LLM adds reasoning on top of script output). The AI never
owns the data model.

---

## 2. System Architecture

### Infrastructure Layers

```
┌──────────────────────────────────────────────────────────────────┐
│ CAPTURE                                                          │
│ keep.md │ Obsidian Web Clipper │ Manual notes │ Telegram /add    │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│ PROCESSING                                                       │
│ Inbox watchdog → Full pipeline (parse → classify → format →      │
│ security scan → privacy → queue → ingest)                        │
│ LLMAgent interface (Anthropic default, Ollama/OpenAI optional)   │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│ STORAGE                                                          │
│ FalkorDB (UID-keyed, schema v5) │ Obsidian vault (NVMe, Syncthing)│
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│ ACCESS                                                           │
│ Telegram bot │ Web UI :3001 │ FalkorDB Browser :3000             │
│ SSH + bg CLI │ Graph API                                         │
└──────────────────────────────────────────────────────────────────┘
```

### Functional Layers

```
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 4: Automation — "The vault maintains itself"               │
│ Scheduled: morning-brief, nightly-close, health-check, backup    │
│ Event-driven: on-file-change (graph sync), on-commit             │
├──────────────────────────────────────────────────────────────────┤
│ LAYER 3: Context Engine — "The vault knows you"                  │
│ bg context --level 0/1/2/3 │ identity.md at vault root           │
├──────────────────────────────────────────────────────────────────┤
│ LAYER 2: Thinking Tools — "The vault thinks with you"            │
│ bg think challenge/emerge/connect/graduate/forecast/audit         │
│ All backed by FalkorDB Cypher; LLM optional for synthesis        │
├──────────────────────────────────────────────────────────────────┤
│ LAYER 1: Vault Operations — "The vault remembers"                │
│ bg daily/task/find/project/health/init/capture/save/export/      │
│ archive/ingest                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Vault Structure

The vault lives at `~/vault/` and uses numbered PARA directories plus
three additional directories for entities, raw captures, and synthesis.

```
~/vault/
├── 00-meta/            Meta: templates, MOCs, task lists
├── 01-inbox/           New captures land here (watcher monitors this)
├── 02-queue/           Qualification queue (pending human review)
├── 03-fleeting/        Fleeting notes, saved extracts
├── 04-daily/           Daily notes (YYYY-MM-DD.md)
├── 05-projects/        Active projects (one dir per project)
├── 06-areas/           Ongoing responsibilities
├── 07-resources/       Processed articles organised by topic
├── 08-archive/         Completed / inactive documents
├── 09-attachments/     Binary files, images
├── entities/           Entity pages (people/, organizations/, tools/,
│                       concepts/, places/)
├── raw/                Immutable source captures (articles/,
│                       transcripts/, pdfs/)
├── index.md            Auto-maintained vault index
└── log.md              Auto-maintained activity log
```

---

## 4. Frontmatter Specification

Every markdown file uses structured YAML frontmatter. The canonical
specification lives in `docs/planning/beestgraph-template.md`.

**Key rules:**

- `uid` is the immutable primary key (YYYYMMDDHHMMSS format)
- `uid` is never overwritten once set
- `dates.captured` is preserved — never overwrite once set
- `dates.processed` updates every agent pass (ISO 8601 with Z)
- All graph writes use MERGE (idempotent)
- Missing fields mean "not yet known" — do not guess

**Tier 1 fields (mandatory on every document):**
`uid`, `title`, `type`, `tags`, `status`, `dates.created`,
`dates.captured`, `dates.processed`, `dates.modified`, `source.type`

**Minimum viable document (human creates):**

```yaml
---
title: "Quick thought about X"
type: note
---
Content here.
```

The pipeline fills in remaining Tier 1 fields during processing.

---

## 5. Graph Schema

**Database:** FalkorDB, graph name: `beestgraph`, schema version: 5

### Node Types

```
(:Document {uid, path, title, type, status, para, importance,
            confidence, content_stage, summary, source_type, source_url,
            author, created, captured, processed, modified, published,
            engagement_status, content, key_claims, ...})
(:Tag {name, normalized_name})
(:Topic {name, level})
(:Person {name, normalized_name})
(:Concept {name, normalized_name, description})
(:Organization {name, normalized_name})
(:Tool {name, normalized_name, url})
(:Place {name, normalized_name})
(:Source {url, domain, name})
```

### Relationship Types

```
(Document)-[:LINKS_TO]->(Document)           Inline wikilinks
(Document)-[:TAGGED_WITH]->(Tag)
(Document)-[:BELONGS_TO]->(Topic)
(Document)-[:MENTIONS {confidence}]->(Person|Concept|Organization|Tool|Place)
(Document)-[:DERIVED_FROM]->(Source)
(Document)-[:SUPPORTS {weight}]->(Document)
(Document)-[:CONTRADICTS {weight}]->(Document)
(Document)-[:EXTENDS]->(Document)
(Document)-[:SUPERSEDES]->(Document)
(Document)-[:INSPIRED_BY]->(Document)
(Document)-[:RELATED_TO {weight}]->(Document)
(Document)-[:CHILD_OF]->(Document)           From up: field
(Topic)-[:SUBTOPIC_OF]->(Topic)
```

### Indexes

Range indexes exist on: `Document.uid`, `Document.path`,
`Document.type`, `Document.status`, `Document.para`,
`Document.importance`, `Document.created`, `Document.captured`,
`Document.modified`, `Tag.normalized_name`, `Topic.name`,
`Person.normalized_name`, `Concept.normalized_name`,
`Organization.normalized_name`, `Tool.normalized_name`,
`Place.normalized_name`, `Source.url`.

Full-text indexes: `Document(title, summary)`, `Document(key_claims)`,
`Tag(name)`, `Concept(name, description)`, `MOC(name, description)`.

---

## 6. The `bg` CLI

Installed as a script entry point: `bg = src.cli.main:app` (Typer).

### Global Flags

- `--version` — Show version
- `--agent` — Enable LLM agent enhancement (adds prose synthesis)

### Layer 1: Vault Operations

| Command | Description |
|---------|-------------|
| `bg daily` | Create/open today's daily note |
| `bg task <title>` | Add a task (--project, --priority, --due) |
| `bg find <query>` | Full-text graph search (--type, --limit, --json) |
| `bg project <name>` | Project status from vault + graph |
| `bg health` | System health report (services, graph, disk) |
| `bg init` | Bootstrap vault directories (entities/, raw/) |
| `bg capture <text>` | Quick capture to inbox (--title, --tags) |
| `bg save <text>` | Extract action items and decisions |
| `bg export` | Export vault as JSON (--flat, --output) |
| `bg archive <slug>` | Archive a document (--reason) |
| `bg ingest <url>` | Ingest URL or file through pipeline |
| `bg migrate` | Vault migration (--dry-run, --uid-only, --write) |

### Layer 2: Thinking Tools

| Command | Description |
|---------|-------------|
| `bg think challenge <topic>` | Surface counter-evidence |
| `bg think emerge` | Detect trending patterns (--period) |
| `bg think connect <A> <B>` | Find paths between concepts |
| `bg think graduate <idea>` | Context for promoting to permanent |
| `bg think forecast <topic>` | Frequency timeline and trends |
| `bg think audit <claim>` | Verify against supporting/contradicting evidence |

### Two-Path Contract

Every command implements:
```
run_without_agent(**kwargs) -> Result   # Always works, no LLM
run_with_agent(agent, **kwargs) -> Result  # LLM-enhanced (optional)
```

---

## 7. Key File Locations and Ports

| Resource | Location |
|----------|----------|
| Repo root | `~/beestgraph/` |
| Vault | `~/vault/` |
| Config | `~/beestgraph/config/beestgraph.yml` |
| Agent config | `~/beestgraph/config/agent.toml` |
| Python source | `~/beestgraph/src/` |
| Tests | `~/beestgraph/tests/` |
| Planning docs | `~/beestgraph/docs/planning/` |
| FalkorDB | `localhost:6379` (Docker) |
| FalkorDB Browser | `http://localhost:3000` |
| Web UI | `http://localhost:3001` |
| Radicale (CalDAV) | `http://localhost:5232` |

### Systemd Services

| Service | Purpose |
|---------|---------|
| `beestgraph-watcher` | Monitors `~/vault/01-inbox/` for new .md files |
| `beestgraph-bot` | Telegram bot for mobile review |
| `beestgraph-heartbeat` | Periodic health checks |
| `beestgraph-web` | Next.js web UI |

---

## 8. Querying FalkorDB

All queries run via `redis-cli` or the Python `falkordb` client.

```bash
# Count all nodes
redis-cli -p 6379 GRAPH.QUERY beestgraph "MATCH (n) RETURN count(n)"

# Count documents
redis-cli -p 6379 GRAPH.QUERY beestgraph \
  "MATCH (d:Document) RETURN count(d)"

# Find documents by topic
redis-cli -p 6379 GRAPH.QUERY beestgraph \
  "MATCH (d:Document)-[:BELONGS_TO]->(tp:Topic {name: 'technology/ai-ml'}) \
   RETURN d.title, d.path"

# Full-text search
redis-cli -p 6379 GRAPH.QUERY beestgraph \
  "CALL db.idx.fulltext.queryNodes('Document', 'knowledge graph') \
   YIELD node, score RETURN node.title, score ORDER BY score DESC"

# Find orphan documents (no relationships)
redis-cli -p 6379 GRAPH.QUERY beestgraph \
  "MATCH (d:Document) WHERE NOT (d)--() RETURN d.title, d.path"
```

---

## 9. Running Tests

```bash
cd ~/beestgraph

uv run pytest                        # All tests
uv run pytest tests/pipeline/        # Pipeline tests only
uv run pytest tests/cli/             # CLI tests only
uv run pytest tests/graph/           # Graph tests only
uv run ruff check src/               # Linting
```

---

## 10. Restarting Services

```bash
# Check status
sudo systemctl status beestgraph-watcher
sudo systemctl status beestgraph-bot
sudo systemctl status beestgraph-heartbeat
sudo systemctl status beestgraph-web

# Restart a service
sudo systemctl restart beestgraph-watcher

# View logs
sudo journalctl -u beestgraph-watcher -f --no-pager
```

Always run tests before restarting a service to avoid deploying broken
code. If a restart fails, roll back: `cd ~/beestgraph && git checkout HEAD~1`.
