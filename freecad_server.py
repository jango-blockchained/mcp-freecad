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

import argparse
import json
import logging
import os
import socket
import sys
import threading
import time
import traceback
import subprocess

logger = logging.getLogger(__name__)

# Default settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 12345
CONFIG_FILE = os.path.expanduser("~/.freecad_server.json")

# Load config and parse command line args first, so we can use the paths
parser = argparse.ArgumentParser(description="FreeCAD Server")
parser.add_argument("--host", help="Server hostname")
parser.add_argument("--port", type=int, help="Server port")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
parser.add_argument("--config", help="Path to config file")
parser.add_argument(
    "--connect",
    action="store_true",
    help="Connect to running FreeCAD instead of using mock mode",
)

args = parser.parse_args()

# Load config
config = {
    "host": DEFAULT_HOST,
    "port": DEFAULT_PORT,
    "debug": True,
    "connect_to_freecad": False,
}

# First try explicitly provided config file
if args.config and os.path.exists(args.config):
    try:
        with open(args.config, "r") as f:
            config.update(json.load(f))
    except Exception as e:
        print(f"Error loading config file {args.config}: {e}")
# Then try default config file
elif os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r") as f:
            config.update(json.load(f))
    except Exception as e:
        print(f"Error loading config: {e}")

# Also look for config.json in current directory
if os.path.exists("config.json"):
    try:
        with open("config.json", "r") as f:
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
module_path = freecad_config.get("module_path")
use_mock = freecad_config.get("use_mock", False)

# If we're being told explicitly not to use mock mode, we'll try harder to find FreeCAD
if not use_mock:
    print("Mock mode disabled. Attempting to locate and load actual FreeCAD modules...")

    # Step 1: Check if module_path is specified and valid
    if module_path and os.path.exists(module_path):
        print(f"Using module path from config: {module_path}")
        sys.path.append(module_path)

    # Step 2: Try to find FreeCAD executable and get its Python environment
    if freecad_path and os.path.exists(freecad_path):
        try:
            # Since --write-python-path is not supported, let's just add the known paths
            # for an extracted AppImage
            if os.path.exists(os.path.join(os.path.dirname(freecad_path), "usr/lib")):
                # AppImage structure
                lib_path = os.path.join(os.path.dirname(freecad_path), "usr/lib")
                print(f"Adding AppImage lib path: {lib_path}")
                sys.path.append(lib_path)
            else:
                # Traditional FreeCAD installation
                print(f"Using standard FreeCAD paths")
        except Exception as e:
            print(f"Error getting FreeCAD Python paths: {e}")

    # Step 3: Look in common system locations
    common_freecad_paths = [
        "/usr/lib/freecad-python3/lib",
        "/usr/lib/freecad/lib",
        "/usr/lib/freecad",
        "/usr/lib/python3/dist-packages/freecad",
        "/usr/share/freecad/lib",
    ]

    for path in common_freecad_paths:
        if os.path.exists(path):
            print(f"Found potential FreeCAD path: {path}")
            sys.path.append(path)

# Try to import FreeCAD
try:
    import FreeCAD

    # FreeCAD module imported successfully
    # Verify that essential methods and attributes exist
    if (
        not hasattr(FreeCAD, "ActiveDocument")
        or not hasattr(FreeCAD, "newDocument")
        or not hasattr(FreeCAD, "Version")
    ):
        print(
            "WARNING: FreeCAD module imported but appears incomplete. Using mock implementation instead."
        )
        FREECAD_AVAILABLE = False
        # Define a mock FreeCAD module
        # ... (existing mock code) ...
    else:
        # FreeCAD module appears to be valid
        FREECAD_AVAILABLE = True
        print("FreeCAD module found and imported successfully.")
        print(f"FreeCAD Version: {FreeCAD.Version}")
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
                return (
                    (self.x - other.x) ** 2
                    + (self.y - other.y) ** 2
                    + (self.z - other.z) ** 2
                ) ** 0.5

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

    # Check if essential methods and attributes exist
    gui_available = True

    # Basic test to ensure the GUI module is actually functional
    if not hasattr(FreeCADGui, "ActiveDocument") or not hasattr(
        FreeCADGui, "getDocument"
    ):
        print(
            "FreeCADGui module found but appears to be incomplete. Some GUI operations may fail."
        )
        print(
            "This is normal when running in connect mode without a proper GUI environment."
        )
        gui_available = False

    FREECADGUI_AVAILABLE = gui_available
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
        response = json.dumps(result).encode() + b"\n"
        conn.sendall(response)
        log(f"Sent response: {result}")
    except Exception as e:
        error_message = traceback.format_exc()
        log(f"Error handling client: {error_message}")
        try:
            conn.sendall(
                json.dumps({"error": str(e), "traceback": error_message}).encode()
            )
        except (ConnectionError, OSError) as send_error:
            log(f"Failed to send error response: {send_error}")
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
        "export_document": handle_export_document,
    }

    handler = command_handlers.get(cmd_type)
    if handler:
        try:
            return handler(params)
        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}

    return {"error": f"Unknown command: {cmd_type}"}


# Command handlers


def handle_ping(params):
    """Handle ping command"""
    return {
        "pong": True,
        "timestamp": time.time(),
        "freecad_available": FREECAD_AVAILABLE,
        "freecadgui_available": FREECADGUI_AVAILABLE,
        "connect_mode": config.get("connect_to_freecad", False),
    }


def handle_get_version(params):
    """Get FreeCAD version information"""
    version_info = {}

    # Get version information with safety checks
    if hasattr(FreeCAD, "Version"):
        # Handle Version which could be a variety of types
        try:
            if callable(FreeCAD.Version):
                try:
                    version = FreeCAD.Version()
                    if isinstance(version, (list, tuple)):
                        version_info["version"] = list(version)
                    else:
                        version_info["version"] = [str(version)]
                except (AttributeError, TypeError):
                    version_info["version"] = ["Unknown (callable error)"]
            # If it's a list or tuple, convert to list
            elif isinstance(FreeCAD.Version, (list, tuple)):
                version_info["version"] = list(FreeCAD.Version)
            # Otherwise convert to string in a list
            else:
                version_info["version"] = [str(FreeCAD.Version)]
        except (AttributeError, TypeError):
            version_info["version"] = ["Unknown (error)"]
    else:
        version_info["version"] = ["Unknown (missing)"]

    # BuildDate might not be available in all FreeCAD builds
    if hasattr(FreeCAD, "BuildDate"):
        # Handle BuildDate similarly
        try:
            if callable(FreeCAD.BuildDate):
                try:
                    version_info["build_date"] = str(FreeCAD.BuildDate())
                except (AttributeError, TypeError):
                    version_info["build_date"] = "Unknown (callable)"
            else:
                version_info["build_date"] = str(FreeCAD.BuildDate)
        except (AttributeError, TypeError):
            version_info["build_date"] = "Unknown (error)"
    else:
        version_info["build_date"] = "Unknown (missing)"

    # Add system information
    version_info["os_platform"] = sys.platform
    version_info["freecad_available"] = FREECAD_AVAILABLE
    version_info["freecadgui_available"] = FREECADGUI_AVAILABLE

    return version_info


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

                properties[prop] = {"type": prop_type, "value": prop_value}
            except (AttributeError, TypeError, ValueError) as e:
                # Skip properties that can't be serialized
                log(f"Failed to serialize property {prop}: {e}")
                continue

        objects.append(
            {
                "name": obj.Name,
                "label": obj.Label,
                "type": obj.TypeId,
                "visibility": obj.Visibility,
                "properties": properties,
            }
        )

    return {
        "document": {
            "name": doc.Name,
            "label": doc.Label,
            "modified": doc.Modified,
            "objects_count": len(doc.Objects),
        },
        "objects": objects,
        "freecad_available": FREECAD_AVAILABLE,
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
        try:
            # Check if the required methods exist before calling them
            if hasattr(FreeCADGui, "getDocument") and callable(FreeCADGui.getDocument):
                FreeCADGui.getDocument(name)
                if hasattr(FreeCADGui, "ActiveDocument"):
                    FreeCADGui.ActiveDocument = FreeCADGui.getDocument(name)
                    if hasattr(FreeCADGui.ActiveDocument, "resetEdit") and callable(
                        FreeCADGui.ActiveDocument.resetEdit
                    ):
                        FreeCADGui.ActiveDocument.resetEdit()
        except Exception as e:
            log(f"GUI activation error (non-fatal): {e}")

    return {
        "success": True,
        "document": {"name": doc.Name, "label": doc.Label},
        "freecad_available": FREECAD_AVAILABLE,
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

    return {"success": True, "freecad_available": FREECAD_AVAILABLE}


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
                try:
                    # Check if the required methods exist before calling them
                    if hasattr(FreeCADGui, "getDocument") and callable(
                        FreeCADGui.getDocument
                    ):
                        FreeCADGui.getDocument(doc_name)
                        if hasattr(FreeCADGui, "ActiveDocument"):
                            FreeCADGui.ActiveDocument = FreeCADGui.getDocument(doc_name)
                except Exception as e:
                    log(f"GUI activation error (non-fatal): {e}")
    else:
        if FreeCAD.ActiveDocument:
            doc = FreeCAD.ActiveDocument
        else:
            doc = FreeCAD.newDocument("Unnamed")
            if config.get("connect_to_freecad", False) and FREECADGUI_AVAILABLE:
                try:
                    # Check if the required methods exist before calling them
                    if hasattr(FreeCADGui, "getDocument") and callable(
                        FreeCADGui.getDocument
                    ):
                        FreeCADGui.getDocument("Unnamed")
                        if hasattr(FreeCADGui, "ActiveDocument"):
                            FreeCADGui.ActiveDocument = FreeCADGui.getDocument(
                                "Unnamed"
                            )
                except Exception as e:
                    log(f"GUI activation error (non-fatal): {e}")

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
            except Exception:
                pass

    # Recompute document
    doc.recompute()

    # Update GUI if in connect mode
    if config.get("connect_to_freecad", False) and FREECADGUI_AVAILABLE:
        try:
            # Check if updateGui method exists
            if hasattr(FreeCADGui, "updateGui") and callable(FreeCADGui.updateGui):
                FreeCADGui.updateGui()

                # Force view update - with safety checks
                if hasattr(FreeCADGui, "ActiveDocument") and FreeCADGui.ActiveDocument:
                    try:
                        # Check if getMainWindow and findChildren are available
                        if (
                            hasattr(FreeCADGui, "getMainWindow")
                            and callable(FreeCADGui.getMainWindow)
                            and hasattr(FreeCADGui, "View3DInventor")
                        ):
                            main_window = FreeCADGui.getMainWindow()
                            if main_window and hasattr(main_window, "findChildren"):
                                for view in main_window.findChildren(
                                    FreeCADGui.View3DInventor
                                ):
                                    if hasattr(view, "update") and callable(
                                        view.update
                                    ):
                                        view.update()
                    except Exception as e:
                        log(f"View update error (non-fatal): {e}")
        except Exception as e:
            log(f"GUI update error (non-fatal): {e}")

    return {
        "success": True,
        "object": {"name": obj.Name, "label": obj.Label, "type": obj.TypeId},
        "freecad_available": FREECAD_AVAILABLE,
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
    except (AttributeError, RuntimeError):
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
        try:
            if hasattr(FreeCADGui, "updateGui") and callable(FreeCADGui.updateGui):
                FreeCADGui.updateGui()
        except Exception as e:
            log(f"GUI update error (non-fatal): {e}")

    return {
        "success": True,
        "modified_properties": modified_props,
        "freecad_available": FREECAD_AVAILABLE,
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
    except (AttributeError, RuntimeError):
        return {"error": f"Object '{obj_name}' not found"}

    if not obj:
        return {"error": f"Object '{obj_name}' not found"}

    # Delete object
    doc.removeObject(obj_name)

    # Update GUI if in connect mode
    if config.get("connect_to_freecad", False) and FREECADGUI_AVAILABLE:
        try:
            if hasattr(FreeCADGui, "updateGui") and callable(FreeCADGui.updateGui):
                FreeCADGui.updateGui()
        except Exception as e:
            log(f"GUI update error (non-fatal): {e}")

    return {"success": True, "freecad_available": FREECAD_AVAILABLE}


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
                except (TypeError, ValueError):
                    result_env[key] = str(value)

        return {
            "success": True,
            "environment": result_env,
            "freecad_available": FREECAD_AVAILABLE,
        }
    except (AttributeError, RuntimeError) as e:
        logger.error(f"Error executing script: {e}")
        return {"error": str(e)}


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
            "freecad_available": FREECAD_AVAILABLE,
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


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
                "freecad_available": FREECAD_AVAILABLE,
            }

        if file_type.lower() == "step":
            try:
                # Try to import the module with error handling
                import importlib

                try:
                    # Try ImportGui first
                    ImportGui = importlib.import_module("ImportGui")
                    ImportGui.export(doc.Objects, file_path)
                except (ImportError, AttributeError) as e:
                    log(f"ImportGui not available: {e}, trying Part module")
                    # Fallback to Part module
                    import Part

                    Part.export(doc.Objects, file_path)
            except Exception as e:
                return {"error": f"Failed to export STEP: {e}"}

        elif file_type.lower() == "stl":
            try:
                # Try to import the module with error handling
                import importlib

                try:
                    # Try Mesh module first
                    Mesh = importlib.import_module("Mesh")
                    Mesh.export(doc.Objects, file_path)
                except (ImportError, AttributeError) as e:
                    return {"error": f"Mesh module not available: {e}"}
            except Exception as e:
                return {"error": f"Failed to export STL: {e}"}

        else:
            return {"error": f"Unsupported file type: {file_type}"}

        return {
            "success": True,
            "path": file_path,
            "freecad_available": FREECAD_AVAILABLE,
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


def start_server(host=None, port=None):
    """Start the FreeCAD server"""
    host = host or config["host"]
    port = port or config["port"]

    connect_mode = config.get("connect_to_freecad", False)
    mode_text = "in connect mode" if connect_mode else "in standalone mode"
    freecad_status = (
        "available"
        if FREECAD_AVAILABLE
        else "not available - using mock implementation"
    )

    print(
        f"Starting FreeCAD server on {host}:{port} {mode_text} (FreeCAD {freecad_status})"
    )

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
                client_thread = threading.Thread(
                    target=handle_client, args=(conn, addr)
                )
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
