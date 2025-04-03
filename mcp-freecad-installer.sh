#!/bin/bash
# MCP-FreeCAD Installer and Runner
# This script checks out the MCP-FreeCAD repository if needed, and runs the MCP server

set -e  # Exit on error

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required commands
if ! command_exists git; then
    echo "Error: git is required but not installed. Please install git and try again."
    exit 1
fi

if ! command_exists python3; then
    echo "Error: python3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Repository URL and local directory
REPO_URL="https://github.com/user/mcp-freecad.git"  # Replace with your actual repository URL
INSTALL_DIR="$HOME/.mcp-freecad"

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Creating installation directory at $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"
fi

# Clone or update the repository
if [ ! -d "$INSTALL_DIR/.git" ]; then
    echo "Cloning MCP-FreeCAD repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
else
    echo "Updating MCP-FreeCAD repository..."
    cd "$INSTALL_DIR"
    git pull
fi

# Set up Python virtual environment if it doesn't exist
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    echo "Setting up Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Function to run the MCP server
run_mcp_server() {
    echo "Starting MCP-FreeCAD server..."
    python3 freecad_mcp_server.py "$@"
}

# Run the MCP server
run_mcp_server "$@"
