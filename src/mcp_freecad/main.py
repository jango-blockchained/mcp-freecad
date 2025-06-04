#!/usr/bin/env python3
"""
Main entry point for MCP-FreeCAD server.

This script provides a unified way to start the MCP server with all
tool providers and proper configuration.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

from . import __version__, TOOL_PROVIDERS
from .core.server import MCPServer

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file with fallback to defaults."""
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(
            f"Could not load config from {config_path}: {e}. Using defaults."
        )
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        "server": {
            "name": "mcp-freecad-server",
            "version": __version__,
            "description": "MCP server for FreeCAD integration",
        },
        "auth": {"api_key": "development", "enabled": False},
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
            "enable_export_import": True,
            "enable_measurement": True,
            "enable_code_generator": True,
        },
        "logging": {"level": "INFO", "file": "logs/mcp_freecad.log"},
    }


async def setup_server(config: Dict[str, Any]) -> MCPServer:
    """Setup and configure the MCP server."""
    # Create server instance
    server = MCPServer(config_path="config.json")

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

    # TODO: Register other tool providers as they become available
    # if tools_config.get("enable_export_import", True):
    #     server.register_tool("export_import", TOOL_PROVIDERS["export_import"]())

    # Initialize server
    await server.initialize()

    return server


async def main():
    """Main server function."""
    parser = argparse.ArgumentParser(
        description=f"MCP-FreeCAD Server v{__version__}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m mcp_freecad.main                    # Start with default config
  python -m mcp_freecad.main --config my.json   # Start with custom config
  python -m mcp_freecad.main --debug            # Start with debug logging
        """,
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Configuration file path (default: config.json)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--version", action="version", version=f"MCP-FreeCAD v{__version__}"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/mcp_freecad.log", mode="a"),
        ],
    )

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    logger.info(f"Starting MCP-FreeCAD Server v{__version__}")

    try:
        # Load configuration
        config = load_config(args.config)

        # Setup server
        server = await setup_server(config)

        logger.info("MCP server initialized successfully")
        logger.info("Server is ready to accept connections")

        # Keep the server running
        # Note: In a real MCP implementation, this would be handled by the MCP framework
        # For now, we'll just keep the process alive
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")

    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Server shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
