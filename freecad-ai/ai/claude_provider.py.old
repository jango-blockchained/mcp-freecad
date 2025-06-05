"""
Claude Provider - Anthropic Claude API integration

This module provides integration with Anthropic's Claude API for
AI-powered CAD operations with support for latest models and thinking modes.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from .base_provider import AIProvider


class ClaudeProvider(AIProvider):
    """Provider for Anthropic Claude AI models."""

    # Latest Claude models (as of June 2025)
    AVAILABLE_MODELS = [
        "claude-4-opus-20250522",  # Latest Claude 4 Opus - most capable
        "claude-4-sonnet-20250522",  # Latest Claude 4 Sonnet - balanced performance
        "claude-3-7-sonnet-20250224",  # Claude 3.7 Sonnet - hybrid reasoning
        "claude-3-5-sonnet-20241022",  # Claude 3.5 Sonnet - reliable baseline
        "claude-3-opus-20240229",  # Claude 3 Opus - complex reasoning
        "claude-3-haiku-20240307",  # Claude 3 Haiku - fast and efficient
    ]

    API_BASE_URL = "https://api.anthropic.com/v1"

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize Claude provider."""
        super().__init__(api_key, config)
        self.config.setdefault("model", self.AVAILABLE_MODELS[0])
        self.config.setdefault("max_tokens", 4096)
        self.config.setdefault("temperature", 0.7)
        # Thinking mode configuration
        self.config.setdefault("thinking_mode", False)
        self.config.setdefault("thinking_budget", None)  # None = no limit

    async def send_message(self, message: str, context: Optional[Dict] = None) -> str:
        """Send message to Claude API with thinking mode support."""
        if not self._session:
            self._session = aiohttp.ClientSession()

        headers = {
            "x-api-key": self.api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.config["model"],
            "max_tokens": self.config["max_tokens"],
            "temperature": self.config["temperature"],
            "messages": [{"role": "user", "content": message}],
        }

        # Add thinking mode support for compatible models
        if self._supports_thinking_mode() and self.config.get("thinking_mode"):
            payload["thinking"] = {}
            if self.config.get("thinking_budget"):
                payload["thinking"]["max_tokens"] = self.config["thinking_budget"]

        try:
            async with self._session.post(
                f"{self.API_BASE_URL}/messages", headers=headers, json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["content"][0]["text"]

                    # Handle thinking mode response
                    if "thinking" in data and data["thinking"]:
                        thinking_content = data["thinking"].get("content", "")
                        if thinking_content:
                            content = f"**Thinking Process:**\n{thinking_content}\n\n**Response:**\n{content}"

                    return content
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"Claude API error: {response.status} - {error_text}"
                    )
                    return f"Error: {response.status}"
        except Exception as e:
            self.logger.error(f"Claude API exception: {e}")
            return f"Error: {str(e)}"

    def _supports_thinking_mode(self) -> bool:
        """Check if current model supports thinking mode."""
        thinking_models = [
            "claude-4-opus-20250522",
            "claude-4-sonnet-20250522",
            "claude-3-7-sonnet-20250224",
        ]
        return self.config["model"] in thinking_models

    def enable_thinking_mode(self, budget: Optional[int] = None):
        """Enable thinking mode with optional token budget."""
        if self._supports_thinking_mode():
            self.config["thinking_mode"] = True
            if budget:
                self.config["thinking_budget"] = budget
            return True
        return False

    def disable_thinking_mode(self):
        """Disable thinking mode."""
        self.config["thinking_mode"] = False
        self.config["thinking_budget"] = None

    def get_available_models(self) -> List[str]:
        """Get available Claude models."""
        return self.AVAILABLE_MODELS.copy()

    def validate_api_key(self) -> bool:
        """Validate Claude API key."""
        return bool(self.api_key and self.api_key.startswith("sk-"))

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Claude"

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model."""
        model = self.config["model"]
        info = {
            "model": model,
            "supports_thinking": self._supports_thinking_mode(),
            "thinking_enabled": self.config.get("thinking_mode", False),
            "thinking_budget": self.config.get("thinking_budget"),
        }

        # Add model-specific info
        if "claude-4-opus" in model:
            info.update(
                {
                    "tier": "Premium",
                    "description": "Most capable Claude model with advanced reasoning",
                    "best_for": "Complex analysis, research, advanced coding",
                }
            )
        elif "claude-4-sonnet" in model:
            info.update(
                {
                    "tier": "Balanced",
                    "description": "High performance with excellent coding capabilities",
                    "best_for": "Software development, technical writing, problem solving",
                }
            )
        elif "claude-3-7-sonnet" in model:
            info.update(
                {
                    "tier": "Hybrid",
                    "description": "First hybrid reasoning model with extended thinking",
                    "best_for": "Complex reasoning, step-by-step analysis",
                }
            )
        elif "claude-3-5-sonnet" in model:
            info.update(
                {
                    "tier": "Standard",
                    "description": "Reliable and capable for most tasks",
                    "best_for": "General purpose, balanced performance",
                }
            )

        return info
