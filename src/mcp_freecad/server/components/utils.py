"""
Utility functions for FreeCAD MCP Server.

Provides input sanitization and common helper functions.
"""

import os

try:
    from fastmcp.exceptions import FastMCPError
except ImportError:
    class FastMCPError(Exception):
        pass


def sanitize_name(name: str) -> str:
    """Basic sanitization for names used in scripts."""
    return name.replace('"', '\\"').replace('\\\\', '\\\\\\\\')


def sanitize_path(path: str) -> str:
    """Basic path sanitization to prevent directory traversal."""
    if ".." in path:
        raise FastMCPError("Path cannot contain '..'")
    
    # Additional checks can be added here if needed
    # Example: restrict to certain directories
    # if os.path.isabs(path):
    #     raise FastMCPError("Absolute paths are not allowed")
    
    return path


def format_error_message(error: Exception, operation: str) -> str:
    """Format error messages consistently."""
    return f"Error in {operation}: {str(error)}"


def validate_numeric_input(value: any, param_name: str, min_val: float = None, max_val: float = None) -> float:
    """Validate numeric input with optional range checking."""
    try:
        num_value = float(value)
        if min_val is not None and num_value < min_val:
            raise FastMCPError(f"{param_name} must be >= {min_val}")
        if max_val is not None and num_value > max_val:
            raise FastMCPError(f"{param_name} must be <= {max_val}")
        return num_value
    except (ValueError, TypeError):
        raise FastMCPError(f"{param_name} must be a valid number")