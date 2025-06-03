# 📦 Installation Guide - MCP Integration FreeCAD Addon

This guide will help you install and configure the MCP Integration addon for FreeCAD.

## 📋 Prerequisites

### System Requirements
- **FreeCAD**: Version 0.20.0 or newer
- **Python**: Version 3.8 or newer (included with FreeCAD)
- **Operating System**: Windows, macOS, or Linux

### Required Dependencies
The addon requires these Python packages (automatically installed):
- `PySide2` (included with FreeCAD)
- `requests` (for API communication)
- `modelcontextprotocol` (MCP SDK)

## 🚀 Installation Methods

### Method 1: FreeCAD Addon Manager (Recommended)

1. **Open FreeCAD**
2. **Go to Tools → Addon Manager**
3. **Search for "MCP Integration"**
4. **Click Install**
5. **Restart FreeCAD**

> **Note**: If the addon is not yet in the official repository, use Method 2 or 3.

### Method 2: Manual Installation

1. **Download the addon**:
   ```bash
   git clone https://github.com/jango-blockchained/mcp-freecad.git
   ```

2. **Navigate to FreeCAD's user modules directory**:
   - **Windows**: `%APPDATA%\FreeCAD\Mod\`
   - **macOS**: `~/Library/Preferences/FreeCAD/Mod/`
   - **Linux**: `~/.local/share/FreeCAD/Mod/` or `~/.FreeCAD/Mod/`

3. **Copy the addon folder**:
   ```bash
   cp -r mcp-freecad/freecad-addon ~/.local/share/FreeCAD/Mod/MCPIntegration
   ```

4. **Install Python dependencies**:
   ```bash
   # In FreeCAD Python console:
   import subprocess
   import sys
   subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "modelcontextprotocol"])
   ```

5. **Restart FreeCAD**

### Method 3: Development Installation (For Contributors)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/jango-blockchained/mcp-freecad.git
   cd mcp-freecad
   ```

2. **Create a symbolic link**:
   ```bash
   # Linux/macOS
   ln -s $(pwd)/freecad-addon ~/.local/share/FreeCAD/Mod/MCPIntegration
   
   # Windows (run as Administrator)
   mklink /D "%APPDATA%\FreeCAD\Mod\MCPIntegration" "C:\path\to\mcp-freecad\freecad-addon"
   ```

3. **Install dependencies in development mode**:
   ```bash
   pip install -e .
   ```

## ⚙️ Configuration

### First-Time Setup

1. **Start FreeCAD**
2. **Switch to MCP Integration Workbench**:
   - Use the workbench dropdown in the toolbar
   - Select "MCP Integration"

3. **Configure AI Providers**:
   - Go to the **AI Models** tab
   - Select your preferred provider (Claude, Gemini, or OpenRouter)
   - Enter your API key
   - Test the connection

### API Key Setup

#### Claude (Anthropic)
1. Get your API key from [console.anthropic.com](https://console.anthropic.com/)
2. Enter in the Claude API Key field
3. Select Claude 4 model with Thinking Mode

#### Gemini (Google)
1. Get your API key from [makersuite.google.com](https://makersuite.google.com/app/apikey)
2. Enter in the Gemini API Key field

#### OpenRouter
1. Get your API key from [openrouter.ai](https://openrouter.ai/)
2. Enter in the OpenRouter API Key field
3. Choose from 13+ available models

### MCP Server Connection

The addon can connect to MCP servers using various methods:

1. **Launcher** (Recommended):
   - Automatically uses the extracted AppImage
   - No additional configuration needed

2. **Wrapper**:
   - Uses subprocess for isolation
   - Good for development

3. **Server**:
   - Connects to existing MCP server
   - Configure host and port in settings

4. **Bridge**:
   - Uses FreeCAD CLI
   - Requires FreeCAD in system PATH

## 🔍 Verification

### Check Installation

1. **Open FreeCAD**
2. **Check workbench list**:
   - "MCP Integration" should appear in the dropdown

3. **Switch to MCP Integration workbench**
4. **Check for toolbar**:
   - Should see MCP toolbar with 3 buttons

5. **Open the interface**:
   - Click "Show MCP Interface" button
   - Or use menu: MCP → Show Interface

### Test Functionality

1. **Test AI Connection**:
   - Go to AI Models tab
   - Enter API key
   - Click "Test Connection"
   - Should see "Connection successful"

2. **Test Tool Execution**:
   - Go to Tools tab
   - Select "Primitives"
   - Try creating a box
   - Should see new object in 3D view

## 🔧 Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'requests'"
```python
# In FreeCAD Python console:
import subprocess
import sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
```

#### "Workbench not showing up"
1. Check installation path
2. Ensure folder is named correctly
3. Restart FreeCAD
4. Check Report View for errors

#### "API connection failed"
1. Verify API key is correct
2. Check internet connection
3. Ensure firewall isn't blocking
4. Try different API endpoint

### Getting Help

1. **Check logs**:
   - Go to Logs tab in MCP interface
   - Look for error messages

2. **Report View**:
   - View → Panels → Report view
   - Check for Python errors

3. **GitHub Issues**:
   - [Report bugs](https://github.com/jango-blockchained/mcp-freecad/issues)
   - Include FreeCAD version and error logs

## 📚 Next Steps

1. **Read the documentation**:
   - [README.md](README.md) - Overview and features
   - [AI_MODELS_SUPPORTED.md](AI_MODELS_SUPPORTED.md) - AI provider details
   - [THINKING_MODE_GUIDE.md](THINKING_MODE_GUIDE.md) - Claude thinking mode

2. **Try examples**:
   - Create primitives with AI assistance
   - Perform boolean operations
   - Export models to STL

3. **Join the community**:
   - Report issues on GitHub
   - Contribute improvements
   - Share your creations

## 🎉 Success!

You've successfully installed the MCP Integration addon for FreeCAD. Enjoy AI-powered CAD design!

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-27  
**Author**: jango-blockchained 
