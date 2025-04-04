#!/bin/bash
# Install MCP-FreeCAD globally

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/usr/local/bin"

echo "Installing MCP-FreeCAD globally..."

# Create the shell script wrapper
cat > "$SCRIPT_DIR/mcp-freecad" << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
python3 "$SCRIPT_DIR/freecad_mcp_server.py" "\$@"
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
