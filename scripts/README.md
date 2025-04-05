# MCP-FreeCAD Scripts

This directory contains various scripts for running, installing, and setting up the MCP-FreeCAD integration.

## Directory Structure

- `bin/`: Contains executable scripts for installation and running the server
- `/`: Contains main operational scripts

## Script Descriptions

### Main Scripts

- `start_server.py`: Python script to start the FreeCAD server from within FreeCAD's Python console or as a macro
- `start_freecad_with_server.sh`: Shell script to launch FreeCAD with the integrated server enabled
- `run_mcp_server.py`: Python script to run the MCP server using FreeCAD's AppRun
- `start_mcp_server.sh`: Shell script to start the MCP server with proper environment settings

### Bin Scripts

- `install-global.sh`: Script to install MCP-FreeCAD globally on the system
- `mcp-freecad.sh`: Simple wrapper script to call the MCP-FreeCAD server with the Python interpreter
- `mcp-freecad-installer.sh`: Script to check out the MCP-FreeCAD repository if needed and run the MCP server
- `run-freecad-server.sh`: Wrapper script to run freecad_server.py with the correct environment settings

## Usage

### Starting FreeCAD with the Integrated Server

```bash
./scripts/start_freecad_with_server.sh
```

### Starting the MCP Server

```bash
./scripts/start_mcp_server.sh
```

### Installing MCP-FreeCAD Globally

```bash
./scripts/bin/install-global.sh
```

### Running the FreeCAD Server with the Correct Environment

```bash
./scripts/bin/run-freecad-server.sh
```

### Installing and Running the MCP-FreeCAD Server

```bash
./scripts/bin/mcp-freecad-installer.sh
```

## Python Interpreter Configuration

For more information about the Python interpreter configuration and FreeCAD integration, see:
[Python Interpreter Setup](../docs/PYTHON_INTERPRETER_SETUP.md) 
