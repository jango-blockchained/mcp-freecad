"""
MCP FreeCAD Addon - Model Context Protocol Integration for FreeCAD

This addon provides a comprehensive GUI interface for managing MCP connections,
servers, and AI model integrations within FreeCAD.

Features:
- Connection management for multiple MCP methods
- Server monitoring and control
- AI model integration (Claude, Gemini, OpenRouter)
- Real-time monitoring and diagnostics
- Tool management interface
- Modern Qt-based GUI

Author: MCP-FreeCAD Development Team
License: MIT
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "jango-blockchained"
__license__ = "MIT"

# FreeCAD addon metadata
ADDON_NAME = "MCP Integration"
ADDON_DESCRIPTION = "Model Context Protocol Integration for AI-powered CAD"
ADDON_AUTHOR = "jango-blockchained"
ADDON_VERSION = __version__
ADDON_LICENSE = __license__

# Import main components when the addon is loaded
try:
    import FreeCAD
    import FreeCADGui

    # Check if we're in GUI mode
    if FreeCAD.GuiUp:
        # Import will be handled by InitGui.py
        pass
    else:
        FreeCAD.Console.PrintMessage("MCP FreeCAD Addon: GUI not available, console mode only\n")

except ImportError as e:
    print(f"MCP FreeCAD Addon: Failed to import FreeCAD modules: {e}")# Addon information for FreeCAD
def getInfo():
    """Return addon information for FreeCAD addon manager."""
    return {
        "name": ADDON_NAME,
        "description": ADDON_DESCRIPTION,
        "author": ADDON_AUTHOR,
        "version": ADDON_VERSION,
        "license": ADDON_LICENSE,
        "url": "https://github.com/jango-blockchained/mcp-freecad",
        "categories": ["AI", "Automation", "External"],
        "freecad_version": "0.20.0",
        "python_version": "3.8",
        "icon": "resources/icons/mcp_workbench.svg"
    }
