"""
OpenRouter AI Provider

OpenRouter integration providing access to multiple AI models through a single interface.
Supports Claude, GPT, and open source models with unified API access.

Author: jango-blockchained
"""

from typing import Dict, List, Optional, Any
from .base_provider import BaseAIProvider, AIResponse


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter AI provider implementation (coming soon)."""

    OPENROUTER_MODELS = [
        "claude-4-opus-20250522",
        "claude-4-sonnet-20250522",
        "claude-3-7-sonnet-20250224",
        "gpt-4.1-latest",
        "o3-mini-latest",
        "gemini-2.5-pro-latest"
    ]

    def __init__(self, api_key: str, model: str = "claude-4-sonnet-20250522", **kwargs):
        """Initialize OpenRouter provider."""
        super().__init__(api_key, model, **kwargs)
        if not self.model:
            self.model = "claude-4-sonnet-20250522"

    @property
    def name(self) -> str:
        return "OpenRouter"

    @property
    def supported_models(self) -> List[str]:
        return self.OPENROUTER_MODELS.copy()

    @property
    def supports_thinking_mode(self) -> bool:
        # Only for Claude models routed through OpenRouter
        return "claude-4" in self.model or "claude-3-7" in self.model

    async def send_message(self, message: str, **kwargs) -> AIResponse:
        """Send message to OpenRouter (not yet implemented)."""
        raise NotImplementedError("OpenRouter provider implementation coming soon")

    async def test_connection(self) -> bool:
        """Test OpenRouter connection (not yet implemented)."""
        return False
