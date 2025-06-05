from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, ValidationError


class ToolParams(BaseModel):
    """Base model for tool parameters."""

    tool_id: str = Field(..., description="The ID of the tool to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")

    class Config:
        arbitrary_types_allowed = True


class ToolResult(BaseModel):
    """Base model for tool results."""

    status: str = Field(..., description="Status of the tool execution")
    result: Optional[Dict[str, Any]] = Field(None, description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if execution failed")


class ToolSchema(BaseModel):
    """Schema definition for a tool."""

    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: Dict[str, Any] = Field(..., description="Parameter schema")
    returns: Dict[str, Any] = Field(..., description="Return value schema")
    examples: Optional[list[Dict[str, Any]]] = Field(None, description="Example usage")


class ToolProvider(ABC):
    """Base class for all tool providers in the MCP server."""

    @property
    @abstractmethod
    def tool_schema(self) -> ToolSchema:
        """
        Get the schema for this tool.

        Returns:
            ToolSchema containing the tool's schema definition
        """
        pass

    @abstractmethod
    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> ToolResult:
        """
        Execute a tool.

        Args:
            tool_id: The ID of the tool to execute
            params: Parameters for the tool

        Returns:
            ToolResult containing the execution status and result

        Raises:
            ValidationError: If the parameters are invalid
            ToolExecutionError: If the tool execution fails
        """
        pass

    def validate_params(self, params: Dict[str, Any]) -> None:
        """
        Validate tool parameters against the schema.

        Args:
            params: Parameters to validate

        Raises:
            ValidationError: If the parameters are invalid
        """
        try:
            ToolParams(**params)
        except ValidationError as e:
            raise ValueError(f"Invalid parameters: {str(e)}")

    def format_result(
        self,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> ToolResult:
        """
        Format a tool execution result.

        Args:
            status: Status of the execution
            result: Optional result data
            error: Optional error message

        Returns:
            ToolResult containing the formatted result
        """
        return ToolResult(status=status, result=result, error=error)
