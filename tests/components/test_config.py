"""
Tests for configuration management component.
"""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, mock_open

from src.mcp_freecad.server.components.config import (
    load_config,
    get_config,
    get_server_name,
    get_server_version,
    _merge_configs
)


class TestConfigManagement:
    """Test configuration loading and management."""

    def test_load_default_config(self):
        """Test loading default configuration when no file exists."""
        with patch('os.path.exists', return_value=False):
            config = load_config("nonexistent.json")
            
        assert config["server"]["name"] == "advanced-freecad-mcp-server"
        assert config["server"]["version"] == "0.7.11"
        assert config["freecad"]["host"] == "localhost"
        assert config["freecad"]["port"] == 12345

    def test_load_config_from_file(self):
        """Test loading configuration from file."""
        test_config = {
            "server": {"name": "test-server", "version": "1.0.0"},
            "freecad": {"host": "remote", "port": 54321}
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
                config = load_config("test.json")
        
        assert config["server"]["name"] == "test-server"
        assert config["freecad"]["host"] == "remote"
        # Should merge with defaults
        assert "auto_connect" in config["freecad"]

    def test_merge_configs(self):
        """Test configuration merging."""
        default = {"a": 1, "b": {"x": 1, "y": 2}}
        override = {"b": {"x": 10}, "c": 3}
        
        result = _merge_configs(default, override)
        
        assert result["a"] == 1
        assert result["b"]["x"] == 10
        assert result["b"]["y"] == 2
        assert result["c"] == 3

    def test_get_server_info(self):
        """Test server info getters."""
        test_config = {
            "server": {"name": "custom-server", "version": "2.0.0"}
        }
        
        with patch('src.mcp_freecad.server.components.config.CONFIG', test_config):
            assert get_server_name() == "custom-server"
            assert get_server_version() == "2.0.0"