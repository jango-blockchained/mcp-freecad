"""
AI Providers Package

Provides AI provider implementations with lazy loading and dependency management.
"""

import FreeCAD
from typing import Dict, Any, Optional

# Import base classes first
from .base_provider import BaseAIProvider, AIResponse, AIMessage, MessageRole

# Lazy loading for providers to handle missing dependencies gracefully
_providers = {}
_provider_errors = {}


def _lazy_import_provider(provider_name: str, module_name: str, class_name: str):
    """Lazy import a provider with error handling."""
    if provider_name in _providers:
        return _providers[provider_name]

    if provider_name in _provider_errors:
        # Don't retry if we already failed
        return None

    try:
        module = __import__(f"ai.providers.{module_name}", fromlist=[class_name])
        provider_class = getattr(module, class_name)
        _providers[provider_name] = provider_class
        return provider_class
    except ImportError as e:
        error_msg = f"Failed to import {provider_name}: {str(e)}"
        _provider_errors[provider_name] = error_msg
        FreeCAD.Console.PrintWarning(f"MCP Integration: {error_msg}\n")

        # Check if it's a missing dependency issue
        if 'aiohttp' in str(e):
            FreeCAD.Console.PrintMessage(
                "MCP Integration: Missing 'aiohttp' dependency. "
                "Use the Dependencies tab in the MCP Integration interface to install it.\n"
            )
        return None
    except Exception as e:
        error_msg = f"Error loading {provider_name}: {str(e)}"
        _provider_errors[provider_name] = error_msg
        FreeCAD.Console.PrintError(f"MCP Integration: {error_msg}\n")
        return None


def get_claude_provider():
    """Get Claude provider class with lazy loading."""
    return _lazy_import_provider("Claude", "claude_provider", "ClaudeProvider")


def get_gemini_provider():
    """Get Gemini provider class with lazy loading."""
    return _lazy_import_provider("Gemini", "gemini_provider", "GeminiProvider")


def get_openrouter_provider():
    """Get OpenRouter provider class with lazy loading."""
    return _lazy_import_provider("OpenRouter", "openrouter_provider", "OpenRouterProvider")


def get_available_providers() -> Dict[str, Any]:
    """Get all available provider classes.

    Returns:
        Dictionary mapping provider names to classes (None if unavailable)
    """
    return {
        "Claude": get_claude_provider(),
        "Gemini": get_gemini_provider(),
        "OpenRouter": get_openrouter_provider()
    }


def get_provider_errors() -> Dict[str, str]:
    """Get any provider loading errors.

    Returns:
        Dictionary mapping provider names to error messages
    """
    return _provider_errors.copy()


def check_dependencies() -> Dict[str, bool]:
    """Check if dependencies are available for providers.

    Returns:
        Dictionary mapping dependency names to availability
    """
    try:
        from ..utils.dependency_manager import check_dependencies
        return check_dependencies()
    except ImportError:
        # Fallback manual check
        dependencies = {}
        try:
            import aiohttp
            dependencies['aiohttp'] = True
        except ImportError:
            dependencies['aiohttp'] = False

        try:
            import requests
            dependencies['requests'] = True
        except ImportError:
            dependencies['requests'] = False

        return dependencies


# For backward compatibility, try to import providers directly
# but don't fail if dependencies are missing
ClaudeProvider = get_claude_provider()
GeminiProvider = get_gemini_provider()
OpenRouterProvider = get_openrouter_provider()

# Export list for explicit imports
__all__ = [
    "BaseAIProvider",
    "AIResponse",
    "AIMessage",
    "MessageRole",
    "get_claude_provider",
    "get_gemini_provider",
    "get_openrouter_provider",
    "get_available_providers",
    "get_provider_errors",
    "check_dependencies"
]

# Add provider classes if they loaded successfully
if ClaudeProvider:
    __all__.append("ClaudeProvider")
if GeminiProvider:
    __all__.append("GeminiProvider")
if OpenRouterProvider:
    __all__.append("OpenRouterProvider")
