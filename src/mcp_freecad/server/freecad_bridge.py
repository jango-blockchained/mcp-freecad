#!/usr/bin/env python3
"""
FreeCAD Bridge Module

This module provides a bridge between Python scripts and FreeCAD,
allowing execution of FreeCAD commands without directly importing
the FreeCAD modules.

Usage:
    from freecad_connection_bridge import FreeCADBridge

    # Create a bridge instance
    fc = FreeCADBridge()

    # Check if FreeCAD is available
    if fc.is_available():
        # Get FreeCAD version
        version = fc.get_version()
        print(f"FreeCAD version: {version}")

        # Create a document and a box
        doc_name = fc.create_document("MyDocument")
        box = fc.create_box(10, 20, 30)

        # Export to STL
        fc.export_stl(box, "my_box.stl")
"""

import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, Optional, Tuple


class FreeCADBridge:
    """A bridge for executing FreeCAD commands from Python scripts"""

    def __init__(self, freecad_path: str = "freecad"):
        """
        Initialize the FreeCAD bridge

        Args:
            freecad_path: Path to the FreeCAD executable (default: 'freecad')
        """
        self.freecad_path = freecad_path
        self._version = None
        self._available = None

    def is_available(self) -> bool:
        """Check if FreeCAD is available"""
        if self._available is not None:
            return self._available

        try:
            result = subprocess.run(
                [self.freecad_path, "--version"], capture_output=True, text=True
            )
            self._available = result.returncode == 0
            return self._available
        except (FileNotFoundError, subprocess.SubprocessError):
            self._available = False
            return False

    def run_script(self, script_content: str) -> Tuple[str, str]:
        """
        Run a Python script in FreeCAD

        Args:
            script_content: The Python script to run

        Returns:
            Tuple of (stdout, stderr)
        """
        # Create a temporary script
        fd, temp_path = tempfile.mkstemp(suffix=".py")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(script_content)

            # Run the script with FreeCAD
            process = subprocess.run(
                [self.freecad_path, "-c", temp_path], capture_output=True, text=True
            )

            return process.stdout, process.stderr
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def get_version(self) -> Dict[str, Any]:
        """
        Get the FreeCAD version

        Returns:
            Dictionary with version information
        """
        if self._version is not None:
            return self._version

        script = """
import json
import FreeCAD
print(json.dumps({
    "version": FreeCAD.Version,
    "build_date": FreeCAD.BuildDate,
    "success": True
}))
"""

        stdout, stderr = self.run_script(script)

        try:
            # Find the JSON output in stdout
            for line in stdout.strip().split("\n"):
                if line.startswith("{") and line.endswith("}"):
                    self._version = json.loads(line)
                    return self._version

            return {"success": False, "error": "No valid JSON output"}
        except json.JSONDecodeError:
            return {"success": False, "error": f"Failed to parse JSON: {stdout}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_document(self, name: str) -> str:
        """
        Create a new FreeCAD document

        Args:
            name: The name for the new document

        Returns:
            The name of the created document
        """
        script = f"""
import json
import FreeCAD
doc = FreeCAD.newDocument("{name}")
print(json.dumps({{"name": doc.Name, "success": True}}))
"""

        stdout, stderr = self.run_script(script)

        try:
            for line in stdout.strip().split("\n"):
                if line.startswith("{") and line.endswith("}"):
                    result = json.loads(line)
                    if result.get("success"):
                        return result.get("name")

            raise RuntimeError(f"Failed to create document: {stderr}")
        except Exception as e:
            raise RuntimeError(f"Error creating document: {e}")

    def create_box(
        self,
        length: float = 10.0,
        width: float = 10.0,
        height: float = 10.0,
        doc_name: Optional[str] = None,
    ) -> str:
        """
        Create a box in a FreeCAD document

        Args:
            length: Length of the box
            width: Width of the box
            height: Height of the box
            doc_name: Name of the document (creates a new one if None)

        Returns:
            The name of the created box object
        """
        doc_creation = (
            'doc = FreeCAD.newDocument("BoxDocument")'
            if doc_name is None
            else f'doc = FreeCAD.getDocument("{doc_name}")'
        )

        script = f"""
import json
import FreeCAD
import Part

# Get or create document
{doc_creation}

# Create box
box = doc.addObject("Part::Box", "Box")
box.Length = {length}
box.Width = {width}
box.Height = {height}

# Recompute
doc.recompute()

# Return info
print(json.dumps({{
    "name": box.Name,
    "document": doc.Name,
    "dimensions": {{"length": box.Length, "width": box.Width, "height": box.Height}},
    "success": True
}}))
"""

        stdout, stderr = self.run_script(script)

        try:
            for line in stdout.strip().split("\n"):
                if line.startswith("{") and line.endswith("}"):
                    result = json.loads(line)
                    if result.get("success"):
                        return result.get("name")

            raise RuntimeError("Failed to create box: " + stderr)
        except Exception as e:
            raise RuntimeError(f"Error creating box: {e}")

    def export_stl(
        self, object_name: str, output_path: str, doc_name: Optional[str] = None
    ) -> bool:
        """
        Export an object to STL

        Args:
            object_name: Name of the object to export
            output_path: Path to save the STL file
            doc_name: Name of the document (uses active document if None)

        Returns:
            True if successful
        """
        doc_ref = (
            "doc = FreeCAD.ActiveDocument"
            if doc_name is None
            else f'doc = FreeCAD.getDocument("{doc_name}")'
        )

        script = f"""
import json
import FreeCAD
import Mesh

try:
    # Get document
    {doc_ref}

    # Get object
    obj = doc.getObject("{object_name}")

    # Export to STL
    Mesh.export([obj], "{output_path}")

    print(json.dumps({{"success": True, "path": "{output_path}"}}))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}))
"""

        stdout, stderr = self.run_script(script)

        try:
            for line in stdout.strip().split("\n"):
                if line.startswith("{") and line.endswith("}"):
                    result = json.loads(line)
                    return result.get("success", False)

            return False
        except Exception:
            return False


# Example usage
if __name__ == "__main__":
    # Create a bridge instance
    bridge = FreeCADBridge()

    # Check if FreeCAD is available
    if not bridge.is_available():
        print("FreeCAD is not available. Please install it or check the path.")
        sys.exit(1)

    # Get version
    version_info = bridge.get_version()
    if version_info.get("success"):
        print(f"FreeCAD Version: {version_info.get('version')}")
        print(f"Build Date: {version_info.get('build_date')}")
    else:
        print(f"Failed to get FreeCAD version: {version_info.get('error')}")
        sys.exit(1)

    try:
        # Create a document
        doc_name = bridge.create_document("Example")
        print(f"Created document: {doc_name}")

        # Create a box
        box_name = bridge.create_box(10.0, 20.0, 30.0, doc_name)
        print(f"Created box: {box_name}")

        # Export to STL
        output_file = os.path.join(os.getcwd(), "example_box.stl")
        if bridge.export_stl(box_name, output_file, doc_name):
            print(f"Exported STL to: {output_file}")
        else:
            print("Failed to export STL")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("All operations completed successfully!")
