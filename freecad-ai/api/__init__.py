"""
API for FreeCAD AI addon.

This module contains API handlers for tools, resources, and events.
"""

# Import API handlers
API_AVAILABLE = False
available_apis = []

# Try importing each API individually to be more robust
apis_to_import = [
    ("tools", "create_tool_router"),  # Use the function name instead
    ("resources", "ResourcesAPI"),
    ("events", "EventsAPI")
]

for module_name, item_name in apis_to_import:
    try:
        module = __import__(f"api.{module_name}", fromlist=[item_name])
        if hasattr(module, item_name):
            globals()[item_name] = getattr(module, item_name)
            available_apis.append(item_name)
    except ImportError as e:
        try:
            import FreeCAD
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Failed to import {item_name}: {e}\n"
            )
        except ImportError:
            print(f"FreeCAD AI: Failed to import {item_name}: {e}")

if available_apis:
    API_AVAILABLE = True

__all__ = available_apis + ["API_AVAILABLE"]
