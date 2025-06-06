import logging
import math
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .base import ResourceProvider

logger = logging.getLogger(__name__)


class MeasurementResourceProvider(ResourceProvider):
    """Resource provider for measurements in CAD models."""

    def __init__(self, freecad_app=None):
        """
        Initialize the measurement resource provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
        """
        # self.extractor = CADContextExtractor(freecad_app)  # Not needed for measurement resources
        self.app = freecad_app
        if self.app is None:
            try:
                import FreeCAD

                self.app = FreeCAD
                logger.info("Connected to FreeCAD for measurements")
            except ImportError:
                logger.warning(
                    "Could not import FreeCAD. Make sure it's installed and in your Python path."
                )
                self.app = None

    async def get_resource(
        self, uri: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve measurement data from the CAD model.

        Args:
            uri: The resource URI in format "cad://measurements/[measurement_type]/[objects]"
            params: Optional parameters for the measurement

        Returns:
            The measurement data
        """
        logger.info(f"Retrieving measurement resource: {uri}")

        # Parse the URI
        parsed_uri = urlparse(uri)

        if parsed_uri.scheme != "cad":
            raise ValueError(f"Invalid URI scheme: {parsed_uri.scheme}, expected 'cad'")

        path_parts = parsed_uri.path.strip("/").split("/")

        if len(path_parts) < 2 or path_parts[0] != "measurements":
            raise ValueError(
                f"Invalid URI format: {uri}, expected 'cad://measurements/...'"
            )

        # Get measurement type
        measurement_type = path_parts[1]

        # Handle different measurement types
        if measurement_type == "distance":
            return await self._measure_distance(path_parts[2:], params)
        elif measurement_type == "area":
            return await self._measure_area(path_parts[2:], params)
        elif measurement_type == "volume":
            return await self._measure_volume(path_parts[2:], params)
        elif measurement_type == "angle":
            return await self._measure_angle(path_parts[2:], params)
        elif measurement_type == "bounding_box":
            return await self._measure_bounding_box(path_parts[2:], params)
        else:
            raise ValueError(f"Unknown measurement type: {measurement_type}")

    async def _measure_distance(
        self, path_parts: List[str], params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Measure distance between objects or points."""
        if self.app is None:
            return self._mock_distance_measurement(path_parts, params)

        try:
            # In a real implementation, we would use FreeCAD's measurement tools
            # For now, we'll provide a simplified implementation

            # Check if we're measuring between objects or points
            if params and "points" in params:
                # Measuring between points
                points = params["points"]
                if len(points) < 2:
                    return {"error": "Need at least two points to measure distance"}

                # Calculate distance between first two points
                p1 = points[0]
                p2 = points[1]

                distance = math.sqrt(
                    (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2
                )

                return {
                    "measurement_type": "distance",
                    "value": distance,
                    "unit": "mm",
                    "points": [p1, p2],
                }
            else:
                # Measuring between objects
                # Get object names from path or params
                object_names = path_parts if path_parts else params.get("objects", [])

                if len(object_names) < 2:
                    return {"error": "Need at least two objects to measure distance"}

                # Get the active document
                doc = self.app.ActiveDocument
                if not doc:
                    return {"error": "No active document"}

                # Get the objects
                obj1 = doc.getObject(object_names[0])
                obj2 = doc.getObject(object_names[1])

                if not obj1 or not obj2:
                    return {"error": "One or both objects not found"}

                # Calculate distance between object centers
                # In a real implementation, we would use FreeCAD's measurement tools
                # This is a simplified approach using object centers
                center1 = obj1.Shape.BoundBox.Center if hasattr(obj1, "Shape") else None
                center2 = obj2.Shape.BoundBox.Center if hasattr(obj2, "Shape") else None

                if not center1 or not center2:
                    return {"error": "Could not determine object centers"}

                distance = center1.distanceToPoint(center2)

                return {
                    "measurement_type": "distance",
                    "value": distance,
                    "unit": "mm",
                    "objects": [obj1.Name, obj2.Name],
                }

        except Exception as e:
            logger.error(f"Error measuring distance: {e}")
            return {"error": f"Error measuring distance: {str(e)}"}

    def _mock_distance_measurement(
        self, path_parts: List[str], params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Provide mock distance measurement when FreeCAD is not available."""
        # Check if we're measuring between points or objects
        if params and "points" in params:
            points = params["points"]
            return {
                "measurement_type": "distance",
                "value": 10.5,  # Mock value
                "unit": "mm",
                "points": points[:2],
                "note": "Mock measurement (FreeCAD not available)",
            }
        else:
            object_names = path_parts if path_parts else params.get("objects", [])
            return {
                "measurement_type": "distance",
                "value": 25.75,  # Mock value
                "unit": "mm",
                "objects": (
                    object_names[:2]
                    if len(object_names) >= 2
                    else ["Object1", "Object2"]
                ),
                "note": "Mock measurement (FreeCAD not available)",
            }

    async def _measure_area(
        self, path_parts: List[str], params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Measure surface area of objects."""
        if self.app is None:
            return {
                "measurement_type": "area",
                "value": 100.0,  # Mock value
                "unit": "mm²",
                "object": path_parts[0] if path_parts else "Object1",
                "note": "Mock measurement (FreeCAD not available)",
            }

        try:
            # Get object name
            object_name = path_parts[0] if path_parts else params.get("object")

            if not object_name:
                return {"error": "No object specified for area measurement"}

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"error": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)

            if not obj:
                return {"error": f"Object not found: {object_name}"}

            # Calculate area
            if hasattr(obj, "Shape") and hasattr(obj.Shape, "Area"):
                area = obj.Shape.Area

                return {
                    "measurement_type": "area",
                    "value": area,
                    "unit": "mm²",
                    "object": obj.Name,
                }
            else:
                return {
                    "error": "Object does not have a valid shape for area measurement"
                }

        except Exception as e:
            logger.error(f"Error measuring area: {e}")
            return {"error": f"Error measuring area: {str(e)}"}

    async def _measure_volume(
        self, path_parts: List[str], params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Measure volume of objects."""
        if self.app is None:
            return {
                "measurement_type": "volume",
                "value": 1000.0,  # Mock value
                "unit": "mm³",
                "object": path_parts[0] if path_parts else "Object1",
                "note": "Mock measurement (FreeCAD not available)",
            }

        try:
            # Get object name
            object_name = path_parts[0] if path_parts else params.get("object")

            if not object_name:
                return {"error": "No object specified for volume measurement"}

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"error": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)

            if not obj:
                return {"error": f"Object not found: {object_name}"}

            # Calculate volume
            if hasattr(obj, "Shape") and hasattr(obj.Shape, "Volume"):
                volume = obj.Shape.Volume

                return {
                    "measurement_type": "volume",
                    "value": volume,
                    "unit": "mm³",
                    "object": obj.Name,
                }
            else:
                return {
                    "error": "Object does not have a valid shape for volume measurement"
                }

        except Exception as e:
            logger.error(f"Error measuring volume: {e}")
            return {"error": f"Error measuring volume: {str(e)}"}

    async def _measure_angle(
        self, path_parts: List[str], params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Measure angle between edges, faces, or vectors."""
        # This would be a more complex implementation using FreeCAD's tools
        # For simplicity, we'll return a mock value
        return {
            "measurement_type": "angle",
            "value": 45.0,  # Mock value
            "unit": "degrees",
            "objects": path_parts if path_parts else ["Edge1", "Edge2"],
            "note": "This is a simplified implementation. A complete implementation would use FreeCAD's measurement tools.",
        }

    async def _measure_bounding_box(
        self, path_parts: List[str], params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get bounding box dimensions of an object."""
        if self.app is None:
            return {
                "measurement_type": "bounding_box",
                "dimensions": {"length": 10.0, "width": 10.0, "height": 10.0},
                "unit": "mm",
                "object": path_parts[0] if path_parts else "Object1",
                "note": "Mock measurement (FreeCAD not available)",
            }

        try:
            # Get object name
            object_name = path_parts[0] if path_parts else params.get("object")

            if not object_name:
                return {"error": "No object specified for bounding box measurement"}

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"error": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)

            if not obj:
                return {"error": f"Object not found: {object_name}"}

            # Get bounding box
            if hasattr(obj, "Shape") and hasattr(obj.Shape, "BoundBox"):
                bb = obj.Shape.BoundBox

                return {
                    "measurement_type": "bounding_box",
                    "dimensions": {
                        "length": bb.XLength,
                        "width": bb.YLength,
                        "height": bb.ZLength,
                    },
                    "corners": {
                        "min": [bb.XMin, bb.YMin, bb.ZMin],
                        "max": [bb.XMax, bb.YMax, bb.ZMax],
                    },
                    "center": [bb.Center.x, bb.Center.y, bb.Center.z],
                    "unit": "mm",
                    "object": obj.Name,
                }
            else:
                return {
                    "error": "Object does not have a valid shape for bounding box measurement"
                }

        except Exception as e:
            logger.error(f"Error measuring bounding box: {e}")
            return {"error": f"Error measuring bounding box: {str(e)}"}
