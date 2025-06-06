"""
MCP Bridge - Integration adapter for existing MCP system

This module provides the bridge between the FreeCAD addon
and the existing MCP server and tools.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class MCPBridge:
    """Bridge adapter for integrating with existing MCP system."""

    def __init__(self, mcp_root_path: Optional[str] = None):
        """Initialize the MCP bridge."""
        self.logger = logging.getLogger(__name__)

        # Determine MCP root path
        if mcp_root_path:
            self.mcp_root = Path(mcp_root_path)
        else:
            # Auto-detect MCP root (addon is in freecad-ai/ subdirectory)
            addon_dir = Path(__file__).parent.parent  # freecad-ai/
            self.mcp_root = addon_dir.parent  # mcp-freecad/

        # Add MCP source to Python path
        mcp_src = self.mcp_root / "src"
        if mcp_src.exists() and str(mcp_src) not in sys.path:
            sys.path.insert(0, str(mcp_src))

        # Import existing MCP components
        self._import_mcp_components()

        # Configuration bridge
        self.config_bridge = None
        self._setup_config_bridge()

    def _import_mcp_components(self):
        """Import existing MCP components."""
        try:
            # Import existing MCP tools
            from mcp_freecad.server import freecad_mcp_server
            from mcp_freecad.tools import (
                export_import,
                measurement,
                model_manipulation,
                primitives,
            )

            self.mcp_tools = {
                "primitives": primitives,
                "model_manipulation": model_manipulation,
                "export_import": export_import,
                "measurement": measurement,
            }

            self.mcp_server = freecad_mcp_server

            self.logger.info("Successfully imported existing MCP components")

        except ImportError as e:
            self.logger.warning(f"Could not import existing MCP components: {e}")
            self.mcp_tools = {}
            self.mcp_server = None

    def _setup_config_bridge(self):
        """Setup configuration bridge with existing system."""
        config_file = self.mcp_root / "config.json"
        if config_file.exists():
            try:
                import json

                with open(config_file, "r") as f:
                    self.config_bridge = json.load(f)
                self.logger.info("Loaded existing MCP configuration")
            except Exception as e:
                self.logger.error(f"Error loading MCP config: {e}")
                self.config_bridge = {}
        else:
            self.config_bridge = {}

    def get_existing_tools(self) -> Dict[str, Any]:
        """Get existing MCP tools."""
        return self.mcp_tools.copy()

    def get_connection_config(self) -> Dict[str, Any]:
        """Get connection configuration from existing system."""
        if self.config_bridge and "freecad" in self.config_bridge:
            return self.config_bridge["freecad"]
        return {}

    def execute_mcp_tool(
        self, tool_category: str, tool_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an existing MCP tool."""
        if tool_category not in self.mcp_tools:
            return {"error": f"Tool category '{tool_category}' not found"}

        tool_module = self.mcp_tools[tool_category]

        try:
            # This is a simplified interface - actual implementation
            # would depend on the specific tool API
            if hasattr(tool_module, tool_name):
                tool_func = getattr(tool_module, tool_name)
                result = tool_func(**params)
                return {"success": True, "result": result}
            else:
                return {"error": f"Tool '{tool_name}' not found in '{tool_category}'"}
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_category}.{tool_name}: {e}")
            return {"error": str(e)}
