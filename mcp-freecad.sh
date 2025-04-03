#!/bin/bash

# Directly call the freecad_mcp_server.py with the Python interpreter
cd "$(dirname "$0")"
python3 freecad_mcp_server.py "$@"
