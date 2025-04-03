#!/usr/bin/env python3
"""
FreeCAD MCP Server launcher

This script serves as the main entry point for the FreeCAD MCP server application.
"""

import os
import sys
import logging
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("freecad_mcp")

def main():
    """Main entry point for the FreeCAD MCP server."""
    parser = argparse.ArgumentParser(description="FreeCAD MCP Server")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        from src.mcp_freecad.server.freecad_mcp_server import FreeCADMCPServer, main as server_main

        # If imported directly, run the server's main function
        server_main()
    except ImportError as e:
        logger.error(f"Failed to import FreeCAD MCP Server: {e}")
        logger.info("Make sure the package is installed or in your PYTHONPATH")
        sys.exit(1)

if __name__ == "__main__":
    main()
