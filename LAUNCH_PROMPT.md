# beestgraph — Claude Code Launch Prompt
#
# USAGE:
#   cd ~/beestgraph
#   claude
#   (paste the prompt below)
#
# This prompt initializes the full project build using parallel Opus 4.6
# subagents. Each agent works on an independent track with no file conflicts.
# ────────────────────────────────────────────────────────────────────────

You are launching the initial build of **beestgraph**, an open-source AI-augmented personal knowledge graph system. The CLAUDE.md, scaffolding scripts, Makefile, pyproject.toml, Docker Compose, agent definitions, and system architecture diagram are already in place.

Read CLAUDE.md thoroughly first — it contains the full architecture, coding standards, schema, and conventions.

## Build plan

Execute the following **5 parallel tracks** using subagents. Each track targets different directories with no overlap, so they can run simultaneously. Use Opus 4.6 for all agents. After all agents complete, do a final integration pass.

### Track 1 → `infrastructure` agent
**Directory scope:** `docker/`, `scripts/`, `config/`, root config files

Tasks:
1. Review and finalize `docker/docker-compose.yml` — verify Graphiti image tag, health checks, ARM64 compatibility. Add a `docker-compose.dev.yml` with debug ports and volume mounts for live code reload.
2. Create `scripts/backup.sh` — FalkorDB RDB snapshot + rsync vault to a backup directory. Include rotation (keep last 7 daily backups).
3. Create `scripts/process-keepmd.sh` — cron wrapper that sources .env, runs the keep.md poller, and logs output. Include a lockfile to prevent overlapping runs.
4. Create `config/beestgraph.yml.example` — YAML config file with all settings (vault path, FalkorDB host/port, polling interval, log level, taxonomy path, Telegram settings). Use comments explaining each option.
5. Create `config/mcp.json.example` — the full MCP server config template.
6. Create `config/taxonomy.yml` — the starter topic taxonomy from CLAUDE.md in YAML format.
7. Create systemd unit files: `config/systemd/beestgraph-watcher.service` and `config/systemd/beestgraph-bot.service`.
8. Create `config/templates/article.md`, `concept.md`, `project.md`, `person.md` — frontmatter templates.

### Track 2 → `pipeline` agent
**Directory scope:** `src/pipeline/`, `src/config.py`, `src/__init__.py`

Tasks:
1. Create `src/__init__.py` and `src/config.py` — pydantic BaseSettings loading from `config/beestgraph.yml` with env var overrides. Include all config fields.
2. Create `src/pipeline/__init__.py`
3. Create `src/pipeline/markdown_parser.py` — parse markdown files: extract YAML frontmatter (python-frontmatter), find `[[wiki-links]]`, find `#tags`, extract URLs. Return a structured ParsedDocument dataclass.
4. Create `src/pipeline/ingester.py` — async FalkorDB client wrapper. Functions: `upsert_document()`, `upsert_tag()`, `upsert_topic()`, `create_link()`, `create_mention()`. All use MERGE. Include `ingest_parsed_document()` that takes a ParsedDocument and writes the full subgraph.
5. Create `src/pipeline/watcher.py` — watchdog-based daemon. Monitors vault inbox. On new .md file: parse → ingest → move file to proper vault location. CLI entry point with click.
6. Create `src/pipeline/keepmd_poller.py` — async poller. Uses httpx to call keep.md REST API (list inbox, get item content, mark done). For each item: create markdown in vault, ingest into graph. CLI entry point with click.
7. Create `src/pipeline/processor.py` — orchestrator that can invoke Claude Code headless for AI-powered categorization and entity extraction. Include a fallback mode that does basic keyword extraction without LLM calls.

### Track 3 → `graph` agent
**Directory scope:** `src/graph/`, `tests/test_graph/`

Tasks:
1. Create `src/graph/__init__.py`
2. Create `src/graph/schema.py` — functions to create all indexes (range, full-text, vector). Include a `ensure_schema()` function that's idempotent. Version the schema with a metadata node.
3. Create `src/graph/queries.py` — Cypher query builder functions: `search_documents(query, limit)`, `get_document_neighborhood(path, depth)`, `find_related_by_tags(tags)`, `find_orphans()`, `topic_tree()`, `recent_documents(n)`, `documents_by_source_type(type)`. Each returns a Cypher string + params dict.
4. Create `src/graph/maintenance.py` — `deduplicate_tags()`, `deduplicate_entities()`, `find_orphan_documents()`, `compute_stats()` (node counts by type, edge counts by type, most connected documents), `find_hub_documents(top_n)` using degree centrality.
5. Create `tests/test_graph/conftest.py` with a FalkorDB test fixture (use a separate graph name like `beestgraph_test`).
6. Create `tests/test_graph/test_schema.py`, `test_queries.py`, `test_maintenance.py` — unit tests for all graph functions. Mock the FalkorDB client where needed.

### Track 4 → `web-ui` agent
**Directory scope:** `src/web/`

Tasks:
1. Initialize Next.js 15 project in `src/web/` with TypeScript, Tailwind CSS, App Router. Create `package.json`, `next.config.js`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js`.
2. Create `src/web/src/app/layout.tsx` — root layout with dark mode support, sidebar navigation (Dashboard, Graph, New Entry, Timeline), beestgraph logo/title.
3. Create `src/web/src/app/page.tsx` — dashboard with search bar, recent documents list, quick stats (total documents, topics, tags).
4. Create `src/web/src/app/graph/page.tsx` — Cytoscape.js graph explorer. Load nodes/edges from API route. Support click-to-expand, zoom, topic filtering, search highlighting.
5. Create `src/web/src/app/entry/page.tsx` — new entry form: URL input, title, notes, tags. Submit triggers API route that saves to keep.md and/or vault.
6. Create `src/web/src/app/api/` routes: `graph/route.ts` (query FalkorDB), `search/route.ts` (full-text search), `entry/route.ts` (create new entry), `stats/route.ts` (graph statistics).
7. Create components: `GraphExplorer.tsx`, `SearchBar.tsx`, `EntryCard.tsx`, `TopicTree.tsx`.
8. Create `src/web/src/lib/falkordb.ts` — FalkorDB client wrapper for API routes.

### Track 5 → `docs` agent
**Directory scope:** `docs/`, `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`, `.github/`

Tasks:
1. Create `README.md` — polished public-facing README. Include: project logo placeholder, tagline, feature list with emoji, system architecture diagram embed, hardware requirements table, quickstart (5 steps), configuration overview, links to detailed docs. Add badges: license, Python version, Node version, Docker.
2. Create `CONTRIBUTING.md` — dev setup instructions, branch naming, commit conventions, PR template, code of conduct reference.
3. Create `CHANGELOG.md` — initial entry for v0.1.0-alpha.
4. Create `LICENSE` — MIT license, copyright terbeest 2026.
5. Create `docs/setup-guide.md` — detailed step-by-step Pi setup from bare metal to running system.
6. Create `docs/configuration.md` — all configuration options with descriptions and defaults.
7. Create `docs/schema.md` — graph schema with Cypher examples for every node type and relationship.
8. Create `docs/keepmd-integration.md` — keep.md setup, extension install, MCP connection, workflow.
9. Create `docs/obsidian-integration.md` — vault structure, Syncthing setup, Web Clipper config.
10. Create `docs/mcp-servers.md` — all 4 MCP servers with tool descriptions and usage examples.
11. Create `docs/troubleshooting.md` — common issues (ARM64 Claude Code, FalkorDB connection, Tailscale, etc.).
12. Create `.github/ISSUE_TEMPLATE/bug_report.md` and `feature_request.md`.
13. Create `.github/workflows/ci.yml` — GitHub Actions: lint + test on push/PR.
14. Move existing `beestgraph-system.dot` and `beestgraph-system.svg` to `docs/diagrams/`.

## After all tracks complete

Do a final integration pass:
1. Verify all imports resolve correctly across `src/`.
2. Run `make lint` and fix any issues.
3. Run `make test` and ensure all tests pass.
4. Verify `docker-compose.yml` references are consistent with code.
5. Ensure `README.md` quickstart instructions match the actual scripts.
6. Create a clean git init with `.gitignore` (Python + Node + Docker + env files + .claude/).
7. Report a summary of everything built, any decisions made, and anything that needs manual follow-up (like API keys or keep.md OAuth).
