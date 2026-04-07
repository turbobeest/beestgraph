"""LLM agent interface — pluggable provider for AI-enhanced operations.

Defines the ``LLMAgent`` protocol and concrete implementations for
Anthropic and Ollama. All commands that accept ``--agent`` use this
interface. The system works identically without any agent configured.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import structlog

logger = structlog.get_logger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "agent.toml"


@dataclass
class AgentConfig:
    """Configuration for an LLM provider.

    Attributes:
        provider: Provider key (``"anthropic"``, ``"ollama"``, ``"openai_compatible"``).
        model: Model identifier (e.g. ``"claude-sonnet-4-6"``).
        api_key: API key (resolved from env var if not set directly).
        base_url: Provider base URL.
    """

    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    api_key: str | None = None
    base_url: str | None = None


@runtime_checkable
class LLMAgent(Protocol):
    """Protocol for LLM agent implementations.

    Any object that implements these three methods can serve as an agent.
    """

    def enhance(self, base_result: Any, prompt: str) -> Any:
        """Enhance a base command result with LLM synthesis."""
        ...

    def synthesize(self, documents: list[Any], prompt: str) -> str:
        """Synthesize insights across multiple documents."""
        ...

    def rewrite(self, existing: str, context: str, prompt: str) -> str:
        """Rewrite or update existing text given new context."""
        ...


class AnthropicAgent:
    """Wraps the Anthropic API. Default provider.

    Uses the ``anthropic`` Python SDK to call the Messages API.
    Falls back gracefully if the SDK is not installed or the API key
    is missing.
    """

    def __init__(self, config: AgentConfig) -> None:
        self._config = config
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:
                raise RuntimeError(
                    "The 'anthropic' package is required for AnthropicAgent. "
                    "Install it with: uv add anthropic"
                ) from exc
            api_key = self._config.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY environment variable is not set."
                )
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def _call(self, prompt: str, system: str = "") -> str:
        """Send a single message to the Anthropic API and return the text."""
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self._config.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text

    def enhance(self, base_result: Any, prompt: str) -> Any:
        """Enhance a base Result with LLM synthesis.

        Appends the LLM's response to the base result's output.
        """
        from src.cli.commands import Result

        system = (
            "You are an analytical assistant for a personal knowledge graph. "
            "You receive structured data from graph queries and produce "
            "concise, insightful prose synthesis."
        )
        full_prompt = f"{prompt}\n\nStructured data:\n{base_result.output}"
        try:
            synthesis = self._call(full_prompt, system=system)
        except Exception as exc:
            logger.warning("agent_enhance_failed", error=str(exc))
            return base_result
        return Result(
            success=True,
            output=f"{base_result.output}\n\n--- Agent Synthesis ---\n{synthesis}",
            data=base_result.data,
        )

    def synthesize(self, documents: list[Any], prompt: str) -> str:
        """Synthesize insights across multiple documents."""
        doc_text = "\n\n".join(str(d) for d in documents)
        full_prompt = f"{prompt}\n\nDocuments:\n{doc_text}"
        return self._call(full_prompt)

    def rewrite(self, existing: str, context: str, prompt: str) -> str:
        """Rewrite existing text given new context."""
        full_prompt = f"{prompt}\n\nExisting text:\n{existing}\n\nNew context:\n{context}"
        return self._call(full_prompt)


class OllamaAgent:
    """Local Ollama agent. Privacy-preserving fallback.

    Calls the Ollama HTTP API at the configured base URL.
    """

    def __init__(self, config: AgentConfig) -> None:
        self._config = config
        self._base_url = config.base_url or "http://localhost:11434"

    def _call(self, prompt: str) -> str:
        import httpx

        response = httpx.post(
            f"{self._base_url}/api/generate",
            json={"model": self._config.model, "prompt": prompt, "stream": False},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json().get("response", "")

    def enhance(self, base_result: Any, prompt: str) -> Any:
        from src.cli.commands import Result

        full_prompt = f"{prompt}\n\nStructured data:\n{base_result.output}"
        try:
            synthesis = self._call(full_prompt)
        except Exception as exc:
            logger.warning("ollama_enhance_failed", error=str(exc))
            return base_result
        return Result(
            success=True,
            output=f"{base_result.output}\n\n--- Agent Synthesis ---\n{synthesis}",
            data=base_result.data,
        )

    def synthesize(self, documents: list[Any], prompt: str) -> str:
        doc_text = "\n\n".join(str(d) for d in documents)
        return self._call(f"{prompt}\n\nDocuments:\n{doc_text}")

    def rewrite(self, existing: str, context: str, prompt: str) -> str:
        return self._call(
            f"{prompt}\n\nExisting text:\n{existing}\n\nNew context:\n{context}"
        )


def _load_toml(path: Path) -> dict[str, Any]:
    """Load a TOML file, returning an empty dict on failure."""
    if not path.is_file():
        return {}
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]
    with path.open("rb") as f:
        return tomllib.load(f)


def load_agent(config_path: str | None = None) -> LLMAgent:
    """Load an LLM agent from config/agent.toml.

    Returns an AnthropicAgent by default. Falls back to OllamaAgent
    if the provider is set to ``"ollama"``.

    Args:
        config_path: Optional override for the TOML config path.
    """
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
    toml = _load_toml(path)

    agent_section = toml.get("agent", {})
    provider = agent_section.get("default_provider", "anthropic")
    model = agent_section.get("default_model", "claude-sonnet-4-6")

    providers = toml.get("providers", {})
    provider_conf = providers.get(provider, {})

    api_key: str | None = None
    if api_key_env := provider_conf.get("api_key_env"):
        api_key = os.environ.get(api_key_env)

    base_url = provider_conf.get("base_url")
    if provider == "ollama":
        model = provider_conf.get("default_model", model)

    config = AgentConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
    )

    if provider == "ollama":
        return OllamaAgent(config)
    return AnthropicAgent(config)
