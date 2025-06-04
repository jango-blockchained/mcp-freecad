"""
API for FreeCAD AI addon.

This module contains API handlers for tools, resources, and events.
"""

# Import API handlers
try:
    from .tools import ToolsAPI
    from .resources import ResourcesAPI
    from .events import EventsAPI

    API_AVAILABLE = True

    __all__ = [
        'ToolsAPI',
        'ResourcesAPI',
        'EventsAPI',
        'API_AVAILABLE'
    ]

except ImportError as e:
    import FreeCAD
    FreeCAD.Console.PrintWarning(f"FreeCAD AI: Failed to import some API handlers: {e}\n")
    API_AVAILABLE = False
    __all__ = ['API_AVAILABLE']
