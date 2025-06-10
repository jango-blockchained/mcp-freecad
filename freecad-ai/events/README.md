# Events System Documentation

## Overview

The FreeCAD AI addon includes a comprehensive events system that captures and broadcasts various FreeCAD events to MCP clients. This system enables real-time monitoring of document changes, command execution, errors, and other significant events within FreeCAD.

## Architecture

The events system consists of several key components:

### Core Components

1. **EventRouter** - Central event routing and broadcasting
2. **EventManager** - Coordinates all event providers
3. **MCPEventIntegration** - Bridges events system with MCP clients
4. **Event Providers** - Capture specific types of events

### Event Providers

- **DocumentEventProvider** - Captures document-related events
- **CommandExecutionEventProvider** - Captures command execution events  
- **ErrorEventProvider** - Captures error and exception events

## Quick Start

### Basic Setup

```python
from freecad_ai.events import initialize_event_system

# Initialize the complete events system
event_manager, mcp_integration = await initialize_event_system()

if event_manager:
    print("Events system initialized successfully")
else:
    print("Failed to initialize events system")
```

### Register an MCP Client

```python
# Register a client for event notifications
client_id = "my_mcp_client"
await mcp_integration.register_mcp_client(client_id, {
    "name": "My MCP Client",
    "version": "1.0.0"
})

# Subscribe to specific event types
await mcp_integration.subscribe_to_events(client_id, [
    "document_changed",
    "command_executed",
    "error"
])
```

### Handle Events

```python
# Set custom notification handlers
def handle_document_event(client_id, event_type, event_data):
    print(f"Document event for {client_id}: {event_type}")
    print(f"Data: {event_data}")

mcp_integration.set_notification_handler("document_changed", handle_document_event)
```

## Event Types

### Document Events

- **document_created** - New document created
- **document_changed** - Document modified or recomputed
- **document_closed** - Document closed
- **active_document_changed** - Active document switched
- **selection_changed** - Object selection changed

### Command Events

- **command_executed** - FreeCAD command executed

### Error Events

- **error** - Error or exception occurred

## Event Data Structure

All events follow a consistent structure:

```json
{
  "type": "event_type",
  "timestamp": "2025-06-10T12:00:00.000Z",
  "data": {
    // Event-specific data
  }
}
```

### Document Event Data

```json
{
  "type": "document_changed",
  "document": "Document_Name",
  "timestamp": 1625920800.0,
  "recomputed_objects": ["Cube", "Cylinder"]
}
```

### Command Event Data

```json
{
  "type": "command_executed", 
  "command": "Std_New",
  "timestamp": 1625920800.0
}
```

### Error Event Data

```json
{
  "type": "error",
  "message": "Error description",
  "timestamp": 1625920800.0,
  "source": "freecad_signal",
  "traceback": "Full traceback..."
}
```

## Advanced Usage

### Custom Event Emission

```python
# Emit custom events
await event_manager.emit_custom_event("custom_event", {
    "user_action": "button_clicked",
    "data": {"button": "export", "format": "step"}
})
```

### Event History

```python
# Get event history
history = await event_manager.get_event_history(limit=50)
for event in history:
    print(f"{event['type']}: {event['data']}")

# Get command history specifically
commands = await event_manager.get_command_history(limit=10)

# Get error history
errors = await event_manager.get_error_history(limit=5)
```

### System Status

```python
# Get comprehensive system status
status = await event_manager.get_system_status()
print(f"Initialized: {status['initialized']}")
print(f"Active providers: {list(status['providers'].keys())}")
print(f"Total events: {status['router_stats']['events_in_history']}")
```

### Client Management

```python
# Get client information
clients = await mcp_integration.get_client_info()
for client_id, info in clients.items():
    print(f"Client {client_id}: {info['notification_count']} notifications")

# Cleanup inactive clients (1 hour timeout)
cleaned = await mcp_integration.cleanup_inactive_clients(3600)
print(f"Cleaned up {cleaned} inactive clients")
```

## Configuration

### Event History Limits

The system maintains configurable limits on event history:

- **Event Router**: 1000 events (configurable via `max_history_size`)
- **Command Provider**: 100 commands
- **Error Provider**: 50 errors

### Thread Safety

All components are designed to be thread-safe and work properly in FreeCAD's mixed synchronous/asynchronous environment.

## Error Handling

The events system includes robust error handling:

1. **Graceful Degradation** - Failed imports don't break the system
2. **Safe Async Operations** - Uses `safe_async` utilities for FreeCAD compatibility
3. **Exception Capture** - Global exception handler captures unhandled errors
4. **Logging** - Comprehensive logging for debugging

## Integration with MCP Server

The events system is designed to integrate seamlessly with MCP servers:

```python
# In your MCP server implementation
from freecad_ai.events import initialize_event_system

class FreeCADMCPServer:
    async def __init__(self):
        self.event_manager, self.mcp_integration = await initialize_event_system()
        
    async def handle_client_connect(self, client_id):
        await self.mcp_integration.register_mcp_client(client_id)
        await self.mcp_integration.subscribe_to_events(client_id)
        
    async def handle_client_disconnect(self, client_id):
        await self.mcp_integration.unregister_mcp_client(client_id)
```

## Troubleshooting

### Common Issues

1. **Events not firing** - Check that FreeCAD signals are properly connected
2. **High memory usage** - Adjust event history limits
3. **Thread issues** - Ensure proper async/await usage

### Debug Information

```python
# Check event loop status
from freecad_ai.utils.safe_async import check_event_loop_status
status = check_event_loop_status()
print(f"Event loop status: {status}")

# Get detailed statistics
stats = await mcp_integration.get_event_statistics()
print(f"Statistics: {stats}")
```

## Testing

The events system includes comprehensive tests:

```bash
# Run all events tests
python -m pytest freecad_ai/tests/test_events.py -v

# Run specific test class
python -m pytest freecad_ai/tests/test_events.py::TestEventManager -v
```

## Performance Considerations

- Events are processed asynchronously to avoid blocking FreeCAD
- Event history is limited to prevent memory leaks
- Weak references are used for callback handlers
- Background thread pools handle async operations when no event loop is available

## Security

- Client IDs should be validated before registration
- Event data should be sanitized before broadcasting
- Consider rate limiting for high-frequency events
- Implement proper authentication for MCP clients
