#!/bin/bash
# Install MCP-FreeCAD globally

set -e  # Exit on error

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the repository root (two levels up from the script)
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INSTALL_DIR="/usr/local/bin"

echo "Installing MCP-FreeCAD globally..."

# Create the shell script wrapper
cat > "$SCRIPT_DIR/mcp-freecad" << EOF
#!/bin/bash
cd "$REPO_ROOT"
python3 "$REPO_ROOT/freecad_mcp_server.py" "\$@"
EOF

# Make it executable
chmod +x "$SCRIPT_DIR/mcp-freecad"

# Check if we have permission to write to /usr/local/bin
if [ -w "$INSTALL_DIR" ]; then
    # Create symbolic link
    ln -sf "$SCRIPT_DIR/mcp-freecad" "$INSTALL_DIR/mcp-freecad"
    echo "MCP-FreeCAD installed successfully! You can now run it with 'mcp-freecad'"
else
    echo "Need sudo permission to create symbolic link in $INSTALL_DIR"
    sudo ln -sf "$SCRIPT_DIR/mcp-freecad" "$INSTALL_DIR/mcp-freecad"
    echo "MCP-FreeCAD installed successfully with sudo! You can now run it with 'mcp-freecad'"
fi
