import logging
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from ..extractor.cad_context import CADContextExtractor
from ..resources.base import ResourceProvider

logger = logging.getLogger(__name__)


class CADModelResourceProvider(ResourceProvider):
    """Resource provider for CAD model data."""

    def __init__(self, freecad_app=None):
        """
        Initialize the CAD model resource provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
        """
        self.extractor = CADContextExtractor(freecad_app)

    async def get_resource(
        self, uri: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve a CAD model resource.

        Args:
            uri: The resource URI in format "cad://model/[document_name]/[resource_type]"
            params: Optional parameters for the resource

        Returns:
            The resource data
        """
        logger.info(f"Retrieving CAD model resource: {uri}")

        # Parse the URI to determine what information is being requested
        # Format: "cad://model/[document_name]/[resource_type]"
        parsed_uri = urlparse(uri)

        if parsed_uri.scheme != "cad":
            raise ValueError(f"Invalid URI scheme: {parsed_uri.scheme}, expected 'cad'")

        path_parts = parsed_uri.path.strip("/").split("/")

        if len(path_parts) < 2 or path_parts[0] != "model":
            raise ValueError(f"Invalid URI format: {uri}, expected 'cad://model/...'")

        # Handle special case: if document_name is 'current', use active document
        if path_parts[1] == "current":
            return await self._handle_current_document_resource(
                path_parts[2:] if len(path_parts) > 2 else [], params
            )
        else:
            # Handle specific document
            document_name = path_parts[1]
            return await self._handle_document_resource(
                document_name, path_parts[2:] if len(path_parts) > 2 else [], params
            )

    async def _handle_current_document_resource(
        self, resource_path: list, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle resource requests for the current document."""
        if not resource_path:
            # Return information about the active document
            context = self.extractor.extract_full_context()
            return context.get("active_document", {"error": "No active document"})

        resource_type = resource_path[0]

        if resource_type == "objects":
            # Return list of objects in the active document
            context = self.extractor.extract_full_context()
            active_doc = context.get("active_document", {})
            return {"objects": active_doc.get("objects", [])}

        elif resource_type == "tree":
            # Return object hierarchy of the active document
            context = self.extractor.extract_full_context()
            active_doc = context.get("active_document", {})
            return {"hierarchy": active_doc.get("object_hierarchy", {})}

        elif resource_type == "selection":
            # Return currently selected objects
            context = self.extractor.extract_full_context()
            return {"selection": context.get("selection", [])}

        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

    async def _handle_document_resource(
        self,
        document_name: str,
        resource_path: list,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle resource requests for a specific document."""
        # This is simplified for now, would need to handle specific document lookup
        context = self.extractor.extract_full_context()

        # Find the specified document in the list of documents
        doc_info = None
        for doc in context.get("documents", []):
            if doc.get("name") == document_name:
                doc_info = doc
                break

        if not doc_info:
            return {"error": f"Document not found: {document_name}"}

        # For now, we only support basic document info
        # In a full implementation, we would need to extract specific document context
        return {"document": doc_info}
