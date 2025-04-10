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
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("connection_test")

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from freecad_connection import FreeCADConnection
except ImportError:
    logger.error("Could not import FreeCADConnection. Make sure you're running from the project root.")
    sys.exit(1)

def test_connection_method(method: str, config: Dict[str, Any]) -> bool:
    """Test a specific connection method."""
    logger.info(f"Testing connection method: {method}")

    try:
        # Create a connection using the specified method
        fc = FreeCADConnection(
            host=config.get("host", "localhost"),
            port=config.get("port", 12345),
            freecad_path=config.get("freecad_path", "freecad"),
            auto_connect=False,  # Don't auto-connect yet
            script_path=config.get("script_path")
        )

        # Connect using the specified method
        success = fc.connect(prefer_method=method)

        if success:
            logger.info(f"✅ Successfully connected using {method} method")

            # Test basic operations
            version_info = fc.get_version()
            logger.info(f"FreeCAD version: {version_info}")

            # Create a document
            doc_name = fc.create_document(f"TestDoc_{method}")
            if doc_name:
                logger.info(f"Created document: {doc_name}")
            else:
                logger.warning(f"Failed to create document with {method} method")

            # Close the connection
            fc.close()
            logger.info(f"Connection closed")
            return True
        else:
            logger.error(f"❌ Failed to connect using {method} method")
            return False

    except Exception as e:
        logger.error(f"Error testing {method} method: {e}", exc_info=True)
        return False

def main():
    """Main function to test connection methods."""
    parser = argparse.ArgumentParser(description="Test FreeCAD connection methods")
    parser.add_argument("--method", choices=["server", "bridge", "wrapper", "launcher", "mock", "auto", "all"],
                      default="all", help="Connection method to test")
    parser.add_argument("--host", default="localhost", help="Server hostname")
    parser.add_argument("--port", type=int, default=12345, help="Server port")
    parser.add_argument("--freecad-path", default="freecad", help="Path to FreeCAD executable")
    parser.add_argument("--script-path", help="Path to FreeCAD script (for launcher method)")
    args = parser.parse_args()

    # Create configuration from arguments
    config = {
        "host": args.host,
        "port": args.port,
        "freecad_path": args.freecad_path,
        "script_path": args.script_path
    }

    # Test the specified method(s)
    if args.method == "all":
        methods = ["launcher", "wrapper", "server", "bridge", "mock"]
        successful_methods = []

        for method in methods:
            if test_connection_method(method, config):
                successful_methods.append(method)

        logger.info(f"Summary: {len(successful_methods)}/{len(methods)} methods successful")
        logger.info(f"Successful methods: {successful_methods}")

    elif args.method == "auto":
        # Test auto-selection
        logger.info("Testing auto-selection of connection method")
        fc = FreeCADConnection(
            host=config.get("host"),
            port=config.get("port"),
            freecad_path=config.get("freecad_path"),
            script_path=config.get("script_path"),
            auto_connect=True  # Let it auto-select the method
        )

        if fc.is_connected():
            used_method = fc.get_connection_type()
            logger.info(f"✅ Auto-selected method: {used_method}")

            # Test basic operations
            version_info = fc.get_version()
            logger.info(f"FreeCAD version: {version_info}")

            # Create a document
            doc_name = fc.create_document("TestDoc_Auto")
            if doc_name:
                logger.info(f"Created document: {doc_name}")
            else:
                logger.warning("Failed to create document with auto method")

            # Close the connection
            fc.close()
            logger.info("Connection closed")
        else:
            logger.error("❌ Auto-selection failed to connect")

    else:
        # Test a specific method
        test_connection_method(args.method, config)

if __name__ == "__main__":
    main()
