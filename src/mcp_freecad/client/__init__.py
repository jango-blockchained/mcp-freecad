"""
MCP-FreeCAD Client Tools

This package provides tools for connecting to and interacting with FreeCAD.
"""

from . import freecad_client, freecad_rpc_server

# Expose key modules
from .freecad_connection_manager import FreeCADConnection

__all__ = ["FreeCADClient", "FreeCADConnection"]
