#!/usr/bin/env python3
"""
delete_backup_files.py

A simple utility script to recursively delete all .bak files from the project.
"""

import os
import sys
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Delete all .bak files from the project")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show which files would be deleted without actually deleting them",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Root path to search from (defaults to project root)",
    )
    args = parser.parse_args()

    # Determine the project root directory
    if args.path:
        root_dir = Path(args.path)
    else:
        # Default to the repository root (assumes this script is in scripts/)
        script_dir = Path(__file__).resolve().parent
        root_dir = script_dir.parent

    if not root_dir.exists():
        print(f"Error: Path {root_dir} does not exist")
        return 1

    # Find all .bak files
    backup_files = list(root_dir.glob("**/*.bak"))

    if not backup_files:
        print("No .bak files found")
        return 0

    # Print summary
    print(f"Found {len(backup_files)} .bak files")

    if args.dry_run:
        for file in backup_files:
            print(f"Would delete: {file}")
        print("\nThis was a dry run. No files were deleted.")
        print("To delete files, run without the --dry-run flag")
    else:
        for file in backup_files:
            try:
                file.unlink()
                print(f"Deleted: {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
