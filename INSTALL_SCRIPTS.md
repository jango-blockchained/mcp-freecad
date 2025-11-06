# Installation Scripts Guide

This directory contains installation scripts to set up MCP-FreeCAD on your system. Choose the appropriate script for your operating system.

## Quick Start

### Linux and macOS

```bash
chmod +x install.sh
./install.sh
```

### Windows Systems

```batch
install.bat
```

### Using Python Directly

For all platforms:

```bash
python install.py
```

## What These Scripts Do

All scripts perform the same three-step installation:

1. **Install FreeCAD Addon**
   - Copies addon to FreeCAD user modules directory
   - Installs to correct location for your OS

2. **Install MCP Server Dependencies**
   - Runs `pip install -r requirements.txt`
   - Installs all required Python packages

3. **Configure VS Code**
   - Creates/updates `mcp.json` configuration file
   - Adds FreeCAD MCP server entry

4. **Run Tests**
   - Verifies addon installation
   - Tests MCP server import
   - Ensures all components working

## Advanced Usage

### Linux and macOS Scripts

```bash
# Install only FreeCAD addon
./install.sh --addon-only

# Install only MCP server
./install.sh --server-only

# Configure only VS Code
./install.sh --vscode-only

# Skip tests for faster installation
./install.sh --no-test

# Full installation with verbose output
./install.sh --verbose

# Show help
./install.sh --help
```

### Windows Batch Scripts

```batch
REM Install only FreeCAD addon
install.bat --addon-only

REM Install only MCP server
install.bat --server-only

REM Configure only VS Code
install.bat --vscode-only

REM Skip tests for faster installation
install.bat --no-test

REM Full installation with verbose output
install.bat --verbose

REM Show help
install.bat --help
```

### Python Script Direct

```bash
# Full installation
python install.py

# With specific options
python install.py --addon-only --no-test --verbose

# See all options
python install.py --help
```

## 🔍 Script Comparison

| Feature | install.sh | install.bat | install.py |
|---------|-----------|-----------|-----------|
| Platform | Linux, macOS | Windows | All |
| Colors | Yes | Basic | Yes |
| Easy to use | Yes | Yes | No |
| Full control | Via args | Via args | Recommended |
| Error handling | Excellent | Good | Best |

## Features

### All Scripts Support

- Platform detection (Linux, macOS, Windows)
- Python version checking (3.8+)
- Component selection
- Error handling
- Verification tests
- Helpful error messages

### Shell Script Features (install.sh)

- Colored terminal output
- Advanced POSIX shell features
- Progress indication
- Environment variable setup

### Batch Script Features (install.bat)

- Windows-specific path handling
- Registry-aware configuration
- Batch file optimizations
- CMD.exe compatibility

### Python Script Features (install.py)

- Most reliable across platforms
- Detailed error reporting
- Progress tracking
- Configuration validation

## 🐛 Troubleshooting

### Script Won't Run (Linux/macOS)

```bash
# Make script executable
chmod +x install.sh

# Then run it
./install.sh
```

### Python Not Found

**Linux/macOS:**
```bash
# Check if Python 3 is installed
which python3
python3 --version

# If not installed, use your package manager
# Ubuntu/Debian
sudo apt install python3

# macOS with Homebrew
brew install python3
```

**Windows:**
1. Download Python from <https://www.python.org/>
2. During installation, check "Add Python to PATH"
3. Restart terminal after installation

### Permission Denied (Linux/macOS)

```bash
# Make script executable
chmod +x install.sh

# Or run with explicit Python interpreter
python3 install.sh
```

### Permission Denied (Windows)

Run Command Prompt as Administrator:
1. Press Win+X
2. Select "Command Prompt (Admin)" or "Terminal (Admin)"
3. Navigate to script directory
4. Run `install.bat`

### Installation Failed

1. Check Python version: `python3 --version`
2. Run with verbose output: `./install.sh --verbose`
3. Check internet connection
4. Try component-based installation: `./install.sh --server-only`

## 📚 Configuration Files

After installation, you can find:

**FreeCAD Addon**
- Linux: `~/.local/share/FreeCAD/Mod/MCPIntegration/`
- macOS: `~/Library/Preferences/FreeCAD/Mod/MCPIntegration/`
- Windows: `%APPDATA%\FreeCAD\Mod\MCPIntegration\`

**VS Code Configuration**
- Linux: `~/.config/Code/User/mcp.json`
- macOS: `~/Library/Application Support/Code/User/mcp.json`
- Windows: `%APPDATA%\Code\User\mcp.json`

## 🔗 Related Documentation

- [Installation Guide](INSTALLATION.md) - Detailed installation instructions
- [Main README](README.md) - Project overview
- [FreeCAD Addon Documentation](freecad-ai/INSTALL.md) - Addon-specific guide
- [Connection Methods](docs/CONNECTION_METHODS.md) - MCP connection options

## 🆘 Getting Help

If installation fails:

1. **Check the error message** - Most errors are self-explanatory
2. **Run with verbose output** - `./install.sh --verbose`
3. **Try component installation** - `./install.sh --addon-only`
4. **Check prerequisites** - Python 3.8+, FreeCAD 0.20.0+
5. **Review logs** - Check terminal output for specific errors

For persistent issues:

1. Report on GitHub: <https://github.com/jango-blockchained/mcp-freecad/issues>
2. Include: Python version, OS version, error messages, full terminal output
3. Attach `--verbose` output if possible

## 🎉 After Installation

Once installation is complete:

1. **Restart FreeCAD** - Addon will auto-load
2. **Restart VS Code** - MCP configuration takes effect
3. **Configure API keys** - Add your Claude/Gemini/OpenRouter keys
4. **Test the connection** - Use FreeCAD to create a test object
5. **Start designing** - Use AI assistance for CAD tasks

## ❓ FAQ

### Can I install multiple times?

Yes! The installer can be run multiple times. It will:
- Update existing FreeCAD addon
- Upgrade Python packages
- Reconfigure VS Code settings

### Can I use a custom FreeCAD installation?

The installer auto-detects FreeCAD. If it doesn't find it, ensure:
1. FreeCAD is installed and in PATH
2. You've launched FreeCAD at least once
3. FreeCAD user directory exists

### Do I need internet for installation?

Yes - the installer downloads and installs Python packages from PyPI.

### Can I install for multiple users?

Each user must run the installer individually as it installs to home directory.

### What if I want to uninstall?

Remove these:
1. FreeCAD addon directory (see paths above)
2. Python packages: `pip uninstall fastmcp mcp requests loguru psutil fastapi pydantic aiohttp`
3. VS Code config entry in `mcp.json`

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-06  
**Maintainer**: jango-blockchained
