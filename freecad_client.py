#!/usr/bin/env python3
"""
FreeCAD Client

A client for communicating with FreeCAD using the unified connection interface.
This client can work with the socket-based server, CLI bridge, or mock implementation.
"""

import argparse
import json
import socket
import sys
from typing import Optional

# Import the FreeCADConnection class
try:
    from freecad_connection import FreeCADConnection

    UNIFIED_CONNECTION_AVAILABLE = True
except ImportError:
    UNIFIED_CONNECTION_AVAILABLE = False
    print("Warning: FreeCADConnection not found. Using legacy socket connection mode.")
    print(
        "You may need to install the freecad_connection.py module in the same directory."
    )


class FreeCADClient:
    """Client for communicating with FreeCAD"""

    def __init__(
        self,
        host="localhost",
        port=12345,
        timeout=10.0,
        freecad_path="freecad",
        connection_method=None,
        auto_connect=True,
    ):
        """
        Initialize the client

        Args:
            host: Server hostname for socket connection
            port: Server port for socket connection
            timeout: Connection timeout in seconds
            freecad_path: Path to FreeCAD executable
            connection_method: Preferred connection method (server, bridge, mock)
            auto_connect: Whether to connect automatically
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.freecad_path = freecad_path
        self.connection_method = connection_method
        self._connection = None
        self._legacy_mode = not UNIFIED_CONNECTION_AVAILABLE

        if auto_connect:
            self.connect()

    def connect(self) -> bool:
        """
        Connect to FreeCAD

        Returns:
            bool: True if successfully connected
        """
        if self._legacy_mode:
            # Legacy mode - no connection is maintained, just success status
            try:
                result = self.ping()
                return result.get("pong", False)
            except (socket.error, json.JSONDecodeError):
                return False
        else:
            # Use unified connection
            try:
                self._connection = FreeCADConnection(
                    host=self.host,
                    port=self.port,
                    freecad_path=self.freecad_path,
                    prefer_method=self.connection_method,
                    auto_connect=True,
                )

                # Check if connection is valid
                if self._connection.is_connected():
                    conn_type = self._connection.get_connection_type()
                    print(f"Connected to FreeCAD using {conn_type} method")
                    return True
                else:
                    print("Failed to establish FreeCAD connection")
                    return False
            except Exception as e:
                print(f"Error establishing connection: {e}")
                return False

    def is_connected(self) -> bool:
        """
        Check if connected to FreeCAD

        Returns:
            bool: True if connected
        """
        if self._legacy_mode:
            # In legacy mode, we always try to connect on demand
            try:
                result = self.ping()
                return result.get("pong", False)
            except (socket.error, json.JSONDecodeError):
                return False
        else:
            return self._connection and self._connection.is_connected()

    def get_connection_type(self) -> Optional[str]:
        """
        Get the current connection type

        Returns:
            str: Connection type (server, bridge, or mock)
        """
        if self._legacy_mode:
            return "legacy_socket"

        return self._connection.get_connection_type() if self._connection else None

    def send_command(self, command_type, params=None):
        """
        Send a command to FreeCAD

        Args:
            command_type: Command type
            params: Command parameters

        Returns:
            dict: Command response
        """
        if params is None:
            params = {}

        if self._legacy_mode:
            # Legacy socket-only implementation
            command = {"type": command_type, "params": params}

            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            try:
                # Connect to server
                sock.connect((self.host, self.port))

                # Send command
                sock.sendall(json.dumps(command).encode() + b"\n")

                # Receive response
                response = sock.recv(8192).decode()

                # Parse response
                result = json.loads(response)

                # Check for FreeCADGui attribute errors and provide more helpful messages
                if (
                    "error" in result
                    and "module 'FreeCADGui' has no attribute" in result["error"]
                ):
                    # Add helpful context to the error message
                    result[
                        "error"
                    ] += "\nThis is likely because the server is running without a GUI environment. "
                    result[
                        "error"
                    ] += "Use the '--connect' flag with the server to connect to a running FreeCAD instance."

                return result
            except socket.timeout:
                return {"error": f"Connection timed out after {self.timeout} seconds"}
            except ConnectionRefusedError:
                return {
                    "error": f"Connection refused. Is the FreeCAD server running on {self.host}:{self.port}?"
                }
            except Exception as e:
                return {"error": f"Error communicating with FreeCAD server: {str(e)}"}
            finally:
                sock.close()
        else:
            # Use unified connection
            if not self._connection:
                return {"error": "Not connected to FreeCAD"}

            result = self._connection.execute_command(command_type, params)

            # Check for FreeCADGui attribute errors and provide more helpful messages
            if (
                "error" in result
                and "module 'FreeCADGui' has no attribute" in result["error"]
            ):
                # Add helpful context to the error message
                result[
                    "error"
                ] += "\nThis is likely because the server is running without a GUI environment. "
                result[
                    "error"
                ] += "Use the '--connect' flag with the server to connect to a running FreeCAD instance."

            return result

    def ping(self):
        """Ping the server to check if it's responsive"""
        return self.send_command("ping")

    def get_version(self):
        """Get FreeCAD version information"""
        return self.send_command("get_version")

    def get_model_info(self, document=None):
        """Get information about the current model"""
        params = {}
        if document:
            params["document"] = document

        return self.send_command("get_model_info", params)

    def create_document(self, name="Unnamed"):
        """
        Create a new document

        Args:
            name: Document name

        Returns:
            dict: Response with document info
        """
        return self.send_command("create_document", {"name": name})

    def close_document(self, name=None):
        """Close a document"""
        params = {}
        if name:
            params["name"] = name

        return self.send_command("close_document", params)

    def create_box(
        self, length=10.0, width=10.0, height=10.0, document=None, name=None
    ):
        """Create a box primitive"""
        params = {
            "type": "box",
            "properties": {"length": length, "width": width, "height": height},
        }

        if document:
            params["document"] = document

        if name:
            params["name"] = name

        return self.send_command("create_object", params)

    def create_cylinder(self, radius=5.0, height=10.0, document=None, name=None):
        """Create a cylinder primitive"""
        params = {
            "type": "cylinder",
            "properties": {"radius": radius, "height": height},
        }

        if document:
            params["document"] = document

        if name:
            params["name"] = name

        return self.send_command("create_object", params)

    def create_sphere(self, radius=5.0, document=None, name=None):
        """Create a sphere primitive"""
        params = {"type": "sphere", "properties": {"radius": radius}}

        if document:
            params["document"] = document

        if name:
            params["name"] = name

        return self.send_command("create_object", params)

    def modify_object(self, object_name, properties, document=None):
        """Modify an existing object"""
        params = {"object": object_name, "properties": properties}

        if document:
            params["document"] = document

        return self.send_command("modify_object", params)

    def delete_object(self, object_name, document=None):
        """Delete an object"""
        params = {"object": object_name}

        if document:
            params["document"] = document

        return self.send_command("delete_object", params)

    def execute_script(self, script):
        """Execute a Python script in FreeCAD context"""
        return self.send_command("execute_script", {"script": script})

    def measure_distance(self, from_point, to_point):
        """Measure distance between two points"""
        params = {"from": from_point, "to": to_point}

        return self.send_command("measure_distance", params)

    def export_document(self, file_path, file_type="step", document=None):
        """Export document to a file"""
        params = {"path": file_path, "type": file_type}

        if document:
            params["document"] = document

        return self.send_command("export_document", params)

    def close(self):
        """Close the connection if using unified connection"""
        if not self._legacy_mode and self._connection:
            self._connection.close()
            self._connection = None


def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(description="FreeCAD Client")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=12345, help="Server port")
    parser.add_argument("--timeout", type=float, default=10.0, help="Connection timeout")
    parser.add_argument("--freecad", default="freecad", help="Path to FreeCAD executable")
    parser.add_argument(
        "--connect",
        action="store_true",
        help="Connect to running FreeCAD instance",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically choose connection method",
    )

    args = parser.parse_args()

    # Create client
    client = FreeCADClient(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        freecad_path=args.freecad,
        connection_method="connect" if args.connect else "auto" if args.auto else None,
    )

    # Try to connect
    if not client.is_connected():
        print(
            f"Error: Could not connect to FreeCAD. Please ensure the server is running on {args.host}:{args.port}"
        )
        sys.exit(1)

    # Get connection type
    conn_type = client.get_connection_type()
    print(f"Connected to FreeCAD using {conn_type} method.")

    # Close client
    client.close()


if __name__ == "__main__":
    main()
