"""
MCP Tools Package

Contains implementations of MCP tools for FreeCAD operations including
primitives, operations, measurements, and export/import functionality.

Author: jango-blockchained
"""

# Try importing tools individually to handle missing dependencies
TOOLS_AVAILABLE = False
available_tools = {}

tools_to_import = [
    ("primitives", "PrimitivesTool"),
    ("operations", "OperationsTool"),
    ("measurements", "MeasurementsTool"),
    ("export_import", "ExportImportTool"),
    ("advanced_primitives", "AdvancedPrimitivesTool"),
    ("advanced_operations", "AdvancedOperationsTool"),
    ("surface_modification", "SurfaceModificationTool"),
]

for module_name, class_name in tools_to_import:
    try:
        module = __import__(f"tools.{module_name}", fromlist=[class_name])
        tool_class = getattr(module, class_name)
        globals()[class_name] = tool_class
        available_tools[module_name] = tool_class
    except ImportError as e:
        try:
            import FreeCAD

            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Failed to import {class_name}: {e}\n"
            )
        except ImportError:
            print(f"FreeCAD AI: Failed to import {class_name}: {e}")

if available_tools:
    TOOLS_AVAILABLE = True

__all__ = list(available_tools.keys()) + ["TOOLS_AVAILABLE", "TOOL_REGISTRY"]

# Tool registry for easy access - only include successfully imported tools
TOOL_REGISTRY = available_tools.copy()


def get_tool(tool_name):
    """Get a tool class by name."""
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    return TOOL_REGISTRY[tool_name]


def get_all_tools():
    """Get all available tools."""
    return list(TOOL_REGISTRY.keys())
