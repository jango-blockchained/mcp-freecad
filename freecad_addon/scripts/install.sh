#!/bin/bash

# FreeCAD MCP Indicator Installation Script
# Copies the MCP Indicator Workbench to the FreeCAD Mod directory

set -e

# Print colored messages
print_info() {
    echo -e "\e[1;34m[INFO] $1\e[0m"
}

print_success() {
    echo -e "\e[1;32m[SUCCESS] $1\e[0m"
}

print_warning() {
    echo -e "\e[1;33m[WARNING] $1\e[0m"
}

print_error() {
    echo -e "\e[1;31m[ERROR] $1\e[0m"
}

# Determine the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
SRC_DIR="$PARENT_DIR"
TARGET_NAME="freecad_addon"

print_info "FreeCAD MCP Indicator Installation"
print_info "=================================="
print_info "Source directory: $SRC_DIR"

# Determine the FreeCAD Mod directory
# Check common locations
FREECAD_MOD_DIRS=(
    "$HOME/.local/share/FreeCAD/Mod"
    "$HOME/.FreeCAD/Mod"
    "$HOME/.freecad/Mod"
    "/usr/share/freecad/Mod"
    "/usr/local/share/freecad/Mod"
    "$HOME/Library/Preferences/FreeCAD/Mod"  # macOS
    "$APPDATA/FreeCAD/Mod"                   # Windows (may not work in bash)
)

# Try to find an existing Mod directory
FREECAD_MOD_DIR=""
for dir in "${FREECAD_MOD_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        FREECAD_MOD_DIR="$dir"
        print_info "Found existing FreeCAD Mod directory: $FREECAD_MOD_DIR"
        break
    fi
done

# If no directory found, create the default one
if [ -z "$FREECAD_MOD_DIR" ]; then
    FREECAD_MOD_DIR="$HOME/.FreeCAD/Mod"
    print_warning "No existing FreeCAD Mod directory found."
    print_info "Creating default directory: $FREECAD_MOD_DIR"
    mkdir -p "$FREECAD_MOD_DIR"
fi

# Check if the target directory already exists
TARGET_DIR="$FREECAD_MOD_DIR/$TARGET_NAME"
if [ -d "$TARGET_DIR" ]; then
    print_warning "Target directory already exists: $TARGET_DIR"
    print_warning "This will overwrite the existing installation."

    # Ask for confirmation
    read -p "Continue with installation? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled."
        exit 0
    fi

    # Remove existing directory
    print_info "Removing existing installation..."
    rm -rf "$TARGET_DIR"
fi

# Create the target directory
mkdir -p "$TARGET_DIR"

# Copy all files from the source to the target directory
print_info "Copying files to $TARGET_DIR..."
cp -r "$SRC_DIR"/* "$TARGET_DIR"/

# Make the script executable
if [ -f "$TARGET_DIR/scripts/install.sh" ]; then
    chmod +x "$TARGET_DIR/scripts/install.sh"
fi

# Check if the installation was successful
if [ -d "$TARGET_DIR/mcp_indicator" ] && [ -f "$TARGET_DIR/package.xml" ]; then
    print_success "Installation completed successfully!"
    print_info "Please restart FreeCAD to use the MCP Indicator Workbench."
else
    print_error "Installation failed. Please check the error messages."
    exit 1
fi
