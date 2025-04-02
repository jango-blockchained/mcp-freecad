#!/usr/bin/env python3
"""
FreeCAD Integration Demo

This script demonstrates how to use the FreeCAD bridge module to
create and manipulate FreeCAD objects from a regular Python script.
"""

import os
import sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import FreeCAD
import Mesh
import Part

# Now imports should work
from freecad_bridge import FreeCADBridge


def main():
    """Main function to demonstrate FreeCAD bridge usage"""
    print("FreeCAD Integration Demo")
    print("-----------------------")

    # Create a bridge instance
    # If FreeCAD is in a non-standard location, specify the path:
    # bridge = FreeCADBridge("/path/to/freecad")
    bridge = FreeCADBridge()

    # Check if FreeCAD is available
    if not bridge.is_available():
        print("Error: FreeCAD is not available.")
        print("Please make sure FreeCAD is installed and accessible in your PATH.")
        sys.exit(1)

    # Get FreeCAD version information
    print("\nChecking FreeCAD version...")
    version_info = bridge.get_version()
    if not version_info.get("success", False):
        print(f"Error: Failed to get FreeCAD version - {version_info.get('error')}")
        sys.exit(1)

    print(f"FreeCAD version: {'.'.join(version_info['version'][0:3])}")
    print(f"Build date: {version_info['build_date']}")

    # Create operations
    try:
        # Create a new document
        print("\nCreating a new document...")
        doc_name = bridge.create_document("MCP_Demo")
        print(f"Created document: {doc_name}")

        # Create a box
        print("\nCreating a box...")
        box_name = bridge.create_box(
            length=100.0, width=50.0, height=25.0, doc_name=doc_name
        )
        print(f"Created box: {box_name}")

        # Export to STL
        print("\nExporting to STL...")
        stl_path = os.path.join(os.getcwd(), "mcp_demo_box.stl")
        if bridge.export_stl(box_name, stl_path, doc_name):
            print(f"Successfully exported STL to: {stl_path}")
        else:
            print(f"Failed to export STL")

    except Exception as e:
        print(f"Error during FreeCAD operations: {e}")
        sys.exit(1)

    print("\nAll operations completed successfully!")


if __name__ == "__main__":
    main()
