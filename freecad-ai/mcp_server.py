#!/usr/bin/env python3
"""
FreeCAD MCP Server

Model Context Protocol server that exposes FreeCAD functionality to Claude Desktop
and other MCP clients. Allows direct interaction with FreeCAD from Claude Desktop.

Author: jango-blockchained
"""

import asyncio
import json
import sys
import os
import logging
from typing import Any, Dict, List, Optional, Sequence

# Add the addon directory to Python path
addon_dir = os.path.dirname(os.path.abspath(__file__))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        CallToolRequest,
        CallToolResult,
        ListResourcesRequest,
        ListResourcesResult,
        ListToolsRequest,
        ListToolsResult,
        ReadResourceRequest,
        ReadResourceResult,
    )

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("freecad-mcp-server")


class FreeCADMCPServer:
    """MCP Server for FreeCAD integration."""

    def __init__(self):
        """Initialize the FreeCAD MCP server."""
        self.server = Server("freecad-mcp-server")
        self.freecad_available = False
        self.tools_available = False

        # Try to initialize FreeCAD
        self._init_freecad()

        # Register MCP handlers
        self._register_handlers()

    def _init_freecad(self):
        """Initialize FreeCAD and tools."""
        try:
            # Try to import FreeCAD
            import FreeCAD
            import FreeCADGui

            self.freecad_available = True
            logger.info("FreeCAD imported successfully")

            # Try to import tools
            try:
                from tools.primitives import PrimitivesTool
                from tools.operations import OperationsTool
                from tools.measurements import MeasurementsTool
                from tools.export_import import ExportImportTool

                self.primitives_tool = PrimitivesTool()
                self.operations_tool = OperationsTool()
                self.measurements_tool = MeasurementsTool()
                self.export_import_tool = ExportImportTool()
                self.tools_available = True
                logger.info("FreeCAD tools imported successfully")

            except ImportError as e:
                logger.warning(f"Failed to import FreeCAD tools: {e}")

        except ImportError as e:
            logger.warning(f"Failed to import FreeCAD: {e}")

    def _register_handlers(self):
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available FreeCAD tools."""
            tools = []

            if not self.tools_available:
                return tools

            # Primitive creation tools
            tools.extend(
                [
                    Tool(
                        name="create_box",
                        description="Create a box/cube primitive in FreeCAD",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "length": {
                                    "type": "number",
                                    "description": "Length of the box (mm)",
                                },
                                "width": {
                                    "type": "number",
                                    "description": "Width of the box (mm)",
                                },
                                "height": {
                                    "type": "number",
                                    "description": "Height of the box (mm)",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Optional name for the object",
                                },
                            },
                            "required": ["length", "width", "height"],
                        },
                    ),
                    Tool(
                        name="create_cylinder",
                        description="Create a cylinder primitive in FreeCAD",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "radius": {
                                    "type": "number",
                                    "description": "Radius of the cylinder (mm)",
                                },
                                "height": {
                                    "type": "number",
                                    "description": "Height of the cylinder (mm)",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Optional name for the object",
                                },
                            },
                            "required": ["radius", "height"],
                        },
                    ),
                    Tool(
                        name="create_sphere",
                        description="Create a sphere primitive in FreeCAD",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "radius": {
                                    "type": "number",
                                    "description": "Radius of the sphere (mm)",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Optional name for the object",
                                },
                            },
                            "required": ["radius"],
                        },
                    ),
                    Tool(
                        name="create_cone",
                        description="Create a cone primitive in FreeCAD",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "radius1": {
                                    "type": "number",
                                    "description": "Bottom radius of the cone (mm)",
                                },
                                "radius2": {
                                    "type": "number",
                                    "description": "Top radius of the cone (mm)",
                                },
                                "height": {
                                    "type": "number",
                                    "description": "Height of the cone (mm)",
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Optional name for the object",
                                },
                            },
                            "required": ["radius1", "radius2", "height"],
                        },
                    ),
                ]
            )

            # Boolean operation tools
            tools.extend(
                [
                    Tool(
                        name="boolean_union",
                        description="Perform boolean union of two objects",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "obj1_name": {
                                    "type": "string",
                                    "description": "Name of first object",
                                },
                                "obj2_name": {
                                    "type": "string",
                                    "description": "Name of second object",
                                },
                                "keep_originals": {
                                    "type": "boolean",
                                    "description": "Keep original objects",
                                    "default": False,
                                },
                            },
                            "required": ["obj1_name", "obj2_name"],
                        },
                    ),
                    Tool(
                        name="boolean_cut",
                        description="Perform boolean cut (subtraction) of two objects",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "obj1_name": {
                                    "type": "string",
                                    "description": "Object to cut from",
                                },
                                "obj2_name": {
                                    "type": "string",
                                    "description": "Object to cut with",
                                },
                                "keep_originals": {
                                    "type": "boolean",
                                    "description": "Keep original objects",
                                    "default": False,
                                },
                            },
                            "required": ["obj1_name", "obj2_name"],
                        },
                    ),
                    Tool(
                        name="boolean_intersection",
                        description="Perform boolean intersection of two objects",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "obj1_name": {
                                    "type": "string",
                                    "description": "Name of first object",
                                },
                                "obj2_name": {
                                    "type": "string",
                                    "description": "Name of second object",
                                },
                                "keep_originals": {
                                    "type": "boolean",
                                    "description": "Keep original objects",
                                    "default": False,
                                },
                            },
                            "required": ["obj1_name", "obj2_name"],
                        },
                    ),
                ]
            )

            # Measurement tools
            tools.extend(
                [
                    Tool(
                        name="measure_distance",
                        description="Measure distance between two points or objects",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "point1": {
                                    "type": "string",
                                    "description": "First point or object name",
                                },
                                "point2": {
                                    "type": "string",
                                    "description": "Second point or object name",
                                },
                            },
                            "required": ["point1", "point2"],
                        },
                    ),
                    Tool(
                        name="measure_volume",
                        description="Measure volume of an object",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "obj_name": {
                                    "type": "string",
                                    "description": "Name of object to measure",
                                }
                            },
                            "required": ["obj_name"],
                        },
                    ),
                    Tool(
                        name="measure_area",
                        description="Measure surface area of an object",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "obj_name": {
                                    "type": "string",
                                    "description": "Name of object to measure",
                                }
                            },
                            "required": ["obj_name"],
                        },
                    ),
                ]
            )

            # Export/Import tools
            tools.extend(
                [
                    Tool(
                        name="export_stl",
                        description="Export objects to STL file",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "filepath": {
                                    "type": "string",
                                    "description": "Output file path",
                                },
                                "object_names": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Objects to export (empty = all)",
                                },
                                "ascii": {
                                    "type": "boolean",
                                    "description": "Use ASCII format",
                                    "default": False,
                                },
                            },
                            "required": ["filepath"],
                        },
                    ),
                    Tool(
                        name="export_step",
                        description="Export objects to STEP file",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "filepath": {
                                    "type": "string",
                                    "description": "Output file path",
                                },
                                "object_names": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Objects to export (empty = all)",
                                },
                            },
                            "required": ["filepath"],
                        },
                    ),
                    Tool(
                        name="list_objects",
                        description="List all objects in the current FreeCAD document",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                    Tool(
                        name="create_document",
                        description="Create a new FreeCAD document",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Document name",
                                }
                            },
                        },
                    ),
                ]
            )

            return tools

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[TextContent]:
            """Handle tool calls from Claude."""
            if not self.tools_available:
                return [
                    TextContent(
                        type="text", text="Error: FreeCAD tools are not available"
                    )
                ]

            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(type="text", text=str(result))]
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [
                    TextContent(type="text", text=f"Error executing {name}: {str(e)}")
                ]

        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available FreeCAD resources."""
            resources = []

            if self.freecad_available:
                resources.append(
                    Resource(
                        uri="freecad://document/info",
                        name="FreeCAD Document Info",
                        description="Information about the current FreeCAD document",
                        mimeType="application/json",
                    )
                )

                resources.append(
                    Resource(
                        uri="freecad://objects/list",
                        name="FreeCAD Objects",
                        description="List of all objects in the current document",
                        mimeType="application/json",
                    )
                )

            return resources

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read FreeCAD resource content."""
            if not self.freecad_available:
                return json.dumps({"error": "FreeCAD not available"})

            try:
                import FreeCAD

                if uri == "freecad://document/info":
                    doc = FreeCAD.ActiveDocument
                    if doc:
                        info = {
                            "name": doc.Name,
                            "label": doc.Label,
                            "object_count": len(doc.Objects),
                            "file_name": (
                                doc.FileName if hasattr(doc, "FileName") else None
                            ),
                        }
                    else:
                        info = {"error": "No active document"}
                    return json.dumps(info, indent=2)

                elif uri == "freecad://objects/list":
                    doc = FreeCAD.ActiveDocument
                    if doc:
                        objects = []
                        for obj in doc.Objects:
                            obj_info = {
                                "name": obj.Name,
                                "label": obj.Label,
                                "type": obj.TypeId,
                                "visible": (
                                    obj.ViewObject.Visibility
                                    if hasattr(obj, "ViewObject")
                                    else True
                                ),
                            }
                            objects.append(obj_info)
                        return json.dumps({"objects": objects}, indent=2)
                    else:
                        return json.dumps({"error": "No active document"})

                else:
                    return json.dumps({"error": f"Unknown resource: {uri}"})

            except Exception as e:
                return json.dumps({"error": str(e)})

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a FreeCAD tool."""
        try:
            # Primitive creation tools
            if name == "create_box":
                result = self.primitives_tool.create_box(
                    length=arguments["length"],
                    width=arguments["width"],
                    height=arguments["height"],
                    name=arguments.get("name"),
                )
            elif name == "create_cylinder":
                result = self.primitives_tool.create_cylinder(
                    radius=arguments["radius"],
                    height=arguments["height"],
                    name=arguments.get("name"),
                )
            elif name == "create_sphere":
                result = self.primitives_tool.create_sphere(
                    radius=arguments["radius"], name=arguments.get("name")
                )
            elif name == "create_cone":
                result = self.primitives_tool.create_cone(
                    radius1=arguments["radius1"],
                    radius2=arguments["radius2"],
                    height=arguments["height"],
                    name=arguments.get("name"),
                )

            # Boolean operations
            elif name == "boolean_union":
                result = self.operations_tool.boolean_union(
                    obj1_name=arguments["obj1_name"],
                    obj2_name=arguments["obj2_name"],
                    keep_originals=arguments.get("keep_originals", False),
                )
            elif name == "boolean_cut":
                result = self.operations_tool.boolean_cut(
                    obj1_name=arguments["obj1_name"],
                    obj2_name=arguments["obj2_name"],
                    keep_originals=arguments.get("keep_originals", False),
                )
            elif name == "boolean_intersection":
                result = self.operations_tool.boolean_intersection(
                    obj1_name=arguments["obj1_name"],
                    obj2_name=arguments["obj2_name"],
                    keep_originals=arguments.get("keep_originals", False),
                )

            # Measurements
            elif name == "measure_distance":
                result = self.measurements_tool.measure_distance(
                    point1=arguments["point1"], point2=arguments["point2"]
                )
            elif name == "measure_volume":
                result = self.measurements_tool.measure_volume(
                    obj_name=arguments["obj_name"]
                )
            elif name == "measure_area":
                result = self.measurements_tool.measure_area(
                    obj_name=arguments["obj_name"]
                )

            # Export/Import
            elif name == "export_stl":
                result = self.export_import_tool.export_stl(
                    filepath=arguments["filepath"],
                    object_names=arguments.get("object_names", []),
                    ascii=arguments.get("ascii", False),
                )
            elif name == "export_step":
                result = self.export_import_tool.export_step(
                    filepath=arguments["filepath"],
                    object_names=arguments.get("object_names", []),
                )

            # Document management
            elif name == "list_objects":
                import FreeCAD

                doc = FreeCAD.ActiveDocument
                if doc:
                    objects = [
                        {"name": obj.Name, "label": obj.Label, "type": obj.TypeId}
                        for obj in doc.Objects
                    ]
                    result = {"success": True, "objects": objects}
                else:
                    result = {"success": False, "message": "No active document"}

            elif name == "create_document":
                import FreeCAD

                doc_name = arguments.get("name", "MCPDocument")
                doc = FreeCAD.newDocument(doc_name)
                FreeCAD.setActiveDocument(doc.Name)
                result = {"success": True, "message": f"Created document: {doc.Name}"}

            else:
                result = {"success": False, "message": f"Unknown tool: {name}"}

            # Format result for display
            if isinstance(result, dict):
                if result.get("success"):
                    return f"✅ {result.get('message', 'Operation completed successfully')}"
                else:
                    return f"❌ {result.get('message', 'Operation failed')}"
            else:
                return str(result)

        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return f"❌ Error: {str(e)}"

    async def run(self):
        """Run the MCP server."""
        if not MCP_AVAILABLE:
            logger.error("MCP library not available. Please install: pip install mcp")
            return

        logger.info("Starting FreeCAD MCP Server...")
        logger.info(f"FreeCAD available: {self.freecad_available}")
        logger.info(f"Tools available: {self.tools_available}")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="freecad-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None, experimental_capabilities=None
                    ),
                ),
            )


async def main():
    """Main entry point."""
    server = FreeCADMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
