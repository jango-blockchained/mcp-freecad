#!/usr/bin/env python3
"""
FreeCAD XML-RPC Server

This script is designed to run inside FreeCAD and provide an XML-RPC interface
for remote control of FreeCAD operations. It creates a server that listens
for XML-RPC requests and executes them within the FreeCAD environment.

Usage:
    Inside FreeCAD Python Console:
    ```
    import sys
    sys.path.append("/path/to/mcp-freecad")
    exec(open("/path/to/mcp-freecad/src/mcp_freecad/client/freecad_rpc_server.py").read())
    ```

    Or if mcp-freecad is installed as a package:
    ```
    from mcp_freecad.client import freecad_rpc_server
    freecad_rpc_server.start_rpc_server()
    ```
"""

import contextlib
import io
import os
import queue
import base64
import tempfile
import threading
import json
from typing import Any, Dict, List, Optional
from xmlrpc.server import SimpleXMLRPCServer

try:
    import FreeCAD
    import FreeCADGui
    from PySide2.QtCore import QTimer
    FREECAD_AVAILABLE = True
except ImportError:
    FREECAD_AVAILABLE = False
    print("FreeCAD modules not available. This script must run inside FreeCAD.")

# Global variables to track server state
rpc_server_thread = None
rpc_server_instance = None

# GUI task queue (for operations that must run in the main thread)
rpc_request_queue = queue.Queue()
rpc_response_queue = queue.Queue()


def process_gui_tasks():
    """Process any pending tasks in the GUI thread queue"""
    if not FREECAD_AVAILABLE:
        return

    while not rpc_request_queue.empty():
        task = rpc_request_queue.get()
        res = task()
        if res is not None:
            rpc_response_queue.put(res)
    QTimer.singleShot(500, process_gui_tasks)


class FreeCADRPC:
    """RPC server implementation for FreeCAD"""

    def ping(self):
        """Test if the server is responsive"""
        return True

    def get_version(self):
        """Get FreeCAD version information"""
        if not FREECAD_AVAILABLE:
            return {"success": False, "error": "FreeCAD not available"}

        try:
            version = FreeCAD.Version()
            return {
                "success": True,
                "version": {
                    "major": version[0],
                    "minor": version[1],
                    "build": version[2],
                    "string": ".".join(version[:3]),
                    "additional": " ".join(version[3:])
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_document(self, name="Unnamed"):
        """Create a new FreeCAD document"""
        if not FREECAD_AVAILABLE:
            return {"success": False, "error": "FreeCAD not available"}

        # This needs to run in the GUI thread
        rpc_request_queue.put(lambda: self._create_document_gui(name))
        res = rpc_response_queue.get()
        if isinstance(res, bool) and res:
            return {"success": True, "document_name": name}
        else:
            return {"success": False, "error": res}

    def _create_document_gui(self, name):
        """Internal method to create document in GUI thread"""
        try:
            doc = FreeCAD.newDocument(name)
            doc.recompute()
            FreeCAD.Console.PrintMessage(f"Document '{name}' created via RPC.\n")
            return True
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error creating document: {e}\n")
            return str(e)

    def create_object(self, doc_name, obj_data):
        """Create a new object in a FreeCAD document

        Args:
            doc_name: Name of the document
            obj_data: Dictionary with object data including:
                      - Name: Object name
                      - Type: Object type (e.g., "Part::Box")
                      - Properties: Dictionary of property values

        Returns:
            Dictionary with success status and object name or error
        """
        if not FREECAD_AVAILABLE:
            return {"success": False, "error": "FreeCAD not available"}

        rpc_request_queue.put(lambda: self._create_object_gui(doc_name, obj_data))
        res = rpc_response_queue.get()
        if isinstance(res, bool) and res:
            return {"success": True, "object_name": obj_data.get("Name", "Unknown")}
        else:
            return {"success": False, "error": res}

    def _create_object_gui(self, doc_name, obj_data):
        """Internal method to create object in GUI thread"""
        try:
            doc = FreeCAD.getDocument(doc_name)
            if not doc:
                return f"Document '{doc_name}' not found"

            obj_type = obj_data.get("Type")
            obj_name = obj_data.get("Name", "Unnamed")
            properties = obj_data.get("Properties", {})

            # Create the object
            obj = doc.addObject(obj_type, obj_name)

            # Set properties
            for prop, value in properties.items():
                if prop in obj.PropertiesList:
                    # Handle special property types
                    if prop == "Placement" and isinstance(value, dict):
                        base = value.get("Base", {})
                        rot = value.get("Rotation", {})
                        placement = FreeCAD.Placement(
                            FreeCAD.Vector(
                                base.get("x", 0),
                                base.get("y", 0),
                                base.get("z", 0)
                            ),
                            FreeCAD.Rotation(
                                FreeCAD.Vector(
                                    rot.get("Axis", {}).get("x", 0),
                                    rot.get("Axis", {}).get("y", 0),
                                    rot.get("Axis", {}).get("z", 1)
                                ),
                                rot.get("Angle", 0)
                            )
                        )
                        setattr(obj, prop, placement)
                    elif prop == "ShapeColor" and isinstance(value, list):
                        obj.ViewObject.ShapeColor = tuple(value)
                    else:
                        setattr(obj, prop, value)

            doc.recompute()
            FreeCAD.Console.PrintMessage(f"Object '{obj_name}' created via RPC.\n")
            return True
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error creating object: {e}\n")
            return str(e)

    def export_stl(self, doc_name, obj_name, file_path):
        """Export an object to STL format

        Args:
            doc_name: Name of the document
            obj_name: Name of the object to export
            file_path: Path where to save the STL file

        Returns:
            Dictionary with success status and file path or error
        """
        if not FREECAD_AVAILABLE:
            return {"success": False, "error": "FreeCAD not available"}

        rpc_request_queue.put(lambda: self._export_stl_gui(doc_name, obj_name, file_path))
        res = rpc_response_queue.get()
        if isinstance(res, bool) and res:
            return {"success": True, "path": file_path}
        else:
            return {"success": False, "error": res}

    def _export_stl_gui(self, doc_name, obj_name, file_path):
        """Internal method to export STL in GUI thread"""
        try:
            doc = FreeCAD.getDocument(doc_name)
            if not doc:
                return f"Document '{doc_name}' not found"

            obj = doc.getObject(obj_name)
            if not obj:
                return f"Object '{obj_name}' not found in document '{doc_name}'"

            import Mesh
            Mesh.export([obj], file_path)
            FreeCAD.Console.PrintMessage(f"Exported '{obj_name}' to '{file_path}'.\n")
            return True
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error exporting to STL: {e}\n")
            return str(e)

    def execute_code(self, code):
        """Execute arbitrary Python code in FreeCAD

        Args:
            code: Python code to execute

        Returns:
            Dictionary with success status and output or error
        """
        if not FREECAD_AVAILABLE:
            return {"success": False, "error": "FreeCAD not available"}

        output_buffer = io.StringIO()

        def execute_task():
            try:
                with contextlib.redirect_stdout(output_buffer):
                    exec(code, globals())
                return True
            except Exception as e:
                FreeCAD.Console.PrintError(f"Error executing Python code: {e}\n")
                return str(e)

        rpc_request_queue.put(execute_task)
        res = rpc_response_queue.get()

        if isinstance(res, bool) and res:
            return {
                "success": True,
                "message": "Code executed successfully",
                "output": output_buffer.getvalue()
            }
        else:
            return {"success": False, "error": res}

    def get_active_screenshot(self, view_name="Isometric"):
        """Get a screenshot of the active view

        Args:
            view_name: Name of the view (Isometric, Front, Top, etc.)

        Returns:
            Base64-encoded PNG image data
        """
        if not FREECAD_AVAILABLE:
            return None

        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        rpc_request_queue.put(lambda: self._save_screenshot_gui(temp_file.name, view_name))
        res = rpc_response_queue.get()

        if isinstance(res, bool) and res:
            with open(temp_file.name, "rb") as image_file:
                image_bytes = image_file.read()
                os.remove(temp_file.name)
                return base64.b64encode(image_bytes).decode("utf-8")
        else:
            return None

    def _save_screenshot_gui(self, save_path, view_name="Isometric"):
        """Internal method to save screenshot in GUI thread"""
        try:
            view = FreeCADGui.ActiveDocument.ActiveView

            # Set view orientation
            if view_name == "Isometric":
                view.viewIsometric()
            elif view_name == "Front":
                view.viewFront()
            elif view_name == "Top":
                view.viewTop()
            elif view_name == "Right":
                view.viewRight()
            elif view_name == "Back":
                view.viewBack()
            elif view_name == "Left":
                view.viewLeft()
            elif view_name == "Bottom":
                view.viewBottom()
            else:
                # Default to isometric for unsupported view names
                view.viewIsometric()

            view.fitAll()
            view.saveImage(save_path, 1920, 1080)
            return True
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error saving screenshot: {e}\n")
            return str(e)


def start_rpc_server(host="localhost", port=9875):
    """Start the XML-RPC server

    Args:
        host: Host address to bind to
        port: Port number to use

    Returns:
        String message about server status
    """
    global rpc_server_thread, rpc_server_instance

    if not FREECAD_AVAILABLE:
        return "Error: FreeCAD modules not available. Cannot start RPC server."

    if rpc_server_instance:
        return "RPC Server already running."

    try:
        # Create server instance
        rpc_server_instance = SimpleXMLRPCServer(
            (host, port), allow_none=True, logRequests=False
        )
        rpc_server_instance.register_instance(FreeCADRPC())

        # Start server in a separate thread
        def server_loop():
            FreeCAD.Console.PrintMessage(f"RPC Server started at {host}:{port}\n")
            rpc_server_instance.serve_forever()

        rpc_server_thread = threading.Thread(target=server_loop, daemon=True)
        rpc_server_thread.start()

        # Start task processing timer
        QTimer.singleShot(500, process_gui_tasks)

        return f"RPC Server started at {host}:{port}"
    except Exception as e:
        return f"Error starting RPC server: {e}"


def stop_rpc_server():
    """Stop the XML-RPC server

    Returns:
        String message about server status
    """
    global rpc_server_instance, rpc_server_thread

    if not rpc_server_instance:
        return "RPC Server not running."

    try:
        rpc_server_instance.shutdown()
        rpc_server_thread.join()
        rpc_server_instance = None
        rpc_server_thread = None
        FreeCAD.Console.PrintMessage("RPC Server stopped.\n")
        return "RPC Server stopped."
    except Exception as e:
        return f"Error stopping RPC server: {e}"


# Auto-start if run directly
if __name__ == "__main__" and FREECAD_AVAILABLE:
    try:
        # Try to register FreeCAD GUI commands for the RPC server
        from PySide2 import QtCore

        class StartRPCServerCommand:
            """FreeCAD command to start the RPC server"""

            def GetResources(self):
                return {
                    "MenuText": "Start RPC Server",
                    "ToolTip": "Start XML-RPC Server for MCP-FreeCAD",
                    "Pixmap": ""
                }

            def Activated(self):
                msg = start_rpc_server()
                FreeCAD.Console.PrintMessage(msg + "\n")

            def IsActive(self):
                return True

        class StopRPCServerCommand:
            """FreeCAD command to stop the RPC server"""

            def GetResources(self):
                return {
                    "MenuText": "Stop RPC Server",
                    "ToolTip": "Stop XML-RPC Server for MCP-FreeCAD",
                    "Pixmap": ""
                }

            def Activated(self):
                msg = stop_rpc_server()
                FreeCAD.Console.PrintMessage(msg + "\n")

            def IsActive(self):
                return True

        # Register the commands
        FreeCADGui.addCommand("MCP_Start_RPC_Server", StartRPCServerCommand())
        FreeCADGui.addCommand("MCP_Stop_RPC_Server", StopRPCServerCommand())

        # Auto-start the server
        start_msg = start_rpc_server()
        FreeCAD.Console.PrintMessage(start_msg + "\n")

    except Exception as e:
        FreeCAD.Console.PrintError(f"Error setting up RPC server commands: {e}\n")
        # Still try to start the server even if GUI commands fail
        start_msg = start_rpc_server()
        FreeCAD.Console.PrintMessage(start_msg + "\n")
