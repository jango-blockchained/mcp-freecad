# FreeCAD AI Addon Crash Fix Summary

## Issue
The FreeCAD AI addon was crashing on startup with a segmentation fault in PySide2, especially when switching workbenches.

## Root Causes
1. Incorrect signal definition in `provider_integration_service.py` - Qt signals in PySide2 MUST be defined as class attributes, not instance attributes.
2. QTimer.singleShot causing crashes during workbench activation, possibly due to lambda functions and Qt event loop state.

## Error Messages
```
AttributeError: 'PySide2.QtCore.Signal' object has no attribute 'connect'
Program received signal SIGSEGV, Segmentation fault.
```

## Fixes Applied

### 1. Fixed Signal Definitions
Changed the signal definitions in `/home/jango/Git/mcp-freecad/freecad-ai/ai/provider_integration_service.py`:

### Before (INCORRECT):
```python
class ProviderIntegrationService(QtCore.QObject):
    def __init__(self):
        # This is WRONG - signals cannot be created in __init__
        self.provider_added = QtCore.Signal(str, str)
        self.provider_removed = QtCore.Signal(str)
        self.provider_status_changed = QtCore.Signal(str, str, str)
        self.providers_updated = QtCore.Signal()
```

### After (CORRECT):
```python
class ProviderIntegrationService(QtCore.QObject):
    # Signals MUST be defined as class attributes
    provider_added = QtCore.Signal(str, str)
    provider_removed = QtCore.Signal(str)
    provider_status_changed = QtCore.Signal(str, str, str)
    providers_updated = QtCore.Signal()
    
    def __init__(self):
        # Initialize other instance attributes here
```

### 2. Removed QTimer Usage
Removed all QTimer.singleShot calls to avoid crashes. All initialization is now done directly:

#### In `main_widget.py`:
```python
# Before - CRASHES
QtCore.QTimer.singleShot(1000, self.provider_service.initialize_providers_from_config)
QtCore.QTimer.singleShot(500, self._connect_widgets_to_service_safe)
QtCore.QTimer.singleShot(2000, self._final_connection_check)

# After - STABLE
self.provider_service.initialize_providers_from_config()
self._connect_widgets_to_service_safe()
self._final_connection_check()
```

#### In `provider_integration_service.py`:
```python
# Before - CRASHES
QtCore.QTimer.singleShot(500, lambda: self.test_provider_connection(provider_name))
QtCore.QTimer.singleShot(100, lambda: self._perform_connection_test(provider_name))

# After - STABLE
self.test_provider_connection(provider_name)
self._perform_connection_test(provider_name)
```

#### In `freecad_ai_workbench.py`:
```python
# Direct widget creation instead of using timer
self._create_dock_widget()
```

## Additional Actions
1. Disabled the broken `3D_Printing_Tools` addon that was causing import errors
2. Fixed the signal definitions to be class attributes as required by PySide2
3. Removed all QTimer.singleShot calls which were causing segmentation faults

## Note on QTimer Issue
The use of QTimer.singleShot with lambda functions during workbench initialization was causing crashes, likely due to:
- Qt event loop not being fully initialized when switching workbenches
- Lambda functions creating closure issues with Qt's signal/slot mechanism
- Timing issues during rapid workbench switching

The solution was to remove all timer-based initialization and perform all setup synchronously.

## Result
- FreeCAD now starts without crashing
- The FreeCAD AI addon loads successfully
- The workbench is registered and available
- No more segmentation faults when switching to the FreeCAD AI workbench
- All provider initialization happens synchronously without timer-related crashes

## Testing
To test the fix:
```bash
export QT_QPA_PLATFORM=xcb
./FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage
```

The addon should now load without errors and the FreeCAD AI workbench should be available in the workbench selector. 
