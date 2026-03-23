# Contributing to beestgraph

Thank you for your interest in contributing to beestgraph. This document covers the development setup, workflow, and standards you need to follow.

---

## Table of contents

- [Development setup](#development-setup)
- [Branch naming](#branch-naming)
- [Commit messages](#commit-messages)
- [Pull request process](#pull-request-process)
- [Code standards](#code-standards)
- [Testing](#testing)
- [Code of conduct](#code-of-conduct)

---

## Development setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 20+ and npm (for web UI)
- Docker and Docker Compose
- Git

### Getting started

```bash
# Clone the repository
git clone https://github.com/terbeest/beestgraph.git
cd beestgraph

# Install Python dependencies (includes dev tools)
uv sync --extra dev

# Install web UI dependencies
cd src/web && npm install && cd ../..

# Copy configuration templates
cp config/beestgraph.yml.example config/beestgraph.yml
cp docker/.env.example docker/.env

# Start Docker services
make docker-up

# Initialize the graph schema
make init-schema

# Verify everything works
make lint
make test
```

### Editor setup

Configure your editor to use:

- **Python**: ruff for formatting (line length 100) and linting
- **TypeScript**: prettier for formatting, eslint with `next/core-web-vitals`
- **Line endings**: LF (Unix-style)
- **Trailing whitespace**: trim on save

---

## Branch naming

Use prefixed branch names that describe the change:

| Prefix | Use for |
|--------|---------|
| `feat/` | New features or capabilities |
| `fix/` | Bug fixes |
| `docs/` | Documentation changes |
| `refactor/` | Code restructuring without behavior change |
| `test/` | Adding or improving tests |
| `chore/` | Build, CI, dependency updates |

Examples:
- `feat/telegram-bot-search`
- `fix/falkordb-reconnect`
- `docs/setup-guide-tailscale`

---

## Commit messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must follow this format:

```
<type>: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or correcting tests |
| `chore` | Build process, CI, dependency updates |

### Examples

```
feat: add keep.md inbox polling via MCP

fix: handle FalkorDB connection timeout on slow networks

docs: add troubleshooting section for ARM64 Docker

refactor: extract entity normalization into shared utility

test: add integration tests for FalkorDB ingestion
```

Keep the first line under 72 characters. Use the body for additional context when the "why" is not obvious from the description.

---

## Pull request process

1. **Create a branch** from `main` using the naming convention above.

2. **Make focused changes.** Each PR should address one concern. Avoid mixing unrelated changes.

3. **Write or update tests** for any code changes. The test coverage target is 80% on `src/`.

4. **Run checks locally** before pushing:
   ```bash
   make lint
   make test
   ```

5. **Push and open a PR** against `main`. Fill in the PR template with:
   - A summary of what changed and why
   - How to test the changes
   - Any migration steps or breaking changes

6. **CI must pass.** The GitHub Actions workflow runs `ruff check`, `ruff format --check`, and `pytest`.

7. **Address review feedback** with new commits (do not force-push over review comments).

---

## Code standards

### Python

- **Formatter**: `ruff format` (line length 100)
- **Linter**: `ruff check` with rules: E, W, F, I (isort), UP (pyupgrade), S (bandit), B (bugbear), SIM, RUF
- **Type hints**: Required on all public functions. Use `from __future__ import annotations`.
- **Docstrings**: Google style on all public modules, classes, and functions.
- **Async**: Prefer `async`/`await` for I/O-bound operations.
- **Error handling**: Catch specific exceptions. Never bare `except:`. Log with `structlog`.
- **Imports**: Standard lib, then third-party, then local -- each group separated by a blank line.

### TypeScript / Next.js

- **Formatter**: prettier
- **Linter**: eslint with `next/core-web-vitals`
- **Styling**: Tailwind CSS utility classes
- **Components**: Functional components with hooks only
- **File naming**: `PascalCase.tsx` for components, `camelCase.ts` for utilities

### General

- No secrets in code. Use environment variables or `.env` files (gitignored).
- No dead code. Remove unused imports, variables, and functions.
- File naming: Python uses `snake_case.py`, TypeScript uses conventions above.

---

## Testing

```bash
# Run all tests with coverage
make test

# Run a specific test file
uv run pytest tests/test_pipeline/test_ingester.py -v

# Run tests matching a pattern
uv run pytest -k "test_normalize" -v
```

- Use `pytest` and `pytest-asyncio` for async tests.
- Place test files in `tests/` mirroring the `src/` directory structure.
- Use fixtures in `tests/conftest.py` for shared setup (FalkorDB connections, sample data).
- Avoid tests that require external services unless marked with `@pytest.mark.integration`.

---

## Code of conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you agree to uphold a welcoming, inclusive, and respectful environment.

Report unacceptable behavior by opening an issue or contacting the maintainer directly.
