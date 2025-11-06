"""
Tests for the unified MCP server (mcp_server.py).

These tests verify the basic server functionality.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMCPServer:
    """Tests for the unified MCP server."""

    def test_server_import(self):
        """Test that the mcp_server module can be imported."""
        import mcp_server

        assert hasattr(mcp_server, "main")
        assert hasattr(mcp_server, "__version__")
        assert mcp_server.__version__ == "1.0.0"

    def test_version(self):
        """Test version information."""
        import mcp_server

        assert isinstance(mcp_server.__version__, str)
        assert len(mcp_server.__version__) > 0

    def test_load_config(self):
        """Test configuration loading."""
        import mcp_server

        # Test loading non-existent config returns defaults
        config = mcp_server.load_config("nonexistent.json")
        assert "server" in config
        assert "freecad" in config
        assert "tools" in config

    def test_get_default_config(self):
        """Test default configuration structure."""
        import mcp_server

        config = mcp_server.load_config(None)
        assert config["server"]["name"] == "mcp-freecad-server"
        assert config["server"]["version"] == "1.0.0"
        assert config["freecad"]["auto_connect"] is True
        assert config["tools"]["enable_primitives"] is True


class TestMCPServerIntegration:
    """Integration tests for MCP server (skipped if dependencies unavailable)."""

    def test_server_initialization_placeholder(self):
        """Placeholder test for server initialization."""
        # Would need FastMCP and FreeCAD modules to test actual initialization
        assert True
