# keep.md integration

[keep.md](https://keep.md) is the primary broad-capture tool for beestgraph. It aggregates content from multiple sources into a single markdown-based inbox, accessible via MCP server, REST API, and CLI.

## Table of contents

- [Overview](#overview)
- [Account setup](#account-setup)
- [Browser extension](#browser-extension)
- [Configuring sources](#configuring-sources)
- [MCP connection](#mcp-connection)
- [Capture workflow](#capture-workflow)
- [Processing pipeline](#processing-pipeline)

---

## Overview

keep.md collects content from:

- **Browser bookmarks** (via extension)
- **X/Twitter bookmarks** (auto-sync)
- **RSS feeds**
- **YouTube videos** (with transcripts)
- **GitHub stars**
- **Email** (forwarding address)
- **Mobile** (share sheet on iOS/Android)

Everything is stored as clean markdown with metadata. The beestgraph pipeline polls the keep.md inbox via MCP every 15 minutes, processes each item, and ingests it into the knowledge graph.

---

## Account setup

1. Sign up at [keep.md](https://keep.md). The Plus plan ($10/mo) is required for MCP server access.

2. After signing up, go to Settings and note your API key.

3. Add the API key to your beestgraph configuration:

   ```bash
   # In docker/.env or as an environment variable
   KEEPMD_API_KEY=your-api-key-here
   ```

---

## Browser extension

Install the keep.md browser extension:

- [Chrome Web Store](https://keep.md) (check keep.md docs for current link)
- [Firefox Add-ons](https://keep.md)

Once installed:

1. Click the keep.md icon in your browser toolbar.
2. Sign in with your keep.md account.
3. To save any page, click the icon or use the keyboard shortcut (default: `Ctrl+Shift+K` / `Cmd+Shift+K`).
4. The page title, URL, and selected text (if any) are saved to your keep.md inbox.

---

## Configuring sources

In the keep.md web interface or via the MCP `add_source` tool, connect your content sources:

### X/Twitter bookmarks

1. Go to keep.md Settings > Sources.
2. Connect your X/Twitter account.
3. Any tweet you bookmark on X is automatically saved to keep.md.

### RSS feeds

Add RSS feed URLs through keep.md settings or via MCP:

```
# Via the keep.md MCP tool (used by Claude Code)
add_source(type="rss", url="https://example.com/feed.xml")
```

### YouTube

Connect your YouTube account. When you add a video to a playlist or like a video, keep.md captures the video metadata and transcript.

### GitHub stars

Connect your GitHub account. Starred repositories are captured with their README content.

### Email

keep.md provides a forwarding email address. Forward newsletters or articles to this address, and they appear in your inbox.

---

## MCP connection

The keep.md MCP server is configured in `config/mcp.json`:

```json
{
  "mcpServers": {
    "keep": {
      "transport": "http",
      "url": "https://keep.md/mcp"
    }
  }
}
```

Authentication happens via your keep.md session. When Claude Code connects to the MCP server, it authenticates with your account.

### Available MCP tools

| Tool | Description |
|------|-------------|
| `list_inbox` | List unprocessed items in your inbox |
| `get_item` | Get full content and metadata for a specific item |
| `mark_done` | Mark an item as processed |
| `search_items` | Search across all saved items |
| `save_item` | Save a new item to keep.md |
| `update_item` | Update an existing item |
| `add_source` | Add a new content source (RSS, etc.) |
| `remove_source` | Remove a content source |
| `list_sources` | List all configured sources |
| `get_stats` | Get inbox and source statistics |
| `whoami` | Get current user info |
| `list_items` | List all items (with filters) |

---

## Capture workflow

The typical flow from capture to knowledge graph:

1. **You save something** -- browser extension, X bookmark, RSS auto-sync, email forward, or mobile share.

2. **keep.md stores it** -- as clean markdown with title, URL, content excerpt, and source metadata.

3. **Cron triggers the poller** -- every 15 minutes, `scripts/process-keepmd.sh` runs.

4. **Claude Code processes each item**:
   - Reads the item via `keep.md MCP: get_item`
   - Extracts entities (people, concepts, organizations)
   - Categorizes by topic (from the taxonomy) and PARA category
   - Generates a 2-3 sentence summary
   - Writes a formal markdown file to the vault via `Filesystem MCP: write_file`
   - Ingests into the knowledge graph via `Graphiti MCP: add_episode`
   - Marks the source item as done via `keep.md MCP: mark_done`

5. **The knowledge graph is updated** -- new Document, Tag, Topic, Person, Concept, and Source nodes are created (or merged if they already exist).

---

## Processing pipeline

The keep.md processing is defined in `scripts/process-keepmd.sh`, which calls Claude Code in headless mode:

```bash
# scripts/process-keepmd.sh (simplified)
claude -p "Process all unread keep.md inbox items" \
  --mcp-config config/mcp.json \
  --allowedTools "mcp__keep__*,mcp__filesystem__*,mcp__graphiti__*"
```

The agent uses the prompt templates in `agent/prompts/` for categorization, entity extraction, and summarization.

### Manual processing

To process keep.md items manually (outside of cron):

```bash
make run-poller
```

Or trigger Claude Code directly:

```bash
claude -p "List unprocessed items from keep.md inbox and process the 5 most recent"
```

### Monitoring

Check the poller log for processing status:

```bash
tail -f /tmp/beestgraph-poller.log
```

Each processed item logs: item ID, source URL, entities extracted, topics assigned, and vault path written.
