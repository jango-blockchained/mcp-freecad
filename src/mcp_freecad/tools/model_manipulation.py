import logging
import math
from typing import Any, Dict, List, Optional

from ..extractor.cad_context import CADContextExtractor
from .base import ToolProvider, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class ModelManipulationToolProvider(ToolProvider):
    """Tool provider for manipulating and transforming CAD model objects."""

    def __init__(self, freecad_app=None):
        """
        Initialize the model manipulation tool provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
        """
        self.extractor = CADContextExtractor(freecad_app)
        self.app = freecad_app

        if self.app is None:
            try:
                import FreeCAD
                import Part

                self.app = FreeCAD
                self.Part = Part
                logger.info("Connected to FreeCAD for model manipulation")
            except ImportError:
                logger.warning(
                    "Could not import FreeCAD. Make sure it's installed and in your Python path."
                )
                self.app = None
                self.Part = None
        else:
            try:
                import Part

                self.Part = Part
            except ImportError:
                logger.warning(
                    "Could not import Part module. Some functionality may be limited."
                )
                self.Part = None

    @property
    def tool_schema(self) -> ToolSchema:
        """Get the schema for model manipulation tools."""
        return ToolSchema(
            name="model_manipulation",
            description="Manipulate and transform CAD model objects",
            parameters={
                "type": "object",
                "properties": {
                    "tool_id": {
                        "type": "string",
                        "enum": [
                            "transform",
                            "boolean_operation",
                            "fillet_edge",
                            "chamfer_edge",
                            "mirror",
                            "scale",
                            "offset",
                            "thicken",
                        ],
                        "description": "The manipulation tool to execute",
                    },
                    "params": {
                        "type": "object",
                        "description": "Parameters for the manipulation operation",
                    },
                },
                "required": ["tool_id"],
            },
            returns={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "result": {"type": "object"},
                    "error": {"type": "string"},
                },
            },
            examples=[
                {
                    "tool_id": "transform",
                    "params": {"object": "Box", "translation": [10, 0, 0]},
                },
                {
                    "tool_id": "boolean_operation",
                    "params": {
                        "operation": "union",
                        "object1": "Box",
                        "object2": "Cylinder",
                    },
                },
            ],
        )

    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> ToolResult:
        """
        Execute a model manipulation tool.

        Args:
            tool_id: The ID of the tool to execute
            params: The parameters for the tool

        Returns:
            ToolResult containing the execution status and result
        """
        logger.info(f"Executing model manipulation tool: {tool_id}")

        # Check if FreeCAD is available
        if self.app is None:
            return self.format_result(
                status="error",
                error="FreeCAD is not available. Cannot execute model manipulation tool.",
                result={"mock": True},
            )

        try:
            # Handle different tools
            if tool_id == "transform":
                result = await self._transform_object(params)
            elif tool_id == "boolean_operation":
                result = await self._boolean_operation(params)
            elif tool_id == "fillet_edge":
                result = await self._fillet_edge(params)
            elif tool_id == "chamfer_edge":
                result = await self._chamfer_edge(params)
            elif tool_id == "mirror":
                result = await self._mirror_object(params)
            elif tool_id == "scale":
                result = await self._scale_object(params)
            elif tool_id == "offset":
                result = await self._offset_object(params)
            elif tool_id == "thicken":
                result = await self._thicken_object(params)
            else:
                return self.format_result(
                    status="error", error=f"Unknown tool ID: {tool_id}"
                )

            return self.format_result(status="success", result=result)

        except Exception as e:
            logger.error(f"Error executing model manipulation tool {tool_id}: {e}")
            return self.format_result(status="error", error=str(e))

    async def _transform_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform an object by translation, rotation, and/or mirror."""
        try:
            # Get required parameters
            object_name = params.get("object")
            if not object_name:
                raise ValueError("No object specified for transformation")

            # Early validation of transformation parameters
            translation = params.get("translation")
            rotation = params.get("rotation")

            # Validate translation format if provided
            if translation is not None:
                if not isinstance(translation, list) or len(translation) != 3:
                    raise ValueError("Invalid translation format. Expected [x, y, z]")

            # Validate rotation format if provided
            if rotation is not None:
                if not isinstance(rotation, list) or len(rotation) not in [3, 4]:
                    raise ValueError("Invalid rotation format. Expected [x, y, z] or [x, y, z, angle]")

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                raise ValueError("No active document")

            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                raise ValueError(f"Object not found: {object_name}")

            # Check if object has a placement
            if not hasattr(obj, "Placement"):
                raise ValueError(
                    f"Object {object_name} does not support transformations"
                )

            # Get current placement
            current_placement = obj.Placement

            # Build the transformation
            translation = params.get("translation")
            rotation = params.get("rotation")

            modifications = []

            # Apply translation if provided
            if translation:
                if isinstance(translation, list) and len(translation) == 3:
                    # Create a translation vector
                    vec = self.app.Vector(
                        translation[0], translation[1], translation[2]
                    )

                    # Create a new placement with the translation
                    new_placement = self.app.Placement(
                        current_placement.Base.add(vec), current_placement.Rotation
                    )

                    # Apply the new placement
                    obj.Placement = new_placement

                    modifications.append(
                        f"Translated by ({translation[0]}, {translation[1]}, {translation[2]})"
                    )
                else:
                    raise ValueError("Invalid translation format. Expected [x, y, z]")

            # Apply rotation if provided
            if rotation:
                if isinstance(rotation, list) and len(rotation) >= 3:
                    # Handle different rotation formats
                    if len(rotation) == 3:
                        # Euler angles in degrees (x, y, z)
                        rot_x, rot_y, rot_z = rotation

                        # Convert to radians
                        rot_x_rad = math.radians(rot_x)
                        rot_y_rad = math.radians(rot_y)
                        rot_z_rad = math.radians(rot_z)

                        # Create rotation
                        new_rotation = current_placement.Rotation.multiply(
                            self.app.Rotation(self.app.Vector(1, 0, 0), rot_x)
                            .multiply(
                                self.app.Rotation(self.app.Vector(0, 1, 0), rot_y)
                            )
                            .multiply(
                                self.app.Rotation(self.app.Vector(0, 0, 1), rot_z)
                            )
                        )

                        # Apply the rotation
                        obj.Placement.Rotation = new_rotation

                        modifications.append(
                            f"Rotated by ({rot_x}°, {rot_y}°, {rot_z}°)"
                        )
                    elif len(rotation) == 4:
                        # Axis-angle format [x, y, z, angle]
                        axis_x, axis_y, axis_z, angle = rotation

                        # Create rotation
                        new_rotation = current_placement.Rotation.multiply(
                            self.app.Rotation(
                                self.app.Vector(axis_x, axis_y, axis_z), angle
                            )
                        )

                        # Apply the rotation
                        obj.Placement.Rotation = new_rotation

                        modifications.append(
                            f"Rotated by {angle}° around axis ({axis_x}, {axis_y}, {axis_z})"
                        )
                    else:
                        raise ValueError("Invalid rotation format")
                else:
                    raise ValueError("Invalid rotation format")

            # Update the document
            doc.recompute()

            # Return the result
            if not modifications:
                return {
                    "message": "No transformations applied",
                    "object": object_name,
                }

            return {
                "message": f"Object {object_name} transformed: "
                + ", ".join(modifications),
                "object": object_name,
                "modifications": modifications,
            }

        except Exception as e:
            logger.error(f"Error transforming object: {e}")
            raise

    async def _boolean_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a boolean operation between two objects."""
        try:
            # Get required parameters
            operation_type = params.get("operation")
            if not operation_type:
                raise ValueError("No operation type specified")

            # Validate operation type early
            valid_operations = ["union", "difference", "cut", "intersection", "common"]
            if operation_type.lower() not in valid_operations:
                raise ValueError(f"Unknown operation type: {operation_type}")

            object1 = params.get("object1")
            object2 = params.get("object2")
            if not object1 or not object2:
                raise ValueError("Two objects are required for boolean operations")

            result_name = params.get("result_name", "BooleanResult")

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                raise ValueError("No active document")

            # Get the objects
            obj1 = doc.getObject(object1)
            obj2 = doc.getObject(object2)

            if not obj1:
                raise ValueError(f"Object not found: {object1}")
            if not obj2:
                raise ValueError(f"Object not found: {object2}")

            # Check if objects have shapes
            if not hasattr(obj1, "Shape") or not hasattr(obj2, "Shape"):
                raise ValueError("Objects must have shapes for boolean operations")

            # Perform the boolean operation
            if operation_type.lower() == "union":
                result_shape = obj1.Shape.fuse(obj2.Shape)
                operation_name = "Union"
            elif (
                operation_type.lower() == "difference"
                or operation_type.lower() == "cut"
            ):
                result_shape = obj1.Shape.cut(obj2.Shape)
                operation_name = "Difference"
            elif (
                operation_type.lower() == "intersection"
                or operation_type.lower() == "common"
            ):
                result_shape = obj1.Shape.common(obj2.Shape)
                operation_name = "Intersection"
            else:
                raise ValueError(f"Unknown operation type: {operation_type}")

            # Create a new object with the result
            result_obj = doc.addObject("Part::Feature", result_name)
            result_obj.Shape = result_shape

            # Optionally hide the original objects
            hide_originals = params.get("hide_originals", False)
            if hide_originals and hasattr(self.app, "Gui"):
                self.app.Gui.hideObject(obj1)
                self.app.Gui.hideObject(obj2)

            # Update the document
            doc.recompute()

            # Return the result
            return {
                "message": f"{operation_name} of {object1} and {object2} created as {result_name}",
                "result_object": result_name,
                "operation": operation_type,
            }

        except Exception as e:
            logger.error(f"Error performing boolean operation: {e}")
            raise

    async def _fillet_edge(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fillet on edges of an object."""
        try:
            # Get required parameters
            object_name = params.get("object")
            if not object_name:
                raise ValueError("No object specified for filleting")

            radius = params.get("radius")
            if radius is None:
                raise ValueError("No radius specified for fillet")

            # Get edge indices (optional)
            edge_indices = params.get("edges", [])

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                raise ValueError("No active document")

            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                raise ValueError(f"Object not found: {object_name}")

            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                raise ValueError(f"Object {object_name} does not have a shape")

            # Get edges to fillet
            edges = []
            if edge_indices:
                # Use specified edges
                for idx in edge_indices:
                    if idx < len(obj.Shape.Edges):
                        edges.append(obj.Shape.Edges[idx])
                    else:
                        raise ValueError(f"Edge index out of range: {idx}")
            else:
                # Use all edges
                edges = obj.Shape.Edges

            # Create fillet
            result_shape = obj.Shape.makeFillet(radius, edges)

            # Create a new object with the filleted shape
            result_name = params.get("result_name", f"{object_name}_Filleted")
            result_obj = doc.addObject("Part::Feature", result_name)
            result_obj.Shape = result_shape

            # Optionally hide the original object
            hide_original = params.get("hide_original", False)
            if hide_original and hasattr(self.app, "Gui"):
                self.app.Gui.hideObject(obj)

            # Update the document
            doc.recompute()

            # Return the result
            return {
                "message": f"Fillet created on {object_name} with radius {radius}",
                "result_object": result_name,
                "radius": radius,
                "edge_count": len(edges),
            }

        except Exception as e:
            logger.error(f"Error creating fillet: {e}")
            raise

    async def _chamfer_edge(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chamfer on edges of an object."""
        # Implementation similar to fillet but using makeChamfer
        raise NotImplementedError("Chamfer edge not yet implemented")

    async def _scale_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scale an object uniformly or non-uniformly."""
        # Implementation using transformation matrix
        raise NotImplementedError("Scale object not yet implemented")

    async def _offset_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an offset of a face or shell."""
        # Implementation using makeOffset
        raise NotImplementedError("Offset object not yet implemented")

    async def _thicken_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a solid by thickening a face or shell."""
        # Implementation using makeThickness
        raise NotImplementedError("Thicken object not yet implemented")

    async def _mirror_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mirror an object across a plane."""
        try:
            # Get required parameters
            object_name = params.get("object")
            if not object_name:
                raise ValueError("No object specified for mirroring")

            # Get mirror plane - either by normal vector or by standard plane name
            plane = params.get("plane")
            normal = params.get("normal")

            if not plane and not normal:
                raise ValueError("No mirror plane or normal vector specified")

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                raise ValueError("No active document")

            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                raise ValueError(f"Object not found: {object_name}")

            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                raise ValueError(f"Object {object_name} does not have a shape")

            # Determine the mirror plane
            if plane:
                # Standard planes
                if plane.lower() == "xy" or plane.lower() == "z":
                    mirror_vec = self.app.Vector(0, 0, 1)
                elif plane.lower() == "xz" or plane.lower() == "y":
                    mirror_vec = self.app.Vector(0, 1, 0)
                elif plane.lower() == "yz" or plane.lower() == "x":
                    mirror_vec = self.app.Vector(1, 0, 0)
                else:
                    raise ValueError(
                        f"Unknown plane: {plane}. Use 'xy', 'xz', 'yz', 'x', 'y', or 'z'"
                    )
            else:
                # Custom normal vector
                if isinstance(normal, list) and len(normal) == 3:
                    mirror_vec = self.app.Vector(normal[0], normal[1], normal[2])
                else:
                    raise ValueError("Invalid normal vector format. Expected [x, y, z]")

            # Create a transformation for the mirror operation
            mirror_transform = self.app.Matrix()
            mirror_transform.unity()

            # Set up the mirror matrix based on the normal vector
            nx, ny, nz = mirror_vec.normalize()
            mirror_transform.A11 = 1 - 2 * nx * nx
            mirror_transform.A12 = -2 * nx * ny
            mirror_transform.A13 = -2 * nx * nz
            mirror_transform.A21 = -2 * ny * nx
            mirror_transform.A22 = 1 - 2 * ny * ny
            mirror_transform.A23 = -2 * ny * nz
            mirror_transform.A31 = -2 * nz * nx
            mirror_transform.A32 = -2 * nz * ny
            mirror_transform.A33 = 1 - 2 * nz * nz

            # Apply the transformation to create the mirrored shape
            result_shape = obj.Shape.transformed(mirror_transform)

            # Create a new object with the mirrored shape
            result_name = params.get("result_name", f"{object_name}_Mirrored")
            result_obj = doc.addObject("Part::Feature", result_name)
            result_obj.Shape = result_shape

            # Optionally hide the original object
            hide_original = params.get("hide_original", False)
            if hide_original and hasattr(self.app, "Gui"):
                self.app.Gui.hideObject(obj)

            # Update the document
            doc.recompute()

            # Return the result
            plane_name = (
                plane
                if plane
                else f"normal vector ({normal[0]}, {normal[1]}, {normal[2]})"
            )
            return {
                "message": f"Object {object_name} mirrored across {plane_name}",
                "result_object": result_name,
                "mirror_plane": plane_name,
            }

        except Exception as e:
            logger.error(f"Error mirroring object: {e}")
            raise
