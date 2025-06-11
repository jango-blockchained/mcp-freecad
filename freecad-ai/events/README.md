# Event Implementation Fixes

## Overview
Fixed several critical issues in the FreeCAD AI event system implementation to improve reliability, safety, and maintainability.

## Issues Fixed

### 1. Import Error Handling
- **Problem**: Inconsistent fallback import mechanisms across files
- **Solution**: Created `import_utils.py` with standardized import functions
- **Files**: `events/import_utils.py`, all event provider files

### 2. Signal Handler Connection Safety
- **Problem**: Signal connections could fail silently
- **Solution**: Added `_track_signal_connection()` method to track and properly disconnect signals
- **Files**: `events/base.py`, all event provider files

### 3. Global Exception Handler Safety
- **Problem**: Error provider automatically installed global exception handler, potentially interfering with other code
- **Solution**: Made global handler optional with `install_global_handler=False` default
- **Files**: `events/error_events.py`, `events/event_manager.py`

### 4. Configurable History Limits
- **Problem**: History limits were hardcoded in different places
- **Solution**: Made all history sizes configurable through EventManager constructor
- **Files**: `events/event_manager.py`, `events/event_router.py`, all providers

### 5. Proper Cleanup and Shutdown
- **Problem**: Providers didn't properly disconnect from FreeCAD signals on shutdown
- **Solution**: Added proper `shutdown()` methods with signal disconnection
- **Files**: `events/base.py`, all event provider files

### 6. Thread Pool Management
- **Problem**: Each async operation created new thread pools, potential race conditions
- **Solution**: Centralized thread pool management with proper cleanup
- **Files**: `utils/safe_async.py`

### 7. Input Validation
- **Problem**: Missing validation for client IDs and parameters
- **Solution**: Added validation in base EventProvider and throughout system
- **Files**: `events/base.py`, `events/event_manager.py`

## New Features

### Configurable History Sizes
```python
# Create event system with custom history sizes
event_manager, mcp_integration = create_event_system(
    freecad_app=app,
    max_history_size=2000,      # Event router history
    max_error_history=100,      # Error history
    max_command_history=200     # Command history
)
```

### Safe Global Error Handler
```python
# Enable global error handler when needed (disabled by default)
event_manager.enable_global_error_handler(True)
```

### Status Information
```python
# Get detailed status of all providers
status = await event_manager.get_system_status()
```

### Proper Resource Cleanup
```python
# Clean up resources safely
await event_manager.shutdown()
from utils.safe_async import cleanup_async_resources
cleanup_async_resources()
```

## Usage Examples

### Basic Usage
```python
from events import initialize_event_system

# Create and initialize event system
event_manager, mcp_integration = await initialize_event_system()

# Add event listener
await event_manager.add_event_listener("client_1", ["document_changed", "error"])

# Get event history
history = await event_manager.get_event_history(limit=50)

# Report custom error
await event_manager.report_error("Something went wrong", "custom", {"details": "info"})

# Clean shutdown
await event_manager.shutdown()
```

### Advanced Configuration
```python
from events import create_event_system

# Create with custom settings
event_manager, mcp_integration = create_event_system(
    freecad_app=FreeCAD,
    max_history_size=5000,
    max_error_history=200,
    max_command_history=500
)

# Initialize
await event_manager.initialize()

# Enable global error handling if needed
event_manager.enable_global_error_handler(True)

# Get detailed status
status = await event_manager.get_system_status()
print(f"System initialized: {status['initialized']}")
print(f"Providers: {list(status['providers'].keys())}")
```

## Breaking Changes

1. **EventProvider Constructor**: Now accepts `max_history_size` parameter
2. **ErrorEventProvider Constructor**: Now accepts `install_global_handler` parameter (defaults to False)
3. **Event System Creation**: New optional parameters for history sizes

## Migration Guide

### For Existing Code
Most existing code will continue to work without changes due to default parameter values. However, if you were relying on the global exception handler, you'll need to explicitly enable it:

```python
# Old way (automatic global handler)
error_provider = ErrorEventProvider(app, router)

# New way (explicit global handler)
error_provider = ErrorEventProvider(app, router, install_global_handler=True)
# OR
event_manager.enable_global_error_handler(True)
```

## Testing

The event system now includes comprehensive error handling and logging. Issues will be logged rather than causing silent failures. Monitor logs for:

- Signal connection failures
- Event emission failures  
- Resource cleanup issues
- History size warnings

## Performance Improvements

1. **Centralized Thread Pool**: Reduced overhead from multiple thread pool creation
2. **Configurable History**: Ability to tune memory usage based on needs
3. **Proper Cleanup**: Prevents memory leaks from signal connections
4. **Weak References**: Event callbacks use weak references to prevent memory leaks