"""
Events for FreeCAD AI addon.

This module contains event handlers for document changes, command execution, and error handling.
"""

# Import event handlers
try:
    from .base import EventHandler
    from .document_events import DocumentEventHandler
    from .command_events import CommandEventHandler
    from .error_events import ErrorEventHandler

    EVENTS_AVAILABLE = True

    __all__ = [
        'EventHandler',
        'DocumentEventHandler',
        'CommandEventHandler',
        'ErrorEventHandler',
        'EVENTS_AVAILABLE'
    ]

except ImportError as e:
    import FreeCAD
    FreeCAD.Console.PrintWarning(f"FreeCAD AI: Failed to import some event handlers: {e}\n")
    EVENTS_AVAILABLE = False
    __all__ = ['EVENTS_AVAILABLE']
