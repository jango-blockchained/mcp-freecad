"""
Advanced tools for FreeCAD AI addon.

This module contains advanced CAD tools imported from the MCP FreeCAD project.
"""

# Import advanced tools
ADVANCED_TOOLS_AVAILABLE = False
available_tools = []

# Try importing each tool individually to be more robust
tools_to_import = [
    ("assembly", "AssemblyToolProvider"),
    ("cam", "CAMToolProvider"),
    ("rendering", "RenderingToolProvider"),
    ("smithery", "SmitheryToolProvider")
]

for module_name, class_name in tools_to_import:
    try:
        module = __import__(f"tools.advanced.{module_name}", fromlist=[class_name])
        globals()[class_name] = getattr(module, class_name)
        available_tools.append(class_name)
    except ImportError as e:
        try:
            import FreeCAD
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Failed to import {class_name}: {e}\n"
            )
        except ImportError:
            print(f"FreeCAD AI: Failed to import {class_name}: {e}")

if available_tools:
    ADVANCED_TOOLS_AVAILABLE = True

__all__ = available_tools + ["ADVANCED_TOOLS_AVAILABLE"]
