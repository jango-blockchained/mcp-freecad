"""
GUI Package for MCP FreeCAD Addon

Author: jango-blockchained

This package contains all GUI components for the MCP integration interface.
"""

__version__ = "1.0.0"
__author__ = "MCP-FreeCAD Development Team"

# Import main components
try:
    from .main_widget import MCPMainWidget
    from .connection_widget import ConnectionWidget
    from .server_widget import ServerWidget
    from .ai_widget import AIWidget
    from .tools_widget import ToolsWidget
    from .settings_widget import SettingsWidget
    from .logs_widget import LogsWidget

    __all__ = [
        'MCPMainWidget',
        'ConnectionWidget',
        'ServerWidget',
        'AIWidget',
        'ToolsWidget',
        'SettingsWidget',
        'LogsWidget'
    ]

except ImportError as e:
    # Handle missing dependencies gracefully
    print(f"GUI components not fully available: {e}")
    __all__ = []
