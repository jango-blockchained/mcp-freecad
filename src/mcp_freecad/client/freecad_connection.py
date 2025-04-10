#!/usr/bin/env python3
"""
FreeCAD Connection Manager

This module provides a unified interface for connecting to FreeCAD using either:
1. Socket-based communication with freecad_server.py running inside FreeCAD
2. CLI-based communication using the FreeCAD executable directly

Usage:
    from freecad_connection import FreeCADConnection

    # Create a connection
    fc = FreeCADConnection()

    # Automatically selects the best available connection method
    if fc.is_connected():
        # Get FreeCAD version
        version = fc.get_version()
        print(f"FreeCAD version: {version}")

        # Create a document and objects
        doc_name = fc.create_document("MyDocument")
        box = fc.create_box(length=10, width=20, height=30)
"""

import json
import os
import socket
import sys
from typing import Any, Dict, List, Optional
import logging

# -- Add Repo Root to sys.path --
# Assuming this script is run from src/mcp_freecad/client/
# or the start script cds to repo root
# repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
# if repo_root not in sys.path:
#     sys.path.insert(0, repo_root)
# ------------------------------

# Set up logger for this module
logger = logging.getLogger(__name__)

# --- FreeCADBridge Import Attempt ---
logger.critical("!!! Attempting to import FreeCADBridge !!!") # VERY LOUD LOG
_bridge_import_error_msg = "Unknown import failure" # Renamed variable
BRIDGE_AVAILABLE = False # Default to False
logger.critical(">>> Right before TRY block <<<")
try:
    # Attempt to import FreeCADBridge if FreeCAD is available
    # from src.mcp_freecad.client.freecad_bridge import FreeCADBridge # NEW absolute import
    from freecad_bridge import FreeCADBridge # Direct import

    BRIDGE_AVAILABLE = True
    _bridge_import_error_msg = "" # Reset error message on successful import
    logger.info("Successfully imported FreeCADBridge!")

except BaseException as e:  # Catch BaseException instead of just Exception
    # Log the failure but allow the program to continue without bridge functionality
    _bridge_import_error_msg = f"Failed to import FreeCADBridge: {e}" # Use renamed variable
    # Keep the print for now to confirm fix
    # print(f"!!! EXCEPTION CAUGHT: {type(e).__name__} - {e} !!!")
    logger.warning(_bridge_import_error_msg) # Revert back to logger
    # BRIDGE_AVAILABLE remains False

logger.critical(">>> Immediately after TRY...EXCEPT block <<<")

if not BRIDGE_AVAILABLE:
     logger.error(f"!!! FreeCADBridge NOT available. Last error: {_bridge_import_error_msg} !!!") # Use renamed variable


class FreeCADConnection:
    """
    A unified interface for connecting to FreeCAD using various methods
    """

    CONNECTION_SERVER = "server"
    CONNECTION_BRIDGE = "bridge"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 12345,
        freecad_path: str = "freecad",
        auto_connect: bool = True,
        prefer_method: Optional[str] = None,
    ):
        """
        Initialize the FreeCAD connection

        Args:
            host: Server hostname for socket connection (default: localhost)
            port: Server port for socket connection (default: 12345)
            freecad_path: Path to FreeCAD executable for CLI bridge (default: 'freecad')
            auto_connect: Whether to automatically connect (default: True)
            prefer_method: Preferred connection method (server or bridge)
        """
        self.host = host
        self.port = port
        self.freecad_path = freecad_path
        self.connection_type = None
        self._bridge = None
        self._socket = None

        if auto_connect:
            self.connect(prefer_method)

    def connect(self, prefer_method: Optional[str] = None) -> bool:
        """
        Connect to FreeCAD using the best available method

        Args:
            prefer_method: Preferred connection method (server or bridge)

        Returns:
            bool: True if successfully connected
        """
        # Try connecting in the preferred order
        methods = self._get_connection_methods(prefer_method)

        for method in methods:
            success = False

            if method == self.CONNECTION_SERVER:
                success = self._connect_server()
            elif method == self.CONNECTION_BRIDGE:
                success = self._connect_bridge()

            if success:
                self.connection_type = method
                return True

        # If we got here, all methods failed
        return False

    def _get_connection_methods(self, prefer_method: Optional[str] = None) -> List[str]:
        """
        Get ordered list of connection methods to try.
        FORCED TO BRIDGE ONLY FOR DEBUGGING.

        Args:
            prefer_method: Preferred method (ignored)

        Returns:
            List containing only the bridge method.
        """
        # Force bridge only
        return [self.CONNECTION_BRIDGE]

    def _connect_server(self) -> bool:
        """
        Connect using socket server

        Returns:
            bool: True if successful
        """
        try:
            # Try to ping the server
            response = self._send_server_command({"type": "ping"})
            return response.get("pong", False)
        except Exception:
            return False

    def _connect_bridge(self) -> bool:
        """
        Connect using FreeCAD bridge

        Returns:
            bool: True if successful
        """
        if not BRIDGE_AVAILABLE:
            logger.warning("FreeCADBridge dependency not found. Bridge connection unavailable.")
            return False

        try:
            logger.debug(f"Attempting to initialize FreeCADBridge with path: {self.freecad_path}")
            self._bridge = FreeCADBridge(self.freecad_path)
            is_avail = self._bridge.is_available()
            logger.debug(f"FreeCADBridge.is_available() returned: {is_avail}")
            return is_avail
        except Exception as e:
            logger.error(f"Failed to initialize or check FreeCADBridge: {type(e).__name__} - {e}", exc_info=True)
            return False

    def is_connected(self) -> bool:
        """
        Check if connected to FreeCAD

        Returns:
            bool: True if connected
        """
        return self.connection_type is not None

    def get_connection_type(self) -> Optional[str]:
        """
        Get the current connection type

        Returns:
            str: Connection type (server or bridge)
        """
        return self.connection_type

    def _send_server_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a command to the FreeCAD server

        Args:
            command: Command dictionary

        Returns:
            dict: Response from server
        """
        sock = None  # Define sock outside try for finally block
        try:
            # Create a new socket for each command
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Set a timeout for connection and operations
            sock.settimeout(10.0)
            sock.connect((self.host, self.port))

            # Send command with newline
            data = json.dumps(command).encode()
            sock.sendall(data + b"\n")

            # Receive response in chunks until newline delimiter
            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break  # Connection closed prematurely
                response_data += chunk
                if response_data.endswith(b"\n"):
                    break  # End of message found

            # Remove trailing newline before parsing
            response_str = response_data.strip().decode()

            if not response_str:
                # Handle case where only newline might have been received or connection closed early
                return {"error": "Received empty or incomplete response from server"}

            try:
                return json.loads(response_str)
            except json.JSONDecodeError:
                # Log the actual invalid string received
                print(f"DEBUG: Received invalid JSON data: '{response_str}'")
                return {
                    "error": "Invalid JSON response received"
                }  # Keep message simple for user

        except socket.timeout:
            return {
                "error": f"Connection to FreeCAD server timed out ({self.host}:{self.port})"
            }
        except ConnectionRefusedError:
            return {
                "error": f"Connection refused by FreeCAD server ({self.host}:{self.port}). Is it running?"
            }
        except Exception as e:
            # Log the specific exception
            print(f"DEBUG: Error in _send_server_command: {type(e).__name__} - {e}")
            return {"error": f"Communication error with FreeCAD server: {e}"}
        finally:
            # Ensure the socket is always closed
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

    def execute_command(
        self, command_type: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a command using the current connection method

        Args:
            command_type: Type of command (e.g., 'get_version', 'create_box')
            params: Optional parameters for the command

        Returns:
            dict: Response from FreeCAD or error dictionary
        """
        if not self.is_connected():
            return {"error": "Not connected to FreeCAD"}

        params = params or {}

        if self.connection_type == self.CONNECTION_SERVER:
            command = {"type": command_type, "params": params}
            return self._send_server_command(command)
        elif self.connection_type == self.CONNECTION_BRIDGE:
            if not self._bridge:
                return {"error": "Bridge not initialized correctly"}
            return self._execute_bridge_command(command_type, params)
        else:
            return {"error": f"Unknown connection type: {self.connection_type}"}

    def _execute_bridge_command(
        self, command_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a command using the FreeCAD bridge

        Args:
            command_type: Command type
            params: Command parameters

        Returns:
            dict: Command response
        """
        if not self._bridge:
            return {"error": "Bridge not initialized"}

        try:
            if command_type == "ping":
                return {"pong": True, "bridge": True}

            elif command_type == "get_version":
                version_info = self._bridge.get_version()
                if version_info.get("success"):
                    return version_info
                return {"error": version_info.get("error")}

            elif command_type == "create_document":
                doc_name = params.get("name", "Unnamed")
                try:
                    actual_name = self._bridge.create_document(doc_name)
                    return {
                        "success": True,
                        "document": {"name": actual_name, "label": actual_name},
                    }
                except Exception as e:
                    return {"error": str(e)}

            elif command_type == "create_object":
                obj_type = params.get("type")
                properties = params.get("properties", {})
                doc_name = params.get("document")

                if obj_type == "box":
                    try:
                        box_name = self._bridge.create_box(
                            length=properties.get("length", 10.0),
                            width=properties.get("width", 10.0),
                            height=properties.get("height", 10.0),
                            doc_name=doc_name,
                        )
                        return {
                            "success": True,
                            "object": {"name": box_name, "type": "Part::Box"},
                        }
                    except Exception as e:
                        return {"error": str(e)}

                # Add other object types as needed

                return {"error": f"Unsupported object type: {obj_type}"}

            elif command_type == "export_document":
                obj_name = params.get("object")
                file_path = params.get("path")
                doc_name = params.get("document")

                if not file_path:
                    return {"error": "No file path specified"}

                success = self._bridge.export_stl(obj_name, file_path, doc_name)

                if success:
                    return {"success": True, "path": file_path}
                else:
                    return {"error": "Failed to export document"}

            # Add more command mappings as needed

            return {"error": f"Unsupported command: {command_type}"}

        except Exception as e:
            return {"error": str(e)}

    # Convenience methods for common operations

    def get_version(self) -> Dict[str, Any]:
        """
        Get FreeCAD version information

        Returns:
            dict: Version information
        """
        return self.execute_command("get_version")

    def create_document(self, name: str = "Unnamed") -> Optional[str]:
        """
        Create a new FreeCAD document

        Args:
            name: Document name

        Returns:
            str: Document name if successful, None if failed
        """
        response = self.execute_command("create_document", {"name": name})

        if response.get("success"):
            doc_info = response.get("document", {})
            return doc_info.get("name")

        return None

    def create_box(
        self,
        length: float = 10.0,
        width: float = 10.0,
        height: float = 10.0,
        document: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a box in a FreeCAD document

        Args:
            length: Box length
            width: Box width
            height: Box height
            document: Document name (uses active document if None)

        Returns:
            str: Box object name if successful, None if failed
        """
        params = {
            "type": "box",
            "properties": {"length": length, "width": width, "height": height},
        }

        if document:
            params["document"] = document

        response = self.execute_command("create_object", params)

        if response.get("success"):
            obj_info = response.get("object", {})
            return obj_info.get("name")

        return None

    def create_cylinder(
        self, radius: float = 5.0, height: float = 10.0, document: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a cylinder in a FreeCAD document

        Args:
            radius: Cylinder radius
            height: Cylinder height
            document: Document name (uses active document if None)

        Returns:
            str: Cylinder object name if successful, None if failed
        """
        params = {
            "type": "cylinder",
            "properties": {"radius": radius, "height": height},
        }

        if document:
            params["document"] = document

        response = self.execute_command("create_object", params)

        if response.get("success"):
            obj_info = response.get("object", {})
            return obj_info.get("name")

        return None

    def export_stl(
        self, object_name: str, file_path: str, document: Optional[str] = None
    ) -> bool:
        """
        Export an object to STL

        Args:
            object_name: Name of the object to export
            file_path: Path to save the STL file
            document: Document name (uses active document if None)

        Returns:
            bool: True if successful
        """
        params = {"object": object_name, "path": file_path}

        if document:
            params["document"] = document

        response = self.execute_command("export_document", params)

        return response.get("success", False)

    def close(self):
        """Close the connection"""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

        # Bridge doesn't need closing
        self._bridge = None
        self.connection_type = None


# Example usage
if __name__ == "__main__":
    # Create connection
    # connection = FreeCADConnection()

    # if not connection.is_connected():
    #     print("Failed to connect to FreeCAD")
    #     sys.exit(1)

    # print(f"Connected to FreeCAD using {connection.get_connection_type()} method")

    # # Get version
    # version_info = connection.get_version()
    # print(f"FreeCAD Version: {version_info}")

    # # Create document
    # doc_name = connection.create_document("TestDocument")
    # if doc_name:
    #     print(f"Created document: {doc_name}")

    #     # Create box
    #     box_name = connection.create_box(10.0, 20.0, 30.0, doc_name)
    #     if box_name:
    #         print(f"Created box: {box_name}")

    #         # Export to STL
    #         stl_path = os.path.join(os.getcwd(), "test_export.stl")
    #         if connection.export_stl(box_name, stl_path, doc_name):
    #             print(f"Exported to: {stl_path}")
    #         else:
    #             print("Failed to export STL")
    #     else:
    #         print("Failed to create box")
    # else:
    #     print("Failed to create document")

    # # Close connection
    # connection.close()
    pass # Add pass to avoid empty block error after commenting everything out
