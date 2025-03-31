import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from mcp_freecad.core.server import MCPServer
from mcp_freecad.core.exceptions import (
    ToolExecutionError,
    ResourceAccessError,
    AuthenticationError,
    ValidationError
)
from mcp_freecad.core.recovery import RecoveryConfig

@pytest.fixture
def server():
    """Create a test server instance."""
    server = MCPServer()
    # Configure test authentication
    async def mock_authenticate(token: str) -> bool:
        return True
    server.auth_manager.authenticate = mock_authenticate
    return server

@pytest.fixture
def client(server):
    """Create a test client."""
    return TestClient(server.app)

@pytest.fixture
def auth_headers():
    """Return authentication headers for test requests."""
    return {"Authorization": "Bearer test_token"}

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert isinstance(data["freecad_connected"], bool)

def test_detailed_health(client):
    """Test the detailed health check endpoint."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "freecad_connection" in data
    assert "cache" in data
    assert "server_uptime" in data

def test_authentication(client, auth_headers):
    """Test authentication middleware."""
    # Test without token
    response = client.post("/tools/test/execute", json={"params": {}})
    assert response.status_code == 401

    # Test with valid token
    response = client.post("/tools/test/execute", json={"params": {}}, headers=auth_headers)
    assert response.status_code == 422  # Expected since no tool is registered

def test_tool_execution(client, server, auth_headers):
    """Test tool execution endpoint."""
    # Mock tool
    mock_tool = Mock()
    async def mock_execute_tool(tool_id, params):
        return {
            "status": "success",
            "result": {"test": "data"}
        }
    mock_tool.execute_tool = mock_execute_tool
    server.tools["test_tool"] = mock_tool

    # Test successful execution
    response = client.post(
        "/tools/test_tool/execute",
        json={"params": {"test": "value"}},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"] == {"test": "data"}

def test_resource_access(client, server, auth_headers):
    """Test resource access endpoint."""
    # Mock resource
    mock_resource = Mock()
    async def mock_get_resource(params):
        return {
            "status": "success",
            "content": "test content",
            "mime_type": "text/plain"
        }
    mock_resource.get_resource = mock_get_resource
    server.resources["test_resource"] = mock_resource

    # Test successful access
    response = client.post(
        "/resources/test_resource/access",
        json={"params": {"test": "value"}},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["content"] == "test content"
    assert data["mime_type"] == "text/plain"

def test_diagnostics(client, auth_headers):
    """Test diagnostics endpoints."""
    # Test get diagnostics
    response = client.get("/diagnostics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "uptime" in data
    assert "metrics" in data
    assert "errors" in data
    assert "warnings" in data

def test_cache_operations(client, auth_headers):
    """Test cache operations."""
    # Test clear cache
    response = client.post("/cache/clear", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

@pytest.mark.asyncio
async def test_event_handling(client, server):
    """Test event handling."""
    # Mock event handler
    mock_handler = Mock()
    mock_handler.handle_event = Mock()
    server.event_handlers["test_event"] = [mock_handler]
    
    # Test event emission
    await server._emit_event("test_event", {"test": "data"})
    mock_handler.handle_event.assert_called_once_with("test_event", {"test": "data"})
    
    # Test event handler error
    mock_handler.handle_event.side_effect = Exception("Test error")
    await server._emit_event("test_event", {"test": "data"})
    # Should not raise exception, just log error

def test_validation(client):
    """Test input validation."""
    # Test invalid tool parameters
    response = client.post(
        "/tools/test/execute",
        json={"invalid": "params"},
        headers={"Authorization": "Bearer test_key"}
    )
    assert response.status_code == 422
    
    # Test invalid resource parameters
    response = client.post(
        "/resources/test/access",
        json={"invalid": "params"},
        headers={"Authorization": "Bearer test_key"}
    )
    assert response.status_code == 422 