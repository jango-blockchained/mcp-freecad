#!/usr/bin/env python3
"""
FreeCAD Wrapper

This script provides a wrapper for the FreeCAD subprocess allowing easy communication
with the FreeCAD functionality without mocking.
"""

import json
import logging
import os
import subprocess
import time
import traceback
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FreeCADWrapper:
    """Wrapper for FreeCAD functionality via subprocess communication"""

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.process = None
        self.connected = False
        self.version_info = None

    def log(self, message: str) -> None:
        """Log a message if debug is enabled"""
        if self.debug:
            print(f"[FreeCAD Wrapper] {message}")

    def start(self) -> bool:
        """Start the FreeCAD subprocess"""
        try:
            self.log("Starting FreeCAD subprocess")

            # Check if the subprocess script exists
            subprocess_script = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "freecad_subprocess.py"
            )

            if not os.path.exists(subprocess_script):
                self.log(f"Error: Subprocess script not found at {subprocess_script}")
                return False

            # Start the subprocess with pipes for communication
            self.process = subprocess.Popen(
                ["python3", subprocess_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )

            # Give the subprocess time to initialize
            time.sleep(0.5)

            # Check if process is still running
            if self.process.poll() is not None:
                # Process has terminated, read error output
                stderr = self.process.stderr.read()
                self.log(f"FreeCAD subprocess failed to start: {stderr}")
                return False

            # Ping to test connection
            result = self.send_command("ping", {})

            if result and result.get("pong"):
                self.connected = True
                self.version_info = {
                    "version": result.get("freecad_version", ["unknown"]),
                    "gui_available": result.get("gui_available", False),
                }
                self.log(f"Connected to FreeCAD version {self.version_info['version']}")
                return True
            else:
                self.log("Failed to connect to FreeCAD subprocess")
                return False

        except Exception as e:
            self.log(f"Error starting FreeCAD subprocess: {e}")
            traceback.print_exc()
            return False

    def stop(self) -> None:
        """Stop the FreeCAD subprocess"""
        if self.process:
            try:
                self.log("Stopping FreeCAD subprocess")
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.log("FreeCAD subprocess did not terminate, killing")
                self.process.kill()
            finally:
                self.process = None
                self.connected = False

    def send_command(
        self, cmd_type: str, params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Send a command to the FreeCAD subprocess and get the result"""
        if not self.process or not self.connected:
            self.log("Not connected to FreeCAD subprocess")
            return {"error": "Not connected to FreeCAD"}

        try:
            # Check if process is still running
            if self.process.poll() is not None:
                self.connected = False
                stderr = (
                    self.process.stderr.read()
                    if self.process.stderr
                    else "No stderr output"
                )
                self.log(
                    f"FreeCAD subprocess has terminated unexpectedly. Exit code: {self.process.returncode}. Stderr: {stderr}"
                )
                return {
                    "error": f"FreeCAD subprocess has terminated. Exit code: {self.process.returncode}"
                }

            # Prepare the command
            command = {"type": cmd_type, "params": params}

            # Send the command
            command_json = json.dumps(command) + "\n"
            self.log(f"Sending command: {command_json.strip()}")
            self.process.stdin.write(command_json)
            self.process.stdin.flush()

            # Read the response with timeout
            response_line = None
            start_time = time.time()
            timeout = 60  # seconds

            while time.time() - start_time < timeout:
                # Check if process is still alive
                if self.process.poll() is not None:
                    self.connected = False
                    stderr = (
                        self.process.stderr.read()
                        if self.process.stderr
                        else "No stderr output"
                    )
                    self.log(
                        f"FreeCAD subprocess terminated during command. Exit code: {self.process.returncode}. Stderr: {stderr}"
                    )
                    return {
                        "error": f"FreeCAD subprocess terminated during command. Exit code: {self.process.returncode}"
                    }

                # Check if there's data to read (non-blocking)
                import select

                rlist, _, _ = select.select([self.process.stdout], [], [], 0.1)
                if rlist:
                    response_line = self.process.stdout.readline()
                    if response_line:
                        break

            if not response_line:
                self.log(f"No response from FreeCAD subprocess after {timeout} seconds")
                # Try to read any error output
                stderr = ""
                try:
                    rlist, _, _ = select.select([self.process.stderr], [], [], 0.1)
                    if rlist:
                        stderr = self.process.stderr.read()
                except Exception:
                    pass

                return {
                    "error": f"No response from FreeCAD subprocess after {timeout} seconds",
                    "stderr": stderr,
                }

            # Parse the response
            self.log(f"Received response: {response_line.strip()}")
            try:
                response = json.loads(response_line)
                return response
            except json.JSONDecodeError as e:
                self.log(f"Failed to parse JSON response: {response_line.strip()}")
                return {
                    "error": f"Invalid JSON response: {str(e)}",
                    "raw_response": response_line.strip(),
                }

        except Exception as e:
            self.log(
                f"Error sending command to FreeCAD subprocess: {type(e).__name__}: {e}"
            )
            # Try to check if the process is still running
            if self.process and self.process.poll() is not None:
                self.connected = False
                self.log(
                    f"Process has terminated. Exit code: {self.process.returncode}"
                )

            return {
                "error": f"Command error: {type(e).__name__}: {str(e)}",
                "traceback": traceback.format_exc(),
            }

    def create_document(self, name: str = "Unnamed") -> Dict[str, Any]:
        """Create a new FreeCAD document"""
        return self.send_command("create_document", {"name": name})

    def create_object(
        self,
        obj_type: str,
        obj_name: str = "",
        doc_name: str = None,
        properties: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Create a new object in a FreeCAD document"""
        if properties is None:
            properties = {}

        params = {"type": obj_type, "name": obj_name, "properties": properties}

        if doc_name:
            params["document"] = doc_name

        return self.send_command("create_object", params)

    def get_version(self) -> Dict[str, Any]:
        """Get FreeCAD version information"""
        return self.send_command("get_version", {})

    def __enter__(self):
        """Context manager enter"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


if __name__ == "__main__":
    # Test the wrapper
    with FreeCADWrapper(debug=True) as freecad:
        if freecad.connected:
            print("FreeCAD connected!")

            # Get version
            version = freecad.get_version()
            print(f"FreeCAD Version: {version}")

            # Create a document
            doc_result = freecad.create_document("TestDoc")
            print(f"Create document result: {doc_result}")

            # Create a box
            box_result = freecad.create_object(
                "box",
                "TestBox",
                "TestDoc",
                {"length": 10.0, "width": 20.0, "height": 30.0},
            )
            print(f"Create box result: {box_result}")
        else:
            print("Failed to connect to FreeCAD")
