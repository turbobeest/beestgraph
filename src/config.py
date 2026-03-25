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


class KeepMDSettings(BaseSettings):
    """keep.md MCP / API settings."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_KEEPMD_")

    api_url: str = "https://keep.md/mcp"
    api_key: str = ""
    polling_interval_minutes: int = 15
    poll_interval: int = 900
    max_items_per_cycle: int = 20
    enabled_sources: list[str] = Field(
        default_factory=lambda: [
            "browser",
            "mobile",
            "rss",
            "twitter",
            "youtube",
            "github",
            "email",
        ]
    )


class TelegramSettings(BaseSettings):
    """Telegram bot settings."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_TELEGRAM_")

    bot_token: str = ""
    allowed_user_ids: list[int] = Field(default_factory=list)
    allowed_users: list[int] = Field(default_factory=list)
    enabled: bool = False

    def get_allowed_ids(self) -> list[int]:
        """Return the effective allowed user ID list.

        Merges ``allowed_user_ids`` and ``allowed_users`` for backwards
        compatibility with configs using either field name.

        Returns:
            Deduplicated list of allowed Telegram user IDs.
        """
        combined = set(self.allowed_user_ids) | set(self.allowed_users)
        return sorted(combined)


class VaultSettings(BaseSettings):
    """Obsidian vault paths."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_VAULT_")

    path: str = str(Path.home() / "vault")
    inbox_dir: str = "inbox"
    knowledge_dir: str = "knowledge"
    templates_dir: str = "templates"
    projects_dir: str = "projects"
    areas_dir: str = "areas"
    resources_dir: str = "resources"
    archives_dir: str = "archives"


class ProcessingSettings(BaseSettings):
    """LLM processing configuration."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_PROCESSING_")

    model: str = "claude-sonnet-4-20250514"
    embedding_model: str = "text-embedding-3-small"
    concurrency: int = 2
    max_retries: int = 3


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_LOGGING_")

    level: str = "INFO"
    format: str = "console"
    file: str = ""


class WebSettings(BaseSettings):
    """Web UI configuration."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_WEB_")

    port: int = 3001
    host: str = "0.0.0.0"  # noqa: S104


class BackupSettings(BaseSettings):
    """Backup configuration."""

    model_config = SettingsConfigDict(env_prefix="BEESTGRAPH_BACKUP_")

    dir: str = str(Path.home() / "backups" / "beestgraph")
    retention: int = 7


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
    claude_code_binary: str = str(Path.home() / ".local" / "bin" / "claude")
    enable_llm_processing: bool = True

    falkordb: FalkorDBSettings = Field(default_factory=FalkorDBSettings)
    keepmd: KeepMDSettings = Field(default_factory=KeepMDSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    vault: VaultSettings = Field(default_factory=VaultSettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    web: WebSettings = Field(default_factory=WebSettings)
    backup: BackupSettings = Field(default_factory=BackupSettings)


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
    # Filter to only fields the model recognizes to avoid pydantic extra_forbidden errors.
    known_top_keys = set(BeestgraphSettings.model_fields.keys())
    filtered = {k: v for k, v in overrides.items() if k in known_top_keys}
    # Also filter nested dicts to their sub-model fields.
    _nested_models: dict[str, type[BaseSettings]] = {
        "vault": VaultSettings,
        "falkordb": FalkorDBSettings,
        "keepmd": KeepMDSettings,
        "telegram": TelegramSettings,
        "processing": ProcessingSettings,
        "logging": LoggingSettings,
        "web": WebSettings,
        "backup": BackupSettings,
    }
    for key, model_cls in _nested_models.items():
        if key in filtered and isinstance(filtered[key], dict):
            sub_keys = set(model_cls.model_fields.keys())
            # Filter to known keys and drop empty strings so env vars can override.
            filtered[key] = {
                k: v for k, v in filtered[key].items()
                if k in sub_keys and v != ""
            }
    settings = BeestgraphSettings(**filtered)
    logger.info(
        "settings_loaded",
        config_path=str(path),
        log_level=settings.log_level,
        vault_path=settings.vault.path,
    )
    return settings
