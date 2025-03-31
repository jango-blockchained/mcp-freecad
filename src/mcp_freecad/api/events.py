from typing import Dict, Any, Optional, List
import asyncio
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uuid

logger = logging.getLogger(__name__)

# In-memory store of connected clients and their queues
client_queues = {}

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
            "data": {"client_id": client_id, "message": "Connected to FreeCAD MCP Server"}
        }
        yield f"event: {connection_event['event']}\ndata: {json.dumps(connection_event['data'])}\n\n"
        
        # Keep-alive ping every 15 seconds
        ping_task = asyncio.create_task(ping_client(client_id))
        
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
        logger.info(f"Cleaned up resources for client {client_id}")

async def ping_client(client_id: str):
    """Send periodic pings to keep the connection alive."""
    try:
        while client_id in client_queues:
            await asyncio.sleep(15.0)
            if client_id in client_queues:
                event = {
                    "event": "ping",
                    "data": {"timestamp": int(asyncio.get_event_loop().time())}
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

def create_event_router(mcp_server):
    """Create a FastAPI router for events."""
    router = APIRouter()
    
    @router.get("")
    async def subscribe_events(
        request: Request,
        types: Optional[List[str]] = Query(None, description="Event types to subscribe to"),
        authorization: Optional[str] = Header(None)
    ):
        # Authenticate the request
        if authorization:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            if not await mcp_server.auth_manager.authenticate(token):
                raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Generate a unique client ID
        client_id = str(uuid.uuid4())
        
        # Register this client with event handlers
        if types:
            for event_type in types:
                if event_type in mcp_server.event_handlers:
                    for handler in mcp_server.event_handlers[event_type]:
                        handler.add_listener(client_id)
        else:
            # Register for all event types if none specified
            for event_type, handlers in mcp_server.event_handlers.items():
                for handler in handlers:
                    handler.add_listener(client_id)
        
        # Return a streaming response
        return StreamingResponse(
            event_generator(client_id),
            media_type="text/event-stream"
        )
    
    @router.post("/events/{event_type}")
    async def trigger_event(
        event_type: str,
        event_data: EventData,
        authorization: Optional[str] = Header(None)
    ) -> EventResponse:
        """Trigger an event in the MCP server."""
        # Authenticate the request
        if authorization:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            if not await mcp_server.auth_manager.authenticate(token):
                raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Check if event type is registered
        if event_type not in mcp_server.event_handlers:
            return EventResponse(
                success=False,
                message=f"No handlers registered for event type: {event_type}"
            )
            
        # Trigger the event
        try:
            # Call all registered handlers for this event type
            for handler in mcp_server.event_handlers[event_type]:
                await handler.handle_event(event_type, event_data.data)
                
            return EventResponse(
                success=True,
                message=f"Event {event_type} triggered successfully"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error triggering event: {str(e)}")
    
    # Add a function to broadcast events
    async def broadcast_event(event_type: str, event_data: Dict[str, Any]):
        """
        Broadcast an event to connected clients.
        This function is used internally by event providers.
        """
        # In a real implementation, this would send the event to connected 
        # WebSocket clients or other event subscribers
        pass
    
    # Add the broadcast function to the router
    router.broadcast_event = broadcast_event
    
    return router 