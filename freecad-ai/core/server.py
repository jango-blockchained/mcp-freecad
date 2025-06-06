"""
Minimal MCP Server class for FreeCAD AI addon.
"""

import logging

logger = logging.getLogger(__name__)


class MCPServer:
    """Minimal MCP Server class for tool execution within FreeCAD addon."""

    def __init__(self):
        """Initialize the MCP server."""
        self.tools = {}
        logger.info("MCP Server initialized for FreeCAD addon")

    def register_tool(self, name: str, tool_provider):
        """Register a tool provider.

        Args:
            name: Name of the tool
            tool_provider: Tool provider instance
        """
        self.tools[name] = tool_provider
        logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str):
        """Get a tool provider by name.

        Args:
            name: Name of the tool

        Returns:
            Tool provider instance or None
        """
        return self.tools.get(name)
