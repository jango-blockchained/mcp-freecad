"""
Integration tests for MCP server components.
"""

import asyncio
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from src.mcp_freecad.server.components import (
    load_config,
    setup_logging,
    ToolContext
)


class TestServerIntegration:
    """Test integration between server components."""

    def test_config_and_logging_integration(self):
        """Test that configuration properly affects logging setup."""
        test_config = {
            "logging": {
                "level": "DEBUG",
                "port": 9999,
                "file": "test.log"
            }
        }
        
        with patch('os.makedirs'):
            with patch('logging.basicConfig') as mock_basic_config:
                setup_logging(test_config)
        
        # Verify logging was configured with correct level
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args
        assert call_args[1]['level'] == 10  # DEBUG level

    @pytest.mark.asyncio
    async def test_progress_tracking(self):
        """Test progress tracking functionality."""
        context = ToolContext.get()
        
        # Test progress without callback
        await context.send_progress(0.5, "Test message")
        
        # Test progress with callback
        progress_values = []
        
        async def mock_callback(progress, message):
            progress_values.append((progress, message))
        
        context.set_progress_callback(mock_callback)
        await context.send_progress(0.25, "Quarter done")
        await context.send_progress(1.0, "Complete")
        
        assert len(progress_values) == 2
        assert progress_values[0] == (0.25, "Quarter done")
        assert progress_values[1] == (1.0, "Complete")

    def test_configuration_file_parsing(self):
        """Test configuration file parsing edge cases."""
        # Test malformed JSON
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=json.JSONDecodeError("msg", "doc", 0)):
                config = load_config("bad.json")
        
        # Should fall back to defaults
        assert "server" in config
        assert config["server"]["name"] == "advanced-freecad-mcp-server"