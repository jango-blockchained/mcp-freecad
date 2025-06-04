"""
MCP-FreeCAD Integration Module.

This module provides integration between FreeCAD and the Model Context Protocol (MCP).
"""

__version__ = "0.7.11"

# Import main components for easy access
from .client.freecad_connection_manager import FreeCADConnection
from .tools.primitives import PrimitiveToolProvider
from .tools.model_manipulation import ModelManipulationToolProvider
from .core.server import MCPServer

# Tool providers registry
TOOL_PROVIDERS = {
    "primitives": PrimitiveToolProvider,
    "model_manipulation": ModelManipulationToolProvider,
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
    "PrimitiveToolProvider",
    "ModelManipulationToolProvider",
    "MCPServer",
    "TOOL_PROVIDERS",
    "CONNECTION_TYPES",
]
