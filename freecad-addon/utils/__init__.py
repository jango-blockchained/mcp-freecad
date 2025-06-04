"""
Utilities package for MCP FreeCAD Addon

This package contains utility functions and helper classes
for the MCP integration addon.
"""

__version__ = "1.0.0"

# Import utility classes
try:
    from .mcp_bridge import MCPBridge
    from .dependency_manager import DependencyManager, get_aiohttp_install_script

    __all__ = ['MCPBridge', 'DependencyManager', 'get_aiohttp_install_script']

except ImportError as e:
    print(f"Utility components not fully available: {e}")
    __all__ = []

from .cad_context_extractor import CADContextExtractor, get_cad_context_extractor

__all__ = ['CADContextExtractor', 'get_cad_context_extractor']
