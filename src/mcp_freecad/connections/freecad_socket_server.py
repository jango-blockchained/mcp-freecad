#!/usr/bin/env python3
"""
FreeCAD Server

This script provides a socket-based interface to FreeCAD for use with external
applications, particularly the MCP server.

Usage:
Run from within FreeCAD's Python console: exec(open('freecad_socket_server.py').read())
Run directly with Python: python3 freecad_socket_server.py

Options:
--host HOST     Hostname or IP to listen on (default: localhost)
--port PORT     Port to listen on (default: 12345)
--debug         Enable verbose debug logging
--config PATH   Path to configuration file
--connect       Connect to a running FreeCAD instance
"""

import argparse
import json
import logging
import os
import signal
import socket
import sys
import traceback
from typing import Any, Dict, List, Optional, Tuple

# Parse command-line arguments
parser = argparse.ArgumentParser(description="FreeCAD socket server")
parser.add_argument(
    "--host",
    default="localhost",
    help="Hostname or IP to listen on (default: localhost)",
)
parser.add_argument(
    "--port", type=int, default=12345, help="Port to listen on (default: 12345)"
)
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
parser.add_argument(
    "--config", default="config.json", help="Path to configuration file"
)
parser.add_argument(
    "--connect",
    action="store_true",
    help="Connect to running FreeCAD instead of starting a new instance",
)

args = parser.parse_args()

# Initialize logging
logging.basicConfig(
    level=logging.DEBUG if args.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("freecad_server")

# Load configuration
config_path = args.config
freecad_config = {}
try:
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
            freecad_config = config.get("freecad", {})
            logger.debug(f"Loaded configuration from {config_path}")
    else:
        logger.debug(f"Configuration file {config_path} not found, using defaults")
except Exception as e:
    logger.error(f"Error loading configuration: {e}")

# Try to import FreeCAD
if args.connect:
    print("Running in connect mode - will try to connect to a running FreeCAD instance")

# Load FreeCAD module
try:
    # Try to add FreeCAD module path from config if provided
    freecad_module_path = freecad_config.get("freecad_module_path")
    if freecad_module_path:
        print(f"Using module path from config: {freecad_module_path}")
        sys.path.append(freecad_module_path)
    else:
        # Try standard FreeCAD paths
        print("Using standard FreeCAD paths")
        standard_paths = [
            "/usr/lib/freecad/lib",  # Linux
            "/usr/local/lib/freecad/lib",  # Linux (alternative)
            "/Applications/FreeCAD.app/Contents/lib",  # macOS
            "C:/Program Files/FreeCAD/lib",  # Windows
            "./squashfs-root/usr/lib/",  # Linux AppImage
        ]
        for path in standard_paths:
            if os.path.exists(path):
                sys.path.append(path)

    # Print current Python path for debugging
    print(f"Current Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")

    # Try to import FreeCAD
    import FreeCAD

    # Verify that FreeCAD is properly imported
    if not hasattr(FreeCAD, "Version"):
        raise ImportError("FreeCAD module imported but appears incomplete.")

    # Convert Version to string properly, handling different possible types
    version_str = ""
    try:
        if isinstance(FreeCAD.Version, (list, tuple)):
            version_str = ".".join(str(v) for v in FreeCAD.Version)
        else:
            version_str = str(FreeCAD.Version)
    except Exception as e:
        version_str = f"Unknown (error: {e})"

    print(f"Loaded FreeCAD {version_str}")

    # Try to import FreeCADGui
    try:
        import FreeCADGui

        print("FreeCADGui module available.")
    except ImportError:
        print("FreeCADGui module not available. GUI operations will not be possible.")
        FreeCADGui = None

except ImportError as e:
    print(f"ERROR: Failed to import FreeCAD module: {e}")
    print("This server requires a valid FreeCAD installation accessible in PYTHONPATH.")
    print("Please install FreeCAD or correct your Python path settings.")
    sys.exit(1)


# Server implementation
class FreeCADServer:
    def __init__(self, host="localhost", port=12345, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.socket = None
        self.running = False

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Handle termination signals"""
        if sig in (signal.SIGINT, signal.SIGTERM):
            logger.info("Received termination signal. Shutting down...")
            self.stop()
            sys.exit(0)

    def start(self):
        """Start the server"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow reusing the address
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True

            connect_mode = "connect" if args.connect else "standalone"
            print(
                f"Starting FreeCAD server on {self.host}:{self.port} in {connect_mode} mode"
            )

            # Handle clients
            while self.running:
                try:
                    client_socket, client_address = self.socket.accept()
                    self.handle_client(client_socket, client_address)
                except socket.timeout:
                    continue
                except OSError as e:
                    # Socket was closed by another thread
                    if not self.running:
                        break
                    logger.error(f"Socket error: {e}")

        except Exception as e:
            logger.error(f"Server error: {e}")
            if self.debug:
                traceback.print_exc()
        finally:
            self.stop()

    def stop(self):
        """Stop the server"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {e}")

    def handle_client(self, client_socket, address):
        """Handle client connection"""
        try:
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b"\n" in data:
                    break

            if not data:
                return

            # Parse the command
            command_str = data.decode().strip()
            try:
                command = json.loads(command_str)
            except json.JSONDecodeError:
                self.send_response(
                    client_socket, {"error": "Invalid JSON command format"}
                )
                return

            if self.debug:
                logger.debug(f"Received command: {command}")

            # Process the command
            response = self.process_command(command)

            # Send the response
            self.send_response(client_socket, response)

        except Exception as e:
            logger.error(f"Error handling client: {e}")
            if self.debug:
                traceback.print_exc()
            self.send_response(client_socket, {"error": str(e)})
        finally:
            client_socket.close()

    def send_response(self, client_socket, response):
        """Send response to client"""
        try:
            response_str = json.dumps(response)
            client_socket.sendall((response_str + "\n").encode())
        except Exception as e:
            logger.error(f"Error sending response: {e}")

    def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process a command and return a response"""
        command_type = command.get("type", "")
        params = command.get("params", {})

        # Built-in commands
        if command_type == "ping":
            return {"pong": True}

        elif command_type == "get_version":
            version_info = {}

            # Handle different Version formats
            try:
                if isinstance(FreeCAD.Version, (list, tuple)):
                    version_info["version"] = [str(v) for v in FreeCAD.Version]
                else:
                    version_info["version"] = [str(FreeCAD.Version)]
            except Exception:
                version_info["version"] = ["Unknown"]

            # Handle different BuildDate formats
            try:
                version_info["build_date"] = str(getattr(FreeCAD, "BuildDate", "N/A"))
            except Exception:
                version_info["build_date"] = "Unknown"

            return version_info

        # Document management
        elif command_type == "create_document":
            name = params.get("name", "Unnamed")
            doc = FreeCAD.newDocument(name)
            return {
                "success": True,
                "document": {"name": doc.Name, "label": doc.Label},
            }

        elif command_type == "close_document":
            name = params.get("name")
            if name:
                FreeCAD.closeDocument(name)
                return {"success": True}
            return {"error": "Document name not specified"}

        elif command_type == "get_active_document":
            if FreeCAD.ActiveDocument:
                return {
                    "document": {
                        "name": FreeCAD.ActiveDocument.Name,
                        "label": FreeCAD.ActiveDocument.Label,
                    }
                }
            return {"error": "No active document"}

        elif command_type == "list_documents":
            docs = []
            for doc in FreeCAD.listDocuments().values():
                docs.append({"name": doc.Name, "label": doc.Label})
            return {"documents": docs}

        # Object creation and manipulation
        elif command_type == "create_object":
            obj_type = params.get("type", "")
            doc_name = params.get("document", None)
            name = params.get("name", None)
            properties = params.get("properties", {})

            # Get the document to work with
            doc = None
            if doc_name:
                docs = FreeCAD.listDocuments()
                if doc_name in docs:
                    doc = docs[doc_name]
                else:
                    return {"error": f"Document '{doc_name}' not found"}
            else:
                if FreeCAD.ActiveDocument:
                    doc = FreeCAD.ActiveDocument
                else:
                    return {"error": "No active document and no document specified"}

            # Create the object based on type
            try:
                if obj_type == "box":
                    # Get parameters
                    length = properties.get("length", 10.0)
                    width = properties.get("width", 10.0)
                    height = properties.get("height", 10.0)

                    # Create the object
                    box = doc.addObject("Part::Box", name or "Box")
                    box.Length = length
                    box.Width = width
                    box.Height = height
                    doc.recompute()

                    return {
                        "success": True,
                        "object": {"name": box.Name, "type": box.TypeId},
                    }

                elif obj_type == "cylinder":
                    # Get parameters
                    radius = properties.get("radius", 5.0)
                    height = properties.get("height", 10.0)

                    # Create the object
                    cylinder = doc.addObject("Part::Cylinder", name or "Cylinder")
                    cylinder.Radius = radius
                    cylinder.Height = height
                    doc.recompute()

                    return {
                        "success": True,
                        "object": {"name": cylinder.Name, "type": cylinder.TypeId},
                    }

                else:
                    return {"error": f"Unsupported object type: {obj_type}"}
            except Exception as e:
                return {"error": f"Error creating object: {str(e)}"}

        # Object listing and information
        elif command_type == "list_objects":
            doc_name = params.get("document", None)

            # Get the document to work with
            doc = None
            if doc_name:
                docs = FreeCAD.listDocuments()
                if doc_name in docs:
                    doc = docs[doc_name]
                else:
                    return {"error": f"Document '{doc_name}' not found"}
            else:
                if FreeCAD.ActiveDocument:
                    doc = FreeCAD.ActiveDocument
                else:
                    return {"error": "No active document and no document specified"}

            # List objects
            objects = []
            for obj in doc.Objects:
                objects.append(
                    {
                        "name": obj.Name,
                        "label": obj.Label,
                        "type": obj.TypeId,
                        "visible": (
                            obj.ViewObject.Visibility
                            if hasattr(obj, "ViewObject")
                            else True
                        ),
                    }
                )
            return {"objects": objects}

        # Export operations
        elif command_type == "export_document":
            doc_name = params.get("document", None)
            file_path = params.get("path", "")
            objects = params.get("objects", [])
            format = params.get("format", "").lower()  # e.g., "step", "stl"

            if not file_path:
                return {"error": "No file path specified"}

            # Get the document to work with
            doc = None
            if doc_name:
                docs = FreeCAD.listDocuments()
                if doc_name in docs:
                    doc = docs[doc_name]
                else:
                    return {"error": f"Document '{doc_name}' not found"}
            else:
                if FreeCAD.ActiveDocument:
                    doc = FreeCAD.ActiveDocument
                else:
                    return {"error": "No active document and no document specified"}

            # Handle different export formats
            try:
                if format == "step":
                    import Part

                    if objects:
                        shapes = []
                        for obj_name in objects:
                            obj = doc.getObject(obj_name)
                            if obj and hasattr(obj, "Shape"):
                                shapes.append(obj.Shape)

                        if shapes:
                            Part.export(shapes, file_path)
                        else:
                            return {
                                "error": "No valid shapes found in specified objects"
                            }
                    else:
                        # Export all objects with shapes
                        shapes = []
                        for obj in doc.Objects:
                            if hasattr(obj, "Shape"):
                                shapes.append(obj.Shape)

                        if shapes:
                            Part.export(shapes, file_path)
                        else:
                            return {"error": "No valid shapes found in document"}

                elif format == "stl":
                    import Mesh

                    if objects:
                        for obj_name in objects:
                            obj = doc.getObject(obj_name)
                            if obj and hasattr(obj, "Shape"):
                                mesh = Mesh.Mesh(obj.Shape.tessellate(0.1))
                                mesh.write(file_path)
                                break  # Only export the first one for now
                        else:
                            return {
                                "error": "No valid shapes found in specified objects"
                            }
                    else:
                        # Export all objects with shapes
                        for obj in doc.Objects:
                            if hasattr(obj, "Shape"):
                                mesh = Mesh.Mesh(obj.Shape.tessellate(0.1))
                                mesh.write(file_path)
                                break  # Only export the first one for now
                        else:
                            return {"error": "No valid shapes found in document"}

                else:
                    return {"error": f"Unsupported export format: {format}"}

                return {"success": True, "path": file_path}

            except Exception as e:
                return {"error": f"Error exporting document: {str(e)}"}

        # Script execution
        elif command_type == "execute_script":
            script = params.get("script", "")

            if not script:
                return {"error": "No script provided"}

            try:
                # Create a local environment for script execution
                script_env = {"FreeCAD": FreeCAD}

                # Add FreeCADGui if available
                if FreeCADGui:
                    script_env["FreeCADGui"] = FreeCADGui

                # Add return values environment
                script_env["_env_values"] = {}

                # Execute the script
                exec(script, script_env)

                # Return any values that were stored in _env_values
                return {
                    "success": True,
                    "environment": script_env.get("_env_values", {}),
                }

            except Exception as e:
                traceback_info = traceback.format_exc()
                return {"error": str(e), "traceback": traceback_info}

        else:
            return {"error": f"Unknown command: {command_type}"}


# Main function
def main():
    host = args.host
    port = args.port

    # Create and start the server
    server = FreeCADServer(host=host, port=port, debug=args.debug)

    try:
        # If in a GUI context and not being run from the console, run in a thread
        if args.connect and FreeCADGui:
            print("Running in a GUI context, starting server in a thread...")
            import threading

            server_thread = threading.Thread(target=server.start)
            server_thread.daemon = True
            server_thread.start()
            # Keep thread reference to avoid garbage collection
            FreeCAD.ServerThread = server_thread
        else:
            # Run directly in this process
            server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()
    except Exception as e:
        print(f"Error running server: {e}")
        if args.debug:
            traceback.print_exc()


if __name__ == "__main__":
    main()
