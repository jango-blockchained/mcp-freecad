#!/usr/bin/env python3
"""
FreeCAD Server Script

This script provides a socket-based interface for communicating with external applications
like the MCP server.

Usage:
   Run directly with Python: python3 freecad_server.py

Command-line arguments:
   --host HOST     Server hostname (default: localhost or from config)
   --port PORT     Server port (default: 12345 or from config)
   --debug         Enable debug logging
   --config FILE   Path to config file (default: ~/.freecad_server.json)
   --connect       Try to connect to a running FreeCAD instance instead of using mock mode
"""

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

# Load config and parse command line args first, so we can use the paths
parser = argparse.ArgumentParser(description='FreeCAD Server')
parser.add_argument('--host', help='Server hostname')
parser.add_argument('--port', type=int, help='Server port')
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
parser.add_argument('--config', help='Path to config file')
parser.add_argument('--connect', action='store_true', help='Connect to running FreeCAD instead of using mock mode')

args = parser.parse_args()

# Load config
config = {
    "host": DEFAULT_HOST,
    "port": DEFAULT_PORT,
    "debug": True,
    "connect_to_freecad": False
}

# First try explicitly provided config file
if args.config and os.path.exists(args.config):
    try:
        with open(args.config, 'r') as f:
            config.update(json.load(f))
    except Exception as e:
        print(f"Error loading config file {args.config}: {e}")
# Then try default config file
elif os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r') as f:
            config.update(json.load(f))
    except Exception as e:
        print(f"Error loading config: {e}")

# Also look for config.json in current directory
if os.path.exists("config.json"):
    try:
        with open("config.json", 'r') as f:
            loaded_config = json.load(f)
            if "freecad" in loaded_config:
                config["freecad"] = loaded_config["freecad"]
    except Exception as e:
        print(f"Error loading config.json: {e}")

# Update config with command line arguments
if args.debug:
    config["debug"] = True
    
if args.connect:
    config["connect_to_freecad"] = True
    print("Running in connect mode - will try to connect to a running FreeCAD instance")

# Configure logging
DEBUG = config.get("debug", False)

def log(message):
    """Log message if debug is enabled"""
    if DEBUG:
        print(f"[FreeCAD Server] {message}")

# Try to add FreeCAD module path before importing
freecad_config = config.get("freecad", {})
freecad_path = freecad_config.get("path", "freecad")
freecad_python_path = freecad_config.get("python_path")

# More robust method to find FreeCAD module
found_freecad_module = False

if freecad_path and os.path.exists(freecad_path):
    log(f"Using FreeCAD executable from config: {freecad_path}")
    # Try to locate the FreeCAD module directory based on the executable path
    freecad_base_dir = os.path.dirname(os.path.dirname(freecad_path))
    potential_module_paths = [
        os.path.join(freecad_base_dir, "lib"),
        os.path.join(freecad_base_dir, "lib", "freecad"),
        os.path.join(freecad_base_dir, "Mod"),
        os.path.join(freecad_base_dir, "usr", "lib"),
        os.path.join(freecad_base_dir, "usr", "lib", "freecad"),
        # Directly look in squashfs locations
        os.path.join(freecad_base_dir, "usr", "lib", "python3"),
        os.path.join(freecad_base_dir, "usr", "lib", "python3", "dist-packages"),
        # For AppImage structure
        freecad_base_dir
    ]
    
    # More verbose debugging
    print(f"Looking for FreeCAD module in directories based on executable: {freecad_path}")
    print(f"Base directory: {freecad_base_dir}")
    
    for path in potential_module_paths:
        if os.path.exists(path):
            print(f"Found path: {path}")
            log(f"Adding potential FreeCAD module path: {path}")
            sys.path.append(path)
            
            # Check if we can now import FreeCAD
            try:
                import importlib
                importlib.import_module("FreeCAD")
                found_freecad_module = True
                print(f"Successfully imported FreeCAD module from {path}")
                break
            except ImportError:
                print(f"FreeCAD module not found in {path}")

# If we still haven't found it, try a more direct approach - look for the Python executable's dist-packages
if not found_freecad_module and freecad_python_path and os.path.exists(freecad_python_path):
    print(f"Trying to use Python path from config: {freecad_python_path}")
    # Get Python's site-packages directory
    try:
        # Run Python to get site-packages directory
        import subprocess
        result = subprocess.run(
            [freecad_python_path, "-c", "import site; print(site.getsitepackages())"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            # Parse the output, which will be a list like "['path1', 'path2']"
            import ast
            site_packages = ast.literal_eval(result.stdout.strip())
            for path in site_packages:
                print(f"Adding site-packages path: {path}")
                sys.path.append(path)
                
                # Also try dist-packages
                dist_packages = path.replace("site-packages", "dist-packages")
                if os.path.exists(dist_packages):
                    print(f"Adding dist-packages path: {dist_packages}")
                    sys.path.append(dist_packages)
                
            # Check if we can now import FreeCAD
            try:
                import importlib
                importlib.import_module("FreeCAD")
                found_freecad_module = True
                print(f"Successfully imported FreeCAD module from site-packages")
            except ImportError:
                print(f"FreeCAD module not found in site-packages")
    except Exception as e:
        print(f"Error getting site-packages directory: {e}")

# If we're using an AppImage or standalone FreeCAD executable, try to extract it
if not found_freecad_module and os.path.exists(freecad_path):
    print("Attempting to locate FreeCAD module in AppImage/standalone structure...")
    # For AppImage, the Python module might be in a different location
    # Check if we can run FreeCAD with --write-python-path
    try:
        import subprocess
        result = subprocess.run(
            [freecad_path, "--write-python-path"], 
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            python_path = result.stdout.strip().split('\n')[0]
            print(f"FreeCAD reported Python path: {python_path}")
            if os.path.exists(python_path):
                # Add the path to sys.path
                sys.path.append(python_path)
                # Try to import FreeCAD again
                try:
                    import importlib
                    importlib.import_module("FreeCAD")
                    found_freecad_module = True
                    print(f"Successfully imported FreeCAD module from {python_path}")
                except ImportError:
                    print(f"FreeCAD module not found in {python_path}")
    except Exception as e:
        print(f"Error getting Python path from FreeCAD: {e}")

# Try to import FreeCAD 
try:
    import FreeCAD
    # FreeCAD module imported successfully
    FREECAD_AVAILABLE = True
    print("FreeCAD module found and imported successfully.")
except ImportError as e:
    # FreeCAD module not available, mock it for development
    print(f"WARNING: FreeCAD module not found ({e}). Using mock implementation.")
    print(f"Current Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
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

# Try to import FreeCADGui for GUI operations
try:
    import FreeCADGui
    FREECADGUI_AVAILABLE = True
    print("FreeCADGui module found and imported successfully.")
except ImportError:
    FREECADGUI_AVAILABLE = False
    print("FreeCADGui module not available. GUI operations will not be possible.")

# Use command line arguments if provided, otherwise use config values
host = args.host or config["host"]
port = args.port or config["port"]

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
        
        # Send response (append newline as delimiter)
        response = json.dumps(result).encode() + b'\n'
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
        "freecad_available": FREECAD_AVAILABLE,
        "freecadgui_available": FREECADGUI_AVAILABLE,
        "connect_mode": config.get("connect_to_freecad", False)
    }

def handle_get_version(params):
    """Get FreeCAD version information"""
    return {
        "version": FreeCAD.Version,
        "build_date": FreeCAD.BuildDate,
        "os_platform": sys.platform,
        "freecad_available": FREECAD_AVAILABLE,
        "freecadgui_available": FREECADGUI_AVAILABLE
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
    
    # If in connect mode and GUI is available, make the document visible
    if config.get("connect_to_freecad", False) and FREECADGUI_AVAILABLE:
        FreeCADGui.getDocument(name)
        FreeCADGui.ActiveDocument = FreeCADGui.getDocument(name)
        FreeCADGui.ActiveDocument.resetEdit()
    
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
            if config.get("connect_to_freecad", False) and FREECADGUI_AVAILABLE:
                FreeCADGui.getDocument(doc_name)
                FreeCADGui.ActiveDocument = FreeCADGui.getDocument(doc_name)
    else:
        if FreeCAD.ActiveDocument:
            doc = FreeCAD.ActiveDocument
        else:
            doc = FreeCAD.newDocument("Unnamed")
            if config.get("connect_to_freecad", False) and FREECADGUI_AVAILABLE:
                FreeCADGui.getDocument("Unnamed")
                FreeCADGui.ActiveDocument = FreeCADGui.getDocument("Unnamed")
    
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
    
    # Update GUI if in connect mode
    if config.get("connect_to_freecad", False) and FREECADGUI_AVAILABLE:
        FreeCADGui.updateGui()
        # Force view update
        if FreeCADGui.ActiveDocument:
            for view in FreeCADGui.getMainWindow().findChildren(FreeCADGui.View3DInventor):
                view.update()
    
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
    
    # Update GUI if in connect mode
    if config.get("connect_to_freecad", False) and FREECADGUI_AVAILABLE:
        FreeCADGui.updateGui()
    
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
    
    # Update GUI if in connect mode
    if config.get("connect_to_freecad", False) and FREECADGUI_AVAILABLE:
        FreeCADGui.updateGui()
    
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
    
    # Add FreeCADGui if available
    if FREECADGUI_AVAILABLE:
        local_env["FreeCADGui"] = FreeCADGui
    
    # Execute script
    try:
        exec(script, {}, local_env)
        
        # Filter out non-serializable values from the environment
        result_env = {}
        for key, value in local_env.items():
            if key not in ["FreeCAD", "FreeCADGui"] and not key.startswith("__"):
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
    
    connect_mode = config.get("connect_to_freecad", False)
    mode_text = "in connect mode" if connect_mode else "in standalone mode"
    freecad_status = "available" if FREECAD_AVAILABLE else "not available - using mock implementation"
    
    print(f"Starting FreeCAD server on {host}:{port} {mode_text} (FreeCAD {freecad_status})")
    
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
    # Start the server directly (not as a background thread)
    try:
        start_server(host, port)
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        traceback.print_exc() 