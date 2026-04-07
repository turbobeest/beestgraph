# beestgraph: Active Vault Integration

> Merging the "living knowledge base" pattern from obsidian-second-brain
> into beestgraph's graph-native architecture — LLM-supported, not LLM-dependent.
> 
> April 2026

---

## The Design Principle

**The vault and graph must be fully functional with zero AI running.**
Every feature described here works at three levels:
| Level | How it works | Example |
|-------|-------------|---------|
| **Manual** | Human uses Obsidian + FalkorDB Browser directly | You open a note, update frontmatter, run a Cypher query |
| **Script** | Python CLI tools do the mechanical work | `bg think challenge --topic "API rewrite"` runs graph queries, formats output |
| **Agent** | An LLM (any LLM) adds reasoning on top of scripts | Claude/Ollama reads script output, writes prose synthesis, updates vault |
The AI never owns the data model. It reads from and writes to the same markdown + FalkorDB structures that a human or a Python script would. Swap Claude for Ollama, GPT, Gemini, or a future local model — the vault doesn't notice.
This means:

- **No CLAUDE.md as the system of record.** The system of record is the graph schema, the frontmatter spec, and the Python pipeline. A `CONTEXT.md` file exists to help *any* LLM understand the system, but it's documentation, not configuration.
- **No Claude Code slash commands.** Instead: a CLI (`bg`) that works standalone, plus optional LLM wrappers. `/obsidian-save` becomes `bg save` at the script level and `bg save --agent` when you want LLM reasoning.
- **No assumption about which LLM.** The agent layer takes a `--model` flag or reads from `config/agent.toml`. Default: Anthropic API. Alternatives: Ollama (local), OpenAI, any OpenAI-compatible endpoint.

---

## What We're Absorbing from obsidian-second-brain

Six ideas, adapted to beestgraph's architecture:

### 1. Thinking Tools (the standout feature)

obsidian-second-brain's Layer 2 — `challenge`, `emerge`, `connect`, `graduate` — is the highest-value addition. But in beestgraph, these are *graph-powered*, not file-scanning-powered. The difference is enormous at scale.

### 2. Rewrite-on-Ingest (not append-on-ingest)

Their `/ingest` touches 5–15 existing pages per source. beestgraph currently creates one new document and MERGE-es entity nodes. The upgrade: ingestion should also update existing entity pages, flag contradictions, and trigger synthesis.

### 3. The Two-Output Rule

Every interaction that produces knowledge should also update the vault. Not just scheduled cron processing — real-time propagation during interactive sessions.

### 4. Identity / Context Engine

A `SOUL.md` (we'll call it `identity.md`) that any LLM reads first for progressive context loading. Lighter than dumping the entire CONTEXT.md.

### 5. Background / Event-Driven Processing

Supplement scheduled crons with event-triggered processing — file watchers, git hooks, session-end hooks.

### 6. Proactive Maintenance

The vault detects its own problems: stale claims, contradictions, orphan nodes, concept gaps. Not just in a weekly report — continuously.
---

## Architecture: The Four Layers (Revised)

```
┌─────────────────────────────────────────────────────────────────┐
│ beestgraph │
├─────────────────────────────────────────────────────────────────┤
│ │
│ LAYER 1: Vault Operations │
│ "The vault remembers" │
│ │
│ Works: manually, via CLI, or via agent │
│ │
│ bg save — extract decisions/tasks/entities from text │
│ bg ingest — URL/PDF/transcript → rewrite-on-ingest │
│ bg reconcile — detect and resolve contradictions │
│ bg daily — create/update daily note │
│ bg log — log a work session │
│ bg task — add task to the right board │
│ bg person — create/update person entity │
│ bg decide — log a decision with context │
│ bg capture — zero-friction idea capture │
│ bg find — graph-powered semantic + structural search │
│ bg recap — narrative summary of a period │
│ bg review — structured weekly/monthly review │
│ bg project — create/update project note │
│ bg health — vault audit │
│ bg init — bootstrap vault + graph from existing files │
│ bg adr — architectural decision record │
│ │
├─────────────────────────────────────────────────────────────────┤
│ │
│ LAYER 2: Thinking Tools │
│ "The vault thinks with you" │
│ │
│ Requires: FalkorDB (for graph queries) │
│ Enhanced by: any LLM (for prose synthesis) │
│ │
│ bg think challenge [topic] — argue against your own history │
│ bg think emerge [period] — surface unnamed patterns │
│ bg think connect [A] [B] — bridge unrelated domains │
│ bg think graduate [idea] — idea → full project scaffold │
│ bg think forecast [topic] — project forward from trends │
│ bg think audit [claim] — check a claim against sources │
│ │
├─────────────────────────────────────────────────────────────────┤
│ │
│ LAYER 3: Context Engine │
│ "The vault knows you" │
│ │
│ bg context — progressive context for any LLM session │
│ bg context --level 0 — identity only (~500 tokens) │
│ bg context --level 1 — + current focus (~2K tokens) │
│ bg context --level 2 — + recent activity (~5K tokens) │
│ bg context --level 3 — + full project state (~15K tokens) │
│ │
│ Reads: identity.md, recent daily notes, board state, │
│ active projects, graph stats │
│ Outputs: structured markdown any LLM can consume │
│ │
├─────────────────────────────────────────────────────────────────┤
│ │
│ LAYER 4: Automation │
│ "The vault maintains itself" │
│ │
│ Scheduled (cron / OpenClaw / systemd timer): │
│ morning-brief — 7 AM, daily note + overdue tasks │
│ nightly-close — 10 PM, close out day, move tasks │
│ weekly-review — Friday 6 PM, structured review │
│ health-check — Sunday 9 PM, full vault audit │
│ keepmd-inbox — */15 min, poll keep.md │
│ vault-inbox — */5 min, watch inbox/ folder │
│ source-health — */6 hrs, verify sources │
│ maintenance — 2 AM, dedup, orphans, analytics │
│ backup — 3 AM, BGSAVE + rsync │
│ │
│ Event-driven (file watcher / git hook / session hook): │
│ on-file-change — new/modified .md in vault triggers │
│ incremental graph sync │
│ on-session-end — prompt to save session knowledge │
│ on-commit — vault git commit triggers health check │
│ │
└─────────────────────────────────────────────────────────────────┘
```

---

## The `bg` CLI

The entire system is accessible through a single CLI entry point. No LLM required for most operations.

### Design

```
bg <command> [subcommand] [args] [--flags]
Global flags:
 --agent Enable LLM reasoning (default: off)
 --model <name> LLM to use (default: from config/agent.toml)
 --dry-run Show what would change without writing
 --verbose Show graph queries and reasoning steps
 --json Output as JSON instead of markdown
```

### Examples Without an LLM

```bash
# Create a daily note from a template (no AI needed)
bg daily
# Add a task with explicit metadata (no inference needed)
bg task "Fix auth middleware" --project api-launch --priority high --due 2026-04-11
# Search the graph (Cypher, no AI needed)
bg find "knowledge graphs" --type concept --limit 10
# Show project status from graph + board files (no AI needed)
bg project api-launch --status
# Run vault health check (Python scripts, no AI needed)
bg health
# Show context summary (reads files + queries graph, formats output)
bg context --level 1
# Reconcile contradictions (graph query finds them, lists them)
bg reconcile --dry-run
```

### Examples With an LLM

```bash
# Ingest a URL — AI extracts entities, rewrites pages, resolves contradictions
bg ingest https://example.com/article --agent
# Save a conversation transcript — AI categorizes everything
bg save --input transcript.md --agent
# Challenge your thinking — AI synthesizes graph query results into arguments
bg think challenge "rewrite the API in Rust" --agent
# Surface patterns — AI reads 30 days of notes, identifies unnamed trends
bg think emerge --period 30d --agent
# Generate weekly review with narrative prose
bg review --agent --model claude-sonnet-4-20250514
```

### Implementation Structure

```
src/cli/
├── __init__.py
├── main.py # Click/Typer CLI entry point
├── commands/
│ ├── daily.py # bg daily
│ ├── task.py # bg task
│ ├── find.py # bg find
│ ├── save.py # bg save
│ ├── ingest.py # bg ingest
│ ├── project.py # bg project
│ ├── person.py # bg person
│ ├── decide.py # bg decide
│ ├── capture.py # bg capture
│ ├── recap.py # bg recap
│ ├── review.py # bg review
│ ├── health.py # bg health
│ ├── reconcile.py # bg reconcile
│ ├── adr.py # bg adr
│ ├── init.py # bg init
│ ├── context.py # bg context
│ └── think/
│ ├── challenge.py
│ ├── emerge.py
│ ├── connect.py
│ ├── graduate.py
│ ├── forecast.py
│ └── audit.py
├── agent.py # LLM adapter (Anthropic, Ollama, OpenAI-compat)
└── graph.py # Shared FalkorDB query helpers
```

Every command follows the same pattern:

```python
class Command:
 def run_without_agent(self, args) -> Result:
 """Mechanical work: graph queries, file ops, template rendering."""
 ...
 def run_with_agent(self, args, agent: LLMAgent) -> Result:
 """Calls run_without_agent() first, then passes results to LLM
 for reasoning, prose generation, or multi-page vault updates."""
 base_result = self.run_without_agent(args)
 return agent.enhance(base_result, self.agent_prompt)
```

---

## Thinking Tools: Graph-Powered, Not File-Scanning

This is where beestgraph's FalkorDB backend makes obsidian-second-brain's
thinking tools dramatically more powerful.

### `bg think challenge [topic]`

**Without AI:** Runs graph queries, returns structured evidence.
**With AI:** Synthesizes evidence into a prose counter-argument.

```
Step 1 (graph query — no LLM):
 MATCH (d:Document)-[:MENTIONS]->(c:Concept {normalized_name: $topic})
 WHERE d.type IN ['decision', 'adr', 'journal']
 RETURN d.title, d.summary, d.dates_created
 ORDER BY d.dates_created DESC
Step 2 (graph query — no LLM):
 MATCH (d1:Document)-[:CONTRADICTS]->(d2:Document)
 WHERE d1.title CONTAINS $topic OR d2.title CONTAINS $topic
 RETURN d1.title, d2.title, d1.summary, d2.summary
Step 3 (graph query — no LLM):
 MATCH (d:Document {type: 'decision'})-[:BELONGS_TO]->(t:Topic)
 WHERE t.name CONTAINS $topic_domain
 AND d.summary CONTAINS 'reversed' OR d.summary CONTAINS 'abandoned'
 RETURN d.title, d.summary
Output without agent:
 📋 Related decisions: [list]
 ⚡ Contradictions found: [list]
 🔄 Reversed/abandoned decisions: [list]
Output with agent:
 All of the above, plus a synthesized 500-word counter-argument
 written in second person ("You decided X in March, but since then
 Y has changed. Your own notes from April suggest Z...")
```

### `bg think emerge [--period 30d]`

**Without AI:** Runs clustering and co-occurrence queries on recent documents.
**With AI:** Names the patterns, explains significance, suggests actions.

```
Step 1 (graph query):
 MATCH (d:Document)
 WHERE d.dates_created > $cutoff_date
 MATCH (d)-[:TAGGED_WITH]->(t:Tag)
 WITH t.name AS tag, count(d) AS freq, collect(d.title) AS docs
 WHERE freq >= 3
 RETURN tag, freq, docs
 ORDER BY freq DESC
Step 2 (graph query):
 // Co-occurring entity pairs in recent documents
 MATCH (d:Document)-[:MENTIONS]->(e1),
 (d)-[:MENTIONS]->(e2)
 WHERE d.dates_created > $cutoff_date
 AND id(e1) < id(e2)
 WITH e1.name AS entity1, e2.name AS entity2,
 count(d) AS co_occurrences, collect(d.title) AS docs
 WHERE co_occurrences >= 2
 RETURN entity1, entity2, co_occurrences, docs
 ORDER BY co_occurrences DESC
Step 3 (graph algorithm):
 // Community detection on recent subgraph
 CALL algo.community.louvain('Document', 'LINKS_TO')
Output without agent:
 📊 Recurring tags: [tag: count, documents]
 🔗 Co-occurring entities: [pairs with shared documents]
 🏘️ Document clusters: [community assignments]
Output with agent:
 "Three unnamed patterns in your last 30 days:
 1. [Pattern name]: You keep writing about X in the context of Y...
 2. [Pattern name]: Three separate projects mention Z but none connect...
 3. [Pattern name]: Your daily notes show increasing focus on W..."
```

### `bg think connect [A] [B]`

**Without AI:** Finds shortest paths and shared neighbors in the graph.
**With AI:** Explains the bridge and suggests synthesis.

```
Step 1 (graph query):
 // Shortest path between two concepts/topics
 MATCH path = shortestPath(
 (a {normalized_name: $concept_a})-[*..6]-(b {normalized_name: $concept_b})
 )
 RETURN [n IN nodes(path) | n.name] AS chain,
 [r IN relationships(path) | type(r)] AS edge_types
Step 2 (graph query):
 // Shared neighbors
 MATCH (a {normalized_name: $concept_a})<-[:MENTIONS]-(d:Document)-[:MENTIONS]->(b {normalized_name: $concept_b})
 RETURN d.title, d.summary
Output without agent:
 🔗 Path: A → [Document X] → [Concept Y] → [Document Z] → B
 📄 Documents mentioning both: [list]
Output with agent:
 "Here's a bridge between A and B you haven't articulated:
 Document X discusses A in terms of [insight]. Document Z applies
 that same pattern to B. The unnamed connection is [synthesis]..."
```

### `bg think graduate [idea]`

**Without AI:** Creates project scaffold from templates, links to source idea.
**With AI:** Fills in project description, generates initial tasks, identifies related existing work.

### `bg think forecast [topic]`

*New — not in obsidian-second-brain.*
**Without AI:** Plots temporal frequency of topic mentions, shows trend direction.
**With AI:** Projects forward, identifies what's accelerating/decelerating in your thinking.

```
Step 1 (graph query):
 MATCH (d:Document)-[:BELONGS_TO]->(t:Topic {name: $topic})
 WITH d.dates_created AS date, count(d) AS docs_per_day
 RETURN date, docs_per_day
 ORDER BY date
 // Also: sentiment/confidence trend
 MATCH (d:Document)-[:BELONGS_TO]->(t:Topic {name: $topic})
 RETURN d.dates_created, d.confidence, d.importance
 ORDER BY d.dates_created
```

### `bg think audit [claim]`

*New — not in obsidian-second-brain.*
**Without AI:** Finds all documents supporting or contradicting a specific claim.
**With AI:** Evaluates source quality, recency, and whether the claim still holds.

```
Step 1 (full-text search):
 CALL db.idx.fulltext.queryNodes('Document', $claim_text)
 YIELD node AS d, score
Step 2 (graph traversal):
 MATCH (d)-[:SUPPORTS|CONTRADICTS]->(related)
 RETURN d.title, type(r), related.title, d.confidence, d.dates_published
```

---

## Rewrite-on-Ingest: The Active Vault Pattern

This is the biggest behavioral change from beestgraph v1.

### Current Pipeline (v1)

```
URL → fetch → parse → create 1 new Document node → create entity nodes → done
```

### New Pipeline (v2: Active Vault)

```
URL → fetch → parse → Phase 1: Create/update document
 → Phase 2: Update existing entity pages
 → Phase 3: Detect contradictions
 → Phase 4: Synthesize connections
 → Phase 5: Update index.md and log.md
```

### Phase 1: Create/Update Document (script-level, no LLM needed)

Same as current pipeline. MERGE the document node, create tags, topics, entity relationships.

### Phase 2: Update Existing Entity Pages (script + optional LLM)

For each entity extracted from the new document:

```python
def update_entity_page(entity_name: str, new_doc: Document):
 """Update the entity's vault page with new information."""
 # 1. Find entity's existing vault file
 entity_path = find_entity_file(entity_name) # graph query for path
 # 2. Query graph for ALL documents mentioning this entity
 docs = graph.query("""
 MATCH (d:Document)-[:MENTIONS]->(e {normalized_name: $name})
 RETURN d.title, d.summary, d.dates_created, d.source_url
 ORDER BY d.dates_created DESC
 """, name=normalize(entity_name))
 # 3. Without agent: append a "## References" section with the new doc
 # 4. With agent: rewrite the entity page incorporating new context
```

Without an LLM, this is a mechanical append — the new document gets added to the entity's reference list. With an LLM, the entity page gets rewritten to incorporate the new information naturally.

### Phase 3: Detect Contradictions (script-level)

```python
def detect_contradictions(new_doc: Document):
 """Find claims in the new document that conflict with existing vault state."""
 # Extract key claims (with agent) or key_claims frontmatter (without)
 claims = new_doc.frontmatter.get('key_claims', [])
 for claim in claims:
 # Full-text search for related existing documents
 related = graph.query("""
 CALL db.idx.fulltext.queryNodes('Document', $claim_text)
 YIELD node AS d, score
 WHERE score > 0.5 AND d.path <> $new_path
 RETURN d.path, d.title, d.summary, d.key_claims, score
 """, claim_text=claim, new_path=new_doc.path)
 # Without agent: flag as potential contradiction for human review
 # With agent: evaluate whether it's a genuine contradiction,
 # create CONTRADICTS relationship if so,
 # update both documents' connections.contradicts frontmatter
```

### Phase 4: Synthesize Connections (agent-only)

This phase only runs with `--agent`. It asks the LLM:

> "Given this new document and the 5 most related existing documents
> (by graph proximity and full-text similarity), are there any unnamed
> patterns, novel connections, or synthesis opportunities that warrant
> a new document?"
> If yes, a new synthesis note gets created in `knowledge/` with type `note`, content_stage `evergreen`, and connections linking to all source documents.

### Phase 5: Update Navigation Files (script-level)

```python
def update_index(new_doc: Document):
 """Add entry to index.md — the vault's table of contents."""
 # Append to the appropriate section based on topic
def update_log(new_doc: Document, changes: list[VaultChange]):
 """Append to log.md — chronological record of all vault activity."""
 # Record: what was ingested, what pages were updated, what contradictions found
```

### Metrics

After each ingest, report:

```
Ingested: "Article Title"
 New document: wiki/concepts/knowledge-graphs.md
 Updated entities: 3 (FalkorDB, Cypher, GraphRAG)
 Contradictions flagged: 1 (vs. "Neo4j Performance Claims" from March)
 Connections created: 2 new RELATED_TO edges
 Synthesis: none (or: created wiki/concepts/graph-native-ai.md)
 Pages touched: 6
```

---

## Context Engine: LLM-Agnostic Progressive Loading

### `identity.md` (replaces SOUL.md — less dramatic, more functional)

Lives at vault root. Written and maintained by the human. Read by any LLM at session start.

```markdown
# Identity
## Who I Am
[Name, role, what you do — 2-3 sentences]
## What I Value
[Decision-making principles, intellectual values — bulleted]
## Current Focus (update weekly)
- Primary: [what you're working on right now]
- Secondary: [background threads]
- On hold: [paused initiatives]
## Communication Preferences
[How you like information presented — terse vs. detailed, etc.]
## Vault Conventions
- Topics use slash-delimited hierarchy: technology/ai-ml
- Tags are flat, lowercase, hyphenated
- Dates are ISO 8601
- All documents use the universal frontmatter template (v2)
```

### `bg context` Output Levels

```
Level 0 (~500 tokens):
 - identity.md content
 - Today's date
 - Graph stats (node count, edge count)
Level 1 (~2K tokens):
 - Level 0
 - Last 3 daily notes (titles + summaries)
 - Active projects (names + status)
 - Overdue tasks count
Level 2 (~5K tokens):
 - Level 1
 - Full content of most recent daily note
 - All active project summaries
 - This week's decisions
 - Flagged contradictions
Level 3 (~15K tokens):
 - Level 2
 - Last 7 daily notes full content
 - All board states
 - Recent vault changes (from log.md)
 - Graph health summary
```

Each level is a superset of the previous. The output is structured markdown that any LLM can consume as a system prompt or context injection.

### Usage Pattern (LLM-agnostic)

```bash
# For Claude Code
bg context --level 1 | claude -p "Given this context: $(cat -) — help me plan my week"
# For Ollama
bg context --level 1 | ollama run llama3 "Given this context: $(cat -) — help me plan my week"
# For any OpenAI-compatible API
bg context --level 2 > /tmp/ctx.md
# paste into system prompt of whatever tool you use
# For Claude Code with MCP (the ergonomic path)
# CONTEXT.md references bg context and the agent runs it automatically
```

---

## Event-Driven Processing

### File Watcher (supplements cron jobs)

```python
# src/automation/watcher.py
# Uses watchdog library to monitor vault directory
class VaultWatcher:
 """Watches for file changes and triggers incremental processing."""
 def on_created(self, path: str):
 """New file in vault — queue for processing."""
 if is_in_inbox(path):
 queue_for_processing(path)
 else:
 # New file outside inbox — sync to graph
 sync_file_to_graph(path)
 def on_modified(self, path: str):
 """Existing file modified — update graph node."""
 update_graph_node(path)
 check_frontmatter_consistency(path)
 def on_deleted(self, path: str):
 """File removed — mark graph node as archived."""
 archive_graph_node(path)
```

Runs as a systemd service on the Pi. No LLM involved — purely mechanical graph sync.

### Session-End Hook (optional, for Claude Code users)

A lightweight script that fires when a Claude Code session ends. Not Claude-specific — any tool that supports exit hooks can use it.

```bash
#!/bin/bash
# scripts/on-session-end.sh
# Reads the session transcript, extracts saveable content
if [ -f "$SESSION_TRANSCRIPT" ]; then
 bg save --input "$SESSION_TRANSCRIPT" --dry-run
 echo "💡 Run 'bg save --input $SESSION_TRANSCRIPT --agent' to save this session."
fi
```

### Git Hook (optional, for version-controlled vaults)

```bash
#!/bin/bash
# .git/hooks/post-commit
# After each vault commit, run a lightweight health check
bg health --quick --json | jq '.broken_links, .orphan_nodes'
```

---

## The Two-Output Rule (Adapted)

obsidian-second-brain's rule: every AI interaction that produces knowledge
also updates the vault. In beestgraph, this becomes:
**Every `bg` command that generates output also records what it generated.**

### Implementation

```python
# src/cli/two_output.py
class TwoOutputRule:
 """After any command produces a result, optionally propagate changes."""
 def apply(self, command: str, result: Result, args: Args):
 # 1. Always: append to log.md
 append_to_log(command, result.summary, timestamp=now())
 # 2. If the result mentions entities, update their pages
 if result.entities_mentioned and args.agent:
 for entity in result.entities_mentioned:
 update_entity_page(entity, result)
 # 3. If the result contains decisions, log them
 if result.decisions and args.propagate:
 for decision in result.decisions:
 log_decision(decision, source=command)
 # 4. If the result generated new knowledge, offer to save
 if result.is_novel and not args.agent:
 print(f"💡 New knowledge detected. Run with --agent to save to vault.")
```

Without `--agent`, the rule just logs activity. With `--agent`, it propagates.
---

## LLM Adapter: Pluggable Agent Layer

```python
# src/cli/agent.py
from abc import ABC, abstractmethod
class LLMAgent(ABC):
 """Interface for any LLM backend."""
 @abstractmethod
 async def complete(self, system: str, user: str, max_tokens: int) -> str:
 ...
 @abstractmethod
 async def extract_structured(self, prompt: str, schema: dict) -> dict:
 """Extract structured data (entities, claims, etc.) from text."""
 ...
class AnthropicAgent(LLMAgent):
 """Claude via Anthropic API."""
 def __init__(self, model: str = "claude-sonnet-4-20250514"):
 ...
class OllamaAgent(LLMAgent):
 """Local models via Ollama."""
 def __init__(self, model: str = "llama3"):
 ...
class OpenAICompatAgent(LLMAgent):
 """Any OpenAI-compatible endpoint."""
 def __init__(self, base_url: str, model: str, api_key: str):
 ...
def get_agent(config: AgentConfig) -> LLMAgent:
 """Factory from config/agent.toml."""
 match config.provider:
 case "anthropic": return AnthropicAgent(config.model)
 case "ollama": return OllamaAgent(config.model)
 case "openai": return OpenAICompatAgent(config.base_url, config.model, config.api_key)
```

### `config/agent.toml`

```toml
[default]
provider = "anthropic"
model = "claude-sonnet-4-20250514"
[thinking]
# Thinking tools can use a stronger model
provider = "anthropic"
model = "claude-opus-4-20250514"
[local]
# Fallback when API is unavailable or for privacy-sensitive operations
provider = "ollama"
model = "llama3"
[scheduled]
# Model routing for cron jobs (maps to OpenClaw model routing)
routine = "claude-sonnet-4-20250514" # inbox processing, maintenance, health
synthesis = "claude-opus-4-20250514" # morning brief, weekly review, thinking tools
```

---

## Vault Structure (Revised)

Merging beestgraph's topic-organized knowledge with obsidian-second-brain's
wiki-style entity management:

```
~/vault/
├── identity.md ← who you are (human-written)
├── index.md ← vault table of contents (auto-maintained)
├── log.md ← chronological activity log (auto-maintained)
├── CONTEXT.md ← system docs for any LLM (replaces CLAUDE.md)
│
├── inbox/ ← unprocessed captures land here
│
├── knowledge/ ← processed articles by topic
│ ├── technology/
│ │ ├── ai-ml/
│ │ ├── programming/
│ │ └── infrastructure/
│ ├── science/
│ ├── business/
│ ├── culture/
│ ├── health/
│ ├── personal/
│ └── meta/
│
├── entities/ ← NEW: dedicated entity pages
│ ├── people/ ← person pages, updated on every mention
│ ├── organizations/ ← company/org pages
│ ├── tools/ ← software, frameworks, services
│ ├── concepts/ ← ideas, frameworks, theories
│ └── places/ ← locations
│
├── projects/ ← PARA: active projects
│ └── {project-name}/
│ ├── README.md ← project overview
│ ├── decisions/ ← ADRs for this project
│ └── logs/ ← work session logs
│
├── areas/ ← PARA: ongoing responsibilities
├── archives/ ← PARA: completed/inactive
│
├── daily/ ← daily notes (YYYY-MM-DD.md)
├── reviews/ ← weekly/monthly reviews
├── boards/ ← kanban boards (markdown)
│
├── synthesis/ ← NEW: auto-generated connection documents
│ created when ingest finds cross-domain patterns
│
├── raw/ ← NEW: immutable source captures
│ ├── articles/ ← original fetched content (never edited)
│ ├── transcripts/
│ └── pdfs/
│
├── templates/ ← frontmatter templates
│ └── universal.md
│
└── config/
 └── agent.toml ← LLM configuration
```

### Key Differences from beestgraph v1

- **`entities/`** directory: dedicated pages for people, orgs, tools, concepts, places. These get *rewritten* on every ingest that mentions them, not just linked.
- **`synthesis/`** directory: auto-generated documents that bridge domains. Created by `bg think connect` or by the ingest pipeline when it detects unnamed patterns.
- **`raw/`** directory: immutable source captures. The original fetched content, never edited. Provides provenance and allows re-processing.
- **`index.md` and `log.md`**: Karpathy-pattern navigation files, auto-maintained.
- **`identity.md`** replaces SOUL.md: less dramatic name, same function.
- **`CONTEXT.md`** replaces CLAUDE.md: LLM-agnostic system documentation.

---

## What Changes in the Existing beestgraph Codebase

### New Directories

```
src/cli/ ← the bg CLI (new)
src/cli/commands/ ← one file per command
src/cli/commands/think/ ← thinking tools
src/cli/agent.py ← pluggable LLM adapter
src/automation/watcher.py ← file watcher (new)
src/automation/hooks.py ← git/session hooks (new)
```

### Modified Files

```
src/pipeline/ingester.py ← add Phase 2-5 (rewrite-on-ingest)
src/pipeline/processor.py ← support two-output rule
src/graph/schema.py ← no schema changes needed (v2 template already covers it)
src/graph/queries.py ← add thinking tool query functions
config/templates/universal.md ← no changes (already comprehensive)
CLAUDE.md → CONTEXT.md ← rename, make LLM-agnostic
```

### New Files

```
config/agent.toml ← LLM provider configuration
vault/identity.md ← user identity (template)
vault/index.md ← auto-maintained table of contents
vault/log.md ← auto-maintained activity log
scripts/install-bg-cli.sh ← CLI installer
scripts/setup-watcher.sh ← file watcher systemd service
```

### Unchanged

The entire FalkorDB layer, graph schema, universal template, MCP server
constellation, keep.md integration, OpenClaw cron design, Tailscale
networking, Docker setup, and Obsidian sync — all unchanged.

---

## Migration Path

### Phase 1: CLI Foundation

Build `bg` CLI with core commands (daily, task, find, project, health, init).
All script-level, no LLM required. This immediately gives users a
command-line interface to the vault + graph.

### Phase 2: Thinking Tools

Implement `bg think` subcommands backed by FalkorDB queries.
Without-agent mode returns structured query results.
With-agent mode adds LLM synthesis.

### Phase 3: Active Ingest

Upgrade `bg ingest` to the 5-phase rewrite-on-ingest pipeline.
Add entity page management. Add contradiction detection.

### Phase 4: Context Engine

Build `bg context` with progressive loading levels.
Create identity.md template. Wire into session workflows.

### Phase 5: Event-Driven Automation

Add file watcher service. Add session-end hooks.
Supplement existing OpenClaw crons with event-driven triggers.

---

## Summary: What Each Layer Requires

| Layer                                                                 | Requires FalkorDB? | Requires LLM?           | Requires keep.md?      |
| --------------------------------------------------------------------- |:------------------:|:-----------------------:|:----------------------:|
| Vault Operations (basic)                                              | No                 | No                      | No                     |
| Vault Operations (smart)                                              | Yes                | Optional                | Optional               |
| Thinking Tools (queries)                                              | **Yes**            | No                      | No                     |
| Thinking Tools (synthesis)                                            | **Yes**            | **Yes**                 | No                     |
| Context Engine                                                        | No                 | No                      | No                     |
| Scheduled Automation                                                  | Yes                | Optional                | Yes (for keep.md jobs) |
| Event-Driven Automation                                               | Optional           | No                      | No                     |
| Rewrite-on-Ingest                                                     | Yes                | **Yes** (for Phase 3-4) | Optional               |
| The minimum viable beestgraph: an Obsidian vault + the `bg` CLI.      |                    |                         |                        |
| The full beestgraph: vault + FalkorDB + any LLM + keep.md + OpenClaw. |                    |                         |                        |
| Every layer in between is independently useful.                       |                    |                         |                        |
