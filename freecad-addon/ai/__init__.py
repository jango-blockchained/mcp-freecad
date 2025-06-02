"""
AI Integration package for MCP FreeCAD Addon

This package provides AI model integration capabilities including
support for Claude, Gemini, and OpenRouter APIs.
"""

__version__ = "1.0.0"

# Import main AI provider classes
try:
    from .base_provider import AIProvider
    from .claude_provider import ClaudeProvider
    from .gemini_provider import GeminiProvider
    from .openrouter_provider import OpenRouterProvider
    from .ai_manager import AIManager
    
    __all__ = [
        'AIProvider',
        'ClaudeProvider',
        'GeminiProvider', 
        'OpenRouterProvider',
        'AIManager'
    ]
    
except ImportError as e:
    print(f"AI components not fully available: {e}")
    __all__ = []

# Supported AI models
CLAUDE_MODELS = [
    "claude-3-5-sonnet-20241022",
    "claude-3-opus-20240229", 
    "claude-3-haiku-20240307"
]

GEMINI_MODELS = [
    "gemini-1.5-pro-latest",
    "gemini-1.5-flash-latest",
    "gemini-exp-1114"
]

# Configuration defaults
DEFAULT_CONFIG = {
    "max_tokens": 4096,
    "temperature": 0.7,
    "timeout": 30.0,
    "retry_attempts": 3
}