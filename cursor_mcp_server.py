#!/usr/bin/env python3
"""
FastMCP-based MCP server for Cursor IDE integration.

This server uses the latest fastmcp library following best practices:
- Uses @mcp.tool decorator for tools
- Uses @mcp.resource decorator for resources  
- Simple, clean implementation
- Async support for I/O operations
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastmcp import FastMCP

# Try to import FreeCAD connection
try:
    from mcp_freecad.client.freecad_connection_manager import FreeCADConnection
    FREECAD_AVAILABLE = True
except ImportError:
    FREECAD_AVAILABLE = False

# Create FastMCP server instance
mcp = FastMCP("freecad-mcp-server")


# Resources (read-only data endpoints)
@mcp.resource("freecad://status")
def get_server_status() -> dict:
    """Get FreeCAD MCP server status."""
    return {
        "server": "freecad-mcp-server",
        "version": "2.0.0",
        "freecad_available": FREECAD_AVAILABLE,
        "status": "running"
    }


# Tools (callable functions)
@mcp.tool()
def test_connection() -> str:
    """Test connection to FreeCAD.
    
    Returns:
        Connection status message
    """
    if not FREECAD_AVAILABLE:
        return "❌ FreeCAD modules not available. Make sure FreeCAD is properly installed."
    
    try:
        fc = FreeCADConnection(auto_connect=True)
        if fc.is_connected():
            connection_type = fc.get_connection_type()
            version = fc.get_version()
            return f"✅ FreeCAD connection successful!\nConnection type: {connection_type}\nFreeCAD version: {version}"
        else:
            return "❌ FreeCAD connection failed. Make sure FreeCAD is running and accessible."
    except Exception as e:
        return f"❌ Error connecting to FreeCAD: {str(e)}"


@mcp.tool()
def create_box(length: float, width: float, height: float) -> str:
    """Create a box in FreeCAD.
    
    Args:
        length: Length of the box in mm
        width: Width of the box in mm
        height: Height of the box in mm
        
    Returns:
        Success message with box details
    """
    if not FREECAD_AVAILABLE:
        return "❌ FreeCAD modules not available."
    
    try:
        fc = FreeCADConnection(auto_connect=True)
        if not fc.is_connected():
            return "❌ FreeCAD connection failed. Make sure FreeCAD is running."
        
        box_id = fc.create_box(length=length, width=width, height=height)
        return f"✅ Box created successfully! ID: {box_id}\nDimensions: {length} x {width} x {height}"
    except Exception as e:
        return f"❌ Error creating box: {str(e)}"


@mcp.tool()
def create_document(name: str) -> str:
    """Create a new FreeCAD document.
    
    Args:
        name: Name of the document
        
    Returns:
        Success message with document details
    """
    if not FREECAD_AVAILABLE:
        return "❌ FreeCAD modules not available."
    
    try:
        fc = FreeCADConnection(auto_connect=True)
        if not fc.is_connected():
            return "❌ FreeCAD connection failed. Make sure FreeCAD is running."
        
        doc_id = fc.create_document(name)
        return f"✅ Document '{name}' created successfully! ID: {doc_id}"
    except Exception as e:
        return f"❌ Error creating document: {str(e)}"


@mcp.tool()
def create_cylinder(radius: float, height: float) -> str:
    """Create a cylinder in FreeCAD.
    
    Args:
        radius: Radius of the cylinder in mm
        height: Height of the cylinder in mm
        
    Returns:
        Success message with cylinder details
    """
    if not FREECAD_AVAILABLE:
        return "❌ FreeCAD modules not available."
    
    try:
        fc = FreeCADConnection(auto_connect=True)
        if not fc.is_connected():
            return "❌ FreeCAD connection failed. Make sure FreeCAD is running."
        
        cylinder_id = fc.create_cylinder(radius=radius, height=height)
        return f"✅ Cylinder created successfully! ID: {cylinder_id}\nRadius: {radius}, Height: {height}"
    except Exception as e:
        return f"❌ Error creating cylinder: {str(e)}"


@mcp.tool()
def create_sphere(radius: float) -> str:
    """Create a sphere in FreeCAD.
    
    Args:
        radius: Radius of the sphere in mm
        
    Returns:
        Success message with sphere details
    """
    if not FREECAD_AVAILABLE:
        return "❌ FreeCAD modules not available."
    
    try:
        fc = FreeCADConnection(auto_connect=True)
        if not fc.is_connected():
            return "❌ FreeCAD connection failed. Make sure FreeCAD is running."
        
        sphere_id = fc.create_sphere(radius=radius)
        return f"✅ Sphere created successfully! ID: {sphere_id}\nRadius: {radius}"
    except Exception as e:
        return f"❌ Error creating sphere: {str(e)}"


if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()
