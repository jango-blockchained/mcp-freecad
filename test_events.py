#!/usr/bin/env python3
"""
Test script for the MCP-FreeCAD event system.
This script connects to the MCP server and subscribes to events.
"""

import asyncio
import aiohttp
import json
import logging
import sys
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000"  # Update this to match your server's host and port
API_KEY = "development"  # Update this to match your server's API key

async def trigger_document_change():
    """Trigger a document change event for testing."""
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": API_KEY}
        data = {
            "event_type": "document_changed",
            "data": {
                "document": "TestDocument",
                "timestamp": time.time(),
                "objects": ["TestObject1", "TestObject2"],
                "test": True
            }
        }
        
        try:
            async with session.post(
                f"{API_URL}/events/document_changed",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Triggered document_changed event: {result}")
                else:
                    logger.error(f"Failed to trigger event: {response.status}")
                    text = await response.text()
                    logger.error(text)
        except Exception as e:
            logger.error(f"Error triggering event: {e}")

async def report_test_error():
    """Report a test error for testing the error event system."""
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": API_KEY}
        data = {
            "message": "Test error message from test_events.py",
            "error_type": "test_error",
            "details": {
                "test_run": datetime.now().isoformat(),
                "test_module": "test_events",
                "test_function": "report_test_error"
            }
        }
        
        try:
            async with session.post(
                f"{API_URL}/events/report_error",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Reported test error: {result}")
                else:
                    logger.error(f"Failed to report error: {response.status}")
                    text = await response.text()
                    logger.error(text)
        except Exception as e:
            logger.error(f"Error reporting test error: {e}")

async def subscribe_to_events():
    """Subscribe to server events and print them as they arrive."""
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": API_KEY}
        try:
            # Subscribe to all events (no filter)
            url = f"{API_URL}/events"
            
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to connect to event stream: {response.status}")
                    text = await response.text()
                    logger.error(text)
                    return
                
                logger.info("Connected to event stream. Waiting for events...")
                
                # Process event stream
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if not line:
                        continue
                        
                    if line.startswith('event:'):
                        event_type = line[6:].strip()
                        continue
                        
                    if line.startswith('data:'):
                        try:
                            data = json.loads(line[5:].strip())
                            logger.info(f"Received event: {event_type}")
                            logger.info(f"Data: {json.dumps(data, indent=2)}")
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON data: {line[5:].strip()}")
                        continue
                
        except Exception as e:
            logger.error(f"Error in event subscription: {e}")

async def get_command_history():
    """Get command execution history."""
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": API_KEY}
        try:
            async with session.get(
                f"{API_URL}/events/command_history",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Command history: {json.dumps(result, indent=2)}")
                else:
                    logger.error(f"Failed to get command history: {response.status}")
                    text = await response.text()
                    logger.error(text)
        except Exception as e:
            logger.error(f"Error getting command history: {e}")

async def get_error_history():
    """Get error history."""
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": API_KEY}
        try:
            async with session.get(
                f"{API_URL}/events/error_history",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Error history: {json.dumps(result, indent=2)}")
                else:
                    logger.error(f"Failed to get error history: {response.status}")
                    text = await response.text()
                    logger.error(text)
        except Exception as e:
            logger.error(f"Error getting error history: {e}")

async def test_event_system():
    """Test the event system by connecting to events and triggering test events."""
    
    # Start event subscription in the background
    subscription_task = asyncio.create_task(subscribe_to_events())
    
    # Wait a moment for the connection to establish
    await asyncio.sleep(2)
    
    # Trigger a test document change event
    await trigger_document_change()
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Report a test error
    await report_test_error()
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Get command history
    await get_command_history()
    
    # Get error history
    await get_error_history()
    
    # Keep running for a bit to receive more events
    logger.info("Listening for events for 30 seconds...")
    await asyncio.sleep(30)
    
    # Cancel the subscription task
    subscription_task.cancel()
    try:
        await subscription_task
    except asyncio.CancelledError:
        pass
    
    logger.info("Event test completed.")

if __name__ == "__main__":
    try:
        logger.info("Starting event system test...")
        asyncio.run(test_event_system())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user.")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1) 