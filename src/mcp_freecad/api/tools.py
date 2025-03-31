from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Body
from pydantic import BaseModel

class ToolRequest(BaseModel):
    parameters: Dict[str, Any] = {}

class ToolResponse(BaseModel):
    tool_id: str
    status: str
    result: Dict[str, Any]

def create_tool_router(mcp_server):
    """Create a FastAPI router for tools."""
    router = APIRouter()
    
    @router.post("/tools/{tool_id}")
    async def execute_tool(
        tool_id: str,
        request: ToolRequest,
        authorization: Optional[str] = Header(None)
    ) -> ToolResponse:
        """Execute a tool from the MCP server."""
        # Check if this tool provider is registered
        provider_id, _, specific_tool_id = tool_id.partition(".")
        if provider_id not in mcp_server.tools:
            raise HTTPException(status_code=404, detail=f"Tool provider not found: {provider_id}")
            
        # Authenticate the request
        if authorization:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            if not await mcp_server.auth_manager.authenticate(token):
                raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Get the tool provider
        provider = mcp_server.tools[provider_id]
        
        try:
            # Execute the tool
            result = await provider.execute_tool(specific_tool_id, request.parameters)
            
            # Return the response
            return ToolResponse(
                tool_id=tool_id,
                status="success",
                result=result
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error executing tool: {str(e)}")
    
    return router 