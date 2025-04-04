# Python Interpreter Setup for FreeCAD Integration

This document explains how the Python interpreter is configured and used with FreeCAD in the MCP-FreeCAD project, particularly focusing on the AppImage extraction method.

## Overview

The MCP-FreeCAD project requires access to FreeCAD's Python modules, specifically `FreeCAD` and `FreeCADGui`, to interact with the CAD application. Since these modules are part of FreeCAD's custom Python environment, special configuration is needed to access them correctly.

## AppImage Extraction Method

### What is an AppImage?

AppImage is a format for distributing portable software on Linux without requiring superuser permissions to install. It contains the application and all its dependencies.

### Extraction Process

1. Download the FreeCAD AppImage from the official FreeCAD website.
2. Make the AppImage executable:
   ```bash
   chmod +x FreeCAD-*.AppImage
   ```
3. Extract the AppImage content without running it:
   ```bash
   ./FreeCAD-*.AppImage --appimage-extract
   ```
4. This creates a `squashfs-root` directory containing all FreeCAD files, including the Python interpreter and modules.

## Configuration in MCP-FreeCAD

The project's `config.json` file contains critical settings for the Python interpreter:

```json
"freecad": {
  "path": "/usr/bin/freecad",
  "python_path": "./squashfs-root/usr/bin/python",
  ...
}
```

Key configuration items:
- `path`: Path to the FreeCAD executable
- `python_path`: Path to the Python interpreter within the extracted AppImage

## How the Python Interpreter is Used

The project uses the specified Python interpreter in the following ways:

1. **Direct Execution**: The `run_freecad_server.sh` script reads these settings from `config.json` and uses them to run Python scripts with the correct environment.

2. **Environment Setup**: The script sets up the `PYTHONPATH` to include necessary directories within the extracted AppImage:
   ```bash
   export PYTHONPATH="$FREECAD_BASE/usr/lib/python3/dist-packages:$PYTHONPATH"
   ```

3. **Fallback Mechanism**: If the configured paths are not accessible, the system falls back to using the system Python or directly invoking FreeCAD as a Python interpreter.

## Why This Approach Matters

This setup is crucial because:

1. **Module Access**: It ensures access to FreeCAD and FreeCADGui modules, which are not available in standard Python installations.

2. **Version Consistency**: Using the bundled Python interpreter ensures compatibility with the FreeCAD version.

3. **Dependency Management**: The extracted AppImage includes all necessary dependencies, avoiding complex manual installations.

## Troubleshooting

If you encounter issues with the Python interpreter:

1. Verify that the paths in `config.json` point to valid locations.
2. Check that the extracted AppImage structure matches the expected paths.
3. Ensure proper permissions for both the FreeCAD executable and Python interpreter.
4. Use the `--debug` flag when running scripts for more verbose output.

## Example: Custom Script Execution

To run a custom script with the FreeCAD Python environment:

```bash
./squashfs-root/usr/bin/python my_freecad_script.py
```

Or, using the run_freecad_server.sh script (which handles environment setup):

```bash
./run_freecad_server.sh --script=my_freecad_script.py
```

## Setting Up a Virtual Environment with FreeCAD's Python

For consistent development and to ensure the correct Python interpreter is always used, you can create a virtual environment using the FreeCAD Python interpreter from the extracted AppImage:

### Steps to Create a FreeCAD-based Virtual Environment

1. Navigate to your project directory:
   ```bash
   cd /path/to/mcp-freecad
   ```

2. Create a virtual environment using the Python from squashfs:
   ```bash
   ./squashfs-root/usr/bin/python -m venv .venv-freecad --system-site-packages
   ```
   The `--system-site-packages` flag is crucial as it allows the virtual environment to access the FreeCAD modules from the AppImage's Python.

3. Activate the virtual environment:
   ```bash
   source .venv-freecad/bin/activate
   ```

4. Verify FreeCAD modules are accessible:
   ```bash
   python -c "import FreeCAD; import FreeCADGui; print('FreeCAD version:', FreeCAD.Version())"
   ```

5. Install any additional project dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Benefits of This Approach

- **Consistency**: Always uses the correct Python interpreter with access to FreeCAD modules
- **Isolation**: Keeps project dependencies separate from system Python 
- **Reproducibility**: Easier for other developers to set up the same environment
- **IDE Integration**: Better integration with IDEs like VSCode for code completion and type hints
- **Simplified Development Workflow**: No need to constantly specify the Python path

### Updating Scripts to Use the Virtual Environment

Update your development and deployment scripts to activate the virtual environment:

```bash
#!/bin/bash
# Activate FreeCAD virtual environment
source .venv-freecad/bin/activate

# Run your scripts
python ./your_script.py
```

This ensures that all development and execution consistently use the correct Python interpreter with access to the FreeCAD modules. 
