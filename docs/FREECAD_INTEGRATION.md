# FreeCAD Integration Guide

This document outlines how the MCP-FreeCAD server connects to and interacts with FreeCAD.

## Understanding FreeCAD Integration

FreeCAD has its own embedded Python interpreter and GUI framework. This presents challenges for external applications trying to interact with it:

1.  **Direct Module Import Issues**: FreeCAD's core Python modules (`FreeCAD.so`, `FreeCADGui.so`, etc.) are designed to be initialized by the FreeCAD application itself. Attempting to `import FreeCAD` directly from a standard Python environment often leads to initialization errors or crashes.
2.  **Environment Dependencies**: FreeCAD relies on specific environment variables and library paths being set up correctly, which might not be present in a standard Python environment.

## Connection Methods

The `FreeCADConnection` class (`freecad_connection.py`) provides a unified interface to handle these challenges, offering several connection methods:

### 1. Launcher (Recommended: AppImage Extraction)

- **Method**: `launcher`
- **Mechanism**: This is the **most reliable and recommended** method. It launches FreeCAD as a separate process using a specific script (`freecad_script.py`) executed within FreeCAD's own Python environment. Communication happens via standard input/output between the MCP server and the FreeCAD process.
- **Setup**: It works best when using an **extracted FreeCAD AppImage**. The `extract_appimage.py` utility script simplifies this setup:
    1.  Download a FreeCAD AppImage.
    2.  Run `./extract_appimage.py /path/to/FreeCAD.AppImage`. This extracts the AppImage and automatically updates `config.json` to use the `launcher` method with the `use_apprun: true` option, pointing `apprun_path` to the extraction directory.
- **How it Works**: The `FreeCADLauncher` class (`freecad_launcher.py`) handles constructing the command to run FreeCAD (or `AppRun` from the extracted AppImage) with the `--run-script` argument, passing commands and parameters to `freecad_script.py` and parsing the JSON results from its standard output.
- **Advantages**: Avoids module import issues, uses a self-contained environment (with AppImage), ensures correct initialization.

### 2. Socket Server

- **Method**: `server`
- **Mechanism**: Requires a separate `freecad_server.py` script to be running *inside* an active FreeCAD instance. The `FreeCADConnection` class connects to this server via a TCP socket to send commands and receive results.
- **Setup**: Requires manually starting `freecad_server.py` within FreeCAD (e.g., through the FreeCAD Python console or by launching FreeCAD with the script).
- **Configuration**: Set `connection_method: server` in `config.json` and ensure `host` and `port` match the running `freecad_server.py`.
- **Disadvantages**: Requires managing a separate server process within FreeCAD, potentially less stable than the launcher method.

### 3. CLI Bridge (Legacy)

- **Method**: `bridge`
- **Mechanism**: Uses command-line calls to the FreeCAD executable, attempting to execute small snippets of Python code. Relies on `freecad_bridge.py`.
- **Setup**: Requires the FreeCAD executable to be in the system PATH or configured via `freecad_path` in `config.json`.
- **Disadvantages**: Can be slow due to process startup overhead for each command, may still encounter environment issues, generally less robust than the launcher or server methods.

### 4. Mock Connection

- **Method**: `mock`
- **Mechanism**: A built-in fallback that simulates FreeCAD responses without actually connecting to FreeCAD. Useful for testing the MCP server logic or for development when FreeCAD is unavailable.
- **Setup**: Set `use_mock: true` in the `freecad` section of `config.json`. The `connection_method` is ignored if `use_mock` is true.

## Configuration (`config.json`)

The `freecad` section in `config.json` controls the connection behavior:

```json
{
  "freecad": {
    // General settings
    "path": "/usr/bin/freecad",           // Path to FreeCAD executable (used by bridge, fallback for launcher)
    "auto_connect": true,                // Attempt connection on startup
    "reconnect_on_failure": true,        // Attempt to reconnect if connection fails
    
    // Mock Mode Settings
    "use_mock": false,                   // Set to true to force mock mode
    
    // Connection Method Selection
    "connection_method": "launcher",     // Preferred method: "launcher", "server", "bridge", or null/auto
    
    // Launcher Method Settings
    "script_path": "freecad_script.py",    // Path to the script run by the launcher
    "launcher_path": "freecad_launcher.py", // Path to the launcher helper
    "use_apprun": true,                  // Set to true by extract_appimage.py
    "apprun_path": "/path/to/squashfs-root", // Path to extracted AppImage dir (set by extract_appimage.py)

    // Server Method Settings
    "host": "localhost",                 // Hostname for the freecad_server.py
    "port": 12345,                       // Port for the freecad_server.py
    
    // Legacy/Unused (kept for potential future use or reference)
    "python_path": "/usr/bin/python3", 
    "module_path": "/usr/lib/freecad-python3/lib"
  }
}
```

**Key Configuration Options:**

-   `connection_method`: Determines the primary connection method to try. If set to `null` or omitted, it defaults to the order: `launcher`, `server`, `bridge`. If `use_mock` is `true`, it overrides this.
-   `use_apprun`: When `connection_method` is `launcher`, this tells the launcher to use `AppRun` from the `apprun_path` directory instead of the standard `path` executable.
-   `apprun_path`: The path to the directory containing the extracted AppImage (`squashfs-root`). Set automatically by `extract_appimage.py`.

## Summary

For the most stable and reliable connection, use the **Launcher method with an extracted FreeCAD AppImage**. The `extract_appimage.py` script automates this setup process. 
