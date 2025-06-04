"""OpenRouter Provider - OpenRouter API integration"""

import aiohttp
import json
from typing import Dict, List, Any, Optional
from .base_provider import AIProvider


class OpenRouterProvider(AIProvider):
    """Provider for OpenRouter AI models."""

    # Latest high-performance models available through OpenRouter (June 2025)
    AVAILABLE_MODELS = [
        "anthropic/claude-4-opus-20250522",  # Latest Claude 4 Opus
        "anthropic/claude-4-sonnet-20250522",  # Latest Claude 4 Sonnet
        "anthropic/claude-3-7-sonnet-20250224",  # Claude 3.7 Sonnet with thinking
        "anthropic/claude-3-5-sonnet-20241022",  # Claude 3.5 Sonnet
        "google/gemini-2.5-pro-latest",  # Latest Gemini 2.5 Pro
        "openai/gpt-4.1",  # GPT-4.1 with 1M context
        "openai/o3-mini",  # OpenAI o3 reasoning model
        "openai/gpt-4-turbo",  # GPT-4 Turbo
        "anthropic/claude-3-opus-20240229",  # Claude 3 Opus
        "google/gemini-1.5-pro-latest",  # Gemini 1.5 Pro
        "meta-llama/llama-3.1-70b-instruct",  # Meta Llama 3.1
        "mistralai/mixtral-8x7b-instruct",  # Mistral Mixtral
        "google/gemini-1.5-flash-latest",  # Fast Gemini Flash
    ]

    API_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenRouter provider."""
        super().__init__(api_key, config)
        self.config.setdefault("model", self.AVAILABLE_MODELS[0])
        self.config.setdefault("max_tokens", 4096)
        self.config.setdefault("temperature", 0.7)
        # Thinking mode support for Claude models
        self.config.setdefault("thinking_mode", False)
        self.config.setdefault("thinking_budget", None)

    async def send_message(self, message: str, context: Optional[Dict] = None) -> str:
        """Send message to OpenRouter API."""
        if not self._session:
            self._session = aiohttp.ClientSession()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/jango-blockchained/mcp-freecad",
            "X-Title": "MCP FreeCAD Integration",
        }

        payload = {
            "model": self.config["model"],
            "messages": [{"role": "user", "content": message}],
            "max_tokens": self.config["max_tokens"],
            "temperature": self.config["temperature"],
        }

        # Add thinking mode for Claude models if supported
        if self._supports_thinking_mode() and self.config.get("thinking_mode"):
            payload["thinking"] = {}
            if self.config.get("thinking_budget"):
                payload["thinking"]["max_tokens"] = self.config["thinking_budget"]

        try:
            async with self._session.post(
                f"{self.API_BASE_URL}/chat/completions", headers=headers, json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]

                    # Handle thinking mode response for Claude models
                    if "thinking" in data and data["thinking"]:
                        thinking_content = data["thinking"].get("content", "")
                        if thinking_content:
                            content = f"**Thinking Process:**\n{thinking_content}\n\n**Response:**\n{content}"

                    return content
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"OpenRouter API error: {response.status} - {error_text}"
                    )
                    return f"Error: {response.status}"
        except Exception as e:
            self.logger.error(f"OpenRouter API exception: {e}")
            return f"Error: {str(e)}"

    def _supports_thinking_mode(self) -> bool:
        """Check if current model supports thinking mode."""
        thinking_models = [
            "anthropic/claude-4-opus-20250522",
            "anthropic/claude-4-sonnet-20250522",
            "anthropic/claude-3-7-sonnet-20250224",
        ]
        return self.config["model"] in thinking_models

    def enable_thinking_mode(self, budget: Optional[int] = None):
        """Enable thinking mode for compatible models."""
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
        """Get available OpenRouter models."""
        return self.AVAILABLE_MODELS.copy()

    def validate_api_key(self) -> bool:
        """Validate OpenRouter API key."""
        return bool(self.api_key and self.api_key.startswith("sk-"))

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "OpenRouter"

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model."""
        model = self.config["model"]
        info = {
            "model": model,
            "supports_thinking": self._supports_thinking_mode(),
            "thinking_enabled": self.config.get("thinking_mode", False),
            "thinking_budget": self.config.get("thinking_budget"),
            "provider": "OpenRouter",
        }

        # Add model-specific info
        if "claude-4-opus" in model:
            info.update(
                {
                    "tier": "Premium",
                    "description": "Claude 4 Opus via OpenRouter - most capable",
                    "best_for": "Complex analysis, research, advanced coding",
                }
            )
        elif "claude-4-sonnet" in model:
            info.update(
                {
                    "tier": "Balanced",
                    "description": "Claude 4 Sonnet via OpenRouter - high performance",
                    "best_for": "Software development, technical writing",
                }
            )
        elif "claude-3-7-sonnet" in model:
            info.update(
                {
                    "tier": "Hybrid",
                    "description": "Claude 3.7 Sonnet via OpenRouter - hybrid reasoning",
                    "best_for": "Complex reasoning, step-by-step analysis",
                }
            )
        elif "gemini-2.5-pro" in model:
            info.update(
                {
                    "tier": "Advanced",
                    "description": "Latest Gemini 2.5 Pro via OpenRouter",
                    "best_for": "Multimodal tasks, large context analysis",
                }
            )
        elif "gpt-4.1" in model:
            info.update(
                {
                    "tier": "Advanced",
                    "description": "GPT-4.1 via OpenRouter - 1M context",
                    "best_for": "Large document analysis, complex tasks",
                }
            )
        elif "o3-mini" in model:
            info.update(
                {
                    "tier": "Reasoning",
                    "description": "OpenAI o3-mini via OpenRouter - reasoning specialist",
                    "best_for": "Mathematical reasoning, logical problems",
                }
            )

        return info
