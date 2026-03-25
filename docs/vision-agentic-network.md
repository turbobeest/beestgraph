# Vision: The Beestgraph Agentic Knowledge Network

> Personal knowledge graphs that discover each other, trade knowledge, and connect humans.

**Status:** VISION — long-term direction, not implementation-ready.

---

## The Idea

Every beestgraph instance is a **personal knowledge beast** — it captures, organizes, and connects one person's knowledge. But beasts don't live alone. They roam, they find each other, they communicate.

What if beestgraph instances could:
1. **Advertise** their owner's public interests on the open internet
2. **Discover** other beestgraph instances with overlapping interests
3. **Trade** public knowledge (markdown notes marked as shareable)
4. **Generate** viral/buzzworthy content from their knowledge base
5. **Introduce** their humans to each other when interests align

This turns beestgraph from a personal tool into a **decentralized, agentic social knowledge network** — no central platform, no algorithm you don't control, no data you don't own.

---

## The Public/Private Split

Every markdown note gets a new frontmatter field:

```yaml
visibility: private    # private | public | shared
```

| Visibility | Meaning |
|-----------|---------|
| `private` | Never leaves your vault. Default for everything. |
| `public` | Available for discovery, trading, and syndication by your agent. |
| `shared` | Shared with specific beestgraph instances (named peers). |

### Rules
- **Default is private.** Nothing is public unless explicitly marked.
- The qualification pipeline asks: "Make this public?" as part of the Telegram review.
- Public notes have their content available; private notes may expose only metadata (title, topics, tags) for interest-matching without revealing content.
- The `shared` level enables selective knowledge trading with trusted peers.

### Graph schema addition

```cypher
(:Document {
  visibility: STRING    -- private | public | shared
})

CREATE INDEX FOR (d:Document) ON (d.visibility)
```

---

## Architecture: How Agents Network

### Layer 1: Self-Advertisement

Each beestgraph instance runs an **ambassador agent** that:
- Maintains a public profile derived from public notes and topics
- Publishes an interest manifest (topic weights, active areas, expertise signals)
- Hosts a discovery endpoint (could be a simple JSON file, ActivityPub profile, or DNS TXT record)

```json
{
  "beestgraph": "1.0",
  "instance": "turbobeest",
  "interests": {
    "technology/ai-ml": 0.85,
    "technology/infrastructure": 0.72,
    "meta/pkm": 0.91,
    "technology/programming": 0.68
  },
  "public_notes_count": 42,
  "topics": ["knowledge-graphs", "raspberry-pi", "obsidian", "self-hosted"],
  "contact": {
    "protocol": "beestgraph-a2a",
    "endpoint": "https://turbobeest.beestgraph.net/.well-known/beestgraph"
  },
  "human": {
    "display_name": "turbobeest",
    "intro_channel": "telegram"
  }
}
```

### Layer 2: Discovery

How do beestgraph agents find each other?

**Option A: Registry (simple, centralized fallback)**
- A public registry where instances voluntarily list themselves
- Like a DNS for knowledge graphs
- Could be a simple GitHub repo with JSON files, or a lightweight web service

**Option B: ActivityPub / Fediverse (decentralized)**
- Each beestgraph instance is an ActivityPub actor
- Agents post public notes as ActivityPub objects
- Discovery via follow/boost/hashtag mechanics
- Interoperable with Mastodon, Lemmy, etc.

**Option C: DHT / P2P (fully decentralized)**
- Topic-based distributed hash table
- Agents announce their interest vectors
- Similar to how BitTorrent peers find each other
- No central point of failure

**Option D: A2A Protocol (Google's Agent-to-Agent)**
- Use the emerging A2A standard for agent communication
- Each beestgraph agent exposes an A2A endpoint
- Agents negotiate capabilities and exchange knowledge
- Built-in authentication and trust

**Recommendation:** Start with **Option A** (registry) for simplicity, design the agent protocol to be transport-agnostic so it can migrate to ActivityPub or A2A later.

### Layer 3: Knowledge Trading

When two beestgraph agents find overlapping interests:

1. **Interest matching** — compare topic vectors, find overlap score
2. **Handshake** — agents negotiate what they're willing to share
3. **Exchange** — trade public markdown notes, with full frontmatter and style guide compliance
4. **Integration** — received notes enter the inbox with `source_type: beestgraph-peer`
5. **Attribution** — all traded notes preserve original author and source instance

```
Agent A (turbobeest)              Agent B (researcher42)
├── interests: ai-ml (0.85)       ├── interests: ai-ml (0.90)
├── interests: pkm (0.91)         ├── interests: neuroscience (0.88)
│                                 │
├── "I have 12 public notes       ├── "I have 8 public notes
│    about knowledge graphs"      │    about neural networks"
│                                 │
└── TRADE ←─────────────────────→ └── TRADE
    "Here's my best 3 on KGs"         "Here's my best 3 on NNs"
```

### Layer 4: Buzz Generation

Each agent has a **curator persona** that:
- Analyzes its owner's public knowledge base
- Identifies what's unique, timely, or contrarian
- Generates "buzz notes" — synthesized insights from multiple sources
- Decides what to promote based on a configurable algorithm

**Buzz algorithm inputs:**
- Recency (newer = higher signal)
- Uniqueness (rare topic combinations = interesting)
- Connection density (highly linked notes = important)
- Engagement from peers (traded/requested notes = validated)
- Owner emphasis (quality: high, starred, or manually promoted)

**Buzz algorithm is configurable and transparent** — unlike social media algorithms, the owner sees and controls every parameter.

### Layer 5: Human Introduction

When two agents determine a strong interest overlap:

1. Agent A asks its human (via Telegram): "I found researcher42 — they're deep into neural networks and AI/ML, same as you. 87% interest overlap. Want me to introduce you?"
2. If yes, Agent A sends an introduction message to Agent B
3. Agent B asks its human the same question
4. If both agree, the agents exchange Telegram handles (or email, or any contact method)
5. A warm introduction message is sent to both humans

```
Agent A → Telegram: "I found someone interesting:
  researcher42 — AI/ML researcher, 87% overlap with your interests.
  Their top public notes: Neural Network Architectures,
  Transformer Attention Mechanisms, Graph Neural Networks.

  Want me to introduce you? (yes / no / tell me more)"
```

---

## The Beestgraph Knowledge Standard (BKS)

The organizational framework — PARA + Zettelkasten + Topic Tree — becomes a shared standard that enables interoperability:

### What BKS defines

1. **Frontmatter schema** — universal fields every beestgraph note has
2. **Content types** — the 25+ type taxonomy
3. **Topic tree** — hierarchical topic classification
4. **Maturity model** — raw → fleeting → permanent
5. **Style guide** — formatting, structure, readability rules
6. **Visibility model** — private / public / shared
7. **Agent protocol** — how instances discover, negotiate, and trade

### Why standardization matters

Without BKS, every knowledge graph is an island. With BKS:
- Agents can understand each other's topic trees
- Traded notes slot directly into the receiver's vault
- Interest matching works because topics are shared vocabulary
- Quality assessment is comparable (same readability criteria)
- The network effect compounds — more instances = more knowledge flow

### BKS is opt-in and forkable

- Core BKS is the minimum for interoperability (frontmatter, topics, visibility)
- Extended BKS includes the full style guide and content types
- Anyone can fork and customize while maintaining core compatibility

---

## Implementation Phases

### Phase 1: Foundation (now → near future)
- Add `visibility` field to frontmatter schema
- Add public/private to qualification Telegram flow
- Implement the style guide auto-formatter
- Build the vault schema (numbered folders, MOCs)

### Phase 2: Public Profile (medium-term)
- Agent generates interest manifest from public notes
- Host manifest at a discoverable endpoint
- `beestgraph profile` CLI command shows your public knowledge profile

### Phase 3: Discovery & Trading (future)
- Registry for beestgraph instances
- Agent-to-agent handshake protocol
- Knowledge trading (public note exchange)
- Received notes enter inbox with peer attribution

### Phase 4: Social Layer (long-term)
- Buzz generation algorithm
- Human introduction via Telegram
- Reputation/trust system between instances
- Collaborative MOCs (shared maps of content across instances)

### Phase 5: Federation (visionary)
- ActivityPub integration (beestgraph as fediverse citizen)
- A2A protocol support
- Cross-instance graph queries
- Collective intelligence emergence

---

## Open Questions

1. **Trust model** — how do agents verify each other? Cryptographic identity? Web of trust?
2. **Spam prevention** — how to prevent low-quality agents from flooding the network?
3. **Privacy guarantees** — how to ensure private notes never leak even through metadata patterns?
4. **Monetization** — could knowledge trading have an economic layer? Pay for premium knowledge?
5. **Governance** — who maintains the BKS standard? Community RFC process?
6. **Content licensing** — what license applies to traded public notes? CC-BY-SA default?

---

## Why This Matters

Social media failed because it optimized for engagement, not understanding. The beestgraph network optimizes for **knowledge** — finding people who know things you want to learn, and sharing things you know with people who need them.

No central algorithm. No attention harvesting. No data you don't own. Just beasts finding their herd.
