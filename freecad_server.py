#!/usr/bin/env python3
"""
FreeCAD Server Script

This script runs inside FreeCAD and provides a socket-based interface
for communicating with external applications like the MCP server.

Usage:
1. Run FreeCAD
2. In the Python console in FreeCAD, execute:
   exec(open("/path/to/freecad_server.py").read())

Or run from command line:
   freecad -c /home/jango/Git/mcp-freecad/src/mcp_freecad/tools/freecad_server.py

Command-line arguments:
   --host HOST     Server hostname (default: localhost or from config)
   --port PORT     Server port (default: 12345 or from config)
   --debug         Enable debug logging
   --config FILE   Path to config file (default: ~/.freecad_server.json)
"""

try:
    import FreeCAD
    # FreeCAD module imported successfully
    FREECAD_AVAILABLE = True
except ImportError:
    # FreeCAD module not available, mock it for development
    print("WARNING: FreeCAD module not found. Using mock implementation.")
    FREECAD_AVAILABLE = False
    
    # Create a mock FreeCAD module
    class MockFreeCAD:
        Version = ["0.21.0", "mock", "2025"]
        BuildDate = "2025/03/31"
        BuildVersionMajor = "mock"
        GuiUp = False
        ActiveDocument = None
        
        class Vector:
            def __init__(self, x=0, y=0, z=0):
                self.x = x
                self.y = y
                self.z = z
                
            def distanceToPoint(self, other):
                return ((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)**0.5
        
        def getDocument(self, name):
            return MockDocument(name)
            
        def newDocument(self, name):
            self.ActiveDocument = MockDocument(name)
            return self.ActiveDocument
            
        def listDocuments(self):
            return []
            
    class MockDocument:
        def __init__(self, name):
            self.Name = name
            self.Label = name
            self.Objects = []
            self.Modified = False
            
        def addObject(self, obj_type, name):
            obj = MockObject(obj_type, name)
            self.Objects.append(obj)
            return obj
            
        def removeObject(self, name):
            self.Objects = [obj for obj in self.Objects if obj.Name != name]
            
        def recompute(self):
            pass
            
        def getObject(self, name):
            for obj in self.Objects:
                if obj.Name == name:
                    return obj
            return None
            
    class MockObject:
        def __init__(self, type_id, name):
            self.TypeId = type_id
            self.Name = name
            self.Label = name
            self.Visibility = True
            self.PropertiesList = []
            
            # Add properties based on type
            if type_id == "Part::Box":
                self.Length = 10.0
                self.Width = 10.0
                self.Height = 10.0
                self.PropertiesList = ["Length", "Width", "Height"]
            elif type_id == "Part::Cylinder":
                self.Radius = 5.0
                self.Height = 10.0
                self.PropertiesList = ["Radius", "Height"]
            elif type_id == "Part::Sphere":
                self.Radius = 5.0
                self.PropertiesList = ["Radius"]
                
        def getTypeIdOfProperty(self, prop):
            if prop in ["Length", "Width", "Height", "Radius"]:
                return "App::PropertyLength"
            return "App::PropertyString"
    
    # Create mock FreeCAD instance
    FreeCAD = MockFreeCAD()

import json
import socket
import threading
import sys
import time
import os
import traceback
import argparse

# Default settings
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 12345
CONFIG_FILE = os.path.expanduser("~/.freecad_server.json")

# Load config if exists
config = {
    "host": DEFAULT_HOST,
    "port": DEFAULT_PORT,
    "debug": True
}

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r') as f:
            config.update(json.load(f))
    except Exception as e:
        print(f"Error loading config: {e}")

# Configure logging
DEBUG = config.get("debug", False)

def log(message):
    """Log message if debug is enabled"""
    if DEBUG:
        print(f"[FreeCAD Server] {message}")

def handle_client(conn, addr):
    """Handle a client connection"""
    log(f"Connection from {addr}")
    try:
        # Receive data
        data = conn.recv(4096)
        if not data:
            return
            
        # Parse command
        command = json.loads(data.decode())
        log(f"Received command: {command}")
        
        # Execute command
        result = execute_command(command)
        
        # Send response
        response = json.dumps(result).encode()
        conn.sendall(response)
        log(f"Sent response: {result}")
    except Exception as e:
        error_message = traceback.format_exc()
        log(f"Error handling client: {error_message}")
        try:
            conn.sendall(json.dumps({
                "error": str(e),
                "traceback": error_message
            }).encode())
        except:
            pass
    finally:
        conn.close()

def execute_command(command):
    """Execute a command and return the result"""
    cmd_type = command.get("type")
    params = command.get("params", {})
    
    command_handlers = {
        "ping": handle_ping,
        "get_version": handle_get_version,
        "get_model_info": handle_get_model_info,
        "create_document": handle_create_document,
        "close_document": handle_close_document,
        "create_object": handle_create_object,
        "modify_object": handle_modify_object,
        "delete_object": handle_delete_object,
        "execute_script": handle_execute_script,
        "measure_distance": handle_measure_distance,
        "export_document": handle_export_document
    }
    
    handler = command_handlers.get(cmd_type)
    if handler:
        try:
            return handler(params)
        except Exception as e:
            return {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    return {"error": f"Unknown command: {cmd_type}"}

# Command handlers

def handle_ping(params):
    """Handle ping command"""
    return {
        "pong": True,
        "timestamp": time.time(),
        "freecad_available": FREECAD_AVAILABLE
    }

def handle_get_version(params):
    """Get FreeCAD version information"""
    return {
        "version": FreeCAD.Version,
        "build_date": FreeCAD.BuildDate,
        "os_platform": sys.platform,
        "freecad_available": FREECAD_AVAILABLE
    }

def handle_get_model_info(params):
    """Get information about the current document and objects"""
    doc_name = params.get("document")
    
    # Get the specified document or active document
    if doc_name:
        doc = FreeCAD.getDocument(doc_name)
    else:
        doc = FreeCAD.ActiveDocument
    
    if not doc:
        return {"error": "No active document"}
    
    # Get objects
    objects = []
    for obj in doc.Objects:
        # Get properties
        properties = {}
        for prop in obj.PropertiesList:
            try:
                prop_type = obj.getTypeIdOfProperty(prop)
                prop_value = getattr(obj, prop)
                
                # Convert to serializable type if needed
                if hasattr(prop_value, "__dict__"):
                    prop_value = str(prop_value)
                
                properties[prop] = {
                    "type": prop_type,
                    "value": prop_value
                }
            except:
                # Skip properties that can't be serialized
                pass
        
        objects.append({
            "name": obj.Name,
            "label": obj.Label,
            "type": obj.TypeId,
            "visibility": obj.Visibility,
            "properties": properties
        })
    
    return {
        "document": {
            "name": doc.Name,
            "label": doc.Label,
            "modified": doc.Modified,
            "objects_count": len(doc.Objects)
        },
        "objects": objects,
        "freecad_available": FREECAD_AVAILABLE
    }

def handle_create_document(params):
    """Create a new document"""
    name = params.get("name", "Unnamed")
    
    # Check if document already exists
    if name in FreeCAD.listDocuments():
        return {"error": f"Document '{name}' already exists"}
    
    # Create document
    doc = FreeCAD.newDocument(name)
    
    return {
        "success": True,
        "document": {
            "name": doc.Name,
            "label": doc.Label
        },
        "freecad_available": FREECAD_AVAILABLE
    }

def handle_close_document(params):
    """Close a document"""
    name = params.get("name")
    
    if not name:
        if FreeCAD.ActiveDocument:
            name = FreeCAD.ActiveDocument.Name
        else:
            return {"error": "No active document"}
    
    if name not in FreeCAD.listDocuments():
        return {"error": f"Document '{name}' does not exist"}
    
    FreeCAD.closeDocument(name)
    
    return {
        "success": True,
        "freecad_available": FREECAD_AVAILABLE
    }

def handle_create_object(params):
    """Create a new object"""
    doc_name = params.get("document")
    obj_type = params.get("type")
    obj_name = params.get("name", "")
    properties = params.get("properties", {})
    
    # Get or create document
    if doc_name:
        if doc_name in FreeCAD.listDocuments():
            doc = FreeCAD.getDocument(doc_name)
        else:
            doc = FreeCAD.newDocument(doc_name)
    else:
        if FreeCAD.ActiveDocument:
            doc = FreeCAD.ActiveDocument
        else:
            doc = FreeCAD.newDocument("Unnamed")
    
    # Create object based on type
    if obj_type == "box":
        obj = doc.addObject("Part::Box", obj_name or "Box")
        if "length" in properties:
            obj.Length = properties["length"]
        if "width" in properties:
            obj.Width = properties["width"]
        if "height" in properties:
            obj.Height = properties["height"]
    
    elif obj_type == "cylinder":
        obj = doc.addObject("Part::Cylinder", obj_name or "Cylinder")
        if "radius" in properties:
            obj.Radius = properties["radius"]
        if "height" in properties:
            obj.Height = properties["height"]
    
    elif obj_type == "sphere":
        obj = doc.addObject("Part::Sphere", obj_name or "Sphere")
        if "radius" in properties:
            obj.Radius = properties["radius"]
    
    else:
        return {"error": f"Unsupported object type: {obj_type}"}
    
    # Apply other properties
    for prop, value in properties.items():
        if hasattr(obj, prop) and prop not in ["length", "width", "height", "radius"]:
            try:
                setattr(obj, prop, value)
            except:
                pass
    
    # Recompute document
    doc.recompute()
    
    return {
        "success": True,
        "object": {
            "name": obj.Name,
            "label": obj.Label,
            "type": obj.TypeId
        },
        "freecad_available": FREECAD_AVAILABLE
    }

def handle_modify_object(params):
    """Modify an existing object"""
    doc_name = params.get("document")
    obj_name = params.get("object")
    properties = params.get("properties", {})
    
    # Get document
    if doc_name:
        if doc_name in FreeCAD.listDocuments():
            doc = FreeCAD.getDocument(doc_name)
        else:
            return {"error": f"Document '{doc_name}' does not exist"}
    else:
        if FreeCAD.ActiveDocument:
            doc = FreeCAD.ActiveDocument
        else:
            return {"error": "No active document"}
    
    # Get object
    if not obj_name:
        return {"error": "No object specified"}
    
    try:
        obj = doc.getObject(obj_name)
    except:
        return {"error": f"Object '{obj_name}' not found"}
    
    if not obj:
        return {"error": f"Object '{obj_name}' not found"}
    
    # Modify properties
    modified_props = []
    for prop, value in properties.items():
        if hasattr(obj, prop):
            try:
                setattr(obj, prop, value)
                modified_props.append(prop)
            except Exception as e:
                return {"error": f"Failed to set property '{prop}': {e}"}
    
    # Recompute document
    doc.recompute()
    
    return {
        "success": True,
        "modified_properties": modified_props,
        "freecad_available": FREECAD_AVAILABLE
    }

def handle_delete_object(params):
    """Delete an object"""
    doc_name = params.get("document")
    obj_name = params.get("object")
    
    # Get document
    if doc_name:
        if doc_name in FreeCAD.listDocuments():
            doc = FreeCAD.getDocument(doc_name)
        else:
            return {"error": f"Document '{doc_name}' does not exist"}
    else:
        if FreeCAD.ActiveDocument:
            doc = FreeCAD.ActiveDocument
        else:
            return {"error": "No active document"}
    
    # Get object
    if not obj_name:
        return {"error": "No object specified"}
    
    try:
        obj = doc.getObject(obj_name)
    except:
        return {"error": f"Object '{obj_name}' not found"}
    
    if not obj:
        return {"error": f"Object '{obj_name}' not found"}
    
    # Delete object
    doc.removeObject(obj_name)
    
    return {
        "success": True,
        "freecad_available": FREECAD_AVAILABLE
    }

def handle_execute_script(params):
    """Execute a Python script in FreeCAD context"""
    script = params.get("script")
    
    if not script:
        return {"error": "No script provided"}
    
    # Create a local environment for the script
    local_env = {"FreeCAD": FreeCAD}
    
    # Execute script
    try:
        exec(script, {}, local_env)
        
        # Filter out non-serializable values from the environment
        result_env = {}
        for key, value in local_env.items():
            if key != "FreeCAD" and not key.startswith("__"):
                try:
                    # Test if it's serializable
                    json.dumps({key: value})
                    result_env[key] = value
                except:
                    result_env[key] = str(value)
        
        return {
            "success": True,
            "environment": result_env,
            "freecad_available": FREECAD_AVAILABLE
        }
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def handle_measure_distance(params):
    """Measure distance between points, edges, or faces"""
    from_obj = params.get("from")
    to_obj = params.get("to")
    
    if not from_obj or not to_obj:
        return {"error": "Missing 'from' or 'to' parameters"}
    
    # This is a simplistic implementation - would need to be expanded based on
    # actual requirements and FreeCAD's measurement capabilities
    try:
        # For demonstration, assuming from_obj and to_obj are points
        from_point = FreeCAD.Vector(from_obj[0], from_obj[1], from_obj[2])
        to_point = FreeCAD.Vector(to_obj[0], to_obj[1], to_obj[2])
        
        distance = from_point.distanceToPoint(to_point)
        
        return {
            "success": True,
            "distance": distance,
            "units": "mm",
            "freecad_available": FREECAD_AVAILABLE
        }
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def handle_export_document(params):
    """Export the document to a file"""
    doc_name = params.get("document")
    file_path = params.get("path")
    file_type = params.get("type", "step")
    
    if not file_path:
        return {"error": "No file path specified"}
    
    # Get document
    if doc_name:
        if doc_name in FreeCAD.listDocuments():
            doc = FreeCAD.getDocument(doc_name)
        else:
            return {"error": f"Document '{doc_name}' does not exist"}
    else:
        if FreeCAD.ActiveDocument:
            doc = FreeCAD.ActiveDocument
        else:
            return {"error": "No active document"}
    
    # Export based on file type
    try:
        if not FREECAD_AVAILABLE:
            return {
                "success": True,
                "path": file_path,
                "mock": True,
                "freecad_available": FREECAD_AVAILABLE
            }
            
        if file_type.lower() == "step":
            import ImportGui
            ImportGui.export(doc.Objects, file_path)
        elif file_type.lower() == "stl":
            import Mesh
            Mesh.export(doc.Objects, file_path)
        else:
            return {"error": f"Unsupported file type: {file_type}"}
        
        return {
            "success": True,
            "path": file_path,
            "freecad_available": FREECAD_AVAILABLE
        }
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

def start_server(host=None, port=None):
    """Start the FreeCAD server"""
    host = host or config["host"]
    port = port or config["port"]
    
    print(f"Starting FreeCAD server on {host}:{port} (FreeCAD {'available' if FREECAD_AVAILABLE else 'not available - using mock implementation'})")
    
    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"FreeCAD server listening on {host}:{port}")
        
        while True:
            try:
                # Accept connections
                conn, addr = server_socket.accept()
                
                # Handle client in a new thread
                client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                client_thread.daemon = True
                client_thread.start()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error accepting connection: {e}")
    finally:
        server_socket.close()
        print("FreeCAD server stopped")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='FreeCAD Server')
    parser.add_argument('--host', help='Server hostname')
    parser.add_argument('--port', type=int, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--config', help='Path to config file')
    
    args = parser.parse_args()
    
    # Update config with command line arguments
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                config.update(json.load(f))
        except Exception as e:
            print(f"Error loading config file {args.config}: {e}")
    
    if args.debug:
        config["debug"] = True
        DEBUG = True
    
    # Use command line arguments if provided, otherwise use config values
    host = args.host or config["host"]
    port = args.port or config["port"]
    
    start_server(host, port) 