#!/usr/bin/env python3
"""
Test Runner for MCP-FreeCAD

This script provides a convenient way to run the MCP-FreeCAD test suite with various options.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description or ' '.join(cmd)}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="MCP-FreeCAD Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                           # Run all tests
  python run_tests.py --unit                   # Run only unit tests
  python run_tests.py --integration            # Run only integration tests
  python run_tests.py --house-scenario         # Run only house modeling tests
  python run_tests.py --performance            # Run only performance tests
  python run_tests.py --coverage               # Run with coverage report
  python run_tests.py --verbose                # Run with verbose output
  python run_tests.py --fast                   # Skip slow tests
  python run_tests.py --specific test_primitives.py  # Run specific test file
        """
    )

    # Test selection options
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    parser.add_argument(
        "--house-scenario",
        action="store_true",
        help="Run only house modeling scenario tests"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run only performance tests"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )

    # Output options
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet output"
    )

    # Specific test options
    parser.add_argument(
        "--specific",
        type=str,
        help="Run specific test file or test function"
    )
    parser.add_argument(
        "--pattern", "-k",
        type=str,
        help="Run tests matching pattern"
    )

    # Other options
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running"
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        help="Run tests in parallel (number of workers)"
    )

    args = parser.parse_args()

    # Change to project root directory
    project_root = Path(__file__).parent
    import os
    os.chdir(project_root)

    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        if not run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev]"], "Installing dependencies"):
            print("Failed to install dependencies")
            return 1

    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Add test directory
    cmd.append("tests/")

    # Add verbosity options
    if args.verbose:
        cmd.append("-v")
    elif args.quiet:
        cmd.append("-q")

    # Add coverage options
    if args.coverage:
        cmd.extend(["--cov=src/mcp_freecad", "--cov-report=term-missing"])
        if args.html_report:
            cmd.append("--cov-report=html")

    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])

    # Add test selection markers
    markers = []

    if args.unit:
        markers.append("not integration and not slow")
    elif args.integration:
        markers.append("integration")
    elif args.house_scenario:
        markers.append("house_scenario")
    elif args.performance:
        markers.append("performance")

    if args.fast:
        if markers:
            markers = [f"({' and '.join(markers)}) and not slow"]
        else:
            markers.append("not slow")

    if markers:
        cmd.extend(["-m", " and ".join(markers)])

    # Add specific test or pattern
    if args.specific:
        cmd.append(args.specific)

    if args.pattern:
        cmd.extend(["-k", args.pattern])

    # Add additional pytest options
    cmd.extend([
        "--tb=short",  # Shorter traceback format
        "--strict-markers",  # Strict marker checking
        "--strict-config",  # Strict config checking
    ])

    # Run the tests
    print(f"\nRunning MCP-FreeCAD Test Suite")
    print(f"Command: {' '.join(cmd)}")

    success = run_command(cmd, "Running tests")

    if success:
        print("\n✅ All tests passed!")

        # Show coverage report location if generated
        if args.coverage and args.html_report:
            print(f"\n📊 HTML coverage report generated: {project_root}/htmlcov/index.html")

        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
