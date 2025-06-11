from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Dict, Set
import logging

logger = logging.getLogger(__name__)

EventHandler = Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]


class EventProvider(ABC):
    """Base class for all event providers in the MCP server."""

    def __init__(self, max_history_size: int = 100):
        self.listeners: Set[str] = set()
        self.max_history_size = max_history_size
        self._signal_connections = []  # Track signal connections for cleanup
        self._is_shutdown = False

    def add_listener(self, client_id: str) -> None:
        """
        Add a client as a listener for events.

        Args:
            client_id: The ID of the client
        """
        if not client_id or not isinstance(client_id, str):
            logger.warning(f"Invalid client_id provided: {client_id}")
            return
            
        if self._is_shutdown:
            logger.warning(f"Cannot add listener {client_id}: provider is shutdown")
            return
            
        self.listeners.add(client_id)
        logger.debug(f"Added listener: {client_id}")

    def remove_listener(self, client_id: str) -> None:
        """
        Remove a client as a listener for events.

        Args:
            client_id: The ID of the client
        """
        if not client_id or not isinstance(client_id, str):
            logger.warning(f"Invalid client_id provided: {client_id}")
            return
            
        if client_id in self.listeners:
            self.listeners.remove(client_id)
            logger.debug(f"Removed listener: {client_id}")

    def _track_signal_connection(self, signal, handler) -> bool:
        """
        Track a signal connection for later cleanup.
        
        Args:
            signal: The signal object
            handler: The handler function
            
        Returns:
            bool: True if connection was successful
        """
        try:
            signal.connect(handler)
            self._signal_connections.append((signal, handler))
            return True
        except Exception as e:
            logger.error(f"Failed to connect signal: {e}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the event provider and clean up resources."""
        if self._is_shutdown:
            return
            
        logger.info(f"Shutting down {self.__class__.__name__}")
        
        # Disconnect all tracked signal connections
        for signal, handler in self._signal_connections:
            try:
                signal.disconnect(handler)
                logger.debug(f"Disconnected signal handler: {handler.__name__}")
            except Exception as e:
                logger.warning(f"Failed to disconnect signal handler: {e}")
        
        self._signal_connections.clear()
        self.listeners.clear()
        self._is_shutdown = True

    async def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Handle an event from an external source.

        Args:
            event_type: The type of event
            event_data: The event data
        """
        # By default, just re-emit the event
        await self.emit_event(event_type, event_data)

    @abstractmethod
    async def emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Emit an event to all listeners.

        Args:
            event_type: The type of event
            event_data: The event data
        """
