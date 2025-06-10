"""
FreeCAD connection management for MCP server.

Handles connection establishment, monitoring, and error recovery.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Global connection instance
FC_CONNECTION: Optional[Any] = None

try:
    from src.mcp_freecad.client.freecad_connection_manager import FreeCADConnection

    FREECAD_CONNECTION_AVAILABLE = True
except ImportError:
    try:
        from ...client.freecad_connection_manager import FreeCADConnection

        FREECAD_CONNECTION_AVAILABLE = True
    except ImportError:
        logger.warning("FreeCAD connection unavailable")
        FREECAD_CONNECTION_AVAILABLE = False
        FreeCADConnection = None


async def initialize_connection(config: Dict[str, Any]) -> bool:
    """Initialize FreeCAD connection based on configuration."""
    global FC_CONNECTION

    if not FREECAD_CONNECTION_AVAILABLE:
        logger.warning("FreeCAD connection not available")
        return False

    freecad_config = config.get("freecad", {})

    try:
        FC_CONNECTION = FreeCADConnection(
            host=freecad_config.get("host", "localhost"),
            port=freecad_config.get("port", 12345),
            freecad_path=freecad_config.get("freecad_path", "freecad"),
            auto_connect=freecad_config.get("auto_connect", True),
            prefer_method=freecad_config.get("prefer_method", "bridge"),
        )

        if FC_CONNECTION.connect():
            logger.info("FreeCAD connection established")
            return True
        else:
            logger.warning("Failed to connect to FreeCAD")
            FC_CONNECTION = None
            return False

    except Exception as e:
        logger.error(f"Error initializing FreeCAD connection: {e}")
        FC_CONNECTION = None
        return False


async def connection_check_loop(config: Dict[str, Any]):
    """Background task to monitor and maintain FreeCAD connection."""
    global FC_CONNECTION

    check_interval = 5  # seconds
    freecad_config = config.get("freecad", {})

    logger.info(f"Starting connection monitor (interval: {check_interval}s)")

    while True:
        try:
            if FC_CONNECTION is None or not FC_CONNECTION.is_connected():
                logger.info("Attempting to re-establish FreeCAD connection...")
                await initialize_connection(config)

            await asyncio.sleep(check_interval)

        except asyncio.CancelledError:
            logger.info("Connection check loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in connection check loop: {e}")
            await asyncio.sleep(check_interval)


def get_connection():
    """Get current FreeCAD connection instance."""
    return FC_CONNECTION


def is_connected() -> bool:
    """Check if FreeCAD connection is active."""
    return FC_CONNECTION is not None and FC_CONNECTION.is_connected()
