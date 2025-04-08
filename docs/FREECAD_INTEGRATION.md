# FreeCAD Integration Guide

This document outlines how the MCP-FreeCAD server connects to and interacts with FreeCAD using the `FreeCADConnection` class.

## Understanding FreeCAD Integration

FreeCAD has its own embedded Python interpreter and GUI framework. This presents challenges for external applications trying to interact with it:

1.  **Direct Module Import Issues**: FreeCAD's core Python modules (`FreeCAD.so`, `FreeCADGui.so`, etc.) are designed to be initialized by the FreeCAD application itself. Attempting to `import FreeCAD` directly from a standard Python environment often leads to initialization errors or crashes.

2.  **Environment Dependencies**: FreeCAD relies on specific environment variables and library paths being set up correctly, which might not be present in a standard Python environment.

## Connection Methods

The `FreeCADConnection` class (`freecad_connection.py`) provides a unified interface to handle these challenges, offering several connection methods:

### 1. Launcher (Recommended: AppImage Extraction)

- **Method**: `launcher`
- **Mechanism**: This is the **most reliable and recommended** method. It uses `freecad_launcher.py` to launch FreeCAD as a separate process (typically via `AppRun` from an extracted AppImage) and executes commands using `freecad_script.py` running *inside* FreeCAD's own Python environment. Communication happens via standard input/output between the launcher script and the FreeCAD process.
- **Setup**: Works best with an **extracted FreeCAD AppImage**. The `extract_appimage.py` utility script simplifies this:
    1.  Download a FreeCAD AppImage.
    2.  Run `python extract_appimage.py /path/to/FreeCAD.AppImage`. This extracts the AppImage and automatically updates `config.json` to use the `launcher` method with the `use_apprun: true` option, setting necessary paths.
- **How it Works**: `freecad_launcher.py` constructs the command to run `AppRun` (or the FreeCAD executable), passing `freecad_script.py` as an argument. It sends commands (like `create_box`) and parameters as further arguments to `freecad_script.py` and parses the JSON results from its standard output.
- **Advantages**: Avoids module import issues, uses a self-contained environment (with AppImage), ensures correct initialization, generally robust.

### 2. Wrapper

- **Method**: `wrapper`
- **Mechanism**: Uses `freecad_wrapper.py`, which starts `freecad_subprocess.py` as a separate Python 3 process. `freecad_subprocess.py` attempts to `import FreeCAD` directly and communicates with the wrapper via standard input/output pipes.
- **Setup**: Requires a Python 3 environment where `import FreeCAD` works correctly. This might involve setting `PYTHONPATH` and `LD_LIBRARY_PATH` manually or running the MCP server using the Python interpreter from an extracted AppImage.
- **How it Works**: The wrapper sends JSON commands to the subprocess, which executes them using the imported FreeCAD modules and sends back JSON results.
- **Advantages**: Can be simpler than the server method if direct import works in the target environment. Avoids CLI overhead of the bridge method.
- **Disadvantages**: Relies on `import FreeCAD` succeeding in the subprocess environment, which can be tricky to configure correctly without AppRun.

### 3. Socket Server

- **Method**: `server`
- **Mechanism**: Requires a separate `freecad_server.py` script to be running *inside* an active FreeCAD instance. The `FreeCADConnection` class connects to this server via a TCP socket to send commands and receive results.
- **Setup**: Requires manually starting `freecad_server.py` within FreeCAD (e.g., through the FreeCAD Python console or by launching FreeCAD with the script). See `docs/FREECAD_SERVER_SETUP.md`.
- **Configuration**: Set `connection_method: server` in `config.json` and ensure `host` and `port` match the running `freecad_server.py`.
- **Disadvantages**: Requires managing a separate server process within FreeCAD, potentially less stable than the launcher method.

### 4. CLI Bridge (Legacy)

- **Method**: `bridge`
- **Mechanism**: Uses command-line calls to the FreeCAD executable (`freecad`) via `freecad_bridge.py`, attempting to execute small snippets of Python code.
- **Setup**: Requires the FreeCAD executable to be in the system PATH or configured via `path` in `config.json`.
- **Disadvantages**: Can be slow due to process startup overhead for each command, may still encounter environment issues, generally less robust than the other methods.

### 5. Mock Connection

- **Method**: `mock`
- **Mechanism**: A built-in fallback that simulates FreeCAD responses without actually connecting to FreeCAD. Useful for testing the MCP server logic or for development when FreeCAD is unavailable.
- **Setup**: Set `use_mock: true` in the `freecad` section of `config.json`. The `connection_method` is ignored if `use_mock` is true.

## Configuration (`config.json`)

The `freecad` section in `config.json` controls the connection behavior:

```json
{
  "freecad": {
    // General settings
    "path": "/home/user/mcp-freecad/squashfs-root/usr/bin/freecad", // Path to FreeCAD binary (used by bridge, fallback for launcher)
    "auto_connect": false,                // Connection handled internally by MCP server
    "reconnect_on_failure": true,

    // Mock Mode Settings
    "use_mock": false,                   // Set true to force mock mode, overrides connection_method

    // Connection Method Selection
    "connection_method": "launcher",     // Preferred: "launcher", "wrapper", "server", "bridge", or "auto" (null also means auto)

    // Launcher Method Settings (Set automatically by extract_appimage.py)
    "script_path": "/home/user/mcp-freecad/freecad_script.py",    // Path to the script run by the launcher
    "launcher_path": "/home/user/mcp-freecad/freecad_launcher.py", // Path to the launcher helper
    "use_apprun": true,                  // *** Tells launcher to use AppRun ***
    "apprun_path": "/home/user/mcp-freecad/squashfs-root/AppRun", // Path to AppRun (usually in squashfs-root)

    // Server Method Settings
    "host": "localhost",                 // Hostname for the freecad_server.py
    "port": 12345,                       // Port for the freecad_server.py

    // Paths primarily for reference or non-AppRun scenarios
    "python_path": "/home/user/mcp-freecad/squashfs-root/usr/bin/python",
    "module_path": "/home/user/mcp-freecad/squashfs-root/usr/lib/"
  }
}
```
*Note: Replace example paths with your actual absolute paths.*

**Key Configuration Options:**

-   `connection_method`: Determines the primary connection method to try. If set to `null` or `"auto"`, it defaults to the order: `launcher`, `wrapper`, `server`, `bridge`. If `use_mock` is `true`, it overrides this.
-   `use_apprun`: **Crucial for the recommended setup.** When `connection_method` is `launcher`, this tells the launcher to use `AppRun` from the `apprun_path` directory instead of the standard `path` executable.
-   `apprun_path`: The path to the `AppRun` executable itself, typically within the extracted AppImage directory (`squashfs-root`). Set automatically by `extract_appimage.py`.
-   `script_path`, `launcher_path`: Paths to helper scripts used by the launcher method. Should be absolute paths.
-   `path`: Path to the FreeCAD binary. Primarily used by the `bridge` method, but also as a fallback reference.

## Summary

For the most stable and reliable connection, use the **Launcher method with an extracted FreeCAD AppImage**. The `extract_appimage.py` script automates this setup process, configuring `config.json` appropriately. 
