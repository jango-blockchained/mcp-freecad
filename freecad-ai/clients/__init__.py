"""
Clients for FreeCAD AI addon.

This module contains client implementations for FreeCAD and MCP bridge.
"""

# Import clients
try:
    from .freecad_client import FreeCADClient
    from .cursor_mcp_bridge import CursorMCPBridge

    CLIENTS_AVAILABLE = True

    __all__ = ["FreeCADClient", "CursorMCPBridge", "CLIENTS_AVAILABLE"]

except ImportError as e:
    import FreeCAD

    FreeCAD.Console.PrintWarning(f"FreeCAD AI: Failed to import some clients: {e}\n")
    CLIENTS_AVAILABLE = False
    __all__ = ["CLIENTS_AVAILABLE"]
