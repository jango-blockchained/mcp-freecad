#!/usr/bin/env python3
"""
FreeCAD Subprocess Loader

This script loads FreeCAD in a separate Python process to avoid initialization issues.
It communicates with the main process via pipes.
"""

import os
import sys
import json
import traceback

# REMOVED: Hardcoded path assumption - rely on environment (e.g., AppRun setup)
# freecad_module_path = "/usr/lib/freecad-python3/lib"
# if os.path.exists(freecad_module_path):
#     sys.path.append(freecad_module_path)

try:
    import FreeCAD

    print("Successfully imported FreeCAD")
    print(f"FreeCAD Version: {FreeCAD.Version}")
    print(f"FreeCAD Build Date: {FreeCAD.BuildDate}")
    print(f"FreeCAD module location: {FreeCAD.__file__}")

    # Try to import FreeCADGui
    try:
        import FreeCADGui

        print("Successfully imported FreeCADGui")
        gui_available = True
    except ImportError as e:
        print(f"FreeCADGui not available: {e}")
        gui_available = False

    # Main command processing loop
    while True:
        try:
            # Read a command from stdin
            line = sys.stdin.readline()
            if not line:
                # End of stream
                break

            # Parse the command
            command = json.loads(line)
            cmd_type = command.get("type")
            params = command.get("params", {})

            # Process the command
            result = {"success": True}

            if cmd_type == "ping":
                result["pong"] = True
                result["freecad_version"] = list(FreeCAD.Version)
                result["gui_available"] = gui_available

            elif cmd_type == "get_version":
                result["version"] = list(FreeCAD.Version)
                result["build_date"] = FreeCAD.BuildDate
                result["gui_available"] = gui_available

            elif cmd_type == "create_document":
                name = params.get("name", "Unnamed")
                doc = FreeCAD.newDocument(name)
                result["document_name"] = doc.Name

            elif cmd_type == "create_object":
                doc_name = params.get("document")
                obj_type = params.get("type")
                obj_name = params.get("name", "")
                properties = params.get("properties", {})

                # Get the document
                if doc_name:
                    doc = FreeCAD.getDocument(doc_name)
                else:
                    doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("Unnamed")

                # Create the object
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
                    result["success"] = False
                    result["error"] = f"Unsupported object type: {obj_type}"

                if result["success"]:
                    # Apply other properties
                    for prop, value in properties.items():
                        if prop not in [
                            "length",
                            "width",
                            "height",
                            "radius",
                        ] and hasattr(obj, prop):
                            setattr(obj, prop, value)

                    # Recompute the document
                    doc.recompute()

                    result["object"] = {
                        "name": obj.Name,
                        "label": obj.Label,
                        "type": obj.TypeId,
                    }

            # Send the result back
            sys.stdout.write(json.dumps(result) + "\n")
            sys.stdout.flush()

        except Exception as e:
            # Send error back
            error_result = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
            sys.stdout.write(json.dumps(error_result) + "\n")
            sys.stdout.flush()

except ImportError as e:
    # Report import error
    print(f"Failed to import FreeCAD: {e}")
    print(f"Python path: {sys.path}")

    # Send an error response
    error_result = {
        "success": False,
        "error": f"Failed to import FreeCAD: {e}",
        "traceback": traceback.format_exc(),
    }
    sys.stdout.write(json.dumps(error_result) + "\n")
    sys.stdout.flush()

    # Exit with error
    sys.exit(1)
