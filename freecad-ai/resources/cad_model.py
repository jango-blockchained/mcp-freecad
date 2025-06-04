import logging
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from .base import ResourceProvider

logger = logging.getLogger(__name__)


class CADModelResourceProvider(ResourceProvider):
    """Resource provider for CAD model data."""

    def __init__(self, freecad_app=None):
        """
        Initialize the CAD model resource provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
        """
        self.app = freecad_app
        if self.app is None:
            try:
                import FreeCAD
                self.app = FreeCAD
                logger.info("Connected to FreeCAD for CAD model data")
            except ImportError:
                logger.warning("Could not import FreeCAD. Make sure it's installed and in your Python path.")
                self.app = None

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
        if self.app is None:
            return {"error": "FreeCAD not available"}

        if not resource_path:
            # Return information about the active document
            if self.app.ActiveDocument:
                doc = self.app.ActiveDocument
                return {
                    "name": doc.Name,
                    "label": doc.Label,
                    "objects_count": len(doc.Objects)
                }
            else:
                return {"error": "No active document"}

        resource_type = resource_path[0]

        if resource_type == "objects":
            # Return list of objects in the active document
            if self.app.ActiveDocument:
                objects = []
                for obj in self.app.ActiveDocument.Objects:
                    objects.append({
                        "name": obj.Name,
                        "label": obj.Label,
                        "type": obj.TypeId
                    })
                return {"objects": objects}
            else:
                return {"error": "No active document"}

        elif resource_type == "tree":
            # Return object hierarchy of the active document
            # This is simplified - a full implementation would build the actual tree
            return {"hierarchy": {"note": "Tree view not yet implemented"}}

        elif resource_type == "selection":
            # Return currently selected objects
            import FreeCADGui
            if hasattr(FreeCADGui, 'Selection'):
                selection = []
                for obj in FreeCADGui.Selection.getSelection():
                    selection.append({
                        "name": obj.Name,
                        "label": obj.Label,
                        "type": obj.TypeId
                    })
                return {"selection": selection}
            else:
                return {"selection": []}

        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

    async def _handle_document_resource(
        self,
        document_name: str,
        resource_path: list,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle resource requests for a specific document."""
        if self.app is None:
            return {"error": "FreeCAD not available"}

        # Find the specified document
        doc = self.app.getDocument(document_name)

        if not doc:
            return {"error": f"Document not found: {document_name}"}

        # Return basic document info
        doc_info = {
            "name": doc.Name,
            "label": doc.Label,
            "objects_count": len(doc.Objects)
        }

        return {"document": doc_info}
