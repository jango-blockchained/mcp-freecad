#!/usr/bin/env python3
"""
Quick Start Script for MCP-FreeCAD
Run this from Cursor IDE to start the MCP server with various options.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Start MCP-FreeCAD Server")
    parser.add_argument(
        "--mode",
        choices=["server", "app", "docker", "freecad"],
        default="server",
        help="Start mode",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--port", type=int, default=8000, help="Server port")

    args = parser.parse_args()

    # Ensure we're in the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    print(f"🚀 Starting MCP-FreeCAD in {args.mode} mode...")
    print(f"📁 Working directory: {project_dir}")

    try:
        if args.mode == "server":
            cmd = [sys.executable, "-m", "src.mcp_freecad.main"]
            if args.config:
                cmd.extend(["--config", args.config])
            if args.debug:
                cmd.append("--debug")

        elif args.mode == "app":
            cmd = [sys.executable, "app.py"]

        elif args.mode == "docker":
            cmd = ["docker", "compose", "up"]
            if args.debug:
                cmd.append("--verbose")

        elif args.mode == "freecad":
            print("🔧 Starting FreeCAD...")
            print("Make sure the addon is installed in ~/.FreeCAD/Mod/")
            cmd = ["freecad"]

        print(f"💻 Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting MCP server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down MCP server...")
        sys.exit(0)


if __name__ == "__main__":
    main()
