import asyncio
import logging
import time
from typing import Any, Dict

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


class DocumentEventProvider(EventProvider):
    """Event provider for FreeCAD document events."""

    def __init__(self, freecad_app=None, event_router=None):
        """
        Initialize the document event provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
            event_router: Router for broadcasting events
        """
        super().__init__()
        self.app = freecad_app
        self.event_router = event_router

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
        """Set up signal handlers for FreeCAD events."""
        if self.app is None:
            logger.warning("FreeCAD not available, cannot set up signal handlers")
            return

        try:
            # Connect to document changed signal
            if hasattr(self.app, "signalDocumentChanged"):
                self.app.signalDocumentChanged.connect(self._on_document_changed)
                logger.info("Connected to FreeCAD document changed signal")

            # Connect to document created signal
            if hasattr(self.app, "signalNewDocument"):
                self.app.signalNewDocument.connect(self._on_document_created)
                logger.info("Connected to FreeCAD new document signal")

            # Connect to document closed signal
            if hasattr(self.app, "signalDeleteDocument"):
                self.app.signalDeleteDocument.connect(self._on_document_closed)
                logger.info("Connected to FreeCAD delete document signal")

            # Connect to active document changed signal
            if hasattr(self.app, "signalActiveDocument"):
                self.app.signalActiveDocument.connect(self._on_active_document_changed)
                logger.info("Connected to FreeCAD active document signal")

            # Connect to GUI selection changed signal if available
            if hasattr(self.app, "Gui") and hasattr(self.app.Gui, "Selection"):
                if hasattr(self.app.Gui.Selection, "signalSelectionChanged"):
                    self.app.Gui.Selection.signalSelectionChanged.connect(
                        self._on_selection_changed
                    )
                    logger.info("Connected to FreeCAD selection changed signal")

        except Exception as e:
            logger.error(f"Error setting up FreeCAD signal handlers: {e}")

    def _on_document_changed(self, doc):
        """Handle document changed event."""
        logger.info(f"Document changed: {doc.Name}")
        event_data = {
            "type": "document_changed",
            "document": doc.Name,
            "timestamp": time.time(),
            "recomputed_objects": [obj.Name for obj in doc.Objects if obj.State],
        }
        asyncio.create_task(self.emit_event("document_changed", event_data))

    def _on_document_created(self, doc):
        """Handle document created event."""
        logger.info(f"Document created: {doc.Name}")
        event_data = {
            "type": "document_created",
            "document": doc.Name,
            "timestamp": time.time(),
        }
        asyncio.create_task(self.emit_event("document_created", event_data))

    def _on_document_closed(self, doc_name):
        """Handle document closed event."""
        logger.info(f"Document closed: {doc_name}")
        event_data = {
            "type": "document_closed",
            "document": doc_name,
            "timestamp": time.time(),
        }
        asyncio.create_task(self.emit_event("document_closed", event_data))

    def _on_active_document_changed(self, doc):
        """Handle active document changed event."""
        logger.info(f"Active document changed: {doc.Name if doc else 'None'}")
        event_data = {
            "type": "active_document_changed",
            "document": doc.Name if doc else None,
            "timestamp": time.time(),
        }
        asyncio.create_task(self.emit_event("active_document_changed", event_data))

    def _on_selection_changed(self):
        """Handle selection changed event."""
        if not hasattr(self.app, "Gui") or not hasattr(self.app.Gui, "Selection"):
            return

        selected_objects = []
        for obj in self.app.Gui.Selection.getSelection():
            selected_objects.append(
                {
                    "id": obj.Name,
                    "label": obj.Label,
                    "document": obj.Document.Name if hasattr(obj, "Document") else None,
                }
            )

        logger.info(f"Selection changed: {len(selected_objects)} objects")
        event_data = {
            "type": "selection_changed",
            "selection": selected_objects,
            "timestamp": time.time(),
        }
        asyncio.create_task(self.emit_event("selection_changed", event_data))

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
