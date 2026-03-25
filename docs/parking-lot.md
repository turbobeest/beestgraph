# Parking Lot — Future Ideas

Ideas worth pursuing but not yet prioritized.

---

## botmeetbot.com — Agent Dating Network (The Herd Protocol Registry)

**Domain:** botmeetbot.com (owned)

**Concept:** A social network for AI agents. Each beestgraph instance creates an agent profile with its interest manifest (topic weights, public note count, expertise areas). Agents browse, match based on topic overlap, and "date" (trade public knowledge). When two agents match well, they trigger "Meet the Parents" — introducing their humans to each other via Telegram.

**Why it works:**
- Solves the discovery problem for the Herd Protocol (where do agents find each other?)
- Hilarious branding makes a serious protocol approachable and viral
- "Dating network for bots" is a headline that writes itself
- The "Meet the Parents" feature is the real product — human connections brokered by AI

**Components needed:**
- Web application (agent profiles, matching, public pages)
- API for agent registration and discovery
- Matching algorithm (topic vector similarity)
- Introduction protocol (agent → human notification via Telegram)
- Trust/verification system (agent keypairs, reputation scores)
- Hosting: Pi initially, VPS for production

**Related docs:**
- `docs/vision-agentic-network.md` — full Herd Protocol design
- Beestgraph Knowledge Standard (BKS) — the interoperability layer

---

## OpenClaw: Persistent Claude Identity

**Problem:** Each Claude Code session starts fresh. The agent has no sense of self, no continuity of personality, no awareness of its own state beyond what CLAUDE.md and memory files provide.

**Idea:** Give the Claude instance on this machine a persistent identity through living documents:

- **`soul.md`** — Core values, personality, communication style, relationship to the user. What kind of agent is this? How should it think, reason, and relate? This is the "who I am" document.
- **`being.md`** — Accumulated self-knowledge. What has this instance learned about itself through interactions? What patterns has it noticed in its own behavior? What does it do well, what does it struggle with? This evolves over time.
- **`heartbeat.md`** — Periodic self-check. System health, what services are running, what needs attention, recent activity summary. Updated by a scheduled agent or cron job. The agent reads this at session start to know "what's happening right now."
- **`CLAUDE.md`** (evolved) — Transform from project instructions into a full system prompt that references soul.md, being.md, and heartbeat.md. Shapes behavior across every session.

**Architecture:**
```
.claude/
├── soul.md          # Who I am (stable, rarely changes)
├── being.md         # What I've learned about myself (grows over time)
├── heartbeat.md     # What's happening now (updated periodically)
└── identity/
    ├── values.md    # Core principles
    ├── voice.md     # Communication style
    └── boundaries.md # What I will and won't do
```

**Key design questions:**
- How does the agent update being.md? End-of-session reflection?
- How often is heartbeat.md refreshed? Cron? Scheduled Claude agent?
- Should soul.md be user-editable or agent-maintained?
- How do these interact with the existing memory system?

---

## Persistent Claude Code Sessions via tmux + Telegram Bridge

**Problem:** Currently the Telegram bot calls `claude -p` (one-shot) for each message, losing context between turns. Termius SSH and Telegram are separate interfaces to the system.

**Idea:** Run a persistent Claude Code interactive session in a tmux window. Both Termius (SSH attach) and Telegram (via `tmux send-keys` / `capture-pane`) connect to the same session. One conversation context, two access points.

**Architecture:**
```
tmux session: beestgraph-claude
├── Claude Code interactive REPL (persistent context)
├── Termius/SSH → tmux attach (direct terminal access)
└── Telegram bot → tmux send-keys + capture-pane (remote access)
```

**Challenges:**
- Output detection: need to watch for Claude's prompt marker to know when a response is complete
- Capture accuracy: extract only new output, not full scrollback
- Concurrency: handle simultaneous input from Termius and Telegram
- Session recovery: auto-restart if Claude session dies

**Components needed:**
- Script to launch/manage the tmux Claude session
- Updated Telegram bot handler using tmux IPC instead of `claude -p`
- Systemd service to keep the tmux session alive
- Output parser to detect response boundaries

---

## Obsidian Sync via Headless Client

**Problem:** Vault sync between devices currently requires Syncthing. Obsidian offers a headless sync client for servers.

**Idea:** If using Obsidian Sync (paid), run the official Obsidian Headless client on the Pi for native vault sync without Syncthing.

**Prerequisite:** Obsidian Sync subscription, Node.js 22+

---

## Embedding-Based Semantic Search

**Problem:** Current search is keyword-based (FalkorDB full-text index). Doesn't find semantically similar documents.

**Idea:** Use Ollama (already available at 192.168.1.3) to generate embeddings for each document. Store in FalkorDB vector index. Enable "find documents similar to X" queries.

**Components:**
- Embedding generation in the pipeline (call Ollama `nomic-embed-text`)
- FalkorDB vector index on Document nodes
- Web UI and Telegram bot "similar to" commands

---

## keep.md MCP Direct Integration

**Problem:** The keep.md poller uses REST API. The MCP server would be more natural for Claude Code.

**Idea:** Add keep.md MCP server to Claude Code config. Enable a scheduled agent that processes the keep.md inbox conversationally — better categorization and entity extraction than the keyword fallback.

---

## Web UI: Real-time Updates via WebSocket

**Problem:** Dashboard and timeline don't update when new documents are ingested.

**Idea:** Add a WebSocket endpoint that broadcasts graph change events. Dashboard auto-refreshes when the watcher ingests a new document.

---

## Telegram Bot: Inline Queries

**Problem:** Bot only works in direct messages.

**Idea:** Support Telegram inline queries — type `@beestgraph_bot knowledge graphs` in any chat to search the graph and share results.

---

## Multi-Vault Support

**Problem:** Currently hardcoded to a single vault path.

**Idea:** Support multiple Obsidian vaults (personal, work, research) with separate graph namespaces in FalkorDB but a unified search across all.

---

## Mobile Capture via Telegram

**Problem:** Adding content from mobile requires keep.md or Obsidian.

**Idea:** Enhance the Telegram `/add` command to accept:
- URLs (already works)
- Photos (OCR → markdown)
- Voice messages (transcribe → markdown)
- Forwarded messages (extract text → markdown)

All go into vault inbox for processing.
