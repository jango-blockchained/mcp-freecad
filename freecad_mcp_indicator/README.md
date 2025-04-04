# FreeCAD MCP Connection Indicator

> **⚠️ UNDER HEAVY DEVELOPMENT! ⚠️**  
> This project is being actively developed with daily updates. Features and interfaces may change frequently. Check back regularly for improvements!

[![CI](https://github.com/yourusername/freecad_mcp_indicator/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/freecad_mcp_indicator/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A FreeCAD workbench that shows MCP connection status in the status bar and provides comprehensive control over the MCP server.

## Features

- **Dual Indicators in Status Bar**:
  - MCP Client indicator: Green (connected) or Red (disconnected)
  - MCP Server indicator: Blue (running) or Orange (stopped)
  
- **Connection Details**:
  - View detailed connection information with a single click
  - Display connection type, port numbers, and server status
  - Monitor connected clients and server uptime
  
- **Server Management**:
  - Start/stop/restart the MCP server directly from FreeCAD
  - Choose between standalone or FreeCAD-connected mode
  - Configure server settings through an intuitive interface
  
- **Configuration Options**:
  - Set custom MCP server path
  - Configure server configuration file location
  - Customize client connection settings (host, port)
  
- **Automatic Status Updates**:
  - Connection status updated every 5 seconds
  - Real-time server monitoring
  - Detailed tooltips on hover

## Installation

### Automatic Installation

This module includes installation scripts for easy setup:

#### Using Python (Cross-platform):
```bash
cd /path/to/freecad_mcp_indicator
python3 scripts/install.py
```

#### Using Bash (Linux/macOS):
```bash
cd /path/to/freecad_mcp_indicator
./scripts/install.sh
```

These scripts will automatically find your FreeCAD Mod directory and install the workbench to the correct location.

### Manual Installation

1. Locate your FreeCAD Mod directory:
   - Linux: `~/.FreeCAD/Mod` or `~/.freecad/Mod`
   - Windows: `%APPDATA%\FreeCAD\Mod`
   - macOS: `~/Library/Preferences/FreeCAD/Mod`

2. Copy or clone this repository into your Mod directory:
   ```bash
   # Linux/macOS
   cp -r /path/to/freecad_mcp_indicator ~/.FreeCAD/Mod/
   
   # Or clone directly
   cd ~/.FreeCAD/Mod
   git clone https://github.com/yourusername/freecad_mcp_indicator.git
   ```

3. Make sure you have the MCP FreeCAD library installed:
   ```bash
   pip install mcp-freecad
   ```

4. Restart FreeCAD

## Usage

### Indicators

- **Client Indicator** (right icon):
  - Green: Active MCP client connection
  - Red: No MCP client connection
  - Click to view detailed client connection information

- **Server Indicator** (left icon):
  - Blue: MCP server is running
  - Orange: MCP server is stopped
  - Click to view detailed server status and connected clients

### Configuration

1. Right-click either indicator and select "Settings..."
2. In the Settings dialog, configure:
   - Server Settings: Path to server script and configuration file
   - Client Settings: Host and port for MCP server connection

### Server Control

Right-click either indicator to access server controls:
- **Start Server (Standalone)**: Run server in standalone mode
- **Start Server (Connect to FreeCAD)**: Run server in FreeCAD-connected mode
- **Stop Server**: Terminate the running server
- **Restart Server**: Restart the currently running server

## Troubleshooting

### Common Issues

#### Qt/OpenGL Warnings
Messages like `QOpenGLFunctions created with non-current context` are typically harmless warnings from Qt's graphics system and don't affect functionality.

#### QtGui Import Errors
If you see errors like `name 'QtGui' is not defined`, ensure you have the latest version of the workbench installed. This issue has been fixed in version 0.2.0+.

#### Wayland Compatibility Issues
When running on Wayland, you may see warnings like `Wayland does not support QWindow::requestActivate()`. These are expected limitations of the Wayland display server and won't affect core functionality, though some window behaviors may be different.

### Fixing Installation Issues
If you encounter issues with the installation:

1. Ensure you have the correct permissions to write to your FreeCAD Mod directory
2. Try running the installation script with administrator/sudo privileges
3. If all else fails, use the manual installation method

### Server Connection Problems
If you're having trouble connecting to the MCP server:

1. Check that the server is running (blue indicator)
2. Verify the correct host and port settings in the configuration
3. Check for any firewall rules that might be blocking connections
4. Look for error messages in the FreeCAD Report view

## Requirements

- FreeCAD 0.19 or later
- Python 3.8 or later
- mcp-freecad library
- PySide2

## Development

### Running Tests
The project includes automated tests to ensure code quality. To run tests locally:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8
black --check .
isort --check .
```

### CI/CD
This project uses GitHub Actions for continuous integration. The CI process:
- Runs tests across multiple Python versions (3.8, 3.9, 3.10, 3.11)
- Performs static code analysis and linting
- Ensures consistent code formatting

## License

MIT License 
