import logging
import math
from typing import Any, Dict, List, Optional

from ..extractor.cad_context import CADContextExtractor
from ..tools.base import ToolProvider

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

    async def execute_tool(
        self, tool_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a model manipulation tool.

        Args:
            tool_id: The ID of the tool to execute
            params: The parameters for the tool

        Returns:
            The result of the tool execution
        """
        logger.info(f"Executing model manipulation tool: {tool_id}")

        # Check if FreeCAD is available
        if self.app is None:
            return {
                "status": "error",
                "message": "FreeCAD is not available. Cannot execute model manipulation tool.",
                "mock": True,
            }

        # Handle different tools
        if tool_id == "transform":
            return await self._transform_object(params)
        elif tool_id == "boolean_operation":
            return await self._boolean_operation(params)
        elif tool_id == "fillet_edge":
            return await self._fillet_edge(params)
        elif tool_id == "chamfer_edge":
            return await self._chamfer_edge(params)
        elif tool_id == "mirror":
            return await self._mirror_object(params)
        elif tool_id == "scale":
            return await self._scale_object(params)
        elif tool_id == "offset":
            return await self._offset_object(params)
        elif tool_id == "thicken":
            return await self._thicken_object(params)
        else:
            logger.error(f"Unknown tool ID: {tool_id}")
            return {"status": "error", "message": f"Unknown tool ID: {tool_id}"}

    async def _transform_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform an object by translation, rotation, and/or mirror."""
        try:
            # Get required parameters
            object_name = params.get("object")
            if not object_name:
                return {
                    "status": "error",
                    "message": "No object specified for transformation",
                }

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {
                    "status": "error",
                    "message": f"Object not found: {object_name}",
                }

            # Check if object has a placement
            if not hasattr(obj, "Placement"):
                return {
                    "status": "error",
                    "message": f"Object {object_name} does not support transformations",
                }

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
                    return {
                        "status": "error",
                        "message": "Invalid translation format. Expected [x, y, z]",
                    }

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
                        return {"status": "error", "message": "Invalid rotation format"}
                else:
                    return {"status": "error", "message": "Invalid rotation format"}

            # Update the document
            doc.recompute()

            # Return the result
            if not modifications:
                return {
                    "status": "warning",
                    "message": "No transformations applied",
                    "object": object_name,
                }

            return {
                "status": "success",
                "message": f"Object {object_name} transformed: "
                + ", ".join(modifications),
                "object": object_name,
                "modifications": modifications,
            }

        except Exception as e:
            logger.error(f"Error transforming object: {e}")
            return {
                "status": "error",
                "message": f"Error transforming object: {str(e)}",
            }

    async def _boolean_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a boolean operation between two objects."""
        try:
            # Get required parameters
            operation_type = params.get("operation")
            if not operation_type:
                return {"status": "error", "message": "No operation type specified"}

            object1 = params.get("object1")
            object2 = params.get("object2")
            if not object1 or not object2:
                return {
                    "status": "error",
                    "message": "Two objects are required for boolean operations",
                }

            result_name = params.get("result_name", "BooleanResult")

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}

            # Get the objects
            obj1 = doc.getObject(object1)
            obj2 = doc.getObject(object2)

            if not obj1:
                return {"status": "error", "message": f"Object not found: {object1}"}
            if not obj2:
                return {"status": "error", "message": f"Object not found: {object2}"}

            # Check if objects have shapes
            if not hasattr(obj1, "Shape") or not hasattr(obj2, "Shape"):
                return {
                    "status": "error",
                    "message": "Objects must have shapes for boolean operations",
                }

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
                return {
                    "status": "error",
                    "message": f"Unknown operation type: {operation_type}",
                }

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
                "status": "success",
                "message": f"{operation_name} of {object1} and {object2} created as {result_name}",
                "result_object": result_name,
                "operation": operation_type,
            }

        except Exception as e:
            logger.error(f"Error performing boolean operation: {e}")
            return {
                "status": "error",
                "message": f"Error performing boolean operation: {str(e)}",
            }

    async def _fillet_edge(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fillet on edges of an object."""
        try:
            # Get required parameters
            object_name = params.get("object")
            if not object_name:
                return {
                    "status": "error",
                    "message": "No object specified for filleting",
                }

            radius = params.get("radius")
            if radius is None:
                return {"status": "error", "message": "No radius specified for fillet"}

            # Get edge indices (optional)
            edge_indices = params.get("edges", [])

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {
                    "status": "error",
                    "message": f"Object not found: {object_name}",
                }

            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                return {
                    "status": "error",
                    "message": f"Object {object_name} does not have a shape",
                }

            # Get edges to fillet
            edges = []
            if edge_indices:
                # Use specified edges
                for idx in edge_indices:
                    if idx < len(obj.Shape.Edges):
                        edges.append(obj.Shape.Edges[idx])
                    else:
                        return {
                            "status": "error",
                            "message": f"Edge index out of range: {idx}",
                        }
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
                "status": "success",
                "message": f"Fillet created on {object_name} with radius {radius}",
                "result_object": result_name,
                "radius": radius,
                "edge_count": len(edges),
            }

        except Exception as e:
            logger.error(f"Error creating fillet: {e}")
            return {"status": "error", "message": f"Error creating fillet: {str(e)}"}

    async def _chamfer_edge(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chamfer on edges of an object."""
        try:
            # Get required parameters
            object_name = params.get("object")
            if not object_name:
                return {
                    "status": "error",
                    "message": "No object specified for chamfering",
                }

            distance = params.get("distance")
            if distance is None:
                return {
                    "status": "error",
                    "message": "No distance specified for chamfer",
                }

            # Get optional second distance for asymmetric chamfer
            distance2 = params.get("distance2", distance)

            # Get edge indices (optional)
            edge_indices = params.get("edges", [])

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {
                    "status": "error",
                    "message": f"Object not found: {object_name}",
                }

            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                return {
                    "status": "error",
                    "message": f"Object {object_name} does not have a shape",
                }

            # Get edges to chamfer
            edges = []
            if edge_indices:
                # Use specified edges
                for idx in edge_indices:
                    if idx < len(obj.Shape.Edges):
                        edges.append(obj.Shape.Edges[idx])
                    else:
                        return {
                            "status": "error",
                            "message": f"Edge index out of range: {idx}",
                        }
            else:
                # Use all edges
                edges = obj.Shape.Edges

            # Create chamfer
            result_shape = obj.Shape.makeChamfer(distance, distance2, edges)

            # Create a new object with the chamfered shape
            result_name = params.get("result_name", f"{object_name}_Chamfered")
            result_obj = doc.addObject("Part::Feature", result_name)
            result_obj.Shape = result_shape

            # Optionally hide the original object
            hide_original = params.get("hide_original", False)
            if hide_original and hasattr(self.app, "Gui"):
                self.app.Gui.hideObject(obj)

            # Update the document
            doc.recompute()

            # Return the result
            chamfer_type = "symmetric" if distance == distance2 else "asymmetric"
            return {
                "status": "success",
                "message": f"{chamfer_type.capitalize()} chamfer created on {object_name} with distance {distance}",
                "result_object": result_name,
                "distance": distance,
                "distance2": distance2,
                "edge_count": len(edges),
                "chamfer_type": chamfer_type,
            }

        except Exception as e:
            logger.error(f"Error creating chamfer: {e}")
            return {"status": "error", "message": f"Error creating chamfer: {str(e)}"}

    async def _mirror_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mirror an object across a plane."""
        try:
            # Get required parameters
            object_name = params.get("object")
            if not object_name:
                return {
                    "status": "error",
                    "message": "No object specified for mirroring",
                }

            # Get mirror plane - either by normal vector or by standard plane name
            plane = params.get("plane")
            normal = params.get("normal")

            if not plane and not normal:
                return {
                    "status": "error",
                    "message": "No mirror plane or normal vector specified",
                }

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {
                    "status": "error",
                    "message": f"Object not found: {object_name}",
                }

            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                return {
                    "status": "error",
                    "message": f"Object {object_name} does not have a shape",
                }

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
                    return {
                        "status": "error",
                        "message": f"Unknown plane: {plane}. Use 'xy', 'xz', 'yz', 'x', 'y', or 'z'",
                    }
            else:
                # Custom normal vector
                if isinstance(normal, list) and len(normal) == 3:
                    mirror_vec = self.app.Vector(normal[0], normal[1], normal[2])
                else:
                    return {
                        "status": "error",
                        "message": "Invalid normal vector format. Expected [x, y, z]",
                    }

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
                "status": "success",
                "message": f"Object {object_name} mirrored across {plane_name}",
                "result_object": result_name,
                "mirror_plane": plane_name,
            }

        except Exception as e:
            logger.error(f"Error mirroring object: {e}")
            return {"status": "error", "message": f"Error mirroring object: {str(e)}"}

    async def _scale_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scale an object uniformly or non-uniformly."""
        try:
            # Get required parameters
            object_name = params.get("object")
            if not object_name:
                return {"status": "error", "message": "No object specified for scaling"}

            # Get scale factors
            scale = params.get("scale")
            scale_x = params.get("scale_x")
            scale_y = params.get("scale_y")
            scale_z = params.get("scale_z")

            # Check if we have any scale factors
            if (
                scale is None
                and scale_x is None
                and scale_y is None
                and scale_z is None
            ):
                return {"status": "error", "message": "No scale factors specified"}

            # If uniform scale is provided, use it for all axes
            if scale is not None:
                scale_x = scale_y = scale_z = scale

            # Default to 1.0 (no scaling) for any unspecified axes
            scale_x = scale_x if scale_x is not None else 1.0
            scale_y = scale_y if scale_y is not None else 1.0
            scale_z = scale_z if scale_z is not None else 1.0

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {
                    "status": "error",
                    "message": f"Object not found: {object_name}",
                }

            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                return {
                    "status": "error",
                    "message": f"Object {object_name} does not have a shape",
                }

            # Create a transformation matrix for scaling
            scale_transform = self.app.Matrix()
            scale_transform.unity()

            # Set the scale factors
            scale_transform.A11 = scale_x
            scale_transform.A22 = scale_y
            scale_transform.A33 = scale_z

            # Apply the transformation to create the scaled shape
            result_shape = obj.Shape.transformed(scale_transform)

            # Create a new object with the scaled shape
            result_name = params.get("result_name", f"{object_name}_Scaled")
            result_obj = doc.addObject("Part::Feature", result_name)
            result_obj.Shape = result_shape

            # Optionally hide the original object
            hide_original = params.get("hide_original", False)
            if hide_original and hasattr(self.app, "Gui"):
                self.app.Gui.hideObject(obj)

            # Update the document
            doc.recompute()

            # Determine if scaling was uniform or non-uniform
            is_uniform = scale_x == scale_y == scale_z
            scale_type = "uniform" if is_uniform else "non-uniform"

            # Return the result
            if is_uniform:
                scale_message = f"by factor {scale_x}"
            else:
                scale_message = f"by factors (x:{scale_x}, y:{scale_y}, z:{scale_z})"

            return {
                "status": "success",
                "message": f"Object {object_name} scaled {scale_message}",
                "result_object": result_name,
                "scale_x": scale_x,
                "scale_y": scale_y,
                "scale_z": scale_z,
                "scale_type": scale_type,
            }

        except Exception as e:
            logger.error(f"Error scaling object: {e}")
            return {"status": "error", "message": f"Error scaling object: {str(e)}"}

    async def _offset_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an offset of a face or shell."""
        try:
            # Get required parameters
            object_name = params.get("object")
            if not object_name:
                return {"status": "error", "message": "No object specified for offset"}

            offset = params.get("offset")
            if offset is None:
                return {"status": "error", "message": "No offset distance specified"}

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {
                    "status": "error",
                    "message": f"Object not found: {object_name}",
                }

            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                return {
                    "status": "error",
                    "message": f"Object {object_name} does not have a shape",
                }

            # Get optional parameters
            tolerance = params.get("tolerance", 0.1)
            intersection = params.get("intersection", False)
            self_intersection = params.get("self_intersection", False)
            join_type = params.get("join_type", 0)  # 0=arc, 1=tangent, 2=intersection

            # Create the offset shape
            result_shape = obj.Shape.makeOffset(
                offset, tolerance, intersection, self_intersection, join_type
            )

            # Create a new object with the offset shape
            result_name = params.get("result_name", f"{object_name}_Offset")
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
                "status": "success",
                "message": f"Offset of {object_name} created with distance {offset}",
                "result_object": result_name,
                "offset": offset,
            }

        except Exception as e:
            logger.error(f"Error creating offset: {e}")
            return {"status": "error", "message": f"Error creating offset: {str(e)}"}

    async def _thicken_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a solid by thickening a face or shell."""
        try:
            # Get required parameters
            object_name = params.get("object")
            if not object_name:
                return {
                    "status": "error",
                    "message": "No object specified for thickening",
                }

            thickness = params.get("thickness")
            if thickness is None:
                return {"status": "error", "message": "No thickness specified"}

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {
                    "status": "error",
                    "message": f"Object not found: {object_name}",
                }

            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                return {
                    "status": "error",
                    "message": f"Object {object_name} does not have a shape",
                }

            # Create the thickened shape
            result_shape = obj.Shape.makeThickness(
                obj.Shape.Faces,
                thickness,
                params.get("tolerance", 0.1),
                params.get("join_type", 0),  # 0=arc, 1=tangent, 2=intersection
                params.get("intersection", False),
                params.get("self_intersection", False),
            )

            # Create a new object with the thickened shape
            result_name = params.get("result_name", f"{object_name}_Thickened")
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
                "status": "success",
                "message": f"Thickened solid created from {object_name} with thickness {thickness}",
                "result_object": result_name,
                "thickness": thickness,
            }

        except Exception as e:
            logger.error(f"Error thickening object: {e}")
            return {"status": "error", "message": f"Error thickening object: {str(e)}"}
