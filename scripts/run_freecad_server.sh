#!/bin/bash

# Wrapper script to run freecad_server.py with the correct environment

# Get the absolute path to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
CONNECT_MODE="--connect"
for arg in "$@"; do
    if [[ "$arg" == "--no-connect" ]]; then
        CONNECT_MODE=""
        # Remove this argument for forwarding to server
        set -- "${@//--no-connect/}"
    fi
done

# Check if config.json exists
if [[ -f "config.json" ]]; then
    # Get FreeCAD binary path from config.json
    FREECAD_PATH=$(grep -o "\"path\": \"[^\"]*\"" config.json | head -1 | cut -d "\"" -f 4)
    PYTHON_PATH=$(grep -o "\"python_path\": \"[^\"]*\"" config.json | head -1 | cut -d "\"" -f 4)
    
    if [[ -n "$FREECAD_PATH" && -f "$FREECAD_PATH" ]]; then
        echo "Found FreeCAD path in config.json: $FREECAD_PATH"
        
        # Extract base directory
        FREECAD_BASE=$(dirname "$(dirname "$FREECAD_PATH")")
        
        # Set up environment
        if [[ -n "$PYTHON_PATH" && -f "$PYTHON_PATH" ]]; then
            echo "Using Python from config: $PYTHON_PATH"
            export PATH="$(dirname "$PYTHON_PATH"):$PATH"
            
            # If this is a Debian/Ubuntu-based FreeCAD with squashfs structure
            if [[ -d "$FREECAD_BASE/usr/lib/python3" ]]; then
                echo "Found Python modules in $FREECAD_BASE/usr/lib/python3"
                export PYTHONPATH="$FREECAD_BASE/usr/lib/python3/dist-packages:$PYTHONPATH"
            fi
            
            # Add more potential module paths
            if [[ -d "$FREECAD_BASE/lib" ]]; then
                export PYTHONPATH="$FREECAD_BASE/lib:$PYTHONPATH"
            fi
            
            if [[ -d "$FREECAD_BASE/usr/lib" ]]; then
                export PYTHONPATH="$FREECAD_BASE/usr/lib:$PYTHONPATH"
            fi
            
            echo "PYTHONPATH set to: $PYTHONPATH"
            
            # Run the server using the specified Python
            echo "Starting server with $PYTHON_PATH $CONNECT_MODE"
            exec "$PYTHON_PATH" ./freecad_server.py $CONNECT_MODE "$@"
        else
            echo "No Python path in config, trying to run with FreeCAD"
            # Try to run using FreeCAD as the Python interpreter
            echo "Starting server with $FREECAD_PATH $CONNECT_MODE"
            exec "$FREECAD_PATH" ./freecad_server.py $CONNECT_MODE "$@"
        fi
    fi
fi

# Fallback to system Python if we couldn't find FreeCAD or its not properly configured
echo "Using system Python $CONNECT_MODE"
exec python3 ./freecad_server.py $CONNECT_MODE "$@"
