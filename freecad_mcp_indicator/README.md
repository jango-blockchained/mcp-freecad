# FreeCAD MCP Connection Indicator

A simple FreeCAD workbench that shows the MCP connection status in the status bar.

## Features

- Shows a colored indicator in the status bar (green for connected, red for disconnected)
- Updates connection status every 5 seconds
- Displays tooltip with connection status on hover
- Integrates with the MCP FreeCAD library

## Installation

1. Clone this repository into your FreeCAD Mod directory:
   ```bash
   cd ~/.FreeCAD/Mod  # Linux
   # or
   cd %APPDATA%/FreeCAD/Mod  # Windows
   git clone https://github.com/yourusername/freecad_mcp_indicator.git
   ```

2. Make sure you have the MCP FreeCAD library installed:
   ```bash
   pip install mcp-freecad
   ```

3. Restart FreeCAD

## Usage

1. The indicator will appear in the status bar automatically
2. Green circle indicates active MCP connection
3. Red circle indicates no MCP connection
4. Hover over the indicator to see the connection status

## Requirements

- FreeCAD 0.19 or later
- Python 3.8 or later
- mcp-freecad library
- PySide2

## License

MIT License 