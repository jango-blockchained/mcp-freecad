#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Activate the virtual environment
source "$SCRIPT_DIR/mcp_venv/bin/activate"

# Start the MCP server with debug mode
python "$SCRIPT_DIR/freecad_mcp_server.py" --debug "$@"
