"""
Configuration package for MCP FreeCAD Addon

This package handles configuration management for the addon,
including settings persistence, validation, and defaults.
"""

__version__ = "1.0.0"

# Import configuration classes
try:
    from .config_manager import ConfigManager

    __all__ = ["ConfigManager"]

except ImportError as e:
    print(f"Configuration components not fully available: {e}")
    __all__ = []

# Default configuration structure
DEFAULT_CONFIG = {
    "addon": {"version": "1.0.0", "debug": False, "auto_start": True},
    "connections": {"default_method": "launcher", "timeout": 30.0, "retry_attempts": 3},
    "ai_models": {"default_provider": "claude", "max_tokens": 4096, "temperature": 0.7},
    "ui": {"theme": "light", "dock_position": "right", "auto_hide": False},
    "logging": {"level": "INFO", "max_size": 10485760, "backup_count": 3},
}
