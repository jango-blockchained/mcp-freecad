#!/bin/bash

# Script to start FreeCAD with server enabled
echo "Starting FreeCAD with integrated server..."

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Launch FreeCAD with the macro
freecad --run-script="$SCRIPT_DIR/start_server.py"
