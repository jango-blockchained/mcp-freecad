# MCP-FreeCAD Complete Installation Setup

Complete guide for installing and configuring MCP-FreeCAD integration including FreeCAD addon, MCP server, and VS Code setup.

## Quick Start (30 seconds)

### Linux & macOS
```bash
cd mcp-freecad
chmod +x install.sh
./install.sh
```

### Windows
```batch
cd mcp-freecad
install.bat
```

### All Platforms (Python)
```bash
cd mcp-freecad
python install.py
```

**Then restart FreeCAD and VS Code!**

---

## What Gets Installed

### 1. FreeCAD Addon (MCPIntegration Workbench)

**Installed to:**
- Linux: `~/.local/share/FreeCAD/Mod/MCPIntegration/`
- macOS: `~/Library/Preferences/FreeCAD/Mod/MCPIntegration/`
- Windows: `%APPDATA%\FreeCAD\Mod\MCPIntegration\`

**Includes:**
- AI integration workbench
- Modern tabbed GUI interface
- Tool providers (primitives, model manipulation, etc.)
- Configuration management
- Logging and diagnostics

**Access in FreeCAD:**
1. Open FreeCAD
2. Workbench dropdown (top right)
3. Select "FreeCAD AI" or "MCP Integration"
4. New workbench loads with AI assistant panel

### 2. MCP Server (Python Backend)

**Python Packages:**
```
fastmcp>=2.13.0              - Modern MCP server framework
mcp>=1.20.0                  - MCP SDK
requests>=2.28.0             - HTTP communication
loguru>=0.7.0                - Structured logging
psutil>=5.9.0                - System information
fastapi>=0.100.0             - Web framework
pydantic>=2.0.0              - Data validation
aiohttp>=3.8.0               - Async HTTP client
PySide2                      - Qt framework (FreeCAD)
```

**Installation Method:**
- Installed via `pip install -r requirements.txt`
- System-wide or virtual environment
- Automatically handles dependencies

**Server Features:**
- Runs on localhost:12345 by default
- Stdio-based communication with MCP clients
- Multiple connection methods supported
- Hot-reload capability for development

### 3. VS Code MCP Configuration

**File:** `~/.config/Code/User/mcp.json`

**Content Example:**
```json
{
  "mcpServers": {
    "freecad-mcp": {
      "command": "python3",
      "args": ["/path/to/freecad-ai/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/addon:/path/to/project",
        "MCP_DEBUG": "1"
      }
    }
  }
}
```

**VS Code Integration:**
- MCP Explorer shows FreeCAD server
- Can test connection directly
- Auto-reconnects if server restarts
- Logs available for debugging

---

## Installation Methods

### Method 1: Shell Script (Recommended - Linux/macOS)

```bash
chmod +x install.sh
./install.sh
```

**Features:**
- Colored output with progress
- Python version checking
- Error detection and reporting
- Help menu built-in

**Options:**
```bash
./install.sh --addon-only      # FreeCAD addon only
./install.sh --server-only     # MCP server only
./install.sh --vscode-only     # VS Code config only
./install.sh --no-test         # Skip verification tests
./install.sh --verbose         # Detailed output
./install.sh --help            # Show help
```

### Method 2: Batch Script (Windows)

```batch
install.bat
```

**Features:**
- Windows command line compatible
- Administrator privilege suggestions
- Error handling and reporting
- Same functionality as shell script

**Options:**
Same as shell script (see above)

### Method 3: Python Script (All Platforms)

```bash
python install.py
```

**Features:**
- Cross-platform reliability
- Most detailed error messages
- Component-based installation
- Progress tracking

**Options:**
```bash
python install.py --addon-only   # FreeCAD addon only
python install.py --server-only  # MCP server only
python install.py --vscode-only  # VS Code config only
python install.py --no-test      # Skip tests
python install.py --verbose      # Verbose output
python install.py --help         # Show help
```

---

## Verification

### After Installation

The installer automatically verifies:

1. **FreeCAD Addon Installation**
   - Checks addon directory exists
   - Verifies required files present

2. **MCP Server**
   - Tests module can be imported
   - Validates dependencies installed

3. **Python Environment**
   - Confirms all packages available
   - Checks version compatibility

### Manual Verification

**Check FreeCAD Addon:**
```bash
# Linux/macOS
ls -la ~/.local/share/FreeCAD/Mod/MCPIntegration/

# Or look for MCPIntegration in FreeCAD workbench dropdown
```

**Check MCP Server:**
```python
import sys
sys.path.insert(0, '/path/to/freecad-ai')
import mcp_server
print("✓ MCP server can be imported")
```

**Check VS Code Config:**
```bash
# Linux/macOS
cat ~/.config/Code/User/mcp.json

# Windows
type %APPDATA%\Code\User\mcp.json
```

**Check Python Packages:**
```bash
pip list | grep -E "fastmcp|mcp|requests|loguru|psutil"
```

---

## Troubleshooting

### Python Not Found
```bash
# Check if Python 3 is installed
python3 --version

# Install if missing
# Ubuntu/Debian: sudo apt install python3
# macOS (Homebrew): brew install python3
# Windows: Download from python.org and add to PATH
```

### FreeCAD Installation Issues

**"Could not determine FreeCAD modules directory"**
1. Ensure FreeCAD is installed
2. Download from: https://www.freecadweb.org/
3. Launch FreeCAD at least once
4. Re-run installer

**Addon doesn't appear in workbench list**
1. Verify addon location (see "What Gets Installed")
2. Restart FreeCAD completely
3. Check FreeCAD Report view for errors
4. Delete cache: `~/.FreeCAD/` and restart

### VS Code Issues

**mcp.json not created**
1. Ensure VS Code is installed
2. Run: `python install.py --vscode-only`
3. Manually restart VS Code
4. Check MCP Explorer for freecad-mcp server

**MCP server not connecting**
1. Ensure Python packages installed: `pip list`
2. Run installer again: `python install.py --server-only`
3. Check VS Code output panel for errors
4. Run with verbose: `python install.py --verbose`

### Permission Issues

**Linux/macOS:**
```bash
# Run with elevated privileges
sudo python install.py

# Or make script executable
chmod +x install.sh
./install.sh
```

**Windows:**
1. Right-click Command Prompt
2. Select "Run as Administrator"
3. Run: `install.bat`

### Existing Installation Problems

**Clean reinstall:**
```bash
# Remove old installation
rm -rf ~/.local/share/FreeCAD/Mod/MCPIntegration/

# Remove Python packages
pip uninstall fastmcp mcp requests loguru psutil fastapi pydantic aiohttp

# Remove VS Code config entry
# Edit ~/.config/Code/User/mcp.json and remove "freecad-mcp" entry

# Restart and reinstall
python install.py
```

---

## After Installation

### First Use

1. **Restart FreeCAD**
   - Close completely
   - Reopen FreeCAD
   - New workbench should appear in dropdown

2. **Switch to MCP Integration Workbench**
   - Click workbench dropdown (top right toolbar)
   - Select "FreeCAD AI" or "MCP Integration"
   - Loading panel should appear

3. **Configure AI Provider**
   - Go to "AI Models" tab
   - Select provider (Claude, Gemini, or OpenRouter)
   - Enter API key
   - Click "Test Connection"

4. **Test Basic Operations**
   - Go to "Tools" tab
   - Select "Primitives"
   - Create a test box
   - Should see new object in 3D view

### Configuration Files

**FreeCAD Addon Config:**
`freecad-ai/addon_config.json`

Contains:
- AI provider settings
- Model parameters
- UI configuration
- Tool defaults

**MCP Server Config:**
`config.json` and `config.example.json`

Contains:
- Server settings
- Connection method
- Logging configuration
- Tool enablement

**VS Code Config:**
`~/.config/Code/User/mcp.json`

Contains:
- MCP server entries
- Connection parameters
- Environment variables

---

## Advanced Usage

### Component-Based Installation

**FreeCAD Addon Only** (no MCP server):
```bash
python install.py --addon-only
```

**MCP Server Only** (development setup):
```bash
python install.py --server-only
```

**VS Code Only** (add to existing MCP setup):
```bash
python install.py --vscode-only
```

### Update Existing Installation

```bash
# Re-run installer to update all components
python install.py

# Or update specific components
python install.py --server-only  # Update Python packages
python install.py --vscode-only  # Update VS Code config
```

### Development Setup

```bash
# Install with symbolic link for development
cd ~/.local/share/FreeCAD/Mod/
ln -s /path/to/mcp-freecad/freecad-ai MCPIntegration

# Then run server installer
python install.py --server-only
```

### Custom Configuration

1. Edit `config.json` for server settings
2. Edit `freecad-ai/addon_config.json` for addon settings
3. Edit `~/.config/Code/User/mcp.json` for VS Code settings
4. Restart relevant applications

---

## Uninstallation

### Remove FreeCAD Addon
```bash
# Linux/macOS
rm -rf ~/.local/share/FreeCAD/Mod/MCPIntegration/

# Windows
rmdir /S %APPDATA%\FreeCAD\Mod\MCPIntegration
```

### Remove Python Packages
```bash
pip uninstall fastmcp mcp requests loguru psutil fastapi pydantic aiohttp
```

### Remove VS Code Configuration
```bash
# Edit ~/.config/Code/User/mcp.json
# Remove the "freecad-mcp" entry from mcpServers

# Or manually (Linux/macOS):
nano ~/.config/Code/User/mcp.json

# Or (Windows):
notepad %APPDATA%\Code\User\mcp.json
```

### Clean Complete Uninstall
```bash
# FreeCAD
rm -rf ~/.local/share/FreeCAD/Mod/MCPIntegration/

# Python packages
pip uninstall -y fastmcp mcp requests loguru psutil fastapi pydantic aiohttp

# VS Code config
# Manually edit mcp.json

# Restart applications
```

---

## Support & Resources

### Documentation
- [Installation Guide](INSTALLATION.md) - Detailed setup instructions
- [Installation Scripts](INSTALL_SCRIPTS.md) - Script documentation
- [Main README](README.md) - Project overview
- [FreeCAD Addon Guide](freecad-ai/INSTALL.md) - Addon specifics

### Getting Help
1. Check troubleshooting section above
2. Review error messages carefully
3. Run with `--verbose` flag for details
4. Check application logs:
   - FreeCAD: View → Panels → Report view
   - VS Code: Output panel → MCP

### Reporting Issues
- GitHub Issues: https://github.com/jango-blockchained/mcp-freecad/issues
- Include: Python version, OS, error messages, terminal output
- Run: `python install.py --verbose` and attach output

---

## FAQ

**Q: Do I need to restart FreeCAD and VS Code?**
A: Yes, both need to be restarted for changes to take effect.

**Q: Can I install multiple times?**
A: Yes! The installer is safe to run repeatedly and will update existing installations.

**Q: Do I need internet to run the installer?**
A: Yes, for downloading Python packages from PyPI.

**Q: Can I use a custom FreeCAD installation?**
A: The installer auto-detects FreeCAD. If detection fails, ensure FreeCAD is in your PATH.

**Q: What if I have both FreeCAD 0.x and 1.x installed?**
A: The installer will use the first one found. For specific version, run component-wise.

**Q: Can I install for multiple users?**
A: Each user must run the installer individually as it installs to home directories.

**Q: Is my API key secure?**
A: API keys are stored locally in FreeCAD config with file-level permissions.

**Q: Can I use this offline?**
A: Initial installation requires internet. After installation, some features work offline.

**Q: What's the minimum Python version?**
A: Python 3.8 or newer. Check with: `python3 --version`

**Q: How much disk space do I need?**
A: Approximately 300-500 MB (addon + dependencies + cache).

---

## Success Checklist

After installation, verify:

- [ ] FreeCAD addon appears in workbench dropdown
- [ ] VS Code shows freecad-mcp in MCP Explorer
- [ ] MCP server test passed without errors
- [ ] Can create primitives in FreeCAD
- [ ] API key connection works
- [ ] No errors in FreeCAD Report view
- [ ] No errors in VS Code Output panel

---

**Installation Complete! 🎉**

You're now ready to use AI-assisted CAD design with MCP-FreeCAD integration.

---

**Version:** 1.0.0
**Last Updated:** 2025-11-06
**Maintainer:** jango-blockchained
