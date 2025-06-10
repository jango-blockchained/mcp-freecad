#!/usr/bin/env python3
"""
FreeCAD Server Starter

This script is meant to be run from within FreeCAD's Python console
or as a macro to start the server in connect mode.
"""
import os
import subprocess
import sys
import threading

import FreeCAD
import FreeCADGui

print("Starting FreeCAD server in connect mode...")

# Get the path to the server script
script_dir = os.path.dirname(os.path.realpath(__file__))
server_script = os.path.join(script_dir, "..", "src", "mcp_freecad", "connections", "freecad_socket_server.py")

if not os.path.exists(server_script):
    print(f"Error: Server script not found at {server_script}")
    sys.exit(1)

# Define a function to run the server in a separate thread
def run_server():
    # Import the server module and run it
    sys.path.append(script_dir)

    # Backup sys.argv and restore it after
    old_argv = sys.argv
    sys.argv = [server_script, "--connect"]

    try:
        print(f"Running server from: {server_script}")
        # Execute the server script
        namespace = {}
        with open(server_script, 'r') as f:
            server_code = f.read()
            exec(server_code, namespace)
    except Exception as e:
        print(f"Error starting server: {e}")
    finally:
        sys.argv = old_argv

# Start the server in a separate thread
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True  # Make sure it doesn't prevent FreeCAD from exiting
server_thread.start()

print("Server thread started. You can now use the MCP server with this FreeCAD instance.")
