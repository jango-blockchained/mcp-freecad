#!/bin/bash
# MCP-FreeCAD Installation Wrapper
# Convenience script to run the Python installer with proper environment setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Print header
echo ""
echo "╔════════════════════════════════════════╗"
echo "║  MCP-FreeCAD Installation Wrapper      ║"
echo "║  Version: 1.0.0                        ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed or not in PATH"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
info "Using Python $PYTHON_VERSION"

# Check Python version (3.8 or newer)
PYTHON_MINOR=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
    error "Python 3.8 or newer is required (found $PYTHON_MINOR)"
    exit 1
fi

success "Python version check passed"

# Display usage if requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo ""
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  (no args)        Run full installation with tests"
    echo "  --addon-only     Install FreeCAD addon only"
    echo "  --server-only    Install MCP server dependencies only"
    echo "  --vscode-only    Configure VS Code only"
    echo "  --no-test        Skip tests"
    echo "  --verbose        Enable verbose output"
    echo "  -h, --help       Show this help message"
    echo ""
    exit 0
fi

# Check if install.py exists
if [ ! -f "$SCRIPT_DIR/install.py" ]; then
    error "install.py not found in $SCRIPT_DIR"
    exit 1
fi

success "Found install.py at $SCRIPT_DIR/install.py"

echo ""
info "Starting MCP-FreeCAD installation..."
echo ""

# Run the Python installer with all arguments passed through
python3 "$SCRIPT_DIR/install.py" "$@"
INSTALL_STATUS=$?

echo ""
if [ $INSTALL_STATUS -eq 0 ]; then
    success "Installation completed successfully! 🎉"
    echo ""
    echo "Next steps:"
    echo "  1. Restart FreeCAD to load the addon"
    echo "  2. Restart VS Code to activate the MCP server"
    echo "  3. Start using FreeCAD with AI assistance!"
    echo ""
else
    error "Installation failed with exit code $INSTALL_STATUS"
    error "Please review the error messages above"
    exit $INSTALL_STATUS
fi

exit 0
