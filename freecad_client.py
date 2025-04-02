#!/usr/bin/env python3
"""
FreeCAD Client

A client for communicating with FreeCAD using the unified connection interface.
This client can work with the socket-based server, CLI bridge, or mock implementation.
"""

import socket
import json
import sys
import os
import time
import argparse
from typing import Dict, Any, Optional, List

# Import the FreeCADConnection class
try:
    from freecad_connection import FreeCADConnection
    UNIFIED_CONNECTION_AVAILABLE = True
except ImportError:
    UNIFIED_CONNECTION_AVAILABLE = False
    print("Warning: FreeCADConnection not found. Using legacy socket connection mode.")
    print("You may need to install the freecad_connection.py module in the same directory.")

class FreeCADClient:
    """Client for communicating with FreeCAD"""
    
    def __init__(self, host='localhost', port=12345, timeout=10.0, freecad_path='freecad', 
                 connection_method=None, auto_connect=True):
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
            except Exception as e:
                print(f"Connection error: {e}")
                return False
        else:
            # Use unified connection
            try:
                self._connection = FreeCADConnection(
                    host=self.host,
                    port=self.port,
                    freecad_path=self.freecad_path,
                    prefer_method=self.connection_method,
                    auto_connect=True
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
            except:
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
            command = {
                "type": command_type,
                "params": params
            }
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            try:
                # Connect to server
                sock.connect((self.host, self.port))
                
                # Send command
                sock.sendall(json.dumps(command).encode() + b'\n')
                
                # Receive response
                response = sock.recv(8192).decode()
                
                # Parse response
                result = json.loads(response)
                
                # Check for FreeCADGui attribute errors and provide more helpful messages
                if "error" in result and "module 'FreeCADGui' has no attribute" in result["error"]:
                    # Add helpful context to the error message
                    result["error"] += "\nThis is likely because the server is running without a GUI environment. "
                    result["error"] += "Use the '--connect' flag with the server to connect to a running FreeCAD instance."
                
                return result
            except socket.timeout:
                return {"error": f"Connection timed out after {self.timeout} seconds"}
            except ConnectionRefusedError:
                return {"error": f"Connection refused. Is the FreeCAD server running on {self.host}:{self.port}?"}
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
            if "error" in result and "module 'FreeCADGui' has no attribute" in result["error"]:
                # Add helpful context to the error message
                result["error"] += "\nThis is likely because the server is running without a GUI environment. "
                result["error"] += "Use the '--connect' flag with the server to connect to a running FreeCAD instance."
            
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
    
    def create_box(self, length=10.0, width=10.0, height=10.0, document=None, name=None):
        """Create a box primitive"""
        params = {
            "type": "box",
            "properties": {
                "length": length,
                "width": width,
                "height": height
            }
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
            "properties": {
                "radius": radius,
                "height": height
            }
        }
        
        if document:
            params["document"] = document
            
        if name:
            params["name"] = name
            
        return self.send_command("create_object", params)
    
    def create_sphere(self, radius=5.0, document=None, name=None):
        """Create a sphere primitive"""
        params = {
            "type": "sphere",
            "properties": {
                "radius": radius
            }
        }
        
        if document:
            params["document"] = document
            
        if name:
            params["name"] = name
            
        return self.send_command("create_object", params)
    
    def modify_object(self, object_name, properties, document=None):
        """Modify an existing object"""
        params = {
            "object": object_name,
            "properties": properties
        }
        
        if document:
            params["document"] = document
            
        return self.send_command("modify_object", params)
    
    def delete_object(self, object_name, document=None):
        """Delete an object"""
        params = {
            "object": object_name
        }
        
        if document:
            params["document"] = document
            
        return self.send_command("delete_object", params)
    
    def execute_script(self, script):
        """Execute a Python script in FreeCAD context"""
        return self.send_command("execute_script", {"script": script})
    
    def measure_distance(self, from_point, to_point):
        """Measure distance between two points"""
        params = {
            "from": from_point,
            "to": to_point
        }
        
        return self.send_command("measure_distance", params)
    
    def export_document(self, file_path, file_type="step", document=None):
        """Export document to a file"""
        params = {
            "path": file_path,
            "type": file_type
        }
        
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
    parser = argparse.ArgumentParser(description='FreeCAD Client')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=12345, help='Server port (default: 12345)')
    parser.add_argument('--timeout', type=float, default=10.0, help='Connection timeout in seconds (default: 10.0)')
    parser.add_argument('--method', choices=['server', 'bridge', 'mock'], 
                        help='Preferred connection method (default: auto-detect)')
    parser.add_argument('--freecad-path', default='freecad', 
                        help='Path to FreeCAD executable (default: "freecad")')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Ping command
    ping_parser = subparsers.add_parser('ping', help='Ping the FreeCAD server')
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Get FreeCAD version')
    
    # Model info command
    model_parser = subparsers.add_parser('model', help='Get model info')
    model_parser.add_argument('--document', help='Document name')
    
    # Create document command
    create_doc_parser = subparsers.add_parser('create-document', help='Create a new document')
    create_doc_parser.add_argument('name', nargs='?', default='Unnamed', help='Document name')
    
    # Close document command
    close_doc_parser = subparsers.add_parser('close-document', help='Close a document')
    close_doc_parser.add_argument('name', nargs='?', help='Document name')
    
    # Create box command
    create_box_parser = subparsers.add_parser('create-box', help='Create a box')
    create_box_parser.add_argument('--length', type=float, default=10.0, help='Box length')
    create_box_parser.add_argument('--width', type=float, default=10.0, help='Box width')
    create_box_parser.add_argument('--height', type=float, default=10.0, help='Box height')
    create_box_parser.add_argument('--document', help='Document name')
    create_box_parser.add_argument('--name', help='Object name')
    
    # Create cylinder command
    create_cylinder_parser = subparsers.add_parser('create-cylinder', help='Create a cylinder')
    create_cylinder_parser.add_argument('--radius', type=float, default=5.0, help='Cylinder radius')
    create_cylinder_parser.add_argument('--height', type=float, default=10.0, help='Cylinder height')
    create_cylinder_parser.add_argument('--document', help='Document name')
    create_cylinder_parser.add_argument('--name', help='Object name')
    
    # Create sphere command
    create_sphere_parser = subparsers.add_parser('create-sphere', help='Create a sphere')
    create_sphere_parser.add_argument('--radius', type=float, default=5.0, help='Sphere radius')
    create_sphere_parser.add_argument('--document', help='Document name')
    create_sphere_parser.add_argument('--name', help='Object name')
    
    # Modify object command
    modify_parser = subparsers.add_parser('modify', help='Modify an object')
    modify_parser.add_argument('object', help='Object name')
    modify_parser.add_argument('--property', '-p', action='append', nargs=2, metavar=('NAME', 'VALUE'),
                              help='Property name and value')
    modify_parser.add_argument('--document', help='Document name')
    
    # Delete object command
    delete_parser = subparsers.add_parser('delete', help='Delete an object')
    delete_parser.add_argument('object', help='Object name')
    delete_parser.add_argument('--document', help='Document name')
    
    # Execute script command
    script_parser = subparsers.add_parser('script', help='Execute a Python script')
    script_parser.add_argument('script', help='Python script to execute')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export document to a file')
    export_parser.add_argument('path', help='Output file path')
    export_parser.add_argument('--type', default='step', choices=['step', 'stl'], help='File type')
    export_parser.add_argument('--document', help='Document name')
    
    args = parser.parse_args()
    
    # Create client
    client = FreeCADClient(
        host=args.host, 
        port=args.port, 
        timeout=args.timeout,
        freecad_path=args.freecad_path,
        connection_method=args.method,
        auto_connect=True
    )
    
    # Check connection
    if not client.is_connected():
        print(f"Error: Could not connect to FreeCAD. Please ensure the server is running on {args.host}:{args.port}")
        sys.exit(1)
    
    conn_type = client.get_connection_type()
    print(f"Connected to FreeCAD using {conn_type} method.")
    
    # Execute command
    result = None
    
    if args.command == 'ping':
        result = client.ping()
    
    elif args.command == 'version':
        result = client.get_version()
    
    elif args.command == 'model':
        result = client.get_model_info(args.document)
    
    elif args.command == 'create-document':
        result = client.create_document(args.name)
    
    elif args.command == 'close-document':
        result = client.close_document(args.name)
    
    elif args.command == 'create-box':
        result = client.create_box(
            length=args.length,
            width=args.width,
            height=args.height,
            document=args.document,
            name=args.name
        )
    
    elif args.command == 'create-cylinder':
        result = client.create_cylinder(
            radius=args.radius,
            height=args.height,
            document=args.document,
            name=args.name
        )
    
    elif args.command == 'create-sphere':
        result = client.create_sphere(
            radius=args.radius,
            document=args.document,
            name=args.name
        )
    
    elif args.command == 'modify':
        # Parse property values
        properties = {}
        if args.property:
            for name, value in args.property:
                # Try to convert value to number if possible
                try:
                    if '.' in value:
                        properties[name] = float(value)
                    else:
                        properties[name] = int(value)
                except ValueError:
                    properties[name] = value
        
        result = client.modify_object(args.object, properties, args.document)
    
    elif args.command == 'delete':
        result = client.delete_object(args.object, args.document)
    
    elif args.command == 'script':
        result = client.execute_script(args.script)
    
    elif args.command == 'export':
        result = client.export_document(args.path, args.type, args.document)
    
    else:
        print("Error: No command specified")
        parser.print_help()
        sys.exit(1)
    
    # Print result
    if result:
        if 'error' in result:
            print(f"Error: {result['error']}")
            sys.exit(1)
        else:
            print(json.dumps(result, indent=2))
    
    # Close the connection
    client.close()


if __name__ == "__main__":
    main() 