"""
E2E Test Configuration

This module contains configuration settings for end-to-end tests.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path to ensure imports work correctly
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(PROJECT_ROOT))

# Test settings
TEST_TIMEOUT = 30  # seconds
TEST_SERVER_PORT = 12346  # Use a different port for testing to avoid conflicts

# Paths
TEST_OUTPUT_DIR = PROJECT_ROOT / "tests" / "e2e" / "output"
TEST_MODELS_DIR = PROJECT_ROOT / "tests" / "e2e" / "models"

# Create directories if they don't exist
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
os.makedirs(TEST_MODELS_DIR, exist_ok=True)

# FreeCAD test settings
FREECAD_TEST_CONFIG = {
    "freecad": {
        "connection_method": "auto",  # "auto", "server", "bridge", or "mock"
        "host": "localhost",
        "port": TEST_SERVER_PORT,
        "path": "/usr/bin/freecad",
        "python_path": "./squashfs-root/usr/bin/python",
        "use_mock": True  # Default to mock for tests
    },
    "tools": {
        "enable_smithery": True,
        "enable_primitives": True,
        "enable_model_manipulation": True,
        "enable_export_import": True,
        "enable_measurement": True
    }
}
