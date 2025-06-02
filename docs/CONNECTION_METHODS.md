# FreeCAD Connection Methods Guide

This document provides detailed information about the different connection methods used by MCP-FreeCAD to communicate with FreeCAD, their requirements, configuration, and troubleshooting steps.

## Overview

MCP-FreeCAD supports multiple methods to connect to FreeCAD:

1. **Launcher Mode** (Recommended) - Uses AppRun from an extracted AppImage to execute FreeCAD with my script
2. **Wrapper Mode** - Runs FreeCAD in a subprocess with direct module imports
3. **Server Mode** - Connects to a running FreeCAD instance via sockets
4. **RPC Mode** - Connects to a running FreeCAD instance via XML-RPC
5. **Bridge Mode** - Uses CLI-based communication with the FreeCAD executable
6. **Mock Mode** - Simulates FreeCAD for testing when no real FreeCAD is available

The system will try these methods in the order listed above by default, unless a specific method is configured.

## Connection Method Requirements

### 1. Launcher Mode (Recommended)

**Requirements:**
- FreeCAD executable or AppRun from an extracted AppImage
- `freecad_launcher_script.py` in the same directory as `freecad_connection_launcher.py`

**Configuration:**
```json
{
  "freecad": {
    "connection_method": "launcher",
    "freecad_path": "/path/to/FreeCAD/executable",
    "use_apprun": true,  // Set to true if using AppRun from AppImage
    "apprun_path": "/path/to/extracted/AppImage"  // Optional, defaults to freecad_path
  }
}
```

**Troubleshooting:**
- Ensure the AppImage is properly extracted if using AppRun mode
- Check that `freecad_launcher_script.py` exists and is accessible
- Verify the FreeCAD or AppRun path is correct and the file exists
- Check console output for Python errors when executing the script

### 2. Wrapper Mode

**Requirements:**
- Python environment where `import FreeCAD` works
- `freecad_subprocess.py` in the same directory as `freecad_connection_wrapper.py`

**Configuration:**
```json
{
  "freecad": {
    "connection_method": "wrapper"
  }
}
```

**Troubleshooting:**
- Ensure FreeCAD modules are in the Python path
- Check for any import errors in the subprocess output
- Verify that `freecad_subprocess.py` exists and is accessible
- For GUI operations, X11 forwarding may be required

### 3. Server Mode

**Requirements:**
- Running `freecad_socket_server.py` inside a FreeCAD instance
- Network access to the server (typically localhost)

**Configuration:**
```json
{
  "freecad": {
    "connection_method": "server",
    "host": "localhost",
    "port": 12345
  }
}
```

**Troubleshooting:**
- Ensure `freecad_socket_server.py` is running inside FreeCAD
- Check that the host and port match the server configuration
- Verify no firewall is blocking the connection
- Check the server logs for any connection errors

### 4. RPC Mode

**Requirements:**
- Running XML-RPC server inside a FreeCAD instance (similar to the FreeCADMCP addon)
- Network access to the server (typically localhost)

**Configuration:**
```json
{
  "freecad": {
    "connection_method": "rpc",
    "host": "localhost",
    "rpc_port": 9875
  }
}
```

**Troubleshooting:**
- Ensure the XML-RPC server is running inside FreeCAD
- Check that the host and rpc_port match the server configuration
- Verify no firewall is blocking the connection
- Check the server logs for any connection errors
- This method is compatible with the FreeCADMCP addon's RPC server

### 5. Bridge Mode

**Requirements:**
- FreeCAD executable in the system PATH or configured path
- CLI access to FreeCAD

**Configuration:**
```json
{
  "freecad": {
    "connection_method": "bridge",
    "freecad_path": "/path/to/freecad"
  }
}
```

**Troubleshooting:**
- Ensure FreeCAD is installed and accessible via command line
- Check that the FreeCAD path is correct
- Verify FreeCAD version (should be 0.19 or newer)
- This method can be slower than others due to process overhead

### 6. Mock Mode

**Requirements:**
- None (fallback mode)

**Configuration:**
```json
{
  "freecad": {
    "connection_method": "mock",
    "use_mock": true
  }
}
```

**Troubleshooting:**
- This is a simulation mode only - no real FreeCAD operations will be performed
- Useful for testing the MCP interface without FreeCAD
- All operations will return mock data

## Auto Selection

By default, MCP-FreeCAD will try each method in order until one succeeds. You can configure the preferred method in the config.json file:

```json
{
  "freecad": {
    "connection_method": "auto"  // Will try all methods in recommended order
  }
}
```

The default order is: RPC > Server > Bridge > Wrapper > Launcher > Mock

## Testing Connection Methods

Use the `tests/test_connection_methods.py` script to test different connection methods:

```bash
# Test all methods


# Test a specific method
python tests/test_connection_methods.py --method launcher

# Test auto-selection
python tests/test_connection_methods.py --method auto

# Specify FreeCAD path
python tests/test_connection_methods.py --method launcher --freecad-path /path/to/freecad
```

## Common Issues and Solutions

### FreeCAD Import Errors

If you see errors related to importing FreeCAD modules:

1. Ensure FreeCAD is properly installed
2. Try using the launcher method with an extracted AppImage
3. Check your Python path includes FreeCAD modules
4. If using wrapper mode, verify the Python environment can import FreeCAD

### Connection Timeouts

If connections are timing out:

1. For server mode, ensure the server script is running inside FreeCAD
2. Check firewall settings
3. Verify the host and port settings
4. Increase timeout values if needed

### Subprocess Errors

If the wrapper method fails with subprocess errors:

1. Check if the subprocess.py script can run independently
2. Ensure the Python environment can import FreeCAD
3. Look for error messages in the subprocess stderr output
4. Try running with debug logs enabled

## Recommended Setup

The recommended setup is to use the **launcher** method with an extracted AppImage:

1. Download the FreeCAD AppImage
2. Extract it using `./FreeCAD-xxx.AppImage --appimage-extract`
3. Configure MCP-FreeCAD to use the launcher method with:
   ```json
   {
     "freecad": {
       "connection_method": "launcher",
       "use_apprun": true,
       "apprun_path": "/path/to/squashfs-root"
     }
   }
   ```

This method provides the best compatibility across different environments. 
