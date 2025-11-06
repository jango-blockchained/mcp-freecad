#!/usr/bin/env python3
"""
Simple MCP server startup script for Cursor IDE integration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from mcp import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        TextContent,
        Tool,
    )
except ImportError:
    print("MCP package not found. Installing...")
    os.system("pip install mcp")
    from mcp import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        TextContent,
        Tool,
    )

# Try to import FreeCAD connection
try:
    from mcp_freecad.client.freecad_connection_manager import FreeCADConnection
    FREECAD_AVAILABLE = True
except ImportError:
    FREECAD_AVAILABLE = False

server = Server("freecad-mcp-server")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    tools = [
        Tool(
            name="test_connection",
            description="Test connection to FreeCAD",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]
    
    if FREECAD_AVAILABLE:
        tools.extend([
            Tool(
                name="create_box",
                description="Create a box in FreeCAD",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "length": {"type": "number", "description": "Length of the box"},
                        "width": {"type": "number", "description": "Width of the box"},
                        "height": {"type": "number", "description": "Height of the box"},
                    },
                    "required": ["length", "width", "height"],
                },
            ),
            Tool(
                name="create_document",
                description="Create a new FreeCAD document",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the document"},
                    },
                    "required": ["name"],
                },
            ),
        ])
    
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "test_connection":
        if FREECAD_AVAILABLE:
            try:
                fc = FreeCADConnection(auto_connect=True)
                if fc.is_connected():
                    connection_type = fc.get_connection_type()
                    version = fc.get_version()
                    return [
                        TextContent(
                            type="text",
                            text=f"✅ FreeCAD connection successful!\nConnection type: {connection_type}\nFreeCAD version: {version}"
                        )
                    ]
                else:
                    return [
                        TextContent(
                            type="text",
                            text="❌ FreeCAD connection failed. Make sure FreeCAD is running and accessible."
                        )
                    ]
            except Exception as e:
                return [
                    TextContent(
                        type="text",
                        text=f"❌ Error connecting to FreeCAD: {str(e)}"
                    )
                ]
        else:
            return [
                TextContent(
                    type="text",
                    text="❌ FreeCAD modules not available. Make sure FreeCAD is properly installed."
                )
            ]
    
    elif name == "create_box" and FREECAD_AVAILABLE:
        try:
            fc = FreeCADConnection(auto_connect=True)
            if fc.is_connected():
                length = arguments.get("length", 10)
                width = arguments.get("width", 10)
                height = arguments.get("height", 10)
                
                box_id = fc.create_box(length=length, width=width, height=height)
                return [
                    TextContent(
                        type="text",
                        text=f"✅ Box created successfully! ID: {box_id}\nDimensions: {length} x {width} x {height}"
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text",
                        text="❌ FreeCAD connection failed. Make sure FreeCAD is running."
                    )
                ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"❌ Error creating box: {str(e)}"
                )
            ]
    
    elif name == "create_document" and FREECAD_AVAILABLE:
        try:
            fc = FreeCADConnection(auto_connect=True)
            if fc.is_connected():
                doc_name = arguments.get("name", "MyDocument")
                doc_id = fc.create_document(doc_name)
                return [
                    TextContent(
                        type="text",
                        text=f"✅ Document '{doc_name}' created successfully! ID: {doc_id}"
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text",
                        text="❌ FreeCAD connection failed. Make sure FreeCAD is running."
                    )
                ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"❌ Error creating document: {str(e)}"
                )
            ]
    
    else:
        return [
            TextContent(
                type="text",
                text=f"❌ Unknown tool: {name}"
            )
        ]

async def main():
    """Run the server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
