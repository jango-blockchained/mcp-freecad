#!/usr/bin/env python3
"""
FreeCAD Script

This script is meant to be run inside FreeCAD's Python interpreter to perform operations.
It avoids the module initialization issues.
"""

import sys
import os
import json

# FreeCAD modules are already loaded when running inside FreeCAD
import FreeCAD
import Part

# If running in GUI mode, import GUI modules
try:
    import FreeCADGui
    GUI_MODE = True
except ImportError:
    GUI_MODE = False

def create_document(name="Unnamed"):
    """Create a new document"""
    doc = FreeCAD.newDocument(name)
    return doc.Name

def create_box(length=10.0, width=10.0, height=10.0, doc_name=None):
    """Create a box in a document"""
    if doc_name:
        doc = FreeCAD.getDocument(doc_name)
    else:
        if FreeCAD.ActiveDocument:
            doc = FreeCAD.ActiveDocument
        else:
            doc = FreeCAD.newDocument("Unnamed")

    # Create a box
    box = doc.addObject("Part::Box", "Box")
    box.Length = length
    box.Width = width
    box.Height = height

    # Recompute the document
    doc.recompute()

    return box.Name

def export_stl(obj_name, file_path, doc_name=None):
    """Export an object to STL format"""
    if doc_name:
        doc = FreeCAD.getDocument(doc_name)
    else:
        if FreeCAD.ActiveDocument:
            doc = FreeCAD.ActiveDocument
        else:
            return False

    obj = doc.getObject(obj_name)
    if not obj:
        return False

    # Export to STL
    import Mesh
    stl_mesh = Mesh.Mesh()
    stl_mesh.addFacets(obj.Shape.tessellate(0.1))
    stl_mesh.write(file_path)

    return os.path.exists(file_path)

def get_version():
    """Get FreeCAD version information"""
    version_info = {
        "version": list(FreeCAD.Version),
        "build_date": FreeCAD.BuildDate if hasattr(FreeCAD, "BuildDate") else "Unknown",
        "gui_available": GUI_MODE
    }
    return version_info

def main():
    """Main function to execute commands from arguments"""
    # --- Remove Debug Print ---
    # print(f"DEBUG freecad_script.py sys.argv: {sys.argv}", file=sys.stderr)
    # -----------------------

    # Check for command line arguments
    if len(sys.argv) < 2:
        print("No command specified")
        return 1

    # Get the command from the first argument
    command = sys.argv[1]

    # Parse the parameters if provided
    params = {}
    if len(sys.argv) >= 3:
        try:
            params = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            print("Invalid parameters format")
            return 1

    # Execute the command
    result = {"success": False}

    if command == "get_version":
        result = get_version()
        result["success"] = True

    elif command == "create_document":
        name = params.get("name", "Unnamed")
        doc_name = create_document(name)
        result = {
            "success": True,
            "document_name": doc_name
        }

    elif command == "create_box":
        length = params.get("length", 10.0)
        width = params.get("width", 10.0)
        height = params.get("height", 10.0)
        doc_name = params.get("document")

        box_name = create_box(length, width, height, doc_name)
        result = {
            "success": True,
            "box_name": box_name,
            "document": doc_name or (FreeCAD.ActiveDocument.Name if FreeCAD.ActiveDocument else "Unnamed")
        }

    elif command == "export_stl":
        obj_name = params.get("object")
        file_path = params.get("path")
        doc_name = params.get("document")

        if not obj_name or not file_path:
            result = {
                "success": False,
                "error": "Missing object name or file path"
            }
        else:
            success = export_stl(obj_name, file_path, doc_name)
            result = {
                "success": success,
                "path": file_path if success else None
            }

    else:
        result = {
            "success": False,
            "error": f"Unknown command: {command}"
        }

    # Print the result as JSON
    print(json.dumps(result))
    return 0

if __name__ == "__main__":
    sys.exit(main())
