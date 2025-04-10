#!/bin/bash
# MCP-FreeCAD Installer and Runner
# This script checks out the MCP-FreeCAD repository if needed, sets up the environment,
# optionally downloads the latest FreeCAD AppImage, and runs the MCP server.

set -e  # Exit on error

# --- Configuration ---
REPO_URL="https://github.com/jango-blockchained/mcp-freecad.git"
INSTALL_DIR="$HOME/.mcp-freecad"
DOWNLOAD_SCRIPT="download_appimage.py"
REQUIREMENTS_FILE="requirements.txt"
VENV_DIR=".venv"
SERVER_SCRIPT="src/mcp_freecad/server/freecad_mcp_server.py"
# ---------------------

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

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Creating installation directory at $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"
fi

# Clone or update the repository
if [ ! -d "$INSTALL_DIR/.git" ]; then
    echo "Cloning MCP-FreeCAD repository into $INSTALL_DIR..."
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
else
    echo "Updating MCP-FreeCAD repository in $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    # Stash local changes, pull, then try to reapply stashed changes
    git stash push -m "Installer auto-stash" || true
    git pull || { echo "Git pull failed. Please resolve conflicts manually in $INSTALL_DIR"; exit 1; }
    git stash pop || true # Pop might fail if no stash or if conflicts occur
fi

# Set up Python virtual environment if it doesn't exist or requirements changed
if [ ! -d "$INSTALL_DIR/$VENV_DIR" ] || [ "$INSTALL_DIR/$REQUIREMENTS_FILE" -nt "$INSTALL_DIR/$VENV_DIR/pyvenv.cfg" ]; then
    echo "Setting up Python virtual environment in $INSTALL_DIR/$VENV_DIR..."
    # Remove old venv if it exists and requirements changed
    if [ -d "$INSTALL_DIR/$VENV_DIR" ]; then
        echo "Requirements file updated, recreating virtual environment..."
        rm -rf "$INSTALL_DIR/$VENV_DIR"
    fi
    python3 -m venv "$VENV_DIR"
    # Activate venv for this script's context
    source "$VENV_DIR/bin/activate"
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
else
    # Activate existing venv for this script's context
    source "$INSTALL_DIR/$VENV_DIR/bin/activate"
fi

# Function to run the MCP server
run_mcp_server() {
    echo "Starting MCP-FreeCAD server from $INSTALL_DIR..."
    # Ensure we are in the correct directory
    cd "$INSTALL_DIR" || exit 1
    # Execute the server script using the python from the virtual environment
    # Pass any remaining arguments to the server script
    python3 "$SERVER_SCRIPT" "$@"
}

# Run the MCP server with any remaining arguments
run_mcp_server "$@"
