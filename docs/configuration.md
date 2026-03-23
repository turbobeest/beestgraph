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
#
# These fields match the Python model in src/config.py (BeestgraphSettings).
# Unrecognized fields are silently ignored.

# ── Top-level ───────────────────────────────────────────────
log_level: INFO                # DEBUG | INFO | WARNING | ERROR
taxonomy_path: config/taxonomy.yml  # Path to topic taxonomy definition
claude_code_binary: claude     # Path to Claude Code CLI binary
enable_llm_processing: true    # Set false to skip LLM calls in the pipeline

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

# ── keep.md ─────────────────────────────────────────────────
keepmd:
  api_url: https://keep.md/mcp # keep.md MCP endpoint URL
  api_key: ""                  # keep.md API key (prefer env var)
  polling_interval_minutes: 15 # Minutes between polls

# ── Telegram Bot ────────────────────────────────────────────
telegram:
  bot_token: ""                # Bot token from @BotFather (prefer env var)
  allowed_user_ids: []         # List of allowed Telegram user IDs
```

---

## Environment variables

Environment variables override `config/beestgraph.yml` values. The naming convention is `BEESTGRAPH_` prefix with double underscores for nesting.

| Variable | Config path | Type | Description |
|----------|------------|------|-------------|
| `BEESTGRAPH_LOG_LEVEL` | `log_level` | string | Logging level |
| `BEESTGRAPH_TAXONOMY_PATH` | `taxonomy_path` | string | Path to taxonomy YAML |
| `BEESTGRAPH_CLAUDE_CODE_BINARY` | `claude_code_binary` | string | Claude Code CLI path |
| `BEESTGRAPH_ENABLE_LLM_PROCESSING` | `enable_llm_processing` | bool | Enable LLM calls |
| `BEESTGRAPH_VAULT_PATH` | `vault.path` | string | Vault root path |
| `BEESTGRAPH_FALKORDB_HOST` | `falkordb.host` | string | FalkorDB hostname |
| `BEESTGRAPH_FALKORDB_PORT` | `falkordb.port` | int | FalkorDB port |
| `BEESTGRAPH_FALKORDB_GRAPH_NAME` | `falkordb.graph_name` | string | Graph name |
| `BEESTGRAPH_KEEPMD_API_URL` | `keepmd.api_url` | string | keep.md MCP endpoint |
| `BEESTGRAPH_KEEPMD_POLLING_INTERVAL_MINUTES` | `keepmd.polling_interval_minutes` | int | Poll interval (minutes) |

### Sensitive variables (never put in config file)

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude Code |
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
| `ANTHROPIC_API_KEY` | (required) | Anthropic API key for Claude Code |
| `FALKORDB_PORT` | `6379` | Host port for FalkorDB |

### Docker resource limits

Defined in `docker/docker-compose.yml`:

| Service | Memory limit | Purpose |
|---------|-------------|---------|
| FalkorDB | 8 GB | In-memory graph database |

On a 16GB Pi 5, this leaves approximately 8GB for the OS, Python pipeline, web UI, and other services. Adjust the limits in `docker/docker-compose.yml` if needed.

---

## MCP server configuration

MCP servers are configured in `config/mcp.json`. This file is read by Claude Code to connect to the three servers.

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
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/vault"]
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

Replace `~/vault` with your actual vault path.

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
