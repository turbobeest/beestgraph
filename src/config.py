"""Application configuration loaded from beestgraph.yml with env var overrides.

Uses pydantic BaseSettings so every field can be overridden with
``BEESTGRAPH_<SECTION>__<FIELD>`` environment variables (double-underscore
for nested models).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "beestgraph.yml"


class FalkorDBSettings(BaseSettings):
    """FalkorDB connection settings."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_FALKORDB_")

    host: str = "localhost"
    port: int = 6379
    graph_name: str = "beestgraph"
    password: str = ""


class GraphitiSettings(BaseSettings):
    """Graphiti (Zep) service settings."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_GRAPHITI_")

    url: str = "http://localhost:8000"
    timeout_seconds: int = 30


class KeepMDSettings(BaseSettings):
    """keep.md MCP / API settings."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_KEEPMD_")

    api_url: str = "https://keep.md/mcp"
    api_key: str = ""
    polling_interval_minutes: int = 15


class TelegramSettings(BaseSettings):
    """Telegram bot settings."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_TELEGRAM_")

    bot_token: str = ""
    allowed_user_ids: list[int] = Field(default_factory=list)


class VaultSettings(BaseSettings):
    """Obsidian vault paths."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_VAULT_")

    path: str = str(Path.home() / "vault")
    inbox_dir: str = "inbox"
    knowledge_dir: str = "knowledge"
    templates_dir: str = "templates"


class BeestgraphSettings(BaseSettings):
    """Top-level application settings.

    Loads values in this priority (highest wins):
        1. Environment variables (``BEESTGRAPH_*``)
        2. Config YAML file (``config/beestgraph.yml``)
        3. Field defaults defined here
    """

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_")

    log_level: str = "INFO"
    taxonomy_path: str = str(_PROJECT_ROOT / "config" / "taxonomy.yml")
    claude_code_binary: str = "claude"
    enable_llm_processing: bool = True

    falkordb: FalkorDBSettings = Field(default_factory=FalkorDBSettings)
    graphiti: GraphitiSettings = Field(default_factory=GraphitiSettings)
    keepmd: KeepMDSettings = Field(default_factory=KeepMDSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    vault: VaultSettings = Field(default_factory=VaultSettings)


def _load_yaml_overrides(path: Path) -> dict[str, Any]:
    """Read the YAML config file and return a flat dict.

    Args:
        path: Filesystem path to the YAML config file.

    Returns:
        Parsed dict from YAML, or empty dict if the file is missing / invalid.
    """
    if not path.is_file():
        logger.warning("config_file_missing", path=str(path))
        return {}
    try:
        with path.open() as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError as exc:
        logger.error("config_yaml_parse_error", path=str(path), error=str(exc))
        return {}


def load_settings(config_path: Path | None = None) -> BeestgraphSettings:
    """Build a fully-resolved settings object.

    Args:
        config_path: Optional override for the config YAML location.
            Defaults to ``config/beestgraph.yml`` relative to the project root.

    Returns:
        A validated ``BeestgraphSettings`` instance.
    """
    path = config_path or _DEFAULT_CONFIG_PATH
    overrides = _load_yaml_overrides(path)
    settings = BeestgraphSettings(**overrides)
    logger.info(
        "settings_loaded",
        config_path=str(path),
        log_level=settings.log_level,
        vault_path=settings.vault.path,
    )
    return settings
