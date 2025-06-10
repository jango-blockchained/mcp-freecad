#!/usr/bin/env python3
"""
Main application entry point for MCP-FreeCAD server.

This script serves as the primary entry point for running the MCP server,
providing a simplified interface for starting the application.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from mcp_freecad.server.freecad_mcp_server import main as server_main
except ImportError as e:
    print(f"Error importing MCP server: {e}")
    print(
        "Please ensure all dependencies are installed with: pip install -r requirements.txt"
    )
    sys.exit(1)


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="MCP-FreeCAD Server")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Configuration file path (default: config.json)",
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Server port (default: 8080)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Set environment variables
    os.environ["PYTHONPATH"] = str(Path(__file__).parent)

    if args.debug:
        os.environ["DEBUG"] = "1"

    # Run the server
    try:
        asyncio.run(server_main(args))
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
