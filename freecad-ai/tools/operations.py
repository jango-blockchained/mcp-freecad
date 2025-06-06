"""
Operations Tool

MCP tool for performing boolean operations (union, cut, intersection) and
other geometric operations on FreeCAD objects.

Author: jango-blockchained
"""

from typing import Any, Dict, Optional

import FreeCAD as App


class OperationsTool:
    """Tool for performing boolean and geometric operations on objects."""

    def __init__(self):
        """Initialize the operations tool."""
        self.name = "operations"
        self.description = "Perform boolean and geometric operations on objects"

    def _get_object(self, obj_name: str, doc: Any = None) -> Optional[Any]:
        """Get an object by name from the document.

        Args:
            obj_name: Name of the object to find
            doc: Document to search in (uses ActiveDocument if None)

        Returns:
            The FreeCAD object or None if not found
        """
        if doc is None:
            doc = App.ActiveDocument
        if not doc:
            return None

        return doc.getObject(obj_name)

    def _validate_objects(self, obj1_name: str, obj2_name: str) -> tuple:
        """Validate that two objects exist and have valid shapes.

        Args:
            obj1_name: Name of first object
            obj2_name: Name of second object

        Returns:
            Tuple of (success, obj1, obj2, error_message)
        """
        doc = App.ActiveDocument
        if not doc:
            return False, None, None, "No active document"

        obj1 = self._get_object(obj1_name, doc)
        if not obj1:
            return False, None, None, f"Object '{obj1_name}' not found"

        obj2 = self._get_object(obj2_name, doc)
        if not obj2:
            return False, None, None, f"Object '{obj2_name}' not found"

        if not hasattr(obj1, "Shape") or not obj1.Shape:
            return False, None, None, f"Object '{obj1_name}' has no valid shape"

        if not hasattr(obj2, "Shape") or not obj2.Shape:
            return False, None, None, f"Object '{obj2_name}' has no valid shape"

        return True, obj1, obj2, None

    def boolean_union(
        self,
        obj1_name: str,
        obj2_name: str,
        result_name: str = None,
        keep_originals: bool = False,
    ) -> Dict[str, Any]:
        """Perform a boolean union (fuse) operation on two objects.

        Args:
            obj1_name: Name of first object
            obj2_name: Name of second object
            result_name: Optional name for result object
            keep_originals: Whether to keep original objects

        Returns:
            Dictionary with operation result
        """
        try:
            # Validate objects
            valid, obj1, obj2, error = self._validate_objects(obj1_name, obj2_name)
            if not valid:
                return {
                    "success": False,
                    "error": error,
                    "message": f"Boolean union failed: {error}",
                }

            doc = App.ActiveDocument

            # Perform union operation
            union_shape = obj1.Shape.fuse(obj2.Shape)

            # Create result object
            name = result_name or f"Union_{obj1_name}_{obj2_name}"
            union_obj = doc.addObject("Part::Feature", name)
            union_obj.Shape = union_shape
            union_obj.Label = name

            # Handle original objects
            if not keep_originals:
                doc.removeObject(obj1_name)
                doc.removeObject(obj2_name)

            # Recompute document
            doc.recompute()

            return {
                "success": True,
                "object_name": union_obj.Name,
                "label": union_obj.Label,
                "message": f"Successfully created union of {obj1_name} and {obj2_name}",
                "properties": {
                    "volume": round(union_shape.Volume, 2),
                    "area": round(union_shape.Area, 2),
                    "originals_kept": keep_originals,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to perform boolean union: {str(e)}",
            }

    def boolean_cut(
        self,
        obj1_name: str,
        obj2_name: str,
        result_name: str = None,
        keep_originals: bool = False,
    ) -> Dict[str, Any]:
        """Perform a boolean cut (difference) operation - subtract obj2 from obj1.

        Args:
            obj1_name: Name of object to cut from
            obj2_name: Name of cutting object
            result_name: Optional name for result object
            keep_originals: Whether to keep original objects

        Returns:
            Dictionary with operation result
        """
        try:
            # Validate objects
            valid, obj1, obj2, error = self._validate_objects(obj1_name, obj2_name)
            if not valid:
                return {
                    "success": False,
                    "error": error,
                    "message": f"Boolean cut failed: {error}",
                }

            doc = App.ActiveDocument

            # Perform cut operation
            cut_shape = obj1.Shape.cut(obj2.Shape)

            # Create result object
            name = result_name or f"Cut_{obj1_name}_minus_{obj2_name}"
            cut_obj = doc.addObject("Part::Feature", name)
            cut_obj.Shape = cut_shape
            cut_obj.Label = name

            # Handle original objects
            if not keep_originals:
                doc.removeObject(obj1_name)
                doc.removeObject(obj2_name)

            # Recompute document
            doc.recompute()

            return {
                "success": True,
                "object_name": cut_obj.Name,
                "label": cut_obj.Label,
                "message": f"Successfully cut {obj2_name} from {obj1_name}",
                "properties": {
                    "volume": round(cut_shape.Volume, 2),
                    "area": round(cut_shape.Area, 2),
                    "originals_kept": keep_originals,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to perform boolean cut: {str(e)}",
            }

    def boolean_intersection(
        self,
        obj1_name: str,
        obj2_name: str,
        result_name: str = None,
        keep_originals: bool = False,
    ) -> Dict[str, Any]:
        """Perform a boolean intersection (common) operation on two objects.

        Args:
            obj1_name: Name of first object
            obj2_name: Name of second object
            result_name: Optional name for result object
            keep_originals: Whether to keep original objects

        Returns:
            Dictionary with operation result
        """
        try:
            # Validate objects
            valid, obj1, obj2, error = self._validate_objects(obj1_name, obj2_name)
            if not valid:
                return {
                    "success": False,
                    "error": error,
                    "message": f"Boolean intersection failed: {error}",
                }

            doc = App.ActiveDocument

            # Perform intersection operation
            intersect_shape = obj1.Shape.common(obj2.Shape)

            # Check if intersection is empty
            if intersect_shape.Volume < 0.001:  # Very small threshold
                return {
                    "success": False,
                    "error": "No intersection",
                    "message": f"Objects {obj1_name} and {obj2_name} do not intersect",
                }

            # Create result object
            name = result_name or f"Intersection_{obj1_name}_{obj2_name}"
            intersect_obj = doc.addObject("Part::Feature", name)
            intersect_obj.Shape = intersect_shape
            intersect_obj.Label = name

            # Handle original objects
            if not keep_originals:
                doc.removeObject(obj1_name)
                doc.removeObject(obj2_name)

            # Recompute document
            doc.recompute()

            return {
                "success": True,
                "object_name": intersect_obj.Name,
                "label": intersect_obj.Label,
                "message": f"Successfully created intersection of {obj1_name} and {obj2_name}",
                "properties": {
                    "volume": round(intersect_shape.Volume, 2),
                    "area": round(intersect_shape.Area, 2),
                    "originals_kept": keep_originals,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to perform boolean intersection: {str(e)}",
            }

    def move_object(
        self,
        obj_name: str,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        relative: bool = True,
    ) -> Dict[str, Any]:
        """Move an object to a new position.

        Args:
            obj_name: Name of object to move
            x: X displacement or position
            y: Y displacement or position
            z: Z displacement or position
            relative: If True, move relative to current position; if False, move to absolute position

        Returns:
            Dictionary with operation result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document found",
                }

            obj = self._get_object(obj_name, doc)
            if not obj:
                return {
                    "success": False,
                    "error": f"Object '{obj_name}' not found",
                    "message": f"Object '{obj_name}' not found in document",
                }

            # Get current position
            current_pos = obj.Placement.Base

            if relative:
                # Move relative to current position
                new_pos = App.Vector(
                    current_pos.x + x, current_pos.y + y, current_pos.z + z
                )
                operation = "moved"
            else:
                # Move to absolute position
                new_pos = App.Vector(x, y, z)
                operation = "positioned"

            # Apply new position
            obj.Placement.Base = new_pos

            # Recompute document
            doc.recompute()

            return {
                "success": True,
                "object_name": obj.Name,
                "label": obj.Label,
                "message": f"Successfully {operation} {obj_name} to ({new_pos.x}, {new_pos.y}, {new_pos.z})",
                "properties": {
                    "old_position": (current_pos.x, current_pos.y, current_pos.z),
                    "new_position": (new_pos.x, new_pos.y, new_pos.z),
                    "relative": relative,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to move object: {str(e)}",
            }

    def rotate_object(
        self,
        obj_name: str,
        angle_x: float = 0,
        angle_y: float = 0,
        angle_z: float = 0,
        center: tuple = None,
    ) -> Dict[str, Any]:
        """Rotate an object around its center or a specified point.

        Args:
            obj_name: Name of object to rotate
            angle_x: Rotation angle around X axis in degrees
            angle_y: Rotation angle around Y axis in degrees
            angle_z: Rotation angle around Z axis in degrees
            center: Optional center point (x, y, z) for rotation

        Returns:
            Dictionary with operation result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document found",
                }

            obj = self._get_object(obj_name, doc)
            if not obj:
                return {
                    "success": False,
                    "error": f"Object '{obj_name}' not found",
                    "message": f"Object '{obj_name}' not found in document",
                }

            # Create rotation
            rot = App.Rotation(
                angle_z, angle_y, angle_x
            )  # Note: FreeCAD uses ZYX order

            if center:
                # Rotate around specified center
                center_vec = App.Vector(*center)
                placement = App.Placement(center_vec, App.Rotation())
                placement = placement.multiply(App.Placement(App.Vector(), rot))
                placement = placement.multiply(
                    App.Placement(-center_vec, App.Rotation())
                )
                obj.Placement = obj.Placement.multiply(placement)
            else:
                # Rotate around object's current position
                current_placement = obj.Placement
                new_rotation = current_placement.Rotation.multiply(rot)
                obj.Placement.Rotation = new_rotation

            # Recompute document
            doc.recompute()

            return {
                "success": True,
                "object_name": obj.Name,
                "label": obj.Label,
                "message": f"Successfully rotated {obj_name} by ({angle_x}°, {angle_y}°, {angle_z}°)",
                "properties": {
                    "rotation_angles": (angle_x, angle_y, angle_z),
                    "rotation_center": center if center else "object center",
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to rotate object: {str(e)}",
            }

    def scale_object(
        self,
        obj_name: str,
        scale_x: float = 1.0,
        scale_y: float = None,
        scale_z: float = None,
        uniform: bool = True,
    ) -> Dict[str, Any]:
        """Scale an object by specified factors.

        Args:
            obj_name: Name of object to scale
            scale_x: Scale factor for X axis (or uniform scale if uniform=True)
            scale_y: Scale factor for Y axis (ignored if uniform=True)
            scale_z: Scale factor for Z axis (ignored if uniform=True)
            uniform: If True, use scale_x for all axes

        Returns:
            Dictionary with operation result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document found",
                }

            obj = self._get_object(obj_name, doc)
            if not obj:
                return {
                    "success": False,
                    "error": f"Object '{obj_name}' not found",
                    "message": f"Object '{obj_name}' not found in document",
                }

            if not hasattr(obj, "Shape") or not obj.Shape:
                return {
                    "success": False,
                    "error": "Object has no shape",
                    "message": f"Object '{obj_name}' has no valid shape to scale",
                }

            # Determine scale factors
            if uniform:
                sx = sy = sz = scale_x
            else:
                sx = scale_x
                sy = scale_y if scale_y is not None else scale_x
                sz = scale_z if scale_z is not None else scale_x

            # Create transformation matrix
            mat = App.Matrix()
            mat.scale(sx, sy, sz)

            # Apply transformation
            scaled_shape = obj.Shape.transformGeometry(mat)

            # Create new object with scaled shape
            scaled_name = f"{obj_name}_scaled"
            scaled_obj = doc.addObject("Part::Feature", scaled_name)
            scaled_obj.Shape = scaled_shape
            scaled_obj.Label = f"{obj.Label} (scaled)"

            # Copy placement from original
            scaled_obj.Placement = obj.Placement

            # Optionally remove original
            # doc.removeObject(obj_name)

            # Recompute document
            doc.recompute()

            return {
                "success": True,
                "object_name": scaled_obj.Name,
                "label": scaled_obj.Label,
                "message": f"Successfully scaled {obj_name} by factors ({sx}, {sy}, {sz})",
                "properties": {
                    "scale_factors": (sx, sy, sz),
                    "uniform_scale": uniform,
                    "new_volume": round(scaled_shape.Volume, 2),
                    "new_area": round(scaled_shape.Area, 2),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to scale object: {str(e)}",
            }

    def get_available_operations(self) -> Dict[str, Any]:
        """Get list of available operations.

        Returns:
            Dictionary with available operations and their parameters
        """
        return {
            "operations": {
                "boolean_union": {
                    "description": "Fuse two objects together",
                    "parameters": [
                        "obj1_name",
                        "obj2_name",
                        "result_name",
                        "keep_originals",
                    ],
                },
                "boolean_cut": {
                    "description": "Subtract one object from another",
                    "parameters": [
                        "obj1_name",
                        "obj2_name",
                        "result_name",
                        "keep_originals",
                    ],
                },
                "boolean_intersection": {
                    "description": "Find common volume between two objects",
                    "parameters": [
                        "obj1_name",
                        "obj2_name",
                        "result_name",
                        "keep_originals",
                    ],
                },
                "move_object": {
                    "description": "Move object to new position",
                    "parameters": ["obj_name", "x", "y", "z", "relative"],
                },
                "rotate_object": {
                    "description": "Rotate object around axes",
                    "parameters": [
                        "obj_name",
                        "angle_x",
                        "angle_y",
                        "angle_z",
                        "center",
                    ],
                },
                "scale_object": {
                    "description": "Scale object by factors",
                    "parameters": [
                        "obj_name",
                        "scale_x",
                        "scale_y",
                        "scale_z",
                        "uniform",
                    ],
                },
            }
        }
