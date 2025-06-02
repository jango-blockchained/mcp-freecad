# Python Interpreter Setup for FreeCAD Integration

This document explains how to set up your Python environment to interact with FreeCAD, particularly when using the recommended AppImage-based connection method for the MCP-FreeCAD project.

## The Challenge: FreeCAD's Embedded Python

FreeCAD comes with its own embedded Python interpreter and modules (like `FreeCAD`, `Part`, `FreeCADGui`). These modules are designed to be initialized and run by the FreeCAD application itself. Attempting to directly `import FreeCAD` from your system's standard Python installation will usually fail due to initialization errors and missing dependencies.

## Recommended Solution: AppImage Extraction + Launcher

The most reliable way to interact with FreeCAD is by using its own environment. The MCP-FreeCAD project facilitates this through the **AppImage extraction and Launcher method**:

1.  **Download a FreeCAD AppImage**: Get the latest stable or weekly build AppImage from the [FreeCAD releases page](https://github.com/FreeCAD/FreeCAD/releases).
2.  **Extract the AppImage**: Use the provided `extract_appimage.py` script:
    ```bash
    cd /path/to/mcp-freecad
    ./extract_appimage.py /path/to/FreeCAD_*.AppImage
    ```
    This script:
    *   Extracts the AppImage to a `squashfs-root` directory.
    *   Updates your `config.json` to use the `launcher` connection method via `AppRun` from the extracted directory.
    *   Ensures all FreeCAD dependencies and Python modules are contained within `squashfs-root`.

3.  **How it Works**: When you run the MCP server (`python src/mcp_freecad/server/freecad_mcp_server.py`), the `FreeCADConnection` uses the `FreeCADLauncher`. The launcher executes the `AppRun` script within the `squashfs-root` directory. `AppRun` correctly sets up the FreeCAD environment (paths, libraries) and then runs my `freecad_launcher_script.py` using FreeCAD's *internal* Python interpreter. All communication happens via standard input/output.

**Why this is Recommended:**

*   **No Import Errors**: I don't attempt to import FreeCAD modules into my main Python environment.
*   **Correct Environment**: FreeCAD runs in the exact environment it was packaged with.
*   **Dependency Isolation**: All dependencies are bundled within the extracted AppImage.
*   **Simplicity**: The `extract_appimage.py` script automates the setup.

**With this recommended setup, you generally don't need to manually configure your Python interpreter or `PYTHONPATH` for the MCP server itself**, as the interaction happens via the subprocess launched by `AppRun`.

## Alternative: Creating a Dev Environment (For Tool Development/Debugging)

While the AppRun method is best for *running* the MCP server, if you are developing custom tools or need to debug scripts *intended to run inside FreeCAD*, you might want a development environment where you can directly import FreeCAD modules.

**Warning**: This is more complex and potentially less stable than using the AppRun method for the server itself.

### Steps to Create a FreeCAD-based Virtual Environment

1.  **Extract the AppImage**: Follow steps 1 & 2 from the recommended solution above.

2.  **Identify FreeCAD's Python**: Locate the Python executable within the extracted directory (e.g., `./squashfs-root/usr/bin/python`).

3.  **Create Virtual Environment**: Navigate to your project directory and create a venv using FreeCAD's Python:
    ```bash
    cd /path/to/mcp-freecad
    ./squashfs-root/usr/bin/python -m venv .venv-freecad --system-site-packages
    ```
    *   **Crucial**: Use the Python *from the extracted AppImage*.
    *   **Crucial**: Use `--system-site-packages` to allow access to FreeCAD modules already present in the AppImage's Python environment.

4.  **Activate**: `source .venv-freecad/bin/activate`

5.  **Verify**: Check if you can import FreeCAD:
    ```bash
    python -c "import FreeCAD; import Part; import FreeCADGui; print(f'Successfully imported FreeCAD {FreeCAD.Version()}')"
    ```
    *Note: `FreeCADGui` might fail if you don't have a graphical environment (X11/Wayland) set up correctly, but `FreeCAD` and `Part` should import.* 

6.  **Install Dependencies**: Install your project's *other* dependencies into this venv:
    ```bash
    pip install -r requirements.txt
    ```

### Using the Dev Environment

*   Activate this `.venv-freecad` whenever you want to run scripts that *directly* `import FreeCAD` for testing or development purposes.
*   Your IDE (like VSCode) can be configured to use this virtual environment's interpreter for better code completion and debugging of FreeCAD-specific code.
*   **Remember**: This setup is primarily for *development* convenience. For *running* the MCP server, stick to the AppRun method configured by `extract_appimage.py`, which doesn't require activating this specific venv.

## Troubleshooting

*   **`extract_appimage.py` Fails**: Ensure the AppImage path is correct and you have execution permissions. Check for sufficient disk space.
*   **AppRun Method Fails**: Check the `apprun_path` in `config.json` points to the correct `squashfs-root` directory. Look for errors in the MCP server logs when it tries to connect.
*   **Dev Environment Import Errors**: Make sure you created the venv using the *correct* Python from `squashfs-root` and included `--system-site-packages`. Ensure the venv is activated.
