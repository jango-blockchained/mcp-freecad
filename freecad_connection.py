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

# Import FreeCADBridge class if available
try:
    from freecad_bridge import FreeCADBridge

    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False


class FreeCADConnection:
    """
    A unified interface for connecting to FreeCAD using various methods
    """

    CONNECTION_SERVER = "server"
    CONNECTION_BRIDGE = "bridge"
    CONNECTION_MOCK = "mock"

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
            prefer_method: Preferred connection method (default: None = auto-detect)
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
            prefer_method: Preferred connection method (server, bridge, or mock)

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
            elif method == self.CONNECTION_MOCK:
                success = self._connect_mock()

            if success:
                self.connection_type = method
                return True

        # If we got here, all methods failed
        return False

    def _get_connection_methods(self, prefer_method: Optional[str] = None) -> List[str]:
        """
        Get ordered list of connection methods to try

        Args:
            prefer_method: Preferred method

        Returns:
            List of methods to try in order
        """
        all_methods = [
            self.CONNECTION_SERVER,
            self.CONNECTION_BRIDGE,
            self.CONNECTION_MOCK,
        ]

        if prefer_method in all_methods:
            # Move preferred method to the front
            methods = [prefer_method]
            methods.extend([m for m in all_methods if m != prefer_method])
            return methods

        return all_methods

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
            return False

        try:
            self._bridge = FreeCADBridge(self.freecad_path)
            return self._bridge.is_available()
        except Exception:
            return False

    def _connect_mock(self) -> bool:
        """
        Connect using mock implementation

        Returns:
            bool: Always True
        """
        # Mock connection is always available as fallback
        return True

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
            str: Connection type (server, bridge, or mock)
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

    def _execute_mock_command(
        self, command_type: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a mock command when no real FreeCAD is available

        Args:
            command_type: Command type
            params: Command parameters

        Returns:
            dict: Mock response
        """
        params = params or {}

        if command_type == "ping":
            return {"pong": True, "mock": True}

        elif command_type == "get_version":
            return {
                "version": ["0.21.0", "mock", "2023"],
                "build_date": "2023/01/01",
                "mock": True,
            }

        elif command_type == "create_document":
            return {
                "success": True,
                "document": {
                    "name": params.get("name", "Unnamed"),
                    "label": params.get("name", "Unnamed"),
                },
                "mock": True,
            }

        elif command_type == "create_object":
            obj_type = params.get("type", "box")
            obj_name = params.get("name", f"Mock{obj_type.capitalize()}")

            obj_properties = {}
            if obj_type == "box":
                obj_properties = {
                    "length": params.get("properties", {}).get("length", 10.0),
                    "width": params.get("properties", {}).get("width", 10.0),
                    "height": params.get("properties", {}).get("height", 10.0),
                }
            elif obj_type == "cylinder":
                obj_properties = {
                    "radius": params.get("properties", {}).get("radius", 5.0),
                    "height": params.get("properties", {}).get("height", 10.0),
                }

            return {
                "success": True,
                "object": {
                    "name": obj_name,
                    "label": obj_name,
                    "type": f"Part::{obj_type.capitalize()}",
                },
                "properties": obj_properties,
                "mock": True,
            }

        elif command_type == "export_document":
            return {
                "success": True,
                "path": params.get("path", "mock_export.stl"),
                "mock": True,
            }

        # Default mock response
        return {
            "success": True,
            "command": command_type,
            "params": params,
            "mock": True,
        }

    def execute_command(
        self, command_type: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a command using the current connection method

        Args:
            command_type: Command type
            params: Command parameters

        Returns:
            dict: Command response
        """
        params = params or {}

        if not self.is_connected():
            return {"error": "Not connected to FreeCAD"}

        if self.connection_type == self.CONNECTION_SERVER:
            # Use socket server
            command = {"type": command_type, "params": params}
            return self._send_server_command(command)

        elif self.connection_type == self.CONNECTION_BRIDGE:
            # Use bridge
            return self._execute_bridge_command(command_type, params)

        else:
            # Use mock implementation
            return self._execute_mock_command(command_type, params)

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
    connection = FreeCADConnection()

    if not connection.is_connected():
        print("Failed to connect to FreeCAD")
        sys.exit(1)

    print(f"Connected to FreeCAD using {connection.get_connection_type()} method")

    # Get version
    version_info = connection.get_version()
    print(f"FreeCAD Version: {version_info}")

    # Create document
    doc_name = connection.create_document("TestDocument")
    if doc_name:
        print(f"Created document: {doc_name}")

        # Create box
        box_name = connection.create_box(10.0, 20.0, 30.0, doc_name)
        if box_name:
            print(f"Created box: {box_name}")

            # Export to STL
            stl_path = os.path.join(os.getcwd(), "test_export.stl")
            if connection.export_stl(box_name, stl_path, doc_name):
                print(f"Exported to: {stl_path}")
            else:
                print("Failed to export STL")
        else:
            print("Failed to create box")
    else:
        print("Failed to create document")

    # Close connection
    connection.close()
