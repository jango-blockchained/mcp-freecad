from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

class ResourceResponse(BaseModel):
    resource_id: str
    resource_type: str
    data: Dict[str, Any]

def create_resource_router(mcp_server):
    """Create a FastAPI router for resources."""
    router = APIRouter()
    
    @router.get("/resources/{resource_id}")
    async def get_resource(
        resource_id: str,
        authorization: Optional[str] = Header(None)
    ) -> ResourceResponse:
        """Get a resource from the MCP server."""
        # Authenticate the request
        if authorization:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            if not await mcp_server.auth_manager.authenticate(token):
                raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Parse resource ID
        provider_id, _, specific_resource_id = resource_id.partition(".")
        
        # Check if resource provider is registered
        if provider_id not in mcp_server.resources:
            raise HTTPException(status_code=404, detail=f"Resource provider not found: {provider_id}")
            
        # Get the resource provider
        provider = mcp_server.resources[provider_id]
        
        try:
            # Get the resource
            resource_data = await provider.get_resource(specific_resource_id or resource_id)
            
            # Return the response
            return ResourceResponse(
                resource_id=resource_id,
                resource_type=provider.__class__.__name__,
                data=resource_data
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting resource: {str(e)}")
    
    return router 