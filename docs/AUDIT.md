# beestgraph — Comprehensive Codebase Audit

> Generated 2026-03-22 by Claude Opus 4.6. Covers every module, config, script, doc, and service.

---

## Table of Contents

1. [Critical](#critical)
2. [High — Blocks Correct Operation](#high--blocks-correct-operation)
3. [Medium — Causes Confusion or Partial Failure](#medium--causes-confusion-or-partial-failure)
4. [Low — Cosmetic or Minor](#low--cosmetic-or-minor)
5. [Summary Statistics](#summary-statistics)

---

## Critical

### C1: Cypher Injection in Web UI

**File:** `src/web/src/lib/falkordb.ts:25-31`

The `graphQuery` function constructs Cypher parameters via string interpolation:

```ts
.map(([k, v]) => `${k}=${typeof v === "string" ? `"${v.replace(/"/g, '\\"')}"` : v}`)
```

Escapes `"` but NOT `\`. A value like `foo\` produces `"foo\"` which closes the string. User input from search bar and entry form flows directly here. **This is a Cypher injection vector.**

**Fix:** Use FalkorDB's native parameterized query support, or properly escape both `\` and `"`.

---

### C2: API Key Rotation Required

**File:** `docker/.env:5`

The Anthropic API key and GitHub PAT were exposed in conversation history during this session. The `.env` file is gitignored but both secrets should be rotated immediately.

---

## High — Blocks Correct Operation

### ~~H1: `asyncio.run()` Inside Running Event Loop Will Crash~~ (resolved)

*Removed: Graphiti integration has been removed from the project. The ingester no longer calls `asyncio.run()` for Graphiti episodes.*

---

### H2: Redis Client Singleton — No Reconnection

**File:** `src/web/src/lib/falkordb.ts:8-17`

Once connected, the Redis client is cached forever. If FalkorDB restarts or the connection drops, ALL web UI API routes return 500 errors permanently until the Next.js process is restarted. No reconnection logic, no health check, no error-triggered reset.

**Fix:** Catch connection errors in `graphQuery`, set `clientInstance = null`, and retry.

---

### H3: Config YAML Fields Silently Ignored (14 fields)

**Files:** `src/config.py:130-142`, `config/beestgraph.yml.example`

The `load_settings()` function filters YAML keys to only those in the pydantic model. These config sections/fields appear configurable but have **zero effect**:

| YAML Key | Expected By User | Reality |
|----------|-----------------|---------|
| `processing.model` | Sets LLM model | Dropped |
| `processing.concurrency` | Limits parallel tasks | Dropped |
| `processing.max_retries` | Retry limit | Dropped |
| `keepmd.poll_interval` | Polling interval | Dropped (field is `polling_interval_minutes`) |
| `keepmd.max_items_per_cycle` | Batch size | Dropped |
| `keepmd.enabled_sources` | Source filter | Dropped |
| `telegram.allowed_users` | Access control | Dropped (field is `allowed_user_ids`) |
| `telegram.enabled` | On/off toggle | Dropped |
| `logging.format` | Log format | Dropped |
| `logging.file` | Log file path | Dropped |
| `web.port` | Web UI port | Dropped |
| `web.host` | Bind address | Dropped |
| `backup.dir` | Backup location | Dropped |
| `backup.retention` | Retention days | Dropped |

**Fix:** Either add corresponding pydantic models or remove misleading YAML sections.

---

### H4: Schema Drift — `init-schema.sh` vs `schema.py`

**Files:** `scripts/init-schema.sh:38-54`, `src/graph/schema.py:22-35`

`init-schema.sh` creates **11 range indexes + 3 full-text indexes**. `schema.py` creates **7 range indexes + 1 full-text index**. Missing from `schema.py`:

- Range: `Document.para_category`, `Document.source_type`, `Source.url`, `Project.name`
- Full-text: `Tag.name`, `Concept.name+description`

Running `ensure_schema()` in Python vs `make init-schema` produces different database states.

**Fix:** Sync `schema.py` to match `init-schema.sh`.

---

### ~~H5: Graphiti Docker Image Name Likely Wrong~~ (resolved)

*Removed: Graphiti has been removed from the project entirely.*

---

### H6: Async/Sync Type Mismatch Across Layers

**Files:** `src/graph/schema.py` (async), `src/graph/maintenance.py` (async), `src/pipeline/ingester.py` (sync), `src/bot/telegram_bot.py` (sync graph in async handlers)

- `ensure_schema()` expects `falkordb.asyncio.Graph` — cannot be called from sync ingester
- `compute_stats()`, `deduplicate_tags()`, `deduplicate_entities()` are async — cannot be called from the sync bot graph handle
- Bot handlers are `async` but call `graph.query()` synchronously, blocking the event loop

**Fix:** Standardize on either async or sync throughout, or add adapter layers.

*Note: The Graphiti async/sync mismatch (former H1) has been resolved by removing Graphiti entirely.*

---

## Medium — Causes Confusion or Partial Failure

### M1: Tag Query Ignores Topic Filter in Graph Explorer

**File:** `src/web/src/lib/falkordb.ts:145-153`

When a user selects a topic filter, document-topic edges are filtered correctly, but document-tag edges are returned unfiltered. The graph shows misleading extra nodes from other topics.

---

### M2: Dark Mode Flash (FOUC)

**Files:** `src/web/src/components/Sidebar.tsx:86-101`, `src/web/src/app/layout.tsx:14`

Dark mode state starts as `false`, reads `localStorage` in `useEffect`. Causes a visible flash of light mode for dark-mode users on every page load. No inline `<script>` to set the `dark` class before React hydrates.

---

### M3: `process-keepmd.sh` Doesn't Match Architecture Description

**Files:** `scripts/process-keepmd.sh:93`, `CLAUDE.md:191`

CLAUDE.md says: `cron → scripts/process-keepmd.sh → claude -p (headless)`. The actual script runs `uv run python -m src.pipeline.keepmd_poller` directly — no Claude Code invocation.

---

### M4: Broken Link in README

**File:** `README.md:40,132`

Links to `docs/beestgraph-architecture.md` which doesn't exist (was deleted as a duplicate).

---

### ~~M5: MCP Config Inconsistency~~ (resolved)

*Removed: Graphiti has been removed from the project. MCP config now only includes keep.md, Filesystem, and FalkorDB.*

---

### M6: `personal/relationships` Topic Missing from `init-schema.sh`

**File:** `scripts/init-schema.sh:82-88`

CLAUDE.md taxonomy and `config/taxonomy.yml` include `personal/relationships`. The seed script omits it. `src/vault/manager.py` includes it.

---

### ~~M7: Graphiti Health Check May Fail~~ (resolved)

*Removed: Graphiti has been removed from the project.*

---

### M8: Non-existent Maintenance CLI in Troubleshooting Docs

**File:** `docs/troubleshooting.md:402`

References `uv run python -m src.graph.maintenance --deduplicate`. No CLI entry point exists in `maintenance.py`.

---

### ~~M9: `configure-mcp.sh` Only Configures 3 of 4 MCP Servers~~ (resolved)

*Resolved: Graphiti has been removed. The script now correctly configures all 3 MCP servers (keep.md, Filesystem, FalkorDB).*

---

### M10: Timeline Shows Stale Data Alongside Error

**File:** `src/web/src/app/timeline/page.tsx:298,322`

On re-fetch failure, error banner displays but old document data still renders below it.

---

### M11: `docs/configuration.md` Describes Non-existent Config Fields

**File:** `docs/configuration.md:30-73`

Documents `general.timezone`, `keepmd.enabled`, `keepmd.mcp_url`, `processing.summary_max_words`, `processing.entity_confidence_threshold` — none of which exist in the Python model.

---

### M12: Pydantic Env Var Overrides May Not Work for Nested Models

**File:** `src/config.py:27-67`

Each sub-model has its own `env_prefix` (e.g., `BEESTGRAPH_FALKORDB_`), but sub-models are instantiated via `Field(default_factory=...)` in the parent. Pydantic-settings v2 may not propagate env vars to sub-models instantiated this way.

---

## Low — Cosmetic or Minor

### L1: Concept `description` Never Populated

**File:** `src/pipeline/ingester.py:77-80`

CLAUDE.md schema defines `(:Concept {name, normalized_name, description})` but `_MERGE_CONCEPT` only sets `name` and `normalized_name`.

---

### L2: Dead Code `_deduplicate_by_label` with Bug

**File:** `src/graph/maintenance.py:19-50`

Unused function that hardcodes `TAGGED_WITH` for all labels (wrong for Person/Concept which use `MENTIONS`).

---

### L3: Unused Dependencies

**File:** `pyproject.toml:31-34`

`obsidiantools` and `rich` are declared but never imported in any `src/` file.

---

### L4: Triple-Duplicated `FakeResultSet` in Tests

**Files:** `tests/graph/conftest.py`, `tests/pipeline/conftest.py`, `tests/graph/test_maintenance.py`

Three independent implementations of the same test helper.

---

### L5: Bot Handlers Block Event Loop

**File:** `src/bot/telegram_bot.py:122-210`

All 6 handlers call `graph.query()` synchronously inside `async` functions, blocking the aiogram event loop during database queries.

---

### L6: `/home/pi` References Throughout

**Files:** `docker/.env.example:8`, `scripts/process-keepmd.sh:7`, `scripts/setup.sh:121`, `docs/setup-guide.md:47`

Multiple files reference `/home/pi` or user `pi` instead of being parameterized.

---

### L7: `dark:hover:bg-gray-750` Non-existent Tailwind Class

**File:** `src/web/src/app/timeline/page.tsx:134`

`gray-750` is not a standard Tailwind shade. Hover state missing in dark mode.

---

### L8: Double Border on Cytoscape Container

**Files:** `src/web/src/app/globals.css:12`, `src/web/src/app/graph/page.tsx:114`

Both parent div and `.cytoscape-container` apply `border border-gray-200`.

---

### L9: `closeConnection()` Exported but Never Called

**File:** `src/web/src/lib/falkordb.ts:377`

Redis connection is never properly closed on shutdown.

---

### L10: CI Only Tests Python 3.11, Runtime Is 3.13

**File:** `.github/workflows/ci.yml:23`

CI pins Python 3.11. Actual runtime is 3.13. Should test both.

---

### L11: CI Does Not Test Web UI

**File:** `.github/workflows/ci.yml`

No Node.js install, no `npm run build`, no TypeScript type checking in CI.

---

### L12: `make install` Doesn't Install Dev Dependencies

**File:** `Makefile:20-21`

`install` target runs `uv sync` without `--extra dev`. Users following README quickstart won't have ruff/pytest.

---

### L13: `make run-all` Orphans Background Process

**File:** `Makefile:47-50`

Watcher backgrounded with `&`. If bot exits, watcher keeps running. No PID tracking.

---

### L14: Ingester Doesn't Store `author` Field

**File:** `src/pipeline/ingester.py:26-38`

CLAUDE.md frontmatter template includes `author` but `_MERGE_DOCUMENT` doesn't write it to the graph.

---

### L15: `docs/schema.md` Shows Short Topic Names, Code Uses Path-style

**Files:** `docs/schema.md:82-96`, `scripts/init-schema.sh:58-88`

Docs show topics as `"ai-ml"`, code stores them as `"technology/ai-ml"`.

---

### L16: Node.js Version Mismatch Between Docs

**Files:** `scripts/setup.sh:88` (Node 22), `docs/setup-guide.md:188` (Node 20), `README.md:5` (badge says 20+)

---

### L17: `.prettierrc` Exists but Was Reported Missing

**File:** `src/web/.prettierrc`

File exists — no issue. (Audit agent may not have found it.)

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| Critical | 2 |
| High | 6 |
| Medium | 12 |
| Low | 17 |
| **Total** | **37** |

### By Domain

| Domain | Findings |
|--------|----------|
| Security | 3 (C1, C2, H2) |
| Config consistency | 5 (H3, H4, M5, M11, M12) |
| Async/sync architecture | 3 (H1, H6, L5) |
| Web UI | 6 (C1, H2, M1, M2, M10, L7-L9) |
| Documentation accuracy | 6 (M3-M4, M8-M9, M11, L6) |
| Schema drift | 3 (H4, M6, L15) |
| Docker/infra | 3 (H5, M7, L6) |
| Tests/CI | 3 (L4, L10, L11) |
| Dead code | 2 (L2, L3) |
| Pipeline | 3 (H1, L1, L14) |
