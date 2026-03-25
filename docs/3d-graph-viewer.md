# 3D Knowledge Graph Viewer — Design Document

> Three organizational lenses on one knowledge graph, with inline markdown editing.

**Status:** DESIGN — requires review before implementation.

---

## Concept

A 3D interactive graph viewer where users can switch between three organizational views of their knowledge, each revealing different structures and insights:

1. **PARA View** — nodes grouped by actionability (projects, areas, resources, archive)
2. **Zettelkasten View** — nodes layered by maturity (inbox → fleeting → permanent) with link paths
3. **Topic Tree View** — nodes clustered by subject hierarchy with MOC hubs

Clicking any node opens its markdown content in a sidebar with live editing.

---

## Architecture

### Tech stack

| Component | Technology | Why |
|-----------|-----------|-----|
| 3D rendering | Three.js + 3d-force-graph | GPU-accelerated, handles 10K+ nodes |
| Framework | Next.js (existing web UI) | Already running, shared API routes |
| Graph data | FalkorDB via API routes | Already built |
| Markdown rendering | Marked.js or unified | Render markdown in sidebar |
| Markdown editing | CodeMirror 6 or Monaco | In-browser editor with frontmatter support |

`3d-force-graph` is a Three.js wrapper specifically for force-directed 3D graphs. It handles node/edge rendering, camera controls, and physics simulation out of the box.

### Page location

`src/web/src/app/graph3d/page.tsx` — new route in the existing Next.js app at `:3001/graph3d`

---

## Three Views

### View 1: PARA (Actionability)

**What you see:** Nodes are spatially grouped into four quadrants or clusters:
- **Projects** (top-left) — active, time-bound work. Bright amber.
- **Areas** (top-right) — ongoing responsibilities. Steady green.
- **Resources** (bottom-center) — reference knowledge. Cool blue. Largest cluster.
- **Archive** (faded, pulled back) — inactive. Dim gray, lower opacity.

**Edges shown:**
- `IN_PROJECT` — document → project node
- `IN_AREA` — document → area node
- `LINKS_TO` — document → document (wiki-links)

**Node appearance:**
- Size: proportional to connection count
- Color: by PARA category
- Shape: projects = cube, areas = sphere, resources = octahedron, archive = small dot

**Interaction:**
- Click a project node → shows all connected documents in the sidebar
- Drag to rearrange clusters
- Filter: show only one PARA category

**Insight this reveals:** "What am I actively working on? What's getting neglected? Where's my knowledge concentrated vs sparse?"

---

### View 2: Zettelkasten (Maturity + Connections)

**What you see:** Nodes are layered vertically by maturity:
- **Permanent notes** (top layer) — bright, large, heavily connected
- **Fleeting notes** (middle layer) — medium, some connections
- **Inbox/Raw** (bottom layer) — dim, small, unconnected

**Edges shown:**
- `GRADUATED_FROM` — fleeting → permanent (vertical upward arrows)
- `SPARKED_BY` — note → note (idea origin)
- `SUPERSEDES` — note → note (updated thinking)
- `LINKS_TO` — wiki-links (horizontal connections)
- `MENTIONS` — entity connections

**Node appearance:**
- Y-position: determined by maturity (inbox=bottom, fleeting=middle, permanent=top)
- Size: proportional to outgoing wiki-link count (heavily linked = larger)
- Color: gradient from dim blue (raw) → amber (fleeting) → bright gold (permanent)
- Opacity: permanent=100%, fleeting=70%, raw=40%

**Edge appearance:**
- `GRADUATED_FROM` arrows: bright green, vertical, thicker
- `LINKS_TO` edges: white, horizontal
- `SPARKED_BY` edges: amber dashed lines

**Interaction:**
- Click a permanent note → see its lineage (what fleeting notes it graduated from)
- Click a fleeting note → see "suggested graduations" (similar permanent notes it could merge with)
- Time slider: animate the graph growing over time (show captures arriving at the bottom, graduating upward)

**Insight this reveals:** "How is my thinking evolving? What ideas keep recurring as fleeting but never graduate? Where are the dense connection clusters?"

---

### View 3: Topic Tree (Navigation)

**What you see:** Nodes clustered in a hierarchical spatial layout:
- **Top-level topics** (technology, science, business, etc.) — large hub nodes at center
- **Subtopics** (ai-ml, programming, etc.) — medium nodes orbiting their parent
- **Documents** — small nodes orbiting their subtopic
- **MOCs** — distinctive large nodes that serve as curated entry points

**Edges shown:**
- `BELONGS_TO` — document → topic
- `SUBTOPIC_OF` — topic → parent topic
- `IN_MOC` — document → MOC
- `TAGGED_WITH` — document → tag (optional, togglable)

**Layout:** Hierarchical force-directed — topics attract their documents, subtopics orbit parents. Results in a galaxy-like structure where each topic cluster is visible.

**Node appearance:**
- Topics: large spheres, colored by topic category
- MOCs: large star/diamond shapes, same color as their topic but brighter
- Documents: small spheres, colored by their primary topic
- Tags: tiny dots, only visible when zoomed in

**Interaction:**
- Click a topic → zoom into that cluster, show all documents
- Click a MOC → show its curated list in the sidebar
- Right-click a document → "Add to MOC" context menu
- Search highlights matching nodes with glow effect

**Insight this reveals:** "What topics do I know the most about? Where are the cross-topic connections? Which MOCs need updating?"

---

## Sidebar: Markdown Viewer + Editor

When a node is clicked, a sidebar slides in from the right showing:

### Read mode (default)
```
┌─────────────────────────────────────┐
│ ← Back   Understanding Docker       │
│                                     │
│ 🔒 private | tutorial | technology  │
│ Maturity: fleeting                  │
│ Quality: high | 2026-03-24          │
│ ─────────────────────────────────── │
│                                     │
│ # Understanding Docker Networking   │
│                                     │
│ > Guide to Docker container         │
│ > networking modes.                 │
│                                     │
│ ## Content                          │
│                                     │
│ Docker provides several network     │
│ drivers for container communication.│
│ ...                                 │
│                                     │
│ ─────────────────────────────────── │
│ Connections:                        │
│   → [[Docker Setup Guide]]         │
│   → [[Raspberry Pi Homelab]]       │
│   ← mentioned by: [[PKM MOC]]     │
│                                     │
│ [Edit] [Approve] [Make Public]      │
└─────────────────────────────────────┘
```

### Edit mode
- CodeMirror 6 editor with YAML frontmatter syntax highlighting
- Save button writes to vault via API route
- Changes sync via Obsidian Sync to all devices
- Frontmatter fields are editable (type, topics, tags, visibility)
- Wiki-link autocomplete from existing note titles

### Connection panel
Shows all edges for the selected node, grouped by type:
- **Wiki-links** — outgoing `[[links]]` and incoming backlinks
- **Topics** — which topics this note belongs to
- **Entities** — people, concepts, organizations mentioned
- **PARA** — which project/area it's in
- **Maturity** — what it graduated from, what supersedes it

---

## FalkorDB Queries Per View

### PARA View query
```cypher
MATCH (d:Document)
WHERE d.status <> 'archived'
OPTIONAL MATCH (d)-[:IN_PROJECT]->(p:Project)
OPTIONAL MATCH (d)-[:IN_AREA]->(a:Area)
OPTIONAL MATCH (d)-[l:LINKS_TO]->(d2:Document)
RETURN d, p, a, l, d2
```

### Zettelkasten View query
```cypher
MATCH (d:Document)
OPTIONAL MATCH (d)-[g:GRADUATED_FROM]->(d2:Document)
OPTIONAL MATCH (d)-[s:SPARKED_BY]->(d3:Document)
OPTIONAL MATCH (d)-[l:LINKS_TO]->(d4:Document)
RETURN d, g, d2, s, d3, l, d4
```

### Topic Tree View query
```cypher
MATCH (t:Topic)
OPTIONAL MATCH (t)-[:SUBTOPIC_OF]->(parent:Topic)
OPTIONAL MATCH (d:Document)-[:BELONGS_TO]->(t)
OPTIONAL MATCH (m:MOC)-[:CHILD_OF]->(t)
OPTIONAL MATCH (d)-[:IN_MOC]->(m)
RETURN t, parent, d, m
```

---

## API Routes

```
GET /api/graph3d/para      → PARA view data (nodes + edges)
GET /api/graph3d/zettel    → Zettelkasten view data
GET /api/graph3d/topics    → Topic tree view data
GET /api/graph3d/node/:id  → Single node details + connections
PUT /api/graph3d/node/:id  → Update node (edit frontmatter/content)
```

---

## Performance Considerations

| Vault size | Nodes | Strategy |
|-----------|-------|----------|
| < 500 notes | < 1K nodes | Load everything, full physics |
| 500-5K notes | 1K-10K nodes | Load on demand, simplified physics |
| 5K+ notes | 10K+ nodes | LOD (level of detail), cluster aggregation |

For large vaults:
- Show topic/MOC clusters as single aggregate nodes at zoom-out
- Expand to individual documents on zoom-in
- Use WebGL instanced rendering for 10K+ nodes
- Paginate edge queries

---

## Implementation Phases

### Phase 1: Basic 3D viewer (single view)
- 3d-force-graph integration in Next.js
- One view (Topic Tree — most visually interesting)
- Node click → sidebar with markdown content
- Basic camera controls (orbit, zoom, pan)

### Phase 2: Three views + transitions
- Add PARA and Zettelkasten views
- Animated transitions between views (nodes fly to new positions)
- View switcher UI (tabs or buttons)
- Color legends per view

### Phase 3: Sidebar editor
- CodeMirror markdown editor
- Frontmatter editing
- Save to vault via API
- Wiki-link autocomplete

### Phase 4: Advanced interactions
- Time animation (watch the graph grow)
- Search with glow highlighting
- Right-click context menus (add to MOC, change topic, etc.)
- Connection panel per node
- Keyboard navigation

### Phase 5: Performance
- LOD rendering for large vaults
- Cluster aggregation
- WebGL instancing
- Progressive loading

---

## Open Questions

1. **VR/AR support?** Three.js supports WebXR. Could explore the graph in VR headset.
2. **Collaborative viewing?** Multiple users viewing the same graph (for Herd Protocol peer exploration).
3. **Export?** Screenshot, SVG export, or shareable link to a specific graph state.
4. **Mobile?** Touch controls for the 3D graph on phone (via Tailscale).
