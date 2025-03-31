from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class ResourceProvider(ABC):
    """Base class for all resource providers in the MCP server."""
    
    @abstractmethod
    async def get_resource(self, uri: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve a resource.
        
        Args:
            uri: The resource URI
            params: Optional parameters for the resource
            
        Returns:
            The resource data
        """
        pass 