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
import logging.handlers
import os
import pickle
import socketserver
import struct
import sys
import threading
from typing import Any, Dict, List, Optional

# --- FastMCP Import ---
try:
    from fastmcp import FastMCP
    from fastmcp.exceptions import FastMCPError  # Use actual exception name

    mcp_import_error = None
except ImportError as e:
    mcp_import_error = str(e)

    # Dummy classes/objects for type hints if import fails
    class FastMCP:
        def __init__(self, name: str, version: str = "0.1.0"):
            pass

        def tool(self):
            return lambda f: f

        def resource(self, pattern: str):
            return lambda f: f

        async def run_stdio(self):
            pass

    class FastMCPError(Exception):
        pass  # Define dummy for the actual exception

    # ErrorCode is not defined in fastmcp 0.4.1 exceptions
    # class ErrorCode: InvalidParams = -32602; InternalError = -32603; MethodNotFound = -32601
    class ToolContext:
        pass  # Keep dummy for type hint usage in comments


# --- FreeCAD Connection Import ---
# Import the correct FreeCADConnection class from freecad_connection_manager
try:
    # Assuming execution from workspace root or correct PYTHONPATH
    from src.mcp_freecad.client.freecad_connection_manager import FreeCADConnection

    FREECAD_CONNECTION_AVAILABLE = True
except ImportError:
    try:
        # Fallback if running from within the server directory structure
        from ...client.freecad_connection_manager import FreeCADConnection

        FREECAD_CONNECTION_AVAILABLE = True
    except ImportError:
        logging.warning(
            "FreeCAD connection manager module could not be imported. Server will run without FreeCAD features."
        )
        FREECAD_CONNECTION_AVAILABLE = False
        FreeCADConnection = None  # Define as None if unavailable

# --- Configuration & Globals ---
VERSION = "1.0.0"  # Server version
CONFIG_PATH = "config.json"  # Path relative to repo root
CONFIG: Dict[str, Any] = {}
FC_CONNECTION: Optional[FreeCADConnection] = None

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, "freecad_mcp_server.log")
LOGGING_PORT = 9020  # Define port for logging receiver

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler(),  # Keep logging to console as well
    ],
)
logger = logging.getLogger("advanced_freecad_mcp")

# --- Logging Socket Receiver ---


class LogRequestHandler(socketserver.StreamRequestHandler):
    """Handler for incoming log records."""

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the pickled log record. Logs the record.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))

            try:
                obj = pickle.loads(chunk)
                record = logging.makeLogRecord(obj)
                # Process the record using the server's logger
                logger.handle(record)
            except Exception as e:
                logger.error(f"Error processing log record: {e}")
                # Log the raw chunk data if unpickling fails
                logger.debug(f"Raw log data received: {chunk!r}")
                break  # Stop processing if there's an error with this connection


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """Simple TCP socket server to receive log records."""

    allow_reuse_address = True

    def __init__(self, host="localhost", port=LOGGING_PORT, handler=LogRequestHandler):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select

        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()], [], [], self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort


# --- Configuration Loading ---
def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(
            f"Could not load config from {config_path}: {e}. Using defaults."
        )
        # Return default configuration
        return {
            "server": {"name": "advanced-freecad-mcp-server", "version": VERSION},
            "freecad": {
                "connection_method": "auto",  # auto, server, or bridge
                "host": "localhost",
                "port": 12345,
                "freecad_path": "freecad",
            },
            "tools": {
                "enable_primitives": True,  # Enable primitive creation tools
                "enable_sketcher": True,  # Enable sketcher tools
                "enable_constraints": True,  # Enable constraint tools
                "enable_measurements": True,  # Enable measurement tools
            },
        }


# --- FreeCAD Connection Initialization ---
def initialize_freecad_connection(config: Dict[str, Any]):
    """Initialize connection to FreeCAD."""
    global FC_CONNECTION
    if not FREECAD_CONNECTION_AVAILABLE or not FreeCADConnection:
        logger.warning("FreeCAD connection unavailable. Skipping initialization.")
        FC_CONNECTION = None
        return

    freecad_config = config.get("freecad", {})
    logger.info("Attempting to connect to FreeCAD (preferring bridge mode)...")
    try:
        # Force prefer_method to 'bridge' for headless server
        FC_CONNECTION = FreeCADConnection(
            host=freecad_config.get("host", "localhost"),
            port=freecad_config.get("port", 12345),
            freecad_path=freecad_config.get("freecad_path", "freecad"),
            auto_connect=True,
            prefer_method="bridge",  # Explicitly set bridge as preferred
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
            logger.warning("Failed to connect to FreeCAD using bridge method.")
            FC_CONNECTION = None  # Set to None if connection failed
    except Exception as e:
        logger.error(f"Error initializing FreeCAD connection: {e}")
        FC_CONNECTION = None


# --- Input Sanitization Helper ---
def sanitize_name(name: str) -> str:
    """Basic sanitization for names used in scripts (prevents breaking string literals)."""
    return name.replace('"', '\\"').replace("\\\\", "\\\\\\\\")


def sanitize_path(path: str) -> str:
    """Basic path sanitization."""
    # Add more robust checks if needed (e.g., check against allowed directories)
    if ".." in path:
        raise FastMCPError("Path cannot contain '..'")
    # Ensure absolute paths aren't used unexpectedly if desired
    # if os.path.isabs(path):
    #     raise FastMCPError("Absolute paths are not allowed")
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
            logger.debug(
                f"Progress update: {progress:.2%} - {message or 'Processing...'}"
            )


# --- MCP Server Initialization ---
server_name = CONFIG.get("server", {}).get("name", "advanced-freecad-mcp-server")
mcp = FastMCP(server_name, version=VERSION)


# --- Background Connection Check ---
async def connection_check_loop(config: Dict[str, Any]):
    """Periodically checks and attempts to establish FreeCAD connection if not already connected."""
    global FC_CONNECTION
    check_interval = 5  # seconds
    freecad_config = config.get("freecad", {})
    logger.info(
        f"Starting background FreeCAD connection check (interval: {check_interval}s)"
    )

    while True:
        try:
            if FC_CONNECTION is None or not FC_CONNECTION.is_connected():
                logger.info(
                    "Attempting to establish FreeCAD connection (background check)..."
                )
                temp_connection = None
                try:
                    # Attempt connection using the preferred bridge method
                    temp_connection = FreeCADConnection(
                        host=freecad_config.get("host", "localhost"),
                        port=freecad_config.get("port", 12345),
                        freecad_path=freecad_config.get("freecad_path", "freecad"),
                        auto_connect=False,  # Connect manually below
                        prefer_method="bridge",
                    )
                    if temp_connection.connect(
                        prefer_method="bridge"
                    ):  # Explicitly connect
                        connection_type = temp_connection.get_connection_type()
                        logger.info(
                            f"Successfully connected to FreeCAD via {connection_type} (background check)"
                        )
                        # Check version info (optional, but good feedback)
                        try:
                            version_info = temp_connection.get_version()
                            version_str = ".".join(
                                str(v) for v in version_info.get("version", ["Unknown"])
                            )
                            logger.info(
                                f"FreeCAD version: {version_str} (background check)"
                            )
                        except Exception as e:
                            logger.warning(
                                f"Could not retrieve FreeCAD version (background check): {e}"
                            )

                        # Assign to global connection object
                        FC_CONNECTION = temp_connection
                    else:
                        # Connection failed, FC_CONNECTION remains None
                        # Logger warning happens inside connect() or FreeCADConnection init implicitly
                        logger.debug("Background connection attempt failed.")
                        # Explicitly close if connection object was created but connect failed
                        if temp_connection and hasattr(temp_connection, "close"):
                            temp_connection.close()

                except Exception as e:
                    logger.error(
                        f"Error during background FreeCAD connection attempt: {e}",
                        exc_info=False,
                    )  # Log less verbosely
                    # Explicitly close if connection object was created but failed during setup
                    if temp_connection and hasattr(temp_connection, "close"):
                        temp_connection.close()

            # Wait for the next check interval
            await asyncio.sleep(check_interval)

        except asyncio.CancelledError:
            logger.info("Connection check loop cancelled.")
            break  # Exit the loop if cancelled
        except Exception as e:
            # Log unexpected errors in the loop itself
            logger.error(
                f"Unexpected error in connection_check_loop: {e}", exc_info=True
            )
            await asyncio.sleep(check_interval)  # Still wait before retrying


# --- Helper for script execution ---
async def execute_script_in_freecad(
    script: str, env_vars_to_get: List[str] = None
) -> Dict[str, Any]:
    """Executes a script in FreeCAD and handles errors/results."""
    if not FC_CONNECTION or not FC_CONNECTION.is_connected():
        raise FastMCPError("Not connected to FreeCAD")

    env_vars_to_get = env_vars_to_get or []
    logger.debug(
        f"Executing script in FreeCAD: requesting env vars {env_vars_to_get}\n---\n{script}\n---"
    )

    # Send initial progress update
    ctx = ToolContext.get()
    await ctx.send_progress(0.0, "Starting script execution...")

    try:
        # Send progress update before execution
        await ctx.send_progress(0.1, "Sending script to FreeCAD...")

        result = FC_CONNECTION.execute_command("execute_script", {"script": script})

        # Send progress update after sending command
        await ctx.send_progress(0.4, "Script sent, waiting for execution...")

        # Await if the connection method is async
        if asyncio.iscoroutine(result):
            result = await result

        # Send progress update after execution
        await ctx.send_progress(0.8, "Script executed, processing results...")

        if "error" in result:
            error_msg = result.get(
                "error", "Unknown error from FreeCAD script execution"
            )
            logger.error(f"FreeCAD script execution failed: {error_msg}")
            # Send error progress
            await ctx.send_progress(1.0, f"Error: {error_msg}")
            raise FastMCPError(f"FreeCAD execution error: {error_msg}")

        env = result.get("environment", {})
        extracted_data = {var: env.get(var) for var in env_vars_to_get}
        logger.debug(
            f"Script execution successful. Env data received: {extracted_data}"
        )

        # Send completion progress
        await ctx.send_progress(1.0, "Script execution completed successfully")

        return extracted_data

    except FastMCPError:  # Catch specific error type
        raise
    except Exception as e:
        logger.error(f"Error during script execution call: {e}", exc_info=True)
        # Send error progress
        await ctx.send_progress(1.0, f"Error: {str(e)}")
        raise FastMCPError(f"Server error during script execution: {str(e)}")


# --- Tool Definitions ---


# == FreeCAD Document/Object Tools ==
@mcp.tool()
async def freecad_create_document(name: str = "Unnamed") -> Dict[str, Any]:
    """Create a new FreeCAD document."""
    if not FC_CONNECTION:
        raise FastMCPError("FreeCAD connection not available")

    logger.info(f"Executing freecad.create_document with name: {name}")
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, f"Creating document '{name}'...")
    try:
        doc_name = FC_CONNECTION.create_document(name)
        if not doc_name:
            raise FastMCPError(f"Failed to create document '{name}' in FreeCAD.")
        await ctx.send_progress(1.0, "Document created successfully")
        return {
            "document_name": doc_name,
            "message": f"Successfully created document '{doc_name}'",
            "success": True,
        }
    except Exception as e:
        logger.error(f"Error in freecad.create_document: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Failed to create document: {str(e)}")
        raise FastMCPError(f"Failed to create document: {str(e)}")


@mcp.tool()
async def freecad_list_documents() -> Dict[str, Any]:
    """List all open documents in FreeCAD."""
    logger.info("Executing freecad.list_documents")
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, "Listing documents...")

    script = f"""
import FreeCAD
import json
try:
    docs = [doc.Name for doc in FreeCAD.listDocuments().values()]
    result_json = json.dumps(docs)
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        await ctx.send_progress(0.3, "Executing document list script...")
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        if not result_json_str:
            raise FastMCPError("Did not receive result from FreeCAD script")
        docs_data = json.loads(result_json_str)

        if isinstance(docs_data, dict) and "error" in docs_data:
            raise FastMCPError(
                f"Error listing documents in FreeCAD: {docs_data['error']}"
            )

        document_names = docs_data  # Should be the list
        await ctx.send_progress(1.0, "Documents listed successfully")
        return {
            "documents": document_names,
            "count": len(document_names),
            "message": f"Found {len(document_names)} open documents.",
            "success": True,
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode document list from FreeCAD script")
        await ctx.send_progress(1.0, "Failed to parse response")
        raise FastMCPError("Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Error: {str(e)}")
        if not isinstance(e, FastMCPError):
            raise FastMCPError(f"Error listing documents: {str(e)}")
        else:
            raise e


@mcp.tool()
async def freecad_list_objects(document: Optional[str] = None) -> Dict[str, Any]:
    """List objects in a specific document (or active one if none specified)."""
    logger.info(f"Executing freecad.list_objects (Document: {document})")
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, "Listing objects...")

    safe_doc_name = sanitize_name(document) if document else ""

    script = f"""
import FreeCAD
import json
try:
    doc = None
    if "{safe_doc_name}":
        doc = FreeCAD.getDocument("{safe_doc_name}")
        if not doc: raise Exception(f"Document '{document}' not found")
    else:
        doc = FreeCAD.ActiveDocument
        if not doc: raise Exception("No active document found")

    objects = [obj.Name for obj in doc.Objects]
    result_json = json.dumps(objects)
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        await ctx.send_progress(0.3, "Executing object list script...")
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        if not result_json_str:
            raise FastMCPError("Did not receive result from FreeCAD script")
        objects_data = json.loads(result_json_str)

        if isinstance(objects_data, dict) and "error" in objects_data:
            raise FastMCPError(
                f"Error listing objects in FreeCAD: {objects_data['error']}"
            )

        objects_list = objects_data
        await ctx.send_progress(1.0, "Objects listed successfully")
        return {
            "objects": objects_list,
            "count": len(objects_list),
            "document": document
            or (
                FC_CONNECTION.get_active_document_name() if FC_CONNECTION else "Active"
            ),
            "message": f"Found {len(objects_list)} objects.",
            "success": True,
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode object list from FreeCAD script")
        await ctx.send_progress(1.0, "Failed to parse response")
        raise FastMCPError("Failed to parse object list from FreeCAD")
    except Exception as e:
        logger.error(f"Error listing objects: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Error: {str(e)}")
        if not isinstance(e, FastMCPError):
            raise FastMCPError(f"Error listing objects: {str(e)}")
        else:
            raise e


# == Part Primitive Creation Tools ==
@mcp.tool()
async def freecad_create_box(
    length: float,
    width: float,
    height: float,
    name: str = "Box",
    position_x: float = 0.0,
    position_y: float = 0.0,
    position_z: float = 0.0,
) -> Dict[str, Any]:
    """Create a box primitive."""
    logger.info(f"Executing freecad.create_box: {name}")
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, f"Creating box '{name}'...")

    safe_name = sanitize_name(name)
    script = f"""
import FreeCAD
import Part
import json
result_json = ''
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    box = doc.addObject("Part::Box", "{safe_name}")
    box.Length = float({length})
    box.Width = float({width})
    box.Height = float({height})
    box.Placement.Base.x = float({position_x})
    box.Placement.Base.y = float({position_y})
    box.Placement.Base.z = float({position_z})
    doc.recompute()
    result_json = json.dumps({{"object_name": box.Name, "type": "Box"}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        await ctx.send_progress(0.3, "Executing box creation script...")
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        if not result_json_str:
            raise FastMCPError("Did not receive result from FreeCAD script")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
            raise FastMCPError(f"Error creating box in FreeCAD: {result_data['error']}")

        created_name = result_data.get("object_name")
        await ctx.send_progress(1.0, "Box created successfully")
        return {
            "object_name": created_name,
            "type": "Box",
            "message": f"Successfully created box '{created_name}'",
            "success": True,
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode box creation result from FreeCAD script")
        await ctx.send_progress(1.0, "Failed to parse response")
        raise FastMCPError("Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error creating box: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Error: {str(e)}")
        if not isinstance(e, FastMCPError):
            raise FastMCPError(f"Error creating box: {str(e)}")
        else:
            raise e


@mcp.tool()
async def freecad_create_cylinder(
    radius: float,
    height: float,
    name: str = "Cylinder",
    position_x: float = 0.0,
    position_y: float = 0.0,
    position_z: float = 0.0,
) -> Dict[str, Any]:
    """Create a cylinder primitive."""
    logger.info(f"Executing freecad.create_cylinder: {name}")
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, f"Creating cylinder '{name}'...")

    safe_name = sanitize_name(name)
    script = f"""
import FreeCAD
import Part
import json
result_json = ''
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    cyl = doc.addObject("Part::Cylinder", "{safe_name}")
    cyl.Radius = float({radius})
    cyl.Height = float({height})
    cyl.Placement.Base.x = float({position_x})
    cyl.Placement.Base.y = float({position_y})
    cyl.Placement.Base.z = float({position_z})
    doc.recompute()
    result_json = json.dumps({{"object_name": cyl.Name, "type": "Cylinder"}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        await ctx.send_progress(0.3, "Executing cylinder creation script...")
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        if not result_json_str:
            raise FastMCPError("Did not receive result from FreeCAD script")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
            raise FastMCPError(
                f"Error creating cylinder in FreeCAD: {result_data['error']}"
            )

        created_name = result_data.get("object_name")
        await ctx.send_progress(1.0, "Cylinder created successfully")
        return {
            "object_name": created_name,
            "type": "Cylinder",
            "message": f"Successfully created cylinder '{created_name}'",
            "success": True,
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode cylinder creation result")
        await ctx.send_progress(1.0, "Failed to parse response")
        raise FastMCPError("Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error creating cylinder: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Error: {str(e)}")
        if not isinstance(e, FastMCPError):
            raise FastMCPError(f"Error creating cylinder: {str(e)}")
        else:
            raise e


@mcp.tool()
async def freecad_create_sphere(
    radius: float,
    name: str = "Sphere",
    position_x: float = 0.0,
    position_y: float = 0.0,
    position_z: float = 0.0,
) -> Dict[str, Any]:
    """Create a sphere primitive."""
    logger.info(f"Executing freecad.create_sphere: {name}")
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, f"Creating sphere '{name}'...")

    safe_name = sanitize_name(name)
    script = f"""
import FreeCAD
import Part
import json
result_json = ''
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    sph = doc.addObject("Part::Sphere", "{safe_name}")
    sph.Radius = float({radius})
    sph.Placement.Base.x = float({position_x})
    sph.Placement.Base.y = float({position_y})
    sph.Placement.Base.z = float({position_z})
    doc.recompute()
    result_json = json.dumps({{"object_name": sph.Name, "type": "Sphere"}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        await ctx.send_progress(0.3, "Executing sphere creation script...")
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        if not result_json_str:
            raise FastMCPError("Did not receive result from FreeCAD script")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
            raise FastMCPError(
                f"Error creating sphere in FreeCAD: {result_data['error']}"
            )

        created_name = result_data.get("object_name")
        await ctx.send_progress(1.0, "Sphere created successfully")
        return {
            "object_name": created_name,
            "type": "Sphere",
            "message": f"Successfully created sphere '{created_name}'",
            "success": True,
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode sphere creation result")
        await ctx.send_progress(1.0, "Failed to parse response")
        raise FastMCPError("Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error creating sphere: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Error: {str(e)}")
        if not isinstance(e, FastMCPError):
            raise FastMCPError(f"Error creating sphere: {str(e)}")
        else:
            raise e


@mcp.tool()
async def freecad_create_cone(
    radius1: float,
    height: float,
    radius2: float = 0.0,  # Top radius defaults to 0 for a pointed cone
    name: str = "Cone",
    position_x: float = 0.0,
    position_y: float = 0.0,
    position_z: float = 0.0,
) -> Dict[str, Any]:
    """Create a cone primitive."""
    logger.info(f"Executing freecad.create_cone: {name}")
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, f"Creating cone '{name}'...")

    safe_name = sanitize_name(name)
    script = f"""
import FreeCAD
import Part
import json
result_json = ''
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    cone = doc.addObject("Part::Cone", "{safe_name}")
    cone.Radius1 = float({radius1})
    cone.Radius2 = float({radius2})
    cone.Height = float({height})
    cone.Placement.Base.x = float({position_x})
    cone.Placement.Base.y = float({position_y})
    cone.Placement.Base.z = float({position_z})
    doc.recompute()
    result_json = json.dumps({{"object_name": cone.Name, "type": "Cone"}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        await ctx.send_progress(0.3, "Executing cone creation script...")
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        if not result_json_str:
            raise FastMCPError("Did not receive result from FreeCAD script")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
            raise FastMCPError(
                f"Error creating cone in FreeCAD: {result_data['error']}"
            )

        created_name = result_data.get("object_name")
        await ctx.send_progress(1.0, "Cone created successfully")
        return {
            "object_name": created_name,
            "type": "Cone",
            "message": f"Successfully created cone '{created_name}'",
            "success": True,
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode cone creation result")
        await ctx.send_progress(1.0, "Failed to parse response")
        raise FastMCPError("Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error creating cone: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Error: {str(e)}")
        if not isinstance(e, FastMCPError):
            raise FastMCPError(f"Error creating cone: {str(e)}")
        else:
            raise e


# == Part Boolean Operation Tools ==
@mcp.tool()
async def freecad_boolean_union(
    object1: str, object2: str, name: str = "Union"
) -> Dict[str, Any]:
    """Perform a boolean union (fuse) between two objects."""
    logger.info(f"Executing freecad.boolean_union: {object1} + {object2} -> {name}")
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, "Starting boolean union...")

    safe_obj1_name = sanitize_name(object1)
    safe_obj2_name = sanitize_name(object2)
    safe_result_name = sanitize_name(name)

    script = f"""
import FreeCAD
import Part
import json
result_json = ''
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    obj1 = doc.getObject("{safe_obj1_name}")
    obj2 = doc.getObject("{safe_obj2_name}")
    if not obj1: raise Exception(f"Object '{object1}' not found")
    if not obj2: raise Exception(f"Object '{object2}' not found")

    union = doc.addObject("Part::Fuse", "{safe_result_name}")
    union.Base = obj1
    union.Tool = obj2
    # Hide original objects after operation? Optional.
    # obj1.ViewObject.Visibility = False
    # obj2.ViewObject.Visibility = False
    doc.recompute()
    if union.Shape.isNull():
         raise Exception("Boolean operation resulted in empty shape.")
    result_json = json.dumps({{"object_name": union.Name, "type": "Union"}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        await ctx.send_progress(0.3, "Executing boolean union script...")
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        if not result_json_str:
            raise FastMCPError("Did not receive result from FreeCAD script")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
            await ctx.send_progress(
                1.0, f"Union operation failed: {result_data['error']}"
            )
            raise FastMCPError(
                f"Error creating union in FreeCAD: {result_data['error']}"
            )

        created_name = result_data.get("object_name")
        await ctx.send_progress(1.0, "Union completed successfully")
        return {
            "object_name": created_name,
            "type": "Union",
            "message": f"Successfully created union '{created_name}' from '{object1}' and '{object2}'",
            "success": True,
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode union result")
        await ctx.send_progress(1.0, "Failed to parse response from FreeCAD")
        raise FastMCPError("Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error performing boolean union: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Union operation error: {str(e)}")
        if not isinstance(e, FastMCPError):
            raise FastMCPError(f"Error creating union: {str(e)}")
        else:
            raise e


@mcp.tool()
async def freecad_boolean_cut(
    object1: str, object2: str, name: str = "Cut"
) -> Dict[str, Any]:
    """Perform a boolean cut (difference) between two objects (object1 - object2)."""
    logger.info(f"Executing freecad.boolean_cut: {object1} - {object2} -> {name}")
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, "Starting boolean cut...")

    safe_obj1_name = sanitize_name(object1)
    safe_obj2_name = sanitize_name(object2)
    safe_result_name = sanitize_name(name)

    script = f"""
import FreeCAD
import Part
import json
result_json = ''
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    obj1 = doc.getObject("{safe_obj1_name}") # Base object
    obj2 = doc.getObject("{safe_obj2_name}") # Tool object to subtract
    if not obj1: raise Exception(f"Object '{object1}' not found")
    if not obj2: raise Exception(f"Object '{object2}' not found")

    cut = doc.addObject("Part::Cut", "{safe_result_name}")
    cut.Base = obj1
    cut.Tool = obj2
    # Hide original objects? Optional.
    # obj1.ViewObject.Visibility = False
    # obj2.ViewObject.Visibility = False
    doc.recompute()
    if cut.Shape.isNull():
         raise Exception("Boolean operation resulted in empty shape.")
    result_json = json.dumps({{"object_name": cut.Name, "type": "Cut"}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        await ctx.send_progress(0.3, "Executing boolean cut script...")
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        if not result_json_str:
            raise FastMCPError("Did not receive result from FreeCAD script")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
            await ctx.send_progress(
                1.0, f"Cut operation failed: {result_data['error']}"
            )
            raise FastMCPError(f"Error creating cut in FreeCAD: {result_data['error']}")

        created_name = result_data.get("object_name")
        await ctx.send_progress(1.0, "Cut completed successfully")
        return {
            "object_name": created_name,
            "type": "Cut",
            "message": f"Successfully created cut '{created_name}' ({object1} - {object2})",
            "success": True,
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode cut result")
        await ctx.send_progress(1.0, "Failed to parse response")
        raise FastMCPError("Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error performing boolean cut: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Cut operation error: {str(e)}")
        if not isinstance(e, FastMCPError):
            raise FastMCPError(f"Error creating cut: {str(e)}")
        else:
            raise e


@mcp.tool()
async def freecad_boolean_intersection(
    object1: str, object2: str, name: str = "Intersection"
) -> Dict[str, Any]:
    """Perform a boolean intersection (common) between two objects."""
    logger.info(
        f"Executing freecad.boolean_intersection: {object1} & {object2} -> {name}"
    )
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, "Starting boolean intersection...")

    safe_obj1_name = sanitize_name(object1)
    safe_obj2_name = sanitize_name(object2)
    safe_result_name = sanitize_name(name)

    script = f"""
import FreeCAD
import Part
import json
result_json = ''
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    obj1 = doc.getObject("{safe_obj1_name}")
    obj2 = doc.getObject("{safe_obj2_name}")
    if not obj1: raise Exception(f"Object '{object1}' not found")
    if not obj2: raise Exception(f"Object '{object2}' not found")

    common = doc.addObject("Part::Common", "{safe_result_name}")
    common.Shapes = [obj1, obj2] # Intersection takes a list of shapes
    # Hide original objects? Optional.
    # obj1.ViewObject.Visibility = False
    # obj2.ViewObject.Visibility = False
    doc.recompute()
    if common.Shape.isNull():
         raise Exception("Boolean operation resulted in empty shape.")
    result_json = json.dumps({{"object_name": common.Name, "type": "Intersection"}})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        await ctx.send_progress(0.3, "Executing boolean intersection script...")
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        if not result_json_str:
            raise FastMCPError("Did not receive result from FreeCAD script")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
            await ctx.send_progress(
                1.0, f"Intersection operation failed: {result_data['error']}"
            )
            raise FastMCPError(
                f"Error creating intersection in FreeCAD: {result_data['error']}"
            )

        created_name = result_data.get("object_name")
        await ctx.send_progress(1.0, "Intersection completed successfully")
        return {
            "object_name": created_name,
            "type": "Intersection",
            "message": f"Successfully created intersection '{created_name}' between '{object1}' and '{object2}'",
            "success": True,
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode intersection result")
        await ctx.send_progress(1.0, "Failed to parse response")
        raise FastMCPError("Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error performing boolean intersection: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Intersection operation error: {str(e)}")
        if not isinstance(e, FastMCPError):
            raise FastMCPError(f"Error creating intersection: {str(e)}")
        else:
            raise e


# == FreeCAD Object Manipulation Tools ==
@mcp.tool()
async def freecad_move_object(
    object_name: str,
    x: Optional[float] = None,
    y: Optional[float] = None,
    z: Optional[float] = None,
) -> Dict[str, Any]:
    """Move an object to a new absolute position. Specify at least one coordinate."""
    if x is None and y is None and z is None:
        raise FastMCPError(
            "At least one coordinate (x, y, or z) must be provided for move_object"
        )

    logger.info(
        f"Executing freecad.move_object: {object_name} to (x={x}, y={y}, z={z})"
    )
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, "Starting object move...")

    safe_obj_name = sanitize_name(object_name)
    # Construct parts of the placement update based on provided args
    updates = []
    if x is not None:
        updates.append(f"obj.Placement.Base.x = float({x})")
    if y is not None:
        updates.append(f"obj.Placement.Base.y = float({y})")
    if z is not None:
        updates.append(f"obj.Placement.Base.z = float({z})")
    update_str = "\\n    ".join(updates)

    script = f"""
import FreeCAD
import json
result_json = ''
try:
    doc = FreeCAD.ActiveDocument
    if not doc: raise Exception("No active document")
    obj = doc.getObject("{safe_obj_name}")
    if not obj: raise Exception(f"Object '{object_name}' not found")

    # Apply updates
    {update_str}

    doc.recompute()
    # Report final position
    final_pos = obj.Placement.Base
    result_json = json.dumps({{
        "final_x": final_pos.x,
        "final_y": final_pos.y,
        "final_z": final_pos.z
    }})
except Exception as e:
    result_json = json.dumps({{"error": str(e)}})
"""
    try:
        await ctx.send_progress(0.3, "Executing move script...")
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        if not result_json_str:
            raise FastMCPError("Did not receive result from FreeCAD script")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
            await ctx.send_progress(
                1.0, f"Move operation failed: {result_data['error']}"
            )
            raise FastMCPError(
                f"Error moving object in FreeCAD: {result_data['error']}"
            )

        final_pos = result_data  # Should contain x, y, z
        await ctx.send_progress(1.0, "Move completed successfully")
        return {
            "object_name": object_name,
            "final_position": final_pos,
            "message": f"Successfully moved object '{object_name}' to ({final_pos.get('x',0):.2f}, {final_pos.get('y',0):.2f}, {final_pos.get('z',0):.2f})",
            "success": True,
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode move result")
        await ctx.send_progress(1.0, "Failed to parse response")
        raise FastMCPError("Failed to parse response from FreeCAD")
    except Exception as e:
        logger.error(f"Error moving object: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Move error: {str(e)}")
        if not isinstance(e, FastMCPError):
            raise FastMCPError(f"Error moving object: {str(e)}")
        else:
            raise e


@mcp.tool()
async def freecad_rotate_object(
    object_name: str, angle_x: float = 0.0, angle_y: float = 0.0, angle_z: float = 0.0
) -> Dict[str, Any]:
    """Rotate an object by specified angles around its placement base point (XYZ order)."""
    logger.info(
        f"Executing freecad.rotate_object: {object_name} by (x={angle_x}, y={angle_y}, z={angle_z})"
    )

    ctx = ToolContext.get()
    await ctx.send_progress(0.1, "Starting object rotation...")

    safe_obj_name = sanitize_name(object_name)

    script = f"""
import FreeCAD
import Part
import math
import json

final_rot_x = 0.0; final_rot_y = 0.0; final_rot_z = 0.0 # Store result
result_json = ''
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
    # Rotation applied relative to Base
    new_placement = FreeCAD.Placement(current_placement.Base, new_rotation)
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

    await ctx.send_progress(0.3, "Executing rotation script...")
    try:
        env_data = await execute_script_in_freecad(script, ["result_json"])
        result_json_str = env_data.get("result_json")
        if not result_json_str:
            raise FastMCPError("Did not receive result from FreeCAD script")
        result_data = json.loads(result_json_str)

        if isinstance(result_data, dict) and "error" in result_data:
            raise FastMCPError(
                f"Error rotating object in FreeCAD: {result_data['error']}"
            )

        applied = {
            k.split("_")[1]: v
            for k, v in result_data.items()
            if k.startswith("applied_")
        }
        final = {
            k.split("_")[1]: v for k, v in result_data.items() if k.startswith("final_")
        }  # Include final angles

        await ctx.send_progress(1.0, "Rotation completed successfully")
        return {
            "object_name": object_name,
            "rotation_applied": applied,
            "final_rotation_euler_zyx": final,  # Return final calculated angles
            "message": f"Applied rotation ({applied.get('x', 0.0):.1f}, {applied.get('y', 0.0):.1f}, {applied.get('z', 0.0):.1f}) degrees to object '{object_name}'",
            "success": True,
        }
    except json.JSONDecodeError:
        logger.error("Failed to decode rotation result")
        await ctx.send_progress(1.0, "Failed to parse response from FreeCAD")
        raise FastMCPError("Failed to parse response from FreeCAD")
    except FastMCPError:  # Catch specific error type
        raise
    except Exception as e:
        logger.error(f"Error rotating object: {e}", exc_info=True)
        await ctx.send_progress(1.0, f"Rotation error: {str(e)}")
        raise FastMCPError(f"Error rotating object: {str(e)}")


# == FreeCAD Export Tools ==


@mcp.tool()
async def freecad_export_stl(
    file_path: str, objects: Optional[List[str]] = None, document: Optional[str] = None
) -> Dict[str, Any]:
    """Export specified objects (or all if none specified) from a document to an STL file."""
    logger.info(
        f"Executing freecad.export_stl to: {file_path} (Objects: {objects}, Doc: {document})"
    )

    # Get the ToolContext for progress reporting
    ctx = ToolContext.get()
    await ctx.send_progress(0.1, "Starting STL export...")

    # Basic path validation
    safe_file_path = sanitize_path(file_path)
    if not safe_file_path.lower().endswith(".stl"):
        raise FastMCPError("Invalid file_path. Must end with .stl")

    # Ensure objects is a list of strings if provided
    if objects is not None and (
        not isinstance(objects, list) or not all(isinstance(o, str) for o in objects)
    ):
        raise FastMCPError("Parameter 'objects' must be a list of strings.")

    await ctx.send_progress(0.2, "Validating export parameters...")

    # Use direct API call if available and seems robust enough
    if FC_CONNECTION and hasattr(FC_CONNECTION, "export_stl"):
        try:
            await ctx.send_progress(0.3, "Using direct export method...")
            success = FC_CONNECTION.export_stl(
                object_names=objects, file_path=safe_file_path, document=document
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
                await ctx.send_progress(1.0, "Export failed")
                raise FastMCPError("FreeCADConnection.export_stl returned False.")
        except Exception as e:
            logger.error(f"Error during direct export_stl call: {e}", exc_info=True)
            await ctx.send_progress(1.0, f"Export error: {str(e)}")
            raise FastMCPError(f"Failed to export STL (direct call): {str(e)}")
    else:
        # Fallback to script execution
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
import Mesh # Use Mesh module for STL export
import json

success = False
error_msg = ''
result_json = ''
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
        # Export all visible objects with a Shape if no specific list given
        obj_list_to_export = [o for o in doc.Objects if hasattr(o, 'Shape') and getattr(o.ViewObject, 'Visibility', False)]
    else:
        for name in export_obj_names:
            obj = doc.getObject(name)
            if obj and hasattr(obj, 'Shape'):
                obj_list_to_export.append(obj)
            else:
                raise Exception(f"Object '{{name}}' not found or is not exportable.")

    if not obj_list_to_export:
        raise Exception("No valid objects found to export.")

    # Mesh.export expects list of objects
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
            if not result_json_str:
                raise FastMCPError("Did not receive result from FreeCAD export script")
            result_data = json.loads(result_json_str)

            if result_data.get("error"):
                await ctx.send_progress(1.0, f"Export failed: {result_data['error']}")
                raise FastMCPError(
                    f"Error exporting STL in FreeCAD: {result_data['error']}"
                )

            if result_data.get("success"):
                await ctx.send_progress(1.0, "Export completed successfully")
                return {
                    "file_path": safe_file_path,
                    "message": f"Exported {'selected objects' if objects else 'model'} to {safe_file_path} (via script)",
                    "success": True,
                }
            else:
                await ctx.send_progress(1.0, "Export failed silently")
                raise FastMCPError("STL export script failed silently.")

        except json.JSONDecodeError:
            logger.error("Failed to decode export result")
            await ctx.send_progress(1.0, "Failed to parse response from FreeCAD")
            raise FastMCPError("Failed to parse response from FreeCAD")
        except Exception as e:
            logger.error(f"Error exporting STL (script fallback): {e}", exc_info=True)
            await ctx.send_progress(1.0, f"Export error: {str(e)}")
            if not isinstance(e, FastMCPError):
                raise FastMCPError(f"Error exporting STL: {str(e)}")
            else:
                raise e


# --- Resource Definitions ---


@mcp.resource("freecad://info")
async def get_freecad_info() -> Dict[str, Any]:
    """Get information about the connected FreeCAD instance."""
    logger.info("Executing get_freecad_info resource")
    if not FC_CONNECTION or not FC_CONNECTION.is_connected():
        return {"status": "error", "message": "Not currently connected to FreeCAD."}

    try:
        version_info = FC_CONNECTION.get_version()
        version_str = ".".join(str(v) for v in version_info.get("version", ["Unknown"]))
        connection_type = FC_CONNECTION.get_connection_type()
        return {
            "status": "success",
            "freecad_version": version_str,
            "connection_type": connection_type,
        }
    except Exception as e:
        logger.error(f"Error getting FreeCAD info: {e}")
        return {
            "status": "error",
            "message": f"Error retrieving FreeCAD info: {str(e)}",
        }


@mcp.resource("server://info")
async def get_server_info() -> Dict[str, Any]:
    """
    Get comprehensive information about the MCP server.

    Returns information about the server version, capabilities,
    FreeCAD connection status, and available tools/resources.

    This resource is useful for clients to understand what functionality
    is available and the current state of the server.
    """
    logger.info("Executing get_server_info resource")

    # Get server version and name
    server_info = {
        "name": server_name,
        "version": VERSION,
        "freecad_connection": {
            "connected": FC_CONNECTION is not None and FC_CONNECTION.is_connected(),
            "connection_type": (
                FC_CONNECTION.get_connection_type()
                if FC_CONNECTION and FC_CONNECTION.is_connected()
                else "none"
            ),
        },
        "capabilities": {
            "tools": {
                "document_management": True,
                "primitives": CONFIG.get("tools", {}).get("enable_primitives", True),
                "sketcher": CONFIG.get("tools", {}).get("enable_sketcher", True),
                "constraints": CONFIG.get("tools", {}).get("enable_constraints", True),
                "measurements": CONFIG.get("tools", {}).get(
                    "enable_measurements", True
                ),
                "boolean_operations": True,
                "transformations": True,
                "export": True,
            },
            "resources": {"freecad_info": True, "server_info": True},
        },
        "runtime": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
        },
    }

    # Add FreeCAD version info if connected
    if FC_CONNECTION and FC_CONNECTION.is_connected():
        try:
            version_info = FC_CONNECTION.get_version()
            version_str = ".".join(
                str(v) for v in version_info.get("version", ["Unknown"])
            )
            server_info["freecad_connection"]["version"] = version_str
        except Exception as e:
            logger.warning(f"Could not retrieve FreeCAD version for server info: {e}")
            server_info["freecad_connection"]["version"] = "unknown"

    # Get available tools by inspecting global namespace for mcp.tool decorators
    # This is a simplification - in a real implementation you might want to
    # dynamically discover all tool functions
    tools = []
    for name, value in globals().items():
        if name.startswith("freecad_") and callable(value):
            tools.append(name)

    server_info["available_tools"] = tools

    return server_info


# --- Main Execution ---
async def main():
    """Main entry point for the server."""
    global CONFIG, FC_CONNECTION

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Advanced FreeCAD MCP Server")
    parser.add_argument(
        "--config", default=CONFIG_PATH, help="Path to configuration file"
    )
    parser.add_argument(
        "--log-host", default="localhost", help="Host for the logging socket receiver"
    )
    parser.add_argument(
        "--log-port",
        type=int,
        default=LOGGING_PORT,
        help="Port for the logging socket receiver",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--version", action="store_true", help="Show server version and exit"
    )
    args = parser.parse_args()

    # --- Version Info ---
    if args.version:
        print(f"MCP-FreeCAD Server v{VERSION}")
        return

    # --- Setup Logging ---
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # --- Check MCP Dependency ---
    if mcp_import_error:
        logger.error(
            f"ERROR: FastMCP SDK (fastmcp package) not found or import failed: {mcp_import_error}"
        )
        logger.error("Please install it with: pip install fastmcp")
        sys.exit(1)

    # --- Load Configuration ---
    CONFIG = load_config(args.config)
    if args.host:
        CONFIG.setdefault("freecad", {})["host"] = args.host
    if args.port:
        CONFIG.setdefault("freecad", {})["port"] = args.port

    # --- Initialize FreeCAD Connection (Initial Attempt) ---
    initialize_freecad_connection(CONFIG)

    # --- Logging Receiver Setup ---
    log_receiver = None
    try:
        log_receiver = LogRecordSocketReceiver(host=args.log_host, port=args.log_port)
        receiver_thread = threading.Thread(
            target=log_receiver.serve_until_stopped, daemon=True
        )
        receiver_thread.start()
        logger.info(f"Logging receiver started on {args.log_host}:{args.log_port}")

        # Optional: Add a SocketHandler to the server's own logger
        # to route its logs through the receiver as well. This ensures
        # all logs (local and remote) are handled identically.
        # root_logger = logging.getLogger()
        # socket_handler = logging.handlers.SocketHandler(args.log_host, args.log_port)
        # root_logger.addHandler(socket_handler)
        # logger.info("Server's own logs also routed to socket receiver.")

    except Exception as e:
        logger.error(f"Failed to start logging receiver: {e}")
        # Decide if this is fatal or not
        # return 1 # Example: Exit if logging receiver fails

    # --- Background Connection Check ---
    # Only start if FreeCAD features are desired/possible
    connection_check_task = None
    if FREECAD_CONNECTION_AVAILABLE:
        connection_check_task = asyncio.create_task(connection_check_loop(CONFIG))
    else:
        logger.info(
            "Skipping background connection check as FreeCAD connection is unavailable."
        )

    # --- Register Progress Callback ---
    # Example: Registering a simple progress callback for stdout
    async def local_progress_callback(progress_value, message=None):
        if message:
            logger.info(f"Progress: {progress_value*100:.1f}% - {message}")
        else:
            logger.info(f"Progress: {progress_value*100:.1f}%")

    tool_context = ToolContext.get()
    # Prefer FastMCP's built-in progress if available and setup
    # This assumes FastMCP provides a mechanism to register a progress handler,
    # which might need adjustment based on the actual FastMCP version/API.
    # If FastMCP uses ToolContext directly, this might be redundant.
    # For now, setting it on our ToolContext instance.
    tool_context.set_progress_callback(
        local_progress_callback
    )  # Use local console logger for progress

    # --- Start Server ---
    logger.info(f"Starting MCP server '{server_name}' v{VERSION}...")
    # Pass unknown arguments if necessary, depending on FastMCP's run method
    try:
        # Note: Check FastMCP documentation for how to pass extra args if needed
        await mcp.run_stdio()  # Or run_tcp, run_ws depending on desired transport
    except KeyboardInterrupt:
        logger.info("Server shutting down (KeyboardInterrupt)...")
    except Exception as e:
        logger.error(f"Server exited with error: {e}", exc_info=True)  # Log stack trace
    finally:
        logger.info("Performing cleanup...")
        # --- Cleanup ---
        if connection_check_task:
            connection_check_task.cancel()
            try:
                await connection_check_task
            except asyncio.CancelledError:
                logger.info("Background connection check task cancelled.")

        if FC_CONNECTION and FC_CONNECTION.is_connected():
            logger.info("Closing FreeCAD connection...")
            FC_CONNECTION.close()

        if log_receiver:
            logger.info("Shutting down logging receiver...")
            log_receiver.abort = 1
            # receiver_thread.join() # Wait for thread to finish

        logger.info("Server shutdown complete.")


if __name__ == "__main__":
    # Check if FastMCP was imported successfully
    if mcp_import_error:
        sys.stderr.write(
            f"Fatal Error: Failed to import FastMCP - {mcp_import_error}\n"
        )
        sys.stderr.write(
            "Please ensure FastMCP is installed correctly ('pip install fastmcp').\n"
        )
        sys.exit(1)

    # Run the main async function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Already handled in main's finally block, but catch here too for clean exit
        logger.info("Server shutdown initiated by KeyboardInterrupt.")
    except Exception as e:
        logger.critical(f"Unhandled exception in main execution: {e}", exc_info=True)
        sys.exit(1)
