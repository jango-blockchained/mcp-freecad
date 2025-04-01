#!/usr/bin/env python3
"""
FreeCAD MCP Server

This script implements a Model Context Protocol (MCP) server for FreeCAD.
It provides tools and resources for AI assistants to interact with FreeCAD.

Usage:
    python freecad_mcp_server.py
"""

import os
import sys
import json
import logging
import argparse
import asyncio
from typing import Dict, List, Any, Optional, TypeVar, Generic

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("freecad_mcp")

# Import MCP SDK
try:
    from mcp_sdk.server import Server, StdioServerTransport
    from mcp_sdk.server.requests import ListResourcesRequestSchema, GetResourceRequestSchema
    from mcp_sdk.server.requests import ListToolsRequestSchema, ExecuteToolRequestSchema
    from mcp_sdk.server.responses import ErrorResponse
    MCP_SDK_AVAILABLE = True
except ImportError:
    logger.error("MCP SDK not found. Please install it manually:")
    logger.error("  pip install modelcontextprotocol")
    sys.exit(1) # Exit if MCP SDK is essential and not found

# Import FreeCAD connection
try:
    from freecad_connection import FreeCADConnection
    FREECAD_CONNECTION_AVAILABLE = True
except ImportError:
    logger.warning("FreeCAD connection not found in the current directory")
    FREECAD_CONNECTION_AVAILABLE = False

# Import tool providers from our implementation
try:
    from src.mcp_freecad.tools.primitives import PrimitiveToolProvider
    from src.mcp_freecad.tools.model_manipulation import ModelManipulationToolProvider
    from src.mcp_freecad.tools.smithery import SmitheryToolProvider
    MCP_TOOLS_AVAILABLE = True
except ImportError:
    logger.warning("MCP tool providers not found. Using local implementations if available.")
    MCP_TOOLS_AVAILABLE = False
    try:
        # Try to import the local smithery implementation
        from freecad_bridge import FreeCADBridge
        MCP_TOOLS_AVAILABLE = False
    except ImportError:
        logger.warning("Local FreeCAD bridge not found. Some functionality may be limited.")

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
                "server": {
                    "name": "freecad-mcp-server",
                    "version": "0.1.0"
                },
                "freecad": {
                    "connection_method": "auto",  # auto, server, bridge, or mock
                    "host": "localhost",
                    "port": 12345,
                    "freecad_path": "freecad"
                }
            }
    
    def _initialize_freecad_connection(self):
        """Initialize connection to FreeCAD."""
        if not FREECAD_CONNECTION_AVAILABLE:
            logger.warning("FreeCAD connection not available. Some features may not work.")
            return
        
        freecad_config = self.config.get("freecad", {})
        
        try:
            self.freecad_connection = FreeCADConnection(
                host=freecad_config.get("host", "localhost"),
                port=freecad_config.get("port", 12345),
                freecad_path=freecad_config.get("freecad_path", "freecad"),
                auto_connect=True,
                prefer_method=freecad_config.get("connection_method")
            )
            
            if self.freecad_connection.is_connected():
                connection_type = self.freecad_connection.get_connection_type()
                logger.info(f"Connected to FreeCAD using {connection_type} method")
                
                # Get FreeCAD version
                version_info = self.freecad_connection.get_version()
                version_str = '.'.join(str(v) for v in version_info.get('version', ['Unknown']))
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
                            "default": 400.0
                        },
                        "width": {
                            "type": "number",
                            "description": "Width of the anvil in mm",
                            "default": 120.0
                        },
                        "height": {
                            "type": "number",
                            "description": "Height of the anvil in mm",
                            "default": 200.0
                        },
                        "horn_length": {
                            "type": "number",
                            "description": "Length of the anvil horn in mm",
                            "default": 150.0
                        }
                    }
                }
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
                            "default": 300.0
                        },
                        "handle_diameter": {
                            "type": "number",
                            "description": "Diameter of the hammer handle in mm",
                            "default": 25.0
                        },
                        "head_length": {
                            "type": "number",
                            "description": "Length of the hammer head in mm",
                            "default": 100.0
                        },
                        "head_width": {
                            "type": "number",
                            "description": "Width of the hammer head in mm",
                            "default": 40.0
                        },
                        "head_height": {
                            "type": "number",
                            "description": "Height of the hammer head in mm",
                            "default": 30.0
                        }
                    }
                }
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
                            "default": 300.0
                        },
                        "jaw_length": {
                            "type": "number",
                            "description": "Length of the tongs jaws in mm",
                            "default": 80.0
                        },
                        "thickness": {
                            "type": "number",
                            "description": "Thickness of the tongs in mm",
                            "default": 10.0
                        },
                        "width": {
                            "type": "number",
                            "description": "Width of the tongs in mm",
                            "default": 20.0
                        },
                        "opening_angle": {
                            "type": "number",
                            "description": "Opening angle of the jaws in degrees",
                            "default": 15.0
                        }
                    }
                }
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
                            "default": 250.0
                        },
                        "blade_width": {
                            "type": "number",
                            "description": "Width of the blade in mm",
                            "default": 40.0
                        },
                        "thickness": {
                            "type": "number",
                            "description": "Thickness of the blade in mm",
                            "default": 4.0
                        },
                        "tang_length": {
                            "type": "number",
                            "description": "Length of the tang in mm",
                            "default": 100.0
                        },
                        "tang_width": {
                            "type": "number",
                            "description": "Width of the tang in mm",
                            "default": 15.0
                        },
                        "curvature": {
                            "type": "number",
                            "description": "Curvature of the blade in mm",
                            "default": 10.0
                        }
                    }
                }
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
                            "default": 60.0
                        },
                        "inner_radius": {
                            "type": "number",
                            "description": "Inner radius of the horseshoe in mm",
                            "default": 40.0
                        },
                        "thickness": {
                            "type": "number",
                            "description": "Thickness of the horseshoe in mm",
                            "default": 10.0
                        },
                        "opening_angle": {
                            "type": "number",
                            "description": "Opening angle of the horseshoe in degrees",
                            "default": 60.0
                        }
                    }
                }
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
                            "default": "Unnamed"
                        }
                    }
                }
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
                            "default": "output.stl"
                        },
                        "object_name": {
                            "type": "string",
                            "description": "Name of the object to export (optional)"
                        },
                        "document": {
                            "type": "string",
                            "description": "Name of the document (optional)"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }
        
        # Initialize resources
        self.resources = {
            "freecad://info": {
                "uri": "freecad://info",
                "name": "FreeCAD Information",
                "description": "Information about the FreeCAD instance"
            }
        }
    
    async def start(self):
        """Start the MCP server."""
        if not MCP_SDK_AVAILABLE:
            logger.error("MCP SDK not available. Cannot start server.")
            return
            
        server_config = self.config.get("server", {})
        
        # Create MCP server with Cursor-compatible configuration
        self.server = Server(
            info={
                "name": server_config.get("name", "freecad-mcp-server"),
                "version": server_config.get("version", "0.1.0"),
                "description": "FreeCAD MCP Server for Cursor integration"
            },
            config={
                "capabilities": {
                    "resources": True,
                    "tools": True
                }
            }
        )
        
        # Set up request handlers
        self._setup_request_handlers()
        
        # Connect to transport using stdio for Cursor compatibility
        transport = StdioServerTransport()
        logger.info("Starting FreeCAD MCP Server for Cursor...")
        
        try:
            await self.server.connect(transport)
            logger.info("MCP Server connected to Cursor via stdio transport")
        except Exception as e:
            logger.error(f"Error connecting to transport: {e}")
            return ErrorResponse(message=f"Failed to start server: {str(e)}")
    
    def _setup_request_handlers(self):
        """Set up request handlers for the MCP server."""
        if not self.server:
            return
            
        # Handle ListToolsRequest
        self.server.setRequestHandler(ListToolsRequestSchema, self._handle_list_tools)
        
        # Handle ExecuteToolRequest
        self.server.setRequestHandler(ExecuteToolRequestSchema, self._handle_execute_tool)
        
        # Handle ListResourcesRequest
        self.server.setRequestHandler(ListResourcesRequestSchema, self._handle_list_resources)
        
        # Handle GetResourceRequest
        self.server.setRequestHandler(GetResourceRequestSchema, self._handle_get_resource)
    
    async def _handle_list_tools(self, request, extra):
        """Handle a request to list available tools."""
        return {
            "tools": [
                {
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "inputSchema": tool_info["schema"]
                }
                for tool_id, tool_info in self.tools.items()
            ]
        }
    
    async def _handle_execute_tool(self, request, extra):
        """Handle a request to execute a tool."""
        tool_name = request.get("name")
        arguments = request.get("arguments", {})
        
        logger.info(f"Executing tool: {tool_name} with arguments: {arguments}")
        
        if not tool_name or tool_name not in self.tools:
            return ErrorResponse(message=f"Unknown tool: {tool_name}")
        
        try:
            # Handle smithery tools
            if tool_name.startswith("smithery."):
                return await self._execute_smithery_tool(tool_name, arguments)
            
            # Handle basic FreeCAD tools
            elif tool_name.startswith("freecad."):
                return await self._execute_freecad_tool(tool_name, arguments)
            
            return ErrorResponse(message=f"Tool not implemented: {tool_name}")
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return ErrorResponse(message=f"Error executing tool: {str(e)}")
    
    async def _execute_smithery_tool(self, tool_name, arguments):
        """Execute a smithery tool."""
        if not self.freecad_connection or not self.freecad_connection.is_connected():
            return ErrorResponse(message="Not connected to FreeCAD")
        
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

# Create document
doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("Smithery")

# Create main body
body = doc.addObject("Part::Box", "AnvilBody")
body.Length = {length}
body.Width = {width}
body.Height = {height * 0.7}

# Create top
top = doc.addObject("Part::Box", "AnvilTop")
top.Length = {length * 0.9}
top.Width = {width}
top.Height = {height * 0.3}
top.Placement.Base = FreeCAD.Vector(({length} - top.Length) / 2, 0, body.Height)

# Create horn
horn = doc.addObject("Part::Cone", "AnvilHorn")
horn.Radius1 = {width / 3}
horn.Radius2 = {width / 6}
horn.Height = {horn_length}
horn.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90)
horn.Placement.Base = FreeCAD.Vector({length}, {width / 2}, body.Height + top.Height / 2)

# Create fusion
fusion = doc.addObject("Part::MultiFuse", "Anvil")
fusion.Shapes = [body, top, horn]

# Recompute
doc.recompute()

# Return object ID
anvil_id = fusion.Name
"""
                result = self.freecad_connection.execute_command("execute_script", {"script": script})
                if "error" in result:
                    return ErrorResponse(message=result["error"])
                
                # Get the name of the created object from the environment
                anvil_id = result.get("environment", {}).get("anvil_id", "Anvil")
                
                return {
                    "anvil_id": anvil_id,
                    "message": f"Created anvil with dimensions: {length}x{width}x{height}mm",
                    "success": True
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
                result = self.freecad_connection.execute_command("execute_script", {"script": script})
                if "error" in result:
                    return ErrorResponse(message=result["error"])
                
                # Get the name of the created object from the environment
                hammer_id = result.get("environment", {}).get("hammer_id", "Hammer")
                
                return {
                    "hammer_id": hammer_id,
                    "message": f"Created hammer with handle length {handle_length}mm and head dimensions {head_length}x{head_width}x{head_height}mm",
                    "success": True
                }
                
            # Similarly implement other smithery tools
            
            else:
                return ErrorResponse(message=f"Tool not yet implemented: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error executing smithery tool {tool_name}: {e}")
            return ErrorResponse(message=f"Error executing tool: {str(e)}")
    
    async def _execute_freecad_tool(self, tool_name, arguments):
        """Execute a basic FreeCAD tool."""
        if not self.freecad_connection or not self.freecad_connection.is_connected():
            return ErrorResponse(message="Not connected to FreeCAD")
        
        try:
            if tool_name == "freecad.create_document":
                name = arguments.get("name", "Unnamed")
                result = self.freecad_connection.create_document(name)
                return {
                    "document_name": result,
                    "message": f"Created document: {result}",
                    "success": bool(result)
                }
            
            elif tool_name == "freecad.export_stl":
                file_path = arguments.get("file_path")
                object_name = arguments.get("object_name")
                document = arguments.get("document")
                
                if not file_path:
                    return ErrorResponse(message="File path is required")
                
                success = self.freecad_connection.export_stl(object_name, file_path, document)
                
                return {
                    "file_path": file_path,
                    "message": f"Exported {'model' if not object_name else object_name} to {file_path}",
                    "success": success
                }
            
            return ErrorResponse(message=f"Tool not implemented: {tool_name}")
            
        except Exception as e:
            logger.error(f"Error executing FreeCAD tool {tool_name}: {e}")
            return ErrorResponse(message=f"Error executing tool: {str(e)}")
    
    async def _handle_list_resources(self, request, extra):
        """Handle a request to list available resources."""
        return {
            "resources": [
                {
                    "uri": resource_info["uri"],
                    "name": resource_info["name"]
                }
                for resource_id, resource_info in self.resources.items()
            ]
        }
    
    async def _handle_get_resource(self, request, extra):
        """Handle a request to get a resource."""
        uri = request.get("uri")
        logger.info(f"Getting resource: {uri}")
        
        if not uri or uri not in self.resources:
            return ErrorResponse(message=f"Unknown resource: {uri}")
        
        try:
            if uri == "freecad://info":
                if self.freecad_connection and self.freecad_connection.is_connected():
                    version_info = self.freecad_connection.get_version()
                    version_str = '.'.join(str(v) for v in version_info.get('version', ['Unknown']))
                    connection_type = self.freecad_connection.get_connection_type()
                    
                    return {
                        "content": f"FreeCAD version: {version_str}\nConnection type: {connection_type}"
                    }
                else:
                    return {
                        "content": "Not connected to FreeCAD"
                    }
            
            return ErrorResponse(message=f"Resource not implemented: {uri}")
        except Exception as e:
            logger.error(f"Error getting resource {uri}: {e}")
            return ErrorResponse(message=f"Error getting resource: {str(e)}")
    
    def close(self):
        """Close the server and clean up resources."""
        if self.freecad_connection:
            self.freecad_connection.close()
            logger.info("Closed FreeCAD connection")

async def main():
    """Main function to run the FreeCAD MCP Server."""
    parser = argparse.ArgumentParser(description="FreeCAD MCP Server")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    args = parser.parse_args()
    
    # Create and start the server
    server = FreeCADMCPServer(args.config)
    try:
        await server.start()
    finally:
        server.close()

if __name__ == "__main__":
    asyncio.run(main()) 