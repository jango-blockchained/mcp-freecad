"""
Basic tests for the FreeCAD MCP Indicator.
These tests don't require FreeCAD to be installed, making them suitable for CI.
"""

import os
import sys
from unittest import mock

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_module_structure():
    """Test that the package structure is correct."""
    # Check that required directories exist
    assert os.path.isdir(os.path.join(os.path.dirname(__file__), '..', 'mcp_indicator'))
    assert os.path.isfile(os.path.join(os.path.dirname(__file__), '..', 'package.xml'))


def test_resources_exist():
    """Test that the resources directory exists."""
    resources_dir = os.path.join(os.path.dirname(__file__), '..', 'mcp_indicator', 'resources')
    assert os.path.isdir(resources_dir)


def test_scripts_exist():
    """Test that the installation scripts exist."""
    scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
    assert os.path.isdir(scripts_dir)
    assert os.path.isfile(os.path.join(scripts_dir, 'install.py'))
    assert os.path.isfile(os.path.join(scripts_dir, 'install.sh'))


def test_installation_script_mock():
    """Mock test for installation script functionality."""
    # This is a mock test that just ensures the test infrastructure works
    # without requiring actual installation of FreeCAD
    assert True
