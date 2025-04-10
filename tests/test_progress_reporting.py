#!/usr/bin/env python3
"""
Test script for verifying progress reporting functionality.

This script tests the progress reporting implementation in the MCP-FreeCAD server
by executing operations that should report progress.
"""

import os
import sys
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Callable, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("progress_test")

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.mcp_freecad.server.freecad_mcp_server import ToolContext
except ImportError:
    logger.error("Could not import ToolContext. Make sure you're running from the project root.")
    sys.exit(1)

# Create a list to store progress updates
progress_updates = []

# Define a progress callback
async def progress_callback(progress: float, message: Optional[str] = None):
    """Store progress updates in the global list and log them."""
    update = {"progress": progress, "message": message}
    progress_updates.append(update)
    logger.info(f"Progress: {progress:.0%} - {message or ''}")

async def test_progress_reporting():
    """Test progress reporting functionality."""
    # Get the ToolContext singleton
    ctx = ToolContext.get()

    # Set our progress callback
    ctx.set_progress_callback(progress_callback)

    # Test sending progress updates
    logger.info("Testing direct progress updates...")
    await ctx.send_progress(0.0, "Starting test...")
    await asyncio.sleep(0.5)
    await ctx.send_progress(0.25, "25% complete")
    await asyncio.sleep(0.5)
    await ctx.send_progress(0.5, "50% complete")
    await asyncio.sleep(0.5)
    await ctx.send_progress(0.75, "75% complete")
    await asyncio.sleep(0.5)
    await ctx.send_progress(1.0, "Test completed")

    # Log the progress updates we received
    logger.info(f"Received {len(progress_updates)} progress updates:")
    for i, update in enumerate(progress_updates):
        logger.info(f"  {i+1}. {update['progress']:.0%} - {update['message']}")

if __name__ == "__main__":
    logger.info("Starting progress reporting test...")
    asyncio.run(test_progress_reporting())
    logger.info("Test completed.")
