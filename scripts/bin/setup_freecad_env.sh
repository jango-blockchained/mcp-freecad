#!/bin/bash
# MCP-FreeCAD Environment Setup Script
# Clones/updates the repo, sets up venv, downloads latest AppImage,
# and extracts it for the recommended launcher mode.

set -e  # Exit on error

# --- Configuration ---
REPO_URL="https://github.com/jango-blockchained/mcp-freecad.git"
INSTALL_DIR="$HOME/.mcp-freecad"
DOWNLOAD_SCRIPT="download_appimage.py"
EXTRACT_SCRIPT="extract_appimage.py"
REQUIREMENTS_FILE="requirements.txt"
VENV_DIR=".venv"
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
    git stash push -m "Setup script auto-stash" || true
    git pull || { echo "Git pull failed. Please resolve conflicts manually in $INSTALL_DIR"; exit 1; }
    git stash pop || true
fi

# Set up Python virtual environment if it doesn't exist or requirements changed
if [ ! -d "$INSTALL_DIR/$VENV_DIR" ] || [ "$INSTALL_DIR/$REQUIREMENTS_FILE" -nt "$INSTALL_DIR/$VENV_DIR/pyvenv.cfg" ]; then
    echo "Setting up Python virtual environment in $INSTALL_DIR/$VENV_DIR..."
    if [ -d "$INSTALL_DIR/$VENV_DIR" ]; then
        echo "Requirements file updated, recreating virtual environment..."
        rm -rf "$INSTALL_DIR/$VENV_DIR"
    fi
    python3 -m venv "$VENV_DIR"
    # Activate venv for subsequent commands in this script
    source "$VENV_DIR/bin/activate"
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
else
    # Activate existing venv for subsequent commands in this script
    source "$INSTALL_DIR/$VENV_DIR/bin/activate"
fi

# --- Download AppImage ---
DOWNLOAD_SCRIPT_PATH="$INSTALL_DIR/$DOWNLOAD_SCRIPT"
if [ -f "$DOWNLOAD_SCRIPT_PATH" ]; then
    echo "Downloading latest FreeCAD AppImage (if needed)..."
    # Run the download script, saving the AppImage inside INSTALL_DIR
    # The download script should ideally check if the file exists first, but we run it anyway
    # Use python from venv
    python3 "$DOWNLOAD_SCRIPT_PATH" -o "$INSTALL_DIR"
else
    echo "Error: Download script $DOWNLOAD_SCRIPT not found in $INSTALL_DIR."
    exit 1
fi

# --- Find Downloaded AppImage ---
# Find the most recently downloaded AppImage file in the install dir
APPIMAGE_FILE=$(find "$INSTALL_DIR" -maxdepth 1 -name '*.AppImage' -printf '%T+ %p\n' | sort -r | head -n 1 | cut -d' ' -f2-)

if [ -z "$APPIMAGE_FILE" ] || [ ! -f "$APPIMAGE_FILE" ]; then
    echo "Error: Could not find a downloaded AppImage file in $INSTALL_DIR."
    exit 1
fi
echo "Found AppImage: $APPIMAGE_FILE"

# --- Extract AppImage ---
EXTRACT_SCRIPT_PATH="$INSTALL_DIR/$EXTRACT_SCRIPT"
if [ -f "$EXTRACT_SCRIPT_PATH" ]; then
    echo "Extracting AppImage: $APPIMAGE_FILE ..."
    # Run the extract script using python from venv
    # It will create squashfs-root inside $INSTALL_DIR and update config.json
    python3 "$EXTRACT_SCRIPT_PATH" "$APPIMAGE_FILE"
else
    echo "Error: Extraction script $EXTRACT_SCRIPT not found in $INSTALL_DIR."
    exit 1
fi

echo "-----------------------------------------------------"
echo "Setup Complete!"
echo "FreeCAD AppImage downloaded and extracted to $INSTALL_DIR/squashfs-root"
echo "config.json has been updated for launcher mode."
echo ""
echo "You can now start the MCP server using:"
echo "  ~/.mcp-freecad/scripts/bin/mcp-freecad-installer.sh"
echo "Or (if globally installed):"
echo "  mcp-freecad"
echo "-----------------------------------------------------"
