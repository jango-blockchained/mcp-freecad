#!/usr/bin/env python3
"""
FreeCAD MCP Server Launcher

Launcher script for the FreeCAD MCP server that can be called by Claude Desktop.
This script handles FreeCAD initialization and starts the MCP server.

Usage:
    python launch_mcp_server.py [--freecad-path PATH] [--headless]

Author: jango-blockchained
"""

import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("freecad-mcp-launcher")


def find_freecad_executable():
    """Find FreeCAD executable on the system."""
    possible_paths = []

    if sys.platform == "win32":
        # Windows paths
        possible_paths.extend([
            r"C:\Program Files\FreeCAD 0.21\bin\FreeCAD.exe",
            r"C:\Program Files\FreeCAD 0.22\bin\FreeCAD.exe",
            r"C:\Program Files\FreeCAD\bin\FreeCAD.exe",
            r"C:\Program Files (x86)\FreeCAD 0.21\bin\FreeCAD.exe",
            r"C:\Program Files (x86)\FreeCAD 0.22\bin\FreeCAD.exe",
            r"C:\Program Files (x86)\FreeCAD\bin\FreeCAD.exe"
        ])
    elif sys.platform == "darwin":
        # macOS paths
        possible_paths.extend([
            "/Applications/FreeCAD.app/Contents/MacOS/FreeCAD",
            "/Applications/FreeCAD 0.21.app/Contents/MacOS/FreeCAD",
            "/Applications/FreeCAD 0.22.app/Contents/MacOS/FreeCAD"
        ])
    else:
        # Linux paths
        possible_paths.extend([
            "/usr/bin/freecad",
            "/usr/local/bin/freecad",
            "/opt/freecad/bin/FreeCAD",
            "/snap/freecad/current/usr/bin/freecad"
        ])

    # Check PATH
    import shutil
    freecad_in_path = shutil.which("freecad") or shutil.which("FreeCAD")
    if freecad_in_path:
        possible_paths.insert(0, freecad_in_path)

    # Find first existing path
    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def setup_freecad_environment(freecad_path=None):
    """Setup environment for FreeCAD."""
    if freecad_path:
        freecad_exe = freecad_path
    else:
        freecad_exe = find_freecad_executable()

    if not freecad_exe:
        logger.error("FreeCAD executable not found. Please specify with --freecad-path")
        return False

    logger.info(f"Using FreeCAD executable: {freecad_exe}")

    # Add FreeCAD paths to Python path
    freecad_dir = os.path.dirname(freecad_exe)

    # Common FreeCAD library paths
    lib_paths = []

    if sys.platform == "win32":
        lib_paths.extend([
            freecad_dir,
            os.path.join(freecad_dir, "lib"),
            os.path.join(freecad_dir, "Mod")
        ])
    elif sys.platform == "darwin":
        # macOS app bundle structure
        contents_dir = os.path.dirname(freecad_dir)
        lib_paths.extend([
            os.path.join(contents_dir, "lib"),
            os.path.join(contents_dir, "Mod"),
            freecad_dir
        ])
    else:
        # Linux
        lib_paths.extend([
            "/usr/lib/freecad/lib",
            "/usr/lib/freecad/Mod",
            "/usr/local/lib/freecad/lib",
            "/usr/local/lib/freecad/Mod",
            os.path.join(freecad_dir, "..", "lib"),
            os.path.join(freecad_dir, "..", "Mod")
        ])

    # Add existing paths to Python path
    for lib_path in lib_paths:
        if os.path.exists(lib_path) and lib_path not in sys.path:
            sys.path.insert(0, lib_path)
            logger.debug(f"Added to Python path: {lib_path}")

    return True


def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(description="Launch FreeCAD MCP Server")
    parser.add_argument("--freecad-path", help="Path to FreeCAD executable")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--addon-path", help="Path to MCP addon directory")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting FreeCAD MCP Server Launcher...")

    # Setup FreeCAD environment
    if not setup_freecad_environment(args.freecad_path):
        sys.exit(1)

    # Add addon path to Python path
    if args.addon_path:
        addon_path = args.addon_path
    else:
        # Try to find addon relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        addon_path = os.path.join(script_dir, "..", "freecad-ai")

    addon_path = os.path.abspath(addon_path)
    if os.path.exists(addon_path):
        sys.path.insert(0, addon_path)
        logger.info(f"Added addon path: {addon_path}")
    else:
        logger.warning(f"Addon path not found: {addon_path}")

    # Set headless mode if requested
    if args.headless:
        os.environ["FREECAD_HEADLESS"] = "1"

    try:
        # Import and run the MCP server
        logger.info("Importing MCP server...")

        # Change to addon directory for relative imports
        original_cwd = os.getcwd()
        if os.path.exists(addon_path):
            os.chdir(addon_path)

        try:
            import asyncio

            from mcp_server import main as mcp_main

            logger.info("Starting MCP server...")
            asyncio.run(mcp_main())

        finally:
            os.chdir(original_cwd)

    except ImportError as e:
        logger.error(f"Failed to import MCP server: {e}")
        logger.error("Make sure the MCP library is installed: pip install mcp")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
