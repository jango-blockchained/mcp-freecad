"""
Utilities package for MCP FreeCAD Addon

This package contains utility functions and helper classes
for the MCP integration addon.
"""

__version__ = "1.0.0"

# Import utility classes
try:
    from .mcp_bridge import MCPBridge
    from .config_utils import ConfigUtils
    from .logging_utils import LoggingUtils
    
    __all__ = ['MCPBridge', 'ConfigUtils', 'LoggingUtils']
    
except ImportError as e:
    print(f"Utility components not fully available: {e}")
    __all__ = []