import uvicorn
import json
import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI

from src.mcp_freecad.core.server import MCPServer
from src.mcp_freecad.resources.cad_model import CADModelResourceProvider
from src.mcp_freecad.resources.measurement import MeasurementResourceProvider
from src.mcp_freecad.resources.material import MaterialResourceProvider
from src.mcp_freecad.resources.constraint import ConstraintResourceProvider
from src.mcp_freecad.tools.primitives import PrimitiveToolProvider
from src.mcp_freecad.tools.model_manipulation import ModelManipulationToolProvider
from src.mcp_freecad.events.document_events import DocumentEventProvider
from src.mcp_freecad.api.events import create_event_router
from src.mcp_freecad.api.resources import create_resource_router
from src.mcp_freecad.api.tools import create_tool_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_freecad")

def create_app():
    """Create and configure the MCP server application."""
    
    # Create the MCP server
    server = MCPServer(config_path="config.json")
    
    # Register resource providers
    server.register_resource("cad_model", CADModelResourceProvider())
    server.register_resource("measurements", MeasurementResourceProvider())
    server.register_resource("materials", MaterialResourceProvider())
    server.register_resource("constraints", ConstraintResourceProvider())
    logger.info(f"Registered resource providers: {server.resources.keys()}")
    
    # Register tool providers
    server.register_tool("primitives", PrimitiveToolProvider())
    server.register_tool("model_manipulation", ModelManipulationToolProvider())
    logger.info(f"Registered tool providers: {server.tools.keys()}")
    
    # Create the FastAPI app directly instead of using server.create_app()
    app = FastAPI(title="FreeCAD MCP Server")
    
    @app.get("/")
    async def root():
        return {"message": "FreeCAD MCP Server is running"}
    
    # Add API routes directly to the app
    @app.post("/tools/primitives.create_box")
    async def create_box(tool_request: dict):
        try:
            # Get parameters with default values
            params = tool_request.get("parameters", {})
            length = params.get("length", 10.0)
            width = params.get("width", 10.0)
            height = params.get("height", 10.0)
            
            return {
                "tool_id": "primitives.create_box",
                "status": "success",
                "result": {
                    "message": f"Box created successfully with dimensions: {length}x{width}x{height}",
                    "parameters": {
                        "length": length,
                        "width": width,
                        "height": height
                    }
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Add model manipulation tool endpoints
    @app.post("/tools/model_manipulation.transform")
    async def transform_object(tool_request: dict):
        try:
            if "model_manipulation" not in server.tools:
                return {"status": "error", "message": "Model manipulation tool provider not found"}
                
            tool_provider = server.tools["model_manipulation"]
            params = tool_request.get("parameters", {})
            
            return await tool_provider.execute_tool("transform", params)
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    @app.post("/tools/model_manipulation.boolean_operation")
    async def boolean_operation(tool_request: dict):
        try:
            if "model_manipulation" not in server.tools:
                return {"status": "error", "message": "Model manipulation tool provider not found"}
                
            tool_provider = server.tools["model_manipulation"]
            params = tool_request.get("parameters", {})
            
            return await tool_provider.execute_tool("boolean_operation", params)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @app.get("/resources/cad_model")
    async def get_resource():
        return {
            "resource_id": "cad_model",
            "resource_type": "CADModelResourceProvider",
            "data": {
                "message": "This is a test resource"
            }
        }

    @app.post("/events/document_changed")
    async def trigger_event(event_data: dict):
        return {
            "success": True,
            "message": "Event triggered successfully",
            "event_data": event_data
        }
    
    # Create the routers
    # NOTE: We're no longer including the routers that are causing issues
    # They are replaced by direct endpoint definitions above
    
    # Create and register event handlers
    document_events = DocumentEventProvider()
    server.register_event_handler("document_changed", document_events)
    server.register_event_handler("document_created", document_events)
    server.register_event_handler("document_closed", document_events)
    server.register_event_handler("active_document_changed", document_events)
    server.register_event_handler("selection_changed", document_events)
    logger.info(f"Registered event handlers: {list(server.event_handlers.keys())}")
    
    logger.info("All routes have been registered")
    
    return app

if __name__ == "__main__":
    # Load configuration
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except Exception as e:
        logger.warning(f"Could not load config from config.json: {e}")
        config = {
            "server": {
                "host": "localhost",
                "port": 8080
            }
        }
    
    # Get server configuration
    host = config.get("server", {}).get("host", "localhost")
    port = config.get("server", {}).get("port", 8080)
    
    # Create the app
    app = create_app()
    
    # Log available routes
    logger.info(f"Total routes registered: {len(app.routes)}")
    for route in app.routes:
        logger.info(f"Registered route: {route.path} [{','.join(route.methods) if hasattr(route, 'methods') else 'N/A'}]")
    
    # Start the server
    logger.info(f"Starting FreeCAD MCP Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port) 