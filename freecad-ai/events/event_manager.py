"""
Event manager for coordinating all event providers in the FreeCAD AI addon.

This module provides a central manager that coordinates all event providers
and integrates them with the MCP server.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
import weakref

try:
    from .event_router import EventRouter
    from .base import EventProvider
    from .document_events import DocumentEventProvider
    from .command_events import CommandExecutionEventProvider
    from .error_events import ErrorEventProvider
except ImportError:
    # Fallback for when module is loaded by FreeCAD
    import os
    import sys

    addon_dir = os.path.dirname(os.path.dirname(__file__))
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)
    
    from events.event_router import EventRouter
    from events.base import EventProvider
    from events.document_events import DocumentEventProvider
    from events.command_events import CommandExecutionEventProvider
    from events.error_events import ErrorEventProvider

logger = logging.getLogger(__name__)


class EventManager:
    """
    Central event manager that coordinates all event providers.
    
    This class manages the lifecycle of event providers, routes events,
    and provides a unified interface for the MCP server.
    """

    def __init__(self, freecad_app=None):
        """
        Initialize the event manager.

        Args:
            freecad_app: Optional FreeCAD application instance
        """
        self.freecad_app = freecad_app
        self.event_router = EventRouter()
        self.providers: Dict[str, EventProvider] = {}
        self.is_initialized = False
        self._lock = asyncio.Lock()

        # Try to import FreeCAD if not provided
        if self.freecad_app is None:
            try:
                import FreeCAD
                self.freecad_app = FreeCAD
                logger.info("EventManager connected to FreeCAD")
            except ImportError:
                logger.warning("FreeCAD not available for EventManager")

    async def initialize(self) -> bool:
        """
        Initialize all event providers.

        Returns:
            bool: True if initialization was successful
        """
        async with self._lock:
            if self.is_initialized:
                logger.warning("EventManager already initialized")
                return True

            try:
                # Initialize document event provider
                self.providers["document"] = DocumentEventProvider(
                    freecad_app=self.freecad_app,
                    event_router=self.event_router
                )
                logger.info("Initialized document event provider")

                # Initialize command execution event provider
                self.providers["command"] = CommandExecutionEventProvider(
                    freecad_app=self.freecad_app,
                    event_router=self.event_router
                )
                logger.info("Initialized command execution event provider")

                # Initialize error event provider
                self.providers["error"] = ErrorEventProvider(
                    freecad_app=self.freecad_app,
                    event_router=self.event_router
                )
                logger.info("Initialized error event provider")

                self.is_initialized = True
                logger.info("EventManager initialization complete")
                return True

            except Exception as e:
                logger.error(f"Failed to initialize EventManager: {e}")
                # Clean up any partially initialized providers
                await self._cleanup_providers()
                return False

    async def shutdown(self) -> None:
        """Shutdown the event manager and all providers."""
        async with self._lock:
            if not self.is_initialized:
                return

            await self._cleanup_providers()
            await self.event_router.shutdown()
            self.is_initialized = False
            logger.info("EventManager shutdown complete")

    async def _cleanup_providers(self) -> None:
        """Clean up all event providers."""
        for provider_name, provider in self.providers.items():
            try:
                if hasattr(provider, "shutdown"):
                    await provider.shutdown()
                elif hasattr(provider, "__del__"):
                    provider.__del__()
                logger.debug(f"Cleaned up {provider_name} provider")
            except Exception as e:
                logger.error(f"Error cleaning up {provider_name} provider: {e}")
        
        self.providers.clear()

    async def add_event_listener(self, 
                                client_id: str, 
                                event_types: List[str] = None) -> bool:
        """
        Add an event listener for a client.

        Args:
            client_id: Unique identifier for the client
            event_types: List of event types to listen for (None for all events)

        Returns:
            bool: True if listener was added successfully
        """
        if not self.is_initialized:
            logger.error("EventManager not initialized")
            return False

        try:
            await self.event_router.add_listener(client_id, event_types)
            
            # Also add to individual providers
            for provider in self.providers.values():
                provider.add_listener(client_id)

            logger.info(f"Added event listener for client {client_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add event listener for {client_id}: {e}")
            return False

    async def remove_event_listener(self, 
                                   client_id: str, 
                                   event_types: List[str] = None) -> bool:
        """
        Remove an event listener for a client.

        Args:
            client_id: Unique identifier for the client
            event_types: List of event types to stop listening for (None for all)

        Returns:
            bool: True if listener was removed successfully
        """
        if not self.is_initialized:
            logger.error("EventManager not initialized")
            return False

        try:
            await self.event_router.remove_listener(client_id, event_types)
            
            # Also remove from individual providers if removing all events
            if event_types is None:
                for provider in self.providers.values():
                    provider.remove_listener(client_id)

            logger.info(f"Removed event listener for client {client_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove event listener for {client_id}: {e}")
            return False

    async def get_event_history(self, 
                               client_id: str = None,
                               event_types: List[str] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get event history.

        Args:
            client_id: Optional client ID to filter by subscriptions
            event_types: Optional list of event types to filter by
            limit: Maximum number of events to return

        Returns:
            List of event records
        """
        if not self.is_initialized:
            logger.error("EventManager not initialized")
            return []

        return await self.event_router.get_event_history(client_id, event_types, limit)

    async def get_command_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get command execution history.

        Args:
            limit: Optional limit on the number of history items to return

        Returns:
            List of command execution events
        """
        if not self.is_initialized or "command" not in self.providers:
            return []

        command_provider = self.providers["command"]
        if hasattr(command_provider, "get_command_history"):
            return command_provider.get_command_history(limit)
        
        return []

    async def get_error_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get error history.

        Args:
            limit: Optional limit on the number of history items to return

        Returns:
            List of error events
        """
        if not self.is_initialized or "error" not in self.providers:
            return []

        error_provider = self.providers["error"]
        if hasattr(error_provider, "get_error_history"):
            return error_provider.get_error_history(limit)
        
        return []

    async def report_error(self, 
                          error_message: str, 
                          error_type: str = "manual",
                          details: Dict[str, Any] = None) -> bool:
        """
        Manually report an error.

        Args:
            error_message: Error message
            error_type: Type of error
            details: Additional error details

        Returns:
            bool: True if error was reported successfully
        """
        if not self.is_initialized or "error" not in self.providers:
            logger.error("Error provider not available")
            return False

        try:
            error_provider = self.providers["error"]
            if hasattr(error_provider, "report_error"):
                error_provider.report_error(error_message, error_type, details)
                return True
            else:
                logger.error("Error provider does not support manual error reporting")
                return False

        except Exception as e:
            logger.error(f"Failed to report error: {e}")
            return False

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get the current status of the event system.

        Returns:
            Dictionary with system status information
        """
        status = {
            "initialized": self.is_initialized,
            "freecad_available": self.freecad_app is not None,
            "providers": {},
            "router_stats": self.event_router.get_stats(),
            "active_listeners": await self.event_router.get_active_listeners()
        }

        # Get status from each provider
        for name, provider in self.providers.items():
            provider_status = {
                "type": type(provider).__name__,
                "listeners": len(provider.listeners) if hasattr(provider, "listeners") else 0
            }
            
            # Add provider-specific status
            if hasattr(provider, "get_status"):
                try:
                    provider_status.update(provider.get_status())
                except Exception as e:
                    provider_status["error"] = str(e)

            status["providers"][name] = provider_status

        return status

    def get_provider(self, provider_name: str) -> Optional[EventProvider]:
        """
        Get a specific event provider by name.

        Args:
            provider_name: Name of the provider ('document', 'command', 'error')

        Returns:
            EventProvider instance or None if not found
        """
        return self.providers.get(provider_name)

    async def emit_custom_event(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Emit a custom event through the event system.

        Args:
            event_type: The type of event
            event_data: The event data

        Returns:
            bool: True if event was emitted successfully
        """
        if not self.is_initialized:
            logger.error("EventManager not initialized")
            return False

        try:
            await self.event_router.broadcast_event(event_type, event_data)
            return True
        except Exception as e:
            logger.error(f"Failed to emit custom event {event_type}: {e}")
            return False
