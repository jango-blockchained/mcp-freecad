#!/usr/bin/env python3
"""
Refactored FreeCAD MCP Server.

A clean, modular implementation using separated components.
"""

import argparse
import asyncio
import logging
import sys
from typing import Optional

# Import refactored components
from .components.config import load_config, get_server_name, get_server_version
from .components.logging_setup import setup_logging
from .components.connection_manager import initialize_connection, connection_check_loop
from .components.progress_tracker import ToolContext

# FastMCP import with fallback
try:
    from fastmcp import FastMCP
    from fastmcp.exceptions import FastMCPError
    mcp_import_error = None
except ImportError as e:
    mcp_import_error = str(e)
    # Dummy classes for type hints
    class FastMCP:
        def __init__(self, name: str, version: str = "0.1.0"): pass
        def tool(self): return lambda f: f
        async def run_stdio(self): pass
    class FastMCPError(Exception): pass

logger = logging.getLogger(__name__)


async def main(args=None):
    """Main server function."""
    if mcp_import_error:
        logger.error(f"FastMCP import failed: {mcp_import_error}")
        sys.exit(1)

    # Load configuration
    config_path = args.config if args and hasattr(args, 'config') else "config.json"
    config = load_config(config_path)
    
    # Setup logging
    log_receiver = setup_logging(config)
    
    # Initialize MCP server
    server_name = get_server_name()
    server_version = get_server_version()
    mcp = FastMCP(server_name, version=server_version)
    
    # Setup progress tracking
    def local_progress_callback(progress_value, message=None):
        if message:
            logger.info(f"Progress: {progress_value*100:.1f}% - {message}")
        else:
            logger.info(f"Progress: {progress_value*100:.1f}%")
    
    tool_context = ToolContext.get()
    tool_context.set_progress_callback(local_progress_callback)
    
    # Initialize FreeCAD connection
    await initialize_connection(config)
    
    # Start background connection monitoring
    connection_task = asyncio.create_task(connection_check_loop(config))
    
    logger.info(f"Starting MCP server '{server_name}' v{server_version}...")
    
    try:
        await mcp.run_stdio()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    finally:
        # Cleanup
        connection_task.cancel()
        try:
            await connection_task
        except asyncio.CancelledError:
            pass
        
        if log_receiver:
            log_receiver.abort = 1
        
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FreeCAD MCP Server")
    parser.add_argument("--config", default="config.json", help="Config file path")
    args = parser.parse_args()
    
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)