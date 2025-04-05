#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Force X11 backend to avoid Wayland issues
export QT_QPA_PLATFORM=xcb

# Run the FreeCAD AppRun with the proper options
# Pass the script path directly without --console flag
"$SCRIPT_DIR/squashfs-root/AppRun" "$SCRIPT_DIR/freecad_mcp_server.py" -- "$@"
