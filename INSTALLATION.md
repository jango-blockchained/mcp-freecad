# MCP-FreeCAD Installation Guide

This guide will help you install the complete MCP-FreeCAD integration, including the FreeCAD addon, MCP server, and VS Code configuration.

## Prerequisites

### System Requirements

- **Python**: 3.8 or newer
- **Operating System**: Windows, macOS, or Linux
- **FreeCAD**: Version 0.20.0 or newer (for addon installation)
- **VS Code**: Optional (for VS Code integration)

### Network Requirements

- Internet connection for downloading dependencies
- No proxy/firewall restrictions on pip package downloads

## Quick Start

### Option 1: Full Installation (Recommended)

Install everything with a single command:

```bash
python install.py
```

This will:

1. Install FreeCAD addon to `~/.local/share/FreeCAD/Mod/MCPIntegration` (Linux)
2. Install MCP server dependencies
3. Configure VS Code MCP settings
4. Run verification tests

### Option 2: Component-Based Installation

Install only what you need:

```bash
# Install FreeCAD addon only
python install.py --addon-only

# Install MCP server dependencies only
python install.py --server-only

# Configure VS Code only
python install.py --vscode-only
```

### Option 3: Skip Tests

For faster installation without verification:

```bash
python install.py --no-test
```

## Command Line Options

```bash
usage: install.py [-h] [--addon-only] [--server-only] [--vscode-only]
                   [--no-test] [--verbose]

Options:
  -h, --help         Show this help message
  --addon-only       Install FreeCAD addon only
  --server-only      Install MCP server dependencies only
  --vscode-only      Configure VS Code only
  --no-test          Skip verification tests
  -v, --verbose      Enable verbose output
```

## What Gets Installed

### FreeCAD Addon

**Location:**

- Linux: `~/.local/share/FreeCAD/Mod/MCPIntegration/`
- macOS: `~/Library/Preferences/FreeCAD/Mod/MCPIntegration/`
- Windows: `%APPDATA%\FreeCAD\Mod\MCPIntegration\`

**Contents:**

- AI workbench implementation
- GUI components
- Tool providers
- Configuration files

### MCP Server Dependencies

**Packages installed:**

- `fastmcp` - Modern MCP server framework
- `mcp` - MCP SDK
- `requests` - HTTP library
- `loguru` - Logging
- `psutil` - System utilities
- `fastapi` - Web framework
- `pydantic` - Data validation
- `aiohttp` - Async HTTP

### VS Code Configuration

**File:**

- Linux: `~/.config/Code/User/mcp.json`
- macOS: `~/Library/Application Support/Code/User/mcp.json`
- Windows: `%APPDATA%\Code\User\mcp.json`

**Configuration example:**

```json
{
  "mcpServers": {
    "freecad-mcp": {
      "command": "python3",
      "args": ["/path/to/freecad-ai/mcp_server.py"],
      "env": {
        "PYTHONPATH": "...",
        "MCP_DEBUG": "1"
      }
    }
  }
}
```

## Verification

The installer automatically runs tests to verify:

1. **FreeCAD Addon**: Checks if addon was installed correctly
2. **MCP Server**: Verifies MCP server can be imported
3. **Dependencies**: Confirms all Python packages installed

If tests fail, the installer will provide error messages to help troubleshoot.

## Troubleshooting

### "Could not determine FreeCAD modules directory"

**Cause:** FreeCAD is not installed or in non-standard location

**Solution:**

1. Install FreeCAD first: <https://www.freecadweb.org/>
2. Launch FreeCAD at least once to create mod directory
3. Run installer again

### "Permission denied" errors

**Linux/macOS:** Run with `sudo python install.py`

**Windows:** Run VS Code or terminal as Administrator

### "ModuleNotFoundError: No module named 'mcp'"

**Cause:** MCP dependencies not installed

**Solution:** Run `python install.py --server-only` again

### VS Code MCP not appearing

**Cause:** mcp.json not created or VS Code not installed

**Solution:**

1. Restart VS Code completely
2. Check if mcp.json exists at expected path
3. Run `python install.py --vscode-only` again

### FreeCAD Addon not showing in Workbench list

**Cause:** Addon not fully installed or FreeCAD cache

**Solution:**

1. Verify addon location (see "What Gets Installed" section)
2. Delete FreeCAD cache: `~/.FreeCAD/ModManager/` (Linux)
3. Restart FreeCAD## Next Steps

### After Installation

1. **Restart FreeCAD**
   - Addon will auto-load
   - New workbench appears in dropdown

2. **Restart VS Code**
   - MCP server configuration takes effect
   - Look for FreeCAD MCP server in MCP settings

3. **Configure API Keys**
   - Open FreeCAD → MCP Integration workbench
   - Go to "AI Models" tab
   - Enter your API key (Claude, Gemini, or OpenRouter)

4. **Test Connectivity**
   - Use "Test Connection" button
   - Try creating a simple primitive shape

### Configuration Files

**FreeCAD Addon Config:**

- `freecad-ai/addon_config.json` - Addon settings

**MCP Server Config:**

- `config.json` - Server settings
- `config.example.json` - Template

**VS Code Config:**

- `~/.config/Code/User/settings.json` - General settings
- `~/.config/Code/User/mcp.json` - MCP servers

## Documentation

- [MCP-FreeCAD README](README.md) - Project overview
- [FreeCAD Addon INSTALL](freecad-ai/INSTALL.md) - Addon-specific guide
- [API Reference](docs/ALLOWED_OPTIONS.md) - Available tools and options
- [Connection Methods](docs/CONNECTION_METHODS.md) - Different connection types

## Support

### Getting Help

1. **Check Logs**
   - FreeCAD: View → Panels → Report view
   - VS Code: Output → MCP

2. **Review Errors**
   - Run installer with `--verbose` flag
   - Check generated log files

3. **Report Issues**
   - GitHub Issues: <https://github.com/jango-blockchained/mcp-freecad/issues>
   - Include Python version, OS, and error messages

## Security Notes

- MCP server runs on localhost:12345 by default
- API keys are stored securely in FreeCAD config
- No telemetry or data collection

## System Information

To help with troubleshooting, the installer collects:

- Operating system and version
- Python version
- FreeCAD installation path
- VS Code configuration path

All information is local and not transmitted anywhere.

## Success Checklist

After installation, verify:

- FreeCAD addon appears in workbench list
- VS Code recognizes MCP server
- MCP test in installer passed
- Can create primitives in FreeCAD
- API key tested successfully

## Uninstallation

To remove the installation:

```bash
# Remove FreeCAD addon
rm -rf ~/.local/share/FreeCAD/Mod/MCPIntegration/

# Remove Python packages
pip uninstall fastmcp mcp requests loguru psutil fastapi pydantic aiohttp

# Remove VS Code config
# Edit ~/.config/Code/User/mcp.json and remove freecad-mcp server entry
```

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-06  
**Author**: jango-blockchained
