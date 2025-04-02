#!/usr/bin/env python3
"""
FreeCAD Connection Test Script

This script tests the FreeCAD connection implementation by trying
all connection methods and performing basic operations.
"""

import os
import subprocess
import sys
import time

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from freecad_connection import FreeCADConnection


def test_connection(connection_type=None):
    """Test FreeCAD connection with the specified method"""
    print(f"\n=== Testing {connection_type or 'auto'} connection ===")

    # Create connection with specified method
    connection = FreeCADConnection(prefer_method=connection_type)

    if not connection.is_connected():
        print(f"Failed to connect to FreeCAD using {connection_type or 'auto'} method")
        return False

    actual_type = connection.get_connection_type()
    print(f"Connected to FreeCAD using {actual_type} method")

    # Get version info
    print("\nGetting FreeCAD version...")
    version_info = connection.get_version()
    if "error" in version_info:
        print(f"Error: {version_info['error']}")
        return False

    version_str = ".".join(str(v) for v in version_info.get("version", ["unknown"]))
    print(f"FreeCAD Version: {version_str}")
    print(f"Build Date: {version_info.get('build_date', 'unknown')}")

    # Create a document
    print("\nCreating document...")
    doc_name = connection.create_document(f"TestDoc_{connection_type or 'auto'}")

    if not doc_name:
        print("Failed to create document")
        return False

    print(f"Created document: {doc_name}")

    # Create geometry
    print("\nCreating box...")
    box_name = connection.create_box(length=100, width=50, height=25, document=doc_name)

    if not box_name:
        print("Failed to create box")
        return False

    print(f"Created box: {box_name}")

    # Export to STL
    print("\nExporting to STL...")
    output_path = os.path.join(os.getcwd(), f"test_{actual_type}.stl")

    if connection.export_stl(box_name, output_path, doc_name):
        print(f"Exported to: {output_path}")
        if os.path.exists(output_path):
            print(f"File size: {os.path.getsize(output_path)} bytes")
        else:
            print("Warning: File doesn't exist (mock export)")
    else:
        print("Failed to export STL")

    # Close connection
    connection.close()
    print("\nConnection closed")

    return True


def start_freecad_server():
    """Start the FreeCAD server in the background"""
    print("Starting FreeCAD server in background...")
    try:
        # Using freecad command-line to start the server
        process = subprocess.Popen(
            ["freecad", "-c", "freecad_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait a bit for server to start
        time.sleep(2)

        # Check if process is still running
        if process.poll() is not None:
            stderr = process.stderr.read().decode()
            print(f"Error starting FreeCAD server: {stderr}")
            return None

        return process
    except Exception as e:
        print(f"Error starting FreeCAD server: {e}")
        return None


def main():
    """Run the test"""
    print("FreeCAD Connection Test")
    print("======================")

    # Start the FreeCAD server for socket-based connection
    server_process = start_freecad_server()

    try:
        # Test auto connection (should pick the best available method)
        test_connection()

        # Test specific connection methods
        test_connection(FreeCADConnection.CONNECTION_SERVER)
        test_connection(FreeCADConnection.CONNECTION_BRIDGE)
        test_connection(FreeCADConnection.CONNECTION_MOCK)

    finally:
        # Stop the server if started
        if server_process:
            print("\nStopping FreeCAD server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()


if __name__ == "__main__":
    main()
