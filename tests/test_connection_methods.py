#!/usr/bin/env python3
"""
Connection Methods Test Script

This script tests different connection methods for connecting to FreeCAD.
It attempts to connect using each method and reports success or failure.
"""

import os
import sys
import logging
import argparse
import json
import pytest
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("connection_test")

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.mcp_freecad.client.freecad_connection_manager import FreeCADConnection
except ImportError:
    logger.error(
        "Could not import FreeCADConnection. Make sure PYTHONPATH is set or run tests from the project root."
    )
    sys.exit(1)


@pytest.fixture(scope="module")
def connection_config() -> Dict[str, Any]:
    """Load the FreeCAD connection configuration from config.json."""
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "config.json")
    )
    try:
        with open(config_path, "r") as f:
            full_config = json.load(f)
            if "freecad" not in full_config:
                pytest.fail("'freecad' section not found in config.json")
            # Return only the 'freecad' section needed by the connection
            return full_config["freecad"]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load or parse config.json at {config_path}: {e}")


# Define the connection methods to test
CONNECTION_METHODS = ["launcher", "wrapper", "server", "bridge", "mock"]


@pytest.mark.parametrize("method", CONNECTION_METHODS)
def test_connection_method(method: str, connection_config: Dict[str, Any]):
    """Test a specific connection method."""
    logger.info(f"Testing connection method: {method}")

    # Check if FreeCAD is available for real connection methods
    freecad_path = connection_config.get("path")
    if method != "mock" and freecad_path and not os.path.exists(freecad_path):
        pytest.skip(f"Skipping {method} test: FreeCAD not found at {freecad_path}")

    # For non-mock methods, skip if we're in a test environment without FreeCAD
    if method != "mock" and os.getenv("CI") or not freecad_path:
        pytest.skip(f"Skipping {method} test: Not available in test environment")

    success = False

    # Ensure required config keys are present
    required_keys = ["host", "port", "path"]
    for key in required_keys:
        if key not in connection_config:
            pytest.fail(f"Missing key '{key}' in freecad config section")

    # Handle optional script_path specifically for launcher
    script_path = connection_config.get("script_path")
    if method == "launcher" and not script_path:
        pytest.skip("Skipping launcher test: 'script_path' not defined in config.json")

    try:
        # Create a connection using the specified method
        fc = FreeCADConnection(
            host=connection_config.get("host", "localhost"),
            port=connection_config.get("port", 12345),
            freecad_path=connection_config.get("path"),
            auto_connect=False,
        )

        # Connect using the specified method
        success = fc.connect(prefer_method=method)

        if success:
            logger.info(
                f"✅ Successfully connected using {method} method ({fc.get_connection_type()})"
            )

            # Test basic operations
            version_info = fc.get_version()
            assert version_info is not None, "Failed to get version info"
            logger.info(f"FreeCAD version: {version_info}")

            # Create a document
            doc_name = fc.create_document(f"TestDoc_{method}")
            assert doc_name is not None, "Failed to create document"
            logger.info(f"Created document: {doc_name}")

            # Close the connection
            fc.close()
            logger.info("Connection closed")

        else:
            # Log failure but let assert handle the test outcome
            logger.error(f"❌ Failed to connect using {method} method")

    except Exception as e:
        logger.error(f"Error testing {method} method: {e}", exc_info=True)
        # Fail the test explicitly on exception
        pytest.fail(f"Exception occurred during {method} test: {e}")

    # Assert success at the end
    assert success, f"Connection method '{method}' failed"
