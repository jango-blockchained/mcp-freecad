"""
MCP-FreeCAD Integration Module.

This module provides integration between FreeCAD and the Model Context Protocol (MCP).
"""

__version__ = "0.7.11"

# Import core components that don't require heavy dependencies
from .client.freecad_connection_manager import FreeCADConnection


# Conditional imports for components with heavy dependencies
def get_primitive_tool_provider():
    """Lazy import for PrimitiveToolProvider."""
    from .tools.primitives import PrimitiveToolProvider

    return PrimitiveToolProvider


def get_model_manipulation_tool_provider():
    """Lazy import for ModelManipulationToolProvider."""
    from .tools.model_manipulation import ModelManipulationToolProvider

    return ModelManipulationToolProvider


def get_mcp_server():
    """Lazy import for MCPServer."""
    from .core.server import MCPServer

    return MCPServer


# Tool providers registry (lazy loading)
TOOL_PROVIDERS = {
    "primitives": get_primitive_tool_provider,
    "model_manipulation": get_model_manipulation_tool_provider,
}

# Connection types
CONNECTION_TYPES = {
    "server": "Socket-based connection to FreeCAD server",
    "bridge": "CLI-based connection using FreeCAD executable",
    "rpc": "XML-RPC connection to FreeCAD",
    "launcher": "AppImage launcher connection",
    "wrapper": "Subprocess wrapper connection",
}

__all__ = [
    "__version__",
    "FreeCADConnection",
    "get_primitive_tool_provider",
    "get_model_manipulation_tool_provider",
    "get_mcp_server",
    "TOOL_PROVIDERS",
    "CONNECTION_TYPES",
]
