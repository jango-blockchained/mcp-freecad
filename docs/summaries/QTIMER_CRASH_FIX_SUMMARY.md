# QTimer.singleShot Crash Fix Summary

## Issue
The FreeCAD AI addon was experiencing crashes due to QTimer.singleShot calls with lambda functions, especially during workbench switching and widget initialization.

## Root Cause
QTimer.singleShot with lambda functions can cause segmentation faults in PySide2/Qt when:
- The Qt event loop is not fully initialized
- During rapid workbench switching
- Lambda functions create closure issues with Qt's signal/slot mechanism

## Files Fixed

### 1. **freecad-ai/gui/providers_widget.py**
- **Lines fixed**: 661, 1044, 1114, 1554
- **Changes**: Removed all QTimer.singleShot calls that were clearing status labels after delays
- **Impact**: Status labels now remain visible for user reference instead of auto-clearing

### 2. **freecad-ai/gui/connection_widget.py**
- **Lines fixed**: 373, 423
- **Changes**: Removed delayed connection simulations and test result displays
- **Impact**: Connection operations execute immediately without delay

### 3. **freecad-ai/gui/unified_connection_widget.py**
- **Lines fixed**: 431, 464, 471, 505-507
- **Changes**: Removed all delayed operations for server management and connection testing
- **Impact**: All operations execute synchronously without timer delays

### 4. **freecad-ai/gui/agent_control_widget.py**
- **Line fixed**: 329
- **Changes**: Removed delayed command completion simulation
- **Impact**: Commands complete immediately

### 5. **freecad-ai/gui/conversation_widget.py**
- **Line fixed**: 637
- **Changes**: Removed asynchronous AI call timer
- **Impact**: AI calls execute directly without timer indirection

### 6. **freecad-ai/gui/server_widget.py**
- **Line fixed**: 444
- **Changes**: Removed delayed server restart
- **Impact**: Server restarts immediately after stopping

## Solution Pattern
All QTimer.singleShot calls were replaced with direct method calls:

**Before:**
```python
QtCore.QTimer.singleShot(delay, lambda: self.method())
```

**After:**
```python
self.method()  # Direct call to avoid QTimer crashes
```

## Testing
After applying all fixes:
- FreeCAD starts successfully without segmentation faults
- The FreeCAD AI addon loads without crashes
- Workbench switching no longer causes crashes

## Note
The MCP server files (src/mcp_freecad/client/freecad_rpc_server.py) also contain QTimer.singleShot calls, but these were not modified as they are part of the server infrastructure and not related to the addon crashes.

## Recommendation
For future development:
1. Avoid using QTimer.singleShot with lambda functions in FreeCAD addons
2. Use direct method calls or QTimer with proper slot connections
3. Be cautious with Qt timers during widget initialization and workbench switching 
