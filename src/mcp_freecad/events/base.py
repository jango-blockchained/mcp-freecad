from typing import Dict, Any, Set, Callable, Coroutine
from abc import ABC, abstractmethod

EventHandler = Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]

class EventProvider(ABC):
    """Base class for all event providers in the MCP server."""
    
    def __init__(self):
        self.listeners: Set[str] = set()
    
    def add_listener(self, client_id: str) -> None:
        """
        Add a client as a listener for events.
        
        Args:
            client_id: The ID of the client
        """
        self.listeners.add(client_id)
        
    def remove_listener(self, client_id: str) -> None:
        """
        Remove a client as a listener for events.
        
        Args:
            client_id: The ID of the client
        """
        if client_id in self.listeners:
            self.listeners.remove(client_id)
    
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
        pass 