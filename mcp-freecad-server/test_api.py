import requests
import json
import sys

def test_root():
    """Test the root endpoint."""
    url = "http://localhost:8080/"
    response = requests.get(url)
    print(f"Root endpoint: {response.status_code}")
    print(response.json())
    print()

def test_openapi():
    """Test the OpenAPI schema."""
    url = "http://localhost:8080/openapi.json"
    response = requests.get(url)
    print(f"OpenAPI schema: {response.status_code}")
    print()

def test_create_box():
    """Test the create_box tool."""
    url = "http://localhost:8080/tools/primitives.create_box"
    data = {
        "parameters": {
            "length": 20.0,
            "width": 15.0,
            "height": 10.0
        }
    }
    response = requests.post(url, json=data)
    print(f"Create box: {response.status_code}")
    if response.status_code == 200:
        print(response.json())
    else:
        print(response.text)
    print()
    
def test_get_resource():
    """Test getting a resource."""
    url = "http://localhost:8080/resources/cad_model"
    response = requests.get(url)
    print(f"Get resource: {response.status_code}")
    if response.status_code == 200:
        print(response.json())
    else:
        print(response.text)
    print()
    
def test_trigger_event():
    """Test triggering an event."""
    url = "http://localhost:8080/events/document_changed"
    data = {
        "event_type": "document_changed",
        "data": {
            "document": "test_document",
            "timestamp": 1234567890
        }
    }
    response = requests.post(url, json=data)
    print(f"Trigger event: {response.status_code}")
    if response.status_code == 200:
        print(response.json())
    else:
        print(response.text)
    print()
    
if __name__ == "__main__":
    print("Testing FreeCAD MCP Server API...")
    print("=================================")
    
    # Test root endpoint
    print("Testing root endpoint...")
    try:
        test_root()
    except Exception as e:
        print(f"Error testing root endpoint: {e}")
        sys.exit(1)
    
    # Test OpenAPI schema
    print("Testing OpenAPI schema...")
    try:
        test_openapi()
    except Exception as e:
        print(f"Error testing OpenAPI schema: {e}")
    
    # Test create_box tool
    print("Testing create_box tool...")
    try:
        test_create_box()
    except Exception as e:
        print(f"Error testing create_box tool: {e}")
    
    # Test get resource
    print("Testing get resource...")
    try:
        test_get_resource()
    except Exception as e:
        print(f"Error testing get resource: {e}")
    
    # Test trigger event
    print("Testing trigger event...")
    try:
        test_trigger_event()
    except Exception as e:
        print(f"Error testing trigger event: {e}")
        
    print("Tests completed.") 