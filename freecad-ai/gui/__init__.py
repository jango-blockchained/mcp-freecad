"""
GUI Package for MCP FreeCAD Addon

Author: jango-blockchained

This package contains all GUI components for the MCP integration interface.
"""

__version__ = "1.0.0"
__author__ = "MCP-FreeCAD Development Team"

# Import main components
try:
    # Try to import compact tools widget
    try:
        __all__ = [
            "MCPMainWidget",
            "ConnectionWidget",
            "ServerWidget",
            "ProvidersWidget",
            "ConversationWidget",
            "ToolsWidget",
            "CompactToolsWidget",
            "SettingsWidget",
        ]
    except ImportError:
        __all__ = [
            "MCPMainWidget",
            "ConnectionWidget",
            "ServerWidget",
            "ProvidersWidget",
            "ConversationWidget",
            "ToolsWidget",
            "SettingsWidget",
        ]

except ImportError as e:
    # Handle missing dependencies gracefully
    print(f"GUI components not fully available: {e}")
    __all__ = []
