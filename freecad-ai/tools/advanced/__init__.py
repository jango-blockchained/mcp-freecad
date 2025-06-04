"""
Advanced tools for FreeCAD AI addon.

This module contains advanced CAD tools imported from the MCP FreeCAD project.
"""

# Import advanced tools
try:
    from .assembly import AssemblyToolProvider
    from .cam import CAMToolProvider
    from .rendering import RenderingToolProvider
    from .smithery import SmitheryToolProvider

    ADVANCED_TOOLS_AVAILABLE = True

    __all__ = [
        "AssemblyToolProvider",
        "CAMToolProvider",
        "RenderingToolProvider",
        "SmitheryToolProvider",
        "ADVANCED_TOOLS_AVAILABLE",
    ]

except ImportError as e:
    import FreeCAD

    FreeCAD.Console.PrintWarning(
        f"FreeCAD AI: Failed to import some advanced tools: {e}\n"
    )
    ADVANCED_TOOLS_AVAILABLE = False
    __all__ = ["ADVANCED_TOOLS_AVAILABLE"]
