"""
Events for FreeCAD AI addon.

This module contains event handlers for document changes, command execution, and error handling.
"""

# Import event handlers
EVENTS_AVAILABLE = False
available_handlers = []

# Try importing each handler individually to be more robust
handlers_to_import = [
    ("base", "EventHandler"),
    ("document_events", "DocumentEventHandler"),
    ("command_events", "CommandEventHandler"),
    ("error_events", "ErrorEventHandler")
]

for module_name, class_name in handlers_to_import:
    try:
        if module_name == "base":
            from .base import EventHandler
            available_handlers.append("EventHandler")
        elif module_name == "document_events":
            from .document_events import DocumentEventProvider as DocumentEventHandler
            globals()["DocumentEventHandler"] = DocumentEventHandler
            available_handlers.append("DocumentEventHandler")
        elif module_name == "command_events":
            from .command_events import CommandExecutionEventProvider as CommandEventHandler
            globals()["CommandEventHandler"] = CommandEventHandler
            available_handlers.append("CommandEventHandler")
        elif module_name == "error_events":
            from .error_events import ErrorEventProvider as ErrorEventHandler
            globals()["ErrorEventHandler"] = ErrorEventHandler
            available_handlers.append("ErrorEventHandler")
    except ImportError as e:
        try:
            import FreeCAD
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Failed to import {class_name}: {e}\n"
            )
        except ImportError:
            print(f"FreeCAD AI: Failed to import {class_name}: {e}")

if available_handlers:
    EVENTS_AVAILABLE = True

__all__ = available_handlers + ["EVENTS_AVAILABLE"]
