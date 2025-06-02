import FreeCAD
import FreeCADGui

import contextlib
import queue
import base64
import io
import os
import tempfile
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from xmlrpc.server import SimpleXMLRPCServer

from PySide2.QtCore import QTimer

from .serialize import serialize_object

# Global variables for server state
rpc_server_thread = None
rpc_server_instance = None

# GUI task queue for thread-safe operations
rpc_request_queue = queue.Queue()
rpc_response_queue = queue.Queue()


def process_gui_tasks():
    """Process tasks in the GUI thread queue"""
    while not rpc_request_queue.empty():
        task = rpc_request_queue.get()
        res = task()
        if res is not None:
            rpc_response_queue.put(res)
    QTimer.singleShot(500, process_gui_tasks)


@dataclass
class Object:
    """Data class for object creation/modification"""
    name: str
    type: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)


def set_object_property(
    doc: FreeCAD.Document, obj: FreeCAD.DocumentObject, properties: Dict[str, Any]
):
    """Set properties on a FreeCAD object
    
    Args:
        doc: FreeCAD document
        obj: FreeCAD object
        properties: Dictionary of properties to set
    """
    for prop, val in properties.items():
        try:
            if prop in obj.PropertiesList:
                if prop == "Placement" and isinstance(val, dict):
                    if "Base" in val:
                        pos = val["Base"]
                    elif "Position" in val:
                        pos = val["Position"]
                    else:
                        pos = {}
                    rot = val.get("Rotation", {})
                    placement = FreeCAD.Placement(
                        FreeCAD.Vector(
                            pos.get("x", 0),
                            pos.get("y", 0),
                            pos.get("z", 0),
                        ),
                        FreeCAD.Rotation(
                            FreeCAD.Vector(
                                rot.get("Axis", {}).get("x", 0),
                                rot.get("Axis", {}).get("y", 0),
                                rot.get("Axis", {}).get("z", 1),
                            ),
                            rot.get("Angle", 0),
                        ),
                    )
                    setattr(obj, prop, placement)

                elif isinstance(getattr(obj, prop), FreeCAD.Vector) and isinstance(
                    val, dict
                ):
                    vector = FreeCAD.Vector(
                        val.get("x", 0), val.get("y", 0), val.get("z", 0)
                    )
                    setattr(obj, prop, vector)

                elif prop in ["Base", "Tool", "Source", "Profile"] and isinstance(
                    val, str
                ):
                    ref_obj = doc.getObject(val)
                    if ref_obj:
                        setattr(obj, prop, ref_obj)
                    else:
                        raise ValueError(f"Referenced object '{val}' not found.")

                elif prop == "References" and isinstance(val, list):
                    refs = []
                    for ref_name, face in val:
                        ref_obj = doc.getObject(ref_name)
                        if ref_obj:
                            refs.append((ref_obj, face))
                        else:
                            raise ValueError(f"Referenced object '{ref_name}' not found.")
                    setattr(obj, prop, refs)

                else:
                    setattr(obj, prop, val)
            # ShapeColor is a property of the ViewObject
            elif prop == "ShapeColor" and isinstance(val, (list, tuple)) and hasattr(obj, "ViewObject"):
                setattr(obj.ViewObject, prop, (float(val[0]), float(val[1]), float(val[2]), float(val[3]) if len(val) > 3 else 0.0))

            elif prop == "ViewObject" and isinstance(val, dict) and hasattr(obj, "ViewObject"):
                for k, v in val.items():
                    if k == "ShapeColor" and isinstance(v, (list, tuple)):
                        setattr(obj.ViewObject, k, (float(v[0]), float(v[1]), float(v[2]), float(v[3]) if len(v) > 3 else 0.0))
                    else:
                        setattr(obj.ViewObject, k, v)

            else:
                setattr(obj, prop, val)

        except Exception as e:
            FreeCAD.Console.PrintError(f"Property '{prop}' assignment error: {e}\n")


class FreeCADRPC:
    """RPC server for FreeCAD"""

    def ping(self):
        """Simple ping method to check server status
        
        Returns:
            bool: True if server is running
        """
        return True

    def create_document(self, name="New_Document"):
        """Create a new FreeCAD document
        
        Args:
            name: Name for the new document
            
        Returns:
            Dict with success status and document name or error
        """
        rpc_request_queue.put(lambda: self._create_document_gui(name))
        res = rpc_response_queue.get()
        if res is True:
            return {"success": True, "document_name": name}
        else:
            return {"success": False, "error": res}

    def create_object(self, doc_name, obj_data: Dict[str, Any]):
        """Create a new object in a FreeCAD document
        
        Args:
            doc_name: Name of the document to create the object in
            obj_data: Dictionary with object data
            
        Returns:
            Dict with success status and object name or error
        """
        obj = Object(
            name=obj_data.get("Name", "New_Object"),
            type=obj_data["Type"],
            properties=obj_data.get("Properties", {}),
        )
        rpc_request_queue.put(lambda: self._create_object_gui(doc_name, obj))
        res = rpc_response_queue.get()
        if res is True:
            return {"success": True, "object_name": obj.name}
        else:
            return {"success": False, "error": res}

    def edit_object(self, doc_name: str, obj_name: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Edit an existing object in a FreeCAD document
        
        Args:
            doc_name: Name of the document containing the object
            obj_name: Name of the object to edit
            properties: Dictionary with properties to update
            
        Returns:
            Dict with success status and object name or error
        """
        obj = Object(
            name=obj_name,
            properties=properties.get("Properties", {}),
        )
        rpc_request_queue.put(lambda: self._edit_object_gui(doc_name, obj))
        res = rpc_response_queue.get()
        if res is True:
            return {"success": True, "object_name": obj.name}
        else:
            return {"success": False, "error": res}

    def delete_object(self, doc_name: str, obj_name: str):
        """Delete an object from a FreeCAD document
        
        Args:
            doc_name: Name of the document containing the object
            obj_name: Name of the object to delete
            
        Returns:
            Dict with success status and object name or error
        """
        rpc_request_queue.put(lambda: self._delete_object_gui(doc_name, obj_name))
        res = rpc_response_queue.get()
        if res is True:
            return {"success": True, "object_name": obj_name}
        else:
            return {"success": False, "error": res}

    def execute_code(self, code: str) -> Dict[str, Any]:
        """Execute arbitrary Python code in the FreeCAD context
        
        Args:
            code: Python code to execute
            
        Returns:
            Dict with success status and output or error
        """
        output_buffer = io.StringIO()
        def task():
            try:
                with contextlib.redirect_stdout(output_buffer):
                    exec(code, globals())
                FreeCAD.Console.PrintMessage("Python code executed successfully.\n")
                return True
            except Exception as e:
                FreeCAD.Console.PrintError(
                    f"Error executing Python code: {e}\n"
                )
                return f"Error executing Python code: {e}\n"

        rpc_request_queue.put(task)
        res = rpc_response_queue.get()
        if res is True:
            return {
                "success": True,
                "message": "Python code execution scheduled. \nOutput: " + output_buffer.getvalue()
            }
        else:
            return {"success": False, "error": res}

    def get_objects(self, doc_name):
        """Get all objects in a document
        
        Args:
            doc_name: Name of the document
            
        Returns:
            List of serialized objects
        """
        try:
            doc = FreeCAD.getDocument(doc_name)
            if doc:
                return [serialize_object(obj) for obj in doc.Objects]
            else:
                return []
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error getting objects: {e}\n")
            return []

    def get_object(self, doc_name, obj_name):
        """Get a specific object by name
        
        Args:
            doc_name: Name of the document
            obj_name: Name of the object
            
        Returns:
            Serialized object or None
        """
        try:
            doc = FreeCAD.getDocument(doc_name)
            if doc:
                obj = doc.getObject(obj_name)
                if obj:
                    return serialize_object(obj)
            return None
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error getting object: {e}\n")
            return None

    def list_documents(self):
        """List all open documents
        
        Returns:
            List of document names
        """
        return list(FreeCAD.listDocuments().keys())

    def get_active_screenshot(self, view_name: str = "Isometric") -> str:
        """Get a screenshot of the active view
        
        Args:
            view_name: Name of the view to capture
            
        Returns:
            Base64 encoded PNG image
        """
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        rpc_request_queue.put(lambda: self._save_active_screenshot(temp_file.name, view_name))
        res = rpc_response_queue.get()
        if res is True:
            with open(temp_file.name, "rb") as image_file:
                image_bytes = image_file.read()
                os.remove(temp_file.name)
                return base64.b64encode(image_bytes).decode("utf-8")
        else:
            return None

    def recompute_document(self, doc_name: str) -> Dict[str, Any]:
        """Recompute a document
        
        Args:
            doc_name: Name of the document to recompute
            
        Returns:
            Dict with success status and message or error
        """
        rpc_request_queue.put(lambda: self._recompute_document_gui(doc_name))
        res = rpc_response_queue.get()
        if res is True:
            return {"success": True, "message": f"Document '{doc_name}' recomputed."}
        else:
            return {"success": False, "error": res}

    def _create_document_gui(self, name):
        """Create a document in the GUI thread
        
        Args:
            name: Name for the document
            
        Returns:
            True on success, error message on failure
        """
        try:
            doc = FreeCAD.newDocument(name)
            doc.recompute()
            FreeCAD.Console.PrintMessage(f"Document '{name}' created via RPC.\n")
            return True
        except Exception as e:
            return str(e)

    def _create_object_gui(self, doc_name, obj: Object):
        """Create an object in the GUI thread
        
        Args:
            doc_name: Document name
            obj: Object data
            
        Returns:
            True on success, error message on failure
        """
        try:
            doc = FreeCAD.getDocument(doc_name)
            if not doc:
                return f"Document '{doc_name}' not found"

            # Create object based on type
            new_obj = None
            
            # Part objects
            if obj.type.startswith("Part::"):
                if obj.type == "Part::Box":
                    new_obj = doc.addObject("Part::Box", obj.name)
                elif obj.type == "Part::Cylinder":
                    new_obj = doc.addObject("Part::Cylinder", obj.name)
                elif obj.type == "Part::Sphere":
                    new_obj = doc.addObject("Part::Sphere", obj.name)
                elif obj.type == "Part::Cone":
                    new_obj = doc.addObject("Part::Cone", obj.name)
                elif obj.type == "Part::Torus":
                    new_obj = doc.addObject("Part::Torus", obj.name)
                else:
                    new_obj = doc.addObject(obj.type, obj.name)
            # Other object types
            else:
                new_obj = doc.addObject(obj.type, obj.name)
            
            if not new_obj:
                return f"Failed to create object of type '{obj.type}'"
            
            # Set properties
            set_object_property(doc, new_obj, obj.properties)
            
            # Recompute
            doc.recompute()
            FreeCAD.Console.PrintMessage(f"Object '{obj.name}' created via RPC.\n")
            return True
        except Exception as e:
            return str(e)

    def _edit_object_gui(self, doc_name: str, obj: Object):
        """Edit an object in the GUI thread
        
        Args:
            doc_name: Document name
            obj: Object data
            
        Returns:
            True on success, error message on failure
        """
        try:
            doc = FreeCAD.getDocument(doc_name)
            if not doc:
                return f"Document '{doc_name}' not found"
            
            fc_obj = doc.getObject(obj.name)
            if not fc_obj:
                return f"Object '{obj.name}' not found in document '{doc_name}'"
            
            # Set properties
            set_object_property(doc, fc_obj, obj.properties)
            
            # Recompute
            doc.recompute()
            FreeCAD.Console.PrintMessage(f"Object '{obj.name}' updated via RPC.\n")
            return True
        except Exception as e:
            return str(e)

    def _delete_object_gui(self, doc_name: str, obj_name: str):
        """Delete an object in the GUI thread
        
        Args:
            doc_name: Document name
            obj_name: Object name
            
        Returns:
            True on success, error message on failure
        """
        try:
            doc = FreeCAD.getDocument(doc_name)
            if not doc:
                return f"Document '{doc_name}' not found"
            
            obj = doc.getObject(obj_name)
            if not obj:
                return f"Object '{obj_name}' not found in document '{doc_name}'"
            
            doc.removeObject(obj_name)
            doc.recompute()
            FreeCAD.Console.PrintMessage(f"Object '{obj_name}' deleted via RPC.\n")
            return True
        except Exception as e:
            return str(e)

    def _save_active_screenshot(self, save_path: str, view_name: str = "Isometric"):
        """Save a screenshot of the active view
        
        Args:
            save_path: Path to save the screenshot
            view_name: Name of the view to capture
            
        Returns:
            True on success, error message on failure
        """
        try:
            if not FreeCADGui.ActiveDocument:
                return "No active document"
            
            # Get view
            mw = FreeCADGui.getMainWindow()
            view = None
            
            # Find 3D view
            for child in mw.findChildren():
                if "View3DInventor" in child.metaObject().className():
                    view = child
                    break
            
            if not view:
                return "Could not find 3D view"
            
            # Set view direction
            if view_name.lower() == "top":
                view.viewTop()
            elif view_name.lower() == "bottom":
                view.viewBottom()
            elif view_name.lower() == "front":
                view.viewFront()
            elif view_name.lower() == "rear":
                view.viewRear()
            elif view_name.lower() == "right":
                view.viewRight()
            elif view_name.lower() == "left":
                view.viewLeft()
            elif view_name.lower() == "isometric":
                view.viewIsometric()
            
            # Capture image
            view.grabFramebuffer().save(save_path)
            return True
        except Exception as e:
            return str(e)
            
    def _recompute_document_gui(self, doc_name: str):
        """Recompute a document in the GUI thread
        
        Args:
            doc_name: Document name
            
        Returns:
            True on success, error message on failure
        """
        try:
            doc = FreeCAD.getDocument(doc_name)
            if not doc:
                return f"Document '{doc_name}' not found"
            
            doc.recompute()
            FreeCAD.Console.PrintMessage(f"Document '{doc_name}' recomputed via RPC.\n")
            return True
        except Exception as e:
            return str(e)


def start_rpc_server(host="localhost", port=9875):
    """Start the RPC server
    
    Args:
        host: Host to bind to
        port: Port to bind to
        
    Returns:
        True if server started successfully, False otherwise
    """
    global rpc_server_thread, rpc_server_instance
    
    if rpc_server_thread is not None:
        FreeCAD.Console.PrintWarning("RPC server is already running\n")
        return False
    
    # Start request queue processing
    QTimer.singleShot(100, process_gui_tasks)
    
    def server_loop():
        global rpc_server_instance
        try:
            server = SimpleXMLRPCServer((host, port), allow_none=True)
            server.register_instance(FreeCADRPC())
            rpc_server_instance = server
            FreeCAD.Console.PrintMessage(f"RPC server running at http://{host}:{port}\n")
            server.serve_forever()
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error starting RPC server: {e}\n")
    
    rpc_server_thread = threading.Thread(target=server_loop, daemon=True)
    rpc_server_thread.start()
    
    return True


def stop_rpc_server():
    """Stop the RPC server
    
    Returns:
        True if server stopped successfully, False otherwise
    """
    global rpc_server_thread, rpc_server_instance
    
    if rpc_server_thread is None or rpc_server_instance is None:
        FreeCAD.Console.PrintWarning("RPC server is not running\n")
        return False
    
    try:
        rpc_server_instance.shutdown()
        rpc_server_thread.join(timeout=2.0)
        rpc_server_thread = None
        rpc_server_instance = None
        FreeCAD.Console.PrintMessage("RPC server stopped\n")
        return True
    except Exception as e:
        FreeCAD.Console.PrintError(f"Error stopping RPC server: {e}\n")
        return False


class StartRPCServerCommand:
    """Command to start the RPC server"""
    
    def GetResources(self):
        return {"MenuText": "Start RPC Server", "ToolTip": "Start XML-RPC Server for remote control"}
    
    def Activated(self):
        start_rpc_server()
    
    def IsActive(self):
        return rpc_server_thread is None


class StopRPCServerCommand:
    """Command to stop the RPC server"""
    
    def GetResources(self):
        return {"MenuText": "Stop RPC Server", "ToolTip": "Stop XML-RPC Server"}
    
    def Activated(self):
        stop_rpc_server()
    
    def IsActive(self):
        return rpc_server_thread is not None