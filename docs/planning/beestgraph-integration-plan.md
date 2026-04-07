# beestgraph: Next-Gen Integration Plan

> Merging the active-vault architecture into the deployed system without
> regressing any capability on the current as-built roadmap.
> 
> **Based on:** beestgraph-as-built.md, beestgraph-architecture.md,
> beestgraph-addendum.md, beestgraph-template.md, beestgraph-active-vault-integration.md
> **Status:** Integration design — pre-build
> **Date:** April 2026

---

## 0. Ground Rules for This Document

This plan treats the as-built system as immutable ground truth for what is
currently running. Every decision below either preserves existing behavior or
extends it. No running service is interrupted. No data is destroyed. All five
planning documents are reconciled, with explicit call-outs wherever they
conflict.
**Conflict resolution hierarchy** (when documents disagree):

1. `beestgraph-template.md` wins on frontmatter questions
2. `beestgraph-addendum.md` wins on architectural questions about the active
   vault, the `bg` CLI, and sequencing
3. `beestgraph-as-built.md` wins on questions of current running state
4. `beestgraph-active-vault-integration.md` is the implementation reference
   for each feature
5. `beestgraph-architecture.md` is the original design reference — valid
   for anything not superseded by the above

---

## 1. Conflict Inventory

Every divergence between the planning documents and the as-built system is
catalogued here with an explicit resolution. Nothing in Sections 2–7 should
surprise anyone who has read this section.

---

### Conflict 1 — Vault Directory Structure

**The tension:** The as-built vault uses numbered PARA directories
(`00-meta` through `09-attachments`). The active-vault-integration document
describes a fully renamed, flat directory scheme (`inbox/`, `knowledge/`,
`entities/`, `projects/`, `archives/`, `daily/`, `reviews/`, `boards/`,
`synthesis/`, `raw/`, `templates/`, `config/`). These are not compatible
without a vault migration.
**What the addendum says (Section 11):** Keep the numbered structure. Add
`entities/`, `synthesis/`, and `raw/` as new directories alongside the
existing numbered ones. Add four root files (`identity.md`, `index.md`,
`log.md`, `CONTEXT.md`) at the vault root.
**Resolution — addendum wins, active-vault-integration is reconciled:**
The three new directories map onto the existing numbered structure as siblings,
not replacements. The active-vault-integration's `knowledge/` concept maps to
`07-resources/` as-is. Daily notes, projects, and areas stay in `04-daily/`,
`05-projects/`, and `06-areas/` respectively. No vault migration required.

```
~/vault/ ← existing structure unchanged
├── 00-meta/ through 09-attachments/ ← all unchanged
├── entities/ ← NEW (Phase 4 creates this)
│ ├── people/
│ ├── organizations/
│ ├── tools/
│ ├── concepts/
│ └── places/
├── synthesis/ ← NEW (Phase 7 creates this)
├── raw/ ← NEW (Phase 4 creates this)
│ ├── articles/
│ ├── transcripts/
│ └── pdfs/
├── identity.md ← NEW (Phase 6 creates this)
├── index.md ← NEW (Phase 5 creates this)
├── log.md ← NEW (Phase 5 creates this)
└── CONTEXT.md ← RENAMED from CLAUDE.md (Phase 3)
```

`bg init` creates the new directories. `bg ingest` populates `entities/` and
`raw/`. `bg think connect` and the synthesis pipeline create `synthesis/`.
The existing numbered directories are never renamed or migrated.

---

### Conflict 2 — CLAUDE.md vs CONTEXT.md

**The tension:** CLAUDE.md is referenced in `src/pipeline/processor.py` as the
agent configuration file, in `tests/` as part of the testing standards
commentary, and in scripts. Renaming it breaks these references.
**Resolution:** The rename happens in Phase 3 as a deliberate migration step,
not as a side effect of some other change. The migration checklist for Phase 3
includes updating every reference before deleting CLAUDE.md. `CONTEXT.md` is
rewritten from scratch — it is not a renamed copy — because the purpose
changes from "Claude Code configuration" to "LLM-agnostic system
documentation." The old CLAUDE.md content is not lost; its processing
instructions move into the Python pipeline and its Cypher templates move into
`src/graph/queries.py`.
**Files to update when Phase 3 ships:**

- `src/pipeline/processor.py` — remove CLAUDE.md path reference
- Any `tests/` fixtures that reference CLAUDE.md
- `scripts/configure-mcp.sh` if it references CLAUDE.md
- `docs/` — update all documentation references
- `README.md`

---

### Conflict 3 — Path-Based vs UID-Based MERGE in the Ingester

**The tension:** The as-built ingester (`src/pipeline/ingester.py`) MERGEs
document nodes on `path`. The template spec defines `uid` as the immutable
primary key. `src/pipeline/zettelkasten.py` generates UIDs but is not
called anywhere in the pipeline. The as-built roadmap item #4 says "Migrate
to uid-based MERGE" but treats it as a discrete future task.
**Why this is a sequencing blocker:** The rewrite-on-ingest pipeline (Phase 4)
depends on stable document identity to find and update entity pages.
Path-based identity breaks if a file is moved or renamed. UID-based identity
is required before rewrite-on-ingest can work reliably.
**Resolution:** UID migration moves to the Pre-Work phase, ahead of the `bg`
CLI build. It is the smallest migration that unblocks everything else:

1. Wire `zettelkasten.py`'s `generate_id()` into the capture path so new
   documents get a `uid` in their frontmatter on creation
2. Update `ingester.py` to MERGE on `uid` when present, fall back to `path`
   when not (backwards compatibility for existing 195 nodes)
3. Add a `bg migrate --uid-only` mode that backfills UIDs onto existing vault
   documents without changing any other frontmatter
   This is the single Pre-Work item that has a hard dependency ordering
   constraint. It must complete before Phase 4 begins.

---

### Conflict 4 — Roadmap Phase Ordering (Active Ingest Position)

**The tension:** The addendum sequences the phases as:

1. CLI Foundation → 2. Thinking Tools → 3. CLAUDE.md Migration + `bg migrate`
   → 4. Active Ingest → 5. Event-Driven Automation → 6. Context Engine
   → 7. Synthesis
   The active-vault-integration document sequences them as:
2. CLI Foundation → 2. Thinking Tools → 3. Active Ingest → 4. Context Engine
   → 5. Event-Driven Automation
   The active-vault-integration puts Active Ingest at Phase 3 (before the
   CLAUDE.md migration) and swaps Context Engine and Event-Driven Automation.
   **Resolution — addendum wins, for two reasons:**
   First, Active Ingest at Phase 3 creates a structural problem: the `entities/`
   directory convention and the `bg migrate` command both need to exist before
   the ingest pipeline assumes them. If Active Ingest ships before migration, the
   pipeline is building on a partially-migrated vault.
   Second, the addendum's rationale for deferring the Context Engine to Phase 6
   is sound: "the context engine is the layer most sensitive to how the user ends
   up using the CLI in practice — better to build it after there is real usage
   to learn from." This is experience-based sequencing, not arbitrary.
   **Merged roadmap order:**
   Pre-Work → Phase 1 (CLI) → Phase 2 (Thinking Tools) → Phase 3 (Migration)
   → Phase 4 (Active Ingest) → Phase 5 (Event-Driven) → Phase 6 (Context Engine)
   → Phase 7 (Synthesis + Full Ingest)

---

### Conflict 5 — Two Watcher Modules

**The tension:** `src/pipeline/watcher.py` exists and runs as the
`beestgraph-watcher` systemd service. It monitors `~/vault/01-inbox/` and
triggers the full capture pipeline on new `.md` files. The
active-vault-integration document specifies a new `src/automation/watcher.py`
that monitors the *entire vault* for incremental graph sync on every file
change.
These are distinct services with distinct purposes and must not be conflated.
**Resolution:** Both watcher modules exist permanently. They are different
services with different scopes:
| Module | Path monitored | Trigger action | Systemd service |
|--------|---------------|----------------|-----------------|
| `src/pipeline/watcher.py` | `~/vault/01-inbox/` | Full pipeline: parse → classify → format → security scan → queue | `beestgraph-watcher` (existing) |
| `src/automation/watcher.py` | `~/vault/**/*.md` | Incremental graph sync: parse frontmatter → MERGE changed fields in FalkorDB | `beestgraph-vault-sync` (new, Phase 5) |
The new automation watcher deliberately does *not* run the full pipeline on
every vault file change — that would be prohibitively expensive for
interactive Obsidian editing. It only syncs frontmatter changes to FalkorDB.
Full pipeline processing remains the exclusive domain of the inbox watcher.

---

### Conflict 6 — Graphiti MCP Server

**The tension:** The architecture document specifies four MCP servers
(keep.md, Graphiti, Filesystem, FalkorDB). The addendum Section 15
("What Did Not Change") explicitly states: "MCP server constellation: The
three-server design (keep.md, Filesystem, FalkorDB) continues." The as-built
system does not show Graphiti actively running.
**Resolution:** Graphiti is treated as a future optional extension, not a
current dependency. The three-server constellation (keep.md, Filesystem,
FalkorDB) is the canonical design. The `config/mcp.json` template retains
Graphiti as a commented-out option for future use. If temporal fact tracking
becomes a priority, it can be re-introduced without affecting the rest of the
architecture.

---

### Conflict 7 — LLM Agent Coupling

**The tension:** The as-built `src/pipeline/processor.py` invokes Claude Code
headless directly, with CLAUDE.md as its configuration file. The new design
requires a pluggable `LLMAgent` interface that can use Anthropic, Ollama, or
any OpenAI-compatible endpoint.
**Resolution:** `processor.py` is refactored in Phase 3 (alongside the
CLAUDE.md → CONTEXT.md migration) to call an `LLMAgent` interface rather than
invoking Claude Code directly. The initial concrete implementation,
`AnthropicAgent`, wraps the same Anthropic API call that currently drives
the headless invocations. No behavior changes at Phase 3 — it is a structural
refactor that preserves existing functionality while opening the adapter
seam. Additional implementations (Ollama, OpenAI-compatible) are added in
later phases or on demand.

```
src/cli/agent.py ← new: LLMAgent Protocol + implementations
 AnthropicAgent ← wraps existing Anthropic API calls
 OllamaAgent ← new, optional
 OpenAICompatibleAgent ← new, optional
```

---

### Conflict 8 — `src/vault/manager.py` vs Proposed Split

**The tension:** The architecture document proposes splitting vault management
into `structure.py`, `templates.py`, and `bulk_import.py`. The as-built system
has a single `manager.py`.
**Resolution:** `manager.py` is not split. The module boundary is a future
refactoring concern, not a prerequisite for any of the new features. A
`bulk_import.py` module is added as a new sibling when bulk import is
specifically needed (not in the current roadmap). `manager.py` is extended
in-place as needed.

---

### Conflict 9 — Automation Schedule Expansion

**The tension:** The as-built system has 2 cron jobs and 5 systemd services.
The new design specifies 9 scheduled jobs (plus 3 event-driven triggers). The
as-built roadmap does not mention the new scheduled jobs.
**Resolution:** The new scheduled jobs are purely additive and land in Phase 5
alongside the event-driven automation work. The existing 2 cron jobs continue
to run without modification:
| Existing | Status |
|----------|--------|
| `process-keepmd.sh` every 15 min | Unchanged — maps to `keepmd-inbox` in new design |
| `mesh-daily-report.sh` daily 8am | Unchanged — stays as-is |
New jobs added in Phase 5:
| New job | Schedule | Notes |
|---------|----------|-------|
| `morning-brief` | 07:00 daily | Replaces mesh-daily-report for personal vault; mesh report stays |
| `nightly-close` | 22:00 daily | New |
| `weekly-review` | Fri 18:00 | New |
| `health-check` | Sun 21:00 | New |
| `source-health` | every 6 hrs | New |
| `maintenance` | 02:00 daily | Schedules existing `src/graph/maintenance.py` (currently unscheduled) |
| `backup` | 03:00 daily | Formalizes `scripts/backup.sh` into a managed cron job |
| `vault-inbox` | every 5 min | Supplement for inbox watcher; cron fallback when watcher is down |

---

### Conflict 10 — `bg` CLI Scope

**The tension:** The as-built roadmap item #2 identifies 6 CLI commands.
The new design specifies 16+ Layer 1 commands, the `bg think` family,
and `bg context`. The 6 in the as-built were the original minimum; the full
set is the canonical design.
**Resolution:** The full command set from the active-vault-integration
document is canonical. The 6 from the as-built are a subset — all 6 are
included. No commands are removed.
**The as-built's 6 commands and their resolution:**
| as-built command | New name/mapping | Phase |
|-----------------|------------------|-------|
| `bg ingest` | `bg ingest` | Phase 1 (basic), Phase 4 (full 5-phase) |
| `bg migrate` | `bg migrate` | Phase 3 |
| `bg export --flat` | `bg export --flat` | Phase 1 |
| `bg archive` | `bg archive` | Phase 1 |
| `bg think audit` | `bg think audit` | Phase 2 |
| `bg task` | `bg task` | Phase 1 |

---

## 2. Reconciled Architecture

### Infrastructure layers (unchanged from as-built)

```
┌──────────────────────────────────────────────────────────────────┐
│ CAPTURE │
│ keep.md | Obsidian Web Clipper | Manual notes | Telegram /add │
└──────────────────────────┬───────────────────────────────────────┘
 │
┌──────────────────────────▼───────────────────────────────────────┐
│ PROCESSING │
│ Inbox watchdog → Full pipeline (parse → classify → format → │
│ security scan → privacy → queue → ingest) │
│ LLMAgent interface (Anthropic default, Ollama/OpenAI optional) │
└──────────────────────────┬───────────────────────────────────────┘
 │
┌──────────────────────────▼───────────────────────────────────────┐
│ STORAGE │
│ FalkorDB (UID-keyed, schema v4+) | Obsidian vault (NVMe, Syncthing) │
│ Radicale (CalDAV) | Raw captures (immutable source store) │
└──────────────────────────┬───────────────────────────────────────┘
 │
┌──────────────────────────▼───────────────────────────────────────┐
│ ACCESS │
│ Telegram bot | Web UI :3001 | FalkorDB Browser :3000 │
│ SSH + bg CLI | Graph API │
└──────────────────────────────────────────────────────────────────┘
```

### Functional layers (new, sitting on top)

```
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 4: Automation │
│ "The vault maintains itself" │
│ Scheduled: morning-brief, nightly-close, weekly-review, │
│ health-check, source-health, maintenance, backup │
│ Event-driven: on-file-change (graph sync), on-session-end, │
│ on-commit (health check) │
├──────────────────────────────────────────────────────────────────┤
│ LAYER 3: Context Engine │
│ "The vault knows you" │
│ bg context --level 0/1/2/3 | identity.md at vault root │
├──────────────────────────────────────────────────────────────────┤
│ LAYER 2: Thinking Tools │
│ "The vault thinks with you" │
│ bg think challenge/emerge/connect/graduate/forecast/audit │
│ All backed by FalkorDB Cypher; LLM optional for synthesis │
├──────────────────────────────────────────────────────────────────┤
│ LAYER 1: Vault Operations │
│ "The vault remembers" │
│ bg save/ingest/reconcile/daily/log/task/person/decide/ │
│ capture/find/recap/review/project/health/init/adr/migrate/ │
│ export/archive │
└──────────────────────────────────────────────────────────────────┘
```

### Source layout (final target)

```
src/
├── config.py (existing — unchanged)
├── bot/ (existing — unchanged)
│ ├── telegram_bot.py
│ └── qualification_handler.py
├── graph/ (existing — extended)
│ ├── schema.py ← minor additions for entities/ node tracking
│ ├── queries.py ← extended with thinking tool Cypher queries
│ └── maintenance.py ← unchanged; finally scheduled in Phase 5
├── vault/ (existing — unchanged)
│ └── manager.py
├── pipeline/ (existing — refactored in Phase 3/4)
│ ├── markdown_parser.py ← unchanged
│ ├── ingester.py ← UID migration (Pre-Work) + 5-phase (Phase 4)
│ ├── processor.py ← refactored to use LLMAgent interface (Phase 3)
│ ├── classifier.py ← unchanged
│ ├── formatter.py ← unchanged
│ ├── qualification.py ← unchanged
│ ├── watcher.py ← unchanged (inbox watchdog only)
│ ├── keepmd_poller.py ← unchanged
│ ├── security_scanner.py ← unchanged
│ ├── privacy.py ← unchanged
│ └── zettelkasten.py ← wired up (Pre-Work)
├── heartbeat/ (existing — unchanged)
│ ├── daemon.py
│ ├── checks.py
│ └── calendar.py
├── cli/ ← NEW (Phase 1)
│ ├── __init__.py
│ ├── main.py ← Click/Typer entry point; `bg` binary
│ ├── agent.py ← LLMAgent Protocol + implementations (Phase 3)
│ └── commands/
│ ├── daily.py ← Phase 1
│ ├── task.py ← Phase 1
│ ├── find.py ← Phase 1
│ ├── project.py ← Phase 1
│ ├── health.py ← Phase 1
│ ├── init.py ← Phase 1
│ ├── capture.py ← Phase 1
│ ├── save.py ← Phase 1
│ ├── export.py ← Phase 1
│ ├── archive.py ← Phase 1
│ ├── ingest.py ← Phase 1 (basic) → Phase 4 (5-phase)
│ ├── migrate.py ← Phase 3
│ ├── reconcile.py ← Phase 4
│ ├── person.py ← Phase 4
│ ├── decide.py ← Phase 4
│ ├── adr.py ← Phase 4
│ ├── log.py ← Phase 5
│ ├── recap.py ← Phase 5
│ ├── review.py ← Phase 5
│ ├── context.py ← Phase 6
│ └── think/
│ ├── __init__.py
│ ├── challenge.py ← Phase 2
│ ├── emerge.py ← Phase 2
│ ├── connect.py ← Phase 2
│ ├── audit.py ← Phase 2
│ ├── graduate.py ← Phase 2
│ └── forecast.py ← Phase 2
└── automation/ ← NEW (Phase 5)
 ├── watcher.py ← full-vault incremental graph sync
 └── hooks.py ← git/session hooks
```

---

## 3. Pre-Work: UID Migration

**Before any phase begins.** This is the dependency that unblocks Phase 4.
**Effort:** Low (2–3 hours). **Risk:** Low (backwards-compatible).

### Step 1 — Wire zettelkasten.py into capture

In `src/pipeline/watcher.py` and `src/pipeline/keepmd_poller.py`, import
`generate_id()` from `zettelkasten.py` and inject `uid: <YYYYMMDDHHMM>` into
the frontmatter of every new document entering the inbox. Documents that
already have a `uid` field are left unchanged.

### Step 2 — Update ingester.py MERGE

Change the MERGE key from `path` to `uid`, with `path` as a fallback for
documents that pre-date the UID system:

```python
# Before:
MERGE (d:Document {path: $path})
# After:
MERGE (d:Document {uid: $uid})
ON CREATE SET d.path = $path
ON MATCH SET d.path = $path # always keep path current after any rename
```

This is fully backwards-compatible. Documents without a `uid` continue to
MERGE on `path` until they are migrated.

### Step 3 — Add uid-only migration mode

A script (later wrapped by `bg migrate --uid-only`) reads every `.md` file
in the vault, generates a `uid` for those that lack one, and writes it to
frontmatter. This can be run opportunistically — there is no urgency to
migrate all 61 existing files at once.

### Exit criteria

- Every new document entering the inbox gets a `uid`
- `ingester.py` MERGEs on `uid` for new documents
- Existing 195 nodes continue to work (path fallback)

---

## 4. Phase 1: CLI Foundation

**The biggest unlock.** All script-level. No new processing logic. The
deliverable is a single `bg` binary that composes the existing pipeline
modules behind a discoverable command surface.

### What gets built

`src/cli/` directory with a Click (or Typer) entry point registered in
`pyproject.toml` as the `bg` script. Initial command set:
| Command | Wraps | Notes |
|---------|-------|-------|
| `bg daily` | `src/pipeline/` + vault templates | Creates/updates today's daily note |
| `bg task` | `src/pipeline/` + frontmatter | Promotes action_items to tasks |
| `bg find` | `src/graph/queries.py` | Graph-powered search; replaces ad-hoc Cypher |
| `bg project` | vault/graph | Project note status from graph + boards |
| `bg health` | `src/heartbeat/checks.py` | Vault audit (orphans, stale queue, disk) |
| `bg init` | vault/manager.py | Bootstrap vault + graph directories |
| `bg capture` | keepmd_poller → inbox | Zero-friction idea capture |
| `bg save` | formatter + ingester | Extract decisions/tasks from text |
| `bg export` | ingester + frontmatter | Flat YAML export |
| `bg archive` | vault/manager.py | Transition document to archived status |
| `bg ingest` | processor + ingester | URL/file → basic (v1) pipeline |
All commands implement the two-path contract:

```python
def run_without_agent(args) -> Result: ...
def run_with_agent(args, agent: LLMAgent) -> Result: ...
```

### `pyproject.toml` change

```toml
[project.scripts]
bg = "src.cli.main:app"
```

### Entry criteria

Click or Typer installed. `src/cli/` directory created.

### Exit criteria

`bg daily` creates today's note. `bg find` queries the graph. `bg health`
audits the vault. `bg ingest <url>` runs the existing v1 pipeline.
`bg --help` shows a complete, organized command tree.

### No regressions

The existing `python -m src.pipeline.<module>` invocations continue to work.
The `bg` CLI is an additional entry point, not a replacement for the systemd
services or the cron scripts.

---

## 5. Phase 2: Thinking Tools

**The value demonstration.** Makes FalkorDB earn its rent. Every thinking
tool has a Cypher-backed path that works without an LLM.

### Graph query additions to `src/graph/queries.py`

Six new query functions, one per thinking tool:

```python
def challenge_queries(topic: str) -> ChallengeEvidence: ...
def emerge_queries(period_days: int) -> EmergenceReport: ...
def connect_queries(a: str, b: str) -> ConnectionPaths: ...
def graduate_queries(idea_slug: str) -> GraduateContext: ...
def forecast_queries(topic: str) -> FrequencyTimeline: ...
def audit_queries(claim: str) -> AuditEvidence: ...
```

Each function returns structured data — typed Python dataclasses, not raw
Cypher results. The CLI commands consume these dataclasses and either render
them directly (no LLM) or pass them to `LLMAgent.enhance()` (with `--agent`).

### Key Cypher patterns (new `key_claims` index required)

Phase 2 adds one new full-text index to `src/graph/schema.py`:

```cypher
CALL db.idx.fulltext.createNodeIndex('Document', 'key_claims')
```

This powers `bg think audit` and Phase 3's contradiction detection.

### Entry criteria

Phase 1 complete. FalkorDB running with schema v4.

### Exit criteria

All six thinking tools return useful structured output. `bg think challenge
--agent` produces a prose counter-argument. `bg think connect A B` returns
shortest-path and shared-neighbor results. Documented with example
invocations.

---

## 6. Phase 3: Migration — CLAUDE.md, LLMAgent, `bg migrate`

**The philosophical commit.** After this phase, the system is provably
LLM-agnostic. CLAUDE.md does not exist. Processing instructions live in
Python. Cypher templates live in `queries.py`.

### Step 1 — Write CONTEXT.md

Write `CONTEXT.md` from scratch as LLM-agnostic system documentation:

- What beestgraph is and how it works
- Vault structure and conventions
- The frontmatter template (reference to `beestgraph-template.md`)
- Graph schema and query patterns
- How to use the `bg` CLI
- *Not* a set of processing instructions for Claude Code specifically
  
  ### Step 2 — Refactor `processor.py`
  
  Extract all LLM invocations from `processor.py` behind the `LLMAgent`
  interface (defined in `src/cli/agent.py`):
  
  ```python
  # Before — processor.py calls Claude Code headless directly
  result = subprocess.run(['claude', '-p', prompt, '--headless'], ...)
  # After — processor.py calls the agent interface
  agent = AnthropicAgent.from_config(config)
  result = agent.enhance(base_result, prompt)
  ```
  
  `AnthropicAgent` is a thin wrapper around the existing Anthropic API call.
  Behavior is identical. The seam is now open for alternative providers.
  
  ### Step 3 — Build `bg migrate`
  
  The vault migration command. Operates on one document at a time or in bulk:
  
  ```bash
  bg migrate --dry-run # report what would change
  bg migrate --uid-only # backfill uid fields only (Pre-Work convenience wrapper)
  bg migrate --frontmatter # upgrade v1/v2 frontmatter to final spec
  bg migrate --all # full migration of all vault files
  ```
  
  Migration rules (from `beestgraph-template.md` Section 16):
- `quality: low/medium/high` → `confidence: 0.3/0.6/0.9`
- Flat kebab-case fields → nested canonical format
- Missing Tier 1 fields → auto-populated with sensible defaults
- `path`-only documents → generate and inject `uid`
- `v1` four-template format → universal template Tier 1 fields
  
  ### Step 4 — Delete CLAUDE.md, update all references
  
  CLAUDE.md is deleted only after CONTEXT.md is written and all references in
  `src/`, `tests/`, `scripts/`, and `docs/` have been updated.
  
  ### Entry criteria
  
  Phase 2 complete.
  
  ### Exit criteria
  
  CLAUDE.md does not exist. CONTEXT.md exists. `processor.py` uses `LLMAgent`
  interface. `bg migrate --dry-run` reports accurately on the vault. One
  successful migration run on a vault backup produces clean output.

---

## 7. Phase 4: Active Ingest (Rewrite-on-Ingest)

**The behavior that distinguishes active vaults from passive archives.** A
single ingest touches 5–15 existing pages. Entity pages become living
documents.

### New vault directories (created by `bg init` update)

```bash
mkdir -p ~/vault/entities/{people,organizations,tools,concepts,places}
mkdir -p ~/vault/raw/{articles,transcripts,pdfs}
```

### Upgrade `src/pipeline/ingester.py`

Extend the existing ingester with Phases 2–5 of the rewrite-on-ingest
pipeline. Phase 1 (the current behavior) is unchanged.

```python
class Ingester:
 def ingest(self, doc: ParsedDocument, agent: Optional[LLMAgent] = None):
 # Phase 1: existing — create/update document node (unchanged)
 self._phase1_upsert_document(doc)
 # Phase 2: new — update existing entity pages
 self._phase2_update_entities(doc, agent)
 # Phase 3: new — detect contradictions via key_claims
 self._phase3_detect_contradictions(doc, agent)
 # Phase 4: agent-only — synthesize connections
 if agent:
 self._phase4_synthesize(doc, agent)
 # Phase 5: new — update index.md and log.md
 self._phase5_update_navigation(doc)
```

**Phase 2** (`_phase2_update_entities`): For each entity in
`doc.frontmatter.entities.*`, find the entity page in `entities/` by canonical
name. Without agent: append a new "Mentioned In" reference. With agent:
rewrite the entity page incorporating the new context.
**Phase 3** (`_phase3_detect_contradictions`): Query the `key_claims`
full-text index (created in Phase 2) for each claim in the new document.
Flag matches scoring above 0.5. Without agent: write to a `contradictions/`
review list. With agent: evaluate genuineness, create `CONTRADICTS` edges
where warranted.
**Phase 4** (`_phase4_synthesize`): Agent receives new document plus five
most graph-proximate existing documents. If the agent identifies an unnamed
pattern, create a new `type: synthesis` document in `synthesis/`.
**Phase 5** (`_phase5_update_navigation`): Append to `index.md` (topic
section) and `log.md` (chronological record). Both files are auto-maintained;
the human never edits them.

### New `bg ingest` flags (Phase 4 upgrade)

```bash
bg ingest <url> # Phase 1 only (default, safe)
bg ingest <url> --active # Phases 1-3 (script-level, no LLM)
bg ingest <url> --agent # Phases 1-5 (full active ingest)
```

The default remains Phase 1 only. Opt-in to the broader phases.

### Entry criteria

Phase 3 complete. `entities/` and `raw/` directories created. UID migration
(Pre-Work) complete.

### Exit criteria

Ingesting a URL that mentions an existing entity updates that entity's page.
Ingesting a URL whose `key_claims` conflict with existing documents flags a
contradiction. `--active` flag runs without errors. `--agent` flag produces
synthesis documents.

---

## 8. Phase 5: Event-Driven Automation

**The watcher service and the expanded cron schedule.** The vault starts
maintaining itself without manual invocation.

### New systemd service: `beestgraph-vault-sync`

`src/automation/watcher.py` — full-vault incremental graph sync. Monitors
`~/vault/**/*.md` (excluding `01-inbox/` which is covered by the existing
watcher). On any `.md` file change: parse frontmatter only, MERGE changed
fields in FalkorDB.
This service deliberately does *not* run the full pipeline. It is the
lightweight sync companion to the heavyweight inbox watchdog.

### New session hook: `on-session-end`

`src/automation/hooks.py` — a lightweight prompt that fires when a `bg`
session closes (or on git commit to the vault). Asks: "Save session
knowledge?" If yes, runs `bg save` to extract decisions and tasks from the
session context.

### New cron jobs (added to the OpenClaw schedule)

All new scheduled jobs call `bg` commands, not raw Python module invocations.
The `bg` binary is the stable interface; implementation can change underneath.
| Job | Schedule | Command |
|-----|----------|---------|
| `morning-brief` | 07:00 daily | `bg daily --brief` |
| `nightly-close` | 22:00 daily | `bg review --daily` |
| `weekly-review` | Fri 18:00 | `bg review --weekly --agent` |
| `health-check` | Sun 21:00 | `bg health --full` |
| `source-health` | every 6 hrs | `bg health --sources` |
| `maintenance` | 02:00 daily | `python -m src.graph.maintenance` |
| `backup` | 03:00 daily | `scripts/backup.sh` |
| `vault-inbox` | every 5 min | `bg health --inbox` (cron fallback) |
The existing `process-keepmd.sh` (every 15 min) and `mesh-daily-report.sh`
(daily 8am) continue to run unchanged.

### Entry criteria

Phase 4 complete. `bg health`, `bg review`, and `bg daily` commands from
Phase 1 extended with the flags above.

### Exit criteria

Editing a file in Obsidian triggers a FalkorDB graph sync within seconds.
`beestgraph-vault-sync` survives reboot. New cron jobs run without errors.
Total running services: 7 (was 5).

---

## 9. Phase 6: Context Engine

**The LLM session primer.** Any LLM can now start a productive beestgraph
session without knowing anything in advance.

### `identity.md` template (new vault root file)

Written by the human, maintained by the human. Target length: under 1KB.
Structure:

```markdown
# Identity
**Who I am:** ...
**Current focus:** ...
**Active projects:** ...
**Recent major decisions:** ...
**LLM style preferences:** ...
```

### `bg context` command

```bash
bg context --level 0 # identity.md only (~500 tokens)
bg context --level 1 # + current daily note + top 3 active projects (~2K)
bg context --level 2 # + last 7 daily notes + board state (~5K)
bg context --level 3 # + full project state + graph stats (~15K)
```

No LLM required. Pure file-and-graph-reading operation that produces a
structured markdown bundle for pasting into any LLM context window.

### Entry criteria

Phase 5 complete. Sufficient real CLI usage to understand what context
levels practitioners actually need.

### Exit criteria

`bg context --level 1` produces a useful bundle in under 2K tokens. A cold
LLM session primed with the bundle can answer questions about current projects
without additional orientation.

---

## 10. Phase 7: Synthesis + Full Ingest Maturation

**The phase where the graph grows documents no human captured.** Phases 4 and
5 of the ingest pipeline reach stability.
By Phase 7, the `synthesis/` directory should be populated with a few
manually-triggered documents (from `bg think connect`) so the pattern is
validated before the automated pipeline adds to it.
The primary work of Phase 7 is:

- Hardening Phase 4 (synthesis) after real-world usage in Phase 6
- Tuning the contradiction detection threshold and LLM prompts from Phase 3
- Establishing a review workflow for auto-generated synthesis documents
  (they should never be silently accepted — always queue for human review)
- Adding the `bg think graduate` command (Phase 2 left it for later)
- Adding the `bg think forecast` command
  
  ### Entry criteria
  
  Phase 6 complete. At least 10 synthesis documents exist from manual
  `bg think connect` usage. Contradiction detection has produced at least 5
  true positives.
  
  ### Exit criteria
  
  A multi-source ingest session produces at least one synthesis document
  linking sources the human did not explicitly connect. Auto-generated synthesis
  documents route through the qualification queue before publication.

---

## 11. Merged Roadmap Summary

```
PRE-WORK (≤1 week)
 □ Wire zettelkasten.py into capture — inject uid on new documents
 □ Update ingester.py — MERGE on uid with path fallback
 □ Clear the 30-item qualification queue backlog
 (Telegram bot /queue, or Web UI :3001/queue, or 24-hr timeout)
PHASE 1 CLI Foundation (2–3 weeks)
 □ Create src/cli/ + Click/Typer entry point
 □ Register `bg` in pyproject.toml
 □ Implement 11 core commands (daily, task, find, project, health,
 init, capture, save, export, archive, ingest-v1)
 □ All commands implement run_without_agent / run_with_agent pattern
PHASE 2 Thinking Tools (2–3 weeks)
 □ Add six query functions to src/graph/queries.py
 □ Add key_claims full-text index to schema.py
 □ Implement bg think challenge/emerge/connect/audit/graduate/forecast
 □ Without-agent mode returns structured Cypher output
 □ With-agent mode adds LLM synthesis via --agent flag
PHASE 3 Migration (1–2 weeks)
 □ Write CONTEXT.md (LLM-agnostic system documentation)
 □ Create src/cli/agent.py — LLMAgent Protocol + AnthropicAgent
 □ Refactor processor.py to use LLMAgent interface
 □ Implement bg migrate (--dry-run, --uid-only, --frontmatter, --all)
 □ Run bg migrate on vault
 □ Delete CLAUDE.md, update all references
PHASE 4 Active Ingest (3–4 weeks)
 □ Create entities/ and raw/ vault directories
 □ Extend ingester.py with Phases 2-5 of rewrite-on-ingest
 □ Add bg ingest --active and --agent flags
 □ Entity page updates working (Phase 2 of ingest)
 □ Contradiction detection working (Phase 3 of ingest)
PHASE 5 Event-Driven Automation (2–3 weeks)
 □ Implement src/automation/watcher.py (full-vault sync)
 □ Create beestgraph-vault-sync.service systemd unit
 □ Implement src/automation/hooks.py (session-end hooks)
 □ Add new cron jobs to OpenClaw schedule
 □ Schedule existing src/graph/maintenance.py (long-overdue roadmap item)
PHASE 6 Context Engine (1–2 weeks)
 □ Write identity.md template + instructions
 □ Implement bg context --level 0/1/2/3
 □ Document LLM session startup workflow
PHASE 7 Synthesis + Full Ingest Maturation (ongoing)
 □ Validate synthesis/ pattern with manual bg think connect usage
 □ Harden ingest Phase 4 (synthesis) from real usage
 □ Route auto-generated synthesis through qualification queue
 □ Add bg think graduate and bg think forecast
```

---

## 12. What the Existing Roadmap Items Become

The as-built document's 12 roadmap items are all preserved. Their position
in the new phased plan:
| as-built item | New location |
|--------------|-------------|
| 1. Process 30 queue items | Pre-Work |
| 2. Build `bg` CLI | Phase 1 |
| 3. Schedule graph maintenance | Phase 5 |
| 4. Migrate to uid-based MERGE | Pre-Work |
| 5. `bg migrate` (frontmatter upgrade) | Phase 3 |
| 6. `bg think connect` | Phase 2 |
| 7. 3D visualization upgrade | Not addressed — remains on future roadmap |
| 8. Rewrite-on-ingest | Phase 4 |
| 9. Agent-to-agent skill invocation | Not addressed — remains on future roadmap |
| 10. Curated persistence policies / TTL | Not addressed — remains on future roadmap |
| 11. `bg think audit` | Phase 2 |
| 12. Public knowledge publishing | Not addressed — remains on future roadmap |
Items 7, 9, 10, and 12 are preserved on a future roadmap beyond Phase 7.
They do not conflict with anything in this plan. 3D visualization in
particular is a web UI concern that can proceed in parallel with any phase.

---

## 13. Test Coverage Expectations

The as-built system has 159 passing tests at 32% overall coverage. The new
code should extend, not erode, this baseline.
| New module | Minimum coverage target | What to test |
|-----------|------------------------|-------------|
| `src/cli/` | 70% | Command output, argument parsing, --dry-run behavior |
| `src/cli/agent.py` | 85% | LLMAgent interface, provider dispatch, error handling |
| `src/cli/commands/think/` | 80% | Cypher query results, structured output format |
| Extended `ingester.py` | 85% (existing baseline: 84%) | Phases 2-5, entity page updates, contradiction flagging |
| `src/automation/watcher.py` | 75% | File change detection, graph sync correctness |
The `run_without_agent` path of every command must have full test coverage
because it is the guaranteed-available path. `run_with_agent` tests can use
a mock `LLMAgent` that returns deterministic output.

---

## 14. Risk Register

| Risk                                                  | Likelihood | Impact | Mitigation                                                                                     |
| ----------------------------------------------------- | ---------- | ------ | ---------------------------------------------------------------------------------------------- |
| UID migration creates duplicate FalkorDB nodes        | Low        | Medium | Path fallback in ingester; dedup script in `maintenance.py` before migration                   |
| bg migrate corrupts frontmatter                       | Low        | High   | Always run `--dry-run` first; operate on vault backup for first run; keep `08-archive/` copies |
| Rewrite-on-ingest rewrites entity pages incorrectly   | Medium     | Medium | Phase 4 defaults to append-only (no LLM); rewrite only with explicit `--agent` flag            |
| Contradiction detection produces false positives      | High       | Low    | False positives go to a review queue, not directly into the graph                              |
| Full-vault watcher creates performance issues on Pi 5 | Medium     | Medium | Debounce writes; exclude 09-attachments/; add CPU throttle in service unit                     |
| Auto-generated synthesis documents pollute the vault  | Medium     | Medium | All synthesis documents route through 02-queue/ before publication                             |
| CLAUDE.md deletion breaks undocumented dependency     | Low        | High   | Grep the entire repo before deletion; keep a copy in 08-archive/ for 30 days                   |

---

*This document is the canonical integration plan for merging the next-gen
architecture into the deployed beestgraph system. Phases 1–7 can each be
reviewed and approved independently. No phase requires any other phase to be
complete before review begins — only before implementation begins.*
