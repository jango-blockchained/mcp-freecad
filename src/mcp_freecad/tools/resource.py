from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, ValidationError


class ResourceParams(BaseModel):
    """Base model for resource parameters."""

    resource_id: str = Field(..., description="The ID of the resource to access")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Resource parameters"
    )

    class Config:
        arbitrary_types_allowed = True


class ResourceResult(BaseModel):
    """Base model for resource results."""

    status: str = Field(..., description="Status of the resource access")
    content: Optional[Any] = Field(None, description="Resource content")
    mime_type: Optional[str] = Field(None, description="MIME type of the content")
    error: Optional[str] = Field(None, description="Error message if access failed")


class ResourceSchema(BaseModel):
    """Schema definition for a resource."""

    name: str = Field(..., description="Name of the resource")
    description: str = Field(
        ..., description="Description of what the resource provides"
    )
    parameters: Dict[str, Any] = Field(..., description="Parameter schema")
    content_type: str = Field(..., description="Expected content type")
    examples: Optional[list[Dict[str, Any]]] = Field(None, description="Example usage")


class ResourceProvider(ABC):
    """Base class for all resource providers in the MCP server."""

    @property
    @abstractmethod
    def resource_schema(self) -> ResourceSchema:
        """
        Get the schema for this resource.

        Returns:
            ResourceSchema containing the resource's schema definition
        """
        pass

    @abstractmethod
    async def get_resource(
        self, resource_id: str, params: Dict[str, Any]
    ) -> ResourceResult:
        """
        Get a resource.

        Args:
            resource_id: The ID of the resource to get
            params: Parameters for accessing the resource

        Returns:
            ResourceResult containing the resource content and metadata

        Raises:
            ValidationError: If the parameters are invalid
            ResourceAccessError: If the resource cannot be accessed
        """
        pass

    def validate_params(self, params: Dict[str, Any]) -> None:
        """
        Validate resource parameters against the schema.

        Args:
            params: Parameters to validate

        Raises:
            ValidationError: If the parameters are invalid
        """
        try:
            ResourceParams(**params)
        except ValidationError as e:
            raise ValidationError(f"Invalid parameters: {str(e)}")

    def format_result(
        self,
        status: str,
        content: Optional[Any] = None,
        mime_type: Optional[str] = None,
        error: Optional[str] = None,
    ) -> ResourceResult:
        """
        Format a resource access result.

        Args:
            status: Status of the access
            content: Optional resource content
            mime_type: Optional MIME type
            error: Optional error message

        Returns:
            ResourceResult containing the formatted result
        """
        return ResourceResult(
            status=status, content=content, mime_type=mime_type, error=error
        )
