"""FreeCAD MCP Server package."""

# Remove the incorrect import
# from .freecad_mcp_server import MCPServer

# Import ToolContext instead, which is used by the test
from .freecad_mcp_server import ToolContext, mcp # Export mcp as well just in case

# Update __all__
__all__ = ["ToolContext", "mcp"]
