"""
Tests for utility functions.
"""

import pytest
from src.mcp_freecad.server.components.utils import (
    sanitize_name,
    sanitize_path,
    validate_numeric_input,
)


class TestUtils:
    """Test utility functions."""

    def test_sanitize_name(self):
        """Test name sanitization."""
        assert sanitize_name("normal_name") == "normal_name"
        assert sanitize_name('name"with"quotes') == 'name\\"with\\"quotes'
        assert (
            sanitize_name("path\\\\with\\\\backslashes")
            == "path\\\\\\\\with\\\\\\\\backslashes"
        )

    def test_sanitize_path_valid(self):
        """Test valid path sanitization."""
        assert sanitize_path("valid/path") == "valid/path"
        assert sanitize_path("file.txt") == "file.txt"

    def test_sanitize_path_invalid(self):
        """Test invalid path rejection."""
        with pytest.raises(Exception):  # FastMCPError or similar
            sanitize_path("../forbidden")

        with pytest.raises(Exception):
            sanitize_path("path/../other")

    def test_validate_numeric_input(self):
        """Test numeric input validation."""
        assert validate_numeric_input("42", "test") == 42.0
        assert validate_numeric_input(3.14, "pi") == 3.14

        # Range validation
        assert validate_numeric_input(5, "val", min_val=0, max_val=10) == 5.0

        with pytest.raises(Exception):
            validate_numeric_input("not_a_number", "test")

        with pytest.raises(Exception):
            validate_numeric_input(-1, "test", min_val=0)

        with pytest.raises(Exception):
            validate_numeric_input(15, "test", max_val=10)
