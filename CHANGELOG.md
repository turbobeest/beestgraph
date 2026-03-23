# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-alpha] - 2026-03-22

### Added

- Project architecture design and documentation
- Repository structure with `src/`, `docker/`, `scripts/`, `config/`, `tests/`, `docs/`
- `pyproject.toml` with all Python dependencies (FalkorDB, watchdog, aiogram, etc.)
- `Makefile` with build, lint, test, Docker, and service commands
- Docker Compose configuration for FalkorDB (ARM64)
- Graph schema definition with 7 node types and 9 relationship types
- MCP server configuration for keep.md, Filesystem, and FalkorDB
- System architecture diagram (Graphviz DOT + SVG)
- Claude Code agent context (`CLAUDE.md`) with full project specifications
- Documentation: architecture deep-dive, setup guide, configuration reference, schema reference, integration guides, troubleshooting
- GitHub Actions CI workflow (ruff lint + pytest)
- GitHub issue templates for bug reports and feature requests
- MIT license

[0.1.0-alpha]: https://github.com/terbeest/beestgraph/releases/tag/v0.1.0-alpha
