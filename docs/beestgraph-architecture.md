# beestgraph

> AI-augmented personal knowledge graph — self-hosted on a Raspberry Pi 5

**beestgraph** turns your bookmarks, articles, notes, and feeds into a queryable knowledge graph powered by FalkorDB, Graphiti, and Claude Code. Capture from anywhere with [keep.md](https://keep.md) and [Obsidian](https://obsidian.md), let an AI agent categorize and extract entities, then explore your knowledge through a graph database, web UI, or natural language queries.

![System Architecture](docs/diagrams/beestgraph-system.svg)

---

## Features

- **Multi-source capture** — browser extension, mobile, X/Twitter, RSS, YouTube, GitHub, email (via keep.md) plus deep article clipping (via Obsidian Web Clipper)
- **AI processing pipeline** — Claude Code agent in headless mode categorizes, extracts entities, and enriches every new item automatically
- **Temporal knowledge graph** — Graphiti tracks when facts became true and when they changed, built on FalkorDB's in-memory graph engine
- **Four MCP servers** — keep.md, Graphiti, Filesystem, and FalkorDB all accessible to the agent through Model Context Protocol
- **Self-hosted** — runs entirely on a Raspberry Pi 5 (16GB) with NVMe SSD behind Tailscale VPN
- **Open Obsidian vault** — all processed knowledge lives as markdown files synced across devices via Syncthing
- **Web UI** — FalkorDB Browser for graph exploration out of the box, with a custom Next.js + Cytoscape.js frontend planned
- **Remote access** — Telegram bot for quick queries, SSH + tmux for full sessions, all over Tailscale

---

## Repository structure

```
beestgraph/
│
├── README.md                        # Project overview and quickstart
├── LICENSE                          # MIT License
├── CONTRIBUTING.md                  # Contribution guidelines
├── CHANGELOG.md                     # Release history
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── workflows/
│       ├── ci.yml                   # Lint, test, build
│       └── release.yml              # Semantic versioning + changelog
│
├── docs/
│   ├── architecture.md              # Full architecture deep-dive
│   ├── setup-guide.md               # Step-by-step Pi setup
│   ├── configuration.md             # All config options
│   ├── schema.md                    # Graph schema reference
│   ├── taxonomy.md                  # Topic taxonomy guide
│   ├── keepmd-integration.md        # keep.md setup and workflow
│   ├── obsidian-integration.md      # Obsidian vault structure and sync
│   ├── mcp-servers.md               # MCP constellation reference
│   ├── web-ui.md                    # Web interface docs
│   ├── telegram-bot.md              # Telegram bot commands
│   ├── troubleshooting.md           # Common issues and fixes
│   └── diagrams/
│       ├── beestgraph-system.dot    # System diagram source (Graphviz)
│       └── beestgraph-system.svg    # Rendered system diagram
│
├── docker/
│   ├── docker-compose.yml           # FalkorDB + Graphiti + services
│   ├── docker-compose.dev.yml       # Development overrides
│   ├── .env.example                 # Environment variable template
│   └── falkordb/
│       └── falkordb.conf            # FalkorDB configuration
│
├── agent/
│   ├── CLAUDE.md                    # Persistent agent instructions
│   ├── skills/
│   │   ├── process-keepmd-item.md   # Skill: process a keep.md inbox item
│   │   ├── process-vault-note.md    # Skill: process an Obsidian inbox note
│   │   ├── bulk-import.md           # Skill: bulk import existing vault
│   │   ├── graph-maintenance.md     # Skill: dedup, orphans, PageRank
│   │   └── research-url.md          # Skill: research a URL and ingest
│   └── prompts/
│       ├── categorize.md            # Categorization prompt template
│       ├── extract-entities.md      # Entity extraction prompt template
│       └── summarize.md             # Summarization prompt template
│
├── src/
│   ├── __init__.py
│   ├── config.py                    # Configuration loader (env + YAML)
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── watcher.py               # Vault inbox watchdog daemon
│   │   ├── keepmd_poller.py          # keep.md inbox polling (cron-friendly)
│   │   ├── processor.py             # Orchestrates Claude Code headless calls
│   │   ├── ingester.py              # FalkorDB/Graphiti ingestion logic
│   │   └── markdown_parser.py       # Frontmatter + wiki-link parser
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── schema.py                # Schema definitions and migrations
│   │   ├── queries.py               # Common Cypher query builders
│   │   └── maintenance.py           # Dedup, orphan detection, stats
│   ├── vault/
│   │   ├── __init__.py
│   │   ├── structure.py             # Vault directory management
│   │   ├── templates.py             # Markdown frontmatter templates
│   │   └── bulk_import.py           # obsidiantools-based bulk importer
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── telegram_bot.py          # Telegram bot (aiogram)
│   │   └── handlers.py              # Command handlers
│   └── web/                         # Custom web UI (Phase 4)
│       ├── package.json
│       ├── next.config.js
│       ├── src/
│       │   ├── app/
│       │   │   ├── layout.tsx
│       │   │   ├── page.tsx          # Dashboard / search
│       │   │   ├── graph/
│       │   │   │   └── page.tsx      # Graph explorer (Cytoscape.js)
│       │   │   ├── entry/
│       │   │   │   └── page.tsx      # New entry form + AI research
│       │   │   └── timeline/
│       │   │       └── page.tsx      # Temporal view
│       │   ├── components/
│       │   │   ├── GraphExplorer.tsx
│       │   │   ├── SearchBar.tsx
│       │   │   ├── EntryCard.tsx
│       │   │   └── TopicTree.tsx
│       │   └── lib/
│       │       ├── falkordb.ts       # FalkorDB client
│       │       └── graphiti.ts       # Graphiti API client
│       └── public/
│           └── beestgraph-logo.svg
│
├── scripts/
│   ├── setup.sh                     # Full Pi setup (Docker, Tailscale, deps)
│   ├── install-claude-code.sh       # Claude Code ARM64 install + workarounds
│   ├── configure-mcp.sh             # Wire up all 4 MCP servers
│   ├── init-schema.sh               # Create FalkorDB indexes and constraints
│   ├── process-keepmd.sh            # Cron wrapper for keep.md polling
│   └── backup.sh                    # FalkorDB snapshot + vault backup
│
├── config/
│   ├── beestgraph.yml.example       # Main configuration file template
│   ├── mcp.json.example             # MCP server configuration template
│   ├── taxonomy.yml                 # Default topic taxonomy
│   └── templates/
│       ├── article.md               # Frontmatter template: article
│       ├── concept.md               # Frontmatter template: concept
│       ├── project.md               # Frontmatter template: project
│       └── person.md                # Frontmatter template: person
│
├── tests/
│   ├── conftest.py
│   ├── test_pipeline/
│   │   ├── test_watcher.py
│   │   ├── test_keepmd_poller.py
│   │   ├── test_processor.py
│   │   └── test_ingester.py
│   ├── test_graph/
│   │   ├── test_schema.py
│   │   ├── test_queries.py
│   │   └── test_maintenance.py
│   └── test_vault/
│       ├── test_parser.py
│       └── test_bulk_import.py
│
├── pyproject.toml                   # Python project config (uv/pip)
├── requirements.txt                 # Pinned Python dependencies
├── requirements-dev.txt             # Dev/test dependencies
└── Makefile                         # Common tasks: setup, test, lint, run
```

---

## Architecture overview

### The four layers

| Layer | Components | Purpose |
|-------|-----------|---------|
| **Capture** | keep.md (browser/mobile/X/RSS/YouTube/GitHub/email), Obsidian Web Clipper, manual notes | Get content into the system with minimal friction |
| **Processing** | Claude Code (headless), cron poller, watchdog daemon, 4 MCP servers | AI-powered categorization, entity extraction, enrichment |
| **Storage** | FalkorDB (in-memory graph), Graphiti (temporal KG), Obsidian vault (NVMe), Syncthing | Persistent graph + markdown files synced everywhere |
| **Access** | FalkorDB Browser, beestgraph Web UI, Telegram bot, SSH+tmux, Obsidian apps | Query, explore, and manage from any device |

### Capture: two-tier system

**keep.md** ($10/mo Plus) handles broad, low-friction capture — one-click bookmarks, auto-synced X bookmarks, RSS feeds, YouTube transcripts, GitHub stars, and email forwarding. Everything is stored as clean markdown accessible via MCP server, REST API, and CLI.

**Obsidian Web Clipper** handles deep capture — full articles with highlights, annotations, and custom YAML frontmatter, saved directly into the vault's `inbox/` folder.

Both streams feed into the processing layer. Most daily captures go through keep.md; deep research goes through Obsidian.

### Processing: the AI agent

Claude Code runs on the Pi in headless mode with persistent context from `CLAUDE.md`. Two intake streams trigger processing:

1. **Cron job** (every 15 min) polls the keep.md inbox via MCP
2. **Python watchdog** monitors `~/vault/inbox/` for new markdown files in real-time

For each new item, the agent: parses content → extracts entities and topics → categorizes (PARA + taxonomy) → generates summary → writes formal markdown to the vault → ingests into Graphiti → marks the source item as processed.

Four MCP servers give the agent full capabilities:

| MCP Server | Endpoint | Key Tools |
|-----------|----------|-----------|
| **keep.md** | `https://keep.md/mcp` | `list_inbox`, `get_item`, `mark_done`, `search_items` |
| **Graphiti** | local SSE | `add_episode`, `search_facts`, `search_nodes` |
| **Filesystem** | local stdio | `read_file`, `write_file`, `list_directory` |
| **FalkorDB** | local stdio | Natural language → Cypher, raw queries |

### Storage: dual persistence

**FalkorDB** (via Docker) holds the knowledge graph in memory with GraphBLAS sparse matrices. Supports OpenCypher queries, full-text search (RediSearch), and vector indexes for semantic similarity. Graphiti adds temporal fact tracking on top.

**Obsidian vault** (on NVMe) stores all processed knowledge as markdown files with frontmatter. Syncthing syncs the vault P2P across all your devices.

### Access: query from anywhere

All access goes through **Tailscale** (WireGuard mesh VPN). FalkorDB Browser on `:3000`, the custom web UI on `:3001`, Telegram bot for mobile queries, SSH+tmux for interactive Claude Code sessions, and Obsidian desktop/mobile apps for the vault.

---

## Hardware requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Board | Raspberry Pi 5 8GB | **Raspberry Pi 5 16GB** |
| Storage | 256GB NVMe SSD | **1-2TB NVMe SSD** |
| Cooling | Passive heatsink | **Active cooling (fan)** |
| Network | Any broadband | **Symmetric fiber (FiOS)** |
| Power | Official 27W PSU | Official 27W PSU |

Enable PCIe Gen 3 for maximum NVMe performance:
```bash
# /boot/firmware/config.txt
dtparam=pciex1_gen=3
```

---

## Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/terbeest/beestgraph.git
cd beestgraph

# 2. Copy and edit configuration
cp config/beestgraph.yml.example config/beestgraph.yml
cp docker/.env.example docker/.env
# Edit both files with your API keys and preferences

# 3. Run the setup script (installs Docker, Tailscale, Python deps)
chmod +x scripts/setup.sh
./scripts/setup.sh

# 4. Start the services
cd docker && docker compose up -d

# 5. Install Claude Code and configure MCP servers
./scripts/install-claude-code.sh
./scripts/configure-mcp.sh

# 6. Initialize the graph schema
./scripts/init-schema.sh

# 7. Start the processing pipeline
make run

# 8. Open FalkorDB Browser
# Visit http://beestgraph:3000 (via Tailscale) or http://localhost:3000
```

---

## Configuration

### Environment variables

```bash
# docker/.env
ANTHROPIC_API_KEY=sk-ant-...
FALKORDB_HOST=localhost
FALKORDB_PORT=6379
KEEPMD_API_KEY=...              # Optional: for REST API polling
TELEGRAM_BOT_TOKEN=...          # Optional: for Telegram bot
TELEGRAM_ALLOWED_USERS=12345    # Your Telegram user ID
VAULT_PATH=/home/pi/vault
```

### MCP servers

```json
// config/mcp.json
{
  "mcpServers": {
    "keep": {
      "transport": "http",
      "url": "https://keep.md/mcp"
    },
    "graphiti": {
      "command": "graphiti-mcp-server",
      "args": ["--transport", "sse"],
      "env": {
        "FALKORDB_HOST": "localhost",
        "FALKORDB_PORT": "6379"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${VAULT_PATH}"]
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

---

## Graph schema

Starting schema — designed to grow organically:

```cypher
// Core node types
CREATE INDEX FOR (d:Document) ON (d.path)
CREATE INDEX FOR (d:Document) ON (d.source_url)
CREATE INDEX FOR (t:Tag) ON (t.normalized_name)
CREATE INDEX FOR (tp:Topic) ON (tp.name)
CREATE INDEX FOR (p:Person) ON (p.normalized_name)
CREATE INDEX FOR (c:Concept) ON (c.normalized_name)

// Full-text search
CALL db.idx.fulltext.createNodeIndex('Document', 'title', 'content', 'summary')
CALL db.idx.fulltext.createNodeIndex('Tag', 'name')

// Document properties:
//   path, title, content, summary, status, para_category,
//   source_type (keepmd | obsidian_clipper | manual),
//   source_url, created_at, updated_at, processed_at

// Relationships:
//   (Document)-[:LINKS_TO]->(Document)
//   (Document)-[:TAGGED_WITH]->(Tag)
//   (Document)-[:BELONGS_TO]->(Topic)
//   (Document)-[:MENTIONS {confidence, context}]->(Person|Concept)
//   (Document)-[:DERIVED_FROM]->(Source)
//   (Topic)-[:SUBTOPIC_OF]->(Topic)
//   (Document)-[:SUPPORTS|CONTRADICTS|SUPERSEDES]->(Document)
```

---

## Roadmap

- [x] Architecture design and research
- [ ] **Phase 1:** Pi foundation — Docker, FalkorDB, Tailscale, keep.md, Obsidian sync
- [ ] **Phase 2:** Ingestion pipeline — Claude Code + MCP servers + watchdog + cron
- [ ] **Phase 3:** Bulk import + taxonomy refinement + Telegram bot
- [ ] **Phase 4:** Custom web UI with graph explorer, search, and AI-powered entry creation
- [ ] **Phase 5:** Community — plugin system, additional MCP servers, alternative LLM support

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. We welcome contributions across all layers — from capture integrations to graph queries to web UI components.

---

## License

[MIT](LICENSE)
