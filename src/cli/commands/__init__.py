"""Command base classes and shared types for the bg CLI.

Every command implements :class:`BaseCommand` with a ``run_without_agent``
method that performs the operation using only local code (no LLM calls).
The optional ``run_with_agent`` path enhances the base result via an
LLMAgent — this is a no-op in Phase 1.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Result:
    """Structured result returned by every CLI command.

    Attributes:
        success: Whether the command completed without error.
        output: Human-readable output text.
        data: Optional structured data for programmatic consumers.
        error: Error message if ``success`` is ``False``.
    """

    success: bool
    output: str
    data: Any | None = None
    error: str | None = None


class BaseCommand(ABC):
    """Two-path command contract.

    All commands must implement ``run_without_agent``. The ``run_with_agent``
    method provides the LLM-enhanced path (Phase 2+).
    """

    agent_prompt: str = ""

    @abstractmethod
    def run_without_agent(self, **kwargs: Any) -> Result:
        """Execute the command without LLM assistance."""
        ...

    def run_with_agent(self, agent: Any, **kwargs: Any) -> Result:
        """Execute the command with optional LLM enhancement.

        Falls back to the base path if no agent is provided or if the
        base path fails.
        """
        base = self.run_without_agent(**kwargs)
        if not base.success:
            return base
        if agent and hasattr(agent, "enhance"):
            return agent.enhance(base, self.agent_prompt)
        return base
