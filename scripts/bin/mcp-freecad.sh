#!/bin/bash

# Get the script directory and repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Change to the repository root directory
cd "$REPO_ROOT"

# Call the freecad_mcp_server.py with the Python interpreter
python3 "$REPO_ROOT/freecad_mcp_server.py" "$@"
