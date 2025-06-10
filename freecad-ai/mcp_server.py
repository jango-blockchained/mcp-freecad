#!/usr/bin/env python3
"""
FreeCAD MCP Server

Model Context Protocol server that exposes FreeCAD functionality to Claude Desktop
and other MCP clients. Allows direct interaction with FreeCAD from Claude Desktop.

Author: jango-blockchained
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List

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
        TextContent,
        Tool,
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
        self.events_available = False
        
        # Events system components
        self.event_manager = None
        self.mcp_integration = None

        # Try to initialize FreeCAD
        self._init_freecad()
        
        # Try to initialize events system
        self._init_events_system()

        # Register MCP handlers
        self._register_handlers()

    def _init_freecad(self):
        """Initialize FreeCAD and tools."""
        try:
            # Try to import FreeCAD
            pass

            self.freecad_available = True
            logger.info("FreeCAD imported successfully")

            # Try to import tools
            try:
                from tools.export_import import ExportImportTool
                from tools.measurements import MeasurementsTool
                from tools.operations import OperationsTool
                from tools.primitives import PrimitivesTool

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

    def _init_events_system(self):
        """Initialize the events system."""
        try:
            from events import create_event_system, EVENTS_AVAILABLE
            
            if EVENTS_AVAILABLE:
                self.event_manager, self.mcp_integration = create_event_system()
                if self.event_manager and self.mcp_integration:
                    self.events_available = True
                    logger.info("Events system initialized successfully")
                else:
                    logger.warning("Failed to create events system components")
            else:
                logger.warning("Events system not available")
                
        except ImportError as e:
            logger.warning(f"Failed to import events system: {e}")

    async def _async_init_events(self):
        """Asynchronously initialize the events system."""
        if self.events_available and self.event_manager:
            try:
                success = await self.event_manager.initialize()
                if success:
                    logger.info("Events system async initialization complete")
                else:
                    logger.warning("Events system async initialization failed")
                    self.events_available = False
            except Exception as e:
                logger.error(f"Error during async events initialization: {e}")
                self.events_available = False

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

            # Events system tools
            if self.events_available:
                tools.extend([
                    Tool(
                        name="subscribe_to_events",
                        description="Subscribe to FreeCAD events",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "client_id": {
                                    "type": "string",
                                    "description": "Unique client identifier",
                                },
                                "event_types": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of event types to subscribe to (document_changed, command_executed, error, selection_changed, etc.). Leave empty for all events.",
                                },
                            },
                            "required": ["client_id"],
                        },
                    ),
                    Tool(
                        name="get_event_history",
                        description="Get recent event history",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "event_types": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Filter by specific event types",
                                },
                                "limit": {
                                    "type": "number",
                                    "description": "Maximum number of events to return (default: 50)",
                                },
                            },
                        },
                    ),
                    Tool(
                        name="get_command_history",
                        description="Get recent command execution history",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "limit": {
                                    "type": "number",
                                    "description": "Maximum number of commands to return (default: 20)",
                                },
                            },
                        },
                    ),
                    Tool(
                        name="get_error_history",
                        description="Get recent error history",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "limit": {
                                    "type": "number",
                                    "description": "Maximum number of errors to return (default: 10)",
                                },
                            },
                        },
                    ),
                    Tool(
                        name="get_events_system_status",
                        description="Get the status of the events system",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                        },
                    ),
                    Tool(
                        name="emit_custom_event",
                        description="Emit a custom event",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "event_type": {
                                    "type": "string",
                                    "description": "Type of the custom event",
                                },
                                "event_data": {
                                    "type": "object",
                                    "description": "Event data as JSON object",
                                },
                            },
                            "required": ["event_type", "event_data"],
                        },
                    ),
                ])

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

            # Events system tools
            elif name == "subscribe_to_events":
                if not self.events_available:
                    result = {"success": False, "message": "Events system not available"}
                else:
                    client_id = arguments["client_id"]
                    event_types = arguments.get("event_types", None)
                    
                    # Register client if not already registered
                    await self.mcp_integration.register_mcp_client(client_id, {
                        "name": f"MCP Client {client_id}",
                        "subscribed_at": asyncio.get_event_loop().time()
                    })
                    
                    # Subscribe to events
                    success = await self.mcp_integration.subscribe_to_events(client_id, event_types)
                    if success:
                        result = {
                            "success": True, 
                            "message": f"Subscribed client {client_id} to events: {event_types or 'all'}"
                        }
                    else:
                        result = {"success": False, "message": "Failed to subscribe to events"}

            elif name == "get_event_history":
                if not self.events_available:
                    result = {"success": False, "message": "Events system not available"}
                else:
                    event_types = arguments.get("event_types", None)
                    limit = arguments.get("limit", 50)
                    
                    history = await self.event_manager.get_event_history(
                        event_types=event_types, limit=limit
                    )
                    result = {
                        "success": True,
                        "events": history,
                        "count": len(history)
                    }

            elif name == "get_command_history":
                if not self.events_available:
                    result = {"success": False, "message": "Events system not available"}
                else:
                    limit = arguments.get("limit", 20)
                    
                    history = await self.event_manager.get_command_history(limit=limit)
                    result = {
                        "success": True,
                        "commands": history,
                        "count": len(history)
                    }

            elif name == "get_error_history":
                if not self.events_available:
                    result = {"success": False, "message": "Events system not available"}
                else:
                    limit = arguments.get("limit", 10)
                    
                    history = await self.event_manager.get_error_history(limit=limit)
                    result = {
                        "success": True,
                        "errors": history,
                        "count": len(history)
                    }

            elif name == "get_events_system_status":
                if not self.events_available:
                    result = {"success": False, "message": "Events system not available"}
                else:
                    status = await self.event_manager.get_system_status()
                    result = {
                        "success": True,
                        "status": status
                    }

            elif name == "emit_custom_event":
                if not self.events_available:
                    result = {"success": False, "message": "Events system not available"}
                else:
                    event_type = arguments["event_type"]
                    event_data = arguments["event_data"]
                    
                    success = await self.event_manager.emit_custom_event(event_type, event_data)
                    if success:
                        result = {
                            "success": True,
                            "message": f"Emitted custom event: {event_type}"
                        }
                    else:
                        result = {"success": False, "message": "Failed to emit custom event"}

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
        logger.info(f"Events available: {self.events_available}")

        # Initialize events system asynchronously
        if self.events_available:
            await self._async_init_events()

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
