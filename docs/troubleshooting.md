# Troubleshooting

Common issues and their solutions when running beestgraph on a Raspberry Pi 5.

## Table of contents

- [Docker and containers](#docker-and-containers)
- [FalkorDB](#falkordb)
- [Graphiti](#graphiti)
- [ARM64 compatibility](#arm64-compatibility)
- [Tailscale and network access](#tailscale-and-network-access)
- [Claude Code](#claude-code)
- [Vault and Syncthing](#vault-and-syncthing)
- [Processing pipeline](#processing-pipeline)

---

## Docker and containers

### Containers fail to start with out-of-memory errors

**Symptom**: `docker compose up` fails or containers restart repeatedly. `docker logs beestgraph-falkordb` shows OOM errors.

**Cause**: FalkorDB is configured with an 8GB memory limit, which may be too high if other processes are using significant memory.

**Fix**: Reduce the memory limit in `docker/docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 4g  # Reduce from 8g
```

Check available memory:

```bash
free -h
```

On a 16GB Pi, aim for: FalkorDB 6-8GB, Graphiti 1-2GB, leaving 6-8GB for OS and services.

### Docker Compose version errors

**Symptom**: `docker compose` commands fail with syntax errors.

**Cause**: Older versions of Docker may use `docker-compose` (with hyphen) instead of `docker compose` (as a Docker subcommand).

**Fix**: Update Docker to the latest version:

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

### Docker data fills up the SD card

**Symptom**: Disk space warnings. `df -h` shows `/` is nearly full.

**Cause**: Docker data is stored on the SD card by default.

**Fix**: Move Docker data to the NVMe SSD. See the [setup guide](setup-guide.md#4-docker) for instructions.

---

## FalkorDB

### Cannot connect to FalkorDB

**Symptom**: Pipeline or tools report connection refused on port 6379.

**Fix**: Check that the container is running and healthy:

```bash
docker ps
docker logs beestgraph-falkordb
```

Test the connection:

```bash
docker exec beestgraph-falkordb redis-cli PING
# Expected: PONG
```

If the container is running but not responding, it may still be loading data. Check the health status:

```bash
docker inspect beestgraph-falkordb --format='{{.State.Health.Status}}'
```

### FalkorDB data is lost after restart

**Symptom**: Graph data is empty after a Docker restart.

**Cause**: Data persistence is not configured, or the volume was removed.

**Fix**: Verify the volume exists:

```bash
docker volume ls | grep falkordb
```

The `docker-compose.yml` configures persistence with `--save 60 1 --appendonly yes`. If data is still missing, check that the volume mount is correct:

```bash
docker inspect beestgraph-falkordb --format='{{.Mounts}}'
```

### Full-text search returns no results

**Symptom**: `CALL db.idx.fulltext.queryNodes(...)` returns empty results even though documents exist.

**Cause**: The full-text index may not have been created, or documents lack the indexed fields.

**Fix**: Recreate the indexes:

```bash
make init-schema
```

Or manually:

```cypher
CALL db.idx.fulltext.createNodeIndex('Document', 'title', 'content', 'summary')
```

---

## Graphiti

### Graphiti container fails to start

**Symptom**: Graphiti container exits immediately or restarts in a loop.

**Cause**: Usually a missing `ANTHROPIC_API_KEY` or FalkorDB not being ready.

**Fix**: Check the logs:

```bash
docker logs beestgraph-graphiti
```

Verify the API key is set:

```bash
grep ANTHROPIC_API_KEY docker/.env
```

Graphiti depends on FalkorDB being healthy. If FalkorDB is slow to start, Graphiti may time out. Restart it after FalkorDB is ready:

```bash
docker restart beestgraph-graphiti
```

### Graphiti health check fails

**Symptom**: `curl http://localhost:8000/health` returns connection refused or error.

**Fix**: The Graphiti server has a 30-second start period. Wait and retry. If it persists, check that port 8000 is not in use by another process:

```bash
sudo lsof -i :8000
```

---

## ARM64 compatibility

### Docker image not available for ARM64

**Symptom**: `docker pull` fails with "no matching manifest for linux/arm64".

**Cause**: Some Docker images do not publish ARM64 variants.

**Fix**: Check if an ARM64 image exists:

```bash
docker manifest inspect <image-name>
```

If no ARM64 image is available, you may need to build from source or use an alternative image. The images specified in `docker/docker-compose.yml` (FalkorDB, Graphiti) have ARM64 support.

### Python packages fail to build on ARM64

**Symptom**: `uv sync` fails with compilation errors for C extension packages.

**Fix**: Install build dependencies:

```bash
sudo apt install -y build-essential libffi-dev libssl-dev python3-dev
```

For specific packages that lack ARM64 wheels, you may need to install system-level alternatives:

```bash
# Example: if numpy compilation fails
sudo apt install -y python3-numpy
```

### Node.js native modules fail

**Symptom**: `npm install` fails with node-gyp errors.

**Fix**: Install build tools:

```bash
sudo apt install -y build-essential python3
```

---

## Tailscale and network access

### Cannot access services remotely

**Symptom**: FalkorDB Browser or web UI not accessible from another device.

**Fix**: Verify Tailscale is connected:

```bash
tailscale status
```

Check that the services are listening on the correct interfaces. Docker maps ports to `0.0.0.0` by default, which is accessible via Tailscale.

Test from another device on the tailnet:

```bash
curl http://<tailscale-hostname>:3000
```

### Tailscale connection drops

**Symptom**: Remote access stops working intermittently.

**Fix**: Check Tailscale logs:

```bash
sudo journalctl -u tailscaled -f
```

Ensure the Pi has a stable network connection. If using Wi-Fi, consider switching to Ethernet for reliability.

### MagicDNS not resolving

**Symptom**: `http://beestgraph:3000` does not resolve.

**Fix**: Enable MagicDNS in the Tailscale admin console (admin.tailscale.com). Use the full tailnet hostname if MagicDNS is not available:

```bash
tailscale status
# Note the IP address, use it directly
```

---

## Claude Code

### Claude Code headless mode not working

**Symptom**: `claude -p "..."` hangs or returns errors.

**Fix**: Verify Claude Code is installed and authenticated:

```bash
claude --version
claude auth status
```

If authentication has expired, re-authenticate:

```bash
claude auth login
```

### MCP servers not connecting

**Symptom**: Claude Code reports "MCP server not available" or tool calls fail.

**Fix**: Check the MCP configuration:

```bash
cat ~/.claude/mcp.json
```

Verify each server is reachable:

```bash
# Graphiti
curl -s http://localhost:8000/health

# FalkorDB (via Docker)
docker exec beestgraph-falkordb redis-cli PING

# keep.md (requires authentication)
# Check in Claude Code directly
```

Re-run the configuration script:

```bash
./scripts/configure-mcp.sh
```

### Claude Code uses too much memory

**Symptom**: System becomes unresponsive during Claude Code processing.

**Fix**: Process fewer items at a time. In the cron poller, limit the batch size. Monitor memory usage:

```bash
htop
```

If memory is consistently an issue, consider processing items sequentially rather than concurrently by setting `processing.max_concurrent: 1` in `config/beestgraph.yml`.

---

## Vault and Syncthing

### Syncthing sync conflicts

**Symptom**: Files appear with `.sync-conflict-*` suffixes.

**Cause**: The same file was modified on two devices before sync completed.

**Fix**: Manually resolve the conflict by comparing the files and keeping the correct version. Delete the conflict file.

To prevent future conflicts, add workspace files to `.stignore`:

```
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache
```

### Watchdog not detecting new files

**Symptom**: Files added to `inbox/` are not processed.

**Fix**: Check that the watchdog is running:

```bash
ps aux | grep watcher
```

Start it if not running:

```bash
make run-watcher
```

Verify the vault path is correct:

```bash
echo $VAULT_PATH
ls -la $VAULT_PATH/inbox/
```

On Linux, the watchdog uses inotify. Check the inotify watch limit:

```bash
cat /proc/sys/fs/inotify/max_user_watches
```

If it is low (8192), increase it:

```bash
echo 65536 | sudo tee /proc/sys/fs/inotify/max_user_watches
# Make persistent
echo 'fs.inotify.max_user_watches=65536' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## Processing pipeline

### Items stuck in "processing" status

**Symptom**: Documents have `status: processing` but were never completed.

**Cause**: The pipeline crashed during processing, or Claude Code timed out.

**Fix**: Reset the status to `inbox` in the frontmatter and re-process:

```yaml
status: inbox
```

Move the file back to `inbox/` if it was moved during processing.

### Duplicate entities in the graph

**Symptom**: The same person or concept appears as multiple nodes.

**Cause**: Inconsistent normalization (e.g., "Geoffrey Hinton" vs "G. Hinton").

**Fix**: Run the maintenance script to detect and merge duplicates:

```bash
uv run python -m src.graph.maintenance --deduplicate
```

The pipeline uses `normalized_name = lower(strip(name))` for deduplication, but variations in source content can still create duplicates.

### Cron job not running

**Symptom**: keep.md items are not being processed automatically.

**Fix**: Check crontab:

```bash
crontab -l
```

Verify the entry exists:

```
*/15 * * * * cd /path/to/beestgraph && make run-poller >> /tmp/beestgraph-poller.log 2>&1
```

Check the log for errors:

```bash
tail -50 /tmp/beestgraph-poller.log
```

Common issue: the cron environment does not have the same PATH as your interactive shell. Use absolute paths in the crontab or source your profile.
