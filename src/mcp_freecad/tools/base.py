from typing import Dict, Any
from abc import ABC, abstractmethod

class ToolProvider(ABC):
    """Base class for all tool providers in the MCP server."""
    
    @abstractmethod
    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool.
        
        Args:
            tool_id: The ID of the tool to execute
            params: Parameters for the tool
            
        Returns:
            The result of the tool execution
        """
        pass 