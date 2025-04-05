#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Get the repository root (one level up from scripts)
REPO_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Force X11 backend to avoid Wayland issues
export QT_QPA_PLATFORM=xcb

# Control Python initialization to prevent "PyImport_AppendInittab after Py_Initialize" errors
export PYTHONNOUSERSITE=1

# Set PYTHONPATH for FreeCAD modules without loading GUI
export PYTHONPATH="$REPO_ROOT/squashfs-root/usr/lib:$PYTHONPATH"

# Check if AppImage is extracted
if [ -d "$REPO_ROOT/squashfs-root" ]; then
    echo "Using AppRun from extracted AppImage"
    # Run the FreeCAD AppRun with the proper options in console mode
    # Pass the script path with the --console flag to prevent GUI
    "$REPO_ROOT/squashfs-root/AppRun" --console "$REPO_ROOT/freecad_mcp_server.py" -- "$@"
else
    echo "AppImage not extracted. Trying to run with system Python"
    # Fallback to running with system Python
    cd "$REPO_ROOT"
    python3 "$REPO_ROOT/freecad_mcp_server.py" "$@"
fi
