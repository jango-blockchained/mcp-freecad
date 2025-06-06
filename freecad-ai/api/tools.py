import logging
from typing import Any, Dict

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel

    FASTAPI_AVAILABLE = True
except ImportError:
    # FastAPI not available, create minimal stubs
    FASTAPI_AVAILABLE = False
    APIRouter = None
    HTTPException = Exception
    BaseModel = object

try:
    from ..core.server import MCPServer
except ImportError:
    # Fallback for when module is loaded by FreeCAD
    import os
    import sys

    addon_dir = os.path.dirname(os.path.dirname(__file__))
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)
    from core.server import MCPServer

logger = logging.getLogger(__name__)


class ToolRequest(BaseModel):
    parameters: Dict[str, Any] = {}


class ToolResponse(BaseModel):
    tool_id: str
    status: str
    result: Dict[str, Any]


def create_tool_router(server: MCPServer):
    """Create a router for tool endpoints."""
    if not FASTAPI_AVAILABLE:
        logger.warning("FastAPI not available, tool router disabled")
        return None

    router = APIRouter(
        prefix="/tools",
        tags=["tools"],
        responses={404: {"description": "Tool not found"}},
    )

    @router.post("/primitives.{tool_id}")
    async def execute_primitive_tool(tool_id: str, tool_request: Dict[str, Any]):
        """Execute a primitive creation tool."""
        logger.info(f"Tool request: primitives.{tool_id}")

        if "primitives" not in server.tools:
            raise HTTPException(
                status_code=404, detail="Primitive tool provider not found"
            )

        tool_provider = server.tools["primitives"]

        try:
            return await tool_provider.execute_tool(
                tool_id, tool_request.get("parameters", {})
            )
        except Exception as e:
            logger.error(f"Error executing primitive tool: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/model_manipulation.{tool_id}")
    async def execute_model_manipulation_tool(
        tool_id: str, tool_request: Dict[str, Any]
    ):
        """Execute a model manipulation tool."""
        logger.info(f"Tool request: model_manipulation.{tool_id}")

        if "model_manipulation" not in server.tools:
            raise HTTPException(
                status_code=404, detail="Model manipulation tool provider not found"
            )

        tool_provider = server.tools["model_manipulation"]

        try:
            return await tool_provider.execute_tool(
                tool_id, tool_request.get("parameters", {})
            )
        except Exception as e:
            logger.error(f"Error executing model manipulation tool: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/measurement.{tool_id}")
    async def execute_measurement_tool(tool_id: str, tool_request: Dict[str, Any]):
        """Execute a measurement tool."""
        logger.info(f"Tool request: measurement.{tool_id}")

        if "measurement" not in server.tools:
            raise HTTPException(
                status_code=404, detail="Measurement tool provider not found"
            )

        tool_provider = server.tools["measurement"]

        try:
            return await tool_provider.execute_tool(
                tool_id, tool_request.get("parameters", {})
            )
        except Exception as e:
            logger.error(f"Error executing measurement tool: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
