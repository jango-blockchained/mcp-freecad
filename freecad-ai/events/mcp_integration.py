"""
MCP integration utilities for the events system.

This module provides utilities for integrating the events system with the MCP server,
including event handlers and client management.
"""

import asyncio
import logging
from typing import Any, Dict, List, Callable

try:
    from .event_manager import EventManager
except ImportError:
    # Fallback for when module is loaded by FreeCAD
    import os
    import sys

    addon_dir = os.path.dirname(os.path.dirname(__file__))
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)

    from events.event_manager import EventManager

logger = logging.getLogger(__name__)


class MCPEventIntegration:
    """
    Integration layer between the events system and MCP server.

    This class handles event subscriptions, notifications, and provides
    MCP-specific event handling capabilities.
    """

    def __init__(self, event_manager: EventManager):
        """
        Initialize the MCP event integration.

        Args:
            event_manager: The EventManager instance
        """
        self.event_manager = event_manager
        self.mcp_clients: Dict[str, Dict[str, Any]] = {}
        self.notification_handlers: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()

    async def register_mcp_client(
        self, client_id: str, client_info: Dict[str, Any] = None
    ) -> bool:
        """
        Register an MCP client for event notifications.

        Args:
            client_id: Unique identifier for the MCP client
            client_info: Optional client information

        Returns:
            bool: True if registration was successful
        """
        async with self._lock:
            self.mcp_clients[client_id] = {
                "info": client_info or {},
                "subscriptions": [],
                "last_activity": asyncio.get_event_loop().time(),
                "notification_count": 0,
            }

        logger.info(f"Registered MCP client: {client_id}")
        return True

    async def unregister_mcp_client(self, client_id: str) -> bool:
        """
        Unregister an MCP client.

        Args:
            client_id: Unique identifier for the MCP client

        Returns:
            bool: True if unregistration was successful
        """
        async with self._lock:
            if client_id in self.mcp_clients:
                # Remove from event subscriptions
                await self.event_manager.remove_event_listener(client_id)

                # Remove client record
                del self.mcp_clients[client_id]

                logger.info(f"Unregistered MCP client: {client_id}")
                return True
            else:
                logger.warning(f"Attempted to unregister unknown client: {client_id}")
                return False

    async def subscribe_to_events(
        self, client_id: str, event_types: List[str] = None
    ) -> bool:
        """
        Subscribe an MCP client to specific event types.

        Args:
            client_id: Unique identifier for the MCP client
            event_types: List of event types to subscribe to (None for all)

        Returns:
            bool: True if subscription was successful
        """
        if client_id not in self.mcp_clients:
            logger.error(f"Client {client_id} not registered")
            return False

        # Subscribe through event manager
        success = await self.event_manager.add_event_listener(client_id, event_types)

        if success:
            async with self._lock:
                if event_types:
                    self.mcp_clients[client_id]["subscriptions"].extend(event_types)
                else:
                    self.mcp_clients[client_id]["subscriptions"] = ["*"]

                self.mcp_clients[client_id][
                    "last_activity"
                ] = asyncio.get_event_loop().time()

        return success

    async def unsubscribe_from_events(
        self, client_id: str, event_types: List[str] = None
    ) -> bool:
        """
        Unsubscribe an MCP client from specific event types.

        Args:
            client_id: Unique identifier for the MCP client
            event_types: List of event types to unsubscribe from (None for all)

        Returns:
            bool: True if unsubscription was successful
        """
        if client_id not in self.mcp_clients:
            logger.error(f"Client {client_id} not registered")
            return False

        # Unsubscribe through event manager
        success = await self.event_manager.remove_event_listener(client_id, event_types)

        if success:
            async with self._lock:
                if event_types:
                    for event_type in event_types:
                        if event_type in self.mcp_clients[client_id]["subscriptions"]:
                            self.mcp_clients[client_id]["subscriptions"].remove(
                                event_type
                            )
                else:
                    self.mcp_clients[client_id]["subscriptions"].clear()

                self.mcp_clients[client_id][
                    "last_activity"
                ] = asyncio.get_event_loop().time()

        return success

    def set_notification_handler(self, event_type: str, handler: Callable) -> None:
        """
        Set a notification handler for a specific event type.

        Args:
            event_type: The event type to handle
            handler: The handler function (should accept client_id, event_type, event_data)
        """
        self.notification_handlers[event_type] = handler
        logger.info(f"Set notification handler for event type: {event_type}")

    async def handle_event_notification(
        self, client_id: str, event_type: str, event_data: Dict[str, Any]
    ) -> bool:
        """
        Handle event notification for a specific client.

        Args:
            client_id: The client to notify
            event_type: The event type
            event_data: The event data

        Returns:
            bool: True if notification was handled successfully
        """
        if client_id not in self.mcp_clients:
            logger.debug(f"Skipping notification for unregistered client: {client_id}")
            return False

        try:
            # Update client activity
            async with self._lock:
                self.mcp_clients[client_id][
                    "last_activity"
                ] = asyncio.get_event_loop().time()
                self.mcp_clients[client_id]["notification_count"] += 1

            # Use specific handler if available
            if event_type in self.notification_handlers:
                handler = self.notification_handlers[event_type]
                if asyncio.iscoroutinefunction(handler):
                    await handler(client_id, event_type, event_data)
                else:
                    handler(client_id, event_type, event_data)
            else:
                # Default notification handling
                await self._default_notification_handler(
                    client_id, event_type, event_data
                )

            return True

        except Exception as e:
            logger.error(f"Error handling event notification for {client_id}: {e}")
            return False

    async def _default_notification_handler(
        self, client_id: str, event_type: str, event_data: Dict[str, Any]
    ) -> None:
        """
        Default notification handler.

        Args:
            client_id: The client to notify
            event_type: The event type
            event_data: The event data
        """
        # Create a formatted notification
        notification = {
            "method": "notifications/events",
            "params": {"type": event_type, "data": event_data, "client_id": client_id},
        }

        logger.debug(f"Default notification for {client_id}: {event_type}")
        # In a real implementation, this would send the notification to the MCP client
        # For now, we just log it

    async def get_client_info(self, client_id: str = None) -> Dict[str, Any]:
        """
        Get information about MCP clients.

        Args:
            client_id: Optional specific client ID

        Returns:
            Dictionary with client information
        """
        async with self._lock:
            if client_id:
                return self.mcp_clients.get(client_id, {})
            else:
                return dict(self.mcp_clients)

    async def get_event_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about event handling.

        Returns:
            Dictionary with event statistics
        """
        system_status = await self.event_manager.get_system_status()

        async with self._lock:
            client_stats = {
                "total_clients": len(self.mcp_clients),
                "clients_with_subscriptions": sum(
                    1 for client in self.mcp_clients.values() if client["subscriptions"]
                ),
                "total_notifications": sum(
                    client["notification_count"] for client in self.mcp_clients.values()
                ),
            }

        return {"mcp_integration": client_stats, "event_system": system_status}

    async def cleanup_inactive_clients(self, timeout: float = 3600.0) -> int:
        """
        Clean up inactive MCP clients.

        Args:
            timeout: Timeout in seconds for considering a client inactive

        Returns:
            Number of clients cleaned up
        """
        current_time = asyncio.get_event_loop().time()
        inactive_clients = []

        async with self._lock:
            for client_id, client_info in self.mcp_clients.items():
                if (current_time - client_info["last_activity"]) > timeout:
                    inactive_clients.append(client_id)

        # Remove inactive clients
        for client_id in inactive_clients:
            await self.unregister_mcp_client(client_id)

        if inactive_clients:
            logger.info(f"Cleaned up {len(inactive_clients)} inactive MCP clients")

        return len(inactive_clients)

    async def shutdown(self) -> None:
        """Shutdown the MCP integration and clean up resources."""
        async with self._lock:
            # Unregister all clients
            client_ids = list(self.mcp_clients.keys())

        for client_id in client_ids:
            await self.unregister_mcp_client(client_id)

        self.notification_handlers.clear()
        logger.info("MCP event integration shutdown complete")
