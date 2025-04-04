"""
Base Test Class for E2E Tests

This module provides a base test class for E2E tests with common setup and teardown methods.
"""

import json
import os
import subprocess
import time
import unittest
from pathlib import Path

import pytest
from tests.e2e.config import PROJECT_ROOT, TEST_OUTPUT_DIR, FREECAD_TEST_CONFIG

class FreeCADTestBase(unittest.TestCase):
    """Base class for all FreeCAD E2E tests."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment once for all test methods in the class."""
        # Create test output directory if it doesn't exist
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

        # Save test config as a temporary file
        cls.test_config_path = TEST_OUTPUT_DIR / "test_config.json"
        with open(cls.test_config_path, 'w') as f:
            json.dump(FREECAD_TEST_CONFIG, f, indent=2)

        # Start the MCP server in a separate process if needed
        # For mock mode, we don't need a separate server
        if not FREECAD_TEST_CONFIG['freecad'].get('use_mock', False):
            cls._start_server_process()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all test methods have run."""
        # Stop the server process if it was started
        if hasattr(cls, 'server_process') and cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait(timeout=5)

        # Clean up test config
        if hasattr(cls, 'test_config_path') and cls.test_config_path.exists():
            cls.test_config_path.unlink()

    @classmethod
    def _start_server_process(cls):
        """Start the FreeCAD server process for testing."""
        server_script = PROJECT_ROOT / "freecad_mcp_server.py"
        cmd = [
            "python",
            str(server_script),
            "--config",
            str(cls.test_config_path),
            "--debug"
        ]

        # Start server as a subprocess
        cls.server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give the server a moment to start up
        time.sleep(2)

        # Check if the server started successfully
        if cls.server_process.poll() is not None:
            raise RuntimeError(f"Server failed to start: {cls.server_process.stderr.read()}")

    def setUp(self):
        """Set up before each test method."""
        # Load the MCP client or FreeCAD connection
        # This is implemented in the specific test classes
        pass

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up any test artifacts
        pass


class MCPClientTestBase(FreeCADTestBase):
    """Base class for tests that use the MCP client interface."""

    def setUp(self):
        """Set up MCP client connection before each test."""
        super().setUp()

        # Import and initialize MCP client
        try:
            # This is a placeholder for your actual MCP client initialization
            # Replace with your actual MCP client import and setup
            from modelcontextprotocol import ToolCall, make_tool_inputs
            self.make_tool_inputs = make_tool_inputs

            # You would typically connect to your MCP server here
            # self.client = YourMCPClient(...)

            # For tests, we'll create a fake client
            class MockMCPClient:
                def execute_tool(self, name, args):
                    # This is a placeholder - implement based on your actual MCP client API
                    print(f"Executing tool: {name} with args: {args}")
                    return {"success": True, "result": "mock result"}

            self.client = MockMCPClient()

        except ImportError as e:
            pytest.skip(f"MCP client dependencies not available: {e}")

    def execute_tool(self, tool_name, **kwargs):
        """Helper to execute a tool with the MCP client."""
        # This is a placeholder - implement based on your actual MCP client API
        return self.client.execute_tool(tool_name, kwargs)
