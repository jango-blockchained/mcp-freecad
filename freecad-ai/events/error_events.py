import logging
import sys
import time
import traceback
from typing import Any, Dict, List, Optional

try:
    from .base import EventProvider
    from .import_utils import safe_import_freecad_util

    freecad_safe_emit = safe_import_freecad_util("freecad_safe_emit")
except ImportError:
    # Fallback for when module is loaded by FreeCAD
    import os

    addon_dir = os.path.dirname(os.path.dirname(__file__))
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)
    from events.base import EventProvider
    from events.import_utils import safe_import_freecad_util

    freecad_safe_emit = safe_import_freecad_util("freecad_safe_emit")

logger = logging.getLogger(__name__)


class ErrorEventProvider(EventProvider):
    """Event provider for FreeCAD error events."""

    def __init__(
        self,
        freecad_app=None,
        event_router=None,
        max_history_size=50,
        install_global_handler=False,
    ):
        """
        Initialize the error event provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
            event_router: Router for broadcasting events
            max_history_size: Maximum number of errors to keep in history
            install_global_handler: Whether to install global exception handler (dangerous, default False)
        """
        super().__init__(max_history_size)
        self.app = freecad_app
        self.event_router = event_router
        self.error_history: List[Dict[str, Any]] = []
        self.original_excepthook = None
        self._global_handler_installed = False

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

        # Only install global exception handler if explicitly requested
        if install_global_handler:
            self._install_global_exception_handler()

        self._setup_signal_handlers()

    def _install_global_exception_handler(self):
        """Install global exception handler if not already installed."""
        if not self._global_handler_installed and hasattr(sys, "excepthook"):
            self.original_excepthook = sys.excepthook
            sys.excepthook = self._global_exception_handler
            self._global_handler_installed = True
            logger.info("Installed global exception handler for error tracking")

    def _uninstall_global_exception_handler(self):
        """Restore original exception handler."""
        if self._global_handler_installed and self.original_excepthook:
            sys.excepthook = self.original_excepthook
            self._global_handler_installed = False
            logger.info("Restored original exception handler")

    def _setup_signal_handlers(self):
        """Set up signal handlers for FreeCAD error events."""
        if self.app is None:
            logger.warning("FreeCAD not available, cannot set up signal handlers")
            return

        try:
            # Connect to error signals if available
            if hasattr(self.app, "signalError"):
                self.app.signalError.connect(self._on_error)
                logger.info("Connected to FreeCAD error signal")

            # Try to connect to the Console observer for Python errors
            if hasattr(self.app, "Gui") and hasattr(self.app.Gui, "getMainWindow"):
                try:
                    # Some FreeCAD versions provide a console viewer with error signals
                    console = self.app.Gui.getMainWindow().findChild(
                        "QTextEdit", "Report view"
                    )
                    if console and hasattr(console, "signalError"):
                        console.signalError.connect(self._on_error)
                        logger.info("Connected to FreeCAD console error signal")
                except Exception as console_error:
                    logger.debug(
                        f"Could not connect to console error signal: {console_error}"
                    )
        except Exception as e:
            logger.error(f"Error setting up FreeCAD error signal handlers: {e}")

    def _on_error(self, error_msg):
        """Handle error event from FreeCAD signals."""
        logger.error(f"FreeCAD error: {error_msg}")

        # Create event data
        event_data = {
            "type": "error",
            "message": error_msg,
            "timestamp": time.time(),
            "source": "freecad_signal",
        }

        # Record the error
        self._record_error(event_data)

    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """Handle unhandled exceptions globally."""
        # Still call the original handler
        self.original_excepthook(exc_type, exc_value, exc_traceback)

        # Format the exception
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        # Create event data
        event_data = {
            "type": "error",
            "message": str(exc_value),
            "traceback": tb_str,
            "timestamp": time.time(),
            "source": "unhandled_exception",
            "exception_type": exc_type.__name__,
        }

        # Record the error
        self._record_error(event_data)

    def _record_error(self, event_data):
        """Record an error and emit an event."""
        # Store in history (limit to configured max size)
        self.error_history.append(event_data)
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)

        # Emit event safely
        if freecad_safe_emit:
            freecad_safe_emit(self.emit_event, "error", event_data, "error_recorded")

    def get_error_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the error history.

        Args:
            limit: Optional limit on the number of history items to return

        Returns:
            List of error events
        """
        if limit and 0 < limit < len(self.error_history):
            return self.error_history[-limit:]
        return self.error_history

    def report_error(
        self,
        error_message: str,
        error_type: str = "manual",
        details: Dict[str, Any] = None,
    ):
        """
        Manually report an error.

        Args:
            error_message: Error message
            error_type: Type of error
            details: Additional error details
        """
        error_data = {
            "type": "error",
            "message": error_message,
            "error_type": error_type,
            "timestamp": time.time(),
            "source": "manual_report",
        }

        if details:
            error_data.update(details)

        self._record_error(error_data)

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the error event provider."""
        return {
            "freecad_available": self.app is not None,
            "global_handler_installed": self._global_handler_installed,
            "signals_connected": len(self._signal_connections),
            "error_history_size": len(self.error_history),
            "max_history_size": self.max_history_size,
            "is_shutdown": self._is_shutdown,
        }

    async def shutdown(self) -> None:
        """Clean up resources when the provider is shutdown."""
        # Restore original exception handler first
        self._uninstall_global_exception_handler()

        # Then call parent shutdown
        await super().shutdown()

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
