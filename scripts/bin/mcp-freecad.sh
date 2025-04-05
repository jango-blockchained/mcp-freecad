#!/bin/bash

# Get the script directory and repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Control Python initialization to prevent "PyImport_AppendInittab after Py_Initialize" errors
export PYTHONNOUSERSITE=1

# Use the start_mcp_server.sh script which has proper initialization
"$REPO_ROOT/scripts/start_mcp_server.sh" "$@"
