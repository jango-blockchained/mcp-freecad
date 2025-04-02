import os
import sys

# import asyncio # Unused
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure the main project directory is in sys.path to find the modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the class to test (handle potential import errors gracefully in tests)
try:
    from freecad_connection import (  # Import for type hinting/mocking base
        FreeCADConnection,
    )
    from freecad_mcp_server import FreeCADMCPServer

    SERVER_IMPORT_FAILED = False
except ImportError as e:
    print(f"WARN: Could not import FreeCADMCPServer or FreeCADConnection: {e}")
    # Define dummy classes if import fails, tests will likely be skipped

    class FreeCADMCPServer:
        pass

    class FreeCADConnection:
        pass

    SERVER_IMPORT_FAILED = True


# Skip all tests in this file if the server class couldn't be imported
pytestmark = pytest.mark.skipif(
    SERVER_IMPORT_FAILED, reason="FreeCADMCPServer or FreeCADConnection import failed"
)


@pytest.fixture
def mock_freecad_connection():
    """Provides a mocked FreeCADConnection instance."""
    mock_conn = MagicMock(spec=FreeCADConnection)
    mock_conn.is_connected.return_value = True
    mock_conn.get_connection_type.return_value = "mock"
    mock_conn.get_version.return_value = {
        "success": True,
        "version": ["0.21.0", "mock", "2023"],
        "build_date": "2023/01/01",
        "mock": True,
    }
    mock_conn.create_document.return_value = "MockDoc001"
    # Mock execute_command used by smithery tools
    mock_conn.execute_command = AsyncMock(
        return_value={
            "success": True,
            "environment": {
                "anvil_id": "Anvil001",
                "hammer_id": "Hammer001",
            },  # Example env result
        }
    )
    mock_conn.export_stl.return_value = True  # Mock export_stl directly
    return mock_conn


@pytest.fixture
def mcp_server_instance(mock_freecad_connection):
    """Provides an instance of FreeCADMCPServer with a mocked connection."""
    # Patch the _initialize_freecad_connection to prevent real connection attempt
    # and inject the mock connection directly
    with patch.object(
        FreeCADMCPServer, "_initialize_freecad_connection", return_value=None
    ) as _:
        # We also need to prevent _load_config from trying to read a file if not needed
        with patch.object(FreeCADMCPServer, "_load_config", return_value={}) as _:
            server = FreeCADMCPServer()  # Initialize with dummy config path
            server.freecad_connection = (
                mock_freecad_connection  # Manually assign the mock
            )
            # Manually call _initialize_tool_providers as it relies on self.config
            # which is usually loaded in __init__ / _load_config
            server._initialize_tool_providers()
            # We need to initialize the MCP server object itself for handlers
            server.server = MagicMock()  # Mock the low-level MCP server object
            return server


# --- Test Cases ---


@pytest.mark.asyncio
async def test_list_tools_handler(mcp_server_instance):
    """Test the _handle_list_tools returns defined tools."""
    request = {}  # No params needed for list_tools
    extra = {}  # Extra context, not used in handler
    response = await mcp_server_instance._handle_list_tools(request, extra)

    assert "tools" in response
    assert isinstance(response["tools"], list)
    # Check if some expected tools are present
    tool_names = [t["name"] for t in response["tools"]]
    assert "smithery.create_anvil" in tool_names
    assert "freecad.create_document" in tool_names
    assert "freecad.export_stl" in tool_names
    # Check if schema is included
    for tool in response["tools"]:
        assert "inputSchema" in tool


@pytest.mark.asyncio
async def test_list_resources_handler(mcp_server_instance):
    """Test the _handle_list_resources returns defined resources."""
    request = {}
    extra = {}
    response = await mcp_server_instance._handle_list_resources(request, extra)

    assert "resources" in response
    assert isinstance(response["resources"], list)
    resource_uris = [r["uri"] for r in response["resources"]]
    assert "freecad://info" in resource_uris


@pytest.mark.asyncio
async def test_get_resource_info_handler(mcp_server_instance, mock_freecad_connection):
    """Test getting the freecad://info resource."""
    request = {"uri": "freecad://info"}
    extra = {}
    response = await mcp_server_instance._handle_get_resource(request, extra)

    assert "content" in response
    assert "mimeType" in response
    assert response["mimeType"] == "text/markdown"
    assert "Connection Type: mock" in response["content"]
    assert "FreeCAD Version: 0.21.0.mock.2023" in response["content"]
    # Check that get_version was called on the mock
    mock_freecad_connection.get_version.assert_called_once()


@pytest.mark.asyncio
async def test_get_resource_info_disconnected(
    mcp_server_instance, mock_freecad_connection
):
    """Test getting the freecad://info resource when disconnected."""
    mock_freecad_connection.is_connected.return_value = False  # Simulate disconnect
    request = {"uri": "freecad://info"}
    extra = {}
    response = await mcp_server_instance._handle_get_resource(request, extra)

    assert "content" in response
    assert "mimeType" in response
    assert response["mimeType"] == "text/plain"
    assert "Error: Not currently connected to FreeCAD." in response["content"]
    # Reset mock state for other tests
    mock_freecad_connection.is_connected.return_value = True


@pytest.mark.asyncio
async def test_get_resource_unknown(mcp_server_instance):
    """Test getting an unknown resource."""
    request = {"uri": "freecad://nonexistent"}
    extra = {}
    response = await mcp_server_instance._handle_get_resource(request, extra)

    assert "error" in response  # Should be an ErrorResponse implicitly
    assert "Unknown resource" in response["message"]


@pytest.mark.asyncio
async def test_execute_create_document(mcp_server_instance, mock_freecad_connection):
    """Test executing the freecad.create_document tool."""
    doc_name = "MyTestDoc"
    request = {"name": "freecad.create_document", "arguments": {"name": doc_name}}
    extra = {}
    # Mock the specific connection method call
    mock_freecad_connection.create_document.return_value = doc_name

    response = await mcp_server_instance._handle_execute_tool(request, extra)

    assert response.get("success") is True
    assert response.get("document_name") == doc_name
    # Check that the correct connection method was called
    mock_freecad_connection.create_document.assert_called_once_with(doc_name)


@pytest.mark.asyncio
async def test_execute_export_stl(mcp_server_instance, mock_freecad_connection):
    """Test executing the freecad.export_stl tool."""
    file_path = "/tmp/test_export.stl"
    obj_name = "MyBox"
    doc_name = "MyDoc"
    request = {
        "name": "freecad.export_stl",
        "arguments": {
            "file_path": file_path,
            "object_name": obj_name,
            "document_name": doc_name,
        },
    }
    extra = {}
    # Mock the specific connection method call
    mock_freecad_connection.export_stl.return_value = True

    response = await mcp_server_instance._handle_execute_tool(request, extra)

    assert response.get("success") is True
    assert response.get("file_path") == file_path
    # Check that the correct connection method was called
    mock_freecad_connection.export_stl.assert_called_once_with(
        object_name=obj_name, file_path=file_path, document=doc_name
    )


@pytest.mark.asyncio
async def test_execute_create_anvil(mcp_server_instance, mock_freecad_connection):
    """Test executing the smithery.create_anvil tool (uses execute_script)."""
    request = {
        "name": "smithery.create_anvil",
        "arguments": {"length": 500, "width": 150},  # Override some defaults
    }
    extra = {}
    # Mock the underlying execute_command call
    mock_freecad_connection.execute_command.reset_mock()  # Reset from fixture setup
    mock_freecad_connection.execute_command.return_value = {
        "success": True,
        "environment": {"anvil_id": "GeneratedAnvil001"},
    }

    response = await mcp_server_instance._handle_execute_tool(request, extra)

    assert response.get("success") is True
    assert response.get("anvil_id") == "GeneratedAnvil001"
    # Check that execute_command was called once
    mock_freecad_connection.execute_command.assert_called_once()
    # Check the command type was 'execute_script'
    call_args = mock_freecad_connection.execute_command.call_args
    assert call_args[0][0] == "execute_script"
    # Check that the script content contains expected elements
    script_content = call_args[0][1].get("script", "")
    assert 'addObject("Part::Box", "AnvilBody")' in script_content
    assert "body_length = 500.0" in script_content  # Check override
    assert "body_width = 150.0" in script_content  # Check override
    assert (
        "anvil_id = fused_anvil.Name" in script_content
    )  # Check result key assignment


@pytest.mark.asyncio
async def test_execute_tool_disconnected(mcp_server_instance, mock_freecad_connection):
    """Test executing a tool when disconnected from FreeCAD."""
    mock_freecad_connection.is_connected.return_value = False  # Simulate disconnect
    request = {"name": "freecad.create_document", "arguments": {"name": "TestDoc"}}
    extra = {}

    response = await mcp_server_instance._handle_execute_tool(request, extra)

    assert "error" in response
    assert "Not connected to FreeCAD" in response["message"]

    # Reset mock state for other tests
    mock_freecad_connection.is_connected.return_value = True


@pytest.mark.asyncio
async def test_execute_unknown_tool(mcp_server_instance):
    """Test executing an unknown tool."""
    request = {"name": "nonexistent.tool", "arguments": {}}
    extra = {}
    response = await mcp_server_instance._handle_execute_tool(request, extra)
    assert "error" in response
    assert "Unknown tool" in response["message"]
