"""
Utilities package for MCP FreeCAD Addon

This package contains utility functions and helper classes
for the MCP integration addon.
"""

__version__ = "1.0.0"

# Import utility classes
from .cad_context_extractor import CADContextExtractor, get_cad_context_extractor

__all__ = ["CADContextExtractor", "get_cad_context_extractor"]
