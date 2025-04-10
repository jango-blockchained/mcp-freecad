#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Get the repository root (one level up from scripts)
REPO_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"

# Force headless mode
export QT_QPA_PLATFORM=offscreen
export DISPLAY=""  # Empty display to prevent X11 connection
export FREECAD_CONSOLE=1  # Force console mode for FreeCAD
export PYTHONNOUSERSITE=1  # Control Python initialization

# Debug message
echo "Starting MCP server in headless mode from $REPO_ROOT"

# Check if AppImage is extracted
if [ -d "$REPO_ROOT/squashfs-root" ]; then
    # Looking for Python in the AppImage
    PYTHON_EXEC="$REPO_ROOT/squashfs-root/usr/bin/python"

    if [ -x "$PYTHON_EXEC" ]; then
        echo "Using Python from extracted AppImage"
        # Set up Python environment for FreeCAD modules
        # Prepend the project source directory to find the mcp_freecad package
        export PYTHONPATH="$REPO_ROOT/src:$PYTHONPATH"
        export PYTHONPATH="$REPO_ROOT/squashfs-root/usr/lib:$PYTHONPATH"
        # Add additional module paths if they exist
        if [ -d "$REPO_ROOT/squashfs-root/usr/lib/python3.1" ]; then
            export PYTHONPATH="$REPO_ROOT/squashfs-root/usr/lib/python3.1:$PYTHONPATH"
        fi
        if [ -d "$REPO_ROOT/squashfs-root/usr/lib/python3.11" ]; then
            export PYTHONPATH="$REPO_ROOT/squashfs-root/usr/lib/python3.11:$PYTHONPATH"
        fi
        if [ -d "$REPO_ROOT/squashfs-root/usr/Ext" ]; then
            export PYTHONPATH="$REPO_ROOT/squashfs-root/usr/Ext:$PYTHONPATH"
        fi
        # Run with Python directly
        cd "$REPO_ROOT"
        echo "Running MCP server with command: $PYTHON_EXEC -m mcp_freecad.server.freecad_mcp_server $@"
        "$PYTHON_EXEC" -m mcp_freecad.server.freecad_mcp_server "$@"
    else
        echo "Python not found in AppImage, falling back to system Python"
        cd "$REPO_ROOT"
        echo "Running MCP server with command: python3 -m mcp_freecad.server.freecad_mcp_server $@"
        python3 -m mcp_freecad.server.freecad_mcp_server "$@"
    fi
else
    echo "AppImage not extracted. Using system Python"
    # Fallback to running with system Python
    cd "$REPO_ROOT"
    echo "Running MCP server with command: python3 -m mcp_freecad.server.freecad_mcp_server $@"
    python3 -m mcp_freecad.server.freecad_mcp_server "$@"
fi
