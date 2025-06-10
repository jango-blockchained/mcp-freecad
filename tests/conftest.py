"""
Pytest configuration file for MCP-FreeCAD tests.

This file contains global fixtures, configuration, and test setup for the entire test suite.
"""

import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("tests/test_output.log", mode="w"),
    ],
)

# Import fixtures from fixtures.py to make them available globally
from .fixtures import *


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line(
        "markers", "house_scenario: marks tests related to house modeling scenario"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark slow tests
        if "slow" in item.nodeid or "complex" in item.nodeid:
            item.add_marker(pytest.mark.slow)

        # Mark integration tests
        if "integration" in item.nodeid or "scenario" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark performance tests
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)

        # Mark house scenario tests
        if "house" in item.nodeid:
            item.add_marker(pytest.mark.house_scenario)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment before running any tests."""
    # Ensure test output directory exists
    test_output_dir = Path("tests/output")
    test_output_dir.mkdir(exist_ok=True)

    # Set environment variables for testing
    os.environ["TESTING"] = "1"
    os.environ["MCP_FREECAD_TEST_MODE"] = "1"

    yield

    # Cleanup after all tests
    # Remove test environment variables
    os.environ.pop("TESTING", None)
    os.environ.pop("MCP_FREECAD_TEST_MODE", None)


@pytest.fixture(scope="function", autouse=True)
def reset_mock_state(mock_freecad):
    """Reset mock FreeCAD state before each test."""
    # Clear all documents
    mock_freecad.Documents.clear()
    mock_freecad.ActiveDocument = None
    mock_freecad._doc_counter = 0

    yield

    # Cleanup after each test
    mock_freecad.Documents.clear()
    mock_freecad.ActiveDocument = None


@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def test_output_dir():
    """Provide path to test output directory."""
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def capture_logs():
    """Capture log messages during test execution."""
    import logging
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)

    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    yield log_capture

    # Remove handler
    root_logger.removeHandler(handler)


@pytest.fixture
def mock_freecad_import():
    """Mock FreeCAD import for tests that need to test import behavior."""
    from .mocks.freecad_mock import MockFreeCAD, MockPart

    mock_freecad = MockFreeCAD()
    mock_part = MockPart()

    with patch.dict(
        sys.modules,
        {"FreeCAD": mock_freecad, "Part": mock_part, "FreeCADGui": mock_freecad.Gui},
    ):
        yield mock_freecad, mock_part


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary configuration file for testing."""
    config_content = {
        "server": {"name": "test-mcp-freecad-server", "version": "1.0.0-test"},
        "freecad": {
            "auto_connect": False,
            "connection_method": "mock",
            "host": "localhost",
            "port": 12345,
        },
        "tools": {
            "enable_primitives": True,
            "enable_model_manipulation": True,
            "enable_export_import": False,
        },
        "logging": {"level": "DEBUG", "file": "test.log"},
    }

    import json

    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(config_content, indent=2))

    return config_file


@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during test execution."""
    import threading
    import time

    import psutil

    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.peak_memory = 0
            self.monitoring = False
            self._monitor_thread = None

        def start(self):
            self.start_time = time.time()
            self.peak_memory = 0
            self.monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitor_memory)
            self._monitor_thread.start()

        def stop(self):
            self.end_time = time.time()
            self.monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join()

        def _monitor_memory(self):
            process = psutil.Process()
            while self.monitoring:
                try:
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    self.peak_memory = max(self.peak_memory, memory_mb)
                    time.sleep(0.1)
                except:
                    break

        @property
        def elapsed_time(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return PerformanceMonitor()


def pytest_runtest_setup(item):
    """Setup before each test item."""
    # Log test start
    logging.getLogger("test_runner").info(f"Starting test: {item.nodeid}")


def pytest_runtest_teardown(item, nextitem):
    """Teardown after each test item."""
    # Log test completion
    logging.getLogger("test_runner").info(f"Completed test: {item.nodeid}")


def pytest_sessionstart(session):
    """Called after the Session object has been created."""
    logging.getLogger("test_runner").info("=" * 80)
    logging.getLogger("test_runner").info("MCP-FreeCAD Test Suite Starting")
    logging.getLogger("test_runner").info("=" * 80)


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished."""
    logging.getLogger("test_runner").info("=" * 80)
    logging.getLogger("test_runner").info(
        f"MCP-FreeCAD Test Suite Finished (exit status: {exitstatus})"
    )
    logging.getLogger("test_runner").info("=" * 80)


# Custom pytest markers for better test organization
pytest_plugins = []
