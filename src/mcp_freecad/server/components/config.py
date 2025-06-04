"""
Configuration management for FreeCAD MCP Server.

Handles configuration loading, defaults, and global settings.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Global configuration
CONFIG: Dict[str, Any] = {}
CONFIG_PATH = "config.json"


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from file with fallback defaults."""
    global CONFIG

    if config_path is None:
        config_path = CONFIG_PATH

    # Default configuration
    default_config = {
        "server": {"name": "advanced-freecad-mcp-server", "version": "0.7.11"},
        "freecad": {
            "host": "localhost",
            "port": 12345,
            "freecad_path": "freecad",
            "auto_connect": True,
            "prefer_method": "bridge",
        },
        "logging": {
            "level": "INFO",
            "port": 9020,
            "file": "logs/freecad_mcp_server.log",
        },
    }

    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                file_config = json.load(f)
            # Merge file config with defaults
            CONFIG = _merge_configs(default_config, file_config)
            logger.info(f"Configuration loaded from {config_path}")
        else:
            CONFIG = default_config
            logger.info(f"Using default configuration (no file found at {config_path})")
    except Exception as e:
        logger.warning(f"Error loading config from {config_path}: {e}")
        CONFIG = default_config

    return CONFIG


def _merge_configs(default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge configuration dictionaries."""
    result = default.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    return result


def get_config() -> Dict[str, Any]:
    """Get current configuration."""
    return CONFIG


def get_server_name() -> str:
    """Get configured server name."""
    return CONFIG.get("server", {}).get("name", "advanced-freecad-mcp-server")


def get_server_version() -> str:
    """Get configured server version."""
    return CONFIG.get("server", {}).get("version", "0.7.11")
