#!/bin/bash
# Script to start FreeCAD with the MCP server environment
# This script requires Python 3.11 for compatibility with FreeCAD

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Setting up MCP-FreeCAD environment..."

# Check for Python 3.11
PYTHON_CMD=""

check_python() {
    local cmd=$1
    if command -v $cmd &> /dev/null; then
        local version=$($cmd --version 2>&1 | awk '{print $2}')
        if [[ $version == 3.11* ]]; then
            PYTHON_CMD=$cmd
            echo "Found compatible Python: $cmd (version $version)"
            return 0
        else
            echo "Found $cmd, but version $version is not compatible (need 3.11.x)"
        fi
    fi
    return 1
}

# Try different possible Python 3.11 commands
if check_python python3.11; then
    :  # Already set PYTHON_CMD
elif check_python python3; then
    :  # Already set PYTHON_CMD if it's 3.11.x
else
    # Check other possible locations
    if [ -e "$SCRIPT_DIR/squashfs-root/usr/bin/python" ]; then
        if check_python "$SCRIPT_DIR/squashfs-root/usr/bin/python"; then
            :  # Already set PYTHON_CMD
        fi
    fi

    if [ -z "$PYTHON_CMD" ] && [ -d "$HOME/.pyenv/versions/3.11.0/bin" ]; then
        if check_python "$HOME/.pyenv/versions/3.11.0/bin/python"; then
            :  # Already set PYTHON_CMD
        fi
    fi

    # Check if we have any virtual environment with Python 3.11
    if [ -z "$PYTHON_CMD" ] && [ -d "$HOME/freecad-py-venv/bin" ]; then
        if check_python "$HOME/freecad-py-venv/bin/python"; then
            :  # Already set PYTHON_CMD
        fi
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "ERROR: Python 3.11 is required but not found"
    echo ""
    echo "Please install Python 3.11 using one of these methods:"
    echo ""
    echo "1. Using deadsnakes PPA (Ubuntu):"
    echo "   sudo add-apt-repository ppa:deadsnakes/ppa"
    echo "   sudo apt update"
    echo "   sudo apt install python3.11 python3.11-venv python3.11-dev"
    echo ""
    echo "2. Using pyenv:"
    echo "   curl https://pyenv.run | bash"
    echo "   # Add pyenv to your shell configuration"
    echo "   pyenv install 3.11.0"
    echo ""
    echo "3. Use FreeCAD's built-in Python:"
    echo "   ./squashfs-root/usr/bin/python -m venv freecad-py-venv"
    echo ""
    echo "For detailed instructions, see BRANCH_INFO.md"
    exit 1
fi

# Make sure virtual environment exists and packages are installed
VENV_DIR="$HOME/freecad-py311-venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python 3.11 virtual environment at $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install -e .
else
    source "$VENV_DIR/bin/activate"
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

if pgrep -f "src/mcp_freecad/server/freecad_mcp_server.py" > /dev/null; then
    echo "Stopping existing MCP server..."
    pkill -f "src/mcp_freecad/server/freecad_mcp_server.py" || true
    restart=true
fi

# Give a moment for processes to terminate
if [ "$restart" = true ]; then
    sleep 2
fi

# Start the FreeCAD server (no mock mode)
echo "Starting FreeCAD server..."
$PYTHON_CMD "$SCRIPT_DIR/freecad_server.py" --debug > freecad_server_stdout.log 2> freecad_server_stderr.log &
FREECAD_SERVER_PID=$!
echo "FreeCAD server started with PID: $FREECAD_SERVER_PID"

# Wait for the FreeCAD server to start up
sleep 2

# Start the MCP server
echo "Starting MCP server..."
$PYTHON_CMD "$SCRIPT_DIR/src/mcp_freecad/server/freecad_mcp_server.py" > mcp_server_stdout.log 2> mcp_server_stderr.log &
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
