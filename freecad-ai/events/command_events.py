import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set

try:
    from .base import EventProvider
except ImportError:
    # Fallback for when module is loaded by FreeCAD
    import os
    import sys

    addon_dir = os.path.dirname(os.path.dirname(__file__))
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)
    from events.base import EventProvider

logger = logging.getLogger(__name__)


class CommandExecutionEventProvider(EventProvider):
    """Event provider for FreeCAD command execution events."""

    def __init__(self, freecad_app=None, event_router=None):
        """
        Initialize the command execution event provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
            event_router: Router for broadcasting events
        """
        super().__init__()
        self.app = freecad_app
        self.event_router = event_router
        self.command_history: List[Dict[str, Any]] = []

        if self.app is None:
            try:
                import FreeCAD

                self.app = FreeCAD
                logger.info("Connected to FreeCAD")
            except ImportError:
                logger.warning(
                    "Could not import FreeCAD. Make sure it's installed and in your Python path."
                )
                self.app = None

        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up signal handlers for FreeCAD command events."""
        if self.app is None:
            logger.warning("FreeCAD not available, cannot set up signal handlers")
            return

        try:
            # Connect to command execution signals if available
            if hasattr(self.app, "Gui") and hasattr(self.app.Gui, "Command"):
                # Different FreeCAD versions might have different signal names
                if hasattr(self.app.Gui.Command, "CommandExecuted"):
                    self.app.Gui.Command.CommandExecuted.connect(
                        self._on_command_executed
                    )
                    logger.info("Connected to FreeCAD command executed signal")
                elif hasattr(self.app.Gui, "commandExecuted"):
                    self.app.Gui.commandExecuted.connect(self._on_command_executed)
                    logger.info("Connected to FreeCAD command executed signal")
        except Exception as e:
            logger.error(
                f"Error setting up FreeCAD command execution signal handlers: {e}"
            )

    def _on_command_executed(self, command_name):
        """Handle command executed event."""
        logger.info(f"Command executed: {command_name}")

        # Create event data
        event_data = {
            "type": "command_executed",
            "command": command_name,
            "timestamp": time.time(),
        }

        # Store in history (limit to last 100 commands)
        self.command_history.append(event_data)
        if len(self.command_history) > 100:
            self.command_history.pop(0)

        # Emit event
        asyncio.create_task(self.emit_event("command_executed", event_data))

    def get_command_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the command execution history.

        Args:
            limit: Optional limit on the number of history items to return

        Returns:
            List of command execution events
        """
        if limit and 0 < limit < len(self.command_history):
            return self.command_history[-limit:]
        return self.command_history

    async def emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Emit an event to all listeners.

        Args:
            event_type: The type of event
            event_data: The event data
        """
        if self.event_router is not None:
            await self.event_router.broadcast_event(event_type, event_data)
        else:
            logger.warning(f"No event router available to broadcast {event_type} event")
