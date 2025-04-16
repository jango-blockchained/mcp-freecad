#!/bin/bash

# FreeCAD MCP Indicator Installation Script
# Copies the 'freecad_addon' directory to the FreeCAD Mod directory

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

# Determine the script directory and the source directory (parent of scripts)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# SRC_DIR is the parent directory containing MCPIndicator, package.xml, etc.
SRC_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
# TARGET_NAME should be the name of the directory to create in FreeCAD's Mod folder
TARGET_NAME="freecad_addon" # Changed from MCPIndicator

# Verify that the source directory looks reasonable (e.g., contains package.xml or MCPIndicator dir)
if [ ! -d "$SRC_DIR/MCPIndicator" ] || [ ! -f "$SRC_DIR/package.xml" ]; then
    print_error "Source directory structure seems incorrect at: $SRC_DIR"
    print_error "Expected to find 'MCPIndicator' subdirectory and 'package.xml'."
    exit 1
fi

print_info "FreeCAD Addon Installation ($TARGET_NAME)"
print_info "=========================================="
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
    # Use the .local path as a more modern default on Linux
    FREECAD_MOD_DIR="$HOME/.local/share/FreeCAD/Mod"
    print_warning "No existing FreeCAD Mod directory found."
    print_info "Creating default directory: $FREECAD_MOD_DIR"
    mkdir -p "$FREECAD_MOD_DIR"
fi


# Define the full target path
TARGET_DIR="$FREECAD_MOD_DIR/$TARGET_NAME" # e.g., ~/.local/share/FreeCAD/Mod/freecad_addon

# Check if the target directory already exists
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

# Create the target base directory (parent of the actual addon dir)
# This ensures the Mod directory exists
mkdir -p "$FREECAD_MOD_DIR"

# Copy the entire source directory (excluding scripts) to the target location
print_info "Copying addon files from $SRC_DIR to $TARGET_DIR..."
# Use rsync for potentially better control and exclusion
rsync -a --exclude='scripts/' --exclude='.git/' --exclude='.github/' "$SRC_DIR/" "$TARGET_DIR/"
# Alternative using cp:
# mkdir -p "$TARGET_DIR"
# cp -a "$SRC_DIR"/* "$TARGET_DIR/" # Copy contents
# cp -a "$SRC_DIR"/.??* "$TARGET_DIR/" # Copy hidden files/dirs if any (be careful)
# rm -rf "$TARGET_DIR/scripts" # Remove scripts dir after copy if needed

# No need to copy package.xml separately, it's part of the main copy


# Check if the installation was successful (check for key files)
if [ -f "$TARGET_DIR/package.xml" ] && [ -d "$TARGET_DIR/MCPIndicator" ] && [ -f "$TARGET_DIR/MCPIndicator/InitGui.py" ]; then
    print_success "Installation completed successfully!"
    print_success "Addon installed at: $TARGET_DIR"
    print_info "Please restart FreeCAD to use the MCP Indicator Workbench."
else
    print_error "Installation failed. Check if files were copied correctly to $TARGET_DIR."
    exit 1
fi

exit 0
