#!/usr/bin/env python3
"""
FreeCAD Client

A client for communicating with FreeCAD using the unified connection interface.
This client can work with the socket-based server, CLI bridge, or mock implementation.
"""

import argparse
import json
import os
import socket
import sys
import textwrap
from typing import Any, Dict, Optional

import requests

# Import the FreeCADConnection class
try:
    from freecad_connection_manager import FreeCADConnection

    UNIFIED_CONNECTION_AVAILABLE = True
except ImportError:
    UNIFIED_CONNECTION_AVAILABLE = False
    print("Warning: FreeCADConnection not found. Using legacy socket connection mode.")
    print(
        "You may need to install the freecad_connection_manager.py module in the same directory."
    )

# Define Gemini API constants
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview:generateContent"


class FreeCADClient:
    """Client for communicating with FreeCAD"""

    def __init__(
        self,
        host="localhost",
        port=12345,
        timeout=10.0,
        freecad_path="freecad",
        connection_method=None,
        auto_connect=True,
    ):
        """
        Initialize the client

        Args:
            host: Server hostname for socket connection
            port: Server port for socket connection
            timeout: Connection timeout in seconds
            freecad_path: Path to FreeCAD executable
            connection_method: Preferred connection method (server, bridge, mock)
            auto_connect: Whether to connect automatically
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.freecad_path = freecad_path
        self.connection_method = connection_method
        self._connection = None
        self._legacy_mode = not UNIFIED_CONNECTION_AVAILABLE

        if auto_connect:
            self.connect()

    def connect(self) -> bool:
        """
        Connect to FreeCAD

        Returns:
            bool: True if successfully connected
        """
        if self._legacy_mode:
            # Legacy mode - no connection is maintained, just success status
            try:
                result = self.ping()
                return result.get("pong", False)
            except (socket.error, json.JSONDecodeError):
                return False
        else:
            # Use unified connection
            try:
                self._connection = FreeCADConnection(
                    host=self.host,
                    port=self.port,
                    freecad_path=self.freecad_path,
                    prefer_method=self.connection_method,
                    auto_connect=True,
                )

                # Check if connection is valid
                if self._connection.is_connected():
                    conn_type = self._connection.get_connection_type()
                    print(f"Connected to FreeCAD using {conn_type} method")
                    return True
                else:
                    print("Failed to establish FreeCAD connection")
                    return False
            except Exception as e:
                print(f"Error establishing connection: {e}")
                return False

    def is_connected(self) -> bool:
        """
        Check if connected to FreeCAD

        Returns:
            bool: True if connected
        """
        if self._legacy_mode:
            # In legacy mode, we always try to connect on demand
            try:
                result = self.ping()
                return result.get("pong", False)
            except (socket.error, json.JSONDecodeError):
                return False
        else:
            return self._connection and self._connection.is_connected()

    def get_connection_type(self) -> Optional[str]:
        """
        Get the current connection type

        Returns:
            str: Connection type (server, bridge, or mock)
        """
        if self._legacy_mode:
            return "legacy_socket"

        return self._connection.get_connection_type() if self._connection else None

    def send_command(self, command_type, params=None):
        """
        Send a command to FreeCAD

        Args:
            command_type: Command type
            params: Command parameters

        Returns:
            dict: Command response
        """
        if params is None:
            params = {}

        if self._legacy_mode:
            # Legacy socket-only implementation
            command = {"type": command_type, "params": params}

            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            try:
                # Connect to server
                sock.connect((self.host, self.port))

                # Send command
                sock.sendall(json.dumps(command).encode() + b"\n")

                # Receive response
                response = sock.recv(8192).decode()

                # Parse response
                result = json.loads(response)

                # Check for FreeCADGui attribute errors and provide more helpful messages
                if (
                    "error" in result
                    and "module 'FreeCADGui' has no attribute" in result["error"]
                ):
                    # Add helpful context to the error message
                    result[
                        "error"
                    ] += "\nThis is likely because the server is running without a GUI environment. "
                    result[
                        "error"
                    ] += "Use the '--connect' flag with the server to connect to a running FreeCAD instance."

                return result
            except socket.timeout:
                return {"error": f"Connection timed out after {self.timeout} seconds"}
            except ConnectionRefusedError:
                return {
                    "error": f"Connection refused. Is the FreeCAD server running on {self.host}:{self.port}?"
                }
            except Exception as e:
                return {"error": f"Error communicating with FreeCAD server: {str(e)}"}
            finally:
                sock.close()
        else:
            # Use unified connection
            if not self._connection:
                return {"error": "Not connected to FreeCAD"}

            result = self._connection.execute_command(command_type, params)

            # Check for FreeCADGui attribute errors and provide more helpful messages
            if (
                "error" in result
                and "module 'FreeCADGui' has no attribute" in result["error"]
            ):
                # Add helpful context to the error message
                result[
                    "error"
                ] += "\nThis is likely because the server is running without a GUI environment. "
                result[
                    "error"
                ] += "Use the '--connect' flag with the server to connect to a running FreeCAD instance."

            return result

    def ping(self):
        """Ping the server to check if it's responsive"""
        return self.send_command("ping")

    def get_version(self):
        """Get FreeCAD version information"""
        return self.send_command("get_version")

    def get_model_info(self, document=None):
        """Get information about the current model"""
        params = {}
        if document:
            params["document"] = document

        return self.send_command("get_model_info", params)

    def create_document(self, name="Unnamed"):
        """
        Create a new document

        Args:
            name: Document name

        Returns:
            dict: Response with document info
        """
        return self.send_command("create_document", {"name": name})

    def close_document(self, name=None):
        """Close a document"""
        params = {}
        if name:
            params["name"] = name

        return self.send_command("close_document", params)

    def create_box(
        self, length=10.0, width=10.0, height=10.0, document=None, name=None
    ):
        """Create a box primitive"""
        params = {
            "type": "box",
            "properties": {"length": length, "width": width, "height": height},
        }

        if document:
            params["document"] = document

        if name:
            params["name"] = name

        return self.send_command("create_object", params)

    def create_cylinder(self, radius=5.0, height=10.0, document=None, name=None):
        """Create a cylinder primitive"""
        params = {
            "type": "cylinder",
            "properties": {"radius": radius, "height": height},
        }

        if document:
            params["document"] = document

        if name:
            params["name"] = name

        return self.send_command("create_object", params)

    def create_sphere(self, radius=5.0, document=None, name=None):
        """Create a sphere primitive"""
        params = {"type": "sphere", "properties": {"radius": radius}}

        if document:
            params["document"] = document

        if name:
            params["name"] = name

        return self.send_command("create_object", params)

    def modify_object(self, object_name, properties, document=None):
        """Modify an existing object"""
        params = {"object": object_name, "properties": properties}

        if document:
            params["document"] = document

        return self.send_command("modify_object", params)

    def delete_object(self, object_name, document=None):
        """Delete an object"""
        params = {"object": object_name}

        if document:
            params["document"] = document

        return self.send_command("delete_object", params)

    def execute_script(self, script):
        """Execute a Python script in FreeCAD context"""
        return self.send_command("execute_script", {"script": script})

    def measure_distance(self, from_point, to_point):
        """Measure distance between two points"""
        params = {"from": from_point, "to": to_point}

        return self.send_command("measure_distance", params)

    def export_document(self, file_path, file_type="step", document=None):
        """Export document to a file"""
        params = {"path": file_path, "type": file_type}

        if document:
            params["document"] = document

        return self.send_command("export_document", params)

    def close(self):
        """Close the connection if using unified connection"""
        if not self._legacy_mode and self._connection:
            self._connection.close()
            self._connection = None


def call_gemini_api(api_key: str, prompt: str) -> Dict[str, Any]:
    """
    Call the Google Gemini API with the given prompt.

    Args:
        api_key: Google Gemini API key
        prompt: User prompt text

    Returns:
        Dict containing the API response
    """
    headers = {
        "Content-Type": "application/json",
    }

    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "topP": 0.8, "topK": 40},
    }

    response = requests.post(
        f"{GEMINI_API_URL}?key={api_key}", headers=headers, json=data
    )

    if response.status_code != 200:
        print(f"Error calling Gemini API: {response.status_code}")
        print(response.text)
        return {"error": f"API error: {response.status_code}"}

    return response.json()


def extract_freecad_commands(gemini_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract FreeCAD commands from Gemini's response.

    Args:
        gemini_response: Response from Gemini API

    Returns:
        Dict with parsed commands or error
    """
    try:
        # Extract the text from Gemini's response
        if "candidates" not in gemini_response or not gemini_response["candidates"]:
            return {"error": "No response from Gemini API"}

        text = gemini_response["candidates"][0]["content"]["parts"][0]["text"]

        # Look for code blocks that might contain commands
        if "```" in text:
            # Extract code between triple backticks
            code_blocks = text.split("```")
            # Code blocks are at odd indices (1, 3, 5, etc.)
            commands_text = "\n".join(
                [code_blocks[i] for i in range(1, len(code_blocks), 2)]
            )
        else:
            # If no code blocks, use the whole text
            commands_text = text

        # Parse and identify the command type and parameters
        lines = commands_text.strip().split("\n")
        command_parts = {}

        # Simple parsing - look for keywords that might indicate commands
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Try to determine the command type
            if any(
                keyword in line.lower()
                for keyword in ["create_document", "new document"]
            ):
                command_parts["type"] = "create-document"
                # Try to extract document name
                if "name" not in command_parts and ":" in line:
                    name = line.split(":", 1)[1].strip().strip("\"'")
                    command_parts["name"] = name

            elif any(
                keyword in line.lower() for keyword in ["create_box", "box", "cube"]
            ):
                command_parts["type"] = "create-box"
                # Look for dimensions
                if "length" in line.lower():
                    try:
                        command_parts["length"] = float(line.split("=")[1].strip())
                    except Exception:
                        pass
                if "width" in line.lower():
                    try:
                        command_parts["width"] = float(line.split("=")[1].strip())
                    except Exception:
                        pass
                if "height" in line.lower():
                    try:
                        command_parts["height"] = float(line.split("=")[1].strip())
                    except Exception:
                        pass

            elif any(
                keyword in line.lower() for keyword in ["create_cylinder", "cylinder"]
            ):
                command_parts["type"] = "create-cylinder"
                if "radius" in line.lower():
                    try:
                        command_parts["radius"] = float(line.split("=")[1].strip())
                    except Exception:
                        pass
                if "height" in line.lower():
                    try:
                        command_parts["height"] = float(line.split("=")[1].strip())
                    except Exception:
                        pass

            elif any(
                keyword in line.lower() for keyword in ["create_sphere", "sphere"]
            ):
                command_parts["type"] = "create-sphere"
                if "radius" in line.lower():
                    try:
                        command_parts["radius"] = float(line.split("=")[1].strip())
                    except Exception:
                        pass

            elif any(keyword in line.lower() for keyword in ["export", "save"]):
                command_parts["type"] = "export-document"
                if "path" in line.lower() or "file" in line.lower():
                    try:
                        path = line.split("=")[1].strip().strip("\"'")
                        command_parts["path"] = path
                    except Exception:
                        pass
                if "format" in line.lower():
                    try:
                        format_type = line.split("=")[1].strip().strip("\"'")
                        command_parts["format"] = format_type
                    except Exception:
                        pass

            # Look for document reference in any command
            if "document" in line.lower() and "document" not in command_parts:
                try:
                    doc = line.split("=")[1].strip().strip("\"'")
                    command_parts["document"] = doc
                except Exception:
                    pass

        if not command_parts.get("type"):
            return {
                "error": "Could not determine a clear FreeCAD command from the response",
                "original_response": text,
            }

        return command_parts

    except Exception as e:
        return {"error": f"Error parsing Gemini response: {str(e)}"}


def interactive_prompt_mode(client, api_key):
    """
    Run an interactive prompt mode using Gemini to translate natural language to FreeCAD commands.

    Args:
        client: FreeCAD client instance
        api_key: Gemini API key
    """
    print("\n==== FreeCAD Prompt Mode with Gemini 2.5 Pro ====")
    print("Type 'exit' or 'quit' to end the session")
    print("Example prompts:")
    print(" - Create a new document called MyProject")
    print(" - Make a box with length 20, width 15, and height 10")
    print(" - Create a sphere with radius 25")
    print(" - Export the current model to 'my_model.step'\n")

    while True:
        try:
            user_input = input("FreeCAD > ")

            # Check for exit command
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting prompt mode.")
                break

            # Skip empty inputs
            if not user_input.strip():
                continue

            # Call Gemini API
            print("Thinking...")
            gemini_response = call_gemini_api(
                api_key,
                f"""
            You are a FreeCAD command translator. Convert the following natural language request into
            a specific FreeCAD command. Only output the command name and parameters, nothing else.
            Available commands are:
            - create-document <name>
            - create-box --length X --width Y --height Z --document DOC
            - create-cylinder --radius X --height Y --document DOC
            - create-sphere --radius X --document DOC
            - export-document --path PATH --format FORMAT --document DOC

            USER REQUEST: {user_input}
            """,
            )

            if "error" in gemini_response:
                print(f"Error: {gemini_response['error']}")
                continue

            # Extract FreeCAD command from Gemini's response
            command = extract_freecad_commands(gemini_response)

            if "error" in command:
                print(f"Error: {command['error']}")
                if "original_response" in command:
                    print("\nOriginal Gemini response:")
                    print(textwrap.fill(command["original_response"], width=80))
                continue

            # Execute the command based on type
            cmd_type = command.get("type")

            if cmd_type == "create-document":
                doc_name = command.get("name", "Unnamed")
                print(f"Creating document: {doc_name}")
                result = client.create_document(doc_name)

            elif cmd_type == "create-box":
                length = command.get("length", 10.0)
                width = command.get("width", 10.0)
                height = command.get("height", 10.0)
                document = command.get("document")
                print(f"Creating box: {length}x{width}x{height}")
                result = client.create_box(
                    length=length, width=width, height=height, document=document
                )

            elif cmd_type == "create-cylinder":
                radius = command.get("radius", 5.0)
                height = command.get("height", 10.0)
                document = command.get("document")
                print(f"Creating cylinder: radius={radius}, height={height}")
                result = client.create_cylinder(
                    radius=radius, height=height, document=document
                )

            elif cmd_type == "create-sphere":
                radius = command.get("radius", 5.0)
                document = command.get("document")
                print(f"Creating sphere: radius={radius}")
                result = client.create_sphere(radius=radius, document=document)

            elif cmd_type == "export-document":
                path = command.get("path", "model.step")
                format_type = command.get("format", "step")
                document = command.get("document")
                print(f"Exporting document to: {path}")
                result = client.export_document(
                    file_path=path, file_type=format_type, document=document
                )

            else:
                print(f"Unknown command type: {cmd_type}")
                continue

            # Display the result
            if "error" in result:
                print(f"Command failed: {result['error']}")
            else:
                print("Command executed successfully")

        except Exception as e:
            print(f"Error: {str(e)}")


def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(description="FreeCAD Client")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=12345, help="Server port")
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="Connection timeout"
    )
    parser.add_argument(
        "--freecad", default="freecad", help="Path to FreeCAD executable"
    )
    parser.add_argument(
        "--connect",
        action="store_true",
        help="Connect to running FreeCAD instance",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically choose connection method",
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Version command
    subparsers.add_parser("version", help="Get FreeCAD version")

    # Create document command
    doc_parser = subparsers.add_parser("create-document", help="Create a new document")
    doc_parser.add_argument("name", help="Document name")

    # Create box command
    box_parser = subparsers.add_parser("create-box", help="Create a box")
    box_parser.add_argument("--length", type=float, default=10.0, help="Box length")
    box_parser.add_argument("--width", type=float, default=10.0, help="Box width")
    box_parser.add_argument("--height", type=float, default=10.0, help="Box height")
    box_parser.add_argument("--document", help="Document name")
    box_parser.add_argument("--name", help="Object name")

    # Create cylinder command
    cyl_parser = subparsers.add_parser("create-cylinder", help="Create a cylinder")
    cyl_parser.add_argument("--radius", type=float, default=5.0, help="Cylinder radius")
    cyl_parser.add_argument(
        "--height", type=float, default=10.0, help="Cylinder height"
    )
    cyl_parser.add_argument("--document", help="Document name")
    cyl_parser.add_argument("--name", help="Object name")

    # Create sphere command
    sphere_parser = subparsers.add_parser("create-sphere", help="Create a sphere")
    sphere_parser.add_argument(
        "--radius", type=float, default=5.0, help="Sphere radius"
    )
    sphere_parser.add_argument("--document", help="Document name")
    sphere_parser.add_argument("--name", help="Object name")

    # Export document command
    export_parser = subparsers.add_parser(
        "export-document", help="Export document to a file"
    )
    export_parser.add_argument("--path", required=True, help="Output file path")
    export_parser.add_argument("--document", help="Document name")
    export_parser.add_argument(
        "--format", default="step", help="Export format (step, stl, etc.)"
    )

    # Prompt mode command
    prompt_parser = subparsers.add_parser(
        "prompt", help="Interactive prompt mode using Google Gemini"
    )
    prompt_parser.add_argument("--api-key", help="Google Gemini API key")

    args = parser.parse_args()

    # Create client
    client = FreeCADClient(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        freecad_path=args.freecad,
        connection_method="connect" if args.connect else "auto" if args.auto else None,
    )

    # Try to connect
    if not client.is_connected():
        print(
            f"Error: Could not connect to FreeCAD. Please ensure the server is running on {args.host}:{args.port}"
        )
        sys.exit(1)

    # Get connection type
    conn_type = client.get_connection_type()
    print(f"Connected to FreeCAD using {conn_type} method.")

    # Handle commands
    if args.command == "prompt":
        # Get API key from argument, environment, or prompt
        api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            api_key = input("Enter your Gemini API key: ").strip()

        if not api_key:
            print("Error: Gemini API key is required for prompt mode")
            sys.exit(1)

        interactive_prompt_mode(client, api_key)

    elif args.command == "version":
        # Get FreeCAD version
        version_info = client.get_version()
        if "error" in version_info:
            print(f"Error: {version_info['error']}")
            sys.exit(1)

        # Print version
        version = version_info.get("version", ["Unknown"])
        build_date = version_info.get("build_date", "Unknown")
        print(f"FreeCAD Version: {'.'.join(str(v) for v in version)}")
        print(f"Build Date: {build_date}")

    elif args.command == "create-document":
        # Create a document
        result = client.create_document(args.name)
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"Created document: {result.get('name', 'Unknown')}")

    elif args.command == "create-box":
        # Create a box
        result = client.create_box(
            length=args.length,
            width=args.width,
            height=args.height,
            document=args.document,
            name=args.name,
        )
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"Created box: {result.get('name', 'Unknown')}")
        print(f"Dimensions: {args.length} x {args.width} x {args.height}")

    elif args.command == "create-cylinder":
        # Create a cylinder
        result = client.create_cylinder(
            radius=args.radius,
            height=args.height,
            document=args.document,
            name=args.name,
        )
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"Created cylinder: {result.get('name', 'Unknown')}")
        print(f"Dimensions: radius={args.radius}, height={args.height}")

    elif args.command == "create-sphere":
        # Create a sphere
        result = client.create_sphere(
            radius=args.radius, document=args.document, name=args.name
        )
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"Created sphere: {result.get('name', 'Unknown')}")
        print(f"Radius: {args.radius}")

    elif args.command == "export-document":
        # Export document
        result = client.export_document(
            file_path=args.path, file_type=args.format, document=args.document
        )
        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"Exported document to {args.path}")

    elif args.command is None:
        # No command specified, just print connection status
        print("No command specified. Use --help for available commands.")

    # Close client
    client.close()


if __name__ == "__main__":
    main()
