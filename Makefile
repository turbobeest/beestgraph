# beestgraph/Makefile

.PHONY: help setup install lint format test run-watcher run-poller run-bot run-all \
        docker-up docker-down docker-logs web-dev web-build init-schema backup clean

PYTHON := python3
UV := uv
VAULT_PATH ?= $(HOME)/vault

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Setup ────────────────────────────────────────────────────

setup: install docker-up init-schema ## Full setup (install deps, start Docker, init schema)
	@echo "\n✅ beestgraph setup complete!"

install: ## Install Python dependencies with uv (including dev tools)
	$(UV) sync --extra dev

# ── Code Quality ─────────────────────────────────────────────

lint: ## Run linters (ruff check + format check)
	$(UV) run ruff check src/ tests/
	$(UV) run ruff format --check src/ tests/

format: ## Auto-format code
	$(UV) run ruff format src/ tests/
	$(UV) run ruff check --fix src/ tests/

test: ## Run tests with coverage
	$(UV) run pytest tests/ -v --cov=src --cov-report=term-missing

# ── Pipeline Services ────────────────────────────────────────

run-watcher: ## Start the vault inbox watchdog daemon
	$(UV) run python -m src.pipeline.watcher

run-poller: ## Run keep.md inbox poller once (for cron)
	$(UV) run python -m src.pipeline.keepmd_poller

run-bot: ## Start the Telegram bot
	$(UV) run python -m src.bot.telegram_bot

run-all: ## Start all Python services (watcher + bot)
	@echo "Starting vault watcher in background..."
	$(UV) run python -m src.pipeline.watcher & WATCHER_PID=$$!; \
	trap "kill $$WATCHER_PID 2>/dev/null" EXIT INT TERM; \
	echo "Watcher PID: $$WATCHER_PID"; \
	echo "Starting Telegram bot (Ctrl+C stops both)..."; \
	$(UV) run python -m src.bot.telegram_bot

# ── Docker ───────────────────────────────────────────────────

docker-up: ## Start FalkorDB container
	cd docker && docker compose up -d

docker-down: ## Stop containers
	cd docker && docker compose down

docker-logs: ## Tail container logs
	cd docker && docker compose logs -f

docker-restart: ## Restart containers
	cd docker && docker compose restart

# ── Web UI ───────────────────────────────────────────────────

web-dev: ## Start Next.js dev server
	cd src/web && npm run dev

web-build: ## Build Next.js for production
	cd src/web && npm run build

web-install: ## Install web UI dependencies
	cd src/web && npm install

# ── Database ─────────────────────────────────────────────────

init-schema: ## Create FalkorDB indexes and seed taxonomy
	bash scripts/init-schema.sh

# ── Maintenance ──────────────────────────────────────────────

backup: ## Snapshot FalkorDB + vault backup
	bash scripts/backup.sh

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

# ── Diagrams ─────────────────────────────────────────────────

diagrams: ## Regenerate system architecture SVG from DOT source
	dot -Tsvg docs/diagrams/beestgraph-system.dot -o docs/diagrams/beestgraph-system.svg
	@echo "Diagram updated: docs/diagrams/beestgraph-system.svg"
