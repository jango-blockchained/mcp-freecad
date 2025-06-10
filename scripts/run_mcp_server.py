#!/usr/bin/env python3
"""
MCP Server Launcher

This script runs the MCP server using FreeCAD's AppRun to ensure
it has access to all FreeCAD modules.
"""

import argparse
import os
import subprocess
import sys


def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to the MCP server script (corrected path)
    mcp_script = os.path.join(
        script_dir, "..", "src", "mcp_freecad", "server", "freecad_mcp_server.py"
    )

    # Path to the AppRun executable (relative to the script's original intended location)
    # Adjust based on where AppRun is actually located relative to the *new* script location if needed.
    # Assuming AppRun is still intended to be found via ../squashfs-root relative to the script's parent dir.
    project_root = os.path.dirname(script_dir)
    apprun_path = os.path.join(project_root, "squashfs-root", "AppRun")

    # Check if files exist
    if not os.path.exists(mcp_script):
        print(f"Error: MCP server script not found at {mcp_script}")
        return 1

    if not os.path.exists(apprun_path):
        print(f"Error: AppRun not found at {apprun_path}")
        return 1

    # Force X11 backend to avoid Wayland issues
    os.environ["QT_QPA_PLATFORM"] = "xcb"

    # Parse arguments and pass them through to the MCP server
    args = sys.argv[1:]

    # Build the command to run
    cmd = [apprun_path, mcp_script]
    if args:
        cmd.extend(["--"] + args)

    # Print the command for debugging
    print(f"Running: {' '.join(cmd)}")

    # Execute the command
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\nMCP Server stopped by user")
        return 0
    except Exception as e:
        print(f"Error running MCP server: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
