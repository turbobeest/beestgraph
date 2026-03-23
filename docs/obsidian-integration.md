# Obsidian integration

Obsidian serves as beestgraph's deep capture tool and the primary human interface for reading and editing knowledge. All processed content lives in the vault as markdown files with YAML frontmatter.

## Table of contents

- [Vault structure](#vault-structure)
- [Syncthing setup](#syncthing-setup)
- [Obsidian Web Clipper](#obsidian-web-clipper)
- [Frontmatter template](#frontmatter-template)
- [Watchdog processing](#watchdog-processing)
- [Working with the vault](#working-with-the-vault)

---

## Vault structure

The vault follows a hybrid structure combining the PARA method (Projects, Areas, Resources, Archives) with topic-based organization for processed knowledge:

```
~/vault/
├── inbox/              <- watchdog monitors this directory
├── knowledge/          <- processed articles organized by topic
│   ├── technology/
│   │   ├── programming/
│   │   ├── ai-ml/
│   │   ├── infrastructure/
│   │   ├── security/
│   │   └── web/
│   ├── science/
│   │   ├── physics/
│   │   ├── biology/
│   │   └── mathematics/
│   ├── business/
│   │   ├── startups/
│   │   ├── finance/
│   │   └── marketing/
│   ├── culture/
│   │   ├── books/
│   │   ├── film/
│   │   ├── music/
│   │   └── history/
│   ├── health/
│   │   ├── fitness/
│   │   ├── nutrition/
│   │   └── mental-health/
│   ├── personal/
│   │   ├── journal/
│   │   ├── goals/
│   │   └── relationships/
│   └── meta/
│       ├── pkm/
│       ├── tools/
│       └── workflows/
├── projects/           <- PARA: active projects
├── areas/              <- PARA: ongoing responsibilities
├── resources/          <- PARA: reference material
├── archives/           <- PARA: completed/inactive
└── templates/          <- frontmatter templates
```

### Directory purposes

| Directory | Purpose | Managed by |
|-----------|---------|-----------|
| `inbox/` | Landing zone for new captures. Watchdog monitors this. | User + Web Clipper |
| `knowledge/` | Processed articles organized by taxonomy topics. | Processing pipeline |
| `projects/` | Active project notes and documents. | User |
| `areas/` | Ongoing responsibilities (health, finance, etc.). | User |
| `resources/` | Reference material not tied to a project. | Pipeline + User |
| `archives/` | Completed or inactive items. | User |
| `templates/` | Frontmatter templates for new documents. | Repository |

---

## Syncthing setup

[Syncthing](https://syncthing.net/) syncs the vault peer-to-peer across all your devices without a cloud service.

### On the Pi (server)

Syncthing should already be running if you followed the [setup guide](setup-guide.md). Verify:

```bash
sudo systemctl status syncthing@$USER
```

Access the Syncthing web UI:

```bash
# Locally
http://localhost:8384

# Via Tailscale
http://beestgraph:8384
```

### Adding a device

1. Open Syncthing on both the Pi and the device you want to sync.
2. On the Pi, go to Actions > Show ID. Copy the device ID.
3. On the other device, go to Add Remote Device and paste the ID.
4. Accept the pairing request on the Pi.

### Sharing the vault folder

1. On the Pi, click Add Folder.
2. Set the folder path to your vault (e.g., `/mnt/nvme/vault` or `~/vault`).
3. Give it a label (e.g., "beestgraph-vault").
4. Under Sharing, select the devices to sync with.
5. On the other devices, accept the folder share.

### Recommended settings

- **File versioning**: Enable "Staggered File Versioning" to keep old versions of files.
- **Ignore patterns**: Add `.obsidian/workspace.json` and `.obsidian/workspace-mobile.json` to `.stignore` to avoid sync conflicts from Obsidian workspace state.

Create a `.stignore` file in the vault root:

```
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache
.trash/
```

---

## Obsidian Web Clipper

The [Obsidian Web Clipper](https://obsidian.md/clipper) browser extension saves full articles directly to the vault's `inbox/` directory with custom frontmatter.

### Installation

1. Install the Obsidian Web Clipper extension for your browser.
2. Configure it to save to your vault's `inbox/` directory.

### Clipper template

Configure the Web Clipper to use this YAML frontmatter template, so captured articles match the beestgraph format:

```yaml
---
title: "{{title}}"
source_url: "{{url}}"
source_type: obsidian_clipper
author: "{{author}}"
date_published: {{published}}
date_captured: {{date}}T{{time}}Z
date_processed:
summary:
para_category:
topics: []
tags: []
entities:
  people: []
  concepts: []
  organizations: []
status: inbox
---
```

The processing pipeline fills in the empty fields (`date_processed`, `summary`, `para_category`, `topics`, `tags`, `entities`) when it processes the item.

### File naming

Configure the Web Clipper to save files as:

```
inbox/{{date}}-{{title|slugify}}.md
```

This ensures unique filenames and chronological ordering in the inbox.

---

## Frontmatter template

Every processed document in the vault gets this frontmatter:

```yaml
---
title: "Article Title"
source_url: "https://..."
source_type: keepmd | obsidian_clipper | manual
author: "Author Name"
date_published: 2026-01-15
date_captured: 2026-01-16T10:30:00Z
date_processed: 2026-01-16T10:45:00Z
summary: "Two to three sentence AI-generated summary."
para_category: resources
topics:
  - technology/ai-ml
tags:
  - knowledge-graphs
  - falkordb
entities:
  people:
    - "Name"
  concepts:
    - "Concept"
  organizations:
    - "Org"
status: published
---
```

### Field descriptions

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Article or note title |
| `source_url` | string | Original URL where content was captured |
| `source_type` | enum | `keepmd`, `obsidian_clipper`, or `manual` |
| `author` | string | Author name (if known) |
| `date_published` | date | When the original content was published |
| `date_captured` | datetime | When beestgraph captured the content (ISO 8601) |
| `date_processed` | datetime | When the pipeline processed the content |
| `summary` | string | AI-generated 2-3 sentence summary |
| `para_category` | enum | `projects`, `areas`, `resources`, or `archives` |
| `topics` | list | Topic paths from the taxonomy (e.g., `technology/ai-ml`) |
| `tags` | list | Flat tags for additional categorization |
| `entities.people` | list | People mentioned in the content |
| `entities.concepts` | list | Concepts and ideas extracted |
| `entities.organizations` | list | Organizations mentioned |
| `status` | enum | `inbox`, `processing`, `published`, or `archived` |

---

## Watchdog processing

The vault watchdog daemon monitors `~/vault/inbox/` for new or modified markdown files using Python's `watchdog` library (inotify on Linux).

### How it works

1. A new `.md` file appears in `inbox/` (from Obsidian Web Clipper, manual creation, or Syncthing).
2. The watchdog detects the file creation event.
3. It triggers the processing pipeline:
   - Reads the file via Filesystem MCP
   - Extracts entities, topics, and tags
   - Generates a summary
   - Moves the file to the correct `knowledge/` subdirectory based on topic
   - Updates the frontmatter with processing results
   - Ingests into the knowledge graph via Graphiti MCP
4. The file's `status` field changes from `inbox` to `published`.

### Starting the watchdog

```bash
make run-watcher
```

Or with a custom vault path:

```bash
VAULT_PATH=/mnt/nvme/vault make run-watcher
```

### Ignoring files

The watchdog ignores:

- Files outside `inbox/`
- Hidden files (starting with `.`)
- Non-markdown files
- Files with `status: published` or `status: archived` in their frontmatter

---

## Working with the vault

### Creating notes manually

Create a markdown file in `inbox/` with at minimum:

```yaml
---
title: "My Note"
source_type: manual
status: inbox
---

Your note content here.
```

The watchdog picks it up and processes it automatically.

### Browsing processed knowledge

Use Obsidian to browse the `knowledge/` directory tree. Each topic subdirectory contains processed articles. The frontmatter is searchable using Obsidian's built-in search or the Dataview plugin.

### Editing processed documents

You can edit any file in the vault. Changes are synced via Syncthing. If you want to re-process an edited document, change its `status` back to `inbox` and move it to the `inbox/` directory.
