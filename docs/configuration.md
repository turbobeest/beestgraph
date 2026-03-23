# Configuration

All beestgraph configuration lives in `config/beestgraph.yml` with environment variable overrides. Sensitive values (API keys, tokens) should always be set via environment variables or `docker/.env`, never committed to the repository.

## Table of contents

- [Configuration file](#configuration-file)
- [Environment variables](#environment-variables)
- [Docker environment](#docker-environment)
- [MCP server configuration](#mcp-server-configuration)
- [Cron configuration](#cron-configuration)
- [Precedence rules](#precedence-rules)

---

## Configuration file

The main configuration file is `config/beestgraph.yml`. Copy the template to get started:

```bash
cp config/beestgraph.yml.example config/beestgraph.yml
```

### Full reference

```yaml
# config/beestgraph.yml

# ── General ─────────────────────────────────────────────────
general:
  log_level: INFO              # DEBUG | INFO | WARNING | ERROR
  log_format: json             # json | console (console for development)
  timezone: America/New_York   # IANA timezone for timestamps

# ── Vault ───────────────────────────────────────────────────
vault:
  path: ~/vault                # Absolute or ~ path to Obsidian vault root
  inbox_dir: inbox             # Subdirectory watchdog monitors
  knowledge_dir: knowledge     # Where processed articles go
  templates_dir: templates     # Frontmatter templates

# ── FalkorDB ────────────────────────────────────────────────
falkordb:
  host: localhost              # FalkorDB hostname
  port: 6379                   # FalkorDB port (Redis protocol)
  graph_name: beestgraph       # Name of the graph in FalkorDB
  password: ""                 # Redis password (if set)

# ── Graphiti ────────────────────────────────────────────────
graphiti:
  url: http://localhost:8000   # Graphiti MCP server URL
  model: claude-sonnet-4-20250514  # Model for Graphiti's LLM calls
  embedding_model: text-embedding-3-small

# ── keep.md ─────────────────────────────────────────────────
keepmd:
  enabled: true                # Enable keep.md polling
  poll_interval: 900           # Seconds between polls (900 = 15 min)
  api_key: ""                  # keep.md API key (prefer env var)
  mcp_url: https://keep.md/mcp

# ── Telegram Bot ────────────────────────────────────────────
telegram:
  enabled: false               # Enable Telegram bot
  bot_token: ""                # Bot token from @BotFather (prefer env var)
  allowed_users: []            # List of allowed Telegram user IDs

# ── Processing ──────────────────────────────────────────────
processing:
  max_concurrent: 2            # Max items processed simultaneously
  summary_max_words: 100       # Target word count for AI summaries
  entity_confidence_threshold: 0.7  # Min confidence for entity extraction
  default_para_category: resources   # Default PARA category for new items

# ── Taxonomy ────────────────────────────────────────────────
taxonomy:
  file: config/taxonomy.yml    # Path to topic taxonomy definition
```

---

## Environment variables

Environment variables override `config/beestgraph.yml` values. The naming convention is `BEESTGRAPH_` prefix with double underscores for nesting.

| Variable | Config path | Type | Description |
|----------|------------|------|-------------|
| `BEESTGRAPH_GENERAL__LOG_LEVEL` | `general.log_level` | string | Logging level |
| `BEESTGRAPH_VAULT__PATH` | `vault.path` | string | Vault root path |
| `BEESTGRAPH_FALKORDB__HOST` | `falkordb.host` | string | FalkorDB hostname |
| `BEESTGRAPH_FALKORDB__PORT` | `falkordb.port` | int | FalkorDB port |
| `BEESTGRAPH_FALKORDB__GRAPH_NAME` | `falkordb.graph_name` | string | Graph name |
| `BEESTGRAPH_GRAPHITI__URL` | `graphiti.url` | string | Graphiti server URL |
| `BEESTGRAPH_KEEPMD__ENABLED` | `keepmd.enabled` | bool | Enable keep.md polling |
| `BEESTGRAPH_KEEPMD__POLL_INTERVAL` | `keepmd.poll_interval` | int | Poll interval (seconds) |
| `BEESTGRAPH_TELEGRAM__ENABLED` | `telegram.enabled` | bool | Enable Telegram bot |
| `BEESTGRAPH_PROCESSING__MAX_CONCURRENT` | `processing.max_concurrent` | int | Max concurrent items |

### Sensitive variables (never put in config file)

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude Code and Graphiti |
| `KEEPMD_API_KEY` | keep.md API key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather |

Set these in `docker/.env` or export them in your shell profile.

---

## Docker environment

Docker services read from `docker/.env`. Copy the template:

```bash
cp docker/.env.example docker/.env
```

### Docker environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Anthropic API key for Graphiti LLM calls |
| `FALKORDB_PORT` | `6379` | Host port for FalkorDB |
| `GRAPHITI_MODEL` | `claude-sonnet-4-20250514` | LLM model for Graphiti |
| `GRAPHITI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model for Graphiti |

### Docker resource limits

Defined in `docker/docker-compose.yml`:

| Service | Memory limit | Purpose |
|---------|-------------|---------|
| FalkorDB | 8 GB | In-memory graph database |
| Graphiti | 2 GB | Knowledge graph framework |

On a 16GB Pi 5, this leaves approximately 6GB for the OS, Python pipeline, web UI, and other services. Adjust the limits in `docker/docker-compose.yml` if needed.

---

## MCP server configuration

MCP servers are configured in `config/mcp.json`. This file is read by Claude Code to connect to the four servers.

```bash
cp config/mcp.json.example config/mcp.json
```

See [`docs/mcp-servers.md`](mcp-servers.md) for detailed server configuration and tool reference.

### MCP configuration format

```json
{
  "mcpServers": {
    "keep": {
      "transport": "http",
      "url": "https://keep.md/mcp"
    },
    "graphiti": {
      "command": "graphiti-mcp-server",
      "args": ["--transport", "sse"],
      "env": {
        "FALKORDB_HOST": "localhost",
        "FALKORDB_PORT": "6379"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/vault"]
    },
    "falkordb": {
      "command": "npx",
      "args": ["-y", "@falkordb/falkordb-mcp-server"],
      "env": {
        "FALKORDB_HOST": "localhost",
        "FALKORDB_PORT": "6379"
      }
    }
  }
}
```

Replace `/path/to/vault` with your actual vault path.

---

## Cron configuration

The keep.md poller runs on a cron schedule. Add this to your crontab (`crontab -e`):

```
*/15 * * * * cd /path/to/beestgraph && make run-poller >> /tmp/beestgraph-poller.log 2>&1
```

Adjust the interval as needed. The default of 15 minutes balances responsiveness with API usage.

---

## Precedence rules

Configuration values are resolved in this order (highest priority first):

1. **Environment variables** (`BEESTGRAPH_*` prefix)
2. **`docker/.env`** (for Docker services)
3. **`config/beestgraph.yml`** (main config file)
4. **Built-in defaults** (defined in `src/config.py` via pydantic `BaseSettings`)

This means you can set defaults in the YAML file and override specific values per-environment using environment variables, without modifying any files.
