"""
MCP Tools Package

Contains implementations of MCP tools for FreeCAD operations including
primitives, operations, measurements, and export/import functionality.

Author: jango-blockchained
"""

from .primitives import PrimitivesTool
from .operations import OperationsTool
from .measurements import MeasurementsTool
from .export_import import ExportImportTool
from .advanced_primitives import AdvancedPrimitivesTool
from .advanced_operations import AdvancedOperationsTool
from .surface_modification import SurfaceModificationTool

__all__ = [
    "PrimitivesTool",
    "OperationsTool",
    "MeasurementsTool",
    "ExportImportTool",
    "AdvancedPrimitivesTool",
    "AdvancedOperationsTool",
    "SurfaceModificationTool",
]

# Tool registry for easy access
TOOL_REGISTRY = {
    "primitives": PrimitivesTool,
    "operations": OperationsTool,
    "measurements": MeasurementsTool,
    "export_import": ExportImportTool,
    "advanced_primitives": AdvancedPrimitivesTool,
    "advanced_operations": AdvancedOperationsTool,
    "surface_modification": SurfaceModificationTool,
}


def get_tool(tool_name):
    """Get a tool class by name."""
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    return TOOL_REGISTRY[tool_name]


def get_all_tools():
    """Get all available tools."""
    return list(TOOL_REGISTRY.keys())
