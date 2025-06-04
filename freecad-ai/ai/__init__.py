"""
AI Integration Package for MCP FreeCAD Addon

This package provides AI provider integrations for Claude, Gemini, OpenRouter, and others.
Supports advanced features like thinking mode and multi-model selection.

Author: jango-blockchained
License: MIT
"""

__version__ = "1.0.0"
__author__ = "jango-blockchained"

from .providers.base_provider import BaseAIProvider
from .providers.claude_provider import ClaudeProvider
from .providers.gemini_provider import GeminiProvider
from .providers.openrouter_provider import OpenRouterProvider

__all__ = ["BaseAIProvider", "ClaudeProvider", "GeminiProvider", "OpenRouterProvider"]

# Available provider types
AVAILABLE_PROVIDERS = {
    "claude": ClaudeProvider,
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider,
}


def get_provider(provider_type, **kwargs):
    """Factory function to create AI providers."""
    if provider_type not in AVAILABLE_PROVIDERS:
        raise ValueError(f"Unknown provider type: {provider_type}")

    return AVAILABLE_PROVIDERS[provider_type](**kwargs)


# Supported AI models
CLAUDE_MODELS = [
    "claude-3-5-sonnet-20241022",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307",
]

GEMINI_MODELS = ["gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-exp-1114"]

# Configuration defaults
DEFAULT_CONFIG = {
    "max_tokens": 4096,
    "temperature": 0.7,
    "timeout": 30.0,
    "retry_attempts": 3,
}
