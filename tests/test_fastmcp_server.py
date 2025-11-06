"""
Test suite for FastMCP-based MCP server.

Tests the refactored server implementation using fastmcp library.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_freecad_connection():
    """Mock FreeCAD connection for testing."""
    with patch("cursor_mcp_server.FreeCADConnection") as mock_fc:
        mock_instance = MagicMock()
        mock_instance.is_connected.return_value = True
        mock_instance.get_connection_type.return_value = "direct"
        mock_instance.get_version.return_value = "0.21.0"
        mock_instance.create_box.return_value = "Box001"
        mock_instance.create_document.return_value = "Document001"
        mock_instance.create_cylinder.return_value = "Cylinder001"
        mock_instance.create_sphere.return_value = "Sphere001"
        mock_fc.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_freecad_available():
    """Mock FREECAD_AVAILABLE flag."""
    with patch("cursor_mcp_server.FREECAD_AVAILABLE", True):
        yield


class TestFastMCPServer:
    """Test suite for FastMCP server implementation."""

    def test_server_import(self):
        """Test that the server can be imported."""
        import cursor_mcp_server

        assert cursor_mcp_server.mcp is not None

    def test_test_connection_success(
        self, mock_freecad_connection, mock_freecad_available
    ):
        """Test successful FreeCAD connection."""
        from cursor_mcp_server import test_connection

        result = test_connection.fn()

        assert "✅" in result
        assert "FreeCAD connection successful" in result
        assert "direct" in result
        assert "0.21.0" in result

    def test_test_connection_failure(self, mock_freecad_available):
        """Test failed FreeCAD connection."""
        from cursor_mcp_server import test_connection

        with patch("cursor_mcp_server.FreeCADConnection") as mock_fc:
            mock_instance = MagicMock()
            mock_instance.is_connected.return_value = False
            mock_fc.return_value = mock_instance

            result = test_connection.fn()

            assert "❌" in result
            assert "connection failed" in result

    def test_test_connection_not_available(self):
        """Test connection when FreeCAD is not available."""
        from cursor_mcp_server import test_connection

        with patch("cursor_mcp_server.FREECAD_AVAILABLE", False):
            result = test_connection.fn()

            assert "❌" in result
            assert "not available" in result

    def test_test_connection_exception(self, mock_freecad_available):
        """Test connection with exception."""
        from cursor_mcp_server import test_connection

        with patch("cursor_mcp_server.FreeCADConnection") as mock_fc:
            mock_fc.side_effect = Exception("Connection error")

            result = test_connection.fn()

            assert "❌" in result
            assert "Error connecting" in result
            assert "Connection error" in result

    def test_create_box_success(self, mock_freecad_connection, mock_freecad_available):
        """Test successful box creation."""
        from cursor_mcp_server import create_box

        result = create_box.fn(length=10.0, width=20.0, height=30.0)

        assert "✅" in result
        assert "Box created successfully" in result
        assert "Box001" in result
        assert "10.0 x 20.0 x 30.0" in result

        mock_freecad_connection.create_box.assert_called_once_with(
            length=10.0, width=20.0, height=30.0
        )

    def test_create_box_not_available(self):
        """Test box creation when FreeCAD is not available."""
        from cursor_mcp_server import create_box

        with patch("cursor_mcp_server.FREECAD_AVAILABLE", False):
            result = create_box.fn(length=10.0, width=20.0, height=30.0)

            assert "❌" in result
            assert "not available" in result

    def test_create_box_connection_failed(self, mock_freecad_available):
        """Test box creation when connection fails."""
        from cursor_mcp_server import create_box

        with patch("cursor_mcp_server.FreeCADConnection") as mock_fc:
            mock_instance = MagicMock()
            mock_instance.is_connected.return_value = False
            mock_fc.return_value = mock_instance

            result = create_box.fn(length=10.0, width=20.0, height=30.0)

            assert "❌" in result
            assert "connection failed" in result

    def test_create_document_success(
        self, mock_freecad_connection, mock_freecad_available
    ):
        """Test successful document creation."""
        from cursor_mcp_server import create_document

        result = create_document.fn(name="TestDoc")

        assert "✅" in result
        assert "Document 'TestDoc' created successfully" in result
        assert "Document001" in result

        mock_freecad_connection.create_document.assert_called_once_with("TestDoc")

    def test_create_cylinder_success(
        self, mock_freecad_connection, mock_freecad_available
    ):
        """Test successful cylinder creation."""
        from cursor_mcp_server import create_cylinder

        result = create_cylinder.fn(radius=5.0, height=10.0)

        assert "✅" in result
        assert "Cylinder created successfully" in result
        assert "Cylinder001" in result
        assert "Radius: 5.0" in result
        assert "Height: 10.0" in result

        mock_freecad_connection.create_cylinder.assert_called_once_with(
            radius=5.0, height=10.0
        )

    def test_create_sphere_success(
        self, mock_freecad_connection, mock_freecad_available
    ):
        """Test successful sphere creation."""
        from cursor_mcp_server import create_sphere

        result = create_sphere.fn(radius=7.5)

        assert "✅" in result
        assert "Sphere created successfully" in result
        assert "Sphere001" in result
        assert "Radius: 7.5" in result

        mock_freecad_connection.create_sphere.assert_called_once_with(radius=7.5)

    def test_get_server_status(self):
        """Test server status resource."""
        from cursor_mcp_server import get_server_status

        status = get_server_status.fn()

        assert isinstance(status, dict)
        assert "server" in status
        assert status["server"] == "freecad-mcp-server"
        assert "version" in status
        assert "freecad_available" in status
        assert "status" in status
        assert status["status"] == "running"

    def test_all_tools_have_docstrings(self):
        """Test that all tools have proper docstrings."""
        from cursor_mcp_server import (
            create_box,
            create_cylinder,
            create_document,
            create_sphere,
            test_connection,
        )

        tools = [
            test_connection,
            create_box,
            create_document,
            create_cylinder,
            create_sphere,
        ]

        for tool in tools:
            # Check that the tool has a description (fastmcp uses description field)
            assert tool.description is not None
            assert len(tool.description.strip()) > 0

    def test_create_box_with_various_dimensions(
        self, mock_freecad_connection, mock_freecad_available
    ):
        """Test box creation with different dimensions."""
        from cursor_mcp_server import create_box

        test_cases = [
            (1.0, 1.0, 1.0),
            (100.0, 50.0, 25.0),
            (0.5, 0.5, 0.5),
        ]

        for length, width, height in test_cases:
            result = create_box.fn(length=length, width=width, height=height)
            assert "✅" in result
            assert f"{length} x {width} x {height}" in result

    def test_error_handling_in_tools(self, mock_freecad_available):
        """Test that tools handle exceptions gracefully."""
        from cursor_mcp_server import create_box

        with patch("cursor_mcp_server.FreeCADConnection") as mock_fc:
            mock_instance = MagicMock()
            mock_instance.is_connected.return_value = True
            mock_instance.create_box.side_effect = Exception("Creation failed")
            mock_fc.return_value = mock_instance

            result = create_box.fn(length=10.0, width=10.0, height=10.0)

            assert "❌" in result
            assert "Error creating box" in result
            assert "Creation failed" in result


@pytest.mark.integration
class TestFastMCPServerIntegration:
    """Integration tests for FastMCP server."""

    def test_server_initialization(self):
        """Test that the server initializes correctly."""
        from cursor_mcp_server import mcp

        assert mcp is not None
        assert hasattr(mcp, "run")

    def test_multiple_operations(self, mock_freecad_connection, mock_freecad_available):
        """Test multiple operations in sequence."""
        from cursor_mcp_server import create_box, create_document, test_connection

        # Test connection
        result1 = test_connection.fn()
        assert "✅" in result1

        # Create document
        result2 = create_document.fn(name="TestDoc")
        assert "✅" in result2

        # Create box
        result3 = create_box.fn(length=10.0, width=10.0, height=10.0)
        assert "✅" in result3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
