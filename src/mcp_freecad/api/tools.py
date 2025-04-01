from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Body
from pydantic import BaseModel
import logging

from ..core.server import MCPServer

logger = logging.getLogger(__name__)

class ToolRequest(BaseModel):
    parameters: Dict[str, Any] = {}

class ToolResponse(BaseModel):
    tool_id: str
    status: str
    result: Dict[str, Any]

def create_tool_router(server: MCPServer) -> APIRouter:
    """Create a router for tool endpoints."""
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
            raise HTTPException(status_code=404, detail="Primitive tool provider not found")
            
        tool_provider = server.tools["primitives"]
        
        try:
            return await tool_provider.execute_tool(tool_id, tool_request.get("parameters", {}))
        except Exception as e:
            logger.error(f"Error executing primitive tool: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/model_manipulation.{tool_id}")
    async def execute_model_manipulation_tool(tool_id: str, tool_request: Dict[str, Any]):
        """Execute a model manipulation tool."""
        logger.info(f"Tool request: model_manipulation.{tool_id}")
        
        if "model_manipulation" not in server.tools:
            raise HTTPException(status_code=404, detail="Model manipulation tool provider not found")
            
        tool_provider = server.tools["model_manipulation"]
        
        try:
            return await tool_provider.execute_tool(tool_id, tool_request.get("parameters", {}))
        except Exception as e:
            logger.error(f"Error executing model manipulation tool: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/measurement.{tool_id}")
    async def execute_measurement_tool(tool_id: str, tool_request: Dict[str, Any]):
        """Execute a measurement tool."""
        logger.info(f"Tool request: measurement.{tool_id}")
        
        if "measurement" not in server.tools:
            raise HTTPException(status_code=404, detail="Measurement tool provider not found")
            
        tool_provider = server.tools["measurement"]
        
        try:
            return await tool_provider.execute_tool(tool_id, tool_request.get("parameters", {}))
        except Exception as e:
            logger.error(f"Error executing measurement tool: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router 