import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, Header, HTTPException, Query, Request
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel

    FASTAPI_AVAILABLE = True
except ImportError:
    # FastAPI not available, create minimal stubs
    FASTAPI_AVAILABLE = False
    APIRouter = None
    HTTPException = Exception
    BaseModel = object
    StreamingResponse = None

logger = logging.getLogger(__name__)

# In-memory store of connected clients and their queues
client_queues = {}
# In-memory store of client subscriptions
client_subscriptions = {}


async def event_generator(client_id: str):
    """Generate SSE events for a specific client."""
    try:
        # Create a new queue for this client if it doesn't exist
        if client_id not in client_queues:
            client_queues[client_id] = asyncio.Queue()

        queue = client_queues[client_id]

        # Send initial connection established event
        connection_event = {
            "event": "connection_established",
            "data": {
                "client_id": client_id,
                "message": "Connected to FreeCAD MCP Server",
            },
        }
        yield f"event: {connection_event['event']}\ndata: {json.dumps(connection_event['data'])}\n\n"

        # Keep-alive ping every 15 seconds
        asyncio.create_task(ping_client(client_id))

        # Wait for events
        while True:
            # Wait for an event with a timeout
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
                queue.task_done()
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                yield f"event: ping\ndata: {json.dumps({'timestamp': int(asyncio.get_event_loop().time())})}\n\n"
    except asyncio.CancelledError:
        # Client disconnected
        logger.info(f"Client {client_id} disconnected")
    finally:
        # Clean up when client disconnects
        if client_id in client_queues:
            del client_queues[client_id]
        if client_id in client_subscriptions:
            del client_subscriptions[client_id]
        logger.info(f"Cleaned up resources for client {client_id}")


async def ping_client(client_id: str):
    """Send periodic pings to keep the connection alive."""
    try:
        while client_id in client_queues:
            await asyncio.sleep(15.0)
            if client_id in client_queues:
                event = {
                    "event": "ping",
                    "data": {"timestamp": int(asyncio.get_event_loop().time())},
                }
                await client_queues[client_id].put(event)
    except asyncio.CancelledError:
        pass


class EventData(BaseModel):
    event_type: str
    data: Dict[str, Any] = {}


class EventResponse(BaseModel):
    success: bool
    message: str


class EventSubscription(BaseModel):
    event_types: List[str] = []
    filters: Dict[str, Any] = {}


def create_event_router(mcp_server):
    """Create a FastAPI router for events."""
    if not FASTAPI_AVAILABLE:
        logger.warning("FastAPI not available, event router disabled")
        return None

    router = APIRouter()

    @router.get("")
    async def subscribe_events(
        request: Request,
        types: Optional[List[str]] = Query(
            None, description="Event types to subscribe to"
        ),
        authorization: Optional[str] = Header(None),
    ):
        # Authenticate the request
        if authorization:
            token = (
                authorization.replace("Bearer ", "")
                if authorization.startswith("Bearer ")
                else authorization
            )
            if not await mcp_server.auth_manager.authenticate(token):
                raise HTTPException(
                    status_code=401, detail="Invalid authentication token"
                )

        # Generate a unique client ID
        client_id = str(uuid.uuid4())

        # Register this client with event handlers
        if types:
            # Store subscription information
            client_subscriptions[client_id] = types

            # Register with specific event handlers
            for event_type in types:
                if event_type in mcp_server.event_handlers:
                    for handler in mcp_server.event_handlers[event_type]:
                        handler.add_listener(client_id)
        else:
            # Register for all event types if none specified
            all_event_types = list(mcp_server.event_handlers.keys())
            client_subscriptions[client_id] = all_event_types

            for event_type, handlers in mcp_server.event_handlers.items():
                for handler in handlers:
                    handler.add_listener(client_id)

        # Return a streaming response
        return StreamingResponse(
            event_generator(client_id), media_type="text/event-stream"
        )

    @router.post("/events/{event_type}")
    async def trigger_event(
        event_type: str,
        event_data: EventData,
        authorization: Optional[str] = Header(None),
    ) -> EventResponse:
        """Trigger an event in the MCP server."""
        # Authenticate the request
        if authorization:
            token = (
                authorization.replace("Bearer ", "")
                if authorization.startswith("Bearer ")
                else authorization
            )
            if not await mcp_server.auth_manager.authenticate(token):
                raise HTTPException(
                    status_code=401, detail="Invalid authentication token"
                )

        # Check if event type is registered
        if event_type not in mcp_server.event_handlers:
            return EventResponse(
                success=False,
                message=f"No handlers registered for event type: {event_type}",
            )

        # Trigger the event
        try:
            # Call all registered handlers for this event type
            for handler in mcp_server.event_handlers[event_type]:
                await handler.handle_event(event_type, event_data.data)

            return EventResponse(
                success=True, message=f"Event {event_type} triggered successfully"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error triggering event: {str(e)}"
            )

    @router.post("/subscribe")
    async def update_subscription(
        subscription: EventSubscription, authorization: Optional[str] = Header(None)
    ) -> EventResponse:
        """Update a client's event subscription."""
        # Authenticate the request
        if authorization:
            token = (
                authorization.replace("Bearer ", "")
                if authorization.startswith("Bearer ")
                else authorization
            )
            if not await mcp_server.auth_manager.authenticate(token):
                raise HTTPException(
                    status_code=401, detail="Invalid authentication token"
                )

        # Extract client ID from token or header
        # This is a simplified example - in a real implementation, you would extract
        # the client ID from the JWT token or a separate header
        client_id = token

        if client_id not in client_queues:
            raise HTTPException(
                status_code=404, detail="Client not found or not connected"
            )

        # Update subscription
        client_subscriptions[client_id] = subscription.event_types

        # Remove from all handlers first
        for event_type, handlers in mcp_server.event_handlers.items():
            for handler in handlers:
                handler.remove_listener(client_id)

        # Add to requested handlers
        for event_type in subscription.event_types:
            if event_type in mcp_server.event_handlers:
                for handler in mcp_server.event_handlers[event_type]:
                    handler.add_listener(client_id)

        return EventResponse(success=True, message="Subscription updated successfully")

    # Function to broadcast events to connected clients
    async def broadcast_event(event_type: str, event_data: Dict[str, Any]):
        """
        Broadcast an event to connected clients.
        This function is used internally by event providers.

        Args:
            event_type: The type of event
            event_data: The event data
        """
        logger.debug(f"Broadcasting event: {event_type}")

        # Send to all connected clients that have subscribed to this event type
        for client_id, queue in client_queues.items():
            # Check if client is subscribed to this event type
            if client_id in client_subscriptions:
                subscribed_events = client_subscriptions[client_id]
                if event_type in subscribed_events or "*" in subscribed_events:
                    event = {"event": event_type, "data": event_data}
                    await queue.put(event)

    # Add the broadcast function to the router
    router.broadcast_event = broadcast_event

    return router
