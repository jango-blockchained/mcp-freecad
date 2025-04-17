#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

source "$SCRIPT_DIR/../.venv/bin/activate"

python "$SCRIPT_DIR/../src/mcp_freecad/server/freecad_mcp_server.py" --debug "$@"
