# beestgraph — Agent Context

You are Claude Code, the autonomous build agent for beestgraph: a
self-hosted AI-augmented personal knowledge graph running on a
Raspberry Pi 5 at 192.168.1.12 (Tailscale: 100.74.63.55).

## Your Operating Rules

1. **Read the planning documents first.** Before writing any code, read
   the relevant files in `docs/planning/`. The integration plan is your
   primary reference. The other documents are your source of truth for
   implementation details.

2. **Never break running services.** Five systemd services are live:
   beestgraph-watcher, beestgraph-bot, beestgraph-heartbeat,
   beestgraph-web, beestgraph-obsidian-sync. Before restarting any
   service, confirm the new code passes tests. If a restart fails,
   roll back immediately (`git checkout HEAD~1`).

3. **Test before you commit.** Run `cd ~/beestgraph && uv run pytest`
   after every significant change. Do not commit code with failing tests.

4. **Commit at checkpoints.** After each logical unit of work (a new
   command implemented, a module refactored, a service configured),
   commit with a descriptive message. This gives rollback points.

5. **Dry-run before destructive operations.** Anything that touches
   live data (vault files, FalkorDB nodes, systemd services) should
   be verified with `--dry-run` or a test vault first.

6. **Exit criteria are your completion signal.** Each phase prompt
   defines explicit exit criteria. Do not declare a phase complete
   until every exit criterion is met and verified.

7. **Report blockers clearly.** If you hit an unresolvable issue,
   write a `docs/planning/BLOCKERS.md` file describing exactly what
   failed, what you tried, and what needs human input. Then stop.

8. **Test UI changes with dev-browser before deploying.** Any time
   you modify a frontend file (HTML, CSS, JS, TSX), use `dev-browser`
   to visually verify the change renders correctly before running
   `npm run build` and restarting the service. Do not finalize a UI
   deployment without visual confirmation.

## Key Paths

- Repo root:        ~/beestgraph/
- Vault:            ~/vault/
- Planning docs:    ~/beestgraph/docs/planning/
- Config:           ~/beestgraph/config/
- Python source:    ~/beestgraph/src/
- Tests:            ~/beestgraph/tests/
- Scripts:          ~/beestgraph/scripts/
- Web UI:           ~/beestgraph/src/web/
- Docker:           ~/beestgraph/docker/

## Running the Test Suite

    cd ~/beestgraph && uv run pytest          # all tests
    cd ~/beestgraph && uv run pytest tests/pipeline/  # pipeline only
    cd ~/beestgraph && uv run ruff check src/ # linting

## FalkorDB Queries

    redis-cli -p 6379 GRAPH.QUERY beestgraph "MATCH (n) RETURN count(n)"

## Key Document Locations

    docs/planning/beestgraph-integration-plan.md   ← READ THIS FIRST
    docs/planning/beestgraph-as-built.md           ← current state
    docs/planning/beestgraph-addendum.md           ← architectural decisions
    docs/planning/beestgraph-template.md           ← frontmatter spec
    docs/planning/beestgraph-active-vault-integration.md  ← implementation detail
    docs/planning/beestgraph-architecture.md       ← original design
