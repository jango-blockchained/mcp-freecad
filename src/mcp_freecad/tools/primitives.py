import logging
from typing import Any, Dict, Optional

from ..tools.base import ToolProvider

logger = logging.getLogger(__name__)


class PrimitiveToolProvider(ToolProvider):
    """Tool provider for creating primitive shapes in FreeCAD."""

    def __init__(self, freecad_app=None):
        """
        Initialize the primitive tool provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
        """
        self.app = freecad_app
        if self.app is None:
            try:
                import FreeCAD

                self.app = FreeCAD
                logger.info("Connected to FreeCAD")
            except ImportError:
                logger.warning(
                    "Could not import FreeCAD. Make sure it's installed and in your Python path."
                )
                self.app = None

    async def execute_tool(
        self, tool_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a primitive creation tool.

        Args:
            tool_id: The ID of the tool to execute
            params: Parameters for the tool

        Returns:
            The result of the tool execution
        """
        if self.app is None:
            return {"error": "FreeCAD not available"}

        if tool_id == "create_box":
            return await self._create_box(params)
        elif tool_id == "create_cylinder":
            return await self._create_cylinder(params)
        elif tool_id == "create_sphere":
            return await self._create_sphere(params)
        elif tool_id == "create_cone":
            return await self._create_cone(params)
        else:
            raise ValueError(f"Unknown tool: {tool_id}")

    async def _create_box(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a box primitive."""
        # Get parameters with default values
        length = params.get("length", 10.0)
        width = params.get("width", 10.0)
        height = params.get("height", 10.0)

        # Get or create document
        doc = self._get_active_document()

        # Create the box
        box = doc.addObject("Part::Box", "Box")
        box.Length = length
        box.Width = width
        box.Height = height

        # Recompute document
        doc.recompute()

        return {
            "status": "success",
            "object_id": box.Name,
            "object_type": "Part::Box",
            "properties": {"Length": length, "Width": width, "Height": height},
        }

    async def _create_cylinder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a cylinder primitive."""
        # Get parameters with default values
        radius = params.get("radius", 5.0)
        height = params.get("height", 10.0)

        # Get or create document
        doc = self._get_active_document()

        # Create the cylinder
        cylinder = doc.addObject("Part::Cylinder", "Cylinder")
        cylinder.Radius = radius
        cylinder.Height = height

        # Recompute document
        doc.recompute()

        return {
            "status": "success",
            "object_id": cylinder.Name,
            "object_type": "Part::Cylinder",
            "properties": {"Radius": radius, "Height": height},
        }

    async def _create_sphere(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a sphere primitive."""
        # Get parameters with default values
        radius = params.get("radius", 5.0)

        # Get or create document
        doc = self._get_active_document()

        # Create the sphere
        sphere = doc.addObject("Part::Sphere", "Sphere")
        sphere.Radius = radius

        # Recompute document
        doc.recompute()

        return {
            "status": "success",
            "object_id": sphere.Name,
            "object_type": "Part::Sphere",
            "properties": {"Radius": radius},
        }

    async def _create_cone(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a cone primitive."""
        # Get parameters with default values
        radius1 = params.get("radius1", 5.0)
        radius2 = params.get("radius2", 0.0)
        height = params.get("height", 10.0)

        # Get or create document
        doc = self._get_active_document()

        # Create the cone
        cone = doc.addObject("Part::Cone", "Cone")
        cone.Radius1 = radius1
        cone.Radius2 = radius2
        cone.Height = height

        # Recompute document
        doc.recompute()

        return {
            "status": "success",
            "object_id": cone.Name,
            "object_type": "Part::Cone",
            "properties": {"Radius1": radius1, "Radius2": radius2, "Height": height},
        }

    def _get_active_document(self):
        """Get the active document or create a new one if none exists."""
        if self.app.ActiveDocument:
            return self.app.ActiveDocument
        else:
            return self.app.newDocument("Unnamed")
