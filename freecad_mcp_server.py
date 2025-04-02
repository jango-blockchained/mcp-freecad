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

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("freecad_mcp")

# Import MCP SDK (using `mcp` package)
try:
    from mcp.server import Server

    MCP_SDK_AVAILABLE = True
except ImportError:
    logger.error(
        "MCP SDK (mcp package) not found or import failed. Please ensure `mcp` is installed correctly:"
    )
    logger.error("  pip install mcp")
    sys.exit(1)  # Exit if MCP SDK is essential and not found

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
    """FreeCAD MCP Server implementation."""

    def __init__(self, config_path: str = "config.json"):
        """Initialize the FreeCAD MCP Server."""
        self.config = self._load_config(config_path)
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
        """Initialize tool providers."""
        # Define available tools with their providers and descriptions
        self.tools = {
            # Smithery tools
            "smithery.create_anvil": {
                "name": "smithery.create_anvil",
                "description": "Create an anvil model with customizable dimensions",
                "schema": {
                    "type": "object",
                    "properties": {
                        "length": {
                            "type": "number",
                            "description": "Length of the anvil in mm",
                            "default": 400.0,
                        },
                        "width": {
                            "type": "number",
                            "description": "Width of the anvil in mm",
                            "default": 120.0,
                        },
                        "height": {
                            "type": "number",
                            "description": "Height of the anvil in mm",
                            "default": 200.0,
                        },
                        "horn_length": {
                            "type": "number",
                            "description": "Length of the anvil horn in mm",
                            "default": 150.0,
                        },
                    },
                },
            },
            "smithery.create_hammer": {
                "name": "smithery.create_hammer",
                "description": "Create a blacksmith hammer model",
                "schema": {
                    "type": "object",
                    "properties": {
                        "handle_length": {
                            "type": "number",
                            "description": "Length of the hammer handle in mm",
                            "default": 300.0,
                        },
                        "handle_diameter": {
                            "type": "number",
                            "description": "Diameter of the hammer handle in mm",
                            "default": 25.0,
                        },
                        "head_length": {
                            "type": "number",
                            "description": "Length of the hammer head in mm",
                            "default": 100.0,
                        },
                        "head_width": {
                            "type": "number",
                            "description": "Width of the hammer head in mm",
                            "default": 40.0,
                        },
                        "head_height": {
                            "type": "number",
                            "description": "Height of the hammer head in mm",
                            "default": 30.0,
                        },
                    },
                },
            },
            "smithery.create_tongs": {
                "name": "smithery.create_tongs",
                "description": "Create blacksmith tongs model",
                "schema": {
                    "type": "object",
                    "properties": {
                        "handle_length": {
                            "type": "number",
                            "description": "Length of the tongs handles in mm",
                            "default": 300.0,
                        },
                        "jaw_length": {
                            "type": "number",
                            "description": "Length of the tongs jaws in mm",
                            "default": 80.0,
                        },
                        "thickness": {
                            "type": "number",
                            "description": "Thickness of the tongs in mm",
                            "default": 10.0,
                        },
                        "width": {
                            "type": "number",
                            "description": "Width of the tongs in mm",
                            "default": 20.0,
                        },
                        "opening_angle": {
                            "type": "number",
                            "description": "Opening angle of the jaws in degrees",
                            "default": 15.0,
                        },
                    },
                },
            },
            "smithery.forge_blade": {
                "name": "smithery.forge_blade",
                "description": "Create a forged blade model",
                "schema": {
                    "type": "object",
                    "properties": {
                        "blade_length": {
                            "type": "number",
                            "description": "Length of the blade in mm",
                            "default": 250.0,
                        },
                        "blade_width": {
                            "type": "number",
                            "description": "Width of the blade in mm",
                            "default": 40.0,
                        },
                        "thickness": {
                            "type": "number",
                            "description": "Thickness of the blade in mm",
                            "default": 4.0,
                        },
                        "tang_length": {
                            "type": "number",
                            "description": "Length of the tang in mm",
                            "default": 100.0,
                        },
                        "tang_width": {
                            "type": "number",
                            "description": "Width of the tang in mm",
                            "default": 15.0,
                        },
                        "curvature": {
                            "type": "number",
                            "description": "Curvature of the blade in mm",
                            "default": 10.0,
                        },
                    },
                },
            },
            "smithery.create_horseshoe": {
                "name": "smithery.create_horseshoe",
                "description": "Create a horseshoe model",
                "schema": {
                    "type": "object",
                    "properties": {
                        "outer_radius": {
                            "type": "number",
                            "description": "Outer radius of the horseshoe in mm",
                            "default": 60.0,
                        },
                        "inner_radius": {
                            "type": "number",
                            "description": "Inner radius of the horseshoe in mm",
                            "default": 40.0,
                        },
                        "thickness": {
                            "type": "number",
                            "description": "Thickness of the horseshoe in mm",
                            "default": 10.0,
                        },
                        "opening_angle": {
                            "type": "number",
                            "description": "Opening angle of the horseshoe in degrees",
                            "default": 60.0,
                        },
                    },
                },
            },
            # Basic FreeCAD tools
            "freecad.create_document": {
                "name": "freecad.create_document",
                "description": "Create a new FreeCAD document",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the document",
                            "default": "Unnamed",
                        }
                    },
                },
            },
            "freecad.export_stl": {
                "name": "freecad.export_stl",
                "description": "Export the model to an STL file",
                "schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to save the STL file",
                            "default": "output.stl",
                        },
                        "object_name": {
                            "type": "string",
                            "description": "Name of the object to export (optional)",
                        },
                        "document": {
                            "type": "string",
                            "description": "Name of the document (optional)",
                        },
                    },
                    "required": ["file_path"],
                },
            },
        }

        # Initialize resources
        self.resources = {
            "freecad://info": {
                "uri": "freecad://info",
                "name": "FreeCAD Information",
                "description": "Information about the FreeCAD instance",
            }
        }

    async def start(self):
        """Start the MCP server."""
        if not MCP_SDK_AVAILABLE:
            logger.error("MCP SDK not available. Cannot start server.")
            return

        server_config = self.config.get("server", {})

        # Create the server with modern API
        self.server = Server(
            {
                "name": server_config.get("name", "freecad-mcp-server"),
                "version": server_config.get("version", "0.1.0"),
                "description": "FreeCAD MCP Server for Cursor integration",
            },
            {"capabilities": {"resources": {}, "tools": {}}},
        )

        # Register handlers
        self._setup_handlers()

        try:
            # Start the server using stdio transport
            # Based on MCP documentation, we need to use server.run() with the stdio transport
            from mcp.server.stdio import stdio_server

            logger.info("Starting FreeCAD MCP Server...")

            # Use the async context manager pattern from the documentation
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(read_stream, write_stream)

            logger.info("Server has completed")
        except Exception as e:
            logger.error(f"Error starting server: {e}")

    def _setup_handlers(self):
        """Set up request handlers for the server."""
        if not self.server:
            return

        # Based on docs and examples of MCP, modify the Server class directly
        # Using the request handler approach as described in the MCP architecture docs

        # Save reference to the self instance for use inside closures
        instance = self

        # List Tools
        self.server.list_tools = lambda: {
            "tools": [
                {
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "inputSchema": tool_info["schema"],
                }
                for tool_id, tool_info in instance.tools.items()
            ]
        }

        # Call Tool
        async def call_tool_impl(name, arguments):
            """Handle call_tool request."""
            logger.info(f"Executing tool: {name} with arguments: {arguments}")

            if name not in instance.tools:
                return {"error": f"Unknown tool: {name}"}

            try:
                # Handle smithery tools
                if name.startswith("smithery."):
                    return await instance._execute_smithery_tool(name, arguments)

                # Handle basic FreeCAD tools
                elif name.startswith("freecad."):
                    return await instance._execute_freecad_tool(name, arguments)

                return {"error": f"Tool not implemented: {name}"}
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return {"error": f"Error executing tool: {str(e)}"}

        self.server.call_tool = call_tool_impl

        # List Resources
        self.server.list_resources = lambda: {
            "resources": [
                {"uri": resource_info["uri"], "name": resource_info["name"]}
                for resource_id, resource_info in instance.resources.items()
            ]
        }

        # Read Resource
        async def read_resource_impl(uri):
            """Handle read_resource request."""
            logger.info(f"Getting resource: {uri}")

            if uri not in instance.resources:
                return {"error": f"Unknown resource: {uri}"}

            try:
                if uri == "freecad://info":
                    if (
                        instance.freecad_connection
                        and instance.freecad_connection.is_connected()
                    ):
                        version_info = instance.freecad_connection.get_version()
                        version_str = ".".join(
                            str(v) for v in version_info.get("version", ["Unknown"])
                        )
                        connection_type = (
                            instance.freecad_connection.get_connection_type()
                        )

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

        self.server.read_resource = read_resource_impl

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


async def main():
    """Main function to run the FreeCAD MCP Server."""
    parser = argparse.ArgumentParser(description="FreeCAD MCP Server")
    parser.add_argument(
        "--config", default="config.json", help="Path to configuration file"
    )
    args = parser.parse_args()

    # Create and start the server
    server = FreeCADMCPServer(args.config)
    try:
        await server.start()
    finally:
        server.close()
        logger.info("FreeCAD MCP Server main function finished.")


if __name__ == "__main__":
    asyncio.run(main())
