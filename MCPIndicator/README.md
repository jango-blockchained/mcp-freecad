# FreeCAD MCP Connection Indicator

> **⚠️ UNDER HEAVY DEVELOPMENT! ⚠️**  
> This project is being actively developed with daily updates. Features and interfaces may change frequently. Check back regularly for improvements!

[![CI](https://github.com/yourusername/MCPIndicator/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/MCPIndicator/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A FreeCAD workbench that shows MCP connection status in the status bar and provides comprehensive control over both the FreeCAD Socket Server and MCP Server with flow visualization capabilities.

## Features

- **Triple Indicators in Status Bar**:
  - MCP Client indicator: Green (connected) or Red (disconnected)
  - FreeCAD Server indicator: Blue with "FC" (running) or Orange with "FC" (stopped)
  - MCP Server indicator: Green with "MCP" (running) or Red with "MCP" (stopped)
  
- **Connection Details**:
  - View detailed connection information with a single click on each indicator
  - Display connection type, port numbers, and server status
  - Monitor connected clients and server uptime
  - Clear differentiation between FreeCAD Socket Server and MCP Server
  
- **MCP Flow Visualization**:
  - Interactive diagram showing message flow between AI assistant, MCP server, and FreeCAD
  - Animated visualization of commands and responses
  - Real-time message logging with timestamps
  - Connection type indication (Socket, Bridge, or Mock)
  
- **Server Management**:
  - Start/stop/restart both FreeCAD and MCP servers directly from FreeCAD
  - Choose between standalone or FreeCAD-connected mode for FreeCAD Server
  - Configure server settings through an intuitive interface
  
- **Configuration Options**:
  - Set custom FreeCAD server path (freecad_socket_server.py)
  - Set custom MCP server path (freecad_mcp_server.py)
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
cd /path/to/MCPIndicator
python3 scripts/install.py
```

#### Using Bash (Linux/macOS):
```bash
cd /path/to/MCPIndicator
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
   cp -r /path/to/MCPIndicator ~/.FreeCAD/Mod/
   
   # Or clone directly
   cd ~/.FreeCAD/Mod
   git clone https://github.com/yourusername/MCPIndicator.git
   ```

3. Make sure you have the MCP FreeCAD library installed:
   ```bash
   pip install mcp-freecad
   ```

4. Restart FreeCAD

## Usage

### Indicators

- **Client Indicator** (rightmost icon):
  - Green: Active MCP client connection
  - Red: No MCP client connection
  - Click to view detailed client connection information

- **FreeCAD Server Indicator** (left icon):
  - Blue with "FC": FreeCAD socket server is running
  - Orange with "FC": FreeCAD socket server is stopped
  - Click to view detailed FreeCAD server status

- **MCP Server Indicator** (middle icon):
  - Green with "MCP": MCP server is running
  - Red with "MCP": MCP server is stopped
  - Click to view detailed MCP server status and connected clients

### Flow Visualization

1. Right-click any indicator and select "Flow Visualization..."
2. The visualization window shows:
   - Interactive diagram of communication between components
   - Message flow animations with color-coded message types
   - Connection type indicator (Socket, Bridge, or Mock)
   - Message log with timestamps and content

### Configuration

1. Right-click any indicator and select "Settings..."
2. In the Settings dialog, configure:
   - FreeCAD Server tab: Path to FreeCAD socket server script (freecad_socket_server.py)
   - MCP Server tab: Path to MCP server script (src/mcp_freecad/server/freecad_mcp_server.py) and configuration file
   - Client Settings tab: Host and port for MCP server connection

### Server Control

Right-click any indicator to access server control menus:

- **FreeCAD Server** menu:
  - Start FreeCAD Server (Standalone): Run socket server in standalone mode
  - Start FreeCAD Server (Connect to FreeCAD): Run socket server in FreeCAD-connected mode
  - Stop FreeCAD Server: Terminate the running socket server
  - Restart FreeCAD Server: Restart the currently running socket server

- **MCP Server** menu:
  - Start MCP Server: Run the MCP server
  - Stop MCP Server: Terminate the running MCP server
  - Restart MCP Server: Restart the currently running MCP server

## Understanding the Servers

### FreeCAD Socket Server (freecad_socket_server.py)
This is a low-level socket server that runs inside FreeCAD and allows external scripts to execute FreeCAD Python commands. It acts as the bridge between the MCP server and FreeCAD's API.

### MCP Server (src/mcp_freecad/server/freecad_mcp_server.py)
This server implements the Model Context Protocol (MCP) and allows AI assistants to interact with FreeCAD through a standardized interface. It communicates with the FreeCAD Socket Server to execute commands.

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
If you're having trouble connecting to the servers:

1. Check that the appropriate server is running (blue or green indicator)
2. Verify the correct host and port settings in the configuration
3. Check for any firewall rules that might be blocking connections
4. Look for error messages in the FreeCAD Report view
5. Check the server log files in the same directory as the server scripts

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
