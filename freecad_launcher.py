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

        # Handle AppRun path detection
        if use_apprun:
            # First, check if the path is directly to AppRun
            if os.path.basename(self.freecad_path) == "AppRun":
                self.apprun_path = self.freecad_path
            else:
                # Then check if AppRun is in the same directory
                potential_apprun = os.path.join(os.path.dirname(self.freecad_path), "AppRun")
                if os.path.exists(potential_apprun):
                    self.apprun_path = potential_apprun
                else:
                    # Finally, check if this is a directory containing AppRun
                    potential_apprun = os.path.join(self.freecad_path, "AppRun")
                    if os.path.exists(potential_apprun):
                        self.apprun_path = potential_apprun
                    else:
                        raise FileNotFoundError(f"AppRun not found at or near {self.freecad_path}. Please specify the correct path.")

            self.log(f"Using AppRun at: {self.apprun_path}")
        else:
            # Check if freecad executable exists
            if not os.path.exists(self.freecad_path):
                raise FileNotFoundError(f"FreeCAD executable not found at {self.freecad_path}")

            self.log(f"Using FreeCAD executable at: {self.freecad_path}")

        self.log(f"Using script: {self.script_path}")

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
            # ---- REVERT TO ORIGINAL COMMAND ----
            cmd = [
                self.apprun_path,      # Use the resolved AppRun path
                self.script_path,      # Script path as direct argument
                "--",                  # Separate script arguments
                command,              # Pass command name as arg to our script
                params_json           # Pass params JSON as arg to our script
            ]
            # ---- END REVERTED COMMAND ----
        else:
            # Standard mode using FreeCAD executable
            # This mode likely needs refinement to work consistently
            cmd = [
                self.freecad_path,     # e.g., /usr/bin/freecad
                "--console",
                self.script_path,
                "--",                 # Separator might be needed depending on FreeCAD version
                command,
                params_json
            ]

        self.log(f"Running command: {' '.join(map(str, cmd))}")

        try:
            # ---> REMOVE Environment Modification <---
            # env = os.environ.copy()
            # env["QT_QPA_PLATFORM"] = "offscreen"
            # self.log(f"Setting QT_QPA_PLATFORM=offscreen")
            # --------------------------------------

            # Run the command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'  # Handle encoding errors gracefully
                # env=env # ---> REMOVE Modified Environment <---
            )

            # Set a timeout for the process
            timeout = 90  # seconds

            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                self.log(f"Command execution timed out after {timeout} seconds")
                return {
                    "success": False,
                    "error": f"Command execution timed out after {timeout} seconds"
                }

            self.log(f"Command executed with return code: {process.returncode}")

            # If we got output on stderr, log it for debugging
            if stderr:
                self.log(f"Command stderr: {stderr}")

            # Check for errors
            if process.returncode != 0:
                self.log(f"Error executing command: {stderr}")
                return {
                    "success": False,
                    "error": f"FreeCAD execution failed with code {process.returncode}",
                    "stderr": stderr
                }

            # Parse the output
            try:
                # Look for JSON output in stdout
                output_lines = stdout.strip().split('\n')

                # Detailed logging for debugging
                if self.debug:
                    self.log(f"Output lines: {len(output_lines)}")
                    for i, line in enumerate(output_lines):
                        self.log(f"Line {i}: {line[:100]}{'...' if len(line) > 100 else ''}")

                # Start from the end to find the last JSON
                for line in reversed(output_lines):
                    line = line.strip()
                    if line and line[0] == '{' and line[-1] == '}':
                        try:
                            result = json.loads(line)
                            self.log(f"Found valid JSON result")
                            return result
                        except json.JSONDecodeError:
                            continue

                # If we didn't find any valid JSON, return the error
                self.log(f"No valid JSON output found")
                self.log(f"Command stdout: {stdout}")
                return {
                    "success": False,
                    "error": "No valid JSON output found in FreeCAD response",
                    "stdout": stdout,
                    "stderr": stderr
                }

            except json.JSONDecodeError as e:
                self.log(f"Error parsing JSON output: {e}")
                return {
                    "success": False,
                    "error": f"Error parsing output: {e}",
                    "stdout": stdout,
                    "stderr": stderr
                }

        except Exception as e:
            self.log(f"Error executing command: {type(e).__name__}: {e}")
            return {
                "success": False,
                "error": f"Error executing command: {type(e).__name__}: {e}"
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
    # print("Testing get_version...")
    # version_info = launcher.get_version()
    # print(f"Version info: {version_info}")

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
