"""
MCP-FreeCAD Client Tools

This package provides tools for connecting to and interacting with FreeCAD.
"""

# Expose key modules
from .freecad_connection_manager import FreeCADConnection
from . import freecad_client
from . import freecad_rpc_server

__all__ = ["FreeCADClient", "FreeCADConnection"]
