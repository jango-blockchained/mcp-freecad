#!/usr/bin/env python3
"""
FreeCAD MCP Server

This script implements a Model Context Protocol (MCP) server for FreeCAD.
It provides tools and resources for AI assistants to interact with FreeCAD.

Usage:
    python freecad_mcp_server.py
"""

import argparse
import asyncio
import json
import logging
import sys
from typing import Any, Dict
import os

# Version information
VERSION = "0.3.1"

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("freecad_mcp")

# Import MCP SDK (using `mcp` package)
try:
    import mcp
    from mcp.server import Server as MCPServer
    from mcp.server.stdio import stdio_server
    from mcp.server import InitializationOptions, NotificationOptions
    from mcp.types import JSONRPCRequest
    mcp_import_error = None
except ImportError as e:
    mcp_import_error = str(e)
    # Create dummy classes for type hints
    class MCPServer:
        pass

    class JSONRPCRequest:
        pass

    class InitializationOptions:
        pass

    class NotificationOptions:
        pass

# Import FreeCAD connection
try:
    from freecad_connection import FreeCADConnection

    FREECAD_CONNECTION_AVAILABLE = True
except ImportError:
    logger.warning(
        "FreeCAD connection module (freecad_connection.py) not found in the current directory or Python path."
    )
    FREECAD_CONNECTION_AVAILABLE = False
    # try:
    #     # Try to import the local smithery implementation
    #     from freecad_bridge import FreeCADBridge
    #     MCP_TOOLS_AVAILABLE = False
    # except ImportError:
    #     logger.warning("Local FreeCAD bridge not found. Some functionality may be limited.")


class FreeCADMCPServer:
    """
    FreeCAD MCP Server implementation.
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the FreeCAD MCP Server.

        Args:
            config_path: Path to the configuration file.
        """
        # Ensure config_path is absolute
        script_dir = os.path.dirname(os.path.abspath(__file__))
        absolute_config_path = os.path.join(script_dir, config_path)
        self.config = self._load_config(absolute_config_path)
        self.freecad_connection = None
        self.server = None
        self.tools = {}
        self.resources = {}

        # Initialize FreeCAD connection
        self._initialize_freecad_connection()

        # Initialize tool providers
        self._initialize_tool_providers()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from a JSON file."""
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            # Return default configuration
            return {
                "server": {"name": "freecad-mcp-server", "version": "0.1.0"},
                "freecad": {
                    "connection_method": "auto",  # auto, server, bridge, or mock
                    "host": "localhost",
                    "port": 12345,
                    "freecad_path": "freecad",
                },
            }

    def _initialize_freecad_connection(self):
        """Initialize connection to FreeCAD."""
        if not FREECAD_CONNECTION_AVAILABLE:
            logger.warning(
                "FreeCAD connection not available. Some features may not work."
            )
            return

        freecad_config = self.config.get("freecad", {})

        try:
            self.freecad_connection = FreeCADConnection(
                host=freecad_config.get("host", "localhost"),
                port=freecad_config.get("port", 12345),
                freecad_path=freecad_config.get("freecad_path", "freecad"),
                auto_connect=True,
                prefer_method=freecad_config.get("connection_method"),
                use_mock=freecad_config.get("use_mock", True)
            )

            if self.freecad_connection.is_connected():
                connection_type = self.freecad_connection.get_connection_type()
                logger.info(f"Connected to FreeCAD using {connection_type} method")

                # Get FreeCAD version
                version_info = self.freecad_connection.get_version()
                version_str = ".".join(
                    str(v) for v in version_info.get("version", ["Unknown"])
                )
                logger.info(f"FreeCAD version: {version_str}")
            else:
                logger.warning("Failed to connect to FreeCAD")
        except Exception as e:
            logger.error(f"Error initializing FreeCAD connection: {e}")

    def _initialize_tool_providers(self):
        """Initialize tool providers - populate the tools dictionary with available tools."""
        logger.info("Initializing tool providers...")
        self.tools = {}

        # Add basic FreeCAD document tools
        self.tools["freecad.create_document"] = {
            "name": "freecad.create_document",
            "description": "Create a new FreeCAD document",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the document"
                    }
                },
                "required": ["name"]
            }
        }

        self.tools["freecad.list_documents"] = {
            "name": "freecad.list_documents",
            "description": "List all open documents",
            "schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

        self.tools["freecad.list_objects"] = {
            "name": "freecad.list_objects",
            "description": "List all objects in the active document",
            "schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

        # Add primitive shape creation tools
        self.tools["freecad.create_box"] = {
            "name": "freecad.create_box",
            "description": "Create a box primitive",
            "schema": {
                "type": "object",
                "properties": {
                    "length": {
                        "type": "number",
                        "description": "Length of the box"
                    },
                    "width": {
                        "type": "number",
                        "description": "Width of the box"
                    },
                    "height": {
                        "type": "number",
                        "description": "Height of the box"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the box object"
                    },
                    "position_x": {
                        "type": "number",
                        "description": "X position of the box"
                    },
                    "position_y": {
                        "type": "number",
                        "description": "Y position of the box"
                    },
                    "position_z": {
                        "type": "number",
                        "description": "Z position of the box"
                    }
                },
                "required": ["length", "width", "height"]
            }
        }

        self.tools["freecad.create_cylinder"] = {
            "name": "freecad.create_cylinder",
            "description": "Create a cylinder primitive",
            "schema": {
                "type": "object",
                "properties": {
                    "radius": {
                        "type": "number",
                        "description": "Radius of the cylinder"
                    },
                    "height": {
                        "type": "number",
                        "description": "Height of the cylinder"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the cylinder object"
                    },
                    "position_x": {
                        "type": "number",
                        "description": "X position of the cylinder"
                    },
                    "position_y": {
                        "type": "number",
                        "description": "Y position of the cylinder"
                    },
                    "position_z": {
                        "type": "number",
                        "description": "Z position of the cylinder"
                    }
                },
                "required": ["radius", "height"]
            }
        }

        self.tools["freecad.create_sphere"] = {
            "name": "freecad.create_sphere",
            "description": "Create a sphere primitive",
            "schema": {
                "type": "object",
                "properties": {
                    "radius": {
                        "type": "number",
                        "description": "Radius of the sphere"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the sphere object"
                    },
                    "position_x": {
                        "type": "number",
                        "description": "X position of the sphere"
                    },
                    "position_y": {
                        "type": "number",
                        "description": "Y position of the sphere"
                    },
                    "position_z": {
                        "type": "number",
                        "description": "Z position of the sphere"
                    }
                },
                "required": ["radius"]
            }
        }

        self.tools["freecad.create_cone"] = {
            "name": "freecad.create_cone",
            "description": "Create a cone primitive",
            "schema": {
                "type": "object",
                "properties": {
                    "radius1": {
                        "type": "number",
                        "description": "Radius of the base"
                    },
                    "radius2": {
                        "type": "number",
                        "description": "Radius of the top (0 for a pointed cone)"
                    },
                    "height": {
                        "type": "number",
                        "description": "Height of the cone"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the cone object"
                    },
                    "position_x": {
                        "type": "number",
                        "description": "X position of the cone"
                    },
                    "position_y": {
                        "type": "number",
                        "description": "Y position of the cone"
                    },
                    "position_z": {
                        "type": "number",
                        "description": "Z position of the cone"
                    }
                },
                "required": ["radius1", "height"]
            }
        }

        # Add boolean operations
        self.tools["freecad.boolean_union"] = {
            "name": "freecad.boolean_union",
            "description": "Create a union of two objects (add them together)",
            "schema": {
                "type": "object",
                "properties": {
                    "object1": {
                        "type": "string",
                        "description": "First object name"
                    },
                    "object2": {
                        "type": "string",
                        "description": "Second object name"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the resulting object"
                    }
                },
                "required": ["object1", "object2"]
            }
        }

        self.tools["freecad.boolean_cut"] = {
            "name": "freecad.boolean_cut",
            "description": "Cut the second object from the first (subtract)",
            "schema": {
                "type": "object",
                "properties": {
                    "object1": {
                        "type": "string",
                        "description": "Base object name (to cut from)"
                    },
                    "object2": {
                        "type": "string",
                        "description": "Tool object name (to cut with)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the resulting object"
                    }
                },
                "required": ["object1", "object2"]
            }
        }

        self.tools["freecad.boolean_intersection"] = {
            "name": "freecad.boolean_intersection",
            "description": "Create the intersection of two objects (common volume)",
            "schema": {
                "type": "object",
                "properties": {
                    "object1": {
                        "type": "string",
                        "description": "First object name"
                    },
                    "object2": {
                        "type": "string",
                        "description": "Second object name"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the resulting object"
                    }
                },
                "required": ["object1", "object2"]
            }
        }

        # Add transformation tools
        self.tools["freecad.move_object"] = {
            "name": "freecad.move_object",
            "description": "Move an object to a new position",
            "schema": {
                "type": "object",
                "properties": {
                    "object_name": {
                        "type": "string",
                        "description": "Name of the object to move"
                    },
                    "x": {
                        "type": "number",
                        "description": "X position"
                    },
                    "y": {
                        "type": "number",
                        "description": "Y position"
                    },
                    "z": {
                        "type": "number",
                        "description": "Z position"
                    }
                },
                "required": ["object_name"]
            }
        }

        self.tools["freecad.rotate_object"] = {
            "name": "freecad.rotate_object",
            "description": "Rotate an object",
            "schema": {
                "type": "object",
                "properties": {
                    "object_name": {
                        "type": "string",
                        "description": "Name of the object to rotate"
                    },
                    "angle_x": {
                        "type": "number",
                        "description": "Rotation angle around X axis in degrees"
                    },
                    "angle_y": {
                        "type": "number",
                        "description": "Rotation angle around Y axis in degrees"
                    },
                    "angle_z": {
                        "type": "number",
                        "description": "Rotation angle around Z axis in degrees"
                    }
                },
                "required": ["object_name"]
            }
        }

        # Add export tools
        self.tools["freecad.export_stl"] = {
            "name": "freecad.export_stl",
            "description": "Export the model to an STL file",
            "schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to save the STL file"
                    },
                    "objects": {
                        "type": "array",
                        "description": "List of objects to export (empty for all objects)",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["file_path"]
            }
        }

        # Add smithery tools if enabled
        if self.config.get("tools", {}).get("enable_smithery", True):
            self.tools["smithery.create_anvil"] = {
                "name": "smithery.create_anvil",
                "description": "Create an anvil model",
                "schema": {
                    "type": "object",
                    "properties": {
                        "length": {
                            "type": "number",
                            "description": "Length of the anvil"
                        },
                        "width": {
                            "type": "number",
                            "description": "Width of the anvil"
                        },
                        "height": {
                            "type": "number",
                            "description": "Height of the anvil"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the anvil object"
                        }
                    },
                    "required": []
                }
            }

            self.tools["smithery.create_hammer"] = {
                "name": "smithery.create_hammer",
                "description": "Create a blacksmith hammer model",
                "schema": {
                    "type": "object",
                    "properties": {
                        "head_length": {
                            "type": "number",
                            "description": "Length of the hammer head"
                        },
                        "handle_length": {
                            "type": "number",
                            "description": "Length of the handle"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the hammer object"
                        }
                    },
                    "required": []
                }
            }

        # Initialize resources dictionary
        self.resources = {
            "freecad://info": {
                "uri": "freecad://info",
                "name": "FreeCAD Info"
            }
        }

        logger.info(f"Initialized {len(self.tools)} tools and {len(self.resources)} resources")

    async def start(self):
        """Start the MCP server."""
        try:
            # Initialize the MCP server with name, version, etc.
            server_config = self.config.get("server", {})
            self.server = MCPServer(server_config.get("name", "freecad-mcp-server"))

            # Register handlers
            self._setup_handlers()

            logger.info("Starting FreeCAD MCP Server...")

            # Use the proper stdio server pattern
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=server_config.get("name", "freecad-mcp-server"),
                        server_version=server_config.get("version", "0.1.0"),
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )

            logger.info("Server has completed")

        except Exception as e:
            logger.error(f"Error starting the server: {e}")
            raise

    def _setup_handlers(self):
        """Set up the MCP server handlers."""
        # Define handlers for the protocols

        # Save reference to self for closures
        instance = self

        # List Tools handler
        @self.server.list_tools()
        async def handle_list_tools():
            logger.debug("Handling list_tools request")
            return [
                {
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "schema": tool_info["schema"],
                }
                for tool_id, tool_info in instance.tools.items()
            ]

        # Call Tool handler
        @self.server.call_tool()
        async def handle_call_tool(name, arguments):
            logger.info(f"Executing tool: {name} with arguments: {arguments}")

            if name not in instance.tools:
                return {"error": f"Unknown tool: {name}"}

            try:
                # Handle smithery tools
                if name.startswith("smithery."):
                    return await instance._execute_smithery_tool(name, arguments)

                # Handle FreeCAD tools
                elif name.startswith("freecad."):
                    return await instance._execute_freecad_tool(name, arguments)

                return {"error": f"Tool not implemented: {name}"}
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return {"error": f"Error executing tool: {str(e)}"}

        # List Resources handler
        @self.server.list_resources()
        async def handle_list_resources():
            return [
                {"uri": resource_info["uri"], "name": resource_info["name"]}
                for resource_id, resource_info in instance.resources.items()
            ]

        # Read Resource handler
        @self.server.read_resource()
        async def handle_read_resource(uri):
            logger.info(f"Getting resource: {uri}")

            if uri not in instance.resources:
                return {"error": f"Unknown resource: {uri}"}

            try:
                if uri == "freecad://info":
                    if instance.freecad_connection and instance.freecad_connection.is_connected():
                        version_info = instance.freecad_connection.get_version()
                        version_str = ".".join(
                            str(v) for v in version_info.get("version", ["Unknown"])
                        )
                        connection_type = instance.freecad_connection.get_connection_type()

                        return {
                            "content": f"FreeCAD version: {version_str}\nConnection type: {connection_type}",
                            "mimeType": "text/markdown",
                        }
                    else:
                        return {
                            "content": "Error: Not currently connected to FreeCAD.",
                            "mimeType": "text/plain",
                        }

                return {"error": f"Resource not implemented: {uri}"}
            except Exception as e:
                logger.error(f"Error getting resource {uri}: {e}")
                return {"error": f"Error getting resource: {str(e)}"}

    async def _execute_smithery_tool(self, tool_name, arguments):
        """Execute a smithery tool."""
        if not self.freecad_connection or not self.freecad_connection.is_connected():
            return {
                "error": "Not connected to FreeCAD",
                "message": "Not connected to FreeCAD",
            }

        # Create smithery provider
        try:
            # In a real implementation, we would use the proper MCP tool provider
            # For now, we'll directly use the FreeCAD connection

            if tool_name == "smithery.create_anvil":
                # Extract parameters
                length = float(arguments.get("length", 400.0))
                width = float(arguments.get("width", 120.0))
                height = float(arguments.get("height", 200.0))
                horn_length = float(arguments.get("horn_length", 150.0))

                # Create anvil using script execution
                script = f"""
import FreeCAD
import Part

# Variables for customization
body_length = {length}
body_width = {width}
body_height = {height * 0.7}
top_length = {length * 0.9}
top_width = {width}
top_height = {height * 0.3}
horn_length = {horn_length}
horn_radius1 = {width / 3}
horn_radius2 = {width / 6}

# Create document
doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("Smithery")

# Create main body
body = doc.addObject("Part::Box", "AnvilBody")
body.Length = body_length
body.Width = body_width
body.Height = body_height

# Create top
top = doc.addObject("Part::Box", "AnvilTop")
top.Length = top_length
top.Width = top_width
top.Height = top_height
top.Placement.Base = FreeCAD.Vector((body_length - top_length) / 2, 0, body_height)

# Create horn
horn = doc.addObject("Part::Cone", "AnvilHorn")
horn.Radius1 = horn_radius1
horn.Radius2 = horn_radius2
horn.Height = horn_length
horn.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90)
horn.Placement.Base = FreeCAD.Vector(body_length, body_width / 2, body_height + top_height / 2)

# Create fusion
fused_anvil = doc.addObject("Part::MultiFuse", "Anvil")
fused_anvil.Shapes = [body, top, horn]

# Recompute
doc.recompute()

# Return object ID
anvil_id = fused_anvil.Name
"""

                # Handle both synchronous and asynchronous versions of execute_command
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Get the name of the created object from the environment
                anvil_id = result.get("environment", {}).get("anvil_id", "Anvil")

                return {
                    "anvil_id": anvil_id,
                    "message": f"Created anvil with dimensions: {length}x{width}x{height}mm",
                    "success": True,
                }

            elif tool_name == "smithery.create_hammer":
                # Extract parameters
                handle_length = float(arguments.get("handle_length", 300.0))
                handle_diameter = float(arguments.get("handle_diameter", 25.0))
                head_length = float(arguments.get("head_length", 100.0))
                head_width = float(arguments.get("head_width", 40.0))
                head_height = float(arguments.get("head_height", 30.0))

                # Create hammer using script execution
                script = f"""
import FreeCAD
import Part

# Create document
doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("Smithery")

# Create handle
handle = doc.addObject("Part::Cylinder", "HammerHandle")
handle.Radius = {handle_diameter / 2}
handle.Height = {handle_length}
handle.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90)

# Create head
head = doc.addObject("Part::Box", "HammerHead")
head.Length = {head_length}
head.Width = {head_width}
head.Height = {head_height}
head.Placement.Base = FreeCAD.Vector(
    handle.Height - head.Length/2,
    -head.Width/2 + handle.Radius,
    -head.Height/2 + handle.Radius
)

# Create fusion
fusion = doc.addObject("Part::MultiFuse", "Hammer")
fusion.Shapes = [handle, head]

# Recompute
doc.recompute()

# Return object ID
hammer_id = fusion.Name
"""
                # Handle both synchronous and asynchronous versions of execute_command
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Get the name of the created object from the environment
                hammer_id = result.get("environment", {}).get("hammer_id", "Hammer")

                return {
                    "hammer_id": hammer_id,
                    "message": f"Created hammer with handle length {handle_length}mm and head dimensions {head_length}x{head_width}x{head_height}mm",
                    "success": True,
                }

            # Similarly implement other smithery tools

            else:
                return {
                    "error": f"Tool not yet implemented: {tool_name}",
                    "message": f"Tool not yet implemented: {tool_name}",
                }

        except Exception as e:
            logger.error(f"Error executing smithery tool {tool_name}: {e}")
            return {
                "error": f"Error executing tool: {str(e)}",
                "message": f"Error executing tool: {str(e)}",
            }

    async def _execute_freecad_tool(self, tool_name, arguments):
        """Execute a basic FreeCAD tool."""
        if not self.freecad_connection or not self.freecad_connection.is_connected():
            return {
                "error": "Not connected to FreeCAD",
                "message": "Not connected to FreeCAD",
            }

        try:
            if tool_name == "freecad.create_document":
                name = arguments.get("name", "Unnamed")
                result = self.freecad_connection.create_document(name)
                return {
                    "document_name": result,
                    "message": f"Created document: {result}",
                    "success": bool(result),
                }

            elif tool_name == "freecad.export_stl":
                file_path = arguments.get("file_path")
                object_name = arguments.get("object_name")
                document = arguments.get(
                    "document", arguments.get("document_name")
                )  # Allow both keys

                if not file_path:
                    return {
                        "error": "File path is required",
                        "message": "File path is required",
                    }

                success = self.freecad_connection.export_stl(
                    object_name=object_name, file_path=file_path, document=document
                )

                return {
                    "file_path": file_path,
                    "message": f"Exported {'model' if not object_name else object_name} to {file_path}",
                    "success": success,
                }

            # 3D Primitive Creation Tools
            elif tool_name == "freecad.create_box":
                # Extract parameters
                length = float(arguments.get("length", 100.0))
                width = float(arguments.get("width", 100.0))
                height = float(arguments.get("height", 100.0))
                name = arguments.get("name", "Box")
                pos_x = float(arguments.get("position_x", 0.0))
                pos_y = float(arguments.get("position_y", 0.0))
                pos_z = float(arguments.get("position_z", 0.0))

                # Create the script
                script = f"""
import FreeCAD
import Part

# Create or get the active document
doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("Unnamed")

# Create a box
box = doc.addObject("Part::Box", "{name}")
box.Length = {length}
box.Width = {width}
box.Height = {height}
box.Placement.Base = FreeCAD.Vector({pos_x}, {pos_y}, {pos_z})

# Recompute
doc.recompute()

# Return the name
box_name = box.Name
"""
                # Execute the script
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Get the name of the created object
                box_name = result.get("environment", {}).get("box_name", name)

                return {
                    "object_name": box_name,
                    "message": f"Created box with dimensions {length}x{width}x{height}mm",
                    "success": True
                }

            elif tool_name == "freecad.create_cylinder":
                # Extract parameters
                radius = float(arguments.get("radius", 50.0))
                height = float(arguments.get("height", 100.0))
                name = arguments.get("name", "Cylinder")
                pos_x = float(arguments.get("position_x", 0.0))
                pos_y = float(arguments.get("position_y", 0.0))
                pos_z = float(arguments.get("position_z", 0.0))

                # Create the script
                script = f"""
import FreeCAD
import Part

# Create or get the active document
doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("Unnamed")

# Create a cylinder
cylinder = doc.addObject("Part::Cylinder", "{name}")
cylinder.Radius = {radius}
cylinder.Height = {height}
cylinder.Placement.Base = FreeCAD.Vector({pos_x}, {pos_y}, {pos_z})

# Recompute
doc.recompute()

# Return the name
cylinder_name = cylinder.Name
"""
                # Execute the script
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Get the name of the created object
                cylinder_name = result.get("environment", {}).get("cylinder_name", name)

                return {
                    "object_name": cylinder_name,
                    "message": f"Created cylinder with radius {radius}mm and height {height}mm",
                    "success": True
                }

            elif tool_name == "freecad.create_sphere":
                # Extract parameters
                radius = float(arguments.get("radius", 50.0))
                name = arguments.get("name", "Sphere")
                pos_x = float(arguments.get("position_x", 0.0))
                pos_y = float(arguments.get("position_y", 0.0))
                pos_z = float(arguments.get("position_z", 0.0))

                # Create the script
                script = f"""
import FreeCAD
import Part

# Create or get the active document
doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("Unnamed")

# Create a sphere
sphere = doc.addObject("Part::Sphere", "{name}")
sphere.Radius = {radius}
sphere.Placement.Base = FreeCAD.Vector({pos_x}, {pos_y}, {pos_z})

# Recompute
doc.recompute()

# Return the name
sphere_name = sphere.Name
"""
                # Execute the script
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Get the name of the created object
                sphere_name = result.get("environment", {}).get("sphere_name", name)

                return {
                    "object_name": sphere_name,
                    "message": f"Created sphere with radius {radius}mm",
                    "success": True
                }

            elif tool_name == "freecad.create_cone":
                # Extract parameters
                radius1 = float(arguments.get("radius1", 50.0))
                radius2 = float(arguments.get("radius2", 0.0))
                height = float(arguments.get("height", 100.0))
                name = arguments.get("name", "Cone")
                pos_x = float(arguments.get("position_x", 0.0))
                pos_y = float(arguments.get("position_y", 0.0))
                pos_z = float(arguments.get("position_z", 0.0))

                # Create the script
                script = f"""
import FreeCAD
import Part

# Create or get the active document
doc = FreeCAD.ActiveDocument
if not doc:
    doc = FreeCAD.newDocument("Unnamed")

# Create a cone
cone = doc.addObject("Part::Cone", "{name}")
cone.Radius1 = {radius1}
cone.Radius2 = {radius2}
cone.Height = {height}
cone.Placement.Base = FreeCAD.Vector({pos_x}, {pos_y}, {pos_z})

# Recompute
doc.recompute()

# Return the name
cone_name = cone.Name
"""
                # Execute the script
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Get the name of the created object
                cone_name = result.get("environment", {}).get("cone_name", name)

                return {
                    "object_name": cone_name,
                    "message": f"Created cone with base radius {radius1}mm, top radius {radius2}mm, and height {height}mm",
                    "success": True
                }

            # Boolean operations
            elif tool_name == "freecad.boolean_union":
                # Extract parameters
                object1 = arguments.get("object1")
                object2 = arguments.get("object2")
                name = arguments.get("name", "Union")

                if not object1 or not object2:
                    return {
                        "error": "Both object names are required",
                        "message": "Both object names are required for boolean union operation",
                    }

                # Create the script
                script = f"""
import FreeCAD
import Part

# Get the active document
doc = FreeCAD.ActiveDocument
if not doc:
    raise Exception("No active document")

# Get the objects
obj1 = doc.getObject("{object1}")
obj2 = doc.getObject("{object2}")

if not obj1:
    raise Exception("Object '{object1}' not found")
if not obj2:
    raise Exception("Object '{object2}' not found")

# Create a union
union = doc.addObject("Part::Fuse", "{name}")
union.Base = obj1
union.Tool = obj2

# Recompute
doc.recompute()

# Return the name
union_name = union.Name
"""
                # Execute the script
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Get the name of the created object
                union_name = result.get("environment", {}).get("union_name", name)

                return {
                    "object_name": union_name,
                    "message": f"Created union of {object1} and {object2}",
                    "success": True
                }

            elif tool_name == "freecad.boolean_cut":
                # Extract parameters
                object1 = arguments.get("object1")
                object2 = arguments.get("object2")
                name = arguments.get("name", "Cut")

                if not object1 or not object2:
                    return {
                        "error": "Both object names are required",
                        "message": "Both object names are required for boolean cut operation",
                    }

                # Create the script
                script = f"""
import FreeCAD
import Part

# Get the active document
doc = FreeCAD.ActiveDocument
if not doc:
    raise Exception("No active document")

# Get the objects
obj1 = doc.getObject("{object1}")
obj2 = doc.getObject("{object2}")

if not obj1:
    raise Exception("Object '{object1}' not found")
if not obj2:
    raise Exception("Object '{object2}' not found")

# Create a cut
cut = doc.addObject("Part::Cut", "{name}")
cut.Base = obj1
cut.Tool = obj2

# Recompute
doc.recompute()

# Return the name
cut_name = cut.Name
"""
                # Execute the script
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Get the name of the created object
                cut_name = result.get("environment", {}).get("cut_name", name)

                return {
                    "object_name": cut_name,
                    "message": f"Created cut of {object1} by {object2}",
                    "success": True
                }

            elif tool_name == "freecad.boolean_intersection":
                # Extract parameters
                object1 = arguments.get("object1")
                object2 = arguments.get("object2")
                name = arguments.get("name", "Intersection")

                if not object1 or not object2:
                    return {
                        "error": "Both object names are required",
                        "message": "Both object names are required for boolean intersection operation",
                    }

                # Create the script
                script = f"""
import FreeCAD
import Part

# Get the active document
doc = FreeCAD.ActiveDocument
if not doc:
    raise Exception("No active document")

# Get the objects
obj1 = doc.getObject("{object1}")
obj2 = doc.getObject("{object2}")

if not obj1:
    raise Exception("Object '{object1}' not found")
if not obj2:
    raise Exception("Object '{object2}' not found")

# Create an intersection
intersection = doc.addObject("Part::Common", "{name}")
intersection.Base = obj1
intersection.Tool = obj2

# Recompute
doc.recompute()

# Return the name
intersection_name = intersection.Name
"""
                # Execute the script
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Get the name of the created object
                intersection_name = result.get("environment", {}).get("intersection_name", name)

                return {
                    "object_name": intersection_name,
                    "message": f"Created intersection of {object1} and {object2}",
                    "success": True
                }

            # Transformation tools
            elif tool_name == "freecad.move_object":
                # Extract parameters
                object_name = arguments.get("object_name")
                pos_x = float(arguments.get("x", 0.0))
                pos_y = float(arguments.get("y", 0.0))
                pos_z = float(arguments.get("z", 0.0))

                if not object_name:
                    return {
                        "error": "Object name is required",
                        "message": "Object name is required for move operation",
                    }

                # Create the script for absolute positioning
                script = f"""
import FreeCAD

# Get the active document
doc = FreeCAD.ActiveDocument
if not doc:
    raise Exception("No active document")

# Get the object
obj = doc.getObject("{object_name}")
if not obj:
    raise Exception("Object '{object_name}' not found")

# Move the object to an absolute position
obj.Placement.Base = FreeCAD.Vector({pos_x}, {pos_y}, {pos_z})

# Recompute
doc.recompute()

# Return the new position
new_pos_x = obj.Placement.Base.x
new_pos_y = obj.Placement.Base.y
new_pos_z = obj.Placement.Base.z
"""
                # Execute the script
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Get the new position from the environment
                new_pos_x = result.get("environment", {}).get("new_pos_x", pos_x)
                new_pos_y = result.get("environment", {}).get("new_pos_y", pos_y)
                new_pos_z = result.get("environment", {}).get("new_pos_z", pos_z)

                return {
                    "object_name": object_name,
                    "position": {
                        "x": new_pos_x,
                        "y": new_pos_y,
                        "z": new_pos_z
                    },
                    "message": f"Moved object {object_name} to position ({new_pos_x}, {new_pos_y}, {new_pos_z})",
                    "success": True
                }

            elif tool_name == "freecad.rotate_object":
                # Extract parameters
                object_name = arguments.get("object_name")
                rot_x = float(arguments.get("angle_x", 0.0))
                rot_y = float(arguments.get("angle_y", 0.0))
                rot_z = float(arguments.get("angle_z", 0.0))

                if not object_name:
                    return {
                        "error": "Object name is required",
                        "message": "Object name is required for rotation operation",
                    }

                # Create the script
                script = f"""
import FreeCAD
import math

# Get the active document
doc = FreeCAD.ActiveDocument
if not doc:
    raise Exception("No active document")

# Get the object
obj = doc.getObject("{object_name}")
if not obj:
    raise Exception("Object '{object_name}' not found")

# Convert degrees to radians
rot_x_rad = math.radians({rot_x})
rot_y_rad = math.radians({rot_y})
rot_z_rad = math.radians({rot_z})

# Create rotation
rotation = FreeCAD.Rotation(rot_x_rad, rot_y_rad, rot_z_rad)

# Create placement with rotation around specified center
center = FreeCAD.Vector(0, 0, 0)  # Assuming the center is the origin
displacement = obj.Placement.Base.sub(center)
displacement = rotation.multVec(displacement)
new_pos = center.add(displacement)

obj.Placement = FreeCAD.Placement(new_pos, rotation)

# Recompute
doc.recompute()

# Return rotation values in degrees
rotation_x = {rot_x}
rotation_y = {rot_y}
rotation_z = {rot_z}
"""
                # Execute the script
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                return {
                    "object_name": object_name,
                    "rotation": {
                        "x": rot_x,
                        "y": rot_y,
                        "z": rot_z
                    },
                    "message": f"Rotated object {object_name} by ({rot_x}, {rot_y}, {rot_z}) degrees",
                    "success": True
                }

            # Document management
            elif tool_name == "freecad.list_objects":
                document = arguments.get("document")

                script = f"""
import FreeCAD

# Get the document
doc = None
if "{document}":
    doc = FreeCAD.getDocument("{document}")
else:
    doc = FreeCAD.ActiveDocument

if not doc:
    raise Exception("No active document")

# Get the list of objects
object_names = [obj.Name for obj in doc.Objects]
object_types = [obj.TypeId for obj in doc.Objects]
object_labels = [obj.Label for obj in doc.Objects]

# Create a list of objects with their properties
objects_list = []
for i, name in enumerate(object_names):
    objects_list.append({{"name": name, "type": object_types[i], "label": object_labels[i]}})
"""
                # Execute the script
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Convert the string representation of objects_list to an actual list
                objects_list = eval(result.get("environment", {}).get("objects_list", "[]"))

                return {
                    "objects": objects_list,
                    "count": len(objects_list),
                    "document": document or "Active Document",
                    "message": f"Found {len(objects_list)} objects in {'document ' + document if document else 'active document'}",
                    "success": True
                }

            elif tool_name == "freecad.list_documents":
                script = """
import FreeCAD

# Get the list of documents
document_names = FreeCAD.listDocuments().keys()
"""
                # Execute the script
                result = self.freecad_connection.execute_command(
                    "execute_script", {"script": script}
                )
                if asyncio.iscoroutine(result):
                    result = await result

                if "error" in result:
                    return {"error": result["error"], "message": result["error"]}

                # Get document names from the environment
                document_names = eval(result.get("environment", {}).get("document_names", "[]"))

                return {
                    "documents": list(document_names),
                    "count": len(document_names),
                    "message": f"Found {len(document_names)} open documents",
                    "success": True
                }

            return {
                "error": f"Tool not implemented: {tool_name}",
                "message": f"Tool not implemented: {tool_name}",
            }

        except Exception as e:
            logger.error(f"Error executing FreeCAD tool {tool_name}: {e}")
            return {
                "error": f"Error executing tool: {str(e)}",
                "message": f"Error executing tool: {str(e)}",
            }

    def close(self):
        """Close the server and clean up resources."""
        if self.freecad_connection:
            self.freecad_connection.close()
            logger.info("Closed FreeCAD connection")

    # Legacy methods for tests

    async def _handle_list_tools(self, request, extra):
        """Handle a request to list available tools (legacy method for tests)."""
        return {
            "tools": [
                {
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "inputSchema": tool_info["schema"],
                }
                for tool_id, tool_info in self.tools.items()
            ]
        }

    async def _handle_list_resources(self, request, extra):
        """Handle a request to list available resources (legacy method for tests)."""
        return {
            "resources": [
                {"uri": resource_info["uri"], "name": resource_info["name"]}
                for resource_id, resource_info in self.resources.items()
            ]
        }

    async def _handle_execute_tool(self, request, extra):
        """Handle a request to execute a tool (legacy method for tests)."""
        tool_name = request.get("name")
        arguments = request.get("arguments", {})

        logger.info(f"Executing tool: {tool_name} with arguments: {arguments}")

        if not tool_name or tool_name not in self.tools:
            return {
                "error": f"Unknown tool: {tool_name}",
                "message": f"Unknown tool: {tool_name}",
            }

        try:
            # Handle smithery tools
            if tool_name.startswith("smithery."):
                return await self._execute_smithery_tool(tool_name, arguments)

            # Handle basic FreeCAD tools
            elif tool_name.startswith("freecad."):
                return await self._execute_freecad_tool(tool_name, arguments)

            return {
                "error": f"Tool not implemented: {tool_name}",
                "message": f"Tool not implemented: {tool_name}",
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "error": f"Error executing tool: {str(e)}",
                "message": f"Error executing tool: {str(e)}",
            }

    async def _handle_get_resource(self, request, extra):
        """Handle a request to get a resource (legacy method for tests)."""
        uri = request.get("uri")
        logger.info(f"Getting resource: {uri}")

        if not uri or uri not in self.resources:
            return {
                "error": f"Unknown resource: {uri}",
                "message": f"Unknown resource: {uri}",
            }

        try:
            if uri == "freecad://info":
                if self.freecad_connection and self.freecad_connection.is_connected():
                    version_info = self.freecad_connection.get_version()
                    version_str = ".".join(
                        str(v) for v in version_info.get("version", ["Unknown"])
                    )
                    connection_type = self.freecad_connection.get_connection_type()

                    return {
                        "content": f"FreeCAD Version: {version_str}\nConnection Type: {connection_type}",
                        "mimeType": "text/markdown",
                    }
                else:
                    return {
                        "content": "Error: Not currently connected to FreeCAD.",
                        "mimeType": "text/plain",
                    }

            return {
                "error": f"Resource not implemented: {uri}",
                "message": f"Resource not implemented: {uri}",
            }
        except Exception as e:
            logger.error(f"Error getting resource {uri}: {e}")
            return {
                "error": f"Error getting resource: {str(e)}",
                "message": f"Error getting resource: {str(e)}",
            }

    async def _get_freecad_tools(self):
        """Get the list of FreeCAD tools."""
        tools = []

        # Basic document tools
        tools.append({
            "name": "freecad.create_document",
            "description": "Create a new FreeCAD document",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the document"
                    }
                },
                "required": ["name"]
            }
        })

        tools.append({
            "name": "freecad.list_documents",
            "description": "List all open documents",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        })

        tools.append({
            "name": "freecad.list_objects",
            "description": "List all objects in the active document",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        })

        # Primitive creation tools
        tools.append({
            "name": "freecad.create_box",
            "description": "Create a box primitive",
            "parameters": {
                "type": "object",
                "properties": {
                    "length": {
                        "type": "number",
                        "description": "Length of the box"
                    },
                    "width": {
                        "type": "number",
                        "description": "Width of the box"
                    },
                    "height": {
                        "type": "number",
                        "description": "Height of the box"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the box object"
                    },
                    "position_x": {
                        "type": "number",
                        "description": "X position of the box"
                    },
                    "position_y": {
                        "type": "number",
                        "description": "Y position of the box"
                    },
                    "position_z": {
                        "type": "number",
                        "description": "Z position of the box"
                    }
                },
                "required": ["length", "width", "height"]
            }
        })

        # Add more tools as needed
        return tools

    async def _get_smithery_tools(self):
        """Get the list of smithery tools."""
        tools = []

        # Smithery tools
        tools.append({
            "name": "smithery.create_anvil",
            "description": "Create an anvil model",
            "parameters": {
                "type": "object",
                "properties": {
                    "length": {
                        "type": "number",
                        "description": "Length of the anvil"
                    },
                    "width": {
                        "type": "number",
                        "description": "Width of the anvil"
                    },
                    "height": {
                        "type": "number",
                        "description": "Height of the anvil"
                    },
                    "name": {
                        "type": "string",
                        "description": "Name of the anvil object"
                    }
                },
                "required": []
            }
        })

        # Add more smithery tools as needed
        return tools


# Add the function to get FreeCAD version
def get_freecad_version():
    """Get the version of FreeCAD installed on the system"""
    try:
        import FreeCAD
        return FreeCAD.Version()
    except ImportError:
        return "FreeCAD not found or not installed"
    except Exception as e:
        return f"Error detecting FreeCAD version: {str(e)}"

def main():
    """
    Main entry point for the MCP-FreeCAD server
    """
    parser = argparse.ArgumentParser(description="FreeCAD MCP Server")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--host", help="Server hostname")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--version", action="store_true", help="Show version information")
    args = parser.parse_args()

    # Show version and exit if requested
    if args.version:
        print(f"MCP-FreeCAD Server v{VERSION}")
        print(f"FreeCAD Version: {get_freecad_version()}")
        return

    # Check if MCP is properly installed
    if mcp_import_error:
        print(f"ERROR: MCP SDK (mcp package) not found or import failed: {mcp_import_error}")
        print("Please install it with: pip install mcp trio")
        sys.exit(1)

    # Set debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Create and start the server
    config_path = args.config if args.config else "config.json"
    server = FreeCADMCPServer(config_path=config_path)

    # Override config with command line arguments if provided
    if args.host:
        server.config["freecad"]["host"] = args.host
    if args.port:
        server.config["freecad"]["port"] = args.port

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running server: {e}")
        sys.exit(1)
    finally:
        server.close()


if __name__ == "__main__":
    main()
