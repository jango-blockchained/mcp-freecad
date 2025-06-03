#!/bin/bash

# Script to recursively delete all __pycache__ directories
# Usage: ./clean_pycache.sh [start_directory]

# Get the project root directory (where the script is located)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# If no directory is specified, use project root
start_dir="${1:-$PROJECT_ROOT}"

# Find and delete all __pycache__ directories
find "$start_dir" -type d -name "__pycache__" -exec rm -rf {} +

echo "All __pycache__ directories have been removed from $start_dir"
