# beestgraph: Active Vault Addendum

> Architectural addendum to the v1 Project White Paper
> 
> **Status:** Addendum, not a replacement
> **Relationship to v1:** Assumes the v1 whitepaper has been read
> **Date:** April 2026
> **Companion documents:** `beestgraph-whitepaper.md` (v1), `beestgraph-template.md` (template spec)

---

## What this addendum is

This is not a second whitepaper. It is an addendum to the original beestgraph project whitepaper, documenting how the architecture evolved after the initial build shipped. It assumes you have read the v1 whitepaper — it does not recap hardware choices, the FalkorDB selection rationale, the keep.md integration, or any of the decisions already captured there. Everything in the v1 whitepaper still holds. This document only covers what is *new* or *different*.
The addendum exists because three things happened after v1 shipped that collectively justified more than a section-level amendment:

1. **The template evolved significantly.** The v1 four-template system was consolidated into a single tiered universal template. The full specification now lives in `beestgraph-template.md` and is referenced, not duplicated, here.
2. **The architecture grew a new layer.** The obsidian-second-brain patterns — thinking tools, rewrite-on-ingest, identity/context engine, event-driven processing — were absorbed into beestgraph's design, but adapted to be graph-powered and LLM-agnostic rather than file-scanning and Claude-dependent.
3. **The agent layer was decoupled from Claude Code.** The v1 design assumed Claude Code as the primary agent with CLAUDE.md as configuration. The new design treats any LLM as a pluggable component and moves the system of record back into the graph schema, the frontmatter spec, and the Python pipeline.
   None of this invalidates v1. The hardware, the graph database, the capture layer, the MCP constellation, the OpenClaw scheduler, and the Tailscale networking all stand. What changed is the *shape of the software layer that sits on top*.

---

## Table of Contents

1. [Current State: Ground Truth](#1-current-state-ground-truth)
2. [The Core Shift: From CLAUDE.md to CONTEXT.md](#2-the-core-shift-from-claudemd-to-contextmd)
3. [The Four-Layer Model](#3-the-four-layer-model)
4. [Layer 1: Vault Operations](#4-layer-1-vault-operations)
5. [Layer 2: Thinking Tools](#5-layer-2-thinking-tools)
6. [Layer 3: Context Engine](#6-layer-3-context-engine)
7. [Layer 4: Automation](#7-layer-4-automation)
8. [The `bg` CLI (Aspirational)](#8-the-bg-cli-aspirational)
9. [Rewrite-on-Ingest: The Active Vault Pattern](#9-rewrite-on-ingest-the-active-vault-pattern)
10. [The Template Consolidation](#10-the-template-consolidation)
11. [Revised Vault Structure](#11-revised-vault-structure)
12. [LLM-Agnostic Agent Layer](#12-llm-agnostic-agent-layer)
13. [New Decisions Log](#13-new-decisions-log)
14. [Roadmap: What to Build Next](#14-roadmap-what-to-build-next)
15. [What Did Not Change](#15-what-did-not-change)

---

## 1. Current State: Ground Truth

Before describing the target architecture, it is worth being honest about what exists today versus what is aspirational. The gap is larger than the prose in the rest of this document might suggest, and the roadmap in Section 14 only makes sense with the starting line clearly marked.

### What exists and runs

- **FalkorDB container.** Running, indexed per the v1 schema, reachable via the FalkorDB Browser and the Python client.
- **The capture layer.** keep.md integration and Obsidian Web Clipper both working as described in v1. The `inbox/` folder receives items, though at the moment the qualification queue is the active path rather than direct ingest.
- **The pipeline components as standalone modules.** `watcher`, `poller`, `telegram_bot`, `heartbeat` all exist and run when invoked directly with `python -m`. They are not yet composed behind a unified CLI entry point.
- **The OpenClaw cron jobs.** Scheduled per v1, invoking the standalone modules.
- **The Tailscale network and remote administration.** Unchanged from v1.
- **The vault structure.** All ten numbered top-level directories exist (`00-meta` through `09-attachments`). Sixty-one markdown files populate the vault at the time of this addendum. The `01-inbox` folder is empty, meaning items are flowing through; `02-queue` holds about twelve items awaiting review; `07-resources` contains three processed documents. The infrastructure is alive but the knowledge base itself is still small.
  
  ### What does not exist yet
- **The `bg` CLI.** There is no `src/cli/` module, no Click or Typer entry point, no `bg` binary installed anywhere. Every `bg <command>` reference in this addendum and in the template spec — `bg ingest`, `bg daily`, `bg think audit`, `bg migrate`, `bg export --flat`, `bg archive`, `bg init`, all of them — describes a design target, not a shipping tool. The individual functions the CLI would orchestrate exist as Python modules, but the unified command-line experience that turns them into a coherent tool has not been built.
- **Rewrite-on-ingest.** The v1 ingest pipeline creates one new document node per source and MERGEs entity nodes. It does not yet update existing entity pages, detect contradictions, or synthesize cross-document connections. The expanded five-phase pipeline described in Section 9 is a design, not a running system.
- **Thinking tools.** No `bg think` command group exists. The graph queries that would back the thinking tools can be written in Cypher today against the running FalkorDB, but they have not been wrapped into CLI commands.
- **The context engine.** No `identity.md` has been written. No `bg context` command exists. CLAUDE.md has not yet been renamed or rewritten as CONTEXT.md.
- **Event-driven automation.** The file watcher module exists as a standalone script but is not wired into a systemd service or into an incremental graph sync pathway. Session-end hooks do not exist.
- **The migration utility.** No `bg migrate` command exists. Existing documents in the vault still use a mix of v1 and v2 frontmatter conventions and have not been migrated to the final template spec.
  
  ### Why this matters for the rest of the document
  
  The rest of this addendum describes the target state. When it says "the `bg` CLI does X," read that as "the `bg` CLI is designed to do X, and when built, it will work this way." The design is settled enough to commit to — these are not exploratory sketches — but none of it is shipping code yet. The roadmap in Section 14 sequences the build in a way that produces useful increments at each step rather than requiring the full architecture to land at once.

---

## 2. The Core Shift: From CLAUDE.md to CONTEXT.md

The single most important architectural change is philosophical, not technical: **the agent is no longer the system of record.**
In v1, CLAUDE.md was effectively configuration. It told Claude Code how to process documents, what entities to extract, how to structure summaries, and which Cypher patterns to use. The processing logic lived in the prompt, which meant the system was bound to Claude Code specifically. If you swapped Claude Code for Ollama, or for a future local model, you would lose the processing logic along with the agent.
In the new design, the system of record is three artifacts that exist independently of any LLM:

1. **The graph schema.** Defined in `src/graph/schema.py`. Nodes, relationships, indexes. Unchanged by which LLM is calling it.
2. **The frontmatter specification.** Defined in `beestgraph-template.md`. Fields, tiers, types, the flattening convention. Unchanged by which LLM is reading it.
3. **The Python pipeline.** Defined in `src/pipeline/`. Ingestion, parsing, graph writes, entity normalization. Runs with or without an LLM available.
   CLAUDE.md becomes CONTEXT.md — a documentation file that helps *any* LLM understand the beestgraph system, rather than a configuration file that Claude Code specifically depends on. An LLM reads CONTEXT.md to learn how the system works, then interacts with the vault and graph through the same interfaces a human or a Python script would use. The LLM is a consumer of the system, not a component of it.
   This change cascades into everything else in the addendum. The `bg` CLI can run without any LLM available. The thinking tools return useful structured output even when `--agent` is not passed. The rewrite-on-ingest pipeline has an LLM-free fallback for every phase. The vault and graph remain fully functional if the API goes down, if billing lapses, if a local model crashes, or if the user simply prefers not to invoke an LLM for a particular operation.
   The test is simple: pull the plug on every LLM the system can talk to. Does beestgraph still work? In the v1 design, the answer was "partially — capture still works but processing stops." In the new design, the answer is "yes — you lose prose synthesis and entity extraction from new sources, but everything you already have remains queryable, editable, and maintainable via CLI."

---

## 3. The Four-Layer Model

The v1 whitepaper described the system as four architectural layers: Capture, Processing, Storage, Access. That model is still accurate at the infrastructure level — it describes *where the bytes live and how they move*. But it does not describe *what the user can do with the system*, and that is where the new four-layer model comes in.
The new four layers are a **functional** stack, not an infrastructure stack. They sit on top of the v1 infrastructure layers rather than replacing them.

```
┌─────────────────────────────────────────────────────────────────┐
│ Functional Layers (new) │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Automation — the vault maintains itself │
│ Layer 3: Context Engine — the vault knows you │
│ Layer 2: Thinking Tools — the vault thinks with you │
│ Layer 1: Vault Operations — the vault remembers │
├─────────────────────────────────────────────────────────────────┤
│ Infrastructure Layers (v1) │
├─────────────────────────────────────────────────────────────────┤
│ Access — FalkorDB Browser, Telegram bot, SSH, web UI │
│ Storage — FalkorDB + Obsidian vault + Syncthing │
│ Processing — Python pipeline + MCP servers + OpenClaw │
│ Capture — keep.md + Obsidian Web Clipper + manual notes │
└─────────────────────────────────────────────────────────────────┘
```

Each functional layer adds capability on top of the infrastructure layers. Each is independently useful — you can have Layer 1 without Layer 2, Layer 2 without Layer 3, Layer 3 without Layer 4. And each layer has a defined position on the LLM-requirement spectrum:
| Layer | Requires FalkorDB? | Requires LLM? |
|---|---|---|
| Vault Operations (basic) | No | No |
| Vault Operations (smart) | Yes | Optional |
| Thinking Tools (queries) | Yes | No |
| Thinking Tools (synthesis) | Yes | Yes |
| Context Engine | No | No |
| Automation (scheduled) | Yes | Optional |
| Automation (event-driven) | Optional | No |
The minimum viable beestgraph is an Obsidian vault plus the `bg` CLI — no graph database, no LLM, still useful. Add FalkorDB and you unlock graph-powered search and thinking tool queries. Add an LLM and you unlock synthesis, rewrite-on-ingest, and prose generation. Every intermediate configuration is valid.

---

## 4. Layer 1: Vault Operations

The base layer: commands that read from and write to the vault and graph. Mostly script-level Python, no LLM required for most operations.
The core Vault Operations commands are:

```
bg save extract decisions/tasks/entities from a transcript or conversation
bg ingest URL/PDF/transcript → rewrite-on-ingest pipeline
bg reconcile detect and resolve contradictions across the graph
bg daily create or update today's daily note
bg log log a work session
bg task add a task to the right board
bg person create or update a person entity page
bg decide log a decision with context
bg capture zero-friction idea capture
bg find graph-powered semantic + structural search
bg recap narrative summary of a period
bg review structured weekly or monthly review
bg project create or update a project note
bg health vault audit
bg init bootstrap vault + graph from existing files
bg adr create an architectural decision record
```

None of these exist today. The functionality behind most of them exists as standalone Python modules — `watcher`, `poller`, the Telegram bot, the heartbeat — but there is no unified CLI that composes them. The target is that every one of these commands runs as a single shell invocation, with or without an LLM.
The universal command pattern:

```python
class Command:
 def run_without_agent(self, args) -> Result:
 """Mechanical work: graph queries, file operations, template rendering."""
 ...
 def run_with_agent(self, args, agent: LLMAgent) -> Result:
 """Calls run_without_agent() first, then passes results to an LLM
 for reasoning, prose generation, or multi-page vault updates."""
 base_result = self.run_without_agent(args)
 return agent.enhance(base_result, self.agent_prompt)
```

This pattern is the fundamental contract of the `bg` CLI: every command has an LLM-free path that does the mechanical work, and an optional LLM-enhanced path that adds reasoning on top. The LLM-free path is never a degraded version — it is the real command. The LLM-enhanced path is additive.
---

## 5. Layer 2: Thinking Tools

Layer 2 is where beestgraph's FalkorDB backend earns its keep. The thinking tools are borrowed in concept from obsidian-second-brain, but adapted to be **graph-powered** rather than file-scanning-powered. The difference compounds with vault size: file scanning degrades linearly as the vault grows; graph queries remain near-constant.
Six thinking tools are in the design:

- **`bg think challenge [topic]`** — argue against your own history on a topic. Without an LLM: returns structured evidence from related decisions, contradictions, and reversed/abandoned choices. With an LLM: synthesizes the evidence into a prose counter-argument written in second person.
- **`bg think emerge [--period 30d]`** — surface unnamed patterns across recent documents. Without an LLM: runs tag-frequency, co-occurring-entity, and community-detection queries. With an LLM: names the patterns and explains their significance.
- **`bg think connect [A] [B]`** — bridge two concepts or documents. Without an LLM: returns shortest-path and shared-neighbor graph queries. With an LLM: writes a synthesis essay explaining the bridge.
- **`bg think graduate [idea]`** — promote an idea from a fleeting note to a full project scaffold. Without an LLM: creates the project directory, templates, and cross-links. With an LLM: fills in project description, generates initial tasks, identifies related existing work.
- **`bg think forecast [topic]`** — new to beestgraph, not in obsidian-second-brain. Without an LLM: plots temporal frequency of topic mentions and shows trend direction. With an LLM: projects forward and identifies what is accelerating or decelerating in your thinking.
- **`bg think audit [claim]`** — new to beestgraph. Without an LLM: finds all documents supporting or contradicting a specific claim via full-text search and `SUPPORTS`/`CONTRADICTS` edge traversal. With an LLM: evaluates source quality, recency, and whether the claim still holds.
  Every thinking tool follows the same two-phase pattern: a Cypher query against FalkorDB returns the raw evidence, and the LLM (if present) synthesizes the evidence into prose. The queries are the source of truth; the LLM output is a presentation layer.
  Concrete example — `bg think challenge` runs three graph queries:
  
  ```cypher
  -- Step 1: Related decisions on the topic
  MATCH (d:Document)-[:MENTIONS]->(c:Concept {normalized_name: $topic})
  WHERE d.type IN ['decision', 'adr', 'journal']
  RETURN d.title, d.summary, d.dates_created
  ORDER BY d.dates_created DESC;
  -- Step 2: Existing contradictions in the topic area
  MATCH (d1:Document)-[:CONTRADICTS]->(d2:Document)
  WHERE d1.title CONTAINS $topic OR d2.title CONTAINS $topic
  RETURN d1.title, d2.title, d1.summary, d2.summary;
  -- Step 3: Reversed or abandoned decisions
  MATCH (d:Document {type: 'decision'})-[:BELONGS_TO]->(t:Topic)
  WHERE t.name CONTAINS $topic_domain
  AND (d.summary CONTAINS 'reversed' OR d.summary CONTAINS 'abandoned')
  RETURN d.title, d.summary;
  ```
  
  The output without an agent is three structured lists. The output with an agent is the same three lists, plus a 500-word prose counter-argument. Both are useful; the first is always available; the second is a paid upgrade.

---

## 6. Layer 3: Context Engine

The context engine is the layer that lets any LLM — not just Claude Code — begin a productive session with the vault. It has two components: a human-written `identity.md` at the vault root, and the `bg context` command that assembles progressive context bundles.

### `identity.md`

A small file at the vault root, written and maintained by the human, read by any LLM at session start. It replaces the SOUL.md concept from obsidian-second-brain with a less dramatic name. It contains the irreducible minimum context an LLM needs to understand the user it is helping:

- Who the user is
- What the user is currently focused on
- The user's active projects and their rough state
- Any recent major decisions or context shifts
- Tone and style preferences for how the LLM should communicate
  The file is intentionally short — target length is under a kilobyte. It is the first thing any LLM loads when the user begins a session, before any document-specific context.
  
  ### `bg context`
  
  Progressive context loading. Four levels, each adding more detail:
  
  ```
  bg context --level 0 identity only (~500 tokens)
  bg context --level 1 + current focus (~2K tokens)
  bg context --level 2 + recent activity (~5K tokens)
  bg context --level 3 + full project state (~15K tokens)
  ```
  
  The command assembles the bundle by reading `identity.md`, recent daily notes, board state, active project files, and graph statistics, then formats the output as structured markdown that any LLM can consume as a system prompt or opening user message. It does not require an LLM to run. It is purely a file-and-graph-reading operation that produces a text bundle.
  This gives the user a clean way to start a session with any LLM: run `bg context --level 1`, paste the output into the LLM's context window, and proceed. The LLM now knows who you are and what you are working on, without beestgraph needing to own the LLM runtime.

---

## 7. Layer 4: Automation

The automation layer supplements the v1 OpenClaw cron jobs with event-driven processing. The scheduled jobs do not go away — they remain the backbone of periodic maintenance. But for operations that should happen as soon as a trigger fires rather than at the next cron tick, the system adds file watchers and session hooks.

### Scheduled jobs (from v1, expanded)

```
morning-brief 07:00 daily daily note + overdue tasks
nightly-close 22:00 daily close out day, move tasks
weekly-review Fri 18:00 structured review
health-check Sun 21:00 full vault audit
keepmd-inbox */15 min poll keep.md for new items
vault-inbox */5 min watch inbox/ folder (supplemented by watcher)
source-health */6 hours verify source URLs still resolve
maintenance 02:00 daily dedup, orphans, analytics
backup 03:00 daily BGSAVE + rsync
```

### Event-driven jobs (new)

```
on-file-change incremental graph sync when a .md file changes in the vault
on-session-end prompt to save session knowledge when a bg session closes
on-commit trigger health check when the vault git repo gets a commit
```

The file watcher is the most important of these. In v1, a new document in the inbox waits up to five minutes for the next cron tick. With the watcher running, the graph updates within seconds of the file appearing. For interactive work — where the user is writing a document and then immediately wants to query the graph for related content — the latency difference matters.
The watcher exists today as a standalone Python module. What is missing is the systemd service that runs it as a supervised background process, and the integration with the pipeline that turns a detected file change into an incremental graph update.

---

## 8. The `bg` CLI (Aspirational)

This section describes the target design of the `bg` CLI. **None of it exists yet.** The functions it would orchestrate exist as modules; the unified CLI that turns them into a tool does not. This section is design spec, not documentation of shipping software.

### Invocation pattern

```
bg <command> [subcommand] [args] [--flags]
Global flags:
 --agent Enable LLM reasoning (default: off)
 --model <name> LLM to use (default: from config/agent.toml)
 --dry-run Show what would change without writing
 --verbose Show graph queries and reasoning steps
 --json Output as JSON instead of markdown
```

Every command is usable without any LLM. The `--agent` flag is opt-in. The default behavior is mechanical.

### Examples without an LLM

```bash
bg daily # create today's daily note
bg task "Fix auth middleware" --project api # add a task
bg find "knowledge graphs" --type concept # graph search
bg project api-launch --status # project status
bg health # vault audit
bg context --level 1 # context bundle
bg reconcile --dry-run # preview contradictions
```

### Examples with an LLM

```bash
bg ingest https://example.com/article --agent # rewrite-on-ingest
bg save --input transcript.md --agent # categorize a conversation
bg think challenge "rewrite in Rust" --agent # counter-argument
bg think emerge --period 30d --agent # pattern surfacing
bg review --agent # narrative weekly review
```

### Target implementation structure

```
src/cli/
├── __init__.py
├── main.py # Click or Typer entry point
├── commands/
│ ├── daily.py
│ ├── task.py
│ ├── find.py
│ ├── save.py
│ ├── ingest.py
│ ├── project.py
│ ├── person.py
│ ├── decide.py
│ ├── capture.py
│ ├── recap.py
│ ├── review.py
│ ├── health.py
│ ├── reconcile.py
│ ├── adr.py
│ ├── init.py
│ ├── context.py
│ └── think/
│ ├── challenge.py
│ ├── emerge.py
│ ├── connect.py
│ ├── graduate.py
│ ├── forecast.py
│ └── audit.py
├── agent.py # pluggable LLM adapter
└── graph.py # shared FalkorDB query helpers
```

### Entry point registration

```toml
# pyproject.toml
[project.scripts]
bg = "beestgraph.cli.main:app"
```

After a `pip install -e .`, the `bg` command is on `$PATH` and every subcommand is dispatched through a single Click or Typer app.

### The command contract

Every command in the CLI follows the same skeleton:

```python
class Command:
 name: str
 requires_graph: bool = True
 requires_llm: bool = False
 agent_prompt: str = ""
 def run_without_agent(self, args) -> Result:
 """The real command. Graph queries, file operations,
 template rendering. Must produce a useful result."""
 raise NotImplementedError
 def run_with_agent(self, args, agent: LLMAgent) -> Result:
 """Calls run_without_agent() first, passes the result
 to the LLM adapter for synthesis. Optional enhancement."""
 base = self.run_without_agent(args)
 if not self.agent_prompt:
 return base
 return agent.enhance(base, self.agent_prompt)
```

This contract is the reason the CLI can make the LLM optional. The mechanical path is always defined. The LLM path is an enhancement that can be swapped out per provider without touching the rest of the command.
---

## 9. Rewrite-on-Ingest: The Active Vault Pattern

The biggest behavioral change from v1. In v1, ingesting a source creates one new document node and MERGEs the entities it mentions. The new document joins the graph; existing documents are unchanged. In the new design, ingesting a source triggers a five-phase pipeline that can touch dozens of existing pages.

### The v1 ingest pipeline

```
URL → fetch → parse → create 1 new Document node → create entity nodes → done
```

### The new ingest pipeline

```
URL → fetch → parse → Phase 1: Create/update document
 → Phase 2: Update existing entity pages
 → Phase 3: Detect contradictions
 → Phase 4: Synthesize connections
 → Phase 5: Update index.md and log.md
```

### Phase 1: Create or update document (script-level)

Same as the v1 pipeline. MERGE the document node, create tags, topics, and entity relationships. No LLM required.

### Phase 2: Update existing entity pages (script + optional LLM)

For each entity extracted from the new document, find the entity's existing vault page and update it. Without an LLM, this is a mechanical append — the new document gets added to the entity's reference list. With an LLM, the entity page gets rewritten to incorporate the new information into the existing narrative.

```python
def update_entity_page(entity_name: str, new_doc: Document, agent: Optional[LLMAgent]):
 entity_path = find_entity_file(entity_name)
 docs = graph.query("""
 MATCH (d:Document)-[:MENTIONS]->(e {normalized_name: $name})
 RETURN d.title, d.summary, d.dates_created, d.source_url
 ORDER BY d.dates_created DESC
 """, name=normalize(entity_name))
 if agent is None:
 append_reference(entity_path, new_doc)
 else:
 rewrite_entity_page(entity_path, docs, new_doc, agent)
```

This is where the `entities/` directory in the new vault structure earns its existence. Entity pages become living documents that accumulate context over time, rather than static stubs that only hold a definition.

### Phase 3: Detect contradictions (script-level)

For each `key_claim` in the new document, run a full-text search for related existing documents and flag potential contradictions. Without an LLM, this produces a list of "possible contradictions needing human review." With an LLM, the agent evaluates whether each is a genuine contradiction, creates `CONTRADICTS` relationships where appropriate, and updates both documents' `connections.contradicts` frontmatter.

```python
def detect_contradictions(new_doc: Document):
 claims = new_doc.frontmatter.get('key_claims', [])
 for claim in claims:
 related = graph.query("""
 CALL db.idx.fulltext.queryNodes('Document', $claim_text)
 YIELD node AS d, score
 WHERE score > 0.5 AND d.path <> $new_path
 RETURN d.path, d.title, d.summary, d.key_claims, score
 """, claim_text=claim, new_path=new_doc.path)
 # With agent: evaluate each match, create CONTRADICTS edges if real
```

### Phase 4: Synthesize connections (agent-only)

Phase 4 runs only with `--agent`. The LLM receives the new document plus the five most related existing documents (by graph proximity and full-text similarity) and is asked whether there are unnamed patterns, novel connections, or synthesis opportunities that warrant a new document.
If yes, a new synthesis note is created in the `synthesis/` directory with `type: synthesis`, `content_stage: evergreen`, and `connections.*` fields linking to all source documents. This is the mechanism by which the graph grows new nodes that did not come from any single captured source.

### Phase 5: Update navigation files (script-level)

Two append-only operations:

- `index.md` at the vault root gets a new entry in the appropriate topic section.
- `log.md` at the vault root gets a chronological record of what was ingested, which pages were updated, which contradictions were flagged, and whether a synthesis document was created.
  Both files are auto-maintained. The user does not edit them directly — they are the system's own record of its activity.
  
  ### Metrics after each ingest
  
  ```
  Ingested: "Article Title"
  New document: knowledge/concepts/knowledge-graphs.md
  Updated entities: 3 (FalkorDB, Cypher, GraphRAG)
  Contradictions: 1 flagged (vs. "Neo4j Performance Claims" from March)
  Connections: 2 new RELATED_TO edges
  Synthesis: created synthesis/graph-native-ai.md
  Pages touched: 6
  ```
  
  The "pages touched" count is the metric that distinguishes active ingest from passive ingest. In v1, every ingest touches exactly one page (the new document). In the active vault, a single ingest routinely touches five to fifteen pages.

---

## 10. The Template Consolidation

The template evolution is documented in full in `beestgraph-template.md` and is not duplicated here. The short version, for readers of this addendum who have not yet read that spec:
The v1 four-template system (`article.md`, `concept.md`, `project.md`, `person.md`) was consolidated into a single universal template with a three-tier field organization. Tier 1 fields (eight of them) appear on every document. Tier 2 fields appear when the document type warrants them, driven by a type registry. Tier 3 fields exist in the spec but are only populated when there is a demonstrated, recurring need.
The key changes from the v1 templates:

- **`uid` field** added as an immutable timestamp-based primary key, decoupling document identity from filename and path.
- **Temporal model expanded** to eleven dimensions, distinguishing file creation, information capture, source publication, agent processing, human modification, human review, agent synthesis, knowledge expiration, and archival.
- **`connections.*` relationships** added as first-class frontmatter fields with a mandatory mirroring rule: every connection in the frontmatter must also appear as an inline wikilink in the document body, because Obsidian's backlink graph does not index frontmatter links.
- **Engagement statuses reduced** from five values to three (`unread`, `read`, `reference`) based on field reports that longer ladders get abandoned.
- **Nested canonical format** with a documented flat-export convention for tool interoperability.
  All v1 and v2 frontmatter continues to parse correctly. Migration is opportunistic — documents upgrade to the final spec as they are re-processed, and a `bg migrate` command (aspirational, not built) can bulk-upgrade on demand.
  The template spec is the authoritative reference for all frontmatter questions. If the addendum and the template spec disagree, the template spec wins.

---

## 11. Revised Vault Structure

The v1 vault structure continues to hold at the top level — the numbered directory scheme (`00-meta` through `09-attachments`) is the active layout today. The new additions are three directories that serve the active vault pattern:

```
vault/
├── 00-meta/ (v1 — unchanged)
├── 01-inbox/ (v1 — unchanged)
├── 02-queue/ (v1 — unchanged)
├── ...
├── entities/ NEW — dedicated pages for people, orgs, tools,
│ concepts, places. Rewritten on every
│ ingest that mentions them.
├── synthesis/ NEW — auto-generated documents that bridge
│ domains. Created by bg think connect or
│ by the ingest pipeline when it detects
│ unnamed patterns.
├── raw/ NEW — immutable source captures. The original
│ fetched content, never edited. Provides
│ provenance and allows re-processing.
├── identity.md NEW — user identity for LLM context loading
├── index.md NEW — auto-maintained table of contents
├── log.md NEW — auto-maintained activity log
└── CONTEXT.md RENAMED from CLAUDE.md, made LLM-agnostic
```

None of the new directories or files exist in the vault today. They are additions the `bg init` command would create, and additions the rewrite-on-ingest pipeline would populate as it ran.
The `entities/` directory is the most important of the three. It is the structural home of the living-document pattern — the place where accumulated context about recurring entities lives and grows. Without `entities/`, the rewrite-on-ingest pipeline has no canonical location to update. With it, the pattern works.

---

## 12. LLM-Agnostic Agent Layer

The pluggable LLM adapter is the concrete mechanism behind the "agent is not the system of record" principle from Section 2.

### `config/agent.toml`

```toml
[agent]
default_provider = "anthropic"
default_model = "claude-sonnet-4-6"
[providers.anthropic]
api_key_env = "ANTHROPIC_API_KEY"
base_url = "https://api.anthropic.com"
[providers.ollama]
base_url = "http://localhost:11434"
default_model = "llama3.1:70b"
[providers.openai_compatible]
base_url = "http://localhost:8080/v1"
api_key_env = "LOCAL_LLM_KEY"
```

### The `LLMAgent` interface

```python
class LLMAgent(Protocol):
 def enhance(self, base_result: Result, prompt: str) -> Result:
 """Take a mechanical result and an enhancement prompt,
 return the result augmented with LLM-generated content."""
 ...
 def synthesize(self, documents: list[Document], prompt: str) -> str:
 """Multi-document synthesis for rewrite-on-ingest Phase 4."""
 ...
 def rewrite(self, existing: str, context: str, prompt: str) -> str:
 """In-place rewrite of an entity page with new context."""
 ...
```

Three concrete implementations ship:

- `AnthropicAgent` — uses the Anthropic API. The default.
- `OllamaAgent` — uses a local Ollama instance. Useful for privacy-sensitive operations or when offline.
- `OpenAICompatibleAgent` — uses any OpenAI-compatible endpoint. Works with LM Studio, vLLM, text-generation-webui, and similar.
  The adapter pattern means adding a new provider is a matter of writing a new class that implements the three methods. No changes to the CLI commands, the pipeline, or the graph layer.
  
  ### What moves out of CLAUDE.md
  
  The v1 CLAUDE.md contained three categories of content: system documentation, processing instructions, and Cypher query templates. In the new design, these move to three different homes:
- **System documentation** → `CONTEXT.md`, written to be LLM-agnostic. Any LLM reads this to understand beestgraph.
- **Processing instructions** → the Python pipeline. The pipeline knows how to parse frontmatter, extract entities, and write to the graph. The LLM is invoked only where prose synthesis or judgment is required.
- **Cypher query templates** → `src/graph/queries.py`. Hardcoded in Python, callable from both the pipeline and the CLI. The LLM does not write Cypher; it consumes the results.
  This separation is what makes the system survive LLM substitution. The processing logic does not live in any prompt. It lives in Python.

---

## 13. New Decisions Log

These are additions to the v1 Key Decisions Log, not replacements. The v1 log continues to hold for the decisions it documents.
| Decision | Chosen | Alternatives | Rationale |
|---|---|---|---|
| Agent coupling | LLM-agnostic adapter | Claude Code as system of record | Survives LLM substitution; graph + pipeline + frontmatter are the system of record |
| CLI entry point | Unified `bg` command | Individual `python -m` invocations | Discoverability, composability, shell autocomplete, single install surface |
| Template organization | Three-tier universal | v1 four templates; v2 flat universal | Tier system prevents blank-field proliferation; evolved from PKM practitioner field reports |
| Canonical YAML format | Nested | Flat kebab-case | Nested communicates structure; flat-export convention covers interop |
| Document identity | `uid` (timestamp) | filename/path | Path independence; survives rename and move |
| Temporal model | Eleven dimensions | Single date field | Powers the highest-value queries in mature vaults |
| Connection storage | Frontmatter + body mirror | Frontmatter only; body only | Obsidian does not index frontmatter links; mirroring keeps both layers in sync |
| Engagement statuses | Three values | Five values (v2) | Field reports converge: longer ladders get abandoned |
| Entity page pattern | Living documents in `entities/` | Static stubs | Enables rewrite-on-ingest; accumulates context over time |
| Ingest pattern | Rewrite-on-ingest (5 phases) | Append-on-ingest (1 phase) | Single ingest updates 5-15 related pages; synthesis opportunities surface |
| Context loading | Progressive `identity.md` + `bg context` | Full CLAUDE.md dump | Lighter token budget; LLM-agnostic; usable in any session |
| Thinking tools backend | FalkorDB graph queries | Filesystem scanning | Scales with vault size; sub-second latency on personal-scale graphs |
| Automation model | Cron (v1) + event-driven | Cron only | Sub-second feedback for interactive work; cron still handles periodic maintenance |
| Contradiction detection | Full-text + `key_claims` + optional LLM judgment | Manual only | Catches conflicts that manual review misses; human still arbitrates |
| Synthesis generation | Phase 4 of ingest pipeline, LLM-only | Separate command | Captures connections while context is fresh in the processing window |

---

## 14. Roadmap: What to Build Next

A suggested sequence that produces useful increments at each step rather than requiring the full architecture to land at once. Each phase is independently shippable — after any phase, the system is strictly better than it was before, and you can stop and catch your breath.

### Phase 1: CLI Foundation (the biggest unlock)

Build the `bg` CLI with the core commands that do not require an LLM: `daily`, `task`, `find`, `project`, `health`, `init`, `capture`, `context`. All script-level. All invoking existing Python modules. No new processing logic. The deliverable is a single installable CLI that turns the currently scattered `python -m <module>` invocations into a coherent command-line tool.
This is the phase that has the highest value-per-unit-effort. Most of the code exists; it just needs to be composed behind a single entry point. After Phase 1, the user can do 80% of what the new architecture promises — they just cannot do the LLM-enhanced parts yet.
Entry criteria: Click or Typer installed, `src/cli/` directory created, `pyproject.toml` script registered. Exit criteria: `bg daily` creates today's note, `bg find` searches the graph, `bg health` audits the vault, and `bg --help` shows a useful command tree.

### Phase 2: Thinking Tools (the value demo)

Implement `bg think` subcommands backed by FalkorDB queries. Start without LLM support — every command returns structured query output. `bg think challenge`, `bg think emerge`, `bg think connect`, `bg think audit` are the first four. `graduate` and `forecast` can come later.
This phase is the one that makes the graph database earn its rent. Before Phase 2, FalkorDB is storage. After Phase 2, FalkorDB is a thinking partner.
Entry criteria: Phase 1 complete. Exit criteria: all four initial thinking tools return useful Cypher-backed output, documented with example invocations.

### Phase 3: CLAUDE.md → CONTEXT.md + Migration

Rename CLAUDE.md to CONTEXT.md. Rewrite its contents to be LLM-agnostic. Move processing instructions into the Python pipeline and Cypher templates into `src/graph/queries.py`. Build the `bg migrate` command and run it against the existing vault to upgrade all documents to the final template spec.
This is the philosophical commit. Before Phase 3, the system still assumes Claude Code. After Phase 3, the system is provably LLM-agnostic.
Entry criteria: Phase 2 complete. Exit criteria: CLAUDE.md does not exist in the repo; CONTEXT.md exists; `bg migrate --dry-run` reports accurately; one test run of `bg migrate` on a copy of the vault produces clean output.

### Phase 4: Active Ingest (Phases 1-3 of the rewrite-on-ingest pipeline)

Upgrade `bg ingest` to the five-phase pipeline, but only the first three phases initially. Phase 1 stays as it is. Phase 2 adds entity page updates (without LLM: append references; with LLM: rewrite). Phase 3 adds contradiction detection (without LLM: flag for review; with LLM: create edges). Phases 4 and 5 wait for later.
This is the phase that requires the `entities/` directory. Building Phase 4 requires creating the directory convention, writing the initial entity templates, and deciding how entity files are named (canonical name as filename, with `aliases` in frontmatter).
Entry criteria: Phase 3 complete. Exit criteria: ingesting a URL that mentions an existing entity updates the entity's page; ingesting a URL whose key_claims conflict with existing documents flags a contradiction.

### Phase 5: Event-Driven Automation

Wire the existing watcher module into a systemd service. Implement incremental graph sync on file change. Add session-end hooks and the on-commit trigger.
Entry criteria: Phase 4 complete. Exit criteria: editing a file in Obsidian triggers a graph update within seconds; the watcher service survives reboot.

### Phase 6: Context Engine + Identity

Write the `identity.md` template. Implement `bg context` with the four progressive levels. Document the intended workflow for starting an LLM session with a context bundle.
Entry criteria: Phase 5 complete. Exit criteria: `bg context --level 1` produces a usable bundle in under 2K tokens; a cold LLM session primed with the bundle can answer questions about current projects.

### Phase 7: Synthesis + Full Ingest

Add Phases 4 and 5 to the rewrite-on-ingest pipeline — synthesis generation and navigation file updates. This is the phase where the vault starts growing documents that no human captured directly.
Entry criteria: Phase 6 complete. Exit criteria: a multi-source ingest session produces at least one synthesis document linking sources the human did not explicitly connect.

### Why this ordering

Phase 1 is first because it has the highest value-per-effort and unblocks everything else. Phase 2 is second because it is the demo that justifies the graph database. Phase 3 comes before Phase 4 because the migration command needs to exist before the new template conventions become structural assumptions. Phase 4 is split at Phase 3 of the ingest pipeline because contradiction detection is useful even without synthesis, and synthesis is the riskiest phase to get right. Phase 5 is after Phase 4 because the watcher is more useful once there is rewrite-on-ingest to feed. Phase 6 is deferred because the context engine is the layer most sensitive to how the user ends up using the CLI in practice — better to build it after there is real usage to learn from. Phase 7 is last because synthesis generation only earns its complexity once the simpler phases are stable.
An aggressive timeline for all seven phases is three months of focused evening work. A realistic timeline is six months. A conservative timeline is "whenever Phase 1 is done, re-evaluate."

---

## 15. What Did Not Change

It is worth enumerating what the v1 whitepaper got right and what continues to hold, because the addendum's scope is easy to over-read. Everything in this list is unchanged from v1:

- **Hardware platform.** Raspberry Pi 5 with 16GB RAM, 2TB NVMe, PCIe Gen 3. The memory budget, cooling requirements, and power budget all stand.
- **Graph database.** FalkorDB. The selection rationale (ARM64, low memory, full-text search, OpenCypher) still holds. The Graphiti decision still holds.
- **Capture layer.** keep.md and Obsidian Web Clipper. The two-tier capture architecture.
- **MCP server constellation.** The three-server design (keep.md, Filesystem, FalkorDB) continues.
- **Scheduled automation.** OpenClaw cron jobs remain the backbone of periodic maintenance. Event-driven automation supplements them, does not replace them.
- **Network security.** Tailscale. Remote administration via SSH through the Tailnet.
- **Obsidian sync.** Syncthing. The vault continues to be a plain filesystem directory.
- **Storage layer.** FalkorDB + Obsidian vault + Syncthing.
- **Repository structure.** The subagent-based build methodology. Python 58%, TypeScript 30%, Shell 10% proportions broadly hold.
- **License.** MIT.
  The v1 whitepaper is the foundation this addendum builds on. It is the documentation of the system as it was first built. The addendum is the documentation of where the system is heading next. Both documents are canonical for their respective scopes, and neither replaces the other.

---

*This addendum should be read alongside the v1 whitepaper and the template specification. When the three documents disagree, the template spec wins on frontmatter questions, this addendum wins on architectural questions about the active vault pattern and the `bg` CLI, and the v1 whitepaper wins on everything else.*
