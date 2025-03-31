import pytest
from fastapi.testclient import TestClient

from app import create_app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app()
    with TestClient(app) as client:
        yield client

def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FreeCAD MCP Server is running"}

def test_resource_endpoint(client):
    """Test the resource endpoint."""
    response = client.get("/resources/cad_model")
    assert response.status_code == 200
    assert response.json()["resource_id"] == "cad_model"
    assert response.json()["resource_type"] == "CADModelResourceProvider"
    assert "data" in response.json()

def test_tool_endpoint(client):
    """Test the tool endpoint."""
    data = {
        "parameters": {
            "length": 20.0,
            "width": 15.0,
            "height": 10.0
        }
    }
    response = client.post("/tools/primitives.create_box", json=data)
    assert response.status_code == 200
    assert response.json()["tool_id"] == "primitives.create_box"
    assert response.json()["status"] == "success"
    assert "result" in response.json()

def test_event_endpoint(client):
    """Test the event endpoint."""
    data = {
        "event_type": "document_changed",
        "data": {
            "document": "test_document",
            "timestamp": 1234567890
        }
    }
    response = client.post("/events/document_changed", json=data)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "event_data" in response.json() 