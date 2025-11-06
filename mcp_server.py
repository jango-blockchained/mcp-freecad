#!/usr/bin/env python3
"""
Unified MCP server for FreeCAD integration.

This server provides both FastMCP (cursor_mcp_server) and traditional MCP
server functionality through command-line arguments.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

__version__ = "1.0.0"

logger = logging.getLogger(__name__)


def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file with fallback to defaults."""
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse config from {config_path}: {e}")

    return {
        "server": {
            "name": "mcp-freecad-server",
            "version": __version__,
            "description": "MCP server for FreeCAD integration",
        },
        "freecad": {
            "auto_connect": True,
            "connection_method": "auto",
            "host": "localhost",
            "port": 12345,
            "freecad_path": "freecad",
        },
        "tools": {
            "enable_primitives": True,
            "enable_model_manipulation": True,
        },
    }


def run_fastmcp_server(config: Dict[str, Any]):
    """Run FastMCP-based server (for Cursor IDE and similar)."""
    try:
        from fastmcp import FastMCP

        from mcp_freecad.client.freecad_connection_manager import FreeCADConnection

        FREECAD_AVAILABLE = True
    except ImportError as e:
        logger.error(f"FastMCP or FreeCAD modules not available: {e}")
        sys.exit(1)

    # Create FastMCP server instance
    mcp = FastMCP("freecad-mcp-server")

    # Resources (read-only data endpoints)
    @mcp.resource("freecad://status")
    def get_server_status() -> dict:
        """Get FreeCAD MCP server status."""
        return {
            "server": "freecad-mcp-server",
            "version": __version__,
            "freecad_available": FREECAD_AVAILABLE,
            "status": "running",
        }

    # Tools (callable functions)
    @mcp.tool()
    def test_connection() -> str:
        """Test connection to FreeCAD.

        Returns:
            Connection status message
        """
        if not FREECAD_AVAILABLE:
            return "❌ FreeCAD modules not available."

        try:
            fc = FreeCADConnection(auto_connect=True)
            if fc.is_connected():
                connection_type = fc.get_connection_type()
                version = fc.get_version()
                return (
                    f"✅ FreeCAD connection successful!\n"
                    f"Type: {connection_type}\nVersion: {version}"
                )
            else:
                return "❌ FreeCAD connection failed."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    @mcp.tool()
    def create_box(length: float, width: float, height: float) -> str:
        """Create a box in FreeCAD.

        Args:
            length: Length of the box in mm
            width: Width of the box in mm
            height: Height of the box in mm
        """
        try:
            fc = FreeCADConnection(auto_connect=True)
            if not fc.is_connected():
                return "❌ FreeCAD connection failed."

            box_id = fc.create_box(length=length, width=width, height=height)
            return f"✅ Box created! ID: {box_id}\nSize: {length}x{width}x{height}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    @mcp.tool()
    def create_document(name: str) -> str:
        """Create a new FreeCAD document.

        Args:
            name: Name of the document
        """
        try:
            fc = FreeCADConnection(auto_connect=True)
            if not fc.is_connected():
                return "❌ FreeCAD connection failed."

            doc_id = fc.create_document(name)
            return f"✅ Document '{name}' created! ID: {doc_id}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    @mcp.tool()
    def create_cylinder(radius: float, height: float) -> str:
        """Create a cylinder in FreeCAD.

        Args:
            radius: Radius of the cylinder in mm
            height: Height of the cylinder in mm
        """
        try:
            fc = FreeCADConnection(auto_connect=True)
            if not fc.is_connected():
                return "❌ FreeCAD connection failed."

            cylinder_id = fc.create_cylinder(radius=radius, height=height)
            return (
                f"✅ Cylinder created! ID: {cylinder_id}\n"
                f"Radius: {radius}, Height: {height}"
            )
        except Exception as e:
            return f"❌ Error: {str(e)}"

    @mcp.tool()
    def create_sphere(radius: float) -> str:
        """Create a sphere in FreeCAD.

        Args:
            radius: Radius of the sphere in mm
        """
        try:
            fc = FreeCADConnection(auto_connect=True)
            if not fc.is_connected():
                return "❌ FreeCAD connection failed."

            sphere_id = fc.create_sphere(radius=radius)
            return f"✅ Sphere created! ID: {sphere_id}\nRadius: {radius}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    logger.info("Starting FastMCP server...")
    mcp.run()


async def run_standard_server(config: Dict[str, Any]):
    """Run standard MCP server with full tool providers."""
    try:
        from mcp_freecad import TOOL_PROVIDERS
        from mcp_freecad.core.server import MCPServer
    except ImportError as e:
        logger.error(f"MCP server modules not available: {e}")
        sys.exit(1)

    # Create server instance
    server = MCPServer(config_path=config.get("config_file"))

    # Register tool providers based on configuration
    tools_config = config.get("tools", {})

    if tools_config.get("enable_primitives", True):
        server.register_tool("primitives", TOOL_PROVIDERS["primitives"]())
        logger.info("Registered primitives tool provider")

    if tools_config.get("enable_model_manipulation", True):
        server.register_tool(
            "model_manipulation", TOOL_PROVIDERS["model_manipulation"]()
        )
        logger.info("Registered model manipulation tool provider")

    # Initialize server
    await server.initialize()
    logger.info("MCP server initialized successfully")
    logger.info("Server is ready to accept connections")

    # Keep the server running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")

    logger.info("Server shutdown complete")


def main():
    """Main entry point with argument parsing."""
    from textwrap import dedent

    parser = argparse.ArgumentParser(
        description=f"MCP-FreeCAD Server v{__version__}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent(
            """
            Server Modes:
              fastmcp    Use FastMCP server (lightweight, ideal for Cursor IDE)
              standard   Use standard MCP server with full tool providers (default)

            Examples:
              python mcp_server.py                           # Standard server
              python mcp_server.py --mode fastmcp            # FastMCP server
              python mcp_server.py --config my.json          # Custom config
              python mcp_server.py --debug                   # Debug logging
              python mcp_server.py --mode standard --debug   # Standard + debug
            """
        ),
    )

    parser.add_argument(
        "--mode",
        choices=["fastmcp", "standard"],
        default="standard",
        help="Server mode to use (default: standard)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Configuration file path (optional)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"MCP-FreeCAD v{__version__}",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)

    logger.info(f"Starting MCP-FreeCAD Server v{__version__}")
    logger.info(f"Mode: {args.mode}")

    # Load configuration
    config = load_config(args.config)
    config["config_file"] = args.config

    try:
        if args.mode == "fastmcp":
            run_fastmcp_server(config)
        else:
            asyncio.run(run_standard_server(config))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
