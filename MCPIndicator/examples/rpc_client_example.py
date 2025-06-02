#!/usr/bin/env python3
"""
Example client for the FreeCAD XML-RPC server implementation.

This script demonstrates how to connect to the FreeCAD XML-RPC server
and execute various operations such as:
- Creating documents
- Creating objects
- Modifying objects
- Getting screenshots

Usage:
    python rpc_client_example.py
"""

import sys
import time
import xmlrpc.client
from typing import Any, Dict, List, Optional


def main():
    """Main function that demonstrates XML-RPC client usage."""
    # Connect to the XML-RPC server
    server_url = "http://localhost:9875"
    print(f"Connecting to XML-RPC server at {server_url}...")
    
    try:
        proxy = xmlrpc.client.ServerProxy(server_url, allow_none=True)
        
        # Test connection with ping
        result = proxy.ping()
        if not result:
            print("ERROR: Server ping failed")
            return 1
        print("Connected to server successfully!")
        
        # Create a new document
        doc_name = f"RPCTest_{int(time.time())}"
        result = proxy.create_document(doc_name)
        if not result.get("success", False):
            print(f"ERROR: Failed to create document: {result.get('error', 'Unknown error')}")
            return 1
        print(f"Created document: {doc_name}")
        
        # Add a box
        box_data = {
            "Name": "Box001",
            "Type": "Part::Box",
            "Properties": {
                "Length": 20.0,
                "Width": 20.0,
                "Height": 20.0,
                "Label": "My Box",
                "ViewObject": {
                    "ShapeColor": (1.0, 0.0, 0.0, 0.0)  # Red
                }
            }
        }
        
        result = proxy.create_object(doc_name, box_data)
        if not result.get("success", False):
            print(f"ERROR: Failed to create box: {result.get('error', 'Unknown error')}")
            return 1
        print(f"Created box: {result.get('object_name')}")
        
        # Add a sphere
        sphere_data = {
            "Name": "Sphere001",
            "Type": "Part::Sphere",
            "Properties": {
                "Radius": 15.0,
                "Label": "My Sphere",
                "Placement": {
                    "Base": {"x": 40.0, "y": 0.0, "z": 0.0},
                    "Rotation": {"Axis": {"x": 0.0, "y": 0.0, "z": 1.0}, "Angle": 0.0}
                },
                "ViewObject": {
                    "ShapeColor": (0.0, 0.0, 1.0, 0.0)  # Blue
                }
            }
        }
        
        result = proxy.create_object(doc_name, sphere_data)
        if not result.get("success", False):
            print(f"ERROR: Failed to create sphere: {result.get('error', 'Unknown error')}")
            return 1
        print(f"Created sphere: {result.get('object_name')}")
        
        # Recompute the document
        result = proxy.recompute_document(doc_name)
        if not result.get("success", False):
            print(f"ERROR: Failed to recompute document: {result.get('error', 'Unknown error')}")
            return 1
        print("Document recomputed successfully!")
        
        # Modify the box
        edit_data = {
            "Properties": {
                "Length": 30.0,
                "Width": 15.0,
                "Height": 25.0,
                "ViewObject": {
                    "ShapeColor": (0.0, 1.0, 0.0, 0.0)  # Green
                }
            }
        }
        
        result = proxy.edit_object(doc_name, "Box001", edit_data)
        if not result.get("success", False):
            print(f"ERROR: Failed to edit box: {result.get('error', 'Unknown error')}")
            return 1
        print("Box modified successfully!")
        
        # List all objects in the document
        objects = proxy.get_objects(doc_name)
        print(f"Document contains {len(objects)} objects:")
        for obj in objects:
            print(f"  - {obj['Name']} ({obj['TypeId']})")
        
        # Take a screenshot
        print("Taking a screenshot of the model...")
        screenshot = proxy.get_active_screenshot()
        if screenshot:
            import base64
            screenshot_file = f"{doc_name}_screenshot.png"
            with open(screenshot_file, "wb") as f:
                f.write(base64.b64decode(screenshot))
            print(f"Screenshot saved to {screenshot_file}")
        else:
            print("ERROR: Failed to take screenshot")
        
        # Execute some Python code
        code = """
import FreeCAD
doc = FreeCAD.ActiveDocument
print("Active document: " + doc.Name)
print("Object count: " + str(len(doc.Objects)))
for obj in doc.Objects:
    print(" - " + obj.Name + ": " + obj.TypeId)
"""
        
        result = proxy.execute_code(code)
        if not result.get("success", False):
            print(f"ERROR: Failed to execute code: {result.get('error', 'Unknown error')}")
            return 1
        print(f"Python code execution result: {result.get('message', '')}")
        
        # Delete the sphere
        result = proxy.delete_object(doc_name, "Sphere001")
        if not result.get("success", False):
            print(f"ERROR: Failed to delete sphere: {result.get('error', 'Unknown error')}")
            return 1
        print("Sphere deleted successfully!")
        
        print("\nAll operations completed successfully!")
        return 0
        
    except ConnectionRefusedError:
        print("ERROR: Connection refused. Make sure the RPC server is running.")
        return 1
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())