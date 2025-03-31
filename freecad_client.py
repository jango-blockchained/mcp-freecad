#!/usr/bin/env python3
"""
FreeCAD Client

A client for communicating with the FreeCAD server.
"""

import socket
import json
import sys
import os
import time

class FreeCADClient:
    """Client for communicating with FreeCAD server"""
    
    def __init__(self, host='localhost', port=12345, timeout=10.0):
        """Initialize the client"""
        self.host = host
        self.port = port
        self.timeout = timeout
    
    def send_command(self, command_type, params=None):
        """Send a command to the FreeCAD server"""
        if params is None:
            params = {}
            
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
            sock.sendall(json.dumps(command).encode())
            
            # Receive response
            response = sock.recv(8192).decode()
            
            # Parse response
            return json.loads(response)
        except socket.timeout:
            return {"error": f"Connection timed out after {self.timeout} seconds"}
        except ConnectionRefusedError:
            return {"error": f"Connection refused. Is the FreeCAD server running on {self.host}:{self.port}?"}
        except Exception as e:
            return {"error": f"Error communicating with FreeCAD server: {str(e)}"}
        finally:
            sock.close()
    
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
        """Create a new document"""
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


def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FreeCAD Client')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=12345, help='Server port (default: 12345)')
    parser.add_argument('--timeout', type=float, default=10.0, help='Connection timeout in seconds (default: 10.0)')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Ping command
    subparsers.add_parser('ping', help='Ping the server')
    
    # Version command
    subparsers.add_parser('version', help='Get FreeCAD version')
    
    # Model info command
    info_parser = subparsers.add_parser('info', help='Get model information')
    info_parser.add_argument('--document', help='Document name')
    
    # Create document command
    create_doc_parser = subparsers.add_parser('create-document', help='Create a new document')
    create_doc_parser.add_argument('name', help='Document name')
    
    # Close document command
    close_doc_parser = subparsers.add_parser('close-document', help='Close a document')
    close_doc_parser.add_argument('--name', help='Document name (optional)')
    
    # Create box command
    box_parser = subparsers.add_parser('create-box', help='Create a box')
    box_parser.add_argument('--length', type=float, default=10.0, help='Box length (default: 10.0)')
    box_parser.add_argument('--width', type=float, default=10.0, help='Box width (default: 10.0)')
    box_parser.add_argument('--height', type=float, default=10.0, help='Box height (default: 10.0)')
    box_parser.add_argument('--document', help='Document name (optional)')
    box_parser.add_argument('--name', help='Object name (optional)')
    
    # Create cylinder command
    cylinder_parser = subparsers.add_parser('create-cylinder', help='Create a cylinder')
    cylinder_parser.add_argument('--radius', type=float, default=5.0, help='Cylinder radius (default: 5.0)')
    cylinder_parser.add_argument('--height', type=float, default=10.0, help='Cylinder height (default: 10.0)')
    cylinder_parser.add_argument('--document', help='Document name (optional)')
    cylinder_parser.add_argument('--name', help='Object name (optional)')
    
    # Create sphere command
    sphere_parser = subparsers.add_parser('create-sphere', help='Create a sphere')
    sphere_parser.add_argument('--radius', type=float, default=5.0, help='Sphere radius (default: 5.0)')
    sphere_parser.add_argument('--document', help='Document name (optional)')
    sphere_parser.add_argument('--name', help='Object name (optional)')
    
    # Execute script command
    script_parser = subparsers.add_parser('execute-script', help='Execute a Python script')
    script_parser.add_argument('script', help='Python script to execute')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create client
    client = FreeCADClient(args.host, args.port, args.timeout)
    
    # Execute command
    if args.command == 'ping':
        result = client.ping()
    elif args.command == 'version':
        result = client.get_version()
    elif args.command == 'info':
        result = client.get_model_info(args.document)
    elif args.command == 'create-document':
        result = client.create_document(args.name)
    elif args.command == 'close-document':
        result = client.close_document(args.name)
    elif args.command == 'create-box':
        result = client.create_box(args.length, args.width, args.height, args.document, args.name)
    elif args.command == 'create-cylinder':
        result = client.create_cylinder(args.radius, args.height, args.document, args.name)
    elif args.command == 'create-sphere':
        result = client.create_sphere(args.radius, args.document, args.name)
    elif args.command == 'execute-script':
        result = client.execute_script(args.script)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Print result
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main() 