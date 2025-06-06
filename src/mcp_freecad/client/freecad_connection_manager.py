#!/usr/bin/env python3
"""
FreeCAD Connection Manager

This module provides a unified interface for connecting to FreeCAD using either:
1. Socket-based communication with freecad_socket_server.py running inside FreeCAD
2. CLI-based communication using the FreeCAD executable directly
3. XML-RPC-based communication with an RPC server running inside FreeCAD

Usage:
    from src.mcp_freecad.client.freecad_connection_manager import FreeCADConnection

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
import xmlrpc.client
from typing import Any, Dict, List, Optional
import logging

# Set up logger for this module
logger = logging.getLogger(__name__)

# --- FreeCADBridge Import Attempt ---
BRIDGE_AVAILABLE = False
_bridge_import_error_msg = ""

try:
    # Try to import from the server directory where bridge implementations are located
    from ..server.freecad_bridge import FreeCADBridge

    BRIDGE_AVAILABLE = True
    logger.info("Successfully imported FreeCADBridge from server module")
except ImportError:
    try:
        # Fallback: try direct import if running from project root
        from freecad_connection_bridge import FreeCADBridge

        BRIDGE_AVAILABLE = True
        logger.info("Successfully imported FreeCADBridge via direct import")
    except ImportError as e:
        _bridge_import_error_msg = f"Failed to import FreeCADBridge: {e}"
        logger.warning(_bridge_import_error_msg)

        # Create a dummy class to prevent runtime errors
        class FreeCADBridge:
            def __init__(self, *args, **kwargs):
                pass

            def is_available(self):
                return False


class FreeCADConnection:
    """
    A unified interface for connecting to FreeCAD using various methods
    """

    CONNECTION_SERVER = "server"
    CONNECTION_BRIDGE = "bridge"
    CONNECTION_RPC = "rpc"
    CONNECTION_MOCK = "mock"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 12345,
        rpc_port: int = 9875,
        freecad_path: str = "freecad",
        auto_connect: bool = True,
        prefer_method: Optional[str] = None,
    ):
        """
        Initialize the FreeCAD connection

        Args:
            host: Server hostname for socket/RPC connection (default: localhost)
            port: Server port for socket connection (default: 12345)
            rpc_port: Server port for XML-RPC connection (default: 9875)
            freecad_path: Path to FreeCAD executable for CLI bridge (default: 'freecad')
            auto_connect: Whether to automatically connect (default: True)
            prefer_method: Preferred connection method (server, bridge, or rpc)
        """
        self.host = host
        self.port = port
        self.rpc_port = rpc_port
        self.freecad_path = freecad_path
        self.connection_type = None
        self._bridge = None
        self._socket = None
        self._rpc = None

        if auto_connect:
            self.connect(prefer_method)

    def connect(self, prefer_method: Optional[str] = None) -> bool:
        """
        Connect to FreeCAD using the best available method

        Args:
            prefer_method: Preferred connection method (server, bridge, or rpc)

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
            elif method == self.CONNECTION_RPC:
                success = self._connect_rpc()
            elif method == self.CONNECTION_MOCK:
                success = self._connect_mock()

            if success:
                self.connection_type = method
                logger.info(f"Successfully connected to FreeCAD using {method} method")
                return True

        logger.error("Failed to connect to FreeCAD using any available method")
        return False

    def _get_connection_methods(self, prefer_method: Optional[str] = None) -> List[str]:
        """
        Get ordered list of connection methods to try.

        Args:
            prefer_method: Preferred method to try first

        Returns:
            List of connection methods in order of preference
        """
        # If a preferred method is specified, try that first
        if prefer_method:
            if prefer_method == self.CONNECTION_RPC:
                return [
                    self.CONNECTION_RPC,
                    self.CONNECTION_BRIDGE,
                    self.CONNECTION_SERVER,
                ]
            elif prefer_method == self.CONNECTION_SERVER:
                return [
                    self.CONNECTION_SERVER,
                    self.CONNECTION_RPC,
                    self.CONNECTION_BRIDGE,
                ]
            elif prefer_method == self.CONNECTION_BRIDGE:
                return [
                    self.CONNECTION_BRIDGE,
                    self.CONNECTION_RPC,
                    self.CONNECTION_SERVER,
                ]
            elif prefer_method == self.CONNECTION_MOCK:
                # Mock connection should be tried exclusively when preferred
                return [self.CONNECTION_MOCK]

        # Default order: RPC first (higher performance), then Server, then Bridge
        return [self.CONNECTION_RPC, self.CONNECTION_SERVER, self.CONNECTION_BRIDGE]

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
        except Exception as e:
            logger.debug(f"Server connection failed: {e}")
            return False

    def _connect_bridge(self) -> bool:
        """
        Connect using FreeCAD bridge

        Returns:
            bool: True if successful
        """
        if not BRIDGE_AVAILABLE:
            logger.debug(
                "FreeCADBridge dependency not found. Bridge connection unavailable."
            )
            return False

        try:
            logger.debug(
                f"Attempting to initialize FreeCADBridge with path: {self.freecad_path}"
            )
            self._bridge = FreeCADBridge(self.freecad_path)
            is_avail = self._bridge.is_available()
            logger.debug(f"FreeCADBridge.is_available() returned: {is_avail}")
            return is_avail
        except Exception as e:
            logger.debug(f"Failed to initialize FreeCADBridge: {e}")
            return False

    def _connect_rpc(self) -> bool:
        """
        Connect using XML-RPC server

        Returns:
            bool: True if successful
        """
        try:
            # Create XML-RPC client
            rpc_url = f"http://{self.host}:{self.rpc_port}"
            self._rpc = xmlrpc.client.ServerProxy(rpc_url, allow_none=True)

            # Test connection with ping
            ping_response = self._rpc.ping()
            logger.debug(f"XML-RPC ping response: {ping_response}")
            return ping_response is True
        except Exception as e:
            logger.debug(f"Failed to connect to FreeCAD XML-RPC server: {e}")
            self._rpc = None
            return False

    def _connect_mock(self) -> bool:
        """
        Connect using mock connection

        Returns:
            bool: True if successful
        """
        # Implementation of _connect_mock method
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
            str: Connection type (server, bridge, or rpc)
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
        sock = None
        try:
            # Create a new socket for each command
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
                    break
                response_data += chunk
                if response_data.endswith(b"\n"):
                    break

            # Remove trailing newline before parsing
            response_str = response_data.strip().decode()

            if not response_str:
                return {"error": "Received empty or incomplete response from server"}

            try:
                return json.loads(response_str)
            except json.JSONDecodeError:
                logger.debug(f"Received invalid JSON data: '{response_str}'")
                return {"error": "Invalid JSON response received"}

        except socket.timeout:
            return {
                "error": f"Connection to FreeCAD server timed out ({self.host}:{self.port})"
            }
        except ConnectionRefusedError:
            return {
                "error": f"Connection refused by FreeCAD server ({self.host}:{self.port}). Is it running?"
            }
        except Exception as e:
            logger.debug(f"Error in _send_server_command: {type(e).__name__} - {e}")
            return {"error": f"Communication error with FreeCAD server: {e}"}
        finally:
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
        elif self.connection_type == self.CONNECTION_RPC:
            if not self._rpc:
                return {"error": "RPC client not initialized correctly"}
            return self._execute_rpc_command(command_type, params)
        elif self.connection_type == self.CONNECTION_MOCK:
            return self._execute_mock_command(command_type, params)
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

            return {"error": f"Unsupported command: {command_type}"}

        except Exception as e:
            return {"error": str(e)}

    def _execute_rpc_command(
        self, command_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a command using the XML-RPC connection

        Args:
            command_type: Command type
            params: Command parameters

        Returns:
            dict: Command response
        """
        if not self._rpc:
            return {"error": "RPC client not initialized"}

        try:
            if command_type == "ping":
                return {"pong": True, "rpc": True}

            elif command_type == "get_version":
                return {"success": True, "version": "RPC version info"}

            elif command_type == "create_document":
                doc_name = params.get("name", "Unnamed")
                response = self._rpc.create_document(doc_name)
                if response.get("success"):
                    return {
                        "success": True,
                        "document": {
                            "name": response.get("document_name"),
                            "label": response.get("document_name"),
                        },
                    }
                else:
                    return {"error": response.get("error", "Unknown error")}

            elif command_type == "create_object":
                obj_type = params.get("type")
                properties = params.get("properties", {})
                doc_name = params.get("document")

                obj_data = {
                    "Name": f"{obj_type.split('::', 1)[-1] if '::' in obj_type else obj_type}",
                    "Type": obj_type,
                    "Properties": properties,
                }

                if obj_type == "box":
                    obj_data = {
                        "Name": "Box",
                        "Type": "Part::Box",
                        "Properties": {
                            "Length": properties.get("length", 10.0),
                            "Width": properties.get("width", 10.0),
                            "Height": properties.get("height", 10.0),
                        },
                    }

                response = self._rpc.create_object(doc_name, obj_data)
                if response.get("success"):
                    return {
                        "success": True,
                        "object": {
                            "name": response.get("object_name"),
                            "type": obj_type,
                        },
                    }
                else:
                    return {"error": response.get("error", "Unknown error")}

            elif command_type == "export_document":
                obj_name = params.get("object")
                file_path = params.get("path")
                doc_name = params.get("document")

                if not file_path:
                    return {"error": "No file path specified"}

                return {
                    "error": "Export functionality not yet implemented for RPC connection"
                }

            return {"error": f"Unsupported command: {command_type}"}

        except Exception as e:
            return {"error": str(e)}

    def _execute_mock_command(
        self, command_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a command using the mock connection

        Args:
            command_type: Command type
            params: Command parameters

        Returns:
            dict: Command response
        """
        # Provide simple in-memory mock behavior for testing
        if command_type == "ping":
            return {"pong": True, "mock": True}

        elif command_type == "get_version":
            return {"success": True, "version": "Mock 0.0.1"}

        elif command_type == "create_document":
            doc_name = params.get("name", "Unnamed")
            # Pretend document creation succeeds
            return {
                "success": True,
                "document": {"name": doc_name, "label": doc_name},
            }

        elif command_type == "create_object":
            obj_type = params.get("type", "object")
            return {
                "success": True,
                "object": {"name": f"Mock{obj_type.title()}", "type": obj_type},
            }

        elif command_type == "export_document":
            file_path = params.get("path", "mock_output.stl")
            return {"success": True, "path": file_path}

        else:
            return {"error": f"Unsupported mock command: {command_type}"}

    # Convenience methods for common operations

    def get_version(self) -> Dict[str, Any]:
        """Get FreeCAD version information"""
        return self.execute_command("get_version")

    def create_document(self, name: str = "Unnamed") -> Optional[str]:
        """Create a new FreeCAD document"""
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
        """Create a box in a FreeCAD document"""
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
        """Create a cylinder in a FreeCAD document"""
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
        """Export an object to STL"""
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

        self._bridge = None
        self._rpc = None
        self.connection_type = None


# Example usage
if __name__ == "__main__":
    pass
