#!/usr/bin/env python3
"""
Advanced FreeCAD MCP Server using FastMCP

This script implements a Model Context Protocol (MCP) server for FreeCAD
using the FastMCP library and incorporating best practices.

Usage:
    python src/mcp_freecad/server/freecad_mcp_server.py
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional


# --- FastMCP Import ---
try:
    from fastmcp import FastMCP
    from fastmcp.error import MCPServerError, ErrorCode
    from fastmcp.server.stdio import stdio_server
    mcp_import_error = None
except ImportError as e:
    mcp_import_error = str(e)
    # Dummy classes/objects for type hints if import fails
    class FastMCP:
        def __init__(self, name: str, version: str = "0.1.0"): pass
        def tool(self): return lambda f: f
        def resource(self, pattern: str): return lambda f: f
        async def run_stdio(self): pass
    class MCPServerError(Exception): pass
    class ErrorCode: InvalidParams = -32602; InternalError = -32603; MethodNotFound = -32601
    class ToolContext: pass # Keep dummy for type hint usage in comments
    async def stdio_server(): pass # Simplified dummy

# --- FreeCAD Connection Import ---
# Adjust path based on actual location relative to this file
try:
    # Assuming execution from workspace root or correct PYTHONPATH
    from src.mcp_freecad.client.freecad_connection import FreeCADConnection
    FREECAD_CONNECTION_AVAILABLE = True
except ImportError:
    try:
        # Fallback if running from within the server directory structure
        from ...client.freecad_connection import FreeCADConnection
        FREECAD_CONNECTION_AVAILABLE = True
    except ImportError:
        logging.warning(
            "FreeCAD connection module not found. Trying relative import."
        )
        try:
            # Final fallback - assumes freecad_connection.py is findable
            from freecad_connection import FreeCADConnection
            FREECAD_CONNECTION_AVAILABLE = True
        except ImportError:
            logging.warning(
                "FreeCAD connection module could not be imported. Server will run without FreeCAD features."
            )
            FREECAD_CONNECTION_AVAILABLE = False
            FreeCADConnection = None # Define as None if unavailable

# --- Configuration & Globals ---
VERSION = "1.0.0" # Server version
CONFIG_PATH = "../../config.json"
CONFIG: Dict[str, Any] = {}
FC_CONNECTION: Optional[FreeCADConnection] = None

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, "freecad_mcp_server.log")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()  # Keep logging to console as well
    ]
)
logger = logging.getLogger("advanced_freecad_mcp")

# --- Configuration Loading ---
def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load config from {config_path}: {e}. Using defaults.")
        # Return default configuration
        return {
            "server": {"name": "advanced-freecad-mcp-server", "version": VERSION},
            "freecad": {
                "connection_method": "auto",  # auto, server, bridge, or mock
                "host": "localhost",
                "port": 12345,
                "freecad_path": "freecad",
            },
            "tools": {
                "enable_primitives": True,  # Enable primitive creation tools
                "enable_sketcher": True,    # Enable sketcher tools
                "enable_constraints": True, # Enable constraint tools
                "enable_measurements": True # Enable measurement tools
            }
        }

# --- FreeCAD Connection Initialization ---
def initialize_freecad_connection(config: Dict[str, Any]):
    """Initialize connection to FreeCAD."""
    global FC_CONNECTION
    if not FREECAD_CONNECTION_AVAILABLE or not FreeCADConnection:
        logger.warning(
            "FreeCAD connection unavailable. Skipping initialization."
        )
        FC_CONNECTION = None
        return

    freecad_config = config.get("freecad", {})
    logger.info("Attempting to connect to FreeCAD...")
    try:
        FC_CONNECTION = FreeCADConnection(
            host=freecad_config.get("host", "localhost"),
            port=freecad_config.get("port", 12345),
            freecad_path=freecad_config.get("freecad_path", "freecad"),
            auto_connect=True, # Attempt connection immediately
            prefer_method=freecad_config.get("connection_method", "auto"),
        )

        if FC_CONNECTION.is_connected():
            connection_type = FC_CONNECTION.get_connection_type()
            logger.info(f"Connected to FreeCAD using {connection_type} method")
            try:
                version_info = FC_CONNECTION.get_version()
                version_str = ".".join(
                    str(v) for v in version_info.get("version", ["Unknown"])
                )
                logger.info(f"FreeCAD version: {version_str}")
            except Exception as e:
                 logger.warning(f"Could not retrieve FreeCAD version: {e}")
        else:
            logger.warning("Failed to connect to FreeCAD initially. Tools requiring connection may fail.")
            FC_CONNECTION = None # Set to None if connection failed
    except Exception as e:
        logger.error(f"Error initializing FreeCAD connection: {e}")
        FC_CONNECTION = None

# --- Input Sanitization Helper ---
def sanitize_name(name: str) -> str:
    """Basic sanitization for names used in scripts (prevents breaking string literals)."""
    return name.replace('"', '\"').replace('\\', '\\\\')

def sanitize_path(path: str) -> str:
    """Basic path sanitization."""
    # Add more robust checks if needed (e.g., check against allowed directories)
    if ".." in path:
        raise MCPServerError(ErrorCode.InvalidParams, "Path cannot contain '..'")
    # Ensure absolute paths aren't used unexpectedly if desired
    # if os.path.isabs(path):
    #     raise MCPServerError(ErrorCode.InvalidParams, "Absolute paths are not allowed")
    return path

# --- Progress Reporting ---
class ToolContext:
    """Context for tool execution, including progress reporting capabilities."""

    _instance = None

    def __init__(self):
        self.progress_callback = None

    @classmethod
    def get(cls):
        """Get the singleton instance of ToolContext."""
        if cls._instance is None:
            cls._instance = ToolContext()
        return cls._instance

    def set_progress_callback(self, callback):
        """Set the callback function for progress reporting."""
        self.progress_callback = callback

    async def send_progress(self, progress: float, message: str = None):
        """
        Send a progress update.

        Args:
            progress: Progress value between 0.0 and 1.0
            message: Optional message describing the current progress
        """
        if self.progress_callback and callable(self.progress_callback):
            await self.progress_callback(progress, message)
        else:
            logger.debug(f"Progress update: {progress:.2%} - {message or 'Processing...'}")


# --- MCP Server Initialization ---
server_name = CONFIG.get("server", {}).get("name", "advanced-freecad-mcp-server")
mcp = FastMCP(server_name, version=VERSION)

# --- Helper for script execution ---
async def execute_script_in_freecad(script: str, env_vars_to_get: List[str] = None) -> Dict[str, Any]:
    """Executes a script in FreeCAD and handles errors/results."""
    if not FC_CONNECTION or not FC_CONNECTION.is_connected():
        raise MCPServerError(ErrorCode.InternalError, "Not connected to FreeCAD")

    env_vars_to_get = env_vars_to_get or []
    logger.debug(f"Executing script in FreeCAD: requesting env vars {env_vars_to_get}\n---\n{script}\n---")

    # Send initial progress update
    ctx = ToolContext.get()
    await ctx.send_progress(0.0, "Starting script execution...")

    try:
        # Send progress update before execution
        await ctx.send_progress(0.1, "Sending script to FreeCAD...")

        result = FC_CONNECTION.execute_command(
            "execute_script", {"script": script}
        )

        # Send progress update after sending command
        await ctx.send_progress(0.4, "Script sent, waiting for execution...")

        # Await if the connection method is async
        if asyncio.iscoroutine(result):
            result = await result

        # Send progress update after execution
        await ctx.send_progress(0.8, "Script executed, processing results...")

        if "error" in result:
            error_msg = result.get("error", "Unknown error from FreeCAD script execution")
            logger.error(f"FreeCAD script execution failed: {error_msg}")
            # Send error progress
            await ctx.send_progress(1.0, f"Error: {error_msg}")
            # Raise specific error type recognized by FastMCP
            raise MCPServerError(ErrorCode.InternalError, f"FreeCAD execution error: {error_msg}")

        env = result.get("environment", {})
        extracted_data = {var: env.get(var) for var in env_vars_to_get}
        logger.debug(f"Script execution successful. Env data received: {extracted_data}")

        # Send completion progress
        await ctx.send_progress(1.0, "Script execution completed successfully")
        return extracted_data

    except MCPServerError: # Re-raise MCP errors
         raise
    except Exception as e:
        logger.error(f"Error during script execution call: {e}", exc_info=True)
        # Send error progress
        await ctx.send_progress(1.0, f"Error: {str(e)}")
        raise MCPServerError(ErrorCode.InternalError, f"Server error during script execution: {str(e)}")

# --- Tool Definitions ---

# == FreeCAD Document Tools ==

@mcp.tool()
async def freecad_create_document(name: str = "Unnamed") -> Dict[str, Any]:
    """Create a new FreeCAD document."""
    if not FC_CONNECTION:
         raise MCPServerError(ErrorCode.InternalError, "FreeCAD connection not available")

    logger.info(f"Executing freecad.create_document with name: {name}")
    try:
        # Use direct API call - safer than script for simple ops
        doc_name = FC_CONNECTION.create_document(name)
        if not doc_name:
             raise MCPServerError(ErrorCode.InternalError, f"Failed to create document '{name}' in FreeCAD.")
        return {
            "document_name": doc_name,
            "message": f"Created document: {doc_name}",
            "success": True,
        }
    except Exception as e:
        logger.error(f"Error in freecad.create_document: {e}", exc_info=True)
        raise MCPServerError(ErrorCode.InternalError, f"Failed to create document: {str(e)}")


@mcp.tool()
async def freecad_list_documents() -> Dict[str, Any]:
    """List all open documents."""
    logger.info("Executing freecad.list_documents")
    script = """
import FreeCAD
import json
try:
    document_names = list(FreeCAD.listDocuments().keys())
    docs_json = json.dumps(document_names)
except Exception as e:
    # Propagate script errors back
    docs_json = json.dumps({"error": str(e)})
"""
    try:
        env_data = await execute_script_in_freecad(script, ["docs_json"])
        docs_json_str = env_data.get("docs_json", "[]")
        docs_data = json.loads(docs_json_str)

        if isinstance(docs_data, dict) and "error" in docs_data:
             raise MCPServerError(ErrorCode.InternalError, f"Error listing documents in FreeCAD: {docs_data['error']}")

        document_names = docs_data # Should be the list
        return {
            "documents": document_names,
            "count": len(document_names),
            "message": f"Found {len(document_names)} open documents",
            "success": True
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode document list from FreeCAD script")
        raise MCPServerError(ErrorCode.InternalError, "Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        # Ensure MCP error is raised if not already
        if not isinstance(e, MCPServerError):
            raise MCPServerError(ErrorCode.InternalError, f"Error listing documents: {str(e)}")
        else:
            raise e


@mcp.tool()
async def freecad_list_objects(document: Optional[str] = None) -> Dict[str, Any]:
    """List all objects in the specified or active document."""
    logger.info(f"Executing freecad.list_objects for document: {document or 'Active'}")
    safe_doc_name = sanitize_name(document) if document else ""

    script = f"""
import FreeCAD
import json

doc = None # Initialize doc to None *before* the try block
doc_name_for_msg = "Active Document"
doc_name_used = None # Variable to store the actual doc name

try:
    if "{safe_doc_name}":
        doc = FreeCAD.getDocument("{safe_doc_name}")
        if not doc: raise Exception(f"Document '{document}' not found")
        doc_name_for_msg = "document '{document}'"
    else:
        # Try to get active document, it might still be None
        doc = FreeCAD.ActiveDocument
        if not doc: raise Exception("No active document found")
        # Assign doc_name_for_msg only after confirming doc exists
        doc_name_for_msg = f"active document '{doc.Name}'"

    # At this point, doc should be a valid Document object if no exception was raised
    doc_name_used = doc.Name # Store the name

    objects_list = []
    for obj in doc.Objects:
        try:
            label = obj.Label if obj.Label else obj.Name # Use Name if Label is empty
        except AttributeError:
            label = obj.Name # Fallback if Label attribute doesn't exist
        objects_list.append({{"name": obj.Name, "type": obj.TypeId, "label": label}})

    # Serialize safely
    objects_json = json.dumps(objects_list)

except Exception as e:
    objects_json = json.dumps({{"error": str(e)}})
    # Ensure doc_name_used is captured even on error, if doc was assigned
    doc_name_used = doc.Name if doc else None # Now 'doc' is guaranteed to be defined (as None or the object)
"""
    try:
        env_data = await execute_script_in_freecad(script, ["objects_json", "doc_name_used", "doc_name_for_msg"])
        objects_json_str = env_data.get("objects_json", "[]")
        objects_data = json.loads(objects_json_str)

        if isinstance(objects_data, dict) and "error" in objects_data:
             raise MCPServerError(ErrorCode.InternalError, f"Error listing objects in FreeCAD: {objects_data['error']}")

        objects_list = objects_data
        doc_name_used = env_data.get("doc_name_used")
        doc_name_for_msg = env_data.get("doc_name_for_msg", doc_name_used or "unknown document")

        return {
            "objects": objects_list,
            "count": len(objects_list),
            "document": doc_name_used,
            "message": f"Found {len(objects_list)} objects in {doc_name_for_msg}",
            "success": True
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode object list from FreeCAD script")
        raise MCPServerError(ErrorCode.InternalError, "Failed to parse object list from FreeCAD")
    except Exception as e:
        logger.error(f"Error listing objects: {e}", exc_info=True)
        if not isinstance(e, MCPServerError):
            raise MCPServerError(ErrorCode.InternalError, f"Error listing objects: {str(e)}")
        else:
            raise e


# == FreeCAD Primitive Tools ==

@mcp.tool()
async def freecad_create_box(
    length: float, width: float, height: float,
    name: str = "Box",
    position_x: float = 0.0, position_y: float = 0.0, position_z: float = 0.0
) -> Dict[str, Any]:
    """Create a box primitive in the active or new document."""
    logger.info(f"Executing freecad.create_box: {name} ({length}x{width}x{height}) at ({position_x},{position_y},{position_z})")
    safe_name = sanitize_name(name)
    script = f"""
import FreeCAD
import Part
import json

box_name = None
try:
    doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("Unnamed")
    box = doc.addObject("Part::Box", "{safe_name}")
    box.Length = float({length})
    box.Width = float({width})
    box.Height = float({height})
    box.Placement.Base = FreeCAD.Vector(float({position_x}), float({position_y}), float({position_z}))
    doc.recompute()
    box_name = box.Name # Get the actual name assigned by FreeCAD
    result_json = json.dumps({{"object_name": box_name}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
             raise MCPServerError(ErrorCode.InternalError, f"Error creating box in FreeCAD: {result_data['error']}")

        created_name = result_data.get("object_name")
        return {
            "object_name": created_name,
            "message": f"Created box '{created_name}' with dimensions {length}x{width}x{height}mm",
            "success": True
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode box creation result from FreeCAD script")
        raise MCPServerError(ErrorCode.InternalError, "Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error creating box: {e}", exc_info=True)
        if not isinstance(e, MCPServerError):
            raise MCPServerError(ErrorCode.InternalError, f"Error creating box: {str(e)}")
        else:
            raise e

@mcp.tool()
async def freecad_create_cylinder(
    radius: float, height: float,
    name: str = "Cylinder",
    position_x: float = 0.0, position_y: float = 0.0, position_z: float = 0.0
) -> Dict[str, Any]:
    """Create a cylinder primitive."""
    logger.info(f"Executing freecad.create_cylinder: {name} (r={radius}, h={height}) at ({position_x},{position_y},{position_z})")
    safe_name = sanitize_name(name)
    script = f"""
import FreeCAD
import Part
import json

cylinder_name = None
try:
    doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("Unnamed")
    cylinder = doc.addObject("Part::Cylinder", "{safe_name}")
    cylinder.Radius = float({radius})
    cylinder.Height = float({height})
    cylinder.Placement.Base = FreeCAD.Vector(float({position_x}), float({position_y}), float({position_z}))
    doc.recompute()
    cylinder_name = cylinder.Name
    result_json = json.dumps({{"object_name": cylinder_name}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
             raise MCPServerError(ErrorCode.InternalError, f"Error creating cylinder in FreeCAD: {result_data['error']}")

        created_name = result_data.get("object_name")
        return {
            "object_name": created_name,
            "message": f"Created cylinder '{created_name}' with radius {radius}mm and height {height}mm",
            "success": True
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode cylinder creation result")
        raise MCPServerError(ErrorCode.InternalError, "Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error creating cylinder: {e}", exc_info=True)
        if not isinstance(e, MCPServerError):
             raise MCPServerError(ErrorCode.InternalError, f"Error creating cylinder: {str(e)}")
        else: raise e


@mcp.tool()
async def freecad_create_sphere(
    radius: float,
    name: str = "Sphere",
    position_x: float = 0.0, position_y: float = 0.0, position_z: float = 0.0
) -> Dict[str, Any]:
    """Create a sphere primitive."""
    logger.info(f"Executing freecad.create_sphere: {name} (r={radius}) at ({position_x},{position_y},{position_z})")
    safe_name = sanitize_name(name)
    script = f"""
import FreeCAD
import Part
import json

sphere_name = None
try:
    doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("Unnamed")
    sphere = doc.addObject("Part::Sphere", "{safe_name}")
    sphere.Radius = float({radius})
    sphere.Placement.Base = FreeCAD.Vector(float({position_x}), float({position_y}), float({position_z}))
    doc.recompute()
    sphere_name = sphere.Name
    result_json = json.dumps({{"object_name": sphere_name}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
             raise MCPServerError(ErrorCode.InternalError, f"Error creating sphere in FreeCAD: {result_data['error']}")

        created_name = result_data.get("object_name")
        return {
            "object_name": created_name,
            "message": f"Created sphere '{created_name}' with radius {radius}mm",
            "success": True
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode sphere creation result")
        raise MCPServerError(ErrorCode.InternalError, "Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error creating sphere: {e}", exc_info=True)
        if not isinstance(e, MCPServerError):
             raise MCPServerError(ErrorCode.InternalError, f"Error creating sphere: {str(e)}")
        else: raise e


@mcp.tool()
async def freecad_create_cone(
    radius1: float, height: float,
    radius2: float = 0.0, # Top radius defaults to 0 for a pointed cone
    name: str = "Cone",
    position_x: float = 0.0, position_y: float = 0.0, position_z: float = 0.0
) -> Dict[str, Any]:
    """Create a cone primitive."""
    logger.info(f"Executing freecad.create_cone: {name} (r1={radius1}, r2={radius2}, h={height}) at ({position_x},{position_y},{position_z})")
    safe_name = sanitize_name(name)
    script = f"""
import FreeCAD
import Part
import json

cone_name = None
try:
    doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("Unnamed")
    cone = doc.addObject("Part::Cone", "{safe_name}")
    cone.Radius1 = float({radius1})
    cone.Radius2 = float({radius2})
    cone.Height = float({height})
    cone.Placement.Base = FreeCAD.Vector(float({position_x}), float({position_y}), float({position_z}))
    doc.recompute()
    cone_name = cone.Name
    result_json = json.dumps({{"object_name": cone_name}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
             raise MCPServerError(ErrorCode.InternalError, f"Error creating cone in FreeCAD: {result_data['error']}")

        created_name = result_data.get("object_name")
        return {
            "object_name": created_name,
            "message": f"Created cone '{created_name}' with base radius {radius1}mm, top radius {radius2}mm, and height {height}mm",
            "success": True
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode cone creation result")
        raise MCPServerError(ErrorCode.InternalError, "Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error creating cone: {e}", exc_info=True)
        if not isinstance(e, MCPServerError):
             raise MCPServerError(ErrorCode.InternalError, f"Error creating cone: {str(e)}")
        else: raise e


# == FreeCAD Boolean Operations ==

@mcp.tool()
async def freecad_boolean_union(object1: str, object2: str, name: str = "Union") -> Dict[str, Any]:
    """Create a union of two objects (Fuse)."""
    logger.info(f"Executing freecad.boolean_union: {name} = {object1} + {object2}")

    # Get the ToolContext for progress reporting
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, "Starting boolean union operation...")

    safe_name = sanitize_name(name)
    safe_obj1 = sanitize_name(object1)
    safe_obj2 = sanitize_name(object2)

    await ctx.send_progress(0.2, "Preparing union operation script...")

    script = f"""
import FreeCAD
import Part
import json

union_name = None
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    obj1 = doc.getObject("{safe_obj1}")
    obj2 = doc.getObject("{safe_obj2}")
    if not obj1: raise Exception(f"Object '{object1}' not found")
    if not obj2: raise Exception(f"Object '{object2}' not found")

    union = doc.addObject("Part::Fuse", "{safe_name}")
    union.Base = obj1
    union.Tool = obj2
    doc.recompute()
    union_name = union.Name
    result_json = json.dumps({{"object_name": union_name}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        await ctx.send_progress(0.4, "Executing union operation in FreeCAD...")
        env_data = await execute_script_in_freecad(script, ["result_json"])

        await ctx.send_progress(0.8, "Processing union operation results...")
        result_json_str = env_data.get("result_json")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
             await ctx.send_progress(1.0, f"Union operation failed: {result_data['error']}")
             raise MCPServerError(ErrorCode.InternalError, f"Error creating union in FreeCAD: {result_data['error']}")

        created_name = result_data.get("object_name")
        await ctx.send_progress(1.0, f"Union operation completed: created {created_name}")
        return {
            "object_name": created_name,
            "message": f"Created union '{created_name}' of {object1} and {object2}",
            "success": True
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode union result")
        await ctx.send_progress(1.0, "Failed to parse response from FreeCAD")
        raise MCPServerError(ErrorCode.InternalError, "Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error performing boolean union: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Union operation error: {str(e)}")
        if not isinstance(e, MCPServerError):
             raise MCPServerError(ErrorCode.InternalError, f"Error creating union: {str(e)}")
        else: raise e

@mcp.tool()
async def freecad_boolean_cut(object1: str, object2: str, name: str = "Cut") -> Dict[str, Any]:
    """Cut the second object from the first (subtract)."""
    logger.info(f"Executing freecad.boolean_cut: {name} = {object1} - {object2}")
    safe_name = sanitize_name(name)
    safe_obj1 = sanitize_name(object1) # Base object
    safe_obj2 = sanitize_name(object2) # Tool object
    script = f"""
import FreeCAD
import Part
import json

cut_name = None
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    obj1 = doc.getObject("{safe_obj1}") # Base
    obj2 = doc.getObject("{safe_obj2}") # Tool
    if not obj1: raise Exception(f"Base object '{object1}' not found")
    if not obj2: raise Exception(f"Tool object '{object2}' not found")

    cut = doc.addObject("Part::Cut", "{safe_name}")
    cut.Base = obj1
    cut.Tool = obj2
    doc.recompute()
    cut_name = cut.Name
    result_json = json.dumps({{"object_name": cut_name}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
             raise MCPServerError(ErrorCode.InternalError, f"Error creating cut in FreeCAD: {result_data['error']}")

        created_name = result_data.get("object_name")
        return {
            "object_name": created_name,
            "message": f"Created cut '{created_name}' of {object1} by {object2}",
            "success": True
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode cut result")
        raise MCPServerError(ErrorCode.InternalError, "Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error performing boolean cut: {e}", exc_info=True)
        if not isinstance(e, MCPServerError):
             raise MCPServerError(ErrorCode.InternalError, f"Error creating cut: {str(e)}")
        else: raise e


@mcp.tool()
async def freecad_boolean_intersection(object1: str, object2: str, name: str = "Intersection") -> Dict[str, Any]:
    """Create the intersection of two objects (Common)."""
    logger.info(f"Executing freecad.boolean_intersection: {name} = {object1} & {object2}")
    safe_name = sanitize_name(name)
    safe_obj1 = sanitize_name(object1)
    safe_obj2 = sanitize_name(object2)
    script = f"""
import FreeCAD
import Part
import json

intersection_name = None
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    obj1 = doc.getObject("{safe_obj1}")
    obj2 = doc.getObject("{safe_obj2}")
    if not obj1: raise Exception(f"Object '{object1}' not found")
    if not obj2: raise Exception(f"Object '{object2}' not found")

    intersection = doc.addObject("Part::Common", "{safe_name}")
    # Part.Common takes a list of shapes
    intersection.Shapes = [obj1, obj2]
    doc.recompute()
    intersection_name = intersection.Name
    result_json = json.dumps({{"object_name": intersection_name}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
             raise MCPServerError(ErrorCode.InternalError, f"Error creating intersection in FreeCAD: {result_data['error']}")

        created_name = result_data.get("object_name")
        return {
            "object_name": created_name,
            "message": f"Created intersection '{created_name}' of {object1} and {object2}",
            "success": True
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode intersection result")
        raise MCPServerError(ErrorCode.InternalError, "Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error performing boolean intersection: {e}", exc_info=True)
        if not isinstance(e, MCPServerError):
             raise MCPServerError(ErrorCode.InternalError, f"Error creating intersection: {str(e)}")
        else: raise e

# == FreeCAD Transformation Tools ==

@mcp.tool()
async def freecad_move_object(
    object_name: str,
    x: Optional[float] = None, y: Optional[float] = None, z: Optional[float] = None
) -> Dict[str, Any]:
    """Move an object to a new absolute position. Specify at least one coordinate."""
    if x is None and y is None and z is None:
         raise MCPServerError(ErrorCode.InvalidParams, "At least one coordinate (x, y, or z) must be provided for move_object")

    logger.info(f"Executing freecad.move_object: {object_name} to (x={x}, y={y}, z={z})")
    safe_obj_name = sanitize_name(object_name)

    # Build the script carefully to handle optional coordinates
    script_lines = [
        "import FreeCAD",
        "import json",
        "new_pos_x = None; new_pos_y = None; new_pos_z = None", # Vars to store final pos
        "try:",
        "    doc = FreeCAD.ActiveDocument",
        "    if not doc: raise Exception(\"No active document\")",
        f"   obj = doc.getObject(\"{safe_obj_name}\")",
        f"   if not obj: raise Exception(\"Object '{object_name}' not found\")",
        "    current_pos = obj.Placement.Base",
        "    target_pos = FreeCAD.Vector(current_pos.x, current_pos.y, current_pos.z)" # Start with current
    ]
    if x is not None: script_lines.append(f"   target_pos.x = float({x})")
    if y is not None: script_lines.append(f"   target_pos.y = float({y})")
    if z is not None: script_lines.append(f"   target_pos.z = float({z})")

    script_lines.extend([
        "    obj.Placement.Base = target_pos",
        "    doc.recompute()",
        "    final_pos = obj.Placement.Base", # Read back final position
        "    new_pos_x = final_pos.x",
        "    new_pos_y = final_pos.y",
        "    new_pos_z = final_pos.z",
        "    result_json = json.dumps({'x': new_pos_x, 'y': new_pos_y, 'z': new_pos_z})",
        "except Exception as e:",
        "    result_json = json.dumps({'error': str(e)})"
    ])
    script = "\n".join(script_lines)

    try:
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
             raise MCPServerError(ErrorCode.InternalError, f"Error moving object in FreeCAD: {result_data['error']}")

        final_pos = result_data # Should contain x, y, z
        return {
            "object_name": object_name,
            "position": final_pos,
            "message": f"Moved object '{object_name}' to position ({final_pos.get('x'):.2f}, {final_pos.get('y'):.2f}, {final_pos.get('z'):.2f})",
            "success": True
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode move result")
        raise MCPServerError(ErrorCode.InternalError, "Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error moving object: {e}", exc_info=True)
        if not isinstance(e, MCPServerError):
             raise MCPServerError(ErrorCode.InternalError, f"Error moving object: {str(e)}")
        else: raise e


@mcp.tool()
async def freecad_rotate_object(
    object_name: str,
    angle_x: float = 0.0, angle_y: float = 0.0, angle_z: float = 0.0
) -> Dict[str, Any]:
    """Rotate an object by Euler angles (degrees) around its placement base point."""
    logger.info(f"Executing freecad.rotate_object: {object_name} by (x={angle_x}, y={angle_y}, z={angle_z}) deg")
    safe_obj_name = sanitize_name(object_name)

    script = f"""
import FreeCAD
import math
import json

final_rot_x = 0.0; final_rot_y = 0.0; final_rot_z = 0.0 # Store result
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    obj = doc.getObject("{safe_obj_name}")
    if not obj: raise Exception(f"Object '{object_name}' not found")

    # Convert degrees to radians
    rot_x_rad = math.radians(float({angle_x}))
    rot_y_rad = math.radians(float({angle_y}))
    rot_z_rad = math.radians(float({angle_z}))

    # Create rotation object for the *increment*
    # Assuming XYZ rotation order for the incremental rotation
    incremental_rotation = FreeCAD.Rotation(rot_x_rad, rot_y_rad, rot_z_rad)

    # Apply the incremental rotation to the object's current placement
    current_placement = obj.Placement
    # Rotation is multiplied: new_rot = increment * old_rot
    new_rotation = incremental_rotation.multiply(current_placement.Rotation)
    # Keep the same base point
    new_placement = FreeCAD.Placement(current_placement.Base, new_rotation, current_placement.Base)
    obj.Placement = new_placement

    doc.recompute()

    # Get final rotation as Euler angles (may differ slightly from input due to quaternion math)
    # FreeCAD's getYawPitchRoll() returns ZYX order
    final_angles = obj.Placement.Rotation.getYawPitchRoll()
    final_rot_z = math.degrees(final_angles[0]) # Yaw
    final_rot_y = math.degrees(final_angles[1]) # Pitch
    final_rot_x = math.degrees(final_angles[2]) # Roll
    result_json = json.dumps({{'applied_x': {angle_x}, 'applied_y': {angle_y}, 'applied_z': {angle_z},
                               'final_x': final_rot_x, 'final_y': final_rot_y, 'final_z': final_rot_z}})

except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
             raise MCPServerError(ErrorCode.InternalError, f"Error rotating object in FreeCAD: {result_data['error']}")

        applied = { k.split('_')[1]: v for k, v in result_data.items() if k.startswith('applied_')}
        # final = { k.split('_')[1]: v for k, v in result_data.items() if k.startswith('final_')}

        return {
            "object_name": object_name,
            "rotation_applied": applied,
            # "final_rotation_euler_zyx": final, # Optional: return final calculated angles
            "message": f"Applied rotation ({applied.get('x', 0.0):.1f}, {applied.get('y', 0.0):.1f}, {applied.get('z', 0.0):.1f}) degrees to object '{object_name}'",
            "success": True
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode rotation result")
        raise MCPServerError(ErrorCode.InternalError, "Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error rotating object: {e}", exc_info=True)
        if not isinstance(e, MCPServerError):
             raise MCPServerError(ErrorCode.InternalError, f"Error rotating object: {str(e)}")
        else: raise e


# == FreeCAD Export Tools ==

@mcp.tool()
async def freecad_export_stl(file_path: str, objects: Optional[List[str]] = None, document: Optional[str] = None) -> Dict[str, Any]:
    """Export specified objects (or all if none specified) from a document to an STL file."""
    logger.info(f"Executing freecad.export_stl to: {file_path} (Objects: {objects}, Doc: {document})")

    # Get the ToolContext for progress reporting
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, "Starting STL export...")

    # Basic path validation
    safe_file_path = sanitize_path(file_path)
    if not safe_file_path.lower().endswith(".stl"):
         raise MCPServerError(ErrorCode.InvalidParams, "Invalid file_path. Must end with .stl")

    # Ensure objects is a list of strings if provided
    if objects is not None and (not isinstance(objects, list) or not all(isinstance(o, str) for o in objects)):
         raise MCPServerError(ErrorCode.InvalidParams, "Parameter 'objects' must be a list of strings.")

    await ctx.send_progress(0.2, "Validating export parameters...")

    # Use direct API call if available and seems robust enough
    if FC_CONNECTION and hasattr(FC_CONNECTION, 'export_stl'):
        try:
             await ctx.send_progress(0.3, "Using direct export method...")
             success = FC_CONNECTION.export_stl(
                 object_names=objects, # Pass list of names directly
                 file_path=safe_file_path,
                 document=document
             )
             await ctx.send_progress(0.9, "Export operation completed, finalizing...")
             if success:
                 await ctx.send_progress(1.0, "Export completed successfully")
                 return {
                     "file_path": safe_file_path,
                     "message": f"Exported {'selected objects' if objects else 'active model'} to {safe_file_path}",
                     "success": True,
                 }
             else:
                  # export_stl likely raises exception on failure, but handle False return just in case
                  await ctx.send_progress(1.0, "Export failed")
                  raise MCPServerError(ErrorCode.InternalError, "FreeCADConnection.export_stl returned False.")
        except Exception as e:
             logger.error(f"Error during direct export_stl call: {e}", exc_info=True)
             await ctx.send_progress(1.0, f"Export error: {str(e)}")
             raise MCPServerError(ErrorCode.InternalError, f"Failed to export STL (direct call): {str(e)}")
    else:
        # Fallback to script execution if direct method isn't available/preferred
        logger.warning("Falling back to script execution for export_stl")
        await ctx.send_progress(0.3, "Using script-based export method...")

        safe_doc_name = sanitize_name(document) if document else ""
        # Convert list of object names into a Python list string for the script
        objects_list_str = "None"
        if objects:
            sanitized_object_names = [f'"{sanitize_name(o)}"' for o in objects]
            objects_list_str = f'[{", ".join(sanitized_object_names)}]'

        await ctx.send_progress(0.4, "Preparing export script...")

        script = f"""
import FreeCAD
import Mesh
import json

success = False
error_msg = ''
try:
    doc = None
    if "{safe_doc_name}":
        doc = FreeCAD.getDocument("{safe_doc_name}")
        if not doc: raise Exception(f"Document '{document}' not found")
    else:
        doc = FreeCAD.ActiveDocument
        if not doc: raise Exception("No active document found")

    obj_list_to_export = []
    export_obj_names = {objects_list_str} # Use the generated list string or None

    if export_obj_names is None:
        # Export all Part::Feature objects if no specific list given
        obj_list_to_export = [o for o in doc.Objects if hasattr(o, 'Shape') and o.TypeId.startswith('Part::')]
    else:
        for name in export_obj_names:
            obj = doc.getObject(name)
            if obj and hasattr(obj, 'Shape'):
                obj_list_to_export.append(obj)
            else:
                raise Exception(f"Object '{{name}}' not found or is not exportable.")

    if not obj_list_to_export:
        raise Exception("No valid objects found to export.")

    # Mesh.export expects list of objects, not names
    Mesh.export(obj_list_to_export, u"{safe_file_path}")
    success = True
except Exception as e:
    error_msg = str(e)

result_json = json.dumps({{"success": success, "error": error_msg}})
"""
        try:
            await ctx.send_progress(0.5, "Executing export script in FreeCAD...")
            env_data = await execute_script_in_freecad(script, ["result_json"])
            await ctx.send_progress(0.9, "Processing export results...")

            result_json_str = env_data.get("result_json")
            result_data = json.loads(result_json_str)

            if result_data.get("error"):
                 await ctx.send_progress(1.0, f"Export failed: {result_data['error']}")
                 raise MCPServerError(ErrorCode.InternalError, f"Error exporting STL in FreeCAD: {result_data['error']}")

            if result_data.get("success"):
                 await ctx.send_progress(1.0, "Export completed successfully")
                 return {
                    "file_path": safe_file_path,
                    "message": f"Exported {'selected objects' if objects else 'model'} to {safe_file_path} (via script)",
                    "success": True,
                 }
            else:
                 await ctx.send_progress(1.0, "Export failed silently")
                 raise MCPServerError(ErrorCode.InternalError, "STL export script failed silently.")

        except json.JSONDecodeError:
            logger.error("Failed to decode export result")
            await ctx.send_progress(1.0, "Failed to parse response from FreeCAD")
            raise MCPServerError(ErrorCode.InternalError, "Failed to parse response from FreeCAD")
        except Exception as e:
            logger.error(f"Error exporting STL (script fallback): {e}", exc_info=True)
            await ctx.send_progress(1.0, f"Export error: {str(e)}")
            if not isinstance(e, MCPServerError):
                 raise MCPServerError(ErrorCode.InternalError, f"Error exporting STL: {str(e)}")
            else: raise e


# --- Resource Definitions ---

@mcp.resource("freecad://info")
async def get_freecad_info() -> str:
    """Get information about the connected FreeCAD instance."""
    logger.info("Executing get_freecad_info resource")
    if not FC_CONNECTION or not FC_CONNECTION.is_connected():
        # Resources typically return content or raise errors
        # Returning an error message string might be acceptable for info resources
        return "Error: Not currently connected to FreeCAD."
        # Alternatively, raise an error:
        # raise MCPServerError(ErrorCode.InternalError, "Not connected to FreeCAD")

    try:
        version_info = FC_CONNECTION.get_version()
        version_str = ".".join(str(v) for v in version_info.get("version", ["Unknown"]))
        connection_type = FC_CONNECTION.get_connection_type()
        # FastMCP resource handlers typically return the content directly
        return f"FreeCAD Version: {version_str}\nConnection Type: {connection_type}"
    except Exception as e:
        logger.error(f"Error getting FreeCAD info: {e}")
        # Return error string for info resource
        return f"Error retrieving FreeCAD info: {str(e)}"
        # Alternatively, raise:
        # raise MCPServerError(ErrorCode.InternalError, f"Error getting FreeCAD info: {str(e)}")

# --- Main Execution ---
def main():
    global CONFIG # Allow modifying global config

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Advanced FreeCAD MCP Server")
    parser.add_argument("--config", default=CONFIG_PATH, help=f"Path to config file (default: {CONFIG_PATH})")
    parser.add_argument("--host", help="Override FreeCAD connection hostname")
    parser.add_argument("--port", type=int, help="Override FreeCAD connection port")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--version", action="store_true", help="Show server version and exit")
    args = parser.parse_args()

    # --- Version Info ---
    if args.version:
        print(f"Advanced-MCP-FreeCAD Server v{VERSION}")
        # Optionally add FreeCAD version check here if needed before full connection init
        return

    # --- Setup Logging ---
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # --- Check MCP Dependency ---
    if mcp_import_error:
        logger.error(f"ERROR: FastMCP SDK (fastmcp package) not found or import failed: {mcp_import_error}")
        logger.error("Please install it with: pip install fastmcp")
        sys.exit(1)

    # --- Load Configuration ---
    CONFIG = load_config(args.config)
    # Override config with command line arguments if provided
    if args.host:
        CONFIG.setdefault("freecad", {})["host"] = args.host
    if args.port:
        CONFIG.setdefault("freecad", {})["port"] = args.port

    # --- Initialize FreeCAD Connection ---
    initialize_freecad_connection(CONFIG)

    # --- Configure Progress Reporting ---
    tool_context = ToolContext.get()
    try:
        # Try to import and use FastMCP progress reporting if available
        from fastmcp.server.context import get_current_context

        # Set up progress callback that integrates with FastMCP's progress reporting
        async def progress_callback(progress_value, message=None):
            try:
                context = get_current_context()
                if hasattr(context, 'send_progress'):
                    await context.send_progress(progress_value, message)
                else:
                    logger.debug(f"Progress: {progress_value:.0%} - {message or ''}")
            except Exception as e:
                logger.debug(f"Error sending progress: {e}")

        tool_context.set_progress_callback(progress_callback)
        logger.info("Progress reporting configured with FastMCP")
    except ImportError:
        logger.info("FastMCP progress context not available, using local progress reporting")

    # --- Start Server ---
    logger.info(f"Starting {server_name} v{VERSION}...")
    try:
        asyncio.run(mcp.run_stdio())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running server: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup FreeCAD connection if it was established
        if FC_CONNECTION and hasattr(FC_CONNECTION, 'close'):
            logger.info("Closing FreeCAD connection...")
            FC_CONNECTION.close()
        logger.info("Server shutdown complete.")


if __name__ == "__main__":
    main()
