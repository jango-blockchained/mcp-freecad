"""
Event router for the FreeCAD AI addon.

This module provides event routing and broadcasting capabilities for the MCP server.
"""

import asyncio
import logging
from typing import Any, Dict, List, Set, Callable
import weakref
from datetime import datetime

logger = logging.getLogger(__name__)


class EventRouter:
    """
    Central event router for broadcasting events to multiple listeners.

    This class manages event subscriptions and broadcasts events to all registered
    listeners in a thread-safe manner.
    """

    def __init__(self, max_history_size: int = 1000):
        """Initialize the event router.

        Args:
            max_history_size: Maximum number of events to keep in history
        """
        self.listeners: Dict[str, Set[Callable]] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}
        self.event_history: List[Dict[str, Any]] = []
        self.max_history_size = max_history_size
        self._lock = asyncio.Lock()

    async def add_listener(
        self, client_id: str, event_types: List[str] = None, callback: Callable = None
    ) -> None:
        """
        Add a listener for specific event types.

        Args:
            client_id: Unique identifier for the client
            event_types: List of event types to listen for (None means all events)
            callback: Optional callback function for direct notification
        """
        async with self._lock:
            if client_id not in self.client_subscriptions:
                self.client_subscriptions[client_id] = set()

            if event_types:
                for event_type in event_types:
                    self.client_subscriptions[client_id].add(event_type)

                    if event_type not in self.listeners:
                        self.listeners[event_type] = set()

                    if callback:
                        # Use weak reference to avoid memory leaks
                        self.listeners[event_type].add(weakref.ref(callback))
            else:
                # Subscribe to all events
                self.client_subscriptions[client_id].add("*")

        logger.info(f"Added listener {client_id} for events: {event_types or ['all']}")

    async def remove_listener(
        self, client_id: str, event_types: List[str] = None
    ) -> None:
        """
        Remove a listener from specific event types.

        Args:
            client_id: Unique identifier for the client
            event_types: List of event types to stop listening for (None means all events)
        """
        async with self._lock:
            if client_id not in self.client_subscriptions:
                return

            if event_types:
                for event_type in event_types:
                    self.client_subscriptions[client_id].discard(event_type)
            else:
                # Remove from all events
                self.client_subscriptions[client_id].clear()

            # Clean up empty subscriptions
            if not self.client_subscriptions[client_id]:
                del self.client_subscriptions[client_id]

        logger.info(
            f"Removed listener {client_id} from events: {event_types or ['all']}"
        )

    async def broadcast_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> None:
        """
        Broadcast an event to all registered listeners.

        Args:
            event_type: The type of event being broadcast
            event_data: The event data
        """
        # Add timestamp if not present
        if "timestamp" not in event_data:
            event_data["timestamp"] = datetime.now().isoformat()

        # Create event record
        event_record = {
            "type": event_type,
            "data": event_data,
            "timestamp": event_data.get("timestamp"),
            "listeners_notified": 0,
        }

        async with self._lock:
            # Add to history
            self.event_history.append(event_record)
            if len(self.event_history) > self.max_history_size:
                self.event_history.pop(0)

            # Find all listeners for this event type
            interested_clients = []

            for client_id, subscriptions in self.client_subscriptions.items():
                if "*" in subscriptions or event_type in subscriptions:
                    interested_clients.append(client_id)

            event_record["listeners_notified"] = len(interested_clients)

            # Notify direct callback listeners
            if event_type in self.listeners:
                dead_refs = []
                for callback_ref in self.listeners[event_type]:
                    callback = callback_ref()
                    if callback is None:
                        # Callback was garbage collected
                        dead_refs.append(callback_ref)
                    else:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                asyncio.create_task(callback(event_type, event_data))
                            else:
                                callback(event_type, event_data)
                        except Exception as e:
                            logger.error(f"Error calling event callback: {e}")

                # Clean up dead references
                for dead_ref in dead_refs:
                    self.listeners[event_type].discard(dead_ref)

        logger.debug(
            f"Broadcast {event_type} event to {len(interested_clients)} listeners"
        )

    async def get_event_history(
        self, client_id: str = None, event_types: List[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get event history for a client or specific event types.

        Args:
            client_id: Optional client ID to filter by subscriptions
            event_types: Optional list of event types to filter by
            limit: Maximum number of events to return

        Returns:
            List of event records
        """
        async with self._lock:
            filtered_events = []

            for event in reversed(self.event_history):
                # Filter by event types if specified
                if event_types and event["type"] not in event_types:
                    continue

                # Filter by client subscriptions if specified
                if client_id and client_id in self.client_subscriptions:
                    subscriptions = self.client_subscriptions[client_id]
                    if "*" not in subscriptions and event["type"] not in subscriptions:
                        continue

                filtered_events.append(event)

                if len(filtered_events) >= limit:
                    break

            return filtered_events

    async def get_active_listeners(self) -> Dict[str, Any]:
        """
        Get information about currently active listeners.

        Returns:
            Dictionary with listener information
        """
        async with self._lock:
            return {
                "total_clients": len(self.client_subscriptions),
                "clients": dict(self.client_subscriptions),
                "event_types_with_callbacks": list(self.listeners.keys()),
                "total_events_in_history": len(self.event_history),
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the event router.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_clients": len(self.client_subscriptions),
            "total_event_types": len(self.listeners),
            "events_in_history": len(self.event_history),
            "max_history_size": self.max_history_size,
        }

        if self.event_history:
            stats["latest_event"] = self.event_history[-1]["timestamp"]
            stats["oldest_event"] = self.event_history[0]["timestamp"]

        return stats

    async def clear_history(self) -> None:
        """Clear the event history."""
        async with self._lock:
            self.event_history.clear()
        logger.info("Event history cleared")

    async def shutdown(self) -> None:
        """Shutdown the event router and clean up resources."""
        async with self._lock:
            self.listeners.clear()
            self.client_subscriptions.clear()
            self.event_history.clear()
        logger.info("Event router shutdown complete")
