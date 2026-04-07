"""Tests for src/cli/agent.py — LLMAgent interface and implementations."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.cli.agent import (
    AgentConfig,
    AnthropicAgent,
    LLMAgent,
    OllamaAgent,
    load_agent,
)
from src.cli.commands import Result


class TestLLMAgentProtocol:
    def test_anthropic_agent_implements_protocol(self) -> None:
        config = AgentConfig(provider="anthropic", model="test-model", api_key="test")
        agent = AnthropicAgent(config)
        assert isinstance(agent, LLMAgent)

    def test_ollama_agent_implements_protocol(self) -> None:
        config = AgentConfig(provider="ollama", model="test-model")
        agent = OllamaAgent(config)
        assert isinstance(agent, LLMAgent)


class TestLoadAgent:
    def test_returns_anthropic_by_default(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agent.toml"
        config_file.write_text(
            '[agent]\ndefault_provider = "anthropic"\ndefault_model = "test"\n'
        )
        agent = load_agent(str(config_file))
        assert isinstance(agent, AnthropicAgent)

    def test_returns_ollama_when_configured(self, tmp_path: Path) -> None:
        config_file = tmp_path / "agent.toml"
        config_file.write_text(
            '[agent]\ndefault_provider = "ollama"\ndefault_model = "llama3"\n'
            '[providers.ollama]\nbase_url = "http://localhost:11434"\n'
        )
        agent = load_agent(str(config_file))
        assert isinstance(agent, OllamaAgent)

    def test_missing_config_returns_anthropic(self, tmp_path: Path) -> None:
        agent = load_agent(str(tmp_path / "nonexistent.toml"))
        assert isinstance(agent, AnthropicAgent)


class TestAnthropicAgentEnhance:
    def test_enhance_calls_api(self) -> None:
        config = AgentConfig(provider="anthropic", model="test-model", api_key="test-key")
        agent = AnthropicAgent(config)

        # Mock the anthropic client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Synthesized insight")]
        mock_client.messages.create.return_value = mock_response
        agent._client = mock_client

        base_result = Result(success=True, output="Some data", data={"key": "value"})
        enhanced = agent.enhance(base_result, "Analyze this")

        assert enhanced.success
        assert "Synthesized insight" in enhanced.output
        assert "Some data" in enhanced.output
        mock_client.messages.create.assert_called_once()

    def test_enhance_falls_back_on_error(self) -> None:
        config = AgentConfig(provider="anthropic", model="test-model", api_key="test-key")
        agent = AnthropicAgent(config)

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("API error")
        agent._client = mock_client

        base_result = Result(success=True, output="Original data")
        result = agent.enhance(base_result, "Analyze this")

        # Should return base result unchanged on error
        assert result.output == "Original data"
