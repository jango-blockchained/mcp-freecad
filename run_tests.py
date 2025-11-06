#!/usr/bin/env python3
"""
Test runner script for MCP-FreeCAD FastMCP implementation.

This script provides an easy way to run tests for the FastMCP server.
"""

import sys
import subprocess
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run tests based on the specified type."""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test path based on type
    if test_type == "fastmcp":
        cmd.append("tests/test_fastmcp_server.py")
        print("Running FastMCP server tests...")
    elif test_type == "integration":
        cmd.append("tests/test_server_integration.py")
        print("Running server integration tests...")
    elif test_type == "all":
        cmd.append("tests/")
        print("Running all tests...")
    else:
        print(f"Unknown test type: {test_type}")
        return 1
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    # Add short traceback
    cmd.append("--tb=short")
    
    print(f"Command: {' '.join(cmd)}")
    print("=" * 80)
    
    # Run tests
    result = subprocess.run(cmd)
    
    if coverage and result.returncode == 0:
        print("\n" + "=" * 80)
        print("Coverage report generated in htmlcov/index.html")
        print("=" * 80)
    
    return result.returncode


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run MCP-FreeCAD FastMCP tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --type fastmcp     # Run only FastMCP tests
  python run_tests.py --verbose          # Run with verbose output
  python run_tests.py --coverage         # Run with coverage report
  python run_tests.py --type fastmcp -v  # FastMCP tests, verbose
        """
    )
    
    parser.add_argument(
        "--type",
        choices=["all", "fastmcp", "integration"],
        default="fastmcp",
        help="Type of tests to run (default: fastmcp)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Run tests with verbose output"
    )
    
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent
    import os
    os.chdir(project_root)
    
    # Run tests
    exit_code = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    # Print summary
    print("\n" + "=" * 80)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed with exit code {exit_code}")
    print("=" * 80)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
