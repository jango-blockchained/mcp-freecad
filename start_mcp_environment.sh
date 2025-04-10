#!/bin/bash
# Script to start FreeCAD with the MCP server environment
# This script requires Python 3.11 for compatibility with FreeCAD

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Setting up MCP-FreeCAD environment..."

# Check for Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "ERROR: Python 3.11 is required but not found"
    echo "Please install Python 3.11 with: sudo apt-get install python3.11 python3.11-venv python3.11-dev"
    exit 1
fi

# Make sure virtual environment exists and packages are installed
if [ ! -d ~/freecad-py311-venv ]; then
    echo "Creating Python 3.11 virtual environment..."
    python3.11 -m venv ~/freecad-py311-venv
    source ~/freecad-py311-venv/bin/activate
    pip install -e .
else
    source ~/freecad-py311-venv/bin/activate
fi

# Set environment variables for server operation
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/src:$PYTHONPATH"

# Verify FreeCAD access
if [ ! -e "$SCRIPT_DIR/squashfs-root/usr/bin/freecad" ]; then
    echo "ERROR: FreeCAD executable not found at $SCRIPT_DIR/squashfs-root/usr/bin/freecad"
    echo "Please check your FreeCAD installation"
    exit 1
fi

# Check if we need to restart servers
restart=false
if pgrep -f "freecad_server.py" > /dev/null; then
    echo "Stopping existing FreeCAD server..."
    pkill -f "freecad_server.py" || true
    restart=true
fi

if pgrep -f "freecad_mcp_server.py" > /dev/null; then
    echo "Stopping existing MCP server..."
    pkill -f "freecad_mcp_server.py" || true
    restart=true
fi

# Give a moment for processes to terminate
if [ "$restart" = true ]; then
    sleep 2
fi

# Start the FreeCAD server (no mock mode)
echo "Starting FreeCAD server..."
python3.11 "$SCRIPT_DIR/freecad_server.py" --debug > freecad_server_stdout.log 2> freecad_server_stderr.log &
FREECAD_SERVER_PID=$!
echo "FreeCAD server started with PID: $FREECAD_SERVER_PID"

# Wait for the FreeCAD server to start up
sleep 2

# Start the MCP server
echo "Starting MCP server..."
python3.11 "$SCRIPT_DIR/src/mcp_freecad/server/freecad_mcp_server.py" > mcp_server_stdout.log 2> mcp_server_stderr.log &
MCP_SERVER_PID=$!
echo "MCP server started with PID: $MCP_SERVER_PID"

echo "Both servers started successfully!"
echo "You can monitor logs in:"
echo "  - freecad_server_stdout.log"
echo "  - freecad_server_stderr.log"
echo "  - mcp_server_stdout.log"
echo "  - mcp_server_stderr.log"
echo ""
echo "To connect to the servers:"
echo "  - FreeCAD server: localhost:12345"
echo "  - MCP server: See the MCP server logs for details"
echo ""
echo "To stop the servers:"
echo "  - Run: kill $FREECAD_SERVER_PID $MCP_SERVER_PID"
echo "  - Or press Ctrl+C now to stop both"

# Wait for both server processes to terminate
wait
