"""
Gemini AI Provider

Google Gemini integration with multimodal capabilities and large context windows.
Provides excellent performance for CAD documentation analysis and multimodal tasks.

Author: jango-blockchained
"""

from typing import Dict, List, Optional, Any
from .base_provider import BaseAIProvider, AIResponse


class GeminiProvider(BaseAIProvider):
    """Gemini AI provider implementation (coming soon)."""

    GEMINI_MODELS = [
        "gemini-2.5-pro-latest",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash-latest"
    ]

    def __init__(self, api_key: str, model: str = "gemini-2.5-pro-latest", **kwargs):
        """Initialize Gemini provider."""
        super().__init__(api_key, model, **kwargs)
        if not self.model:
            self.model = "gemini-2.5-pro-latest"

    @property
    def name(self) -> str:
        return "Gemini (Google)"

    @property
    def supported_models(self) -> List[str]:
        return self.GEMINI_MODELS.copy()

    @property
    def supports_thinking_mode(self) -> bool:
        return False  # Gemini doesn't support thinking mode yet

    async def send_message(self, message: str, **kwargs) -> AIResponse:
        """Send message to Gemini (not yet implemented)."""
        raise NotImplementedError("Gemini provider implementation coming soon")

    async def test_connection(self) -> bool:
        """Test Gemini connection (not yet implemented)."""
        return False
