# Claude Desktop Integration

The FreeCAD MCP Integration addon now supports direct integration with Claude Desktop App through the Model Context Protocol (MCP). This allows you to interact with FreeCAD directly from Claude Desktop without using the built-in chat interface.

## Features

- **Direct FreeCAD Control**: Create 3D objects, perform boolean operations, and manage documents directly from Claude Desktop
- **Seamless Integration**: All FreeCAD tools are exposed as MCP tools that Claude can use
- **Resource Access**: Claude can access information about your FreeCAD documents and objects
- **Headless Operation**: The MCP server can run in headless mode for better performance

## Setup Instructions

### 1. Enable Claude Desktop Mode

1. Open FreeCAD and go to the MCP Integration workbench
2. Navigate to the **Models** tab
3. Check the **"Enable Claude Desktop Mode"** checkbox
4. The Assistant tab will be hidden (you'll use Claude Desktop instead)

### 2. Install Dependencies

Make sure you have the MCP library installed:

```bash
pip install mcp>=1.0.0
```

You can also use the Dependencies tab in the MCP Integration interface to install this automatically.

### 3. Configure Claude Desktop

1. **Copy Configuration**: In the Models tab, click "📋 Copy Configuration to Clipboard"

2. **Edit Claude Desktop Config**: Open your Claude Desktop configuration file:
   - **macOS/Linux**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

3. **Add Configuration**: Paste the configuration into the file. If you already have other MCP servers, merge the configuration:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "/path/to/python",
      "args": ["/path/to/launch_mcp_server.py", "--headless"]
    }
  }
}
```

4. **Restart Claude Desktop**: Close and reopen Claude Desktop App

### 4. Verify Connection

1. Open Claude Desktop
2. Look for the tools icon (🔨) in the interface
3. You should see FreeCAD tools available
4. Try asking Claude to create a simple object: "Create a box with dimensions 10x10x10 mm"

## Available Tools

The MCP server exposes the following FreeCAD tools to Claude:

### Primitive Creation
- `create_box` - Create a box/cube primitive
- `create_cylinder` - Create a cylinder primitive  
- `create_sphere` - Create a sphere primitive
- `create_cone` - Create a cone primitive

### Boolean Operations
- `boolean_union` - Combine two objects
- `boolean_cut` - Subtract one object from another
- `boolean_intersection` - Find intersection of two objects

### Measurements
- `measure_distance` - Measure distance between points/objects
- `measure_volume` - Calculate object volume
- `measure_area` - Calculate surface area

### Export/Import
- `export_stl` - Export objects to STL format
- `export_step` - Export objects to STEP format
- `list_objects` - List all objects in the document
- `create_document` - Create a new FreeCAD document

### Resources
- `freecad://document/info` - Get current document information
- `freecad://objects/list` - Get detailed object list

## Example Usage

Once configured, you can interact with FreeCAD naturally through Claude Desktop:

**User**: "Create a cylinder with radius 5mm and height 20mm, then create a sphere with radius 3mm and subtract it from the cylinder"

**Claude**: I'll help you create those objects and perform the boolean operation.

*[Claude uses the MCP tools to execute the commands]*

**User**: "What objects are currently in my document?"

**Claude**: Let me check your current FreeCAD document.

*[Claude uses the list_objects tool to show current objects]*

## Troubleshooting

### Tools Not Showing Up
1. Check that Claude Desktop is restarted after configuration
2. Verify the configuration file syntax is correct
3. Check Claude Desktop logs for errors

### Connection Issues
1. Ensure FreeCAD is running when using the MCP server
2. Check that the MCP library is installed: `pip install mcp`
3. Verify the launcher script path is correct

### Permission Issues
1. Make sure the launcher script is executable
2. Check that Python has access to FreeCAD libraries
3. Try running the launcher script manually to test

## Advanced Configuration

### Custom FreeCAD Path
If FreeCAD is installed in a non-standard location:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "/path/to/python",
      "args": [
        "/path/to/launch_mcp_server.py", 
        "--freecad-path", "/custom/path/to/freecad",
        "--headless"
      ]
    }
  }
}
```

### Debug Mode
For troubleshooting, enable debug logging:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "/path/to/python",
      "args": [
        "/path/to/launch_mcp_server.py", 
        "--debug",
        "--headless"
      ]
    }
  }
}
```

## Benefits of Claude Desktop Mode

- **Better Performance**: No need to run AI models within FreeCAD
- **Latest Claude Models**: Access to the newest Claude models through Claude Desktop
- **Seamless Workflow**: Switch between CAD work and AI assistance naturally
- **Resource Efficiency**: Offload AI processing to Claude Desktop
- **Enhanced Features**: Access to Claude Desktop's advanced features like file attachments

## Switching Back

To return to the built-in chat interface:

1. Go to the Models tab in FreeCAD
2. Uncheck "Enable Claude Desktop Mode"
3. The Assistant tab will reappear
4. You can use both modes as needed 
