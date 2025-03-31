# FreeCAD Server Setup Guide

This document explains how to set up and use the FreeCAD server for the MCP-FreeCAD integration.

## Requirements

1. FreeCAD (installed on the system)
2. Python 3.6+ (included with FreeCAD)
3. MCP-FreeCAD server code

## Setup Steps

### 1. Install FreeCAD

Install FreeCAD on your system using your package manager or by downloading it from the [official website](https://www.freecad.org/downloads.php).

For Ubuntu/Debian:
```bash
sudo apt-get install freecad
```

For Fedora:
```bash
sudo dnf install freecad
```

For Arch Linux:
```bash
sudo pacman -S freecad
```

### 2. Configure MCP-FreeCAD

Update your `config.json` file to include the FreeCAD server settings:

```json
{
  "freecad": {
    "path": "/usr/bin/freecad",
    "server_port": 12345,
    "auto_connect": true,
    "reconnect_on_failure": true
  }
}
```

Make sure to set the correct path to your FreeCAD executable.

### 3. Server Files

Ensure that the following files are in your project directory:

1. `freecad_server.py`: The server that runs inside FreeCAD
2. `freecad_client.py`: A client for communicating with the FreeCAD server

## Starting the Server

There are two ways to start the FreeCAD server:

### Option 1: Automatic Start (Recommended)

The MCP-FreeCAD integration will automatically start the FreeCAD server when needed, if `auto_connect` is set to `true` in your configuration. This is the recommended approach for regular use.

### Option 2: Manual Start

You can manually start the FreeCAD server by running:

```bash
freecad -c freecad_server.py
```

This will start FreeCAD with the server script, which will listen for connections on port 12345 (or the port specified in the script arguments).

## Testing the Connection

To test that the FreeCAD server is running correctly, you can use the included client:

```bash
python freecad_client.py ping
```

If the server is running, you should see a response like:

```json
{
  "pong": true,
  "timestamp": 1627392982.3456
}
```

## Client Usage Examples

The `freecad_client.py` script can be used to interact with the FreeCAD server:

```bash
# Get FreeCAD version
python freecad_client.py version

# Create a new document
python freecad_client.py create-document MyDocument

# Create a box
python freecad_client.py create-box --length 20 --width 15 --height 10 --document MyDocument

# Export the document to a STEP file
python freecad_client.py export-document --path model.step --document MyDocument
```

## Troubleshooting

### Connection Issues

If you're having trouble connecting to the FreeCAD server:

1. Make sure FreeCAD is installed and the path in `config.json` is correct
2. Check if another instance of the FreeCAD server is already running
3. Verify that port 12345 (or your configured port) is not in use by another application
4. Look at the FreeCAD console output for any error messages

### Crash Recovery

The MCP-FreeCAD integration includes a recovery mechanism that will automatically try to restart the FreeCAD server if it crashes or becomes unresponsive.

## Advanced Configuration

You can create a `.freecad_server.json` file in your home directory to configure the FreeCAD server:

```json
{
  "host": "localhost",
  "port": 12345,
  "debug": true
}
```

Setting `debug` to `true` will enable more verbose logging in the FreeCAD console. 