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
    ("event_router", "EventRouter"),
    ("event_manager", "EventManager"),
    ("mcp_integration", "MCPEventIntegration"),
    ("document_events", "DocumentEventHandler"),
    ("command_events", "CommandEventHandler"),
    ("error_events", "ErrorEventHandler"),
]

for module_name, class_name in handlers_to_import:
    try:
        if module_name == "base":
            from .base import EventHandler

            globals()["EventHandler"] = EventHandler
            available_handlers.append("EventHandler")
        elif module_name == "event_router":
            from .event_router import EventRouter

            globals()["EventRouter"] = EventRouter
            available_handlers.append("EventRouter")
        elif module_name == "event_manager":
            from .event_manager import EventManager

            globals()["EventManager"] = EventManager
            available_handlers.append("EventManager")
        elif module_name == "mcp_integration":
            from .mcp_integration import MCPEventIntegration

            globals()["MCPEventIntegration"] = MCPEventIntegration
            available_handlers.append("MCPEventIntegration")
        elif module_name == "document_events":
            from .document_events import DocumentEventProvider as DocumentEventHandler

            globals()["DocumentEventHandler"] = DocumentEventHandler
            available_handlers.append("DocumentEventHandler")
        elif module_name == "command_events":
            from .command_events import (
                CommandExecutionEventProvider as CommandEventHandler,
            )

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


# Convenience functions for setting up the events system
def create_event_system(
    freecad_app=None,
    max_history_size=1000,
    max_error_history=50,
    max_command_history=100,
):
    """
    Create and initialize a complete events system.

    Args:
        freecad_app: Optional FreeCAD application instance
        max_history_size: Maximum size for event router history
        max_error_history: Maximum size for error history
        max_command_history: Maximum size for command history

    Returns:
        Tuple of (EventManager, MCPEventIntegration) or (None, None) if failed
    """
    if not EVENTS_AVAILABLE:
        try:
            import FreeCAD

            FreeCAD.Console.PrintWarning("FreeCAD AI: Events system not available\n")
        except ImportError:
            print("FreeCAD AI: Events system not available")
        return None, None

    try:
        # Create event manager with configurable history sizes
        event_manager = EventManager(
            freecad_app,
            max_history_size=max_history_size,
            max_error_history=max_error_history,
            max_command_history=max_command_history,
        )

        # Create MCP integration
        mcp_integration = MCPEventIntegration(event_manager)

        return event_manager, mcp_integration

    except Exception as e:
        try:
            import FreeCAD

            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Failed to create events system: {e}\n"
            )
        except ImportError:
            print(f"FreeCAD AI: Failed to create events system: {e}")
        return None, None


async def initialize_event_system(
    freecad_app=None,
    max_history_size=1000,
    max_error_history=50,
    max_command_history=100,
):
    """
    Create and initialize a complete events system asynchronously.

    Args:
        freecad_app: Optional FreeCAD application instance
        max_history_size: Maximum size for event router history
        max_error_history: Maximum size for error history
        max_command_history: Maximum size for command history

    Returns:
        Tuple of (EventManager, MCPEventIntegration) or (None, None) if failed
    """
    event_manager, mcp_integration = create_event_system(
        freecad_app, max_history_size, max_error_history, max_command_history
    )

    if event_manager is None:
        return None, None

    # Initialize the event manager
    success = await event_manager.initialize()

    if not success:
        try:
            import FreeCAD

            FreeCAD.Console.PrintError(
                "FreeCAD AI: Failed to initialize events system\n"
            )
        except ImportError:
            print("FreeCAD AI: Failed to initialize events system")
        return None, None

    return event_manager, mcp_integration
