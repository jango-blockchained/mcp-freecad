import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
from typing import Dict, Any
from fastapi import HTTPException

from mcp_freecad.core.server import MCPServer
from mcp_freecad.core.exceptions import (
    ToolExecutionError,
    ResourceAccessError,
    AuthenticationError,
    ValidationError
)
from mcp_freecad.core.recovery import RecoveryConfig

@pytest_asyncio.fixture
async def server():
    """Create a test server instance."""
    server = MCPServer()
    await server.initialize()
    
    # Register a test tool
    class TestTool:
        async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}
    
    server.register_tool("test", TestTool())
    
    # Register a test resource
    class TestResource:
        async def get_resource(self, resource_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
            return {"data": "test"}
    
    server.register_resource("test", TestResource())
    
    # Mock the authenticate method
    async def mock_authenticate(token: str) -> bool:
        return token == "test_token"
    server.auth_manager.authenticate = mock_authenticate
    
    return server

@pytest_asyncio.fixture
async def client(server):
    """Create a test client."""
    return TestClient(server.app)

@pytest.fixture
def auth_headers():
    """Return authentication headers for test requests."""
    return {"Authorization": "Bearer test_token"}

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_detailed_health(client):
    """Test the detailed health check endpoint."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "freecad_connection" in response.json()
    assert "cache" in response.json()

@pytest.mark.asyncio
async def test_authentication(client, auth_headers):
    """Test authentication middleware."""
    # Test without token
    with pytest.raises(HTTPException) as exc_info:
        client.post("/tools/test/execute", json={"params": {}})
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication token"
    
    # Test with valid token
    response = client.post("/tools/test/execute", json={"params": {}}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["result"] == "success"

@pytest.mark.asyncio
async def test_tool_execution(client, server, auth_headers):
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
    
    response = client.post(
        "/tools/test_tool/execute",
        json={"params": {"test": "value"}},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_resource_access(client, server, auth_headers):
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
    
    response = client.post(
        "/resources/test_resource/access",
        json={"params": {"test": "value"}},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_diagnostics(client, auth_headers):
    """Test diagnostics endpoints."""
    # Test get diagnostics
    response = client.get("/diagnostics", headers=auth_headers)
    assert response.status_code == 200
    assert "metrics" in response.json()

@pytest.mark.asyncio
async def test_cache_operations(client, auth_headers):
    """Test cache operations."""
    # Test clear cache
    response = client.post("/cache/clear", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.asyncio
async def test_event_handling(client, server):
    """Test event handling."""
    # Mock event handler
    mock_handler = Mock()
    mock_handler.handle_event = Mock()
    server.event_handlers["test_event"] = [mock_handler]
    
    # Trigger an event by executing a tool
    response = client.post(
        "/tools/test/execute",
        json={"params": {}},
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_validation(client):
    """Test input validation."""
    # Test invalid tool parameters
    response = client.post(
        "/tools/test/execute",
        json={"invalid": "params"},
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 422
    
    # Test invalid resource parameters
    response = client.post(
        "/resources/test/access",
        json={"invalid": "params"},
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 422 