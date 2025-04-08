#!/usr/bin/env python3
"""
FreeCAD Launcher

This script launches FreeCAD with our script to execute commands directly in FreeCAD's
Python interpreter, avoiding module loading issues.

Can use AppRun from an extracted AppImage for better compatibility.
"""

import json
import os
import subprocess
import time
from typing import Dict, Any, Optional

class FreeCADLauncher:
    """Class to launch FreeCAD with scripts"""

    def __init__(self, freecad_path="/usr/bin/freecad", script_path=None, debug=False, use_apprun=False):
        """Initialize the launcher"""
        self.freecad_path = freecad_path
        self.debug = debug
        self.use_apprun = use_apprun

        # Use the provided script path or look in the same directory as this file
        if script_path:
            self.script_path = script_path
        else:
            self.script_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "freecad_script.py"
            )

        # Check if the script exists
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(f"FreeCAD script not found at {self.script_path}")

        # Check if freecad executable or AppRun exists
        if not os.path.exists(self.freecad_path):
            raise FileNotFoundError(f"FreeCAD executable not found at {self.freecad_path}")

        self.log(f"Initialized FreeCAD launcher with executable: {self.freecad_path}")
        self.log(f"Using script: {self.script_path}")
        if use_apprun:
            self.log("Using AppRun mode - treating path as AppImage extraction directory")

    def log(self, message):
        """Log a message if debug is enabled"""
        if self.debug:
            print(f"[FreeCAD Launcher] {message}")

    def execute_command(self, command, params=None):
        """Execute a command in FreeCAD"""
        if params is None:
            params = {}

        # Convert params to JSON string
        params_json = json.dumps(params)

        # Build the command
        if self.use_apprun:
            # If using AppRun from extracted AppImage
            apprun_path = os.path.join(os.path.dirname(self.freecad_path), "AppRun")
            if not os.path.exists(apprun_path):
                # If path is to extraction directory itself, not the freecad binary inside it
                apprun_path = os.path.join(self.freecad_path, "AppRun")
                if not os.path.exists(apprun_path):
                    return {
                        "success": False,
                        "error": f"AppRun not found at {apprun_path}"
                    }

            cmd = [
                apprun_path,
                self.script_path,  # Script path as direct argument
                "--",  # Separate script arguments
                command,
                params_json
            ]
        else:
            # Standard mode using FreeCAD executable
            cmd = [
                self.freecad_path,
                "--console",  # Run in console mode
                self.script_path,  # Script path as direct argument
                "--",  # Separate script arguments
                command,
                params_json
            ]

        self.log(f"Running command: {' '.join(map(str, cmd))}")

        try:
            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=90  # Increase timeout to prevent hanging
            )

            self.log(f"Command executed with return code: {result.returncode}")

            # If we got output on stderr, log it for debugging
            if result.stderr:
                self.log(f"Command stderr: {result.stderr}")

            # Check for errors
            if result.returncode != 0:
                self.log(f"Error executing command: {result.stderr}")
                return {
                    "success": False,
                    "error": f"FreeCAD execution failed with code {result.returncode}",
                    "stderr": result.stderr
                }

            # Parse the output
            try:
                # Look for JSON output in stdout
                output_lines = result.stdout.strip().split('\n')
                for line in reversed(output_lines):  # Start from the end to find the last JSON
                    line = line.strip()
                    if line and line[0] == '{' and line[-1] == '}':
                        try:
                            return json.loads(line)
                        except json.JSONDecodeError:
                            continue

                # If we didn't find any valid JSON, return the error
                self.log(f"No valid JSON output found")
                self.log(f"Command stdout: {result.stdout}")
                return {
                    "success": False,
                    "error": "No valid JSON output found",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }

            except json.JSONDecodeError as e:
                self.log(f"Error parsing JSON output: {e}")
                return {
                    "success": False,
                    "error": f"Error parsing output: {e}",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }

        except subprocess.TimeoutExpired:
            self.log("Command execution timed out")
            return {
                "success": False,
                "error": "Command execution timed out"
            }
        except Exception as e:
            self.log(f"Error executing command: {e}")
            return {
                "success": False,
                "error": f"Error executing command: {e}"
            }

    def get_version(self):
        """Get FreeCAD version"""
        return self.execute_command("get_version")

    def create_document(self, name="Unnamed"):
        """Create a new document"""
        return self.execute_command("create_document", {"name": name})

    def create_box(self, length=10.0, width=10.0, height=10.0, doc_name=None):
        """Create a box"""
        params = {
            "length": length,
            "width": width,
            "height": height
        }

        if doc_name:
            params["document"] = doc_name

        return self.execute_command("create_box", params)

    def export_stl(self, obj_name, file_path, doc_name=None):
        """Export an object to STL"""
        params = {
            "object": obj_name,
            "path": file_path
        }

        if doc_name:
            params["document"] = doc_name

        return self.execute_command("export_stl", params)


# Test function
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test FreeCAD Launcher")
    parser.add_argument("--apprun", action="store_true", help="Use AppRun mode")
    parser.add_argument("--path", default="/usr/bin/freecad", help="Path to FreeCAD or AppImage extraction directory")
    args = parser.parse_args()

    launcher = FreeCADLauncher(
        freecad_path=args.path,
        debug=True,
        use_apprun=args.apprun
    )

    # Test get version
    print("Testing get_version...")
    version_result = launcher.get_version()
    print(f"FreeCAD Version: {version_result}")

    # Only continue if version check was successful
    if version_result.get("success"):
        # Test create document
        print("\nTesting create_document...")
        doc_result = launcher.create_document("TestDoc")
        print(f"Create document result: {doc_result}")

        if doc_result.get("success"):
            doc_name = doc_result.get("document_name")

            # Test create box
            print("\nTesting create_box...")
            box_result = launcher.create_box(10, 20, 30, doc_name)
            print(f"Create box result: {box_result}")

            if box_result.get("success"):
                box_name = box_result.get("box_name")

                # Test export STL
                print("\nTesting export_stl...")
                export_result = launcher.export_stl(
                    box_name,
                    os.path.join(os.getcwd(), "test_export.stl"),
                    doc_name
                )
                print(f"Export result: {export_result}")
    else:
        print("Version check failed, skipping other tests")
