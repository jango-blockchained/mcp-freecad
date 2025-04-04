#!/usr/bin/env python
"""
E2E Test Runner

This script discovers and runs all E2E tests for the MCP-FreeCAD project.
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

# Add the project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(PROJECT_ROOT))

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run E2E tests for MCP-FreeCAD")
    parser.add_argument("--mock", action="store_true", default=True,
                        help="Run tests with mock FreeCAD (default)")
    parser.add_argument("--real", action="store_true",
                        help="Run tests with real FreeCAD connection")
    parser.add_argument("--single", type=str, default=None,
                        help="Run a single test file (e.g., 'test_primitives.py')")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug output")
    return parser.parse_args()

def modify_config(use_mock=True):
    """Modify the test configuration."""
    import json
    from tests.e2e.config import TEST_OUTPUT_DIR

    config_path = Path(TEST_OUTPUT_DIR) / "test_config.json"

    # Create the directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Load the default config from the module
    from tests.e2e.config import FREECAD_TEST_CONFIG
    config = FREECAD_TEST_CONFIG.copy()

    # Modify the config based on command line args
    config["freecad"]["use_mock"] = use_mock

    # Save the modified config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    return config_path

def discover_tests(single_test=None):
    """Discover test files to run."""
    e2e_dir = Path(__file__).parent

    if single_test:
        # Run a single specified test
        test_path = e2e_dir / single_test
        if not test_path.exists():
            print(f"Error: Test file '{single_test}' not found in {e2e_dir}")
            sys.exit(1)
        return [test_path]

    # Discover all test files
    test_files = list(e2e_dir.glob("test_*.py"))
    test_files = [tf for tf in test_files if tf.name != "__init__.py" and tf.name != "test_base.py"]

    if not test_files:
        print(f"No test files found in {e2e_dir}")
        sys.exit(1)

    return test_files

def run_tests(test_files, verbose=False, debug=False):
    """Run the specified test files using pytest."""
    pytest_args = ["-x"]  # Stop on first failure

    if verbose:
        pytest_args.append("-v")

    if debug:
        pytest_args.append("--log-cli-level=DEBUG")

    # Convert Path objects to strings
    test_files = [str(tf) for tf in test_files]

    # Run tests using pytest
    import pytest
    result = pytest.main(pytest_args + test_files)

    return result

def main():
    """Main entry point for running E2E tests."""
    start_time = time.time()

    # Parse command line arguments
    args = parse_args()

    # Use real FreeCAD if specified, otherwise use mock
    use_mock = not args.real

    # Modify the test configuration
    config_path = modify_config(use_mock=use_mock)
    print(f"Using test configuration: {config_path}")
    print(f"FreeCAD mode: {'MOCK' if use_mock else 'REAL'}")

    # Discover test files to run
    test_files = discover_tests(args.single)
    print(f"Found {len(test_files)} test files to run:")
    for tf in test_files:
        print(f"  - {tf.name}")

    # Run the tests
    print("\nRunning E2E tests...")
    result = run_tests(test_files, verbose=args.verbose, debug=args.debug)

    # Print summary
    elapsed_time = time.time() - start_time
    print(f"\nE2E tests completed in {elapsed_time:.2f} seconds")
    print(f"Result: {'SUCCESS' if result == 0 else 'FAILURE'}")

    return result

if __name__ == "__main__":
    sys.exit(main())
